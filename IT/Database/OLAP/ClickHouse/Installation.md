# ClickHouse Installation and Three-Node Deployment Guide

**Platform:** Rocky Linux 9.8
**ClickHouse version observed:** 26.10.4
**Hosts:** `clickhouse01`, `clickhouse02`, `clickhouse03` 
**Example cluster name:** `logs_cluster`
**Use case:** Centralized log analytics and aggregation
**Retention target:** 180 days
**Related components:** Kafka, LogEase, ClickHouse Keeper, DataGrip

> This is an installation and deployment runbook based on the environment and requirements discussed. Replace example IP addresses, passwords, Kafka brokers, and storage paths with your actual values.

# 1. Architecture decisions before installation

## 1.1 The three physical VMs

| Host | ClickHouse | Keeper |
|---|---|---|
| `clickhouse01` | Yes | Yes |
| `clickhouse02` | Yes | Yes |
| `clickhouse03` | Yes | Yes |

Keeper is the coordination service used by replicated ClickHouse tables. A three-member Keeper ensemble can run on the three physical VMs. It does not need six members just because ClickHouse is configured with six server instances.

## 1.2 Important distinction: physical hosts, server instances, shards, replicas

A ClickHouse **server instance** is a running ClickHouse Server process with its own configuration, data directory, ports, and `{shard}` / `{replica}` macros.

A physical VM can run more than one ClickHouse instance, but two ports in a configuration do not automatically create a second instance. A second instance needs its own process and independent storage/configuration.

For a conventional replicated topology, each ClickHouse instance has one shard/replica identity for its replicated tables.

### Option A — One shard × two replicas

```text
                    logs_cluster
                         |
                Shard 1 (one copy of data)
                   /             \
                  /               \
             Replica 1        Replica 2
                CH01             CH02

      (clickhouse03 runs Keeper only)
```

| VM | Instance | Shard | Replica |
|---|---|---:|---|
| `clickhouse01` | One | 01 | `clickhouse01` |
| `clickhouse02` | One | 01 | `clickhouse02` |
| `clickhouse03` | None (Keeper only) | — | — |

Advantages:
- Stores only two copies of the data instead of three.
- Keeps replica redundancy across two physical VMs.
- Frees `clickhouse03` for other workloads or a lighter footprint.

Trade-offs:
- Still a single shard, so no horizontal scaling (same limitation as Option B).
- Less redundancy than Option B: if both replicas are down at the same time, the data is unavailable.
- Fewer ClickHouse instances overall means less total query and ingest capacity.

### Option B — Three instances: one shard × three replicas

```text
                    logs_cluster
                         |
                Shard 1 (one copy of data)
                  /       |       \
                 /        |        \
             Replica 1 Replica 2 Replica 3
                CH01      CH02      CH03
```

| VM | Instance | Shard | Replica |
|---|---|---:|---|
| `clickhouse01` | One | 01 | `clickhouse01` |
| `clickhouse02` | One | 01 | `clickhouse02` |
| `clickhouse03` | One | 01 | `clickhouse03` |

Advantages:
- Uses the three ClickHouse instances you currently have.
- Provides three copies of each replicated table.
- A single VM failure should leave two replicas available, assuming replication is healthy.

Trade-offs:
- There is only one shard, so this does not distribute the dataset across multiple shards for horizontal storage/query scaling.
- Three replicas consume roughly three copies of the compressed data, plus operational headroom.
- A single shard can become a query/ingest bottleneck.

This is the straightforward choice if you must keep exactly one ClickHouse instance on each of the three VMs and want replica redundancy.

### Option C — Three shards × two replicas

```text
                         logs_cluster

Shard 1                 Shard 2                 Shard 3
CH01 / Replica 1        CH01 / Replica 1        CH02 / Replica 1
CH02 / Replica 2        CH03 / Replica 2        CH03 / Replica 2
```

A placement that spreads each shard's replicas across different physical VMs is:

| Physical VM | Instance A | Instance B |
|---|---|---|
| `clickhouse01` | Shard 01, Replica 1 | Shard 02, Replica 1 |
| `clickhouse02` | Shard 01, Replica 2 | Shard 03, Replica 1 |
| `clickhouse03` | Shard 02, Replica 2 | Shard 03, Replica 2 |

This requires **six independent ClickHouse server instances**, two on each physical VM. Each instance needs:
- Its own configuration directory or clearly separated configuration files.
- Its own data and temporary directories.
- Its own server process and systemd service.
- Unique HTTP, native, and inter-server ports on the same VM.
- Its own `{shard}` and `{replica}` macros.

