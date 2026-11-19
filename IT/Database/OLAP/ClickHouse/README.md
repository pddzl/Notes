# ClickHouse: Concepts, Architecture and Practical Guide

## 1. What Is ClickHouse?

**ClickHouse** is an open-source, column-oriented database management system (DBMS) designed for online analytical processing (OLAP).

It is optimized for:

- Storing massive amounts of data.
- Performing complex analytical queries.
- Aggregating and analyzing large datasets.
- Processing billions of records efficiently.
- Supporting real-time analytical workloads.

ClickHouse was originally developed by Yandex and is now maintained by ClickHouse, Inc. and its open-source community.

## 2. Why Is ClickHouse So Fast?

The primary reason is its column-oriented storage architecture.

### 2.1 Row-Oriented vs Column-Oriented Storage

Consider a table containing three columns:

|id|name|age|
|---|---|---|
|1|Alice|25|
|2|Bob|30|
|3|Charlie|28|

**Row-oriented storage**

Data is stored row by row:

```text
1, Alice, 25
2, Bob, 30
3, Charlie, 28
```

Databases such as MySQL typically use this storage approach.

When retrieving a complete record, the database can efficiently access all its fields.

**Column-oriented storage**

Data is stored column by column:

```text
id:   1, 2, 3
name: Alice, Bob, Charlie
age:  25, 30, 28
```

ClickHouse uses this approach.

Suppose we execute:

```sql
SELECT avg(age) FROM users;
```

ClickHouse only needs to read the `age` column.

It does not need to read `id` or `name`.

This significantly reduces disk I/O when analytical queries only need a few columns from a large dataset.

### 2.2 Compression

Column-oriented storage also improves compression.

Values in the same column often have similar data types and patterns.

For example:

```text
status: 200, 200, 200, 200, 500, 500
```

These values can be compressed efficiently.

ClickHouse supports multiple compression codecs, including:

- LZ4
- ZSTD
- Delta
- DoubleDelta
- Gorilla

Compression reduces storage consumption and disk I/O.

### 2.3 Vectorized Query Execution

ClickHouse processes data in batches rather than handling every row individually.

For example, instead of executing an operation separately for each row, it processes a block of values together.

This improves CPU efficiency and makes better use of modern processors.

### 2.4 Parallel Query Execution

ClickHouse can execute different parts of a query concurrently.

For example, when scanning a large table, multiple CPU threads can process different data ranges simultaneously.

Together, columnar storage, compression, vectorized execution, and parallel processing make ClickHouse extremely fast for analytical workloads.

## 3. ClickHouse Architecture

A typical ClickHouse deployment consists of the following components:

```
                 Applications
                      |
                      v
               ClickHouse Client
                      |
                      v
               ClickHouse Server
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
       Storage     Query       Background
       Engine      Engine      Processing
          |           |           |
          +-----------+-----------+
                      |
                      v
                  Disk Storage
```

### 3.1 ClickHouse Server

The ClickHouse server is the main database service.

Its responsibilities include:

- Accepting client connections.
- Executing SQL queries.
- Managing tables and databases.
- Managing data storage.
- Coordinating distributed queries.
- Handling background operations.

Common ports:

|Port|Protocol|Purpose|
|---|---|---|
|9000|Native TCP|ClickHouse client connections|
|8123|HTTP|HTTP interface|
|9009|HTTP|Inter-server communication|
|9440|Native TCP|Secure native connections|
|8443|HTTPS|Secure HTTP interface|

### 3.2 Storage Engine

ClickHouse uses different table engines to determine how data is stored, replicated, partitioned, and queried.

Important engines include:

|Engine|Purpose|
|---|---|
|MergeTree|General-purpose analytical storage|
|ReplacingMergeTree|Deduplication and replacement of rows|
|SummingMergeTree|Aggregating numeric values|
|AggregatingMergeTree|Storing aggregate states|
|ReplicatedMergeTree|Replicated MergeTree storage|
|Distributed|Distributed query routing|

**MergeTree is the foundation of most ClickHouse deployments.**

