In Zabbix, the **notification workflow** is separate from the permission workflow you described above.

The simplest mental model is:

```text
Metric / Item
     │
     ▼
Trigger expression
     │
     │ condition becomes TRUE
     ▼
   Problem
     │
     ▼
   Event
     │
     ▼
   Action
     │
     ├── Conditions match?
     │
     ├── User / User group?
     │
     ├── Media type?
     │
     └── Severity / schedule / other conditions?
     │
     ▼
 Notification
     │
     ▼
Email / DingTalk / WeChat / Webhook / etc.
```

### 1. Item collects data

For example:

```text
system.cpu.util = 95%
```

Zabbix receives this value through an item.

```text
Host
 └── Item
      └── system.cpu.util
```

The item itself **does not normally send the notification**.

---

### 2. Trigger evaluates the data

Suppose you have:

```text
last(/server/system.cpu.util)>90
```

When CPU goes above 90%:

```text
95%
 │
 ▼
Trigger expression = TRUE
```

The trigger changes from:

```text
OK → PROBLEM
```

This transition generates a **Problem event**.

---

### 3. Event is created

This is an important distinction:

```text
Trigger
   │
   │ state changes
   ▼
Event
```

For example:

```text
Event
├── Event ID
├── Host
├── Problem name
├── Severity = High
├── Time
└── Related trigger
```

The **event** is what Zabbix evaluates against Actions.

---

### 4. Action evaluates the event

This is where notification logic happens.

An Action might have conditions such as:

```text
Event source = Trigger
AND
Event severity >= High
AND
Host group = Production
```

If the event matches:

```text
Problem Event
      │
      ▼
Action conditions
      │
      ├── Match → Operations
      │
      └── No match → Nothing
```

This is why **Trigger ≠ Notification**.

A trigger detects the problem.

An action decides what to do about the event.

---

### 5. Operations determine who gets notified

Inside the Action, you define operations such as:

```text
Operation
├── Send message to User A
├── Send message to User Group "SRE"
└── Send via Media Type "DingTalk"
```

For example:

```text
CPU > 90%
    │
    ▼
Trigger → PROBLEM
    │
    ▼
Event
    │
    ▼
Action
    │
    ├── Severity >= High
    ├── Host Group = Production
    │
    ▼
Operation
    │
    └── User Group = SRE
             │
             ▼
          DingTalk
```

---

### 6. Media type determines how the message is delivered

The user needs a configured **media**.

For example:

```text
User
 └── Media
      ├── Email
      ├── DingTalk
      ├── Webhook
      └── SMS
```

The Action chooses the recipient and media type.

So the complete chain is:

```text
Item
 │
 ▼
Trigger
 │
 │ condition becomes TRUE
 ▼
Event
 │
 ▼
Action
 │
 │ conditions
 ▼
Operation
 │
 │ recipient + media
 ▼
Media Type
 │
 ▼
External system
```

## Recovery is a separate event

When the problem disappears:

```text
CPU = 95%
     │
     ▼
PROBLEM
     │
     │ notification
     ▼
DingTalk

...later...

CPU = 40%
     │
     ▼
OK / RECOVERY
     │
     ▼
Recovery event
     │
     ▼
Action recovery operations
     │
     ▼
DingTalk
```

So you can have:

```text
Problem event  → "CPU is too high"
Recovery event → "CPU has recovered"
```

### One important distinction from your previous permission model

Permissions answer:

```text
"Is this user allowed to see/do something?"
```

Notification configuration answers:

```text
"Who should Zabbix notify when this event happens?"
```

Therefore:

```text
                 Zabbix
                   │
        ┌──────────┴──────────┐
        │                     │
    Permissions          Event/Alerting
        │                     │
   Can user do it?       Should we notify?
        │                     │
   Role + ACL          Trigger → Event → Action
```

And **Actions are doing a different job in these two concepts**: the role has action/capability permissions such as "acknowledge problems," while an **Action** in Zabbix's event system is the automation/notification rule that reacts to events.
