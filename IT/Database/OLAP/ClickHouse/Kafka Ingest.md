## 1. Kafka ingestion options

The discussed data flow is:

```text
LogEase
   |
   | selected logs
   v
Kafka topic (logs)
   |
   +------------------------------------------+
   |                                          |
   v                                          v
ClickHouse Kafka Engine                External Go/Python consumer
   | [consumes JSON messages]               |
   v                                        v
Materialized View                      Parse / clean / transform
   | [extracts and transforms               |
   | JSON fields]                           |
   v                                        v
ReplicatedMergeTree <-----------------------+
   | [stores persistent log data]
   v
Distributed table -- queries across the cluster (1 shard, 3 replicas)
```

Choose one ingestion pattern based on where you want parsing and transformation to happen.

The Kafka Engine + Materialized View path involves four important objects:

|Table|Engine|Purpose|
|---|---|---|
|`HA_SlicingMES_HTTP_KAFKA`|Kafka|Consume Kafka messages|
|`HA_SlicingMES_HTTP_MV`|Materialized View|Transform and forward messages|
|`HA_SlicingMES_HTTP`|ReplicatedMergeTree|Persist logs|
|`HA_SlicingMES_HTTP_ALL`|Distributed|Query all shards|

One clarification: ClickHouse doesn't automatically create any of these objects just because you enable Kafka Engine. You create them using SQL. There is, however, an alternative syntax that lets a materialized view create its own internal destination table by omitting `TO`; see section 6.

### 1.1 Option A: ClickHouse Kafka Engine plus Materialized View

This lets ClickHouse consume Kafka topics and insert rows into a regular MergeTree-family table.

The biggest advantage is that **you don't need to write a Go Kafka consumer**. ClickHouse handles Kafka consumption in the background.

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

### 1.2 Option B: external log-cleaning process

If your existing process reads Kafka, cleans/transforms records, and writes to ClickHouse, it can insert directly into `logs.logs_all` or the local table, depending on your routing design.

Advantages:
- Transformation logic remains in your application.
- Easier to implement custom validation, enrichment, and error routing.
- The process can use the ClickHouse HTTP or native interface.

Make sure the writer handles retries and duplicate delivery appropriately. For batch inserts, use a suitable batch size rather than inserting one log record per request.

Do not run both ingestion approaches for the same Kafka topic unless duplicate ingestion is intentional and controlled.

### 1.3 Kafka Engine vs Go Consumer: Which should you choose?

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

For your current logging architecture, I'd first test Kafka Engine with one topic and one destination table before rolling it out across all three nodes.

## 2. Prepare the Kafka topic

I'll assume:

- Kafka topic: `logs`
- Kafka brokers: `192.168.1.101:9092,192.168.1.102:9092,192.168.1.103:9092`
- Kafka message format: `JSONEachRow`
- ClickHouse database: `logs`
- ClickHouse cluster: `logs_cluster`

Replace the broker addresses with your actual Kafka addresses.

Your Kafka message is already a JSON object, so `JSONEachRow` is the appropriate format. Each Kafka message represents one JSON row.

The topic message format is:

```json
{
  "agent_send_timestamp" : 1795072826202,
  "collector_recv_timestamp" : 1795072827982,
  "raw_message" : "10.16.33.255 - - [19/Nov/2026:15:20:23 +0800] \"GET /sweetMes/basisBill/bill HTTP/1.1\" 200 181 \"http://s1-ha.test.com/\" \"-\" \"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36 Edg/157.0.0.0\" \"-\" 0.004",
  "ip" : "10.16.3.56",
  "index" : "ops-yotta-20261119",
  "source" : "/usr/local/nginx-1.20.2/nginx.log",
  "nginx_access" : {
    "http_method" : "GET",
    "request_time" : "0.004",
    "request_timestamp" : "19/Nov/2026:15:20:23 +0800",
    "http_code" : "200",
    "size" : "181",
    "http_referer" : "http://s1-ha.test.com/",
    "http_x_forwarded_for" : "-",
    "client_ip" : "10.16.33.255",
    "http_request" : "GET /sweetMes/basisBill/bill HTTP/1.1",
    "uri" : "/sweetMes/basisBill/bill",
    "user_agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36 Edg/157.0.0.0"
  },
  "logical_index" : "yotta",
  "logtype" : "nginx_access",
  "hostname" : "tshawnginx01",
  "appname" : "ISC_HA_SlicingMES_PRD__Nginx__tshawnginx01__1001",
  "domain" : "ops",
  "context_id" : 1795072826202613965,
  "tag" : [
    "HA_SlicingMES"
  ],
  "id" : "AaHyrZtakdUujX9cLmb9",
  "raw_message_length" : 271,
  "timestamp" : 1795072826202
}
```

