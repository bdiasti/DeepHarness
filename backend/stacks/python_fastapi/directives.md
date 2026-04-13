# Directives — Python FastAPI

IMMUTABLE rules.

## Architecture
1. FastAPI MUST follow layered architecture: routers → services → repositories.
2. Schemas (Pydantic) MUST be separate from Models (SQLAlchemy).
3. Database access MUST use async SQLAlchemy — no sync calls.
4. Dependency injection via `Depends()` for DB sessions, auth, etc.

## Code Quality
5. Every function MUST have type hints.
6. Pydantic schemas MUST have strict validation.
7. Functions MUST be async when doing I/O.
8. Use `Black` + `ruff` — no style debates.
9. NEVER use mutable default arguments.

## Testing
10. pytest with async fixtures.
11. Use `httpx.AsyncClient` for API tests.
12. Coverage MUST be >80% for services.

## Security
13. NEVER log request bodies (may contain secrets).
14. Use `python-jose` for JWT — never homemade tokens.
15. Password hashing MUST use `passlib` with bcrypt/argon2.
16. CORS configured explicitly — no wildcard in prod.
