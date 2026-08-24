
`kafka_2.13-4.1.0.tgz`

`KRaft 模式`

```shell
# 创建用户和组
sudo useradd -r -m -s /bin/bash kafka
```

```shell
cd /data
ln -s kafka_2.13-4.1.0 kafka
chown -R kafka:kafka kafka*
```

### Install JDK
kafka 4.1.0 works with JDK 11 or JDK 17

Install Amazon Corretto 17 on CentOS 7
```shell
# Import Amazon Corretto repo
sudo rpm --import https://yum.corretto.aws/corretto.key
sudo curl -Lo /etc/yum.repos.d/corretto.repo https://yum.corretto.aws/corretto.repo

# Install JDK 17
sudo yum install -y java-17-amazon-corretto java-17-amazon-corretto-devel
```

`/data/kafka/config/server.properties`

```shell
process.roles=broker,controller
node.id=1
controller.quorum.voters=1@10.168.99.39:19093,2@10.168.99.40:19093,3@10.168.99.41:19093

# listeners
listeners=PLAINTEXT://10.168.99.39:19092,CONTROLLER://10.168.99.39:19093
inter.broker.listener.name=PLAINTEXT
listener.security.protocol.map=PLAINTEXT:PLAINTEXT,CONTROLLER:PLAINTEXT
controller.listener.names=CONTROLLER

# logs and performance
log.dirs=/data/kafka/data
num.partitions=3
num.network.threads=3
num.io.threads=8
socket.send.buffer.bytes=102400
socket.receive.buffer.bytes=102400
socket.request.max.bytes=104857600

# retention
log.retention.hours=720
log.retention.bytes=1073741824
log.segment.bytes=1073741824
log.retention.check.interval.ms=300000
log.cleaner.enable=true

# replication
offsets.topic.replication.factor=3
transaction.state.log.replication.factor=3
transaction.state.log.min.isr=2
num.recovery.threads.per.data.dir=1
```

if you wanna add external port
```shell
process.roles=broker,controller
node.id=1
controller.quorum.voters=1@10.160.173.100:18171,2@10.160.173.101:18171,3@10.160.173.122:18171

# 监听配置
listeners=PLAINTEXT_INTERNAL://10.160.173.100:17108,PLAINTEXT_EXTERNAL://10.160.173.100:18108,CONTROLLER://10.160.173.100:18171
advertised.listeners=PLAINTEXT_INTERNAL://10.160.173.100:17108,PLAINTEXT_EXTERNAL://58.216.51.80:18108
listener.security.protocol.map=PLAINTEXT_INTERNAL:PLAINTEXT,PLAINTEXT_EXTERNAL:PLAINTEXT,CONTROLLER:PLAINTEXT
inter.broker.listener.name=PLAINTEXT_INTERNAL
controller.listener.names=CONTROLLER

# 日志与性能优化
log.dirs=/data/app/kafka/data/
num.partitions=3
num.network.threads=3
num.io.threads=8
socket.send.buffer.bytes=102400
socket.receive.buffer.bytes=102400
socket.request.max.bytes=104857600

# 日志保留策略
log.retention.hours=168
log.retention.bytes=1073741824
log.segment.bytes=1073741824
log.retention.check.interval.ms=300000
log.cleaner.enable=true

# 事务日志与副本配置
offsets.topic.replication.factor=3
transaction.state.log.replication.factor=3
transaction.state.log.min.isr=2
num.recovery.threads.per.data.dir=1
```

### format storage

generate random-uuid
```shell
/data/kafka/bin/kafka-storage.sh random-uuid
```

format storage in each node
```shell
/data/kafka/bin/kafka-storage.sh format -t IaGRZyqFTQexJEDkauFEEQ -c /data/kafka/config/server.properties
```

### systemd service file

`/etc/systemd/system/kafka.service`
```shell
[Unit]
Description=Apache Kafka Server
After=network.target

[Service]
Type=simple
User=kafka
Group=kafka
ExecStart=/data/kafka/bin/kafka-server-start.sh /data/kafka/config/server.properties
ExecStop=/data/kafka/bin/kafka-server-stop.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```
```shell
systemctl daemon-reload
systemctl enable kafka
```

```shell
journalctl -u kafka -n 100 --no-pager
```

create topic
```shell
/data/kafka/bin/kafka-topics.sh \
  --create \
  --topic cloudplatform-virtualhost \
  --bootstrap-server 10.168.99.39:19092,10.168.99.40:19092,10.168.99.41:19092 \
  --partitions 3 \
  --replication-factor 3
```

Delete topic
```shell
/data/kafka/bin/kafka-topics.sh \
  --delete \
  --topic cloudplatform-virtualhost \
  --bootstrap-server 10.168.99.39:19092,10.168.99.40:19092,10.168.99.41:19092
```

List Topic
```shell
/data/kafka/bin/kafka-topics.sh --list --bootstrap-server 10.168.99.39:19092
```