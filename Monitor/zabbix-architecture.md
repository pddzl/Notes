The current architecture is conceptually:

```
                         Zabbix Server
                              ▲
                              │
                       collected data
                              │
                        Zabbix Proxy
                         ▲    ▲    ▲
                         │    │    │
                       Agent Agent Agent
```

Responsibilities:

### Zabbix Agent

```
Collect host/application information
```

### Zabbix Proxy

```
Collect
Temporary buffer
Forward
```

### Zabbix Server

```
Central processing
Long-term storage
Query
Alerting
```

---

# 3. Prometheus Architecture

The basic Prometheus architecture is:

```
Exporter
    ▲
    │ scrape
    │
Prometheus Server
```

Prometheus Server:

```
Scrape
Store
Query
Rule evaluation
```

For example:

```
Linux Server
    │
    └── node_exporter
             ▲
             │ HTTP scrape
             │
        Prometheus
```

---

# 4. Zabbix Agent → Exporter

The closest conceptual mapping is:

```
Zabbix Agent
      ↓
Exporter
```

Examples:

```
Zabbix Agent
      ↓
node_exporter
```

for Linux.

```
Zabbix Agent
      ↓
windows_exporter
```

for Windows.

For applications:

```
Zabbix Agent
      ↓
application /metrics
```

or a specialized exporter.

Important:

> Prometheus does not normally use one universal agent like Zabbix Agent.

Instead, the Prometheus ecosystem uses specialized exporters.

---

# 5. Zabbix Proxy → Prometheus Agent

There is no direct equivalent to Zabbix Proxy in normal Prometheus Server architecture.

However, **Prometheus Agent mode** can play a similar architectural role when there are network boundaries.

Conceptually:

```
Zabbix:

Zabbix Agent
      ↓
Zabbix Proxy
      ↓
Zabbix Server
```

becomes:

```
Prometheus:

Exporter
      ↓
Prometheus Agent
      ↓
Prometheus Server
```

This is not a technical 1:1 mapping.

The similarity is:

```
remote collector
      ↓
temporary buffer
      ↓
central backend
```

---

# 6. Network Topology

The actual network constraint is:

```
Network A
Prometheus
    │
    X
    │
Network B
Servers
```

Prometheus in Network A cannot initiate connections to Network B.

Normal Prometheus pull would require:

```
Prometheus ──────> exporter
```

which cannot work.

---

# 7. Recommended Architecture for This Network

Use Prometheus Agent mode inside Network B.

```
                         NETWORK A

                  ┌─────────────────┐
                  │    Prometheus   │
                  │                 │
                  │      TSDB       │
                  │      Query      │
                  └────────▲────────┘
                           │
                           │ Remote Write
                           │
═══════════════════════════╪═══════════════════════════

                         NETWORK B

                  ┌────────┴────────┐
                  │ Prometheus Agent│
                  └────────┬────────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
      node_exporter  blackbox_exporter  other exporters
            │              │
            ▼              ▼
        Linux host     HTTP/TCP checks
```

The connection direction is:

```
Network A ──X──> Network B

Network B ──────> Network A
```

The Agent initiates the outbound Remote Write connection:

```
Prometheus Agent ──────> Prometheus
```

This fits the firewall topology.

---

# 8. Complete Architecture

```
                         NETWORK A

                  ┌─────────────────┐
                  │    Prometheus   │
                  │                 │
                  │  Scrape         │
                  │  Store          │
                  │  Query          │
                  └────────▲────────┘
                           │
                           │ Remote Write
                           │
═══════════════════════════╪═══════════════════════════

                         NETWORK B

                  ┌────────┴────────┐
                  │ Prometheus Agent│
                  │                 │
                  │ scrape          │
                  │ buffer          │
                  │ remote_write     │
                  └────────┬────────┘
                           │
            ┌──────────────┼───────────────┐
            │              │               │
            ▼              ▼               ▼
      node_exporter  blackbox_exporter  process-exporter
            │              │               │
            ▼              ▼               ▼
       OS metrics      HTTP/TCP        process metrics
```

---

# 9. Monitoring Requirements

## 9.1 Linux CPU / Memory / Disk / Network

Use:

```
node_exporter
```

Architecture:

```
Linux
   │
   ▼
node_exporter
   │
   ▲
   │ scrape
Prometheus Agent
```

---

# 10. HTTP Health Check

For:

```
http://10.13.96.51:8080/health
```

use:

```
blackbox_exporter
```

Architecture:

```
Prometheus Agent
       │
       │ scrape
       ▼
Blackbox Exporter
       │
       │ HTTP GET
       ▼
Application /health
```

Important metric:

```
probe_success
```

Meaning:

```
1 = UP
0 = DOWN
```

HTTP status:

```
probe_http_status_code
```

Response time:

```
probe_duration_seconds
```

Example alert:

```
- alert: HealthCheckFailed
  expr: probe_success == 0
  for: 2m
```

---

# 11. TCP Connection UP/DOWN

If the requirement is simply:

> Can the monitoring system establish a TCP connection to this host and port?

Example:

```
10.13.96.51:5432
```

use:

