
### Install

```shell
mkdir /data/app && cd /data/app
mv /tmp/kafka_exporter-1.9.0.linux-amd64.tar.gz . && tar -zxv -f kafka_exporter-1.9.0.linux-amd64.tar.gz
ln -s kafka_exporter-1.9.0.linux-amd64 kafka_exporter
```

```shell
useradd --no-create-home --shell /bin/false kafka_exporter
chown -R kafka_exporter:kafka_exporter /data/app/kafka_exporter*
touch /etc/systemd/system/kafka_exporter.service
```

`/etc/systemd/system/kafka_exporter.service`
```shell
[Unit]
Description=Kafka Exporter for Prometheus
After=network.target
[Service]
User=kafka_exporter
Group=kafka_exporter
Type=simple
ExecStart=/data/app/kafka_exporter/kafka_exporter \
  --kafka.server=10.17.6.155:9092 \
  --web.listen-address=:59308
Restart=on-failure
[Install]
WantedBy=multi-user.target
```

```shell
systemctl daemon-reload
systemctl enable kafka_exporter
```

```shell
journalctl -u kafka_exporter -xe
```