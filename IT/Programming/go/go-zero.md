
```shell
 protoc \   
  --proto_path=proto \
  --go_out=types \
  --go-grpc_out=types \
  --go_opt=paths=source_relative \
  --go-grpc_opt=paths=source_relative \
  proto/common/common.proto \
  proto/authority/user.proto
```


```shell
/Users/paul/Mine/td27-admin-micro/rpc/basis
```