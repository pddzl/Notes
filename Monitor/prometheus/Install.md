

```shell
mkdir /data/app && cd /data/app
mv /tmp/prometheus-3.7.2.linux-amd64.tar.gz /data/app && tar -zxv -f prometheus-3.7.2.linux-amd64.tar.gz
ln -s prometheus-3.7.2.linux-amd64 prometheus
```

```shell
useradd --no-create-home --shell /bin/false prometheus
chown -R prometheus:prometheus /data/app/prometheus*
touch /etc/systemd/system/prometheus.service
```

`/etc/systemd/system/prometheus.service`
```shell
[Unit]
Description=Prometheus Monitoring System
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/data/app/prometheus/prometheus \
  --config.file=/data/app/prometheus/prometheus.yml \
  --storage.tsdb.path=/data/app/prometheus/data \
  --web.listen-address=:9090 \
  --web.enable-lifecycle

Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```shell
systemctl daemon-reload
systemctl enable prometheus
```

```shell
journalctl -u prometheus -xe
```

