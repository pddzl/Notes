### Install

```shell
mkdir /data/app && cd /data/app
mv /tmp/node_exporter-1.10.2.linux-amd64.tar.gz /data/app && tar -zxv -f node_exporter-1.10.2.linux-amd64.tar.gz
ln -s node_exporter-1.10.2.linux-amd64 node_exporter
```

```shell
useradd --no-create-home --shell /bin/false node_exporter
chown -R node_exporter:node_exporter /data/app/node_exporter*
touch /etc/systemd/system/node_exporter.service
```

`/etc/systemd/system/node_exporter.service`
```shell
[Unit]
Description=Prometheus Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/data/app/node_exporter/node_exporter --web.listen-address=:59100

[Install]
WantedBy=multi-user.target
```

```shell
systemctl daemon-reload
systemctl enable node_exporter
```

```shell
journalctl -u node_exporter -xe
```

### Metric

Why “root” appears in filesystem metrics

In Linux, a small portion of disk space (usually 5%) is **reserved for the root user** to prevent full-disk crashes.  
That’s why we have two metrics in node_exporter:

- **`node_filesystem_free_bytes`** → total free space, _including_ root’s reserved part
    
- **`node_filesystem_avail_bytes`** → free space _excluding_ root’s reserved part (usable by normal users/apps)
    

So:

> Even when an app sees “disk full”, `root` might still be able to write — thanks to that reserved space.

| Metric                        | Meaning             | Value  |
| ----------------------------- | ------------------- | ------ |
| `node_filesystem_size_bytes`  | Total size          | 100 GB |
| `node_filesystem_free_bytes`  | Free including root | 10 GB  |
| `node_filesystem_avail_bytes` | Free for users      | 5 GB   |



