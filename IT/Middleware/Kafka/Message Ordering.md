## 1. Offsets Are Local to Each Partition

An offset identifies a message's position within a partition.

It is not a globally unique message ID.

For example, a topic has three partitions:

```
Partition 0:
Offset 0 -> A
Offset 1 -> B
Offset 2 -> C

Partition 1:
Offset 0 -> D
Offset 1 -> E
Offset 2 -> F

Partition 2:
Offset 0 -> G
Offset 1 -> H
Offset 2 -> I
```

Each partition maintains its own independent offset sequence.

## 2. How Do Three Consumers Process Messages?

Suppose we have:

- One topic
- Three partitions
- One consumer group
- Three consumers

Kafka assigns one partition to each consumer:

```
Consumer Group
      |
      +------------------+
      |                  |
      v                  v
 Consumer 1          Consumer 2          Consumer 3
      |                  |                   |
      v                  v                   v
Partition 0          Partition 1         Partition 2
```

Each consumer processes messages from its assigned partition.

Within each partition, messages are read in offset order.

However, the three consumers work independently and concurrently.

## 3. Why Can Messages Be Processed Out of Order?

Consider the following messages:

```
Partition 0: A -> B -> C
Partition 1: D -> E -> F
Partition 2: G -> H -> I
```

Although each partition preserves its own order, consumers may take different amounts of time to process messages.

For example, the actual processing completion order could be:

```
D -> G -> A -> E -> H -> B -> F -> I -> C
```

This happens because:

- Consumer 1 processes Partition 0.
- Consumer 2 processes Partition 1.
- Consumer 3 processes Partition 2.
- Each consumer works independently.
- Processing times may differ.

**Kafka does not guarantee global message ordering across multiple partitions.**

It also does not automatically reorder messages after consumers have processed them.

## 4. How Can We Preserve Message Ordering?

### 4.1 Use One Partition

If a topic has only one partition:

```
Topic
  |
  v
Partition 0
  |
  +--> Message A
  +--> Message B
  +--> Message C
```

All messages are processed in partition order by one consumer in a consumer group.

Advantages:

- Preserves ordering across all messages in that partition.
- Simple to implement.

Disadvantages:

- Limits consumer parallelism within that group.
- May become a throughput bottleneck.

### 4.2 Use Message Keys

In most business scenarios, we don't need global ordering. We need ordering for messages belonging to the same business entity.

For example, consider order events:

```
Order 1001:
  Order created
  Order paid
  Order shipped

Order 1002:
  Order created
  Order paid
  Order shipped
```

Set `order_id` as the message key:

```
Message 1:
Key = order_1001
Value = Order created

Message 2:
Key = order_1002
Value = Order created

Message 3:
Key = order_1001
Value = Order paid

Message 4:
Key = order_1002
Val
```