```
blackbox_exporter
```

Architecture:

```
Prometheus Agent
       │
       ▼
Blackbox Exporter
       │
       │ TCP connect
       ▼
10.13.96.51:5432
```

Metric:

```
probe_success
```

Meaning:

```
1 = TCP connection successful → UP
0 = TCP connection failed     → DOWN
```

Example alert:

```
- alert: TCPConnectionDown
  expr: probe_success == 0
  for: 1m
```

No `node_exporter` is needed for this check.

---

# 12. Process Count

Existing Zabbix item:

```
proc.num[,,,pgpoolasd]
```

means:

> How many `pgpoolasd` processes are running?

Prometheus does not have a direct equivalent to the Zabbix `proc.num` item.

Possible approaches:

### General process metrics

`node_exporter` can provide:

```
node_processes
node_procs_running
node_procs_blocked
node_procs_forked_total
```

These are general system process metrics.

### Specific process

For:

```
pgpoolasd
```

use:

```
process-exporter
```

or a custom metric using the `node_exporter` textfile collector.

For example:

```
pgrep -c pgpoolasd
```

could produce:

```
pgpoolasd_processes 1
```

---

# 13. Zabbix → Prometheus Monitoring Mapping

|Zabbix requirement|Prometheus solution|
|---|---|
|Zabbix Agent|Exporter|
|Zabbix Proxy|Prometheus Agent for remote-network collection|
|Zabbix Server|Prometheus Server|
|CPU|`node_exporter`|
|Memory|`node_exporter`|
|Disk|`node_exporter`|
|Network|`node_exporter`|
|Specific process count|`process-exporter` / textfile collector|
|HTTP health check|`blackbox_exporter`|
|TCP port UP/DOWN|`blackbox_exporter`|
|PostgreSQL metrics|`postgres_exporter`|
|MySQL metrics|`mysqld_exporter`|
|Short-lived batch job|Pushgateway|

---

# 14. Zabbix Proxy Data Storage

Zabbix Proxy is not just a transparent network forwarder.

It can temporarily store collected data.

```
Agent
  │
  ▼
Zabbix Proxy
  │
  ├── collect
  ├── temporary storage/buffer
  │
  │ Server unavailable
  │
  ▼
local buffer
  │
  │ retry
  ▼
Zabbix Server
```

However, Proxy is not the long-term historical database.

Conceptually:

```
Zabbix Proxy
    =
collect + buffer + forward
```

---

# 15. Prometheus Agent Storage

Prometheus Agent has a similar buffering concept.

```
Exporter
    │
    ▼
Prometheus Agent
    │
    ├── scrape
    ├── local WAL/buffer
    │
    └── remote_write
             │
             ▼
        Prometheus
```

If the central Prometheus is temporarily unavailable, the Agent can retain unsent samples locally and retry.

However:

```
Agent WAL/buffer ≠ TSDB
```

It is not intended to provide queryable historical data.

Conceptually:

```
Prometheus Agent
    =
scrape + buffer + forward
```

---

# 16. Pushgateway Is Not a Zabbix Proxy Replacement

Pushgateway:

```
Batch Job
    │
    │ push
    ▼
Pushgateway
    │
    │ scrape
    ▼
Prometheus
```

It is designed mainly for short-lived jobs.

It should not be used as:

```
Linux Server
    │
    │ push CPU/memory/disk
    ▼
Pushgateway
    │
    ▼
Prometheus
```

For continuous monitoring use:

```
Exporter
    │
    ▼
Prometheus Agent
    │
    ▼
Prometheus
```

---

# 17. Final Architecture

For the current network topology, the recommended Prometheus-only architecture is:

```
                         NETWORK A

                 ┌──────────────────┐
                 │    Prometheus    │
                 │                  │
                 │      TSDB        │
                 │      PromQL      │
                 │      Rules       │
                 └────────▲─────────┘
                          │
                          │ Remote Write
                          │
══════════════════════════╪══════════════════════════

                         NETWORK B

                 ┌────────┴─────────┐
                 │ Prometheus Agent │
                 │                  │
                 │ scrape           │
                 │ buffer           │
                 │ remote_write     │
                 └────────┬─────────┘
                          │
          ┌───────────────┼────────────────┐
          │               │                │
          ▼               ▼                ▼
    node_exporter   blackbox_exporter  process-exporter
          │               │                │
          ▼               ▼                ▼
      OS metrics      HTTP/TCP checks   process metrics
```

The core data flow is:

```
Exporter
   │
   │ scrape
   ▼
Prometheus Agent
   │
   │ remote_write
   ▼
Prometheus Server
   │
   ├── Store
   └── Query
```

The key concepts are:

```
Exporter
  = expose metrics

Prometheus Server
  = scrape + store + query

Prometheus Agent
  = scrape + buffer + forward

Blackbox Exporter
  = HTTP/TCP/ICMP/DNS probing

Process Exporter
  = specific process monitoring

Pushgateway
  = short-lived batch-job metrics
```

This architecture replaces the **Zabbix Agent → Zabbix Proxy → Zabbix Server** model while preserving the important requirement that **Network B cannot be directly reached from Network A**.