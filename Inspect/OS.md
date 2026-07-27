| 分类           | 指标名称（中文） | 指标名称（英文）            | 说明               | 常用命令（Command）                      |
| ------------ | -------- | ------------------- | ---------------- | ---------------------------------- |
| **系统信息**     | 主机名      | Hostname            | 操作系统主机名称         | `hostname` / `hostnamectl`         |
| **系统信息**     | 操作系统版本   | OS Version          | 系统发行版与内核版本       | `cat /etc/os-release` / `uname -r` |
| **系统信息**     | 启动时间     | Uptime              | 系统运行时长           | `uptime`                           |
| **系统信息**     | 当前登录用户   | Logged-in Users     | 当前系统登录用户         | `who` / `w`                        |
| **系统信息**     | 系统时钟同步   | NTP Sync Status     | 系统时间同步状态         | `timedatectl` / `ntpq -p`          |
| **CPU**      | CPU 利用率  | CPU Utilization (%) | 总体 CPU 使用百分比     | `top` / `mpstat`                   |
| **内存**       | 内存使用率    | Memory Usage (%)    | 当前内存使用百分比        | `free -m` / `top`                  |
| **磁盘 / I/O** | 磁盘空间使用率  | Disk Usage (%)      | 文件系统使用百分比        | `df -h`                            |
| **网络**       | 活动连接数    | Active Connections  | 当前 TCP/UDP 连接数量  | `netstat -an                       |
| **系统负载**     | 系统平均负载   | System Load Average | 最近 1/5/15 分钟平均负载 | `uptime` / `top`                   |
| **安全与稳定性**   | 系统日志错误   | System Log Errors   | 关键错误与告警日志        | `journalctl -p err` / `dmesg`      |
| **资源限制与配额**  | 打开文件句柄数  | Open File Handles   | 当前系统打开文件数        | `lsof                              |
| **计划任务与服务**  | 定时任务     | Scheduled Tasks     | 定时任务计划           | `crontab -l`                       |
