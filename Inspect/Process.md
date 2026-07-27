
`基础信息指标 (Basic Information)`

| 中文指标 | 英文指标                  | 说明       | Linux命令                   | Windows命令                                           |
| ---- | --------------------- | -------- | ------------------------- | --------------------------------------------------- |
| 进程状态 | Process status        |          |                           |                                                     |
| 进程ID | Process ID (PID)      | 用于唯一标识进程 | `ps -ef`、`top`            | `tasklist`、`Get-Process`                            |
| 进程名称 | Process Name          | 识别进程类型   | `ps -p <pid> -o comm`     | `Get-Process                                        |
| 启动命令 | Command Line          | 启动参数及路径  | `cat /proc/<pid>/cmdline` | `Get-CimInstance Win32_Process -Filter "ProcessId=" |
| 启动时间 | Start Time            | 进程启动的时间  | `ps -p <pid> -o lstart`   | `Get-Process                                        |
| 运行时长 | Elapsed Time / Uptime | 运行了多长时间  | `ps -p <pid> -o etime`    | `(Get-Date) - (Get-Process).StartTime`              |

`CPU 指标 (CPU Metrics)`

| 中文指标         | 英文指标                 | 说明           | Linux命令                             | Windows命令                                      |
| ------------ | -------------------- | ------------ | ----------------------------------- | ---------------------------------------------- |
| CPU使用率       | CPU Usage (%)        | 占用CPU时间比例    | `top -p <pid>`、`pidstat -p <pid> 1` | `typeperf "\Process(<name>)\% Processor Time"` |
| 线程数          | Thread Count         | 当前线程总数       | `ps -p -L                           | wc -l`                                         |
| CPU核心绑定      | CPU Affinity         | 限定运行的CPU核心   | `taskset -cp <pid>`                 | `Get-Process -Id                               |
| 用户态/内核态CPU时间 | User/System CPU Time | 程序和内核占用CPU时间 | `ps -p <pid> -o time`               | `Get-Process                                   |

`内存指标 (Memory Metrics)`

| 中文指标   | 英文指标                       | 说明         | Linux命令                             | Windows命令                            |
| ------ | -------------------------- | ---------- | ----------------------------------- | ------------------------------------ |
| 常驻内存大小 | Resident Set Size (RSS)    | 实际使用的物理内存  | `ps -o pid,rss,command -p <pid>`    | `Get-Process                         |
| 虚拟内存大小 | Virtual Memory Size (VIRT) | 分配的虚拟地址空间  | `cat /proc/<pid>/status` (`VmSize`) | `Get-Process                         |
| 内存占用比例 | Memory Usage (%)           | 占系统总内存比例   | `top -p <pid>`                      | Task Manager / PerfMon               |
| 交换区使用量 | Swap Usage                 | 是否使用Swap空间 | `grep Swap /proc/<pid>/status`      | `typeperf "\Memory\Pages Input/sec"` |
| 内存增长趋势 | Memory Growth Trend        | 检查内存泄漏     | `pidstat -r -p <pid> 1`             | PerfMon趋势图                           |

`磁盘 I/O 指标 (Disk I/O Metrics)`

| 中文指标    | 英文指标                             | 说明      | Linux命令                    | Windows命令                                            |
| ------- | -------------------------------- | ------- | -------------------------- | ---------------------------------------------------- |
| 读写字节数   | I/O Read/Write Bytes             | 读写磁盘数据量 | `cat /proc/<pid>/io`       | `Get-Process                                         |
| 每秒读写次数  | Read/Write Operations per Second | I/O频率   | `pidstat -d -p <pid> 1`    | `typeperf "\Process(<name>)\IO Read Operations/sec"` |
| I/O等待时间 | I/O Wait Time                    | 是否I/O阻塞 | `iostat -x 1`、`pidstat -d` | PerfMon “Disk Queue Length”                          |
| 打开文件数   | Open File Count                  | 文件句柄数量  | `ls /proc//fd              | wc -l`                                               |

`网络指标 (Network Metrics)`

| 中文指标   | 英文指标                    | 说明                     | Linux命令            | Windows命令                                          |
| ------ | ----------------------- | ---------------------- | ------------------ | -------------------------------------------------- |
| 打开的端口  | Open Ports              | 监听端口信息                 | `ss -tp            | grep `                                             |
| 已建立连接数 | Established Connections | 当前连接数量                 | `ss -s`            | `netstat -an                                       |
| 网络流量   | Network Throughput      | 网络收发字节数                | `nethogs`、`ifstat` | `typeperf "\Network Interface(*)\Bytes Total/sec"` |
| 连接状态分布 | Connection States       | TIME_WAIT/ESTABLISHED等 | `ss -ant`          | `netstat -an`                                      |

`JVM或应用层指标 (JVM / Application Metrics)`

|中文指标|英文指标|说明|Linux命令|Windows命令|
|---|---|---|---|---|
|系统负载|System Load Average|整体CPU压力|`uptime`、`top`|Task Manager|
|可用内存|Available Memory|系统剩余内存|`free -m`|`Get-Counter "\Memory\Available MBytes"`|
|磁盘I/O利用率|Disk Utilization|磁盘压力情况|`iostat -x 1`|Resource Monitor|
|交换区活动|Swap Activity|虚拟内存使用情况|`vmstat 1`|`typeperf "\Memory\Pages/sec"`|
