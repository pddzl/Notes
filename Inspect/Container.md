| 分类           | 指标名称（中文）      | 指标名称（英文）         | 说明           | 常用命令（Command）                                                  |
| ------------ | ------------- | ---------------- | ------------ | -------------------------------------------------------------- |
| **基础信息**     | 容器 ID         | Container ID     | 唯一标识容器实例     | `docker ps -q`                                                 |
| **基础信息**     | 容器名称          | Container Name   | 容器逻辑名称       | `docker ps --format '{{.Names}}'`                              |
| **基础信息**     | 镜像名称          | Image Name       | 容器所用镜像       | `docker inspect --format '{{.Config.Image}}' <id>`             |
| **CPU**      | CPU 使用率       | CPU Usage (%)    | 容器 CPU 占用百分比 | `docker stats --no-stream`                                     |
| **CPU**      | CPU 限制        | CPU Limit        | 容器可用 CPU 限制  | `docker inspect -f '{{.HostConfig.NanoCpus}}' <id>`            |
| **内存**       | 内存使用量         | Memory Usage     | 当前容器占用内存     | `docker stats --no-stream`                                     |
| **网络**       | 网络入流量         | Network RX Bytes | 接收流量         | `docker exec <id> cat /sys/class/net/eth0/statistics/rx_bytes` |
| **网络**       | 网络出流量         | Network TX Bytes | 发送流量         | `docker exec <id> cat /sys/class/net/eth0/statistics/tx_bytes` |
| **存储 / I/O** | 块 I/O         | Block I/O        | 容器磁盘读写字节数    | `docker stats --no-stream`                                     |
| **健康状态**     | 健康检查结果        | Health Status    | 健康检查是否通过     | `docker inspect -f '{{.State.Health.Status}}' <id>`            |
| **资源限制**     | cgroup CPU 限制 | Cgroup CPU Limit | 容器 CPU 限制值   | `cat /sys/fs/cgroup/cpu.max`                                   |
| **宿主机关联**    | 宿主机节点名        | Host Node Name   | 容器所在宿主机      | `hostname`                                                     |