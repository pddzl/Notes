
create index
```shell
db.collection.createIndex({ cloudPlatformId: 1 }, { unique: true })
db.collection.createIndex({ hostname: 1 }, { unique: true })
db.collection.createIndex({ ip: 1 }, { unique: true })
```