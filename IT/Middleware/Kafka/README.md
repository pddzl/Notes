## 1. What is Kafka?

Apache Kafka is a distributed event-streaming platform designed for:

- High-throughput message processing.
- Distributed data transmission.
- Real-time event streaming.
- Data persistence.
- Fault tolerance and high availability.
- Horizontal scalability.

Kafka is commonly used for:

- Asynchronous communication between micro-services.
- Log collection and aggregation.
- Real-time data pipelines.
- Event-driven architectures.
- Monitoring and data integration.

Kafka organizes messages into Topics, divides Topics into Partitions, and distributes Partitions across Brokers.

## 2. Kafka Cluster Architecture

### 2.1 Core Architecture

A Kafka cluster consists of multiple Brokers.

Each Broker is an independent Kafka server responsible for storing and serving data.

A typical architecture:

```
                  Producers
                      |
                      v
              +---------------+
              |  Kafka Cluster|
              |               |
              |  +---------+  |
              |  |Broker 1 |  |
              |  +---------+  |
              |               |
              |  +---------+  |
              |  |Broker 2 |  |
              |  +---------+  |
              |               |
              |  +---------+  |
              |  |Broker 3 |  |
              |  +---------+  |
              +---------------+
                      |
                      v
                  Consumers
```

### 2.2 Main Components

|Component|Responsibility|
|---|---|
|Producer|Publishes messages to Kafka Topics|
|Broker|Kafka server that stores and serves data|
|Topic|Logical category for organizing messages|
|Partition|Ordered log of messages within a Topic|
|Replica|Physical copy of a Partition|
|Consumer|Reads messages from Kafka|
|Consumer Group|Group of Consumers sharing partition workloads|
|Offset|Position of a message within a Partition|
|Controller|Manages cluster metadata and coordination|

### 2.3 Controller and KRaft

Modern Kafka versions use KRaft for cluster metadata management.

The Controller is responsible for managing cluster metadata and coordinating operations such as:

- Broker registration.
- Partition leadership.
- Partition reassignment.
- Metadata updates.

Kafka uses a controller quorum to maintain metadata consistency.

Older Kafka deployments used ZooKeeper, but ZooKeeper mode has been removed from modern Kafka releases.

## 3. Topic and Partition

### 3.1 What is a Topic?

A Topic is a logical category used to organize messages.

For example, an e-commerce system might have:

```
Kafka Cluster
    |
    +--- orders
    |
    +--- payments
    |
    +--- user-events
    |
    +--- inventory
```

Each Topic represents a different type of business event.

- orders: Order events.
- payments: Payment events.
- user-events: User activity events.
- inventory: Inventory changes.

### 3.2 What is a Partition?

A Partition is a subdivision of a Topic that stores an ordered sequence of messages.

For example:

```
                  Topic: orders
                        |
          +-------------+-------------+
          |             |             |
          v             v             v
      Partition 0   Partition 1   Partition 2
      +---------+   +---------+   +---------+
      | Msg A   |   | Msg D   |   | Msg G   |
      | Msg B   |   | Msg E   |   | Msg H   |
      | Msg C   |   | Msg F   |   | Msg I   |
      +---------+   +---------+   +---------+
```

Each Partition is an independent ordered log.

Important characteristics:

1. Each Partition maintains its own message ordering.
2. Different Partitions can be processed concurrently.
3. A Partition is the basic unit of parallelism for Kafka Consumers.
4. A Partition can be distributed across different Brokers through replication.

**Important:** Kafka guarantees ordering within an individual Partition, but not across different Partitions.

### 3.3 What is an Offset?

An Offset identifies the position of a message within a Partition.

Example:

```
Partition 0:

Offset 0 -> Message A
Offset 1 -> Message B
Offset 2 -> Message C
Offset 3 -> Message D
Offset 4 -> Message E
```

Offsets are local to each Partition.

For example:

```
Partition 0: Offset 0, 1, 2, 3...
Partition 1: Offset 0, 1, 2, 3...
Partition 2: Offset 0, 1, 2, 3...
```

An Offset is not a globally unique message ID.

### 3.4 How Does Kafka Determine Which Partition Receives a Message?

When a Producer publishes a message, Kafka determines the target Partition.

Common approaches:

**1. Message Key**

If a message has a Key, the default partitioner generally hashes the Key to determine the Partition.

For example:

```
Key = user-001 -> Partition 0
Key = user-002 -> Partition 1
Key = user-003 -> Partition 2
```

Messages with the same Key are normally routed to the same Partition, assuming the Partition count and partitioning strategy remain unchanged.

This is useful when you need ordering for events belonging to the same business entity.

For example:

```
user-001:
    Login
    Update Profile
    Logout
```

These events can be placed in the same Partition and processed in order.

**2. No Message Key**

When no Key is provided, Kafka's default partitioning behavior distributes records across Partitions using a sticky partitioning strategy.

This helps improve batching efficiency.

## 4. Kafka Replication

Replication is one of Kafka's most important mechanisms for high availability and fault tolerance.

### 4.1 What is Replication Factor?

