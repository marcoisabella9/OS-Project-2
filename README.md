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