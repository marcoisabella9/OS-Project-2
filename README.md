# OS-Project-2
## Project Description
This project is an implementation of Hospital Resource allocation systems with a Web API and automatic scheduler. The system manages critical health resources such as ICU beds and Ventilators and will automatically assign them to patients depending upon priority and waiting time.
## Significance Of Project
This project is significant because we can apply Scheduling algorithms to make it so that we are able to take care of more patients more efficiently with less resources. Poor allocation of resources can sometimes lead to lost lives as well. The system models a genuine ethical and operational challenge within the Healthcare industry.
## Code Structure
* We use Flask for the Web API, SQLite database for persistence, threading, and the standard python libraries to make our project all come together. 
* We define a number of constants to configure our project to work, including things like max and min priority, where the database file is located, resource types and how much of each resource. 
* On the database layer, we use the get_db() and close_connection() functions to deal with connections. We use the init_db() and seed_resources() functions to create the tables from our schema and populate the initial resources. We use db_execute() and db_query_rows() functions to execute queries and fetch data. We also use db_lock to prevent concurrent write conflicts.