## 3. Create the destination table

This is the actual table where your logs will be stored.

Execute:

```sql
CREATE DATABASE IF NOT EXISTS logs
ON CLUSTER logs_cluster;
```

Then create the local table — on **all three nodes**, so every replica has it:

```sql
CREATE TABLE logs.HA_SlicingMES_HTTP
(
    `agent_send_timestamp` UInt64,
    `collector_recv_timestamp` UInt64,
    `raw_message` String,
    `raw_message_length` UInt32,
    `ip` IPv4,
    `index` String,
    `source` String,
    `http_method` LowCardinality(String),
    `request_time` Float64,
    `request_timestamp` String,
    `http_code` UInt16,
    `size` UInt64,
    `http_referer` String,
    `http_x_forwarded_for` String,
    `client_ip` IPv4,
    `http_request` String,
    `uri` String,
    `user_agent` String,
    `logical_index` LowCardinality(String),
    `logtype` LowCardinality(String),
    `hostname` LowCardinality(String),
    `appname` String,
    `domain` LowCardinality(String),
    `context_id` UInt64,
    `tag` Array(String),
    `id` String,
    `timestamp` DateTime64(3, 'Asia/Shanghai'),
    INDEX idx_uri uri TYPE bloom_filter GRANULARITY 4,
    INDEX idx_client_ip client_ip TYPE bloom_filter GRANULARITY 4
)
ENGINE = ReplicatedMergeTree('/clickhouse/tables/{shard}/logs/HA_SlicingMES_HTTP', '{replica}')
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (logtype, hostname, timestamp, id)
TTL timestamp + toIntervalDay(180)
SETTINGS index_granularity = 8192
```

This table is replicated across your three ClickHouse instances.

## 4. Create the Kafka Engine table

> **Note:** Create it on one or more nodes. To run multiple Kafka consumers, create the table on each node — all instances must use the same `kafka_group_name`, so Kafka distributes topic partitions among them. Different group names would each consume the whole topic independently and generate duplicate data.

This is the most important part of the ingestion process.

The Kafka Engine table is not a normal storage table. It acts as a Kafka consumer.

```sql
CREATE TABLE logs.HA_SlicingMES_HTTP_KAFKA  
(  
    `message` String  
)  
ENGINE = Kafka  
SETTINGS kafka_broker_list = '192.168.1.101:9092,192.168.1.102:9092,192.168.1.103:9092', kafka_topic_list = 'HA_SlicingMES_HTTP', kafka_group_name = 'clickhouse_HA_SlicingMES_HTTP', kafka_format = 'JSONAsString', kafka_num_consumers = 1
```

**What is** `kafka_group_name`**?**

It's the Kafka consumer group ID.

All three ClickHouse nodes should use the same group name so Kafka distributes topic partitions among them rather than making every node consume the entire topic independently.

## 5. Create the Materialized View

> **Note:** Create the MV on **every node that has a Kafka Engine table**. An MV only transforms messages consumed by the Kafka Engine table on the same node — if a node consumes messages without an MV, those messages are lost.

Now connect the Kafka Engine table to the destination table.

