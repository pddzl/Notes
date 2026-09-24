`select the last increment id of table`

```sql
SELECT AUTO_INCREMENT  
FROM information_schema.TABLES  
WHERE TABLE_SCHEMA = 'your_database'  
  AND TABLE_NAME = 'your_table_name';
```

`reset increment id`

```sql
ALTER TABLE your_table_name AUTO_INCREMENT = 1;
```

`charset`

| Collation            | Case-sensitive? | Notes                                                |
| -------------------- | --------------- | ---------------------------------------------------- |
| `utf8mb4_general_ci` | ❌ No            | “ci” = case-insensitive                              |
| `utf8mb4_unicode_ci` | ❌ No            | Unicode-aware, but still case-insensitive            |
| `utf8mb4_0900_ai_ci` | ❌ No            | Accent- & case-insensitive (MySQL 8+)                |
| `utf8mb4_bin`        | ✅ Yes           | “bin” = binary comparison (case-sensitive)           |
| `utf8mb4_general_cs` | ✅ Yes           | “cs” = case-sensitive (rare, but exists in MySQL 8+) |