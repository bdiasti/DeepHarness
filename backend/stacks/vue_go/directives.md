# Directives — Vue + Go

IMMUTABLE rules.

## Architecture
1. Go backend MUST follow hexagonal architecture: handlers → services → repositories.
2. Vue MUST use Composition API with `<script setup>`.
3. State MUST use Pinia stores — no global reactive objects.
4. Go MUST use interfaces for dependency injection.

## Code Quality
5. Go: errors MUST be handled explicitly — never ignore with `_`.
6. Vue components MUST be typed with TypeScript.
7. Go functions MUST be small — max 40 lines.
8. No circular imports in Go packages.

## Testing
9. Go: use standard `testing` package with table-driven tests.
10. Vue: use Vitest + @vue/test-utils.
11. Integration tests MUST use testcontainers for DB.

## Security
12. Go MUST use `context.Context` for timeouts/cancellation.
13. SQL MUST use parameterized queries (no string concat).
14. Vue: no `v-html` with user input (XSS risk).
15. CORS configured explicitly on Gin/Fiber.