```sql
CREATE MATERIALIZED VIEW logs.HA_SlicingMES_HTTP_MV TO logs.HA_SlicingMES_HTTP
(
    `agent_send_timestamp` UInt64,
    `collector_recv_timestamp` UInt64,
    `raw_message` String,
    `raw_message_length` UInt32,
    `ip` IPv4,
    `index` String,
    `source` String,
    `http_method` String,
    `request_time` Float64,
    `request_timestamp` String,
    `http_code` UInt16,
    `size` UInt64,
    `http_referer` String,
    `http_x_forwarded_for` String,
    `client_ip` IPv4,
    `http_request` String,
    `uri` String,
    `user_agent` String,
    `logical_index` String,
    `logtype` String,
    `hostname` String,
    `appname` String,
    `domain` String,
    `context_id` UInt64,
    `tag` Array(String),
    `id` String,
    `timestamp` DateTime64(3, 'Asia/Shanghai')
)
AS SELECT
    JSONExtractUInt(message, 'agent_send_timestamp') AS agent_send_timestamp,
    JSONExtractUInt(message, 'collector_recv_timestamp') AS collector_recv_timestamp,
    JSONExtractString(message, 'raw_message') AS raw_message,
    toUInt32OrZero(JSONExtractString(message, 'raw_message_length')) AS raw_message_length,
    toIPv4OrDefault(JSONExtractString(message, 'ip')) AS ip,
    JSONExtractString(message, 'index') AS `index`,
    JSONExtractString(message, 'source') AS source,
    JSONExtractString(message, 'nginx_access', 'http_method') AS http_method,
    toFloat64OrZero(JSONExtractString(message, 'nginx_access', 'request_time')) AS request_time,
    JSONExtractString(message, 'nginx_access', 'request_timestamp') AS request_timestamp,
    toUInt16OrZero(JSONExtractString(message, 'nginx_access', 'http_code')) AS http_code,
    toUInt64OrZero(JSONExtractString(message, 'nginx_access', 'size')) AS size,
    JSONExtractString(message, 'nginx_access', 'http_referer') AS http_referer,
    JSONExtractString(message, 'nginx_access', 'http_x_forwarded_for') AS http_x_forwarded_for,
    toIPv4OrDefault(JSONExtractString(message, 'nginx_access', 'client_ip')) AS client_ip,
    JSONExtractString(message, 'nginx_access', 'http_request') AS http_request,
    JSONExtractString(message, 'nginx_access', 'uri') AS uri,
    JSONExtractString(message, 'nginx_access', 'user_agent') AS user_agent,
    JSONExtractString(message, 'logical_index') AS logical_index,
    JSONExtractString(message, 'logtype') AS logtype,
    JSONExtractString(message, 'hostname') AS hostname,
    JSONExtractString(message, 'appname') AS appname,
    JSONExtractString(message, 'domain') AS domain,
    JSONExtractUInt(message, 'context_id') AS context_id,
    JSONExtract(message, 'tag', 'Array(String)') AS tag,
    JSONExtractString(message, 'id') AS id,
    fromUnixTimestamp64Milli(toInt64(JSONExtractUInt(message, 'timestamp')), 'Asia/Shanghai') AS timestamp
FROM logs.HA_SlicingMES_HTTP_KAFKA
```

That's it!

You don't need to run a Go consumer, poll Kafka, or manually insert each message.

The process is now:

1. Kafka receives a message.
2. ClickHouse Kafka Engine consumes it.
3. Materialized View executes its SELECT statement.
4. Data is converted into the destination schema.
5. Data is inserted into `HA_SlicingMES_HTTP`.
6. ReplicatedMergeTree replicates the data to the other two replicas.

The MV runs continuously in the background.

## 6. Alternative: let ClickHouse automatically create the destination table

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

## 7. Create the Distributed table

Your application and users should query a Distributed table rather than individual local tables.

```sql
CREATE TABLE logs.HA_SlicingMES_HTTP_ALL
(
    `agent_send_timestamp` UInt64,
    `collector_recv_timestamp` UInt64,
    `raw_message` String,
    `raw_message_length` UInt32,
    `ip` IPv4,
    `index` String,
    `source` String,
    `http_method` LowCardinality(String),
    `request_time` Float64,
    `request_timestamp` String,
    `http_code` UInt16,
    `size` UInt64,
    `http_referer` String,
    `http_x_forwarded_for` String,
    `client_ip` IPv4,
    `http_request` String,
    `uri` String,
    `user_agent` String,
    `logical_index` LowCardinality(String),
    `logtype` LowCardinality(String),
    `hostname` LowCardinality(String),
    `appname` String,
    `domain` LowCardinality(String),
    `context_id` UInt64,
    `tag` Array(String),
    `id` String,
    `timestamp` DateTime64(3, 'Asia/Shanghai')
)
ENGINE = Distributed('logs_cluster', 'logs', 'HA_SlicingMES_HTTP', cityHash64(id))
```

## 8. Verify ingestion

First, check the Kafka Engine table:

```sql
SELECT * FROM logs.HA_SlicingMES_HTTP_KAFKA LIMIT 10;
```

**Warning:** Don't use this query for routine monitoring. A direct SELECT from a Kafka Engine table consumes messages and advances Kafka offsets.

Instead, check the destination table:

```sql
SELECT count() FROM logs.HA_SlicingMES_HTTP_ALL;
```

Check the latest messages:

```sql
SELECT
    timestamp,
    hostname,
    appname,
    http_method,
    uri,
    http_code,
    request_time
FROM logs.HA_SlicingMES_HTTP_ALL
ORDER BY timestamp DESC
LIMIT 20;
```

Check Kafka ingestion by application:

```sql
SELECT
    appname,
    count() AS total_requests,
    avg(request_time) AS avg_request_time,
    max(request_time) AS max_request_time
FROM logs.HA_SlicingMES_HTTP_ALL
WHERE timestamp >= now() - INTERVAL 1 HOUR
GROUP BY appname
ORDER BY total_requests DESC;
```

## 9. Important considerations for your 1-shard, 3-replica cluster

My recommendation

Your cluster has three ClickHouse instances:

**Shard** **1**

Replica 1

Kafka consumer

Replica 2

Kafka consumer

Replica 3

Kafka consumer

All three nodes share the same Kafka consumer group.

There are three things to pay attention to:

1. **Same consumer group:** All three Kafka Engine tables must use `clickhouse_HA_SlicingMES_HTTP`. Otherwise, each different group may consume the same messages independently.
2. **Kafka partitions:** With three nodes and one consumer per node, ideally your Kafka topic should have at least three partitions to use all three consumers concurrently.
3. **Replication:** Each node inserts into its local ReplicatedMergeTree table. Its replica receives the data through ClickHouse replication.

The Kafka Engine documentation describes how multiple table instances using the same consumer group distribute topic partitions.

One more production consideration: design for possible duplicate ingestion during failure and retry scenarios. Don't assume Kafka consumption and ClickHouse storage provide end-to-end exactly-once delivery.

## 10. Debugging the Kafka Engine

When the Kafka Engine table or the Materialized View doesn't behave as expected, start from the server log and recent errors.

Search the server log for Kafka-related messages and exceptions:

```sql
SELECT
    event_time,
    level,
    message
FROM system.text_log
WHERE event_time >= now() - INTERVAL 30 MINUTE
  AND (
      message ILIKE '%kafka%'
--       OR message ILIKE '%HA_SlicingMES%'
      OR message ILIKE '%exception%'
  )
ORDER BY event_time DESC
LIMIT 20;
```

> **Note:** `system.text_log` is only populated if it is enabled in the server config (`<text_log>` element). If the query returns nothing, enable it first and restart the server.

List recent server errors — the fastest way to spot MV insert failures:

```sql
SELECT
    name,
    code,
    value,
    last_error_time,
    last_error_message
FROM system.errors
WHERE value > 0
ORDER BY last_error_time DESC
LIMIT 20;
```