We will discuss it in detail later.

## 4. MergeTree: The Most Important Storage Engine

MergeTree is ClickHouse's primary storage engine family.

It provides:

- Efficient data insertion.
- Sorted data storage.
- Data compression.
- Partitioning.
- Primary-key-based data skipping.
- Background data merging.

### 4.1 How MergeTree Stores Data

When data is inserted into a MergeTree table, ClickHouse generally creates immutable data parts.

For example:

```
application_logs/
├── partition_202611/
│   ├── part_1/
│   ├── part_2/
│   └── part_3/
└── partition_202612/
    ├── part_4/
    └── part_5/
```

Each part contains data files and metadata.

ClickHouse periodically merges smaller parts into larger parts in the background.

```
part_1 + part_2 + part_3
             |
             v
       Background Merge
             |
             v
          part_4
```

This process is called **MergeTree background merging**.

Important characteristics:

- Data parts are immutable.
- INSERT operations create new parts.
- Background merges combine existing parts.
- Queries read relevant parts and combine their results.

This architecture is optimized for high-throughput analytical workloads.

### 4.2 ORDER BY and Primary Key

Example:

```sql
CREATE TABLE application_logs
(
    event_time DateTime,
    service_name String,
    level LowCardinality(String),
    message String
)
ENGINE = MergeTree
ORDER BY (event_time, service_name);
```

The `ORDER BY` clause defines the sorting key.

It determines how data is physically organized within data parts.

This helps ClickHouse skip irrelevant data ranges during queries.

For example:

```sql
SELECT *
FROM application_logs
WHERE event_time >= '2026-11-19 00:00:00';
```

If the table is sorted by `event_time`, ClickHouse can efficiently locate relevant data ranges.

**Important:** ClickHouse's primary key is not equivalent to a traditional MySQL primary key.

It is primarily used for data skipping and does not enforce row uniqueness.

### 4.3 PARTITION BY

Partitioning divides a table into logical data groups.

Example:

```sql
CREATE TABLE application_logs
(
    event_time DateTime,
    service_name String,
    level String,
    message String
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(event_time)
ORDER BY (event_time, service_name);
```

The data is partitioned by month:

```
application_logs
├── 202611
├── 202612
├── 202701
└── 202702
```

Benefits:

- Easier retention management.
- Efficient partition-level deletion.
- Better data organization.
- Potentially improved query performance.

For log storage, monthly partitions are often a reasonable starting point.

However, partitioning should not be excessively granular.

## 5. Sharding and Replication

These are two fundamental concepts in distributed ClickHouse deployments.

### 5.1 What Is a Shard?

A shard is an independent portion of the overall dataset.

Sharding distributes data across multiple ClickHouse nodes.

For example, a three-shard cluster:

```text
              ClickHouse Cluster
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
       Shard 1     Shard 2     Shard 3
       Node 1      Node 2      Node 3
          |           |           |
       1/3 data    1/3 data    1/3 data
```

Each shard stores a portion of the total data.

Benefits:

- Distributes storage requirements.
- Increases aggregate processing capacity.
- Enables horizontal scaling.

### 5.2 What Is a Replica?

A replica is a copy of a shard's data.

Replication improves availability and provides redundancy.

For example, three shards with two replicas:

```
                  Cluster
                     |
        +------------+------------+
        |            |            |
        v            v            v
     Shard 1      Shard 2      Shard 3
        |            |            |
     +--+--+      +--+--+      +--+--+
     |     |      |     |      |     |
     v     v      v     v      v     v
    N1    N2     N3    N4     N5    N6
    R1    R2     R1    R2     R1    R2
```

This topology requires six ClickHouse instances.

Each shard has two replicas.

### 5.3 Sharding vs Replication

| Feature            | Sharding               | Replication                      |
| ------------------ | ---------------------- | -------------------------------- |
| Purpose            | Distribute data        | Copy data                        |
| Main benefit       | Scalability            | Availability                     |
| Storage            | Different data subsets | Same shard data                  |
| Failure protection | Not by itself          | Yes, if another replica survives |
| Scaling            | Horizontal capacity    | Redundancy and read capacity     |

