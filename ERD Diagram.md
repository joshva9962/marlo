Chart for main.py:
+---------------------+       +----------------------+
|      User           |       |    API Data          |
|---------------------|       |----------------------|
|username             |       | _id                  |
| role                |-------| group                |
+---------------------+       |  other fields        |
                              +----------------------+
                                      |
                                      |
                                      |
                        +-------------------------------+
                        |    (Relationship via role)    |
                        |                               |
                        |  The User's role determines   |
                        |  the type of data they can    |
                        |  access from API Data (e.g.,  |
                        |  all, bulk, or tanker data).  |
                        +-------------------------------+

Chart for task_scheduler_to_get_daily_data.py:

+-------------------------+
|       api_data          |
+-------------------------+
| _id                     |  <-- Primary Key (auto-generated)
| fetched_at (timestamp)  |  <-- Timestamp when the data was fetched
| (dynamic fields)        |  <-- Other fields from the API response
+-------------------------+

