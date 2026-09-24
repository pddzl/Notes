
# JVM Memory

## Overview

The JVM memory can be divided into several runtime areas.

```text
                    JVM Process
+------------------------------------------------+
|                                                |
| Heap                                           |
|  ├── Young Generation                          |
|  └── Old Generation                            |
|                                                |
| Metaspace                                      |
|                                                |
| Per Thread                                     |
|   ├── Java Stack                               |
|   ├── Program Counter                          |
|   └── Native Method Stack                      |
+------------------------------------------------+
```

| Area | Shared? | Stores |
|------|---------|--------|
| Heap | Shared | Java objects and arrays |
| Java Stack | Per Thread | Stack frames (method execution) |
| Program Counter | Per Thread | Current executing instruction |
| Native Method Stack | Per Thread | Native (JNI) method execution |
| Metaspace | Shared | Class metadata |

---

# Heap

The Heap is the runtime area where **all Java objects and arrays** are allocated.

Characteristics:

- Shared by all threads
- Managed by the Garbage Collector
- Configured using

```bash
-Xms
-Xmx
```

The Heap consists of:

```text
Heap
├── Young Generation
└── Old Generation
```

---

# Young Generation

The Young Generation stores **newly created objects**.

Most Java objects have very short lifetimes.

Example:

```java
User user = new User();
```

## Structure

```text
Young Generation
├── Eden
├── Survivor 0 (S0)
└── Survivor 1 (S1)
```

Typical ratio:

```text
Eden : S0 : S1 = 8 : 1 : 1
```

## Object Lifecycle

1. Object is allocated in Eden.
2. Eden becomes full.
3. Minor GC occurs.
4. Live objects are copied to Survivor.
5. Objects surviving multiple GCs are promoted to the Old Generation.

```text
new Object()
      │
      ▼
    Eden
      │
 Minor GC
      ▼
 Survivor S0
      │
 Minor GC
      ▼
 Survivor S1
      │
      ▼
Old Generation
```

## Why two Survivor spaces?

The JVM uses the **Copying Garbage Collection** algorithm.

Benefits:

- Fast allocation
- Fast GC
- No memory fragmentation

---

# Old Generation

The Old Generation stores **long-lived objects**.

Examples:

- Spring Beans
- Thread pools
- Database connection pools
- Cache objects

Objects are promoted when:

- They survive enough Minor GCs.
- Survivor space is full.
- They are large objects.

## Garbage Collection

Old Generation is collected by:

- Major GC
- Full GC

Compared with Minor GC:

- Less frequent
- Much slower

---

# Metaspace

(Java 8+)

Metaspace replaced Permanent Generation.

Unlike PermGen, Metaspace uses **native memory**.

Stores:

- Class metadata
- Method metadata
- Runtime constant pool
- Class loader information

OOM example:

```text
java.lang.OutOfMemoryError: Metaspace
```

---

# Java Stack

Each thread owns one Java Stack.

Each method invocation creates one **Stack Frame**.

```text
Thread

Java Stack

+--------------+
| bar() Frame  |
+--------------+
| foo() Frame  |
+--------------+
| main() Frame |
+--------------+
```

## Stack Frame

Each Stack Frame contains:

```text
Stack Frame

├── Local Variables
├── Operand Stack
├── Frame Data
│   ├── Return Address
│   ├── Constant Pool Reference
│   └── Exception Information
```

---

# Variable Storage

Example:

```java
public void test() {
    int a = 10;
    User user = new User();
}
```

Memory layout:

```text
Java Stack

a = 10

user -----------+
                |
                ▼

Heap

User Object
```

Summary:

- Primitive local variables → Java Stack
- Object references → Java Stack
- Actual objects → Heap

---

# Primitive Types

Java has eight primitive types.

| Type | Example |
|------|---------|
| byte | 1 |
| short | 2 |
| int | 100 |
| long | 100L |
| float | 3.14f |
| double | 3.14 |
| char | 'A' |
| boolean | true |

Everything else is a reference type.

Examples:

- String
- Arrays
- Classes
- Interfaces
- Enums
- Records

---

# Heap vs Stack

| Heap | Stack |
|------|-------|
| Stores objects | Stores stack frames |
| Shared by all threads | One stack per thread |
| Managed by GC | Automatically released when methods return |
| May cause `OutOfMemoryError: Java heap space` | May cause `StackOverflowError` |

---

# Native Memory vs Heap Memory

Native memory belongs to the operating system process.

Heap memory is only one part of the JVM process memory.

```text
Java Process

+-----------------------------------------+
|                                         |
| Heap                                    |
|   Young Generation                      |
|   Old Generation                        |
|                                         |
| Native Memory                           |
|   Metaspace                             |
|   Java Stacks                           |
|   Direct Buffers                        |
|   Code Cache                            |
|   JNI                                   |
|                                         |
+-----------------------------------------+
```

## Heap

Stores:

- Objects
- Arrays

Managed by:

- Garbage Collector

Configuration:

```bash
-Xms
-Xmx
```

---

## Native Memory

Stores:

- Metaspace
- Java Thread Stacks
- DirectByteBuffer
- Code Cache
- JNI Resources

Configuration examples:

```bash
-Xss
-XX:MaxMetaspaceSize
```

---

# Where is it stored?

| Code | Memory Area |
|------|-------------|
| `int x = 10;` (local variable) | Java Stack |
| `User user` | Java Stack (reference) |
| `new User()` | Heap |
| `static int count` | Heap (inside the `Class` object) |
| Class metadata | Metaspace |
| Thread stack | Native Memory |

---

# Common JVM Memory Errors

| Error | Cause |
|------|-------|
| `OutOfMemoryError: Java heap space` | Heap is full |
| `OutOfMemoryError: Metaspace` | Metaspace is full |
| `StackOverflowError` | Stack grows too deep (usually recursion) |
| `OutOfMemoryError: Unable to create new native thread` | Native memory or OS thread limit reached |

---

# Summary

```text
                  JVM Process
+------------------------------------------------------+
|                                                      |
| Heap (Shared)                                        |
|   Young Generation                                   |
|      Eden                                            |
|      Survivor 0                                      |
|      Survivor 1                                      |
|   Old Generation                                     |
|                                                      |
| Metaspace (Native Memory)                            |
|                                                      |
| Thread 1                                             |
|   Java Stack                                         |
|      Stack Frame                                     |
|      Stack Frame                                     |
|                                                      |
| Thread 2                                             |
|   Java Stack                                         |
|                                                      |
+------------------------------------------------------+
```

## Key Takeaways

- Heap stores Java objects.
- Young Generation stores newly created objects.
- Old Generation stores long-lived objects.
- Metaspace stores class metadata.
- Java Stack stores stack frames.
- Java Stack is implemented using native memory.
- Heap is managed by the Garbage Collector.
- Native memory also contains Metaspace, Java Stacks, Direct Buffers, Code Cache, and JNI resources.