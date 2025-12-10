DROP TABLE IF EXISTS allocations;
DROP TABLE IF EXISTS patient_requests;
DROP TABLE IF EXISTS resources;

CREATE TABLE patient_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    priority INTEGER NOT NULL, -- 1 (Highest) to 5 (Lowest)
    required_resource TEXT NOT NULL, -- NEW: matches resources.resource_type
    est_minutes INTEGER NOT NULL,
    status TEXT NOT NULL, -- queued, allocated, completed
    requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    allocated_at DATETIME,
    released_at DATETIME
);

CREATE TABLE allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id INTEGER NOT NULL,
    allocated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    released_at DATETIME,
    FOREIGN KEY(request_id) REFERENCES patient_requests(id)
);

CREATE TABLE resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_type TEXT NOT NULL, -- ICU_BED, VENTILATOR
    label TEXT NOT NULL, -- "ICU-1", "VENT-2"
    status TEXT NOT NULL -- free, in_use
);