Replication Factor specifies how many physical copies of each Partition Kafka maintains.

For example:

```
Replication Factor = 3
```

This means each Partition has three replicas.

If you have three Brokers and replication factor = 3, each Partition will have one replica on each Broker.

### 4.2 Leader-Follower Architecture

Kafka uses a Leader-Follower replication model.

- Leader: Handles normal read and write requests for the Partition.
- Follower: Replicates data from the Leader.
- ISR: In-Sync Replicas, which are sufficiently caught up with the Leader.

Example:

```
                Kafka Cluster

             Broker 1   Broker 2   Broker 3
             --------   --------   --------
Partition 0    Leader    Follower   Follower
Partition 1    Follower  Leader     Follower
Partition 2    Follower  Follower   Leader
```

Notice that each Partition has its own Leader.

The Leader roles are distributed across Brokers to balance workloads.

### 4.3 Does Every Broker Have Every Partition?

It depends on the Replication Factor.

If you have:

- 3 Brokers.
- 3 Partitions.
- Replication Factor = 3.

Then every Broker has a replica of every Partition.

Example:

```
Broker 1:
    Partition 0 -> Leader
    Partition 1 -> Follower
    Partition 2 -> Follower

Broker 2:
    Partition 0 -> Follower
    Partition 1 -> Leader
    Partition 2 -> Follower

Broker 3:
    Partition 0 -> Follower
    Partition 1 -> Follower
    Partition 2 -> Leader
```

### 4.4 Does Replication Mean Consumers Read the Same Message Three Times?

No.

This is an important distinction.

Suppose Message A is written to Partition 0.

With replication factor = 3:

```
Broker 1: Partition 0 -> Message A (Leader)
Broker 2: Partition 0 -> Message A (Follower)
Broker 3: Partition 0 -> Message A (Follower)
```

There are three physical copies of Message A, but they all belong to the same logical Partition.

It is NOT:

```
Partition 0 -> Message A
Partition 1 -> Message A
Partition 2 -> Message A
```

Replication creates copies of a Partition, not copies across different Partitions.

Consumers normally fetch from the Partition Leader, rather than independently consuming every replica.

### 4.5 What Happens When a Broker Fails?

Suppose Broker 1 fails.

Before failure:

```
Broker 1       Broker 2       Broker 3
P0 Leader      P0 Follower    P0 Follower
```

After failure:

```
Broker 1       Broker 2       Broker 3
  Failed       P0 Leader      P0 Follower
```

Kafka can elect an eligible in-sync follower as the new Leader.

Consumers can reconnect and continue consuming from the new Leader.

### 4.6 Replication Factor and Fault Tolerance

|Replication Factor|Number of Copies|Typical Broker Failure Tolerance|
|---|---|---|
|1|1|0|
|2|2|1|
|3|3|2|

This assumes the replicas are distributed across different Brokers and the surviving replicas are healthy.

Replication provides fault tolerance, but it is not a replacement for backups.

## 5. Consumer and Consumer Group

### 5.1 What is a Consumer?

A Consumer is an application that reads messages from Kafka.

For example:

```
Kafka Topic: orders
       |
       v
   Consumer
       |
       v
 Process Orders
       |
       v
 Update Database
```

### 5.2 What is a Consumer Group?

A Consumer Group is a group of Consumers that share the workload of consuming a Topic.

For example:

```
             Topic: orders
                   |
        +----------+----------+
        |          |          |
        v          v          v
       P0         P1         P2
        |          |          |
        v          v          v
    Consumer1  Consumer2  Consumer3
        \          |          /
         \         |         /
          Consumer Group A
```

Each Consumer is assigned one or more Partitions.

**Important rule:**

Within the same Consumer Group, a Partition can be assigned to only one Consumer at a time.

This prevents multiple Consumers in the same group from independently processing the same Partition concurrently.

### 5.3 Consumer Group vs Multiple Consumer Groups

This is a fundamental concept.

**Scenario A: One Consumer Group**

```
Topic A
   |
   +---- Partition 0 -> Consumer 1
   |
   +---- Partition 1 -> Consumer 2
   |
   +---- Partition 2 -> Consumer 3

Consumer Group A
```

The Consumers share the workload.

Each message is normally delivered to one Consumer in the group.

**Scenario B: Three Consumer Groups**

```
                  Topic A
                     |
          +----------+----------+
          |          |          |
          v          v          v
       Group A    Group B    Group C
          |          |          |
       Consumer   Consumer   Consumer
          1          2          3
```

Each Consumer Group independently consumes the entire Topic.

This is useful when multiple applications need the same events.

For example:

- Group A: Updates the order database.
- Group B: Sends notifications.
- Group C: Generates business analytics.

Each group maintains its own consumption offsets.

### 5.4 Consumer Group and Partition Assignment

Suppose:

- One Topic.
- Three Partitions.
- One Consumer Group.
- Three Consumers.

Kafka assigns the Partitions:

|Consumer|Assigned Partition|
|---|---|
|Consumer 1|Partition 0|
|Consumer 2|Partition 1|
|Consumer 3|Partition 2|

