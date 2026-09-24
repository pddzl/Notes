Dashboard

node_exporter: 1860

`predict`

```shell
100 - (

(predict_linear(node_filesystem_avail_bytes{instance="$node", job="$job", fstype!~"tmpfs|overlay"}[7d], 24 * 3600))

/ node_filesystem_size_bytes{instance="$node", job="$job", fstype!~"tmpfs|overlay"}

) * 100
```

kafka_exporter: 7589