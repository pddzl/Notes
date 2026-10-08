### Core table relationships (Zabbix 7.x)

```text
users ──< users_groups >── usrgrp ──< rights >── hstgrp
  user      membership      user      granted      host
                            group    permission    group
```


```sql
SELECT
    u.userid,
    u.username,
    ug.name       AS user_group,
    hg.name       AS host_group,
    r.permission
FROM users u
JOIN users_groups ugmap ON u.userid = ugmap.userid
JOIN usrgrp ug ON ugmap.usrgrpid = ug.usrgrpid
JOIN rights r ON ug.usrgrpid = r.groupid
JOIN hstgrp hg ON r.id = hg.groupid
WHERE hg.name = 'Your Host Group Name';
```

### `permission` value reference

|Value|Meaning|
|---|---|
|0|Deny|
|2|Read|
|3|Read-write|

In Zabbix, host group permissions are assigned to **user groups**, not to users;  
to check a user's permissions, you must trace back from user group → host group permissions.


# 1. The Conclusion First (Most Important)

> **Zabbix permissions are split into two completely separate lines:**
> 
> 🔹 **User group** → controls _which monitoring objects (host groups, templates, etc.) you can view / modify_  
> 🔹 **Role** → controls _which features, pages, and APIs you can access / use_
> 
> 👉 **Role ≠ monitoring object permissions**

---

# 2. The Overall Zabbix Permission Model (Core)

```text
User
├── Role              → feature permissions (UI / API)
└── User group(s)
    └── Host group permission → monitoring object permissions
```

**This is the official design, not a matter of configuration habit.**

---

# 3. What Does a User Group Do? [Most Important]

## ✅ User group = the only entry point for monitoring object permissions

### What can a user group control?

- Host groups
    
- Templates
    
- Visibility of monitoring data
    
- Whether hosts / triggers / graphs can be modified
    

### Permission levels (Zabbix 7.x)

|Permission|Value|Meaning|
|---|---|---|
|Deny|0|Explicitly denied (highest priority)|
|Read|2|View only|
|Read-write|3|Can modify|

### Precedence rules (very important)

> **Deny > Read-write > Read**

A user:

- may belong to multiple user groups
    
- **as long as one group has Deny, access is denied outright**
    

---

### Where to configure it (Web UI)

`Administration → User groups → Permissions`

What you see here:

- is exactly **"whether this user can see a given host group"**
    

---

## 🔑 Takeaway 1

> **In Zabbix, every "can this user see this host?" question is answered by user groups alone.**

---

# 4. What Does a Role Do? [Often Misunderstood]

## ❌ What a role does NOT do

- ❌ Does not control host groups
    
- ❌ Does not control templates
    
- ❌ Does not control monitoring data
    

---

## ✅ What a role actually controls: feature permissions

### What does a role control?

#### 1️⃣ Page access

- Whether you can enter:
    
    - Configuration
        
    - Administration
        
    - Monitoring
        
    - Reports
        

#### 2️⃣ Action permissions

- Whether you can:
    
    - Create hosts
        
    - Modify templates
        
    - Execute scripts
        
    - Acknowledge events
        
    - Mute alerts
        

#### 3️⃣ API permissions

- Whether the API can be called
    
- Which API methods are available
    

---

### Where to configure it

`Administration → User roles`

---

## Common built-in roles (examples)

|Role|Description|
|---|---|
|Super admin|All features|
|Admin|Can manage configuration, but still limited by user groups|
|User|Read-only monitoring|
|Guest|Minimal permissions|

---

## 🔑 Takeaway 2

> **Roles decide "whether you can act";  
> user groups decide "on whom / what you can act."**

---

# 5. A Concrete Comparison Example

### Scenario: you want someone to "only view monitoring of host group A, and change nothing"

### Correct configuration ✅

1️⃣ User group

```text
A-Viewers
└── Host group A → Read
```

2️⃣ Role

`User (read-only role)`

✔ Can view A  
✔ Cannot change any configuration  
✔ Cannot see B / C

---

### ❌ Wrong understanding (a common misconception)

> "If I give him a read-only role, will he only see a subset of hosts?"

❌ **No**  
→ He would see **all host groups (if user groups impose no restriction)**

---

# 6. Why Is Zabbix Designed This Way? (Design Motivation)

### Reason 1: Decoupling

- Role: function
    
- User group: resource
    

### Reason 2: Security

- Operational permissions ≠ data visibility
    
- Prevents one role from affecting too many resources at once
    

### Reason 3: Backward compatibility

- User group permissions have existed since early Zabbix versions
    
- Roles were added later (5.2+)
    

---

# 7. The Official Permission Evaluation Order (Worth Memorizing)

When a user accesses a host, Zabbix actually evaluates, in order:

1. Is the user disabled?
2. Does the role allow access to that feature page?
3. Does the user group have permission on that host group?
4. Is there a Deny?

---

# 8. Common Misconceptions (Key Points)

|Misconception|Reality|
|---|---|
|Roles control host groups|❌|
|User groups are just a way to categorize users|❌|
|To limit visible hosts → configure roles|❌|
|To limit action capabilities → configure user groups|❌|
|Permissions seem chaotic|Usually a Deny is at play|

---

# 9. One-Sentence Ultimate Summary (Strongly Recommended to Remember)

> **The core of Zabbix permissions lies in user groups; roles are just feature switches.**
