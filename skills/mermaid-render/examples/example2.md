# Mermaid Examples

## 1. Flowchart -- HTTP Request Lifecycle

```mermaid
---
title: Flowchart -- HTTP Request Lifecycle
---

flowchart LR
    Client([🌐 Client]) -->|HTTPS Request| LB[Load Balancer]
    LB --> GW[API Gateway]
    GW -->|Auth check| Auth[(Auth Service)]
    Auth -->|✅ Valid| GW
    GW --> SVC[Microservice]
    SVC -->|Query| DB[(PostgreSQL)]
    SVC -->|Cache hit?| Redis[(Redis)]
    Redis -->|Miss| DB
    DB --> SVC
    SVC -->|JSON response| GW
    GW --> LB
    LB --> Client

    style Client fill:#4F46E5,color:#fff
    style DB fill:#059669,color:#fff
    style Redis fill:#DC2626,color:#fff
    style Auth fill:#D97706,color:#fff
```

## 2. Sequence Diagram -- OAuth2 PKCE Flow

```mermaid
---
title: Sequence Diagram -- OAuth2 PKCE Flow
---
sequenceDiagram
    actor User
    participant App as Client App
    participant Auth as Auth Server
    participant API as Resource API

    User->>App: Click "Login"
    App->>App: Generate code_verifier + challenge
    App->>Auth: GET /authorize?code_challenge=...
    Auth->>User: Show login form
    User->>Auth: Submit credentials
    Auth->>App: Redirect with code
    App->>Auth: POST /token (code + verifier)
    Auth->>App: access_token + refresh_token
    App->>API: GET /data (Bearer token)
    API->>App: 200 OK + payload
    App->>User: Render dashboard
```

## 3. Class Diagram -- Domain Model

```mermaid
---
title: Class Diagram -- Domain Model
---
classDiagram
    class Account {
        +UUID id
        +String email
        +AccountStatus status
        +login() bool
        +suspend() void
    }
    class Transaction {
        +UUID id
        +Decimal amount
        +Currency currency
        +Instant createdAt
        +validate() bool
    }
    class Ledger {
        +UUID id
        +post(tx Transaction) void
        +balance() Decimal
    }
    class Currency {
        <<enumeration>>
        AUD
        EUR
        USD
        GBP
    }

    Account "1" --> "many" Transaction : initiates
    Transaction --> Currency : denominated in
    Ledger "1" --> "many" Transaction : records
```

## 4. Git Graph -- Release Branching

```mermaid
---
title: Git Graph -- Release Branching
---
gitGraph
   commit id: "init"
   branch develop
   checkout develop
   commit id: "feat: auth"
   commit id: "feat: payments"
   branch feature/dark-mode
   checkout feature/dark-mode
   commit id: "wip: tokens"
   commit id: "done: dark mode"
   checkout develop
   merge feature/dark-mode id: "merge dark-mode"
   branch release/1.0
   checkout release/1.0
   commit id: "bump version"
   commit id: "fix: edge case"
   checkout main
   merge release/1.0 id: "v1.0.0" tag: "v1.0.0"
   checkout develop
   merge release/1.0
```

## 5. Timeline -- Project Milestones

```mermaid
---
title: Timeline -- Project Milestone
---

timeline
    title Platform Rebuild -- 2025
    section Q1
        January  : Kickoff & discovery
        February : Architecture sign-off
        March    : Core APIs live
    section Q2
        April : Auth & identity migrated
        May   : Payment gateway integrated
        June  : Internal beta launch
    section Q3
        July      : Performance hardening
        August    : Security audit
        September : Public GA release
```