Keeper can still be the same three-node ensemble.

Advantages:
- Distributes data across three shards.
- Keeps two replicas of each shard on separate physical VMs.
- Provides horizontal data distribution and replica redundancy.

Trade-offs:
- More complicated operations and resource isolation.
- Two ClickHouse instances share CPU, RAM, disk, and network resources on each VM.
- The VM sizing must account for both instances.

### Recommendation for the current three-instance deployment

Do not configure three shards × two replicas by simply adding port `9001` to `remote_servers`. Port `9001` is only a port; it is not a second ClickHouse instance unless a second ClickHouse process is actually running there.

If you are keeping one ClickHouse process per VM, use **one shard × three replicas** (Option B) for replicated redundancy, or choose three shards × one replica if distribution is more important than replica-level availability. If two data copies are enough and one VM can go without a ClickHouse instance, choose **one shard × two replicas** (Option A). If you need both horizontal sharding and two replicas, plan for six instances (Option C).

# 2. Prepare all three Rocky Linux VMs

Perform the following on all three hosts.

## 2.1 Configure hostnames

On each VM, set its own hostname:

```bash
# On VM 1
hostnamectl set-hostname clickhouse01

# On VM 2
hostnamectl set-hostname clickhouse02

# On VM 3
hostnamectl set-hostname clickhouse03
```

Ensure all three hosts can resolve one another. If DNS is not configured, add the real private IPs to `/etc/hosts` on every VM:

```text
<CLICKHOUSE01_PRIVATE_IP> clickhouse01
<CLICKHOUSE02_PRIVATE_IP> clickhouse02
<CLICKHOUSE03_PRIVATE_IP> clickhouse03
```

Verify:

```bash
getent hosts clickhouse01
getent hosts clickhouse02
getent hosts clickhouse03
```

Also verify time synchronization. Consistent system time is important for logs, certificates, and operations:

```bash
timedatectl
```

## 2.2 Update the operating system

```bash
dnf update -y
dnf install -y chrony
systemctl enable --now chronyd
```

# 3. Install ClickHouse packages

Perform on all three VMs.

## 3.1 Add the official RPM repository

```bash
dnf install -y yum-utils
yum-config-manager --add-repo https://packages.clickhouse.com/rpm/clickhouse.repo
```

## 3.2 Install server, client, and Keeper

`clickhouse-keeper` is contained in `clickhouse-server` package

```bash
dnf install -y clickhouse-server clickhouse-client
```

Check versions:

```bash
clickhouse-server --version
clickhouse-client --version
clickhouse-keeper --version
```

Use the same ClickHouse version on all nodes. If you need a pinned version, inspect available package versions and install the same version on each VM rather than allowing the nodes to drift independently.

Do not start all services before their configuration is ready.

# 4. Configure the three-node ClickHouse Keeper ensemble

Keeper provides the coordination service used by replicated tables. Configure one Keeper member on each physical VM.

## 4.1 Keeper configuration

Create or edit:

```text
/etc/clickhouse-keeper/keeper_config.xml
```

Use the same Raft membership list on all three VMs. The `server_id` must be different on each VM.

### On clickhouse01

```xml
<clickhouse>
    <logger>
        <level>information</level>
        <log>/var/log/clickhouse-keeper/clickhouse-keeper.log</log>
        <errorlog>/var/log/clickhouse-keeper/clickhouse-keeper.err.log</errorlog>
        <size>1000M</size>
        <count>3</count>
    </logger>

    <listen_host>0.0.0.0</listen_host>

    <keeper_server>
        <tcp_port>9181</tcp_port>
        <server_id>1</server_id>

        <log_storage_path>/var/lib/clickhouse/coordination/log</log_storage_path>
        <snapshot_storage_path>/var/lib/clickhouse/coordination/snapshots</snapshot_storage_path>

        <raft_configuration>
            <server>
                <id>1</id>
                <hostname>clickhouse01</hostname>
                <port>9234</port>
            </server>
            <server>
                <id>2</id>
                <hostname>clickhouse02</hostname>
                <port>9234</port>
            </server>
            <server>
                <id>3</id>
                <hostname>clickhouse03</hostname>
                <port>9234</port>
            </server>
        </raft_configuration>
    </keeper_server>
</clickhouse>
```

### On clickhouse02

Use the same configuration, but change:

```xml
<server_id>2</server_id>
```