This enables parallel processing.

### 5.5 What Happens If Consumers Exceed Partitions?

Suppose you have:

- 3 Partitions.
- 5 Consumers.
- 1 Consumer Group.

Only three Consumers can actively own Partitions at the same time.

```
Partition 0 -> Consumer 1
Partition 1 -> Consumer 2
Partition 2 -> Consumer 3

Consumer 4 -> Idle
Consumer 5 -> Idle
```

The maximum number of actively assigned Consumers in one group is generally limited by the number of Partitions.

### 5.6 What Happens If a Consumer Fails?

Suppose Consumer 1 fails.

Before failure:

```
Consumer 1 -> Partition 0
Consumer 2 -> Partition 1
Consumer 3 -> Partition 2
```

After failure and rebalancing:

```
Consumer 2 -> Partition 0, Partition 1
Consumer 3 -> Partition 2
```

Kafka's Group Coordinator manages membership and partition assignment.

The reassignment process is called **Rebalancing**.

## 6. One Application Instance with Multiple Consumer Threads

A common deployment is one application instance running multiple Consumer threads.

For example:

```
Application Instance
|
+-- Consumer Thread 1 -> Partition 0
|
+-- Consumer Thread 2 -> Partition 1
|
+-- Consumer Thread 3 -> Partition 2
```

All three Consumers belong to the same Consumer Group.

### Important Implementation Detail

Kafka's Java KafkaConsumer is not thread-safe.

A typical implementation creates one KafkaConsumer instance per thread:

```
public class ConsumerWorker implements Runnable {

    private final KafkaConsumer<String, String> consumer;

    public ConsumerWorker(Properties properties) {
        this.consumer = new KafkaConsumer<>(properties);
    }

    @Override
    public void run() {
        consumer.subscribe(
            Collections.singletonList("topic-A")
        );

        try {
            while (true) {
                ConsumerRecords<String, String> records =
                    consumer.poll(Duration.ofMillis(100));

                for (ConsumerRecord<String, String> record : records) {
                    System.out.println(record.value());
                }
            }
        } finally {
            consumer.close();
        }
    }
}
```

Each thread should have its own Consumer instance.

## 7. Consumer Offset Management

Kafka needs to know where each Consumer Group has progressed.

It uses Consumer Offsets to track the reading position.

### 7.1 Where Are Consumer Offsets Stored?

Kafka stores committed Consumer Group offsets in an internal Topic:

```
__consumer_offsets
```

Offsets are tracked by:

- Consumer Group.
- Topic.
- Partition.

For example:

```
Group: order-service

Topic: orders

Partition 0 -> Committed Offset 100
Partition 1 -> Committed Offset 200
Partition 2 -> Committed Offset 150
```

The committed offset represents the next position to consume.

### 7.2 Automatic vs Manual Commit

**Automatic Commit**

Kafka periodically commits offsets automatically.

```
enable.auto.commit=true
auto.commit.interval.ms=5000
```

Advantages:

- Simple implementation.
- Less manual offset management.

Disadvantages:

- A failure can cause messages to be processed again.
- Committing before processing finishes can cause message loss from the application's perspective.

**Manual Commit**

```
enable.auto.commit=false
```

The application commits offsets after processing messages.

```
consumer.commitSync();
```

This gives the application more control over processing progress.

## 8. Message Delivery Semantics

Kafka supports different message-processing guarantees.

### 8.1 At-most-once

A message is committed before processing.

```
Read Message
     |
     v
Commit Offset
     |
     v
Process Message
```

If the application crashes after committing but before processing, the message may be lost from the application's processing perspective.

### 8.2 At-least-once

A message is processed before committing its offset.

```
Read Message
     |
     v
Process Message
     |
     v
Commit Offset
```

If the application crashes after processing but before committing, the message may be processed again.

This can result in duplicate processing.

### 8.3 Exactly-once

Kafka supports transactional mechanisms for exactly-once processing in supported Kafka workflows.

However, exactly-once behavior is not automatic for arbitrary external database operations.

When integrating with databases or external services, idempotency and transaction coordination must be considered.

## 9. ISR and Reliable Replication

ISR stands for In-Sync Replicas.

These are replicas that are sufficiently caught up with the Leader according to Kafka's replication rules.

For example:

```
Partition 0

Broker 1 -> Leader
Broker 2 -> Follower (ISR)
Broker 3 -> Follower (ISR)
```

If Broker 3 falls too far behind, it may be removed from the ISR.

### 9.1 Important Kafka Configurations

Broker/topic configuration:

```
default.replication.factor=3
min.insync.replicas=2
```

Producer configuration:

```
acks=all
```

Meaning:

|Configuration|Meaning|
|---|---|
|replication.factor=3|Maintain three replicas|
|min.insync.replicas=2|Require at least two ISR replicas for writes using acks=all|
|acks=all|Wait for acknowledgement from the current ISR replicas|

Together, these settings help prevent acknowledged writes from being lost during certain Broker failures.

Note that `acks=all` does not necessarily mean all configured replicas must acknowledge. It means all current ISR replicas.
