# E-commerce Checkout Flow

```mermaid
---
title: E-commerce Checkout Flow
---

graph TB
    A[Add to Cart] --> B{User Logged In?}
    B -->|No| C[Login/Register]
    B -->|Yes| D[Review Cart]
    C --> D
    D --> E{Items Available?}
    E -->|No| F[Update Cart]
    F --> D
    E -->|Yes| G[Select Shipping]
    G --> H[Enter Payment]
    H --> I{Payment Valid?}
    I -->|No| J[Payment Error]
    J --> H
    I -->|Yes| K[Process Order]
    K --> L{Inventory Check}
    L -->|Failed| M[Backorder]
    L -->|Success| N[Confirm Order]
    M --> O[Notify Customer]
    N --> P[Send Confirmation]
    O --> Q[End]
    P --> Q
    
    style A fill:#e1f5fe
    style Q fill:#e8f5e8
    style J fill:#ffebee
    style M fill:#fff3e0

```
# Microservices Architecture

```mermaid
---
title: Microservices Architecture
---

graph TB
    subgraph "Client Layer"
        A[Web App] --> B[Mobile App]
    end
    
    subgraph "API Gateway"
        C[Load Balancer] --> D[Auth Service]
        C --> E[Rate Limiter]
    end
    
    subgraph "Microservices"
        F[User Service] --> G[(User DB)]
        H[Order Service] --> I[(Order DB)]
        J[Payment Service] --> K[(Payment DB)]
        L[Notification Service] --> M[Message Queue]
    end
    
    subgraph "External Services"
        N[Payment Gateway]
        O[Email Service]
        P[SMS Service]
    end
    
    A --> C
    B --> C
    D --> F
    D --> H
    D --> J
    H --> L
    J --> L
    J --> N
    L --> O
    L --> P
    
    classDef client fill:#e3f2fd
    classDef gateway fill:#f3e5f5
    classDef service fill:#e8f5e8
    classDef external fill:#fff3e0
    
    class A,B client
    class C,D,E gateway
    class F,H,J,L service
    class N,O,P external

```
# CI/CD Pipeline

```mermaid
---
title: CI/CD Pipeline
---

graph LR
    A[Developer Push] --> B[Git Repository]
    B --> C{Tests Pass?}
    C -->|No| D[Notify Developer]
    D --> A
    C -->|Yes| E[Build Application]
    E --> F[Security Scan]
    F --> G{Vulnerabilities?}
    G -->|Yes| H[Block Deployment]
    H --> D
    G -->|No| I[Deploy to Staging]
    I --> J[Integration Tests]
    J --> K{Tests Pass?}
    K -->|No| D
    K -->|Yes| L[Deploy to Production]
    L --> M[Monitor & Alert]
    
    style A fill:#e8f5e8
    style L fill:#e1f5fe
    style D fill:#ffebee
    style H fill:#ffebee

```
# Sprint Gantt Chart

```mermaid
---
title: Sprint Gantt Chart
---

gantt
    title Sprint 23 - Q1 2024
    dateFormat YYYY-MM-DD
    section Planning
    Sprint Planning    :done, planning, 2024-01-15, 2024-01-15
    Backlog Refinement :done, refinement, 2024-01-16, 2024-01-16
    section Development
    Feature A Development :active, featureA, 2024-01-17, 2024-01-22
    Feature B Development :featureB, 2024-01-19, 2024-01-24
    Bug Fixes         :bugs, 2024-01-23, 2024-01-25
    section Testing
    QA Testing        :testing, 2024-01-24, 2024-01-26
    UAT               :uat, 2024-01-26, 2024-01-28
    section Ceremonies
    Daily Standups    :standups, 2024-01-17, 2024-01-28
    Sprint Review     :review, 2024-01-29, 2024-01-29
    Retrospective     :retro, 2024-01-29, 2024-01-29

```
# User Onboarding Journey

