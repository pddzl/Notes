# Firewall

Question: CentOS7 uses firewalld, why does iptables command still works

> **`firewalld` is not a replacement for `iptables`; it is a management layer on top of `iptables` on CentOS 7.**

                 firewall-cmd
                      │
                      ▼
                 firewalld daemon
                      │
             translates rules into
                      │
                      ▼
                iptables (kernel)
                      │
                      ▼
             Linux Netfilter framework

On newer systems, such as **RHEL 8/9**, **CentOS Stream 8/9**, and **Rocky Linux 8/9**, the backend is often **nftables** instead of legacy iptables.

# CPU

## Utilization

**CPU utilization** means **the percentage of CPU processing capacity currently being used**.

Question: Does CPU utilization indicate how much CPU time is being consumed.

CPU utilization is essentially **how much of the available CPU execution time is being consumed by running work during a given measurement interval**.

Think of a CPU core as having a stream of **time slices**:

```
Time ──────────────────────────────────────────>

CPU core:
[Process A][Process A][Process B][Idle][Process C][Process C]
```

If during a 1-second interval the CPU spends:

```
0.8 s → executing processes
0.2 s → idle
```

then:

```
CPU utilization = 0.8 / 1.0 × 100%
                = 80%
```

So your statement:

> CPU utilization indicates how much CPU time is being consumed.

is basically correct.

More precisely:

> **CPU utilization is the percentage of CPU execution time that the CPU spends doing work rather than being idle.**

One important point

A process doesn't permanently "own" a CPU time slice.

The scheduler repeatedly gives runnable processes opportunities to execute:

CPU

```
CPU
 │
 ├── time slice → Process A
 ├── time slice → Process B
 ├── time slice → Process A
 ├── time slice → Process C
 ├── time slice → Process B
 └── idle
```

Therefore, if many processes are runnable, the CPU can spend nearly all its time executing something:

```
Process A ─┐
Process B ─┤
Process C ─┤ → CPU → 100% utilization
Process D ─┘
```

And this is why **100% CPU utilization doesn't necessarily mean one process is using 100%**. It can mean many processes collectively consume all available CPU time.

For a multi-core machine, the same principle applies independently to each core, and monitoring tools usually normalize the result to **0–100% of total CPU capacity**.

Question: how to calculate cpu utilization in centos

```
top - 14:03:46 up 558 days, 19:14,  4 users,  load average: 154.34, 139.43, 90.65
Tasks: 999 total,   1 running, 753 sleeping,   0 stopped,   0 zombie
%Cpu(s): 14.0 us,  0.2 sy,  0.0 ni,  9.0 id, 76.6 wa,  0.1 hi,  0.1 si,  0.0 st
```

CPU utilization is typically calculated as:

> **CPU Utilization = 100% − %idle**

From your `top` output:

`%Cpu(s): 14.0 us, 0.2 sy, 0.0 ni, 9.0 id, 76.6 wa, 0.1 hi, 0.1 si, 0.0 st`

- **us** = 14.0% (user)
- **sy** = 0.2% (system)
- **ni** = 0.0% (nice)
- **id** = 9.0% (idle)
- **wa** = 76.6% (I/O wait)
- **hi** = 0.1% (hardware interrupts)
- **si** = 0.1% (software interrupts)
- **st** = 0.0% (steal)

Method 1: Standard CPU utilization (Linux definition)

Linux considers **I/O wait as non-idle CPU time**, so:

CPU Utilization = 100 - id (100 - 9.0 = 91.0%)

**CPU Utilization = 91.0%**

Method 2: Actual CPU busy doing work

If you want to know how much CPU is actually executing code (excluding I/O wait):

CPU Busy = us + sy + ni + hi + si (14.0 + 0.2 + 0.0 + 0.1 + 0.1) = 14.4%

This means:

- **14.4%** of CPU time is executing processes.
- **76.6%** of CPU time is waiting for disk/network I/O.
- **9.0%** is completely idle.

## Load

**CPU load** is a measure of **how many tasks are currently competing for CPU execution or are stuck in uninterruptible waiting states**.

In Linux, it is commonly represented by **load average**, for example:

```
load average: 0.50, 1.20, 2.00
```

These are the average loads over:

```
1 minute    5 minutes    15 minutes
```

Simple way to think about it

Imagine a CPU as a checkout counter:

- **CPU utilization** → how busy the cashier actually is.
- **CPU load** → how many customers are waiting for service.

So:

```text
CPU utilization = "How much CPU time is being used?"
CPU load        = "How much work is waiting for/using CPU?"
```

Example

Suppose you have **4 CPU cores**.

`Load = 2`

There are roughly 2 tasks competing for execution capacity, so the system has plenty of CPU capacity.

`Load = 4`

Roughly one runnable task per CPU core.

`Load = 8`

There is more demand than the 4 cores can execute simultaneously, so tasks may be waiting.

Important

CPU load is **not a percentage**.

For a 4-core server:

```text
Load 1     → low
Load 4     → roughly full CPU demand
Load 8     → significant contention
```


But Linux load also includes tasks in **uninterruptible sleep**, commonly related to I/O. Therefore, a high load doesn't necessarily mean the CPU itself is 100% utilized.

**In one sentence:**

> **CPU load represents the amount of work competing for CPU resources (plus certain uninterruptible waits), while CPU utilization represents the percentage of CPU execution capacity actually being used.**

## Iowait

**I/O wait (`iowait`)** is The percentage of time that the CPU is idle while there are processes waiting for I/O to complete.

