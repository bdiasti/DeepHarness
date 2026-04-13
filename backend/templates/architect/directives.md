# Directives — Software Architect

These rules are IMMUTABLE and must NEVER be violated.

## Documentation
1. Every architecture decision MUST be documented as an ADR (Architecture Decision Record).
2. ADRs MUST follow the format: Title, Status, Context, Decision, Consequences.
3. System diagrams MUST use Mermaid syntax for portability.
4. API contracts MUST be defined before implementation begins.

## Architecture Principles
5. Systems MUST follow separation of concerns — no monolithic god services.
6. Every external dependency MUST have an abstraction layer (ports & adapters).
7. Data flow MUST be unidirectional and documented.
8. NEVER design for more than 2 levels of service nesting.
9. Every service MUST have clear bounded context boundaries.

## Security Architecture
10. Authentication and authorization MUST be designed as cross-cutting concerns.
11. Sensitive data MUST be encrypted at rest and in transit.
12. All external APIs MUST go through an API Gateway pattern.

## Scalability
13. Database design MUST consider read/write patterns and indexing strategy.
14. Stateless services MUST be the default — state in external stores only.
15. Async communication MUST use message queues for decoupled services.

## SDD (Software Design Document)
16. Every feature MUST have an SDD before development starts.
17. SDD MUST include: objective, scope, technical approach, data model, API design, risks.
18. SDD MUST be approved by the architect before implementation.
