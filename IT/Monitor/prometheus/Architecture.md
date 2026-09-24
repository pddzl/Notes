## Overview

Prometheus is a monitoring system based on a pull model

The basic architecture is:

```text
                    ┌─────────────────┐
                    │    Prometheus   │           │
                    │  Scrape         │
                    │  Store          │
                    │  Query          │
                    │  Alert rules    │
                    └────────┬────────┘
                             │
                       HTTP /metrics
                             │
                             |
                             │              
                             ▼              
        node_exporter  xxx_exporter  
```

The basic flow is:

```
Target → Exporter → Prometheus
```

Prometheus actively scrapes the exporter:

```
Prometheus ── GET /metrics──> Exporter
```

## Prometheus Server

A normal Prometheus Server performs several functions:

```
Prometheus Server
 ├── Scrape
 ├── Store
 ├── Query
 ├── Rule evaluation
 └── Remote Write
```

Architecture:

```
Exporter
   │
   │ scrape
   ▼
Prometheus Server
   │
   ├── Local TSDB
   ├── PromQL
   ├── Recording rules
   ├── Alerting rules
   └── Remote Write
```

Therefore:

> **Prometheus Server = scrape + store + query**

## Exporters

An exporter exposes metrics through an HTTP endpoint, usually:

```
/metrics
```

For example:

```
Linux Server
    │
    └── node_exporter :9100
             │
             └── /metrics
```

Prometheus then scrapes it:

```
Prometheus
    │
    │ GET /metrics
    ▼
node_exporter
```

### Common exporters

|Requirement|Component|
|---|---|
|Linux OS|`node_exporter`|
|Windows OS|`windows_exporter`|
|PostgreSQL|`postgres_exporter`|
|MySQL|`mysqld_exporter`|
|HTTP/TCP check|`blackbox_exporter`|
|Specific processes|`process-exporter`|
|Custom metrics|Custom exporter / textfile collector|

## Prometheus Agent

Prometheus can run in Agent mode (like zabbix_proxy).

Agent mode is optimized for:

```
scrape → buffer → remote_write
```

Architecture:

```
Exporter
   │
   │ scrape
   ▼
Prometheus Agent
   │
   │ remote_write
   ▼
Remote backend
```

Unlike a normal Prometheus Server, Agent mode does not provide the normal queryable local TSDB.

Agent does have a local WAL/buffer for unsent samples.

Therefore:

```
Agent ≠ stateless
```

but:

```
WAL/buffer ≠ queryable TSDB
```

The Agent's purpose is:

> Collect metrics and forward them.

Prometheus Agent vs Prometheus Server

|                     | Prometheus Server      | Prometheus Agent    |
| ------------------- | ---------------------- | ------------------- |
| Scrape              | ✅                      | ✅                   |
| Store in local TSDB | ✅                      | ❌                   |
| Query local data    | ✅                      | ❌                   |
| Rule evaluation     | ✅                      | ❌                   |
| Remote Write        | ✅                      | ✅                   |
| Temporary buffering | ✅                      | ✅                   |
| Main purpose        | Full monitoring server | Collector/forwarder |

Mental model:

```
Prometheus Server = scrape + store + query

Prometheus Agent = scrape + buffer + remote_write
```

### Remote Write

Prometheus Agent sends samples using the Prometheus Remote Write protocol

Possible destinations include:

```
Prometheus
VictoriaMetrics
Grafana Mimir
Thanos Receive
Cortex
M3
other Remote-Write-compatible systems
```

Example:

```
Prometheus Agent
       │
       │ Remote Write
       ├────────> Prometheus
       ├────────> VictoriaMetrics
       ├────────> Mimir
       └────────> Thanos Receive
```

## PushGateway

PushGateway is different from Prometheus Agent.

Its main purpose is:

> Receive metrics from short-lived batch jobs.

Normal Prometheus:

```
Prometheus
    │
    │ scrape
    ▼
Exporter
```

PushGateway:

```
Batch Job
    │
    │ PUSH
    ▼
Pushgateway
    │
    │ scrape
    ▼
Prometheus
```

Example:

```
backup job
    │
    │ push
    ▼
Pushgateway
```

The job can push:

```
backup_success 1
backup_duration_seconds 192
```

### Good use cases

- Database backup
- ETL
- Batch processing
- Scheduled cleanup
- Data import
- Other short-lived jobs

### Don't use PushGateway for normal server monitoring

Avoid:

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

Use:

```
Linux
   │
   ▼
node_exporter
   │
   ▲
   │ scrape
Prometheus
```

Mental model:

```
Pushgateway
    =
Store the result of my short-lived job.

Prometheus Agent
    =
Continuously collect metrics and forward them.
```

### PushGateway vs Prometheus Agent

|                              | Pushgateway      | Prometheus Agent      |
| ---------------------------- | ---------------- | --------------------- |
| Main purpose                 | Short-lived jobs | Continuous collection |
| Scrape exporters             | ❌                | ✅                     |
| Receive pushed metrics       | ✅                | ❌ as its primary role |
| Remote Write                 | ❌                | ✅                     |
| Continuous server monitoring | ❌                | ✅                     |
| Temporary buffering          | Limited          | ✅                     |
| Zabbix Proxy-like role       | ❌                | Conceptually closer   |

## Scrape Mode

### Pull

Prometheus initiates the connection:

```
Prometheus ──────> Exporter
```

This is the normal Prometheus model.

### Push

The monitored system initiates the connection:

```
Application ──────> Receiver
```

PushGateway is an example of this model.

### Why pull is attractive for monitoring

#### The monitoring system controls the collection interval

With pull:

```
Prometheus
    │
    ├── 10:00:00 → scrape
    ├── 10:00:15 → scrape
    ├── 10:00:30 → scrape
    └── 10:00:45 → scrape
```

The monitoring server knows:

> I should have received a response at 10:00:30.

If it doesn't, that's itself useful information.

For example:

```
up{instance="server01"} = 0
```

You can immediately detect:

```
server01
   └── exporter unreachable
```

With push, absence of data can be harder to distinguish from:

- agent stopped
- network problem
- application stopped sending
- monitoring server problem
- sending interval changed

#### Pull makes monitoring centralized

Imagine you have:

```
1000 servers
   │
   ├── server01
   ├── server02
   ├── server03
   ├── ...
   └── server1000
```

With pull:

```
                 ┌── server01
                 │
                 ├── server02
Prometheus ──────┼── server03
                 │
                 ├── ...
                 │
                 └── server1000
```

Prometheus decides:

```
What to monitor
When to monitor
How frequently to monitor
```

The servers don't need to know much about the monitoring infrastructure.

#### Pull makes service discovery easier

This is particularly important for Prometheus.

Suppose Kubernetes creates and destroys containers:

```
10:00

Prometheus
   │
   ├── pod A
   ├── pod B
   └── pod C
```

Then:

```
10:05

Prometheus
   │
   ├── pod A
   ├── pod C
   ├── pod D
   └── pod E
```

Prometheus discovers the current targets and simply scrapes them.

The application doesn't need to constantly figure out:

> "Where is the Prometheus server? What URL should I push to?"

That's a major advantage of Prometheus's design.

#### backpressure

Imagine your monitoring server is overloaded.

With **pull**:

```
Monitoring Server
       │
       │ "I can't scrape you right now"
       X
       │
       ▼
   Target waits
```

The monitoring server controls the rate at which it collects data.

With unrestricted **push**:

```
Server 1 ──┐
Server 2 ──┤
Server 3 ──┤
Server 4 ──┤
   ...     ├────> Monitoring Server
Server N ──┘
```

If thousands of agents suddenly push data at the same time, you can get a **thundering herd** against the monitoring system.

Push systems therefore need mechanisms for:

- buffering
- batching
- rate limiting
- retries
- backpressure