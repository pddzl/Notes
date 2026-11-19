## 1. Kafka ingestion options

The discussed data flow is:

```text
LogEase
   |
   | selected logs
   v
Kafka topics
   |
   +------------------------------+
   |                              |
   v                              v
ClickHouse Kafka Engine       External Go/Python consumer
   |                              |
   v                              v
Materialized View             Parse / clean / transform
   |                              |
   v                              v
ReplicatedMergeTree <-------------+
   |
   v
Distributed query table
```

Choose one ingestion pattern based on where you want parsing and transformation to happen.

## 1.1 Option A: ClickHouse Kafka Engine plus Materialized View

This lets ClickHouse consume Kafka topics and insert rows into a regular MergeTree-family table.

Example Kafka source table (adjust broker, topic, consumer group, and format):

```sql
CREATE TABLE logs.kafka_logs
(
    event_time DateTime64(3, 'UTC'),
    host String,
    service String,
    level String,
    message String
)
ENGINE = Kafka
SETTINGS
    kafka_broker_list = 'KAFKA_BROKER_1:9092,KAFKA_BROKER_2:9092',
    kafka_topic_list = 'application-logs',
    kafka_group_name = 'clickhouse-logs-consumer',
    kafka_format = 'JSONEachRow',
    kafka_num_consumers = 2;
```

Create a materialized view to move parsed rows into the replicated table:

```sql
CREATE MATERIALIZED VIEW logs.kafka_logs_mv
TO logs.logs_local
AS
SELECT
    event_time,
    host,
    service,
    level,
    message
FROM logs.kafka_logs;
```

Important:
- The Kafka message format must match the table schema.
- The example assumes JSONEachRow messages with all listed fields.
- Kafka authentication, TLS, error handling, and consumer tuning may need additional settings.
- Do not create multiple competing consumers accidentally. Decide whether one Kafka Engine table per topic/consumer group is appropriate for your deployment.
- Validate delivery and retry behavior under failures before relying on this path for production.

## 1.2 Option B: external log-cleaning process

If your existing process reads Kafka, cleans/transforms records, and writes to ClickHouse, it can insert directly into `logs.logs_all` or the local table, depending on your routing design.

Advantages:
- Transformation logic remains in your application.
- Easier to implement custom validation, enrichment, and error routing.
- The process can use the ClickHouse HTTP or native interface.

Make sure the writer handles retries and duplicate delivery appropriately. For batch inserts, use a suitable batch size rather than inserting one log record per request.

Do not run both ingestion approaches for the same Kafka topic unless duplicate ingestion is intentional and controlled.

ClickHouse's **Kafka Engine + Materialized View (MV)** allows ClickHouse to consume Kafka messages automatically, transform JSON fields, and insert the results into a MergeTree table.

The biggest advantage is that **you don't need to write a Go Kafka consumer**. ClickHouse handles Kafka consumption in the background.

For your logging platform, the architecture would look like this:

**LogEase**

**Kafka Topic**

logs

**ClickHouse Kafka Engine**

Consumes JSON messages

**Materialized View**

Extracts and transforms JSON fields

**MergeTree Destination Table**

Stores persistent log data

**Distributed Table**

Queries across 3 shards

There are three important objects:

|Object|Responsibility|
|---|---|
|Kafka Engine table|Reads messages from Kafka|
|Materialized View|Transforms and forwards messages|
|MergeTree table|Permanently stores messages|

One clarification: ClickHouse doesn't automatically create all three objects just because you enable Kafka Engine. You create them using SQL. You can, however, let a materialized view create its own internal destination table by omitting `TO`; I'll show both approaches.

## 2. Prepare the Kafka topic

I'll assume:

- Kafka topic: `logs`
- Kafka brokers: `192.168.1.101:9092,192.168.1.102:9092,192.168.1.103:9092`
- Kafka message format: `JSONEachRow`
- ClickHouse database: `logs`
- ClickHouse cluster: `logs_cluster`

Replace the broker addresses with your actual Kafka addresses.

Your Kafka message is already a JSON object, so `JSONEachRow` is the appropriate format. Each Kafka message represents one JSON row.

## 3. Create the destination table

This is the actual table where your logs will be stored.

Execute:

```sql
CREATE DATABASE IF NOT EXISTS logs
ON CLUSTER logs_cluster;
```

Then create the local table:

