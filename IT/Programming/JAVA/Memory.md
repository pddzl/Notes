
## overview

```shell
JVM Memory
│
├── Heap
│   ├── Young Generation
│   │   ├── Eden
│   │   ├── Survivor 0 (S0)
│   │   └── Survivor 1 (S1)
│   │
│   └── Old Generation
│
├── Metaspace (replaces Permanent Generation)
│
├── Java Stack
├── Program Counter (PC Register)
└── Native Method Stack
```


## Young Generation

The **Young Generation** stores **newly created objects**.

Most Java objects have a very short lifetime. For example:

```java
public void test() {
    User user = new User();
}
```

When the method finishes, `user` is no longer referenced and becomes eligible for garbage collection.

### Structure

The Young Generation consists of:

```java
Young Generation
├── Eden
├── Survivor 0
└── Survivor 1
```

A common size ratio is:

```shell
Eden : S0 : S1 = 8 : 1 : 1
```

For example, if the Young Generation is 100 MB:

- Eden = 80 MB
- S0 = 10 MB
- S1 = 10 MB

### Object Lifecycle

1. A new object is allocated in **Eden**.
2. When Eden becomes full, a **Minor GC** occurs.
3. Live objects are copied to a Survivor space.
4. During subsequent Minor GCs, surviving objects are copied between S0 and S1.
5. After surviving multiple GCs, they are promoted to the Old Generation.

Example:

```shell
new Object()
      │
      ▼
    Eden
      │
 Minor GC
      ▼
 Survivor 0
      │
 Minor GC
      ▼
 Survivor 1
      │
  ...
      ▼
Old Generation
```

### Why are there two Survivor spaces?

The JVM uses the **Copying Garbage Collection** algorithm in the Young Generation.

Benefits:

- Fast allocation
- Fast garbage collection
- No memory fragmentation

## Old Generation

The **Old Generation** stores objects that live for a long time.

Examples include:

- Spring Beans
- Database connection pools
- Thread pools
- Cache objects
- Long-lived collections

An object is promoted to the Old Generation when:

- It survives enough Minor GCs (default threshold is typically **15**).
- The Survivor space cannot accommodate it.
- It is a very large object (depending on the JVM and GC algorithm).

### Garbage Collection

When the Old Generation becomes full, the JVM performs a:

- **Major GC**, or
- **Full GC** (depending on the collector and situation)

Major/Full GC is much slower than Minor GC because:

- More objects must be scanned.
- Most objects are still alive.
- More memory is involved.

## Permanent Generation (PermGen)

**PermGen existed only in Java 7 and earlier.**

It did **not** store ordinary Java objects.

Instead, it stored:
- Class metadata
- Method metadata
- Runtime constant pool (partially, depending on the Java version)

A common issue in Java 7 was:

```shell
java.lang.OutOfMemoryError: PermGen space
```

This often happened during repeated class loading, such as in application servers like Tomcat during hot deployment.

## Metaspace (java 8+)

Starting with **Java 8**, **PermGen was removed** and replaced by **Metaspace**.

Differences:

| PermGen                      | Metaspace                                            |
| ---------------------------- | ---------------------------------------------------- |
| Part of JVM memory           | Uses native (OS) memory                              |
| Fixed size unless configured | Grows automatically (within available system memory) |
| Java 7 and earlier           | Java 8 and later                                     |

Metaspace stores:

- Class metadata
- Method metadata
- Class loader information

If it becomes full, you'll see:

```shell
java.lang.OutOfMemoryError: Metaspace
```

## Comparsion

| Area                           | Stores                | GC Type                   |
| ------------------------------ | --------------------- | ------------------------- |
| Young Generation               | Newly created objects | Minor GC                  |
| Old Generation                 | Long-lived objects    | Major GC / Full GC        |
| Permanent Generation (Java 7-) | Class metadata        | Full GC                   |
| Metaspace (Java 8+)            | Class metadata        | Full GC (class unloading) |

## Object Lifecycle Summary

```shell
	  new Object()
		   │
		   ▼
	+--------------+
	|    Eden      |
	+--------------+
		   │
	 Minor GC
		   ▼
	+--------------+
	| Survivor S0  |
	+--------------+
		   │
	 Minor GC
		   ▼
	+--------------+
	| Survivor S1  |
	+--------------+
		   │
	Survives multiple GCs
		   ▼
	+--------------+
	| Old Generation|
	+--------------+
		   │
	Major / Full GC
		   ▼
	Reclaimed if unreachable
```

## Java Virtual Machine Stack


## Variables

```java
String s = "Hello";
int n = 100;
```

