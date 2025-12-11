# OS-Project-2
## Project Description
This project is an implementation of Hospital Resource allocation systems with a Web API and automatic scheduler. The system manages critical health resources such as ICU beds and Ventilators and will automatically assign them to patients depending upon priority and waiting time.
## Significance Of Project
This project is significant because we can apply Scheduling algorithms to make it so that we are able to take care of more patients more efficiently with less resources. Poor allocation of resources can sometimes lead to lost lives as well. The system models a genuine ethical and operational challenge within the Healthcare industry.
## Code Structure
* We use Flask for the Web API, SQLite database for persistence, threading, and the standard python libraries to make our project all come together. Within the Flask application, we use an API layer and a background scheduler which flow into a thread-safe database layer. The entire flask application then goes to the SQLite database layer.
* We define a number of constants to configure our project to work, including things like max and min priority, where the database file is located, resource types and how much of each resource. 
* On the database layer, we use the get_db() and close_connection() functions to deal with connections. We use the init_db() and seed_resources() functions to create the tables from our schema and populate the initial resources. We use db_execute() and db_query_rows() functions to execute queries and fetch data. We also use db_lock to prevent concurrent write conflicts.
* For the requests, it flows from the user, generates an API request, validates the data, then inserts it into the Database.
* For the allocations, the scheduler wakes (every 5 seconds), queries free resources, queries queued requests, calculate effective priorities, sorts by priority and fifo, matches and allocates, then updates the database. 
* For releases, it frlows from the user, generates an API request, locks allocation, updates it, frees the resources, completes the request, then unlocks.
## Algorithms
### Priority Aging Algorithm
* Purpose: Prevent starvation of lower-priority patients while maintaining priority based allocation.
* Every 60 seconds of waiting, reduces effective priority by 1 (lower means higher priority).
* Priority cannot go below 1.
* Linear aging ensures predictable behavior.
* Priority 5 patient waiting 0 seconds would yield an effective priority of 5. A Priority 5 patient waiting 120 seconds would yield an effective priority of 3. A Priority 5 patient waiting 300 seconds would yield an effective priority of 1.
### Resource Allocation Algorithm
* Purpose: Match available resources to waiting patients based on effective priority.
* First we discover resources, then we queue processing, then we sort by priority and FIFO, then we do a greedy allocation. 
* The time complexity of this algorithm is O(n log n) where n is the number of queued requests.
* The space complexity of this algorithm is O(n + m) where m is the number of free resources.
### Concurrency Control Algorithm
* A Two Lock strategy is used, using db_lock and allocation_lock. 
* db_lock prevents concurrent SQLite writes, and is used by all database operations.
* allocation_lock prevents race conditions during allocation and ensures atomic allocation operations.
* In the critical section, release operations require allocation_lock to prevent concurrent allocation. The scheduler acquires allocation_lock during the entire allocation cycle. Prevents double allocation, use after free, and inconsistent states.
## Verification of Algorithms

## Functionalities
* Patient Request Submission
    * Endpoint: POST /api/request
    * Input: Patient name, priority (1-5), estimated usage time (minutes)
    * Function: Creates a new resource request in "queued" status
    * Output: Unique request ID
    * Use Case: Emergency department admits patient needing ICU bed

* Resource Status Monitoring
    * Endpoint: GET /api/resources
    * Function: Retrieves current status of all hospital resources
    * Output: List of resources with ID, type, label, and status (free/in_use)
    * Use Case: Hospital staff checks ICU bed availability

* Request Queue Viewing
    * Endpoint: GET /api/requests
    * Function: Lists all patient requests with status and timestamps
    * Output: Complete request history ordered chronologically
    * Use Case: Administrator reviews allocation history and current queue
* Active Allocation Tracking
    * Endpoint: GET /api/allocations
    * Function: Shows currently active resource allocations (unreleased)
    * Output: Allocation details joined with patient information
    * Use Case: Nurse identifies which patient is using which ICU bed

* Resource Release
    * Endpoint: POST /api/release
    * Input: Allocation ID
    * Function: Marks allocation as released, frees resource, completes patient request
    * Output: Release confirmation
    * Use Case: Patient treatment completed, ICU bed becomes available

* Automated Allocation Scheduling
    * Process: Background thread running every 5 seconds
    * Function: Discovers free resources, Calculates effective priorities for queued patients, Performs optimal matching based on priority and FIFO, Updates database with new allocations
    * Use Case: System automatically assigns freed ICU bed to highest-priority waiting patient

* Priority Aging
    * Process: Integrated into allocation cycle
    * Function: Dynamically adjusts patient priority based on waiting time
    * Formula: Priority improves by 1 level per 60 seconds of waiting
    * Use Case: Prevents lower-priority patients from indefinite waiting

* Database Initialization
    * Creates schema from SQL file
    * Seeds initial resources
    * Ensures database consistency on startup

* Web Interface
    * Serves HTML dashboard at root URL
    * Provides user-friendly interface to API
    * Real-time visualization of system state

* Thread-Safe Operations
    * Dual-lock concurrency control
    * Prevents race conditions and data corruption
    * Ensures atomic allocation operations

## Execution Results and Analysis