```sql
CREATE TABLE IF NOT EXISTS logs.http_logs_local
ON CLUSTER logs_cluster
(
    timestamp DateTime64(3, 'Asia/Shanghai'),

    id String,
    context_id UInt64,

    hostname LowCardinality(String),
    appname String,
    service_instance_name String,

    source String,
    sourcetype LowCardinality(String),
    logical_index LowCardinality(String),
    `index` LowCardinality(String),

    env LowCardinality(String),
    domain LowCardinality(String),
    tag Array(String),

    client_ip IPv4,
    ip IPv4,
    host String,
    vhost LowCardinality(String),

    method LowCardinality(String),
    uri String,
    http_version LowCardinality(String),
    http_code UInt16,

    duration_ms UInt32,
    response_body_bytes UInt64,
    response_total_bytes UInt64,

    process_info String,
    raw_message String,
    raw_message_length UInt32,

    agent_send_timestamp DateTime64(3, 'Asia/Shanghai'),
    collector_recv_timestamp DateTime64(3, 'Asia/Shanghai'),

    ingested_at DateTime64(3, 'Asia/Shanghai')
        DEFAULT now64(3)
)
ENGINE = ReplicatedMergeTree(
    '/clickhouse/tables/{shard}/logs/http_logs_local',
    '{replica}'
)
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (env, sourcetype, hostname, timestamp, id)
TTL timestamp + INTERVAL 180 DAY;
```

This table is replicated across your six ClickHouse instances.

## 4. Create the Kafka Engine table

This is the most important part of the ingestion process.

The Kafka Engine table is not a normal storage table. It acts as a Kafka consumer.

```sql
CREATE TABLE logs.http_logs_kafka
ON CLUSTER logs_cluster
(
    raw_message String,
    source String,
    hostname String,
    response_body_bytes String,
    appname String,
    host String,
    client_ip String,
    sourcetype String,
    tag Array(String),
    id String,
    service_instance_name String,

    timestamp UInt64,
    response_total_bytes String,
    agent_send_timestamp UInt64,
    method String,
    collector_recv_timestamp UInt64,
    ip String,
    http_version String,
    `index` String,
    env String,
    uri String,
    logical_index String,
    duration_ms String,
    vhost String,
    context_id UInt64,
    http_code String,
    process_info String,
    domain String,
    raw_message_length UInt32
)
ENGINE = Kafka
SETTINGS
    kafka_broker_list =
        '192.168.1.101:9092,192.168.1.102:9092,192.168.1.103:9092',
    kafka_topic_list = 'logs',
    kafka_group_name = 'clickhouse_logs_consumer',
    kafka_format = 'JSONEachRow',
    kafka_num_consumers = 1;
```

A few details worth understanding:

**Why are some fields String instead of UInt64?**

Look at your original message:

```
{
  "response_body_bytes": "453",
  "duration_ms": "258",
  "http_code": "200",
  "timestamp": 1794909170851
}
```

The first three values are JSON strings, while `timestamp` is a JSON number.

Therefore, I define the Kafka staging table according to the actual JSON types, then convert the values when inserting into the destination table.

**What is** `kafka_group_name`**?**

It's the Kafka consumer group ID.

All six ClickHouse nodes should use the same group name so Kafka distributes topic partitions among them rather than making every node consume the entire topic independently.

GitHub+1

## 5. Create the Materialized View

Now connect the Kafka Engine table to the destination table.

```sql
CREATE MATERIALIZED VIEW logs.http_logs_mv
ON CLUSTER logs_cluster
TO logs.http_logs_local
AS
SELECT
    fromUnixTimestamp64Milli(
        toInt64(timestamp),
        'Asia/Shanghai'
    ) AS timestamp,

    id,
    context_id,

    hostname,
    appname,
    service_instance_name,

    source,
    sourcetype,
    logical_index,
    `index`,

    env,
    domain,
    tag,

    toIPv4(client_ip) AS client_ip,
    toIPv4(ip) AS ip,
    host,
    vhost,

    method,
    uri,
    http_version,
    toUInt16(http_code) AS http_code,

    toUInt32(duration_ms) AS duration_ms,
    toUInt64(response_body_bytes) AS response_body_bytes,
    toUInt64(response_total_bytes) AS response_total_bytes,

    process_info,
    raw_message,
    raw_message_length,

    fromUnixTimestamp64Milli(
        toInt64(agent_send_timestamp),
        'Asia/Shanghai'
    ) AS agent_send_timestamp,

    fromUnixTimestamp64Milli(
        toInt64(collector_recv_timestamp),
        'Asia/Shanghai'
    ) AS collector_recv_timestamp

FROM logs.http_logs_kafka;
```

That's it!

You don't need to run a Go consumer, poll Kafka, or manually insert each message.

The process is now:

1. Kafka receives a message.
2. ClickHouse Kafka Engine consumes it.
3. Materialized View executes its SELECT statement.
4. Data is converted into the destination schema.
5. Data is inserted into `http_logs_local`.
6. ReplicatedMergeTree replicates the data to the other replica.

The MV runs continuously in the background.

## 6. Create the Distributed table

Your application and users should query a Distributed table rather than individual local tables.

```
CREATE TABLE logs.http_logs
ON CLUSTER logs_cluster
AS logs.http_logs_local
ENGINE = Distributed(
    logs_cluster,
    logs,
    http_logs_local,
    cityHash64(hostname)
);
```

Now you have:

|Table|Engine|Purpose|
|---|---|---|
|`http_logs_kafka`|Kafka|Consume Kafka messages|
|`http_logs_mv`|Materialized View|Transform and forward messages|
|`http_logs_local`|ReplicatedMergeTree|Persist logs|
|`http_logs`|Distributed|Query all shards|

## 7. Verify ingestion

First, check the Kafka Engine table:

```sql
SELECT * FROM logs.http_logs_kafka LIMIT 10;
```

**Warning:** Don't use this query for routine monitoring. A direct SELECT from a Kafka Engine table consumes messages and advances Kafka offsets.

Instead, check the destination table:

```sql
SELECT count() FROM logs.http_logs;
```

Check the latest messages:

```sql
SELECT
    timestamp,
    hostname,
    appname,
    method,
    uri,
    http_code,
    duration_ms
FROM logs.http_logs
ORDER BY timestamp DESC
LIMIT 20;
```

Check Kafka ingestion by application:

```sql
SELECT
    appname,
    count() AS total_requests,
    avg(duration_ms) AS avg_duration,
    max(duration_ms) AS max_duration
FROM logs.http_logs
WHERE timestamp >= now() - INTERVAL 1 HOUR
GROUP BY appname
ORDER BY total_requests DESC;
```

## 8. What if I want ClickHouse to automatically create the destination table?

There is another syntax:

```sql
CREATE MATERIALIZED VIEW logs.http_logs_mv
ENGINE = MergeTree
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (hostname, timestamp)
AS
SELECT
    timestamp,
    hostname,
    method,
    uri,
    http_code
FROM logs.http_logs_kafka;
```

Notice that there is no `TO logs.http_logs_local`.

In this case, ClickHouse creates an internal destination table associated with the materialized view.

However, I don't recommend this for your production cluster because:

- You have less control over the destination table.
- Managing replication becomes less straightforward.
- You cannot easily manage the destination table independently.

For your architecture, explicitly creating the destination table and using `TO` is better.

GitHub+1

## 9. Important considerations for your 3-shard, 2-replica cluster

My recommendation

Your cluster has six ClickHouse instances:

**Shard** **1**

Replica 1

Kafka consumer

Replica 2

Kafka consumer

**Shard** **2**

Replica 1

Kafka consumer

Replica 2

Kafka consumer

**Shard** **3**

Replica 1

Kafka consumer

Replica 2

Kafka consumer

All six nodes share the same Kafka consumer group.

There are three things to pay attention to:

1. **Same consumer group:** All six Kafka Engine tables must use `clickhouse_logs_consumer`. Otherwise, each different group may consume the same messages independently.
2. **Kafka partitions:** With six nodes and one consumer per node, ideally your Kafka topic should have at least six partitions to use all six consumers concurrently.
3. **Replication:** Each node inserts into its local ReplicatedMergeTree table. Its replica receives the data through ClickHouse replication.

The Kafka Engine documentation describes how multiple table instances using the same consumer group distribute topic partitions.

One more production consideration: design for possible duplicate ingestion during failure and retry scenarios. Don't assume Kafka consumption and ClickHouse storage provide end-to-end exactly-once delivery.

## 10. Kafka Engine vs Go Consumer: Which should you choose?

For your 50–200 GB/day logging platform:

|Consideration|Kafka Engine + MV|Go Consumer|
|---|---|---|
|Development|Simple|More work|
|Data transformation|SQL|Go code|
|Performance|High|High|
|Error handling|Less flexible|More flexible|
|Complex business logic|Limited|Excellent|
|External API calls|No|Yes|
|Operational maintenance|Relatively simple|More components|

**My recommendation:** Start with Kafka Engine + Materialized View if your primary job is JSON-to-ClickHouse ingestion and straightforward data conversion.

If you later need complicated log parsing, enrichment, deduplication, routing, or integration with other systems, consider Go.

For your current logging architecture, I'd first test Kafka Engine with one topic and one destination table before rolling it out across all six nodes.