```mermaid
---
title: User Onboarding Journey
---

journey
    title New User Onboarding Experience
    section Discovery
      Visit Landing Page: 5: User
      Read About Features: 4: User
      Watch Demo Video: 4: User
      Check Pricing: 3: User
    section Registration
      Click Sign Up: 4: User
      Fill Registration Form: 2: User
      Verify Email: 2: User
      Set Password: 3: User
    section First Login
      Login Successfully: 4: User
      Complete Profile: 3: User
      Take Product Tour: 5: User
      Connect Integrations: 2: User
    section First Use
      Create First Project: 4: User
      Invite Team Members: 3: User
      Complete First Task: 5: User
      Explore Advanced Features: 4: User

```
# E-commerce Entity Relationship Diagram

```mermaid
---
title: E-commerce Entity Relationship Diagram
---

erDiagram
    CUSTOMER ||--o{ ORDER : places
    CUSTOMER {
        int customer_id PK
        string email UK
        string first_name
        string last_name
        string phone
        datetime created_at
        datetime updated_at
    }
    
    ORDER ||--|{ ORDER_ITEM : contains
    ORDER {
        int order_id PK
        int customer_id FK
        datetime order_date
        decimal total_amount
        string status
        string shipping_address
        string billing_address
    }
    
    PRODUCT ||--o{ ORDER_ITEM : "ordered in"
    PRODUCT {
        int product_id PK
        string name
        string description
        decimal price
        int stock_quantity
        int category_id FK
        datetime created_at
    }
    
    CATEGORY ||--o{ PRODUCT : contains
    CATEGORY {
        int category_id PK
        string name
        string description
        int parent_id FK
    }
    
    ORDER_ITEM {
        int order_id FK
        int product_id FK
        int quantity
        decimal unit_price
        decimal total_price
    }
    
    CUSTOMER ||--o{ REVIEW : writes
    PRODUCT ||--o{ REVIEW : receives
    REVIEW {
        int review_id PK
        int customer_id FK
        int product_id FK
        int rating
        string comment
        datetime created_at
    }

```
# Order Status State Machine

```mermaid
---
title: Order Status State Machine
---

stateDiagram-v2
    [*] --> Draft
    Draft --> Pending : submit_order
    Pending --> Confirmed : payment_received
    Pending --> Cancelled : timeout
    Pending --> Cancelled : user_cancel
    Confirmed --> Processing : start_fulfillment
    Processing --> Shipped : items_shipped
    Processing --> Cancelled : out_of_stock
    Shipped --> Delivered : delivery_confirmed
    Shipped --> Returned : return_requested
    Delivered --> Completed : [*]
    Returned --> Refunded : process_return
    Cancelled --> [*]
    Refunded --> [*]
    
    Pending : Payment pending
    Confirmed : Payment confirmed
    Processing : Preparing items
    Shipped : In transit
    Delivered : Successfully delivered
    Cancelled : Order cancelled
    Returned : Return in progress
    Refunded : Refund processed
    Completed : Order complete

```
# Microservices Order Placement Sequence

```mermaid
---
title: Microservices Order Placement Sequence
---

sequenceDiagram
    participant U as User
    participant G as API Gateway
    participant A as Auth Service
    participant O as Order Service
    participant P as Payment Service
    participant I as Inventory Service
    participant N as Notification Service
    participant Q as Message Queue
    
    U->>G: Place Order Request
    G->>A: Validate Token
    A-->>G: Token Valid
    G->>O: Create Order
    
    par Parallel Processing
        O->>I: Check Inventory
        I-->>O: Items Available
    and
        O->>P: Process Payment
        P-->>O: Payment Successful
    end
    
    O->>Q: Publish Order Created Event
    Q->>N: Order Notification
    N->>U: Send Confirmation Email
    
    opt If Payment Fails
        P-->>O: Payment Failed
        O->>Q: Publish Order Failed Event
        Q->>N: Failure Notification
        N->>U: Send Failure Email
    end
    
    O-->>G: Order Created
    G-->>U: Order Confirmation

```
