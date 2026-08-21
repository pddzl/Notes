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