Or, more simply:

> **`iowait` = CPU idle time associated with outstanding I/O.**

A better mental model

```
Process A
    │
    │ requests disk I/O
    ▼
┌──────────────┐
│ Waiting for  │
│     I/O      │
└──────┬───────┘
       │
       │ CPU has no other runnable work
       ▼
     CPU
       │
       └──► iowait
```

Compare:

```
Process waiting for I/O
        ↓
CPU has other runnable processes
        ↓
CPU runs them
        ↓
No iowait for that CPU
```

versus:

```
Process waiting for I/O
        ↓
No other runnable work
        ↓
CPU is idle because I/O is outstanding
        ↓
iowait
```


### Question

#### 1 
when process are waiting for I/O to complete, does it release cpu time slice

Yes. **Normally, when a process blocks waiting for I/O, it gives up the CPU rather than continuing to consume its CPU time slice.**

For example:

```text
Process A
   │
   │ read() from disk
   ▼
Waiting for I/O
   │
   │ ← Process A blocks
   │
   └──► CPU scheduler can run Process B
              │
              ▼
          Process B runs
```

So the sequence is roughly:

1. Process A is running.
2. Process A requests I/O, e.g. `read()` from disk.
3. The I/O cannot complete immediately.
4. Process A becomes **blocked/sleeping**.
5. Process A is removed from the CPU's runnable queue.
6. The scheduler runs another runnable process.
7. When the I/O completes, Process A becomes runnable again.
8. Eventually Process A gets CPU time again.

What happens to the time slice?

Suppose Process A has a 10 ms time slice:

```text
Process A:
[ CPU 3 ms ][ I/O request ][ WAITING ........]
             ↑
             └─ blocks here
```

It **doesn't normally sit on the CPU for the remaining 7 ms**.

That CPU can be given to another process:

```text
CPU:
[ A 3ms ][ B ][ C ][ D ] ...
```

When A's I/O finishes:

```
A → runnable → scheduler → CPU → continues
```

One subtle point about `iowait`

This is why **iowait is not the same as CPU utilization**.

Imagine:

```
Process A → waiting for disk
Process B → waiting for disk
Process C → waiting for disk
```

There may be no runnable process at that moment:

```
CPU
 │
 └── no runnable work
       │
       └── I/O operations in progress
```

Linux can account this period as **iowait**.

So conceptually:

```
CPU execution time
├── user
├── system
└── ...

CPU has no runnable work
├── idle
└── iowait  ← I/O-related waiting
```

The key idea is:

> **A process waiting for I/O normally releases the CPU, but the CPU may still have other processes to run.**

That's why **one process having high I/O wait doesn't necessarily mean the CPU is idle**—other processes may use the CPU while it waits.

#### 2
they release cpu time slice immediately, so why does cpu have many iowait time, i think it should always be zero

Exactly — this is a **very common point of confusion**. Your reasoning is correct about the **process**, but `iowait` is measured from the **CPU's perspective**, not from an individual process's perspective.

The key is:

> **A process releases the CPU while waiting for I/O, but `iowait` can still be recorded for the CPU during that period.**

Imagine a 4-core server

Suppose all 4 cores are doing this:

```text
Core 0 → Process A → waiting for disk
Core 1 → Process B → waiting for disk
Core 2 → Process C → waiting for disk
Core 3 → Process D → waiting for disk
```

All four processes have released their CPU time.

Now:

```text
CPU 0 ── waiting for I/O
CPU 1 ── waiting for I/O
CPU 2 ── waiting for I/O
CPU 3 ── waiting for I/O
```

There may be **no other runnable processes**.

The CPUs have nothing useful to execute, but the system is specifically waiting on I/O.

Linux can account this time as:

```text
iowait
```

Compare two situations

Situation A — genuinely idle

```text
No process needs CPU
No I/O is outstanding

        ↓

CPU has nothing to do

        ↓

idle
```

That's **idle time**.

Situation B — processes are blocked on I/O

```text
Processes need to continue
        ↓
They are blocked waiting for disk
        ↓
No runnable work
        ↓
CPU has nothing to execute
        ↓
iowait
```

That's **iowait**.

So from the CPU's perspective, both can look like:

```text
CPU isn't executing a process
```

but Linux distinguishes the reason:

```text
                 CPU not executing
                       │
             ┌─────────┴─────────┐
             │                   │
        no work needed       waiting on I/O
             │                   │
           idle               iowait
```

And this explains an important case

Suppose you have:

```text
CPU: 8 cores

7 cores → doing CPU work
1 core  → process waiting for disk
```

You might see:

```text
user/system = high
iowait      = low
```

because other CPUs are still busy.

But if:

```text
8 cores → processes all waiting for storage
```

you can see:

```text
user/system = low
iowait      = high
```

even though **none of the CPUs are actually executing application code**.

One more important Linux detail

Strictly speaking, **`iowait` does not mean "the CPU itself is waiting for I/O."** It's an accounting category indicating that there was outstanding I/O while the CPU was otherwise idle.

This distinction matters because Linux's `iowait` accounting has some subtleties, especially on multicore systems. You shouldn't interpret:

> `30% iowait = CPU spent 30% of its processing capacity doing I/O`

That interpretation is misleading.

A better mental model is:

> **High iowait means there is significant I/O-related waiting and potentially not enough other runnable work to keep the CPU busy.**

And for your HANA monitoring, that's why **high iowait is a signal to investigate storage latency/throughput**, rather than a signal that the CPU itself is overloaded.