**Remember:**

- Shard = Different data.
- Replica = Copy of the same data.

### 5.4 Distributed Table

ClickHouse provides the `Distributed` table engine to query multiple shards as one logical table.

Example:

```sql
CREATE TABLE logs_distributed
AS application_logs
ENGINE = Distributed(
    logs_cluster,
    default,
    application_logs,
    cityHash64(service_name)
);
```

Parameters:

1. `logs_cluster`: Cluster name defined in the ClickHouse configuration.
2. `default`: Database name.
3. `application_logs`: Local table name on each shard.
4. `cityHash64(service_name)`: Sharding key used to distribute inserted rows.

A query against the Distributed table can access data across the cluster:

```sql
SELECT
    service_name,
    count()
FROM logs_distributed
GROUP BY service_name;
```

ClickHouse distributes the query across the shards and combines the results.

**Important:** A Distributed table is a query and routing layer. It does not physically store the underlying data.

## 6. ClickHouse and ClickHouse Keeper

Distributed ClickHouse deployments need coordination for replicated tables.

ClickHouse Keeper provides this functionality.

Its responsibilities include:

- Managing replication metadata.
- Coordinating replica operations.
- Maintaining distributed synchronization.
- Tracking replicated data parts.
- Managing distributed DDL operations.

ClickHouse Keeper is compatible with the ZooKeeper coordination protocol.

Typical architecture:

```
              ClickHouse Keeper
                  Cluster
                     |
          +----------+----------+
          |          |          |
          v          v          v
        Node 1     Node 2     Node 3
          |          |          |
          v          v          v
        Replica   Replica    Replica
```

Keeper is not responsible for storing the actual ClickHouse table data.

It coordinates metadata and distributed operations.

## 7. ClickHouse Data Types

ClickHouse supports many specialized data types.

Some commonly used types:

|Type|Description|
|---|---|
|UInt8|Unsigned 8-bit integer|
|UInt32|Unsigned 32-bit integer|
|UInt64|Unsigned 64-bit integer|
|Int64|Signed 64-bit integer|
|Float64|64-bit floating-point number|
|String|Variable-length string|
|Date|Date|
|DateTime|Date and time|
|DateTime64|Date and time with sub-second precision|
|IPv4|IPv4 address|
|IPv6|IPv6 address|
|LowCardinality(String)|Optimized storage for low-cardinality strings|
|Array|Array of values|
|Map|Key-value collection|
|JSON|JSON data|

Example:

```sql
CREATE TABLE system_logs
(
    event_time DateTime64(3),
    client_ip IPv4,
    service_name LowCardinality(String),
    level LowCardinality(String),
    status_code UInt16,
    message String
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(event_time)
ORDER BY (event_time, service_name);
```

Choosing appropriate data types is important for storage efficiency and query performance.

## 8. SQL Operations

ClickHouse supports SQL syntax familiar to MySQL and PostgreSQL users, although some operations behave differently.

### 8.1 INSERT

```sql
INSERT INTO system_logs
(
    event_time,
    client_ip,
    service_name,
    level,
    status_code,
    message
)
VALUES
(
    now(),
    '192.168.1.100',
    'user-service',
    'ERROR',
    500,
    'Database connection failed'
);
```

### 8.2 SELECT

```sql
SELECT * FROM system_logs LIMIT 10;
```

### 8.3 GROUP BY

```sql
SELECT
    service_name,
    count() AS total
FROM system_logs
GROUP BY service_name
ORDER BY total DESC;
```

### 8.4 Time-Based Aggregation

```sql
SELECT
    toStartOfHour(event_time) AS hour,
    count() AS total
FROM system_logs
GROUP BY hour
ORDER BY hour;
```

### 8.5 DELETE

ClickHouse supports mutations, but they are not equivalent to ordinary transactional row deletion in MySQL.

For example:

```sql
ALTER TABLE system_logs
DELETE WHERE level = 'DEBUG';
```

This is an asynchronous mutation that rewrites affected data parts.

For large-scale data retention, partition deletion is often more efficient.

## 9. Data Retention and TTL

TTL stands for Time To Live.

It allows ClickHouse to automatically expire old data.

Example:

```sql
CREATE TABLE system_logs
(
    event_time DateTime,
    service_name String,
    message String
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(event_time)
ORDER BY (event_time, service_name)
TTL event_time + INTERVAL 180 DAY;
```

This means records become eligible for removal after 180 days.

TTL processing is performed during background operations, so expiration is not necessarily immediate.

For log platforms, TTL is particularly useful because log data usually has a defined retention period.

## 10. Kafka Integration

ClickHouse supports Kafka integration through the Kafka table engine and materialized views.

A typical ingestion architecture:

```text
       Application Systems
                |
                v
              Kafka
                |
                v
       ClickHouse Kafka Table
                |
                v
        Materialized View
                |
                v
        MergeTree Table
                |
                v
          Log Analytics
```

### 10.1 Kafka Engine

The Kafka engine allows ClickHouse to consume messages from Kafka topics.

Example:

```sql
CREATE TABLE kafka_logs
(
    event_time DateTime,
    service_name String,
    level String,
    message String
)
ENGINE = Kafka
SETTINGS
    kafka_broker_list = 'kafka01:9092,kafka02:9092,kafka03:9092',
    kafka_topic_list = 'application_logs',
    kafka_group_name = 'clickhouse_consumer',
    kafka_format = 'JSONEachRow';
```

This table acts as a Kafka consumer interface.

It is not a regular persistent MergeTree table.

### 10.2 Materialized View

A materialized view transfers incoming Kafka messages into a persistent table.

First, create the destination table:

```sql
CREATE TABLE application_logs
(
    event_time DateTime,
    service_name String,
    level String,
    message String
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(event_time)
ORDER BY (event_time, service_name);
```

Then create a materialized view:

```sql
CREATE MATERIALIZED VIEW kafka_logs_mv
TO application_logs
AS
SELECT
    event_time,
    service_name,
    level,
    message
FROM kafka_logs;
```

The ingestion process becomes:

1. Kafka receives messages.
2. ClickHouse consumes Kafka messages.
3. The materialized view processes incoming blocks.
4. Data is inserted into the MergeTree table.
5. Users query the persistent table.

### 10.3 Important Considerations

- Kafka ingestion is asynchronous.
- Kafka consumer offsets are managed by the Kafka engine.
- Delivery and retry behavior need to be considered when designing ingestion.
- Duplicates can occur, so do not assume exactly-once insertion.
- Invalid data should be handled explicitly.
- Monitor Kafka consumer lag and ClickHouse ingestion errors.

## 11. ClickHouse vs Elasticsearch vs VictoriaMetrics

These databases solve different problems.

| Feature                 | ClickHouse                           | Elasticsearch                       | VictoriaMetrics         |                    |
| ----------------------- | ------------------------------------ | ----------------------------------- | ----------------------- | ------------------ |
| Main purpose            | Analytical database                  | Search and log analytics            | Time-series monitoring  |                    |
| Storage model           | Column-oriented                      | Inverted index and document storage | Time-series optimized   |                    |
| Best workload           | Aggregation and analytics            | Full-text search                    | Metrics queries         |                    |
| SQL support             | Yes                                  | Elasticsearch SQL / ES              | QL                      | MetricsQL / PromQL |
| Full-text search        | Supported, but not its main strength | Excellent                           | Not designed for it     |                    |
| Log analysis            | Excellent                            | Excellent                           | Not its primary purpose |                    |
| Metrics monitoring      | Possible                             | Possible                            | Excellent               |                    |
| High-volume aggregation | Excellent                            | Good                                | Excellent for metrics   |                    |

### 11.1 ClickHouse vs Elasticsearch

Both can be used for log analytics.

However, their underlying architectures differ.

**Elasticsearch:**

