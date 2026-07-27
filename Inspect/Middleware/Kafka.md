
| 分类              | 指标名称（中文）          | 指标名称（英文）                    | 说明                             | 常用命令（Command）                                                                       |
| --------------- | ----------------- | --------------------------- | ------------------------------ | ----------------------------------------------------------------------------------- |
| **基础信息**        | Kafka 版本          | Kafka Version               | 当前 Kafka 软件版本                  | `kafka-broker-api-versions.sh --bootstrap-server <broker>`                          |
|                 | Broker ID         | Broker ID                   | Kafka 节点的唯一标识符                 | `cat server.properties                                                              |
|                 | 集群节点数             | Cluster Size                | Kafka 集群中 Broker 节点数量          | `zookeeper-shell.sh <zk> ls /brokers/ids` 或 `kafka-broker-api-versions.sh`          |
|                 | 启动时间              | Start Time                  | Broker 启动时间                    | `ps -eo pid,lstart,cmd                                                              |
| **Broker 资源指标** | CPU 使用率           | CPU Usage (%)               | Kafka 进程 CPU 占用比例              | `top -p <pid>`、`pidstat -p <pid>`                                                   |
|                 | 内存使用量             | Memory Usage                | Kafka 占用的物理内存                  | `ps -o pid,rss,comm                                                                 |
|                 | 文件句柄数             | Open File Descriptors       | 检查是否接近 ulimit 限制               | `lsof -p                                                                            |
|                 | 磁盘空间使用            | Disk Usage                  | 检查日志目录占用情况                     | `du -sh /data/kafka/logs`、`df -h`                                                   |
| **Kafka 日志与目录** | 日志目录可用空间          | Log Dir Free Space          | 检查 Kafka 日志目录是否有足够空间           | `df -h /data/kafka`                                                                 |
|                 | 日志段大小             | Log Segment Size            | 检查日志段文件是否异常膨胀                  | `ls -lh /data/kafka/logs/<topic-partition>`                                         |
|                 | 日志清理状态            | Log Cleanup Status          | 检查 compaction 或 retention 是否生效 | 查看 server.log、`kafka-configs.sh --describe`                                         |
| **网络与连接**       | 监听端口              | Listener Port               | Broker 是否监听在正确端口               | `netstat -tulpn                                                                     |
|                 | 网络延迟              | Network Latency             | 客户端与 Broker 之间 RTT             | `ping`、`telnet`、`nc`                                                                |
|                 | 打开连接数             | Open Connections            | 当前 Broker TCP 连接数              | `ss -tnp                                                                            |
| **主题与分区**       | 主题总数              | Topic Count                 | Kafka 当前主题数量                   | `kafka-topics.sh --list --bootstrap-server <broker>`                                |
|                 | 分区数               | Partition Count             | 每个主题的分区数量                      | `kafka-topics.sh --describe`                                                        |
|                 | Leader 分布         | Leader Distribution         | 检查分区 Leader 是否均衡               | `kafka-topics.sh --describe                                                         |
|                 | 未分配分区             | Under Replicated Partitions | 副本同步不完整的分区数                    | `kafka-topics.sh --describe                                                         |
|                 | Offline 分区        | Offline Partitions          | 未能被任何 broker 服务的分区             | `kafka-topics.sh --describe                                                         |
| **生产消费指标**      | Producer TPS      | Producer Throughput         | 生产端写入速率                        | 通过 JMX 或 Prometheus 指标：`kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec` |
|                 | Consumer Lag      | Consumer Lag                | 消费延迟（未消费消息数）                   | `kafka-consumer-groups.sh --describe`                                               |
|                 | 消息积压              | Message Backlog             | 主题积压的消息数                       | 结合 Lag 计算或 Prometheus                                                               |
| **控制器与元数据**     | Controller 状态     | Controller Status           | 检查控制器是否正常运行                    | `grep "Controller" server.log`                                                      |
|                 | 集群元数据同步           | Metadata Sync               | 检查 broker 间元数据一致性              | `kafka-metadata-shell.sh`                                                           |
| **安全与认证**       | SASL/SSL 状态       | SASL/SSL Status             | 检查认证配置                         | `cat server.properties                                                              |
|                 | 证书有效期             | Certificate Expiry          | SSL 证书是否过期                     | `openssl x509 -in server.crt -text -noout`                                          |
| **监控与报警**       | JMX 暴露            | JMX Metrics                 | 确认是否暴露给 Prometheus 或其他监控       | `netstat -tlnp                                                                      |
|                 | Kafka Exporter 状态 | Kafka Exporter              | Prometheus exporter 是否采集正常     | `curl <exporter>:9308/metrics`                                                      |
| **高可用与灾备**      | ISR 同步状态          | In-Sync Replica             | 副本同步是否正常                       | `kafka-topics.sh --describe                                                         |
|                 | 复制延迟              | Replica Lag                 | 副本复制延迟情况                       | `kafka-replica-verification.sh`                                                     |
|                 | 数据副本数             | Replication Factor          | 是否满足冗余要求                       | `kafka-topics.sh --describe`                                                        |