### MySQL
```shell
docker run -p 3306:3306 --name mysql -v /Users/paul/data/mysql:/var/lib/mysql -e MYSQL_ROOT_PASSWORD=td27admin -d mysql:8.0.28-oracle --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci

```


MongoDB
```
docker run -d --name mongodb -p 27017:27017 -e MONGO_INITDB_ROOT_USERNAME=trina_sre -e MONGO_INITDB_ROOT_PASSWORD=trina_123 mongodb/mongodb-community-server:latest
```
