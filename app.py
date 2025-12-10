import sqlite3
import threading
import time
import os
from datetime import datetime
from flask import Flask, g, jsonify, request, render_template

DATABASE = 'hospital.db'
SCHEDULER_INTERVAL = 5  # seconds
AGING_INTERVAL = 30     # Decrease priority score (increase importance) every 30s of waiting
MIN_PRIORITY = 5        # Lowest urgency
MAX_PRIORITY = 1        # Highest urgency

# Resource configuration
RESOURCE_TYPES = {
    'ICU_BED': 5,
    'VENTILATOR': 2
}

app = Flask(__name__)
db_lock = threading.Lock()
allocation_lock = threading.Lock()

# --- Database Setup & Helpers ---

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE, check_same_thread=False)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with db_lock:
        conn = sqlite3.connect(DATABASE)
        with open('schema.sql', 'r') as f:
            sql = f.read()
        conn.executescript(sql)
        conn.commit()
        conn.close()
    seed_resources()

def seed_resources():
    with db_lock:
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM resources")
        if cur.fetchone()[0] == 0:
            print("[System] Seeding resources...")
            id_counter = 1
            for rtype, count in RESOURCE_TYPES.items():
                for i in range(count):
                    label = f"{rtype}-{id_counter}"
                    cur.execute("INSERT INTO resources (resource_type, label, status) VALUES (?, ?, ?)",
                                (rtype, label, "free"))
                    id_counter += 1
            conn.commit()
        conn.close()

def db_query(query, params=(), one=False, commit=False):
    with db_lock:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(query, params)
        if commit:
            conn.commit()
            rv = cur.lastrowid
        else:
            rv = cur.fetchall()
        conn.close()
        return (rv[0] if rv else None) if one else rv

# --- API Endpoints ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/request', methods=['POST'])
def create_request():
    data = request.json
    name = data.get('name', 'Anonymous')
    priority = int(data.get('priority', 3))
    # Ensure priority is within bounds
    priority = max(MAX_PRIORITY, min(priority, MIN_PRIORITY))
    
    req_type = data.get('resource_type', 'ICU_BED')
    est_minutes = int(data.get('est_minutes', 60))

    q = """INSERT INTO patient_requests 
           (name, priority, required_resource, est_minutes, status) 
           VALUES (?, ?, ?, ?, ?)"""
    rid = db_query(q, (name, priority, req_type, est_minutes, 'queued'), commit=True)
    return jsonify({"request_id": rid, "status": "queued"}), 201

@app.route('/api/requests', methods=['GET'])
def list_requests():
    rows = db_query("SELECT * FROM patient_requests ORDER BY requested_at ASC")
    return jsonify([dict(r) for r in rows])

@app.route('/api/resources', methods=['GET'])
def list_resources():
    rows = db_query("SELECT * FROM resources ORDER BY resource_type, id")
    return jsonify([dict(r) for r in rows])

@app.route('/api/allocations', methods=['GET'])
def list_allocations():
    q = """SELECT a.*, p.name, p.priority, p.required_resource 
           FROM allocations a 
           JOIN patient_requests p ON p.id = a.request_id 
           WHERE a.released_at IS NULL"""
    rows = db_query(q)
    return jsonify([dict(r) for r in rows])

@app.route('/api/release', methods=['POST'])
def release_allocation():
    data = request.json
    allocation_id = int(data.get('allocation_id'))
    
    with allocation_lock:
        # 1. Mark allocation as released
        db_query("UPDATE allocations SET released_at = CURRENT_TIMESTAMP WHERE id = ?", (allocation_id,), commit=True)
        
        # 2. Get details to free the specific resource
        row = db_query("SELECT resource_id, request_id FROM allocations WHERE id = ?", (allocation_id,), one=False)
        if row:
            res_id = row[0]['resource_id']
            req_id = row[0]['request_id']
            
            # 3. Free the resource
            db_query("UPDATE resources SET status = 'free' WHERE id = ?", (res_id,), commit=True)
            # 4. Mark request completed
            db_query("UPDATE patient_requests SET status = 'completed', released_at = CURRENT_TIMESTAMP WHERE id = ?", (req_id,), commit=True)
            
            print(f"[Scheduler] Resource {res_id} released.")

    return jsonify({"status": "released"})