- Built on Apache Lucene.
- Uses inverted indexes.
- Optimized for full-text search.
- Provides powerful document search capabilities.

**ClickHouse:**

- Uses column-oriented storage.
- Optimized for analytical queries.
- Provides efficient aggregation and filtering.
- Often offers better storage efficiency for analytical log workloads.

ClickHouse can replace Elasticsearch in some log-analysis architectures, but it is not a drop-in replacement.

If your primary requirement is full-text search across arbitrary log messages, Elasticsearch may still be preferable.

If your primary requirement is high-volume log storage, aggregation, filtering, and statistical analysis, ClickHouse is a strong option.

### 11.2 ClickHouse vs VictoriaMetrics

These systems are complementary.

VictoriaMetrics is designed for time-series metrics:

```
CPU Usage
Memory Usage
Disk I/O
Network Traffic
Request Rate
Error Rate
```

ClickHouse is suitable for structured event and log data:

```
Application Logs
System Logs
Audit Logs
Business Events
Access Logs
```

A monitoring platform can use both.

## 12. Useful ClickHouse Commands

### Check server version

```sql
SELECT version();
```

### Show databases

```sql
SHOW DATABASES;
```

### Show tables

```sql
SHOW TABLES;
```

### Show cluster configuration

```sql
SELECT * FROM system.clusters;
```

### Check cluster nodes

```sql
SELECT
    cluster,
    shard_num,
    replica_num,
    host_name,
    port
FROM system.clusters;
```

### Check tables

```sql
SELECT
    database,
    name,
    engine
FROM system.tables
WHERE database = 'default';
```

### Check MergeTree parts

```sql
SELECT
    database,
    table,
    count() AS parts,
    sum(rows) AS total_rows,
    formatReadableSize(sum(bytes_on_disk)) AS disk_size
FROM system.parts
WHERE active
GROUP BY database, table;
```

### Check replication status

```sql
SELECT
    database,
    table,
    is_leader,
    is_readonly,
    queue_size,
    absolute_delay
FROM system.replicas;
```

### Check Kafka consumer status

```sql
SELECT * FROM system.kafka_consumers;
```

## 13. Key Concepts to Remember

| Concept           | Meaning                                                   |
| ----------------- | --------------------------------------------------------- |
| Columnar Storage  | Stores data column by column                              |
| MergeTree         | Core ClickHouse storage engine family                     |
| Data Part         | Immutable data segment                                    |
| Background Merge  | Combines smaller parts into larger parts                  |
| ORDER BY          | Defines the sorting key                                   |
| Primary Key       | Helps skip irrelevant data ranges                         |
| PARTITION BY      | Divides data into partitions                              |
| Shard             | Stores a portion of the dataset                           |
| Replica           | Copy of a shard                                           |
| Distributed Table | Routes queries across shards                              |
| ClickHouse Keeper | Coordinates replication and distributed operations        |
| TTL               | Automatically expires old data                            |
| Kafka Engine      | Consumes Kafka messages                                   |
| Materialized View | Processes incoming data and writes to a destination table |


## 14. Official Documentation

- ClickHouse Official Website: [https://clickhouse.com/](https://clickhouse.com/)
- Documentation: [https://clickhouse.com/docs](https://clickhouse.com/docs)
- Architecture: [https://clickhouse.com/docs/architecture](https://clickhouse.com/docs/architecture)
- MergeTree Engine: [https://clickhouse.com/docs/engines/table-engines/mergetree-family/mergetree](https://clickhouse.com/docs/engines/table-engines/mergetree-family/mergetree)
- Distributed Engine: [https://clickhouse.com/docs/engines/table-engines/special/distributed](https://clickhouse.com/docs/engines/table-engines/special/distributed)
- Kafka Integration: [https://clickhouse.com/docs/integrations/kafka](https://clickhouse.com/docs/integrations/kafka)
- ClickHouse Keeper: [https://clickhouse.com/docs/guides/sre/keeper](https://clickhouse.com/docs/guides/sre/keeper)