### On clickhouse03

Use the same configuration, but change:

```xml
<server_id>3</server_id>
```

The `server_id` must match the corresponding ID in the shared `raft_configuration`.

## 4.2 Start Keeper

On all three VMs:

```bash
systemctl enable clickhouse-keeper
systemctl start clickhouse-keeper
systemctl status clickhouse-keeper
```

Check logs if a node does not start:

```bash
journalctl -u clickhouse-keeper -n 100 --no-pager
```

The three Keeper members must be able to communicate with one another over TCP port `9234`. ClickHouse servers connect to Keeper over TCP port `9181`.

Do not proceed with replicated-table creation until the Keeper ensemble is healthy.

# 5. Configure ClickHouse to use Keeper

On each ClickHouse VM, create:

```text
/etc/clickhouse-server/config.d/keeper.xml
```

Use the same Keeper list on all three nodes:

```xml
<clickhouse>
    <zookeeper>
        <node>
            <host>clickhouse01</host>
            <port>9181</port>
        </node>
        <node>
            <host>clickhouse02</host>
            <port>9181</port>
        </node>
        <node>
            <host>clickhouse03</host>
            <port>9181</port>
        </node>
    </zookeeper>

    <distributed_ddl>
        <path>/clickhouse/task_queue/ddl</path>
    </distributed_ddl>
</clickhouse>
```

The `<zookeeper>` section is the ClickHouse configuration interface for a ZooKeeper-compatible coordination service; ClickHouse Keeper implements that protocol.

# 6. Configure the ClickHouse cluster

The examples in this section implement **Option B: one shard × three replicas**, matching one ClickHouse instance on each of the three VMs.

## 6.1 Allow remote connections

Create:

```text
/etc/clickhouse-server/config.d/network.xml
```

```xml
<clickhouse>
    <listen_host>0.0.0.0</listen_host>
    <interserver_http_port>9009</interserver_http_port>
    <interserver_http_host>clickhouse01</interserver_http_host>
</clickhouse>
```

On `clickhouse02`, set `<interserver_http_host>clickhouse02</interserver_http_host>`. On `clickhouse03`, set it to `clickhouse03`.

The inter-server host must resolve to the correct address from the other ClickHouse nodes.

## 6.2 Define `logs_cluster`

Create:

```text
/etc/clickhouse-server/config.d/cluster.xml
```

For one shard with three replicas:

```xml
<clickhouse>
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
</clickhouse>
```

`logs_cluster` is only the cluster name. It is not a database and is not created by SQL. ClickHouse loads it from the `remote_servers` configuration.

`internal_replication=true` tells the Distributed engine to send an insert to one replica of a shard and rely on the replicated table engine to replicate the data to the other replicas.

If the remote cluster connections require authentication, configure an appropriate dedicated inter-server/cluster user and credentials consistently. Do not put real passwords in documentation or source control.

## 6.3 Configure macros

Macros identify the shard and replica for replicated table paths.

Create:

```text
/etc/clickhouse-server/config.d/macros.xml
```

### clickhouse01

```xml
<clickhouse>
    <macros>
        <shard>01</shard>
        <replica>clickhouse01</replica>
    </macros>
</clickhouse>
```

### clickhouse02

```xml
<clickhouse>
    <macros>
        <shard>01</shard>
        <replica>clickhouse02</replica>
    </macros>
</clickhouse>
```

### clickhouse03

```xml
<clickhouse>
    <macros>
        <shard>01</shard>
        <replica>clickhouse03</replica>
    </macros>
</clickhouse>
```

All three nodes use shard `01`, because this example has one shard. Each replica value must be unique.

## 6.4 Start ClickHouse

After configuration is in place, start the server on all three nodes:

```bash
systemctl enable clickhouse-server
systemctl start clickhouse-server
systemctl status clickhouse-server
```

Check logs:

```bash
journalctl -u clickhouse-server -n 100 --no-pager
```

You can also inspect:

```bash
tail -n 100 /var/log/clickhouse-server/clickhouse-server.log
tail -n 100 /var/log/clickhouse-server/clickhouse-server.err.log
```

# 7. Configure the three-shard, two-replica topology (Option C)

This is an alternative design, not the configuration to use with only three ClickHouse processes.

To run three shards × two replicas on three physical VMs, deploy six independent ClickHouse instances:

| VM | Instance | Shard | Replica | Example native port |
|---|---|---:|---|---:|
| clickhouse01 | A | 01 | ch01_s1 | 9000 |
| clickhouse01 | B | 02 | ch01_s2 | 9001 |
| clickhouse02 | A | 01 | ch02_s1 | 9000 |
| clickhouse02 | B | 03 | ch02_s3 | 9001 |
| clickhouse03 | A | 02 | ch03_s2 | 9000 |
| clickhouse03 | B | 03 | ch03_s3 | 9001 |

Each instance also needs unique HTTP and inter-server ports on its host. For example:

| Instance on a VM | HTTP | Native | Inter-server HTTP |
|---|---:|---:|---:|
| Instance A | 8123 | 9000 | 9009 |
| Instance B | 8124 | 9001 | 9010 |

Each instance needs separate:
- `path` (data directory)
- `tmp_path`
- user/config overrides as appropriate
- `logger` paths
- macros
- server process and systemd unit

The `remote_servers` layout would have three shard groups, each with two replica entries. The two replicas in each shard must point to the two actual independent instances assigned to that shard.

Do not copy the three-node, one-instance-per-host `macros.xml` from Option B into this six-instance deployment. Every instance needs the macros for its own shard and replica identity.

A six-instance deployment requires a dedicated per-instance configuration and service design. Do not start a second process against the first process's data directory.

# 8. Verify the cluster

Run these queries after all three ClickHouse servers have started.

## 8.1 Check configured clusters

```sql
SELECT
    cluster,
    shard_num,
    replica_num,
    host_name,
    host_address,
    port
FROM system.clusters
WHERE cluster = 'logs_cluster'
ORDER BY shard_num, replica_num;
```

For Option B, expect one shard and three replicas.

List all configured clusters:

```sql
SELECT DISTINCT cluster
FROM system.clusters
ORDER BY cluster;
```

## 8.2 Check Keeper connectivity

```sql
SELECT *
FROM system.zookeeper
WHERE path = '/';
```

If the query succeeds, ClickHouse can communicate with Keeper. If it fails, inspect Keeper service status, network connectivity, and the `<zookeeper>` configuration.

## 8.3 Check replicated tables

After creating a replicated table, inspect:

```sql
SELECT
    database,
    table,
    is_leader,
    is_readonly,
    queue_size,
    inserts_in_queue,
    absolute_delay,
    zookeeper_path,
    replica_name
FROM system.replicas;
```

A healthy replica should normally not be read-only, and replication queues should eventually drain. Investigate nonzero delays or growing queues rather than assuming replication is healthy.

# 9. Create a database and replicated log table

The following is an example schema. Adapt the columns to the actual log format emitted by LogEase or your Kafka-cleaning process.

## 9.1 Create database across the cluster

```sql
CREATE DATABASE IF NOT EXISTS logs
ON CLUSTER logs_cluster;
```

## 9.2 Create the local replicated table

```sql
CREATE TABLE logs.logs_local
ON CLUSTER logs_cluster
(
    event_time DateTime64(3, 'UTC'),
    host String,
    service LowCardinality(String),
    level LowCardinality(String),
    message String
)
ENGINE = ReplicatedMergeTree(
    '/clickhouse/tables/{shard}/logs_local',
    '{replica}'
)
PARTITION BY toYYYYMMDD(event_time)
ORDER BY (service, event_time, host);
```

The path placeholders are substituted from each server's macros:
- `{shard}` becomes the shard identifier.
- `{replica}` becomes the replica identifier.

For Option B, all replicas use the same Keeper table path because they share the same shard, but each has a unique replica name.

## 9.3 Create the Distributed table

```sql
CREATE TABLE logs.logs_all
ON CLUSTER logs_cluster
AS logs.logs_local
ENGINE = Distributed(
    'logs_cluster',
    'logs',
    'logs_local',
    cityHash64(host)
);
```

The `Distributed` table provides a cluster-level query/insert interface. The local `ReplicatedMergeTree` table stores the actual data.

For a one-shard topology, the Distributed table still provides a convenient cluster-wide interface, but it does not create horizontal data distribution across multiple shards.

## 9.4 Test inserts and reads

```sql
INSERT INTO logs.logs_all
(
    event_time,
    host,
    service,
    level,
    message
)
VALUES
(
    now64(3),
    'test-host',
    'test-service',
    'INFO',
    'ClickHouse cluster test'
);
```

Query:

```sql
SELECT *
FROM logs.logs_all
ORDER BY event_time DESC
LIMIT 10;
```

Check which nodes have the row:

