# Directives — Fullstack React + Java

These rules are IMMUTABLE and must NEVER be violated.

## Architecture
1. Backend MUST follow layered architecture: Controller → Service → Repository → Entity.
2. Frontend MUST use functional React components with TypeScript strict mode.
3. API communication MUST use DTOs — NEVER expose entities directly.
4. All endpoints MUST be RESTful with proper HTTP methods and status codes.
5. CORS MUST be configured explicitly — NEVER use allow-all in production code.

## Code Quality
6. Every public method MUST have a clear purpose — no god methods.
7. Business logic MUST live in Service layer — NEVER in Controllers or Repositories.
8. React components MUST be small (<150 lines) — extract when larger.
9. All API calls MUST have error handling with user-friendly messages.
10. TypeScript types MUST be explicit — NEVER use `any`.

## Security
11. NEVER hardcode secrets, passwords, or API keys.
12. All user input MUST be validated on both frontend and backend.
13. SQL queries MUST use parameterized queries or JPA — NEVER string concatenation.
14. Authentication tokens MUST be stored securely (httpOnly cookies preferred).

## Project Standards
15. Every feature MUST have a corresponding SDD task before implementation.
16. README MUST document: setup, architecture, API endpoints, environment variables.
17. Docker Compose MUST define all services needed to run locally.
18. Every API endpoint MUST be documented with request/response examples.

## Testing
19. Backend services MUST have unit tests with >80% coverage.
20. Frontend components MUST have at least smoke tests.
21. API endpoints MUST have integration tests.
