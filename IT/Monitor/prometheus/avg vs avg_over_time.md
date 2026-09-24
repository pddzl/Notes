## Original Range Vector

Query:

```promql
server.net.if.in{ip="10.13.96.51"}[10m]
```

A range selector returns a **range vector**, where each time series contains all samples from the last 10 minutes.

Example (simplified):

```json
[
  {
    "IFNAME": "bond0",
    "values": [
      [1000, 100],
      [1060, 200],
      [1120, 300]
    ]
  },
  {
    "IFNAME": "em1",
    "values": [
      [1000, 800],
      [1060, 1000],
      [1120, 1200]
    ]
  }
]
```

---

## `avg_over_time(range-vector)`

### Definition

`avg_over_time()` calculates the **average value over time for each individual time series**.

```promql
avg_over_time(server.net.if.in{ip="10.13.96.51"}[10m])
```

Output:

```json
[
  {
    "IFNAME": "bond0",
    "value": 200
  },
  {
    "IFNAME": "em1",
    "value": 1000
  }
]
```

Notice that the number of time series **does not change**. Only each series is reduced to its average value over the last 10 minutes.

---

## `avg(instant-vector)`

### Definition

`avg()` calculates the **average across multiple time series** at the current evaluation timestamp.

```promql
avg(server.net.if.in{ip="10.13.96.51"})
```

Output:

```json
{
  "value": 600
}
```

Calculation:

```
(200 + 1000) / 2 = 600
```

All matching time series are aggregated into a **single result**.

---

## Combining Them

Query:

```promql
avg(avg_over_time(server.net.if.in{ip="10.13.96.51"}[10m]))
```

Execution order:

1. `server.net.if.in[10m]`
   - Returns a **range vector**.

2. `avg_over_time(...)`
   - Calculates the 10-minute average **for each interface**.
   - Result:

   ```text
   bond0 = 200
   em1   = 1000
   ```

3. `avg(...)`
   - Averages the results across all interfaces.

Final result:

```
(200 + 1000) / 2 = 600
```

---

## Time Aggregation vs Series Aggregation

| Function | Aggregates | Input | Output |
|----------|------------|-------|--------|
| `avg_over_time()` | Over **time** | Range Vector | Instant Vector |
| `avg()` | Across **series** | Instant Vector | Instant Vector |

A simple way to remember the difference:

- **`avg_over_time()`** → "Average each series over the last *N* minutes."
- **`avg()`** → "Average all matching series together."