## What JPA actually is

**JPA = Java Persistence API**

- It is a **specification (standard)**, not a framework
    
- Defines **interfaces + annotations + behavior**
    
- Implemented by frameworks like:
- 
    - **Hibernate**
    - EclipseLink    
    - OpenJPA
    
JPA is about **ORM (Object–Relational Mapping)**.

## What MyBatis is

**MyBatis is NOT ORM.**

- It is a **SQL Mapper framework**
- You write SQL (XML / annotations)
- Maps **SQL result → Java object**
- No entity lifecycle
- No persistence context
- No dirty checking

## Relationship between MyBatis and JPA

| Aspect            | JPA               | MyBatis         |
| ----------------- | ----------------- | --------------- |
| Standard          | ✅ Yes             | ❌ No            |
| ORM               | ✅ Yes             | ❌ No            |
| SQL ownership     | Framework         | Developer       |
| Entity lifecycle  | Managed           | Not managed     |
| Dirty checking    | Yes               | No              |
| First-level cache | Yes               | Optional        |
| Lazy loading      | Yes               | Limited         |
| Spec provider     | Java EE / Jakarta | MyBatis project |