```sql
SELECT
    hostName() AS node,
    count() AS rows
FROM clusterAllReplicas('logs_cluster', 'logs', 'logs_local')
WHERE message = 'ClickHouse cluster test'
GROUP BY node
ORDER BY node;
```

For a replicated one-shard cluster, the row should eventually be present on all healthy replicas.

# 10. Configure 180-day retention

For the example table:

```sql
ALTER TABLE logs.logs_local
ON CLUSTER logs_cluster
MODIFY TTL event_time + INTERVAL 180 DAY;
```

Verify:

```sql
SHOW CREATE TABLE logs.logs_local;
```

TTL deletion is asynchronous. Expired rows are removed during background merges; they are not necessarily deleted exactly at the instant they reach 180 days.

Choose partitioning and ordering keys based on query patterns. Daily partitions can be convenient for log retention and partition operations, but very high partition counts and many small parts should be monitored.



# 12. User management and authentication

## 12.1 XML-backed `default` user

The `default` account was found in:

```text
/etc/clickhouse-server/users.xml
```

An XML-backed user is read-only to SQL account-management statements. Therefore this can fail:

```sql
ALTER USER default
IDENTIFIED WITH sha256_password BY '...';
```

with:

```text
Cannot update user `default` in users_xml because this storage is readonly.
```

To change an XML-backed user's password, edit the appropriate XML configuration file and restart/reload ClickHouse as required. Inspect all files under `users.d/` first to avoid conflicting definitions.

## 12.2 Inspect grants

```sql
SHOW GRANTS FOR default;
```

The earlier output showed many privileges, including user/role management and grant options, but a broad grant failed because the account did not have every privilege required by `GRANT ALL`.

The missing permission reported by the error was:

```text
SHOW NAMED COLLECTIONS SECRETS
```

Do not assume that `CREATE USER` or `ALTER USER` automatically means the account can grant every privilege represented by `ALL`.

## 12.3 SQL access management

ClickHouse supports SQL-managed users and roles. An XML-defined account can be configured to use SQL access management, but enabling access management does not magically give it every possible grant option.

A configuration file was discussed at:

```text
/etc/clickhouse-server/users.d/access-management.xml
```

Example settings that were proposed:

```xml
<clickhouse>
    <users>
        <default>
            <access_management>1</access_management>
            <named_collection_control>1</named_collection_control>
            <show_named_collections>1</show_named_collections>
            <show_named_collections_secrets>1</show_named_collections_secrets>
        </default>
    </users>
</clickhouse>
```

These settings have security implications, especially the ability to view named-collection secrets. Enable only what is required and only for trusted administrators.

After changing XML:

```bash
systemctl restart clickhouse-server
```

Then reconnect and inspect:

```sql
SHOW GRANTS FOR default;
```

Only after confirming the account has the necessary authority should you try creating a SQL-managed administrator.

## 12.4 Create a SQL-managed administrator

When the executing account has sufficient privileges:

```sql
CREATE USER admin
IDENTIFIED WITH sha256_password BY 'REPLACE_WITH_A_STRONG_SECRET';
```

For a full administrator, the intended grant is:

```sql
GRANT ALL ON *.* TO admin WITH GRANT OPTION;
```

If this fails, use the exact missing privilege from the error to diagnose the grant authority. Do not assume the command succeeded.

Verify:

```sql
SHOW USERS;
SHOW GRANTS FOR admin;
```

Test:

```bash
clickhouse-client --user admin --password
```

A SQL-managed user is stored in ClickHouse access-control storage and can be modified with SQL, subject to privileges.

## 12.5 Apply access configuration across the cluster

A local XML file on one VM does not automatically appear on the other two. Apply the corresponding configuration to each node if the user is locally defined there.

If you want SQL-managed users and roles replicated across the cluster, configure and verify ClickHouse's replicated access-management feature. Do not assume a user created on one node automatically exists on every node.

Keep `default` available until the new administrator is tested successfully. Do not lock yourself out by changing or disabling the only working account prematurely.

```sql
CREATE USER observeM ON CLUSTER logs_cluster IDENTIFIED WITH sha256_password BY 'observeM@2026!';

GRANT ALL ON *.* TO observeM ON CLUSTER logs_cluster;
```

# 13. DataGrip connectivity

The HTTP endpoint previously tested was:

```text
10.160.180.160:8123
```

The HTTP interface was confirmed working with:

```bash
curl "http://10.160.180.160:8123/?query=SELECT%201"
```

Expected output:

```text
1
```

And:

```bash
curl -v http://10.160.180.160:8123/ping
```

Expected response:

```text
Ok.
```

Suggested DataGrip settings:

| Setting | Value |
|---|---|
| Host | `10.160.180.160` |
| Port | `8123` |
| Protocol | HTTP |
| User | `default` or your SQL-managed account |
| Password | The configured password |
| Database | `default` |

An explicit HTTP JDBC URL was suggested:

```text
jdbc:clickhouse:http://10.160.180.160:8123/default
```

The error:

```text
Magic is not correct - expect [-126] but got [82]
```

can occur when the client/driver uses a protocol that does not match the port. Port `8123` is HTTP; port `9000` is the native ClickHouse protocol.

# 14. Firewall ports

Allow only the necessary traffic between trusted hosts and client networks.

| Port | Protocol | Purpose | Typical source |
|---:|---|---|---|
| 8123 | TCP | ClickHouse HTTP | Approved clients / applications |
| 9000 | TCP | ClickHouse native protocol | Approved clients and ClickHouse nodes |
| 9009 | TCP | ClickHouse inter-server HTTP | ClickHouse nodes |
| 9181 | TCP | Keeper client | ClickHouse nodes / Keeper administration |
| 9234 | TCP | Keeper Raft | The three Keeper nodes |

If running a second ClickHouse instance on a VM, its HTTP, native, and inter-server ports must be different from the first instance.

Example firewalld commands (adapt source restrictions to your network policy):

```bash
firewall-cmd --permanent --add-port=8123/tcp
firewall-cmd --permanent --add-port=9000/tcp
firewall-cmd --permanent --add-port=9009/tcp
firewall-cmd --permanent --add-port=9181/tcp
firewall-cmd --permanent --add-port=9234/tcp
firewall-cmd --reload
```

These commands open the ports broadly in the selected firewalld zone. In production, prefer source-restricted rules so that Keeper and inter-server ports are not exposed to untrusted networks.

Check:

```bash
firewall-cmd --list-all
```

# 15. Useful operational checks

## Services

```bash
systemctl status clickhouse-keeper
systemctl status clickhouse-server
```

## Logs

```bash
journalctl -u clickhouse-keeper -n 100 --no-pager
journalctl -u clickhouse-server -n 100 --no-pager
```

## HTTP health

```bash
curl http://clickhouse01:8123/ping
curl http://clickhouse02:8123/ping
curl http://clickhouse03:8123/ping
```

Expected response:

```text
Ok.
```

## Version

```sql
SELECT version();
```

## Cluster members

```sql
SELECT * FROM system.clusters WHERE cluster = 'logs_cluster';
```

## Replication status

```sql
SELECT
    database,
    table,
    is_readonly,
    queue_size,
    inserts_in_queue,
    absolute_delay
FROM system.replicas;
```

## Table sizes

```sql
SELECT
    database,
    table,
    formatReadableSize(sum(data_compressed_bytes)) AS compressed_size,
    formatReadableSize(sum(data_uncompressed_bytes)) AS uncompressed_size,
    sum(rows) AS rows
FROM system.parts
WHERE active
GROUP BY database, table
ORDER BY sum(data_compressed_bytes) DESC;
```

## Disk usage

```sql
SELECT * FROM system.disks;
```

# 16. Troubleshooting checklist

| Symptom | What to check |
|---|---|
| ClickHouse cannot start | `journalctl -u clickhouse-server`, XML syntax, duplicate/conflicting settings, directory permissions |
| Keeper cannot start | Unique `server_id`, matching Raft IDs, DNS, port 9234 connectivity |
| ClickHouse cannot connect to Keeper | Keeper service, port 9181, `<zookeeper>` section, hostname resolution |
| `system.clusters` has no `logs_cluster` | `remote_servers` XML location, XML syntax, server restart, loaded configuration |
| Replicated table is read-only | Keeper quorum/connectivity, Keeper path, replica state, server logs |
| Replication queue grows | Network, Keeper health, disk capacity, replica errors, merge backlog |
| `ON CLUSTER` fails | Cluster definition, remote connectivity, credentials, distributed DDL queue |
| `ALTER USER default` says storage is readonly | User is XML-backed; edit XML instead of using SQL |
| `GRANT ALL` fails | The granting account lacks one or more required grant options |
| DataGrip protocol error | Use HTTP on 8123 or native protocol on 9000 with a matching driver/URL |
| Insert fails on type conversion | Compare Kafka/log field types with ClickHouse table types; validate and normalize input |