The actual `String` object is stored in the heap (or, more precisely, in the JVM's string pool, which is a special area managed within the heap for string literals).

```shell
Java Stack                    Heap

+------------------+          +----------------------+
| s  ------------+ | -------> | String("Hello")      |
| n = 100         |           +----------------------+
+------------------+
```

### Primitive types in Java

Java has exactly **8 primitive types**:

|Primitive|Example|
|---|---|
|`byte`|`1`|
|`short`|`2`|
|`int`|`100`|
|`long`|`100L`|
|`float`|`3.14f`|
|`double`|`3.14`|
|`char`|`'A'`|
|`boolean`|`true`|

Everything else is a **reference type**, including:

- `String`
- Arrays (`int[]`, `String[]`)
- Classes (`Person`, `Object`)
- Interfaces
- Enums
- Records

## native memory vs heap memory

The distinction between **heap memory** and **native memory** is one of the most important concepts in JVM memory management.

| Heap Memory                         | Native Memory                                               |
| ----------------------------------- | ----------------------------------------------------------- |
| Managed by the JVM                  | Managed by the operating system and native code             |
| Stores Java objects                 | Stores JVM internals and native resources                   |
| Garbage-collected                   | Usually not garbage-collected by the JVM                    |
| Configured with `-Xms` and `-Xmx`   | Controlled by various JVM options or the OS                 |
| `OutOfMemoryError: Java heap space` | `OutOfMemoryError: Metaspace` or native allocation failures |
### Heap Memory

The **heap** is where Java objects are allocated.

For example:

```java
User user = new User();
int[] nums = new int[1000];
```

The actual objects are stored in the heap.

```shell
Stack                    Heap
-----                    -----------------
user --------------->    User Object

nums --------------->    int[1000]
```

The heap is managed by the **Garbage Collector (GC)**.

It is divided into:

```shell
Heap
├── Young Generation
└── Old Generation
```

Typical JVM options:

```shell
-Xms2G
-Xmx4G
```

meaning:

- Initial heap size = 2 GB
- Maximum heap size = 4 GB

### Native Memory

Native memory is **outside the Java heap**.

It belongs to the operating system process and is used by both the JVM itself and native libraries.

Typical consumers include:

- **Metaspace** (class metadata)
- Thread stacks
- Direct ByteBuffers (NIO)
- JIT-compiled code (Code Cache)
- JNI (Java Native Interface)
- Internal JVM data structures

A simplified view:

```shell
Operating System Process Memory
+--------------------------------+
| Heap                           |
| Young + Old                    |
+--------------------------------+
| Metaspace                      |
+--------------------------------+
| Thread Stacks                  |
+--------------------------------+
| Direct Buffers                 |
+--------------------------------+
| Code Cache                     |
+--------------------------------+
| JNI Libraries                  |
+--------------------------------+
```

### Example 1: Metaspace

Since Java 8:

```shell
PermGen
      ↓
Metaspace
```

Class metadata is stored in **native memory**, not in the heap.

If too many classes are loaded:

```shell
java.lang.OutOfMemoryError: Metaspace
```

Even if plenty of heap space remains.

### Example 2: Thread Stack

Each Java thread has its own stack.

```java
new Thread(() -> {
    ...
}).start();
```

Each thread allocates native memory for its stack.

The stack size is configured with:

```shell
-Xss1m
```

If you create too many threads, the JVM may fail because it runs out of native memory, even though the heap is not full.

### Example 3: DirectByteBuffer

```java
ByteBuffer buffer = ByteBuffer.allocateDirect(1024 * 1024);
```

`allocateDirect()` allocates **native memory**, not heap memory.

Benefits:

- Faster I/O
- Avoids copying between the JVM and the operating system

This is widely used in high-performance frameworks such as Netty.

### Garbage Collection

#### Heap Memory

```
Object↓Heap↓Minor GC / Major GC↓Freed
```

The JVM automatically reclaims unreachable objects.

### Native Memory

Usually:

```shell
Native allocation
↓
OS memory
↓
Released manually or by JVM components
```

The JVM does **not** perform normal object garbage collection on native memory. Some native resources (such as direct buffers) are released through cleanup mechanisms, but they are not managed in the same way as heap objects.

### Memory Errors

#### Heap exhausted

```shell
Exception in thread "main"

java.lang.OutOfMemoryError:
Java heap space
```

Cause:

Too many Java objects.

### Native memory exhausted

```shell
java.lang.OutOfMemoryError:
Metaspace
```

or

```shell
java.lang.OutOfMemoryError:
Unable to create new native thread
```

Cause:

The process has exhausted native memory or other OS limits.

### Relationship

```shell
          Java Process
+-----------------------------------------+
|                                         |
|  Heap (GC Managed)                      |
|  +-------------------------------+      |
|  | Young Generation              |      |
|  | Old Generation                |      |
|  +-------------------------------+      |
|                                         |
|  Native Memory                          |
|  +-------------------------------+      |
|  | Metaspace                    |       |
|  | Thread Stacks                |       |
|  | Direct Buffers               |       |
|  | Code Cache                   |       |
|  | JNI                          |       |
|  +-------------------------------+      |
|                                         |
+-----------------------------------------+
```

### Key differences

|Feature|Heap Memory|Native Memory|
|---|---|---|
|Location|Inside the JVM heap|Outside the heap, within the process address space|
|Stores|Java objects and arrays|Metaspace, thread stacks, direct buffers, code cache, JNI resources|
|Managed by|JVM Garbage Collector|JVM components, native code, and the operating system|
|Configuration|`-Xms`, `-Xmx`|Options such as `-XX:MaxMetaspaceSize`, `-Xss`, or OS limits|
|Typical OOM|`Java heap space`|`Metaspace`, `Unable to create new native thread`, or other native allocation failures|

In short, **heap memory is for Java objects and is managed by the garbage collector**, while **native memory is everything the JVM process uses outside the heap**, including Metaspace, thread stacks, direct buffers, and other JVM/native resources.