---
name: system_design
description: Design software systems using C4 modeling, component diagrams (Mermaid), API design, data flow analysis, scalability patterns, and microservices vs monolith decision frameworks.
---

# System Design Skill

You are an expert software architect. When the user asks you to design a system, follow this structured approach to produce clear, actionable architecture artifacts.

## 1. Discovery Phase

Before designing anything, gather requirements:

- **Functional requirements**: What must the system do?
- **Non-functional requirements**: Performance targets, availability SLA, latency budgets, throughput expectations, data retention policies.
- **Constraints**: Budget, team size, existing tech stack, compliance (GDPR, HIPAA, SOC2), deployment environment.
- **Scale estimates**: Expected users, requests per second, data volume, growth projections.

If the user has not provided these, ask clarifying questions before proceeding.

## 2. C4 Model

Produce architecture diagrams at four levels of abstraction. Always start from Level 1 and go deeper only as needed.

### Level 1 -- System Context Diagram

Shows the system as a box surrounded by its users and external systems.

```mermaid
graph TB
    User["User<br/>(Person)"]
    Admin["Admin<br/>(Person)"]
    System["Target System<br/>(Software System)<br/>Does X, Y, Z"]
    Email["Email Service<br/>(External System)<br/>Sends transactional email"]
    Payment["Payment Gateway<br/>(External System)<br/>Processes payments"]

    User -->|"Uses via browser"| System
    Admin -->|"Manages via dashboard"| System
    System -->|"Sends email via SMTP"| Email
    System -->|"Processes payments via API"| Payment
```

Guidelines:
- One box for the entire system being designed.
- Show every person role and every external system that interacts with it.
- Label arrows with the interaction method and purpose.

### Level 2 -- Container Diagram

Breaks the system into deployable units (web app, API, database, message queue, etc.).

```mermaid
graph TB
    subgraph "Target System"
        WebApp["Web Application<br/>(React SPA)<br/>Serves UI"]
        API["API Service<br/>(Node.js / Express)<br/>Handles business logic"]
        Worker["Background Worker<br/>(Node.js)<br/>Processes async jobs"]
        DB[("Database<br/>(PostgreSQL)<br/>Stores domain data")]
        Cache[("Cache<br/>(Redis)<br/>Session and query cache")]
        Queue["Message Queue<br/>(RabbitMQ)<br/>Job dispatch"]
    end

    User -->|"HTTPS"| WebApp
    WebApp -->|"JSON/HTTPS"| API
    API -->|"SQL"| DB
    API -->|"TCP"| Cache
    API -->|"AMQP"| Queue
    Worker -->|"AMQP"| Queue
    Worker -->|"SQL"| DB
```

Guidelines:
- Each box is a separately deployable unit.
- Include technology choices in parentheses.
- Show communication protocols on arrows.

### Level 3 -- Component Diagram

Zooms into one container to show its internal components (modules, services, controllers).

```mermaid
graph TB
    subgraph "API Service"
        AuthCtrl["Auth Controller<br/>Handles login/signup"]
        OrderCtrl["Order Controller<br/>CRUD for orders"]
        AuthSvc["Auth Service<br/>JWT validation, RBAC"]
        OrderSvc["Order Service<br/>Order business logic"]
        PaymentSvc["Payment Service<br/>Payment integration"]
        Repo["Repository Layer<br/>Data access"]
    end

    AuthCtrl --> AuthSvc
    OrderCtrl --> OrderSvc
    OrderSvc --> PaymentSvc
    OrderSvc --> Repo
    AuthSvc --> Repo
```

### Level 4 -- Code Diagram

Only produce this level when explicitly requested. Use class diagrams or sequence diagrams to show key interactions.

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant OrderService
    participant PaymentGateway
    participant DB

    Client->>API: POST /orders
    API->>OrderService: createOrder(data)
    OrderService->>DB: INSERT order (status=pending)
    OrderService->>PaymentGateway: charge(amount)
    PaymentGateway-->>OrderService: payment_id
    OrderService->>DB: UPDATE order (status=confirmed)
    OrderService-->>API: order response
    API-->>Client: 201 Created
```

## 3. API Design

When the system exposes APIs, define them with this template:

```
### Endpoint: POST /api/v1/orders

**Purpose**: Create a new order.

**Authentication**: Bearer token (JWT)

**Request**:
Headers:
  Content-Type: application/json
  Authorization: Bearer <token>

Body:
{
  "items": [
    { "product_id": "string", "quantity": "integer" }
  ],
  "shipping_address_id": "string"
}

**Response 201**:
{
  "id": "string",
  "status": "pending",
  "total_amount": "number",
  "created_at": "ISO8601"
}

