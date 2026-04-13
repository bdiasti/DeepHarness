# Constitution — Web App (JHipster)

These rules are IMMUTABLE and apply to EVERYTHING in this project. They cannot be overridden by personas, skills, or user requests.

## Technology Stack (FIXED)
1. Backend MUST be Java 21+ with Spring Boot 3.x.
2. Frontend MUST be React 19+ with TypeScript (or Angular/Vue if selected).
3. Database migrations MUST use Liquibase (no Flyway, no manual scripts).
4. Build tool MUST be Maven (pom.xml).
5. Framework generator MUST be JHipster 8.x (follow JHipster conventions strictly).

## Architecture (FIXED)
6. MUST follow JHipster's layered architecture: Resource (REST) → Service → Repository → Domain.
7. DTOs MUST be used at the API boundary (JHipster's `UserMapper` pattern).
8. Authentication MUST use Spring Security with JWT (JHipster default).
9. Caching MUST use Hibernate 2nd level cache (Ehcache or Caffeine).

## Code Quality
10. Every entity MUST have a Liquibase changeset.
11. Every REST endpoint MUST have integration tests.
12. Every service method MUST have unit tests.
13. Follow JHipster's naming conventions strictly (e.g., `FooResource`, `FooService`, `FooRepository`).

## Deployment
14. MUST include Dockerfile and docker-compose.yml.
15. MUST have profiles: `dev`, `prod`, `test`.
16. Secrets MUST come from environment variables or Spring Cloud Config.

## What's NOT allowed
- Do NOT use Flyway (use Liquibase — mandatory).
- Do NOT bypass DTOs (never expose entities directly).
- Do NOT write custom authentication (use JHipster/Spring Security).
- Do NOT mix frameworks (stick to the chosen one throughout).
