## IAM

IAM (Identity and Access Management) is the overall system for managing:

> Who are you, and what are you allowed to access ?

```text
IAM
├── Identity Management
│   ├── Users
│   ├── Groups
│   └── Directory
│
├── Authentication
│   ├── Password
│   ├── MFA
│   ├── SSO
│   ├── Kerberos
│   ├── SAML
│   └── OIDC
│
└── Authorization
    ├── Roles / RBAC
    ├── Permissions
    ├── Access Policies
    └── OAuth 2.0
```

the big picture:

```text
                         IAM
                          │
          ┌───────────────┴────────────────┐
          │                                │
   Identity Management                 Access Management
          │                                │
          │                         ┌──────┴──────┐
          │                         │             │
          │                    Authentication  Authorization
          │                         │             │
          │                 ┌───────┼───────┐    │
          │                 │       │       │    │
          │               Password  MFA    SSO   │
          │                                 │    │
          │                          ┌──────┴─┐  │
          │                          │        │  │
          │                        SAML     OIDC │
          │                                   │  │
          │                                   │  │
          │                              OAuth 2.0
          │                                   │
          │                                   └── Authorization
          │
     Directory
          │
     ┌────┴────┐
     │         │
    AD      OpenLDAP
     │
     ├── LDAP
     └── Kerberos
```
## Authentication

Authentication answers:

> Who are you?

It verifies that a user really is the person they claim to be.

Common authentication methods include:

```text
Authentication
├── Password
├── MFA
├── Biometrics
├── Security keys
├── Kerberos
└── OIDC
```

## MFA

MFA (Multi-Factor Authentication) means:

> Using two or more different types of authentication factors to verify your identity.

The three common factor types are:

| Factor             | Meaning    | Examples                               |
| ------------------ | ---------- | -------------------------------------- |
| Something you know | Knowledge  | Password, PIN                          |
| Something you have | Possession | Phone, security key, authenticator app |
| Something you are  | Inherence  | Fingerprint, Face ID                   |

### Example

Normal password authentication:

```text
User
 │
 └── Password
       ↓
    Authenticated
```

MFA:

```text
User
 │
 ├── Password
 │       ↓
 │   Something you know
 │
 └── Authenticator code
         ↓
     Something you have 
         ↓
    Authenticated
```

For example:

```text
1. Enter password
2. Approve login on Microsoft Authenticator
3. Access granted
```

### MFA ≠ 2FA

2FA (Two-Factor Authentication) is a specific type of MFA:

```text
MFA
├── 2 factors
│     └── 2FA
└── 3+ factors
```

So:

> Every 2FA implementation is MFA, but MFA does not necessarily mean exactly two factors.

### MFA and SSO

They solve different problems:

```text
MFA
↓
How do we verify the user's identity securely?

SSO
↓
How can the user authenticate once and access multiple applications?
```

They are often used together:

```text
User
 │
 │ 1. Username + password
 ▼
Identity Provider
 │
 │ 2. MFA
 ▼
Authenticated
 │
 │ 3. SSO
 ├──────────────┬──────────────┐
 ▼              ▼              ▼
Grafana        GitLab         ITSM
```

## SSO

SSO (Single Sign-On) means:

> Log in once and access multiple applications without logging in separately to each one.

### Without SSO

```text
Microsoft 365 → username + password
Jira          → username + password
Grafana       → username + password
GitLab        → username + password
ITSM          → username + password
```

### With SSO

```text
                  ┌── Jira
                  ├── Confluence
User ──> IdP ─────┼── Grafana
                  ├── GitLab
                  └── ITSM
```

The user authenticates with a central Identity Provider (IdP), and the applications trust the IdP's authentication result.
### Common IdPs / IAM platforms

`Microsoft Entra ID`, `Keycloak`, `Okta`, `Auth0`

> AD can act as the identity source behind an IdP, but AD itself is not simply synonymous with SSO or an IdP.

### Common SSO protocols

| Protocol              | Main purpose / common use                    |
| --------------------- | -------------------------------------------- |
| SAML 2.0              | Enterprise web SSO                           |
| OpenID Connect (OIDC) | Modern web/application authentication        |
| Kerberos              | Windows / Active Directory authentication    |
| OAuth 2.0             | Authorization; commonly used underneath OIDC |

> SSO is a capability/concept; SAML and OIDC are protocols commonly used to implement it

## OAuth 2.0

OAuth 2.0 is an authorization framework.

> It allows an application to access a user's resources without the application receiving the user's password

### Example

Suppose an application wants to access your Google Drive.

```text
User
 │ 1. Start authorization
 ▼
Google
 │ 2. User authenticates
 │ 3. User grants permissions
 ▼
Authorization Code
 │ 4. App exchanges code
 ▼
Access Token
 │
 ▼
MyApp ── access token ──> Google API
```

The application receives an access token, not the user's password.

### Core components

| Component            | Meaning                                  |
| -------------------- | ---------------------------------------- |
| Resource Owner       | Usually the user who owns the data       |
| Client               | Application requesting access            |
| Authorization Server | Authenticates the user and issues tokens |
| Resource Server      | API holding protected resources          |
| Access Token         | Credential used to access resources      |
| Refresh Token        | Used to obtain new access tokens         |