# --- OS Principles: Scheduler Logic ---

def calculate_effective_priority(base_priority, requested_at_str):
    """
    Implements 'Aging': A technique to prevent starvation.
    As waiting time increases, the effective priority number decreases (approaching 1).
    """
    req_time = datetime.strptime(requested_at_str, "%Y-%m-%d %H:%M:%S")
    wait_seconds = (datetime.utcnow() - req_time).total_seconds()
    
    # For every AGING_INTERVAL seconds, improve priority by 1
    priority_boost = int(wait_seconds // AGING_INTERVAL)
    
    # Effective priority cannot go better than 1 (MAX_PRIORITY)
    effective = max(MAX_PRIORITY, base_priority - priority_boost)
    return effective, wait_seconds

def run_allocation_cycle():
    """
    The Core OS Allocator. 
    1. Looks for free resources.
    2. Looks for queued processes (requests).
    3. Matches them based on Resource Affinity (Type) and Priority.
    """
    with allocation_lock:
        # 1. Identify what is free
        free_resources_rows = db_query("SELECT * FROM resources WHERE status = 'free'")
        if not free_resources_rows:
            return # No resources available, CPU/Scheduler yields

        # Group free resources by type: {'ICU_BED': [row, row], 'VENTILATOR': [row]}
        free_map = {}
        for r in free_resources_rows:
            rtype = r['resource_type']
            if rtype not in free_map:
                free_map[rtype] = []
            free_map[rtype].append(r)

        # 2. Identify who is waiting
        queued_rows = db_query("SELECT * FROM patient_requests WHERE status = 'queued'")
        if not queued_rows:
            return

        # 3. Calculate Effective Priority for all waiting requests
        waiting_list = []
        for req in queued_rows:
            eff_p, wait_sec = calculate_effective_priority(req['priority'], req['requested_at'])
            waiting_list.append({
                'data': req,
                'eff_priority': eff_p,
                'wait_seconds': wait_sec
            })

        # 4. Sort waiting list: 
        # Primary Key: Effective Priority (Ascending -> 1 is best)
        # Secondary Key: Wait Time (Descending -> longest wait first)
        waiting_list.sort(key=lambda x: (x['eff_priority'], -x['wait_seconds']))

        # 5. Allocation Logic
        for item in waiting_list:
            req = item['data']
            needed_type = req['required_resource']

            # Do we have a free resource of this specific type?
            if needed_type in free_map and len(free_map[needed_type]) > 0:
                # Pop the first available resource of this type
                resource = free_map[needed_type].pop(0)
                
                # EXECUTE ALLOCATION
                print(f"[Scheduler] Allocating {resource['label']} to {req['name']} (Eff Pri: {item['eff_priority']})")
                
                db_query("UPDATE resources SET status = 'in_use' WHERE id = ?", (resource['id'],), commit=True)
                db_query("UPDATE patient_requests SET status = 'allocated', allocated_at = CURRENT_TIMESTAMP WHERE id = ?", (req['id'],), commit=True)
                db_query("INSERT INTO allocations (request_id, resource_type, resource_id) VALUES (?, ?, ?)",
                         (req['id'], resource['resource_type'], resource['id']), commit=True)

def scheduler_thread():
    print("[Scheduler] Daemon started...")
    while True:
        try:
            run_allocation_cycle()
        except Exception as e:
            print(f"[Scheduler Error] {e}")
        time.sleep(SCHEDULER_INTERVAL)

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    else:
        seed_resources()
    
    # Start the scheduler in background
    t = threading.Thread(target=scheduler_thread, daemon=True)
    t.start()
    
    app.run(debug=True, threaded=True, port=5000)