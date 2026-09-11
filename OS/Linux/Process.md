## Concept

A process in Linux is a running instance of a program.

The easiest way to think about it:

> Program = a file containing instructions  
> Process = that program while it is running

Example

You have a Java application:

```bash
/usr/bin/java -jar app.jar
```

`/usr/bin/java` is the program (executable). When you run it:

```bash
java -jar app.jar
```

Linux creates a process, for example:

```text
PID     NAME    CMD
79075   java    java -jar app.jar
```

## What Does a Process Contain?

A process isn't just the executable. Linux gives it resources and state:

```text
Process
├── PID                  → process ID
├── Memory               → code, heap, stack, etc.
├── CPU state            → registers, execution state
├── Open files           → file descriptors
├── Network connections
├── Environment variables
├── Current directory
├── User / permissions
├── Parent process (PPID)
└── Command line
```

That's why when you inspect:

```bash
cat /proc/79075/
```

you can see a lot of information about that running process.

## Program vs Process

Run the same program twice:

```bash
java -jar app.jar
java -jar app.jar
```

You get two separate processes:

```text
             Program
                │
       ┌────────┴────────┐
       ↓                 ↓
   Process 1          Process 2
   PID 1000           PID 2000
```

Both processes use the same program, but each has its own memory, PID, file descriptors, etc.

## Key Terms

| Concept            | Meaning                                                   | Example                           |
| ------------------ | --------------------------------------------------------- | --------------------------------- |
| PID                | Process ID                                                | `79075`                           |
| Process name       | Short executable/process name                             | `java`                            |
| Command line (CMD) | How the process was actually started, including arguments | `java -Xms2g -Xmx4g -jar app.jar` |
| Executable         | Actual executable file                                    | `/usr/bin/java`                   |
| PPID               | Parent process ID                                         | `1234`                            |

## Inspecting Processes

### List all processes

```bash
ps -ef
```

This essentially asks Linux: *"Show me all currently running processes."*

```text
root      1234     1  ...  nginx
oracle    5678     1  ...  ora_pmon_DB1
osadmin  79075  1234  ...  java -jar app.jar
```

### A more useful format

```bash
ps -eo pid,ppid,comm,args
```

```text
PID     PPID  COMMAND  COMMAND
79075   1234  java     java -Xms2g -Xmx4g -jar app.jar
```

- `comm` → process name
- `args` → full command line

### Inspect a specific process

```bash
ps -p 79075 -o pid,ppid,comm,args
```

```text
    PID    PPID COMMAND COMMAND
  79075    1234 java    java -Xms2g -Xmx4g -jar app.jar
```

## Inspecting `/proc`

Linux exposes process information under:

```bash
/proc/<PID>/
```

### Process name

```bash
cat /proc/79075/comm
```

```text
java
```

### Full command line

```bash
cat /proc/79075/cmdline
```

You may see:

```text
java -Xms2g -Xmx4g -jar app.jar
```

because arguments are separated by **NUL (`\0`)**, not spaces. Use `tr` to convert them:

```bash
tr '\0' ' ' < /proc/79075/cmdline
```

```text
java -Xms2g -Xmx4g -jar app.jar
```

### Actual executable

```bash
readlink -f /proc/79075/exe
```

```text
/usr/lib/jvm/java/bin/java
```

This lets you distinguish three different things:

```text
Process name : java
Command line : java -Xms2g -Xmx4g -jar app.jar
Executable   : /usr/lib/jvm/java/bin/java
```

### Environment variables

```bash
tr '\0' '\n' < /proc/79075/environ
```

### Working directory

```bash
readlink -f /proc/79075/cwd
```

### Root directory

```bash
readlink -f /proc/79075/root
```

### Parent process

```bash
awk '{print $4}' /proc/79075/stat
```

Or easier:

```bash
ps -p 79075 -o ppid=
```

### Process limits

Particularly useful for open-files/handle investigations:

```bash
cat /proc/79075/limits
```

```text
Max open files            1024                 524288               files
```

- **Soft limit** = `1024`
- **Hard limit** = `524288`

## Memory & CPU Usage

Inspect resource usage of a specific process:

```bash
ps -p 79075 -o pid,comm,%cpu,%mem,rss,vsz
```