### Scope

A scope limits what the application can do.

```text
scope = calendar.read
```

means:

> The application can read the calendar but does not automatically get permission to modify it.

### OAuth ≠ Authentication

OAuth answers:

> What is this application allowed to access?

It does not fundamentally answer:

> Who is this user?

For authentication, modern applications commonly use OpenID Connect (OIDC).

```text
OIDC
 │
 └── Authentication
       "Who is this user?"
             │
             ▼
        OAuth 2.0
             │
             └── Authorization
                   "What can this app access?"
```

## LDAP

LDAP (Lightweight Directory Access Protocol) is a protocol for communicating with a directory service

A directory commonly stores:

- Users
    
- Groups
    
- Organizational units
    
- Email addresses
    
- Computer accounts
    
- Other identity-related information

### Simple analogy

Think of LDAP as a **phone-book protocol**:

```text
Application
     │
     │ LDAP
     ▼
Directory Server
     │
     ├── Users
     ├── Groups
     ├── Computers
     └── Other entries
```

### LDAP data structure

LDAP uses a hierarchical Directory Information Tree (DIT).

```text
dc=example,dc=com
│
├── ou=people
│   ├── uid=jsmith
│   └── uid=alice
│
└── ou=groups
    ├── cn=developers
    └── cn=sre
```

Important terms:

| Term      | Meaning                                     |
| --------- | ------------------------------------------- |
| DIT       | Directory Information Tree                  |
| Entry     | A record in the directory                   |
| DN        | Distinguished Name; unique path to an entry |
| Attribute | Field such as `cn`, `mail`, `uid`           |
| Schema    | Defines valid entry types and attributes    |
| Bind      | Establish an LDAP session / authenticate    |
| Search    | Query directory entries                     |

### Common LDAP operations

`Bind`, `Search`, `Add`, `Modify`, `Delete`, `Compare`

### Common directory products

`Microsoft Active Directory`, `OpenLDAP`, `FreeIPA`, `389 Directory Server`

## Active Directory vs LDAP

This distinction is important:

> LDAP is a protocol. Active Directory is a directory service/product from Microsoft.

```text
                 Directory Services
                       │
              ┌────────┴────────┐
              │                 │
       Active Directory      OpenLDAP
              │
              ├── LDAP
              ├── Kerberos
              ├── DNS integration
              └── Windows domain services
```

So:

```text
LDAP ≠ AD
```

More accurately:

> AD DS provides an LDAP interface, among many other capabilities

AD also uses **Kerberos** extensively for Windows domain authentication.

## LDAP Authentication vs OAuth/OIDC

These solve different problems.
### LDAP authentication

The application directly communicates with the organization's directory:

```text
User
 │
 │ username + password
 ▼
Application
 │
 │ LDAP Bind
 ▼
Active Directory
 │
 └── "Credentials are valid"
```

The application receives the user's password because it is acting as an LDAP client.

### OAuth/OIDC

The application does not collect the user's IdP password.

```text
User
 │
 ▼
Application
 │
 │ redirect
 ▼
Identity Provider
 │
 │ user authenticates
 │
 ▼
Authorization Code / Tokens
 │
 ▼
Application
```

The application trusts the Identity Provider rather than handling the user's IdP password.

## RuoYi's admin

`RuoYi-admin` typically covers several core IAM functions:

```text
RuoYi Admin
│
├── Identity Management
│   ├── Users
│   ├── Departments
│   └── User status
│
├── Authentication
│   └── Login / session
│
├── Authorization
│   ├── Roles
│   ├── Permissions
│   ├── Menus
│   └── Data permissions
│
└── Access Management
    └── User → Role → Permission
```

That is definitely IAM territory.

But RuoYi is not necessarily a complete enterprise IAM platform

I'd distinguish them like this:

| Capability                      | RuoYi                     | Enterprise IAM |
| ------------------------------- | ------------------------- | -------------- |
| User management                 | ✅                         | ✅              |
| Groups/departments              | ✅                         | ✅              |
| RBAC                            | ✅                         | ✅              |
| Menu/API permissions            | ✅                         | ✅              |
| Data permissions                | ✅                         | ✅              |
| Login/authentication            | ✅                         | ✅              |
| SSO                             | Depends on implementation | ✅              |
| MFA                             | Usually needs extension   | ✅              |
| OIDC                            | Usually needs extension   | ✅              |
| SAML                            | Usually needs extension   | ✅              |
| OAuth 2.0 authorization server  | Usually needs extension   | ✅              |
| LDAP/AD integration             | Depends on implementation | ✅              |
| Identity lifecycle/provisioning | Limited                   | ✅              |

So I'd call RuoYi:

> an application-level IAM / access-control system

rather than:

> a full enterprise IAM/IdP platform like Keycloak, Okta, or Microsoft Entra ID.

So your intuition is basically correct: RuoYi's user/role/permission system is an IAM-like implementation, especially on the authorization side.
