### 1.1 OLTP vs OLAP

two types of database workloads.

| Feature               | OLTP                          | OLAP                               |
| --------------------- | ----------------------------- | ---------------------------------- |
| Full name             | Online Transaction Processing | Online Analytical Processing       |
| Purpose               | Handle business transactions  | Analyze large amounts of data      |
| Operations            | INSERT, UPDATE, DELETE        | SELECT, GROUP BY, aggregation      |
| Data volume per query | Usually small                 | Often millions or billions of rows |
| Query complexity      | Relatively simple             | Often complex                      |
| Examples              | MySQL, PostgreSQL             | ClickHouse                         |

For example:

**OLTP:**

```sql
SELECT * FROM users WHERE id = 1001;
```

This retrieves a specific user record.

**OLAP:**

```sql
SELECT
    service_name,
    count(*) AS error_count
FROM application_logs
WHERE level = 'ERROR'
  AND event_time >= now() - INTERVAL 24 HOUR
GROUP BY service_name
ORDER BY error_count DESC;
```

This analyzes potentially billions of log records to identify services with the most errors.