<h4>1. Resource Utilization and Contention</h4>
Our analysis focused on resources allocated versus queue growth under high demand scenarios.
We configured the system with a scarcity of Ventilators (2 units) compared to ICU Beds (5 units) to force contention.
<ul>
    <li><strong>Ventilator Allocation:</strong> With 5 patient requests for Ventilators, only 2 were allocated immediately. The remaining 3 entered the Waiting Queue, demonstrating the <strong>Blocking</strong> state analogous to a process waiting on a full semaphore.</li>
    <li><strong>ICU Bed Allocation:</strong> Requests for ICU Beds were fulfilled instantly, confirming the scheduler's ability to handle resource affinity and isolation (i.e., the shortage of one resource type does not block the use of another).</li>
</ul>

<h4>2. Priority Scheduling and Throughput</h4>
<p>We analyzed the impact of our custom Priority Scheduling algorithm (incorporating Aging) on the order of service:</p>
<table border="1" style="width: 100%; text-align: left;">
    <thead>
        <tr>
            <th>Request</th>
            <th>Base Priority (P)</th>
            <th>Order of Arrival</th>
            <th>Order of Allocation</th>
            <th>Justification (OS Principle)</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Req F</td>
            <td>1 (Highest)</td>
            <td>Last</td>
            <td>1st</td>
            <td><strong>Strict Priority Scheduling:</strong> P1 preempts all lower-priority queued requests.</td>
        </tr>
        <tr>
            <td>Req C</td>
            <td>3 (Medium)</td>
            <td>2nd</td>
            <td>2nd</td>
            <td>FIFO among equal priorities (after P1 is served).</td>
        </tr>
        <tr>
            <td>Req E</td>
            <td>5 (Lowest)</td>
            <td>3rd</td>
            <td>3rd (after aging)</td>
            <td><strong>Aging:</strong> Was allocated before new P3 requests due to accumulated wait time.</td>
        </tr>
    </tbody>
</table>

<h4>3. Implementation of Aging to Prevent Starvation</h4>
<p>The Aging mechanism successfully demonstrated how to prevent "starvation" of low-priority patients. The scheduler was configured to boost the effective priority by 1 (i.e., P5 becomes P4) every 30 seconds of waiting.</p>
<ul>
    <li>A <strong>Priority 5</strong> patient (Req E) was observed to have an <strong>Effective Priority</strong> change from 5 to 4 after 30 seconds, and 4 to 3 after 60 seconds.</li>
    <li>This change ensured that, when a resource became free, the aging patient was prioritized over a newly arriving P3 patient, guaranteeing eventual resource access for all waiting patients.</li>
</ul>

## Conclusions

<h3>Summary of Findings</h3>
<p>The Hospital Resource Allocator effectively models essential OS mechanisms for managing finite resources in a concurrent environment. We successfully implemented:</p>
<ol>
    <li><strong>Resource Management:</strong> Tracking the state (free/in_use) of individual, distinct resources (ICU Beds, Ventilators).</li>
    <li><strong>Concurrency Control:</strong> Using Python's <code>threading.Lock</code> to protect shared resources (the SQLite database and the allocation routine) from race conditions.</li>
    <li><strong>Scheduling:</strong> A custom, preemptive Priority Scheduling algorithm based on patient urgency (1-5).</li>
    <li><strong>Fairness:</strong> An <strong>Aging</strong> mechanism to dynamically adjust priority, ensuring fairness and preventing resource starvation for low-urgency patients.</li>
</ol>

<h3>Project Issues and Challenges</h3>
<ul>
    <li><strong>Real-Time Simulation:</strong> The use of `time.sleep()` in the scheduler thread limits the project's ability to handle high-frequency events, as the minimum scheduler interval is 5 seconds. A true high-performance system would require asynchronous task processing.</li>
    <li><strong>Deadlock Prevention:</strong> The current model only allocates a single resource type per request. Implementing multi-resource requests (e.g., patient needs a Bed AND a Ventilator) would introduce the risk of <strong>Deadlock</strong>, which was not addressed in this version.</li>
    <li><strong>Persistence and Rollback:</strong> The system relies on atomic database updates for state changes. A failure during a critical multi-step allocation or release sequence could leave the system in an inconsistent state, highlighting the need for true database transactions and robust error handling.</li>
</ul>

<h3>Application of Course Learning</h3>
<p>This project served as a direct application of several core Operating Systems course topics:</p>
<ul>
    <li><strong>Processes and Threads:</strong> The scheduler runs as a separate <strong>Daemon Thread</strong>, allowing it to execute concurrently with the main Flask web server thread, simulating a kernel service running alongside user processes.</li>
    <li><strong>Synchronization and Mutual Exclusion:</strong> The `db_lock` and `allocation_lock` objects are used as <strong>Mutexes</strong> (Mutual Exclusion locks) to ensure only one thread modifies the shared database or allocation state at any given time, preventing data corruption and race conditions.</li>
    <li><strong>Scheduling Algorithms:</strong> Implementation of a complex priority-based scheduler, which is a hybrid of <strong>Priority Scheduling</strong> and <strong>First-Come, First-Served (FCFS)</strong> (used as a tie-breaker), with the added complexity of the <strong>Aging</strong> technique.</li>
</ul>