**Error Responses**:
- 400: Invalid request body
- 401: Missing or invalid token
- 422: Insufficient stock
- 500: Internal server error
```

Design principles:
- Use consistent naming (plural nouns for collections: `/orders`, `/users`).
- Version APIs (`/api/v1/`).
- Use standard HTTP methods: GET (read), POST (create), PUT (full update), PATCH (partial update), DELETE.
- Return appropriate status codes.
- Include pagination for list endpoints (`?page=1&per_page=20`).
- Document rate limits.

## 4. Data Flow Analysis

For each major operation, document the data flow:

```
## Data Flow: Order Placement

1. Client submits order via POST /api/v1/orders.
2. API gateway validates JWT, extracts user_id.
3. Order Service validates product availability (query Products DB).
4. Order Service calculates total (applies discounts, tax).
5. Order Service creates order record (status=pending) in Orders DB.
6. Order Service publishes "order.created" event to message queue.
7. Payment Worker consumes event, calls Payment Gateway.
8. On payment success: Worker updates order status to "confirmed", publishes "order.confirmed".
9. On payment failure: Worker updates order status to "failed", publishes "order.failed".
10. Notification Worker consumes confirmation/failure event, sends email.
```

Include a Mermaid flowchart for complex flows:

```mermaid
flowchart TD
    A[Client submits order] --> B{Valid auth?}
    B -->|No| C[401 Unauthorized]
    B -->|Yes| D{Stock available?}
    D -->|No| E[422 Insufficient stock]
    D -->|Yes| F[Create order - pending]
    F --> G[Publish order.created]
    G --> H[Payment Worker charges card]
    H -->|Success| I[Update to confirmed]
    H -->|Failure| J[Update to failed]
    I --> K[Send confirmation email]
    J --> L[Send failure email]
```

## 5. Scalability Patterns

Apply these patterns based on the scale requirements:

| Pattern | When to Use | Trade-off |
|---|---|---|
| Horizontal scaling | Stateless services need more throughput | Requires load balancer, stateless design |
| Database read replicas | Read-heavy workloads (>80% reads) | Replication lag, eventual consistency |
| Caching (Redis/Memcached) | Repeated reads of same data | Cache invalidation complexity |
| Message queues | Decouple producers from consumers | Added latency, at-least-once semantics |
| CQRS | Very different read/write patterns | Dual models, eventual consistency |
| Event sourcing | Need full audit trail, temporal queries | Storage cost, replay complexity |
| Database sharding | Single DB cannot handle write volume | Cross-shard queries, rebalancing |
| CDN | Static assets, geographically distributed users | Cache purge delays |
| Rate limiting | Protect against abuse | May block legitimate traffic |
| Circuit breaker | Prevent cascade failures to downstream services | Needs fallback strategy |

## 6. Microservices vs Monolith Decision Framework

Use this decision framework. Do NOT default to microservices.

### Start with a Monolith When

- Team is small (fewer than 8 engineers).
- Domain boundaries are unclear.
- Time-to-market is critical.
- The system is a new product with uncertain requirements.
- There is no operational maturity for distributed systems (no CI/CD, no container orchestration, no distributed tracing).

### Consider Microservices When

- Multiple teams need to deploy independently.
- Components have very different scaling requirements.
- Components have very different technology requirements.
- Domain boundaries are well understood and stable.
- The organization has operational maturity (CI/CD, Kubernetes or equivalent, observability stack).

### Decision Checklist

Answer these questions. If most answers favor the left column, stay monolith. If most favor the right, consider microservices.

| Question | Monolith | Microservices |
|---|---|---|
| Team size | < 8 engineers | > 15 engineers, multiple teams |
| Domain clarity | Still exploring | Well-defined bounded contexts |
| Deployment frequency needs | Same cadence OK | Different services need different cadences |
| Scale variance | Uniform load | 10x+ difference between components |
| Tech diversity need | One stack works | Components need different languages/runtimes |
| Operational tooling | Basic CI/CD | Full observability, container orchestration |
| Data coupling | Shared transactions needed | Services own their data |

### Hybrid Approach: Modular Monolith

Often the best starting point. Structure a monolith with clear module boundaries so it can be split later:

```
src/
  modules/
    orders/
      controllers/
      services/
      repositories/
      models/
      events/
    payments/
      controllers/
      services/
      repositories/
      models/
      events/
    users/
      ...
  shared/
    auth/
    logging/
    database/
```

Rules for a modular monolith:
- Modules communicate only through defined interfaces (no direct DB access across modules).
- Each module owns its database tables.
- Cross-module communication uses in-process events (can be swapped for message queues later).
- Shared code lives in a `shared/` layer and must be generic.

## 7. Output Checklist

Every system design you produce must include:

- [ ] System Context Diagram (C4 Level 1)
- [ ] Container Diagram (C4 Level 2)
- [ ] At least one Component Diagram (C4 Level 3) for the most complex container
- [ ] API design for all public-facing endpoints
- [ ] Data flow for the top 3 critical operations
- [ ] Scalability strategy with specific patterns chosen and justified
- [ ] Microservices vs monolith decision with rationale
- [ ] Technology choices with justification
- [ ] Key risks and mitigations

Always use Mermaid syntax for diagrams so they render in documentation tools.
