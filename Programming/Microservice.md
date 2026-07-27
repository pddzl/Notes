

| Concern         | go-zero                | springcloud   |
| --------------- | ---------------------- | ------------- |
| Internal calls  | Feign                  | Built-in zrpc |
| Rate limit      | Gateway / Resilience4j | Built-in zrpc |
| Circuit Breaker | Resilience4j           | Built-in zrpc |
| 降级              |                        |               |
| Metrics         | Micrometer             | Built-in zrpc |
| Tracing         | Sleuth / Micrometer    | Built-in zrpc |

`services do NOT have to go through Gateway.  
**Gateway is only for _external_ traffic**, not internal service-to-service calls.`

Gateway: north-south traffic
service-mesh: east-west traffic

Gateway is an edge component, not a service mesh.