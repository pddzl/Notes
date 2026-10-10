Yes — this is a good architectural model of **Zabbix 7.x permissions**. I would make one important terminology adjustment and simplify it into a model that is easier to use when configuring Zabbix.

## Zabbix 7.x Permission Model

Think of Zabbix permissions as **two layers**:

```text
                    ┌─────────────────────────┐
                    │          User           │
                    └────────────┬────────────┘
                                 │
                         member of groups
                                 │
              ┌──────────────────┴──────────────────┐
              │                                     │
      ┌───────▼────────┐                    ┌───────▼────────┐
      │      Role      │                    │  User Group    │
      │                │                    │                │
      │ What can I do? │                    │ What data can  │
      │                │                    │ I access?      │
      └───────┬────────┘                    └───────┬────────┘
              │                                     │
       ┌──────▼──────┐                    ┌─────────▼─────────┐
       │ UI / API /  │                    │ Host Group        │
       │ Actions     │                    │ permissions       │
       └─────────────┘                    └───────────────────┘
```

### 1. Role = What can the user do?

A **role** controls the user's capabilities.

For example:

| Role permission | Meaning                                                                                 |
| --------------- | --------------------------------------------------------------------------------------- |
| UI elements     | Which Zabbix frontend sections/features are accessible                                  |
| API methods     | Which API operations are allowed                                                        |
| Actions         | Whether the user can acknowledge/close problems, execute scripts, edit dashboards, etc. |
| Module access   | Access to frontend modules                                                              |

So:

> **Role answers: "What am I allowed to do?"**

For example:

```text
User
  ↓
Operator role
  ↓
Can:
  ✓ View Monitoring
  ✓ Acknowledge problems
  ✓ Change severity
  ✗ Manage users
  ✗ Manage authentication
  ✗ Modify system configuration
```

Importantly, hiding something in the UI is **not merely cosmetic**. Role restrictions also apply to the corresponding server-side/API operations.

---

# 2. User Group = Where does the user get access?

A user group connects users with both:

```text
User Group
├── Role
└── Host Group permissions
```

For example:

```text
Linux Operations
│
├── Role: Operator
│
├── Linux Production → Read-write
├── Linux Development → Read
└── Windows → Deny
```

Therefore, being an **Operator** does not automatically mean the user can operate every host in Zabbix.

The role says:

> "You are allowed to perform this kind of operation."

The host-group permission says:

> "You are allowed to perform it on these hosts."

---

# 3. Host Group Permission = Which data can the user access?

This is the **data-scope layer**.

Typical permissions are:

```text
Deny
Read
Read-write
Read-write + tag filter
```

For example:

```text
                    Operator role
                         │
                         ▼
                  ┌──────────────┐
                  │ User Group   │
                  │ Linux Ops    │
                  └──────┬───────┘
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
        Production     Dev       Windows
        Read-write      Read       Deny
```

So the same user might be able to:

```text
Production Linux
    → acknowledge problems
    → close problems
    → modify configuration

Development Linux
    → view problems
    → cannot modify

Windows
    → cannot access
```

---

# 4. The key distinction

This is probably the most important thing to remember:

```text
Role
  ↓
WHAT can I do?

Host-group permission
  ↓
WHERE can I do it?
```

Or:

```text
Capability × Data Scope
```

For an operation to succeed, **both** need to allow it.

For example:

```text
User wants to close a problem
             │
             ├── Role
             │     └── "Close problems" = YES
             │
             └── Host-group permission
                   └── Target host = Read-write
                              │
                              ▼
                           SUCCESS
```

But:

```text
User wants to close a problem
             │
             ├── Role
             │     └── "Close problems" = YES
             │
             └── Host-group permission
                   └── Target host = Read
                              │
                              ▼
                           DENIED
```

So your statement:

> A user can have "Close problems" action but read-only host access — then they can't actually close anything.

is exactly the useful way to think about it.

---

# 5. Your three headings

If you're documenting this for your Zabbix notes, I would structure it as:

````markdown
# Zabbix 7.x Permissions

Zabbix permissions consist of two main layers:

1. Role-based capabilities
2. Host-group-based data access

## Role

Controls **what the user can do**.

### Access to UI elements

Controls which frontend sections/features the user can access.

### Access to API

Controls which API methods the user's role can call.

### Actions

Controls specific operations such as:

- Acknowledge problems
- Close problems
- Change severity
- Execute scripts
- Manage dashboards
- Manage API tokens
- Manage maintenance
- Manage scheduled reports

### Module access

Controls access to frontend modules.

---

## User Group

A user group connects users with:

- Roles
- Host-group permissions

A user can belong to multiple groups.

The effective permissions are determined from the user's group memberships.

---

## Host Group Permissions

Controls **which monitoring data the user can access**.

| Permission | Meaning |
|---|---|
| Deny | No access |
| Read | Can view monitoring data |
| Read-write | Can view and modify |
| Read-write + tag filter | Read-write access limited by tags |

Host permissions are assigned between:

`User Group → Host Group`

---

## Permission Evaluation

A user's effective access depends on both:

`Role capability + Host-group permission`

Role:

> What can the user do?

Host-group permission:

> Where can the user do it?

Example:

```text
Role:
  Close problems = Yes

Host group:
  Production = Read-write
  Development = Read
  Windows = Deny
````

Result:

```text
Production → Can close problems
Development → Cannot close problems
Windows → Cannot access problems
```

```

One small correction to your original architecture: I would **not describe Zabbix simply as "RBAC + ACL"** if this is intended as a precise technical document. A better description is:

> **Zabbix uses role-based capability control combined with user-group/host-group-based data access control.**

That makes the separation between **capability** and **scope** much clearer.
```
