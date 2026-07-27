### 核心表关系（Zabbix 7.x）

```shell
users
users_groups 
usrgrp 
rights 
hstgrp
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

### `permission` 值说明

|值|含义|
|---|---|
|0|Deny|
|2|Read|
|3|Read-write|

Zabbix 中主机组权限是分配给“用户组”的，而不是用户；  
想看用户权限，必须从“用户组 → 主机组权限”反查。


# 一、一句话先给结论（最重要）

> **Zabbix 的权限分成两条完全不同的线：**
> 
> 🔹 **用户组（User group）** → 控制 _能看 / 能改 哪些监控对象（主机组、模板等）_  
> 🔹 **角色（Role）** → 控制 _能不能看到 / 使用 哪些功能、页面、API_
> 
> 👉 **角色 ≠ 监控对象权限**

---

# 二、Zabbix 权限整体模型（核心）

`User  ├── Role            → 功能权限（UI / API）  └── User group(s)         └── Host group permission → 监控对象权限`

**这是官方设计，不是配置习惯问题。**

---

# 三、用户组（User group）是干什么的？【最重要】

## ✅ 用户组 = 监控对象权限的唯一入口

### 用户组能控制什么？

- 主机组（Host group）
    
- 模板（Template）
    
- 监控数据可见性
    
- 是否能修改主机 / 触发器 / 图形
    

### 权限级别（Zabbix 7.x）

|权限|含义|
|---|---|
|Deny|明确禁止（最高优先级）|
|Read|只能查看|
|Read-write|可以修改|

### 生效规则（非常重要）

> **Deny > Read-write > Read**

一个用户：

- 属于多个用户组
    
- **只要有一个 Deny，就直接拒绝**
    

---

### 设置路径（Web UI）

`Administration → User groups → Permissions`

你在这里看到的：

- 才是 **“这个用户能不能看到某个主机组”**
    

---

## 🔑 结论 1

> **Zabbix 中，所有“能不能看到某台主机”的问题，都只看用户组。**

---

# 四、角色（Role）是干什么的？【经常被误解】

## ❌ 角色不是干这个的

- ❌ 不控制主机组
    
- ❌ 不控制模板
    
- ❌ 不控制监控数据
    

---

## ✅ 角色真正控制的是：功能权限

### 角色控制什么？

#### 1️⃣ 页面访问权限

- 是否能进入：
    
    - Configuration
        
    - Administration
        
    - Monitoring
        
    - Reports
        

#### 2️⃣ 操作权限

- 能不能：
    
    - 创建主机
        
    - 修改模板
        
    - 执行脚本
        
    - 确认事件
        
    - 静默告警
        

#### 3️⃣ API 权限

- API 是否可调用
    
- 哪些 API 方法可用
    

---

### 设置路径

`Administration → User roles`

---

## 常见内置角色（示例）

|角色|说明|
|---|---|
|Super admin|所有功能|
|Admin|管理配置，但受用户组限制|
|User|只读监控|
|Guest|极少权限|

---

## 🔑 结论 2

> **角色决定“你能不能操作”，  
> 用户组决定“你能操作谁 / 看谁”。**

---

# 五、一个非常直观的对比例子

### 场景：你想让某人“只能看 A 主机组的监控，不允许改任何东西”

### 正确配置方式 ✅

1️⃣ 用户组

`A-Viewers   └── Host group A → Read`

2️⃣ 角色

`User（只读角色）`

✔ 能看 A  
✔ 不能改任何配置  
✔ 看不到 B / C

---

### ❌ 错误理解（很多人这样想）

> “我给他一个只读角色，是不是就只能看到部分主机？”

❌ **不是**  
→ 他会看到 **所有主机组（如果用户组没限制）**

---

# 六、为什么 Zabbix 要这样设计？（设计动机）

### 原因 1：解耦

- 角色：功能（Function）
    
- 用户组：资源（Resource）
    

### 原因 2：安全

- 运维权限 ≠ 数据可见性
    
- 防止一个角色同时影响太多资源
    

### 原因 3：兼容历史版本

- Zabbix 很早就有用户组权限
    
- 角色是后期增强（5.2+）
    

---

# 七、官方级“权限判断顺序”（你可以记住）

当用户访问一个主机时，Zabbix 实际判断：

`1. 用户是否被禁用 2. 角色是否允许访问该功能页面 3. 用户组是否对该主机组有权限 4. 是否存在 Deny`

---

# 八、常见误区总结（重点）

|误区|正解|
|---|---|
|角色能控制主机组|❌|
|用户组只是用户分类|❌|
|想限制可见主机 → 配角色|❌|
|想限制操作能力 → 配用户组|❌|
|权限乱|通常是 Deny 在作怪|

---

# 九、一句话终极总结（强烈推荐你记住）

> **Zabbix 的权限核心在“用户组”，角色只是功能开关。**
