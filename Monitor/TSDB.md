# What is a Time Series Database?

A **Time Series Database (TSDB)** is a database designed specifically for storing and querying data that **changes over time**.

Every record in a TSDB has a **timestamp**, which is one of the most important parts of the data.

## Example

For example, every minute you collect CPU usage:

| Timestamp | IP          | Metric             | Value |
| --------- | ----------- | ------------------ | ----: |
| 10:00:00  | 10.13.96.51 | `server.cpu.usage` |  32.5 |
| 10:01:00  | 10.13.96.51 | `server.cpu.usage` |  35.1 |
| 10:02:00  | 10.13.96.51 | `server.cpu.usage` |  31.8 |

Unlike a traditional database, the primary question is usually:

> **"What was the value over a period of time?"**

rather than:

> **"Find the row with ID = 123."**

## What is a Time Series?

A simple way to understand a time series is:

> **Time Series = Metric + Labels + Timestamp + Value**

Prometheus and VictoriaMetrics organize data as **time series**.

For example:

```promql
server.net.if.in{ip="10.13.96.51", IFNAME="bond0"}
```

This identifies **one time series**.

Its data might look like:

| Timestamp |   Value |
| --------- | ------: |
| 10:00:00  | 1023456 |
| 10:01:00  | 1089234 |
| 10:02:00  | 1156789 |
| 10:03:00  | 1101234 |
| ...       |     ... |

Notice that the **labels identify the series**:

```text
ip="10.13.96.51"
IFNAME="bond0"
```

The labels normally stay the same for this particular series, while the **timestamp and value change over time**.

Therefore:

```text
server.net.if.in{ip="10.13.96.51", IFNAME="bond0"}
```

represents one time series:

```text
                    Time →
10:00 ── 1023456
10:01 ── 1089234
10:02 ── 1156789
10:03 ── 1101234
          ↑
        Value
```

### Key idea

A traditional database is often organized around **entities and records**:

```text
User
Order
Product
Employee
```

A time-series database is organized around **measurements and time**:

```text
CPU usage over time
Memory usage over time
Network traffic over time
Disk I/O over time
Request latency over time
```

So for monitoring systems such as **Prometheus and VictoriaMetrics**, the fundamental object is not simply a row — it is a **time series**.