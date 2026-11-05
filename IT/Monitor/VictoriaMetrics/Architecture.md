VictoriaMetrics is a high-performance time-series database (TSDB) designed for monitoring metrics. It is commonly used as a storage backend for Prometheus, Grafana, and other monitoring systems.

VictoriaMetrics provides two main deployment architectures:

1. Single-node architecture – One VictoriaMetrics process handles data ingestion, storage, querying, and retention.
    
2. Cluster architecture – Multiple components work together to distribute ingestion, storage, and query workloads.
    

The key difference is that Single-node combines all responsibilities into one service, while Cluster separates responsibilities into different components for horizontal scalability.

# 1. Single-node architecture

Simple deployment

All-in-one

## 1.1 Architecture diagram

[vmagent: Key Features Explained in Under 15 Minutes](https://images.openai.com/static-rsc-4/mZcL-ApRGrUTQNxsYkLBvT73ZvYdvDPZEThrBw6wFHpUP_lPABhXJk7R1T0UlcHLPWDB6gkCciRL6I2efrdAmlHHOaKTgJphqyRVrp7qO4it0xbaTYLak_6QiVxNR3FhtYtqFjqo72ljRnocaaW87dUyB2L3OUXq4SaGUcgpBWQ?purpose=inline)

[victoriametrics.com](https://victoriametrics.com/blog/vmagent-key-features-explained/?utm_source=chatgpt.com)

A typical deployment looks like this:

```
                 Monitoring Targets
                (Linux / MySQL / K8s)
                         |
                         v
                   vmagent
                 (Scraping)
                         |
                         v
              VictoriaMetrics Single
              +----------------------+
              |                      |
              |  HTTP API            |
              |  Data Ingestion      |
              |  Data Processing     |
              |  Indexing            |
              |  Data Storage        |
              |  Query Engine        |
              |  Retention           |
              |                      |
              +----------------------+
                         |
                         v
                      Grafana
                    (Visualization)
```

## 1.2 Main components

|Component|Responsibility|
|---|---|
|vmagent|Scrapes metrics from monitoring targets and sends them to VictoriaMetrics|
|VictoriaMetrics|Receives, processes, indexes, and stores time-series data|
|Query Engine|Executes PromQL-compatible queries (MetricsQL)|
|Grafana|Queries VictoriaMetrics and visualizes metrics|

Note that vmagent and Grafana are separate components; they are not built into the VictoriaMetrics single-node process.

## 1.3 Data flow

1. vmagent periodically scrapes metrics from targets.
    
2. vmagent sends metrics to VictoriaMetrics through the HTTP remote-write API.
    
3. VictoriaMetrics processes incoming samples and writes them to its local storage.
    
4. Grafana sends queries to VictoriaMetrics.
    
5. VictoriaMetrics executes queries and returns time-series data.
    
6. Grafana displays the results in dashboards.
    

## 1.4 Storage architecture

VictoriaMetrics Single uses a local storage directory.

For example:

```
victoria-metrics-prod \
  -storageDataPath=/var/lib/victoria-metrics \
  -retentionPeriod=12
```

The storage engine is responsible for:

- Data compression.
    
- Time-series indexing.
    
- Data storage.
    
- Background merging and maintenance.
    
- Data retention and deletion.
    

You don't need to deploy separate storage nodes or configure a distributed database.

Advantages:

- Simple deployment and maintenance.
    
- Low operational complexity.
    
- Suitable for small and medium monitoring environments.
    
- No internal distributed communication overhead.
    

Limitations:

- Limited by the resources of a single server.
    
- No native horizontal scaling across multiple storage nodes.
    
- A single instance can become a bottleneck or single point of failure.
    

# 2. Cluster architecture

Distributed deployment

Horizontal scalability

VictoriaMetrics Cluster separates the system into three main components:

1. vminsert – Data ingestion.
    
2. vmstorage – Data storage.
    
3. vmselect – Data querying.
    

This is the most important architectural distinction to understand.

## 2.1 Architecture diagram

[VictoriaMetrics: Cluster version](https://images.openai.com/static-rsc-4/ecN9289HHKCWY202qLFxhOIrAWAYrlMew0YLMInBnO_g1VCEDCjGdUj99tCqOGgtoQw6B7EOx88zkbD0O20PrBcNxSOtcRMfhiEO4Fxzuu0Q23sO-Mwu0vncV9-miypMWI6hYF1Pkf3b8qpiIzH0SiekzYbuH1S4tIhnQiBDiXI?purpose=inline)

[docs.victoriametrics.com](https://docs.victoriametrics.com/victoriametrics/cluster-victoriametrics/?utm_source=chatgpt.com)

A typical deployment looks like this:

```
                    Monitoring Targets
                           |
                           v
                         vmagent
                           |
                           v
                   Load Balancer
                           |
                           v
                 +-------------------+
                 |     vminsert      |
                 |  Data Ingestion   |
                 +-------------------+
                           |
              Distributes incoming data
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
       +-----------+ +-----------+ +-----------+
       | vmstorage | | vmstorage | | vmstorage |
       |  Node 1   | |  Node 2   | |  Node 3   |
       +-----------+ +-----------+ +-----------+
             ^             ^             ^
             |             |             |
             +-------------+-------------+
                           |
                           |
                 +-------------------+
                 |     vmselect      |
                 |   Query Engine    |
                 +-------------------+
                           ^
                           |
                        Grafana
```

In practice, both vminsert and vmselect can have multiple replicas behind load balancers.

## 2.2 Responsibilities of the three components

### A. vminsert — Write path

Ingestion layer

`vminsert` is responsible for receiving and distributing incoming metrics.

Its workflow:

1. Receives metrics from vmagent or Prometheus.
    
2. Processes incoming time-series data.
    
3. Uses consistent hashing based on metric name and labels to determine which vmstorage nodes should receive the data.
    
4. Forwards data to the corresponding vmstorage nodes.
    

For example:

```
Incoming Metrics
       |
       v
   vminsert
       |
       +----------> vmstorage-1
       |
       +----------> vmstorage-2
       |
       +----------> vmstorage-3
```

Important points:

- vminsert is stateless.
    
- You can deploy multiple vminsert instances.
    
- Adding vminsert instances increases ingestion capacity.
    
- It does not persist the actual time-series data locally.
    

### B. vmstorage — Storage layer

Stateful layer

`vmstorage` is responsible for storing time-series data.

Its responsibilities:

- Receives data from vminsert.
    
- Stores time-series data on local disks.
    
- Maintains indexes and storage structures.
    
- Returns requested data to vmselect.
    
- Performs background storage maintenance and retention management.
    

For example:

```
             vminsert
                 |
        +--------+--------+
        |        |        |
        v        v        v
    Storage  Storage  Storage
     Node 1   Node 2   Node 3
```

An important architectural characteristic:

vmstorage nodes do not communicate with each other or share their data.

This is called a shared-nothing architecture.

Each vmstorage node independently stores its own portion of the data.

docs.victoriametrics.com+1

Consequently:

- Adding vmstorage nodes increases total storage capacity.
    
- Data is distributed across storage nodes.
    
- Each node has its own storage directory.
    
- Storage nodes are stateful and require careful scaling and maintenance.
    

### C. vmselect — Read path

Query layer

`vmselect` is responsible for executing queries and retrieving metrics.

Its workflow:

1. Receives queries from Grafana or other clients.
    
2. Determines which vmstorage nodes need to be queried.
    
3. Sends query requests to the configured vmstorage nodes.
    
4. Collects responses from those nodes.
    
5. Merges and processes the results.
    
6. Returns the final result to Grafana.
    

For example:

```
                  Grafana
                     |
                     v
                  vmselect
                     |
          +----------+----------+
          |          |          |
          v          v          v
      Storage    Storage    Storage
       Node 1     Node 2     Node 3
          |          |          |
          +----------+----------+
                     |
                     v
               Query Results
                     |
                     v
                  Grafana
```

Important points:

- vmselect is stateless.
    
- You can deploy multiple vmselect instances.
    
- Adding vmselect instances increases query concurrency and throughput.
    
- vmselect does not store the original time-series data.
    

docs.victoriametrics.com+1

## 2.3 Cluster data flow: Write vs Read

This is probably the most important thing to understand about VictoriaMetrics Cluster.

Write path

1. vmagent scrapes monitoring targets.
    
2. vminsert receives metrics.
    
3. vminsert distributes metrics to vmstorage nodes.
    
4. vmstorage persists the metrics.
    

Read path

1. Grafana sends a query.
    
2. vmselect receives the query.
    
3. vmselect queries the relevant vmstorage nodes.
    
4. vmselect merges the returned data.
    
5. Grafana displays the results.
    

## 2.4 How to scale the cluster

One of the biggest advantages of cluster architecture is that you can scale different components independently.

|Component|Scaling method|What improves|
|---|---|---|
|vminsert|Horizontal|Write throughput|
|vmstorage|Horizontal / Vertical|Storage capacity and ingestion/query capacity|
|vmselect|Horizontal|Query concurrency|
|vmselect|Vertical|Heavy query performance|

For example, suppose your monitoring system has the following problems:

|Problem|Possible solution|
|---|---|
|Too many metrics being ingested|Add vminsert instances|
|Insufficient disk capacity|Add vmstorage nodes|
|High query latency due to heavy queries|Increase vmselect CPU/RAM|
|Too many concurrent Grafana queries|Add vmselect instances|

One important detail: vmstorage is stateful. Adding or removing storage nodes requires more planning than scaling vminsert or vmselect.

docs.victoriametrics.com+1

# 3. Single-node vs Cluster comparison

|Feature|Single-node|Cluster|
|---|---|---|
|Architecture|All-in-one|Distributed|
|Ingestion|Built-in|vminsert|
|Storage|Built-in|vmstorage|
|Query|Built-in|vmselect|
|Horizontal scaling|No|Yes|
|Vertical scaling|Yes|Yes|
|Multi-tenancy|No|Yes|
|Data distribution|Local|Consistent hashing|
|Replication|No built-in cluster replication|Supported|
|Operational complexity|Low|Higher|
|Typical usage|Small/medium deployments|Large-scale deployments|

A useful clarification: Single-node can also be deployed in an HA setup using multiple independent instances and data replication mechanisms, but that is different from the native distributed cluster architecture.

docs.victoriametrics.com+1

# 4. Production deployment example

Let's put the components together in a more realistic monitoring architecture.

Suppose you are building a centralized monitoring platform for multiple business systems, including:

- Linux servers
    
- Kubernetes clusters
    
- MySQL databases
    
- Middleware
    
- Business applications
    

A possible architecture is:

```
                 Monitoring Targets
           +----------+----------+----------+
           |          |          |          |
         Linux       MySQL      K8s       Apps
           |          |          |          |
           +----------+----------+----------+
                              |
                              v
                           vmagent
                              |
                              v
                       Load Balancer
                              |
                              v
                    +------------------+
                    |     vminsert     |
                    |    (Multiple)    |
                    +------------------+
                              |
                              v
                    +------------------+
                    |    vmstorage     |
                    |   (Multiple)     |
                    +------------------+
                              ^
                              |
                    +------------------+
                    |     vmselect     |
                    |    (Multiple)    |
                    +------------------+
                              ^
                              |
                       Load Balancer
                              ^
                              |
                           Grafana

                 Additional Components
                 ---------------------
                     vmalert
                   Alertmanager
                     vmauth
```

Some additional components are worth understanding:

|Component|Responsibility|
|---|---|
|vmagent|Collects and forwards metrics|
|vmauth|Authentication and request routing|
|vmalert|Evaluates alerting and recording rules|
|Alertmanager|Handles alert grouping, routing and notifications|
|Grafana|Monitoring dashboards and visualization|

These are ecosystem components rather than mandatory parts of the VictoriaMetrics Cluster itself.

# 5. Important architectural considerations

There are three concepts I particularly recommend understanding before deploying VictoriaMetrics Cluster.

1. Stateless vs Stateful

- vminsert: Stateless.
    
- vmselect: Stateless.
    
- vmstorage: Stateful.
    

This distinction determines how you deploy, scale, restart, and maintain each component.

2. Data replication is not automatic

By default, vminsert distributes data across vmstorage nodes. Distribution does not mean replication.

If you want application-level replication, you can configure:

```
-replicationFactor=2
```

This tells vminsert to store two copies of each sample on different vmstorage nodes.

You also need to configure vmselect's replication factor and deduplication appropriately.

docs.victoriametrics.com+1

3. Cluster is not always better

VictoriaMetrics recommends considering Single-node carefully before choosing Cluster.

Single-node can handle substantial workloads and may be more resource-efficient because it avoids internal network communication between separate components.

Cluster is more appropriate when you need independent horizontal scaling, distributed storage, multi-tenancy, or cluster-level availability.

docs.victoriametrics.com+1

# 6. Official documentation

These are useful resources for understanding the architecture in more depth:

- [VictoriaMetrics Cluster Architecture](https://docs.victoriametrics.com/victoriametrics/cluster-victoriametrics/?utm_source=chatgpt.com)
    
- [VictoriaMetrics Deployment Architectures](https://docs.victoriametrics.com/guides/vm-architectures/?utm_source=chatgpt.com)
    
- [VictoriaMetrics Documentation](https://docs.victoriametrics.com/?utm_source=chatgpt.com)
    

My recommendation: If you are learning VictoriaMetrics from an SRE/monitoring architecture perspective, understand these three things in order:

1. Single-node: How metrics are ingested, stored, and queried.
    
2. Cluster: How vminsert, vmstorage, and vmselect cooperate.
    
3. High Availability: How replication, multiple replicas, load balancing, and failure recovery work.
    

Once you understand these, you'll have a solid foundation for designing a production monitoring platform.

If you have 3 vmstorage nodes and configure:

```
-replicationFactor=2
```

It means VictoriaMetrics stores two copies of each time-series sample on two different vmstorage nodes, rather than storing three copies on all three nodes.

Let's look at an example.

## 1. How data is distributed

Assume you have three storage nodes:

- vmstorage-1
    
- vmstorage-2
    
- vmstorage-3
    

And one metric:

```
cpu_usage{host="server01"} 75
```

With `replicationFactor=2`, vminsert writes the sample to two storage nodes.

Example: replication factor = 2

vmstorage-1

Copy 1

vmstorage-2

Copy 2

vmstorage-3

Not selected

Illustrative placement of one time series; actual placement is determined by the cluster's hashing and replication mechanism.

The important point is that vmstorage-3 can still store other time series. It simply isn't selected for this particular sample.

## 2. What happens if one node fails?

This is where replication becomes useful.

Suppose vmstorage-1 fails.

|Node|Status|Data|
|---|---|---|
|vmstorage-1|Failed|Copy 1 unavailable|
|vmstorage-2|Healthy|Copy 2 available|
|vmstorage-3|Healthy|Other data|

The second copy remains available, so the data can still be queried.

This provides resilience against a single storage-node failure, assuming the surviving replica is healthy and accessible.

## 3. What if replicationFactor = 3?

With three vmstorage nodes:

|Replication factor|Copies per sample|Tolerance of one node failure|
|---|---|---|
|1|1|No replica protection|
|2|2|Yes|
|3|3|Yes|

This table assumes replicas are placed on distinct nodes and considers storage-node failures only.

## 4. Does replicationFactor = 2 mean double disk usage?

Yes, approximately.

Suppose your original metrics consume 1 TB of storage.

|Configuration|Approximate total storage|
|---|---|
|Replication factor = 1|1 TB|
|Replication factor = 2|2 TB|
|Replication factor = 3|3 TB|

Actual usage can differ due to indexing, compression, and storage overhead.

## 5. My recommendation for a 3-node cluster

For a production monitoring system with three vmstorage nodes, I would generally consider:

```
-replicationFactor=2
```

This gives you:

- Redundancy against one storage-node failure.
    
- Better storage efficiency than three replicas.
    
- Continued access to replicated data when one node fails.
    

One important distinction: Replication is not the same as backup. If someone accidentally deletes data or corrupts it across replicas, replication alone cannot protect you. You still need backups.

Official reference: [VictoriaMetrics Cluster – Replication](https://docs.victoriametrics.com/victoriametrics/cluster-victoriametrics/?utm_source=chatgpt.com).