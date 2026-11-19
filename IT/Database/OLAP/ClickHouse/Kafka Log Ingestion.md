## 1. Architecture

### Cluster topology

- Nodes: 3
- Shards: 1
- Replicas: 3
- Storage engine: ReplicatedMergeTree
- Coordination: ClickHouse Keeper
- Kafka ingestion: clickhouse01
- Data retention: 180 days

```
                    LogEase
                       |
                       v
                 Kafka Cluster
                  Topic: logs
                       |
                       v
                 clickhouse01
                       |
                  Kafka Engine
                       |
                Materialized View
                       |
                       v
                ReplicatedMergeTree
                       |
              ClickHouse Keeper
                       |
           +-----------+-----------+
           |           |           |
           v           v           v
      clickhouse01 clickhouse02 clickhouse03
       Replica 01   Replica 02   Replica 03
           |           |           |
           +-----------+-----------+
                       |
                       v
                Distributed Table
                       |
                       v
                  Log Analysis
```

### Component responsibilities

|Component|Responsibility|
|---|---|
|LogEase|Collects and forwards logs|
|Kafka|Buffers and distributes messages|
|Kafka Engine|Consumes Kafka messages|
|Materialized View|Transforms and forwards messages|
|ReplicatedMergeTree|Stores and replicates data|
|ClickHouse Keeper|Coordinates replication|
|Distributed|Provides a unified query interface|

**Important:** Only `clickhouse01` hosts the Kafka ingestion pipeline initially. The other two nodes receive data through ReplicatedMergeTree replication.

---

## 2. Cluster Configuration

### 2.1 remote_servers.xml

Apply the same configuration on all three nodes.

```
<remote_servers>
    <logs_cluster>
        <shard>
            <internal_replication>true</internal_replication>

            <replica>
                <host>clickhouse01</host>
                <port>9000</port>
            </replica>

            <replica>
                <host>clickhouse02</host>
                <port>9000</port>
            </replica>

            <replica>
                <host>clickhouse03</host>
                <port>9000</port>
            </replica>
        </shard>
    </logs_cluster>
</remote_servers>
```

### 2.2 Node macros

Configure different replica identifiers on each node.

**clickhouse01**

```
<macros>
    <shard>01</shard>
    <replica>clickhouse01</replica>
</macros>
```

**clickhouse02**

```
<macros>
    <shard>01</shard>
    <replica>clickhouse02</replica>
</macros>
```

**clickhouse03**

```
<macros>
    <shard>01</shard>
    <replica>clickhouse03</replica>
</macros>
```

All nodes must use the same ClickHouse Keeper cluster configuration.

### 2.3 Verify cluster topology

```
SELECT
    cluster,
    shard_num,
    replica_num,
    host_name,
    port,
    is_local
FROM system.clusters
WHERE cluster = 'logs_cluster'
ORDER BY shard_num, replica_num;
```

Expected: one shard containing three replicas.

---

## 3. Create Database

Execute on any node:

```
CREATE DATABASE IF NOT EXISTS logs
ON CLUSTER logs_cluster;
```

## 4. Create Destination Table

Create the local persistent table on all three nodes.

```
CREATE TABLE IF NOT EXISTS logs.cz_esmes_http_local
ON CLUSTER logs_cluster
(
    timestamp DateTime64(3, 'Asia/Shanghai'),

    id String,
    context_id UInt64,

    hostname LowCardinality(String),
    appname LowCardinality(String),
    service_instance_name String,

    source LowCardinality(String),
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
    '/clickhouse/tables/{shard}/logs/cz_esmes_http_local',
    '{replica}'
)
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY
(
    env,
    sourcetype,
    hostname,
    timestamp,
    id
)
TTL timestamp + INTERVAL 180 DAY;
```

### Design notes

- `ReplicatedMergeTree` maintains three copies of the same data.
    
- `{shard}` resolves to `01` on all nodes.
    
- `{replica}` resolves to each node's unique replica name.
    
- Daily partitions support time-based retention.
    
- TTL removes records older than 180 days during background merges.
    
- Sorting prioritizes environment, log type, hostname, and time-range filtering.
    

---

## 5. Create Kafka Engine Table

**Execute only on clickhouse01.**

Do not use `ON CLUSTER` for this table because we are deliberately using one ingestion node.

```
CREATE TABLE IF NOT EXISTS logs.cz_esmes_http_kafka
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

### Important

The Kafka table uses the actual JSON data types.

For example:

```
{
    "response_body_bytes": "453",
    "duration_ms": "258",
    "http_code": "200",
    "timestamp": 1794909170851
}
```

Numeric-looking strings must be declared as `String` in the Kafka table and converted by the Materialized View.

---

## 6. Create Materialized View

**Execute only on clickhouse01.**

The Materialized View converts incoming messages and inserts them into the local ReplicatedMergeTree table.

```
CREATE MATERIALIZED VIEW IF NOT EXISTS logs.cz_esmes_http_mv
TO logs.cz_esmes_http_local
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

    toIPv4OrDefault(client_ip) AS client_ip,
    toIPv4OrDefault(ip) AS ip,

    host,
    vhost,

    method,
    uri,
    http_version,

    toUInt16OrZero(http_code) AS http_code,

    toUInt32OrZero(duration_ms) AS duration_ms,
    toUInt64OrZero(response_body_bytes) AS response_body_bytes,
    toUInt64OrZero(response_total_bytes) AS response_total_bytes,

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

FROM logs.cz_esmes_http_kafka;
```

### Ingestion workflow

1. LogEase sends logs to Kafka.
    
2. `clickhouse01` consumes messages.
    
3. The Materialized View transforms the JSON fields.
    
4. Data is inserted into `cz_esmes_http_local`.
    
5. ReplicatedMergeTree replicates the inserted data to `clickhouse02` and `clickhouse03`.
    
6. All three nodes maintain the same dataset.
    

---

## 7. Create Distributed Table

Create the Distributed table on all three nodes.

```
CREATE TABLE IF NOT EXISTS logs.cz_esmes_http
ON CLUSTER logs_cluster
AS logs.cz_esmes_http_local
ENGINE = Distributed(
    logs_cluster,
    logs,
    cz_esmes_http_local,
    cityHash64(id)
);
```

Because the cluster has only one shard, the sharding key does not distribute data across multiple shards. It is retained for compatibility with future topology changes.

### Final table structure

|Table|Engine|Purpose|
|---|---|---|
|cz_esmes_http_kafka|Kafka|Consume messages|
|cz_esmes_http_mv|Materialized View|Transform messages|
|cz_esmes_http_local|ReplicatedMergeTree|Persist and replicate data|
||||