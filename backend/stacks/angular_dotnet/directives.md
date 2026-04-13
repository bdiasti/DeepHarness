# Directives — Angular + .NET

IMMUTABLE rules.

## Architecture
1. Backend MUST follow Clean Architecture: Controllers → Services → Repositories → Entities.
2. Frontend MUST use Angular standalone components or NgModules consistently.
3. Data transfer MUST use DTOs — NEVER expose EF entities directly.
4. API endpoints MUST be RESTful with proper HTTP methods and status codes.

## Code Quality
5. Use dependency injection everywhere — NEVER `new` services directly.
6. All async operations MUST use `async/await`, never `.Result` or `.Wait()`.
7. Angular components MUST use `OnPush` change detection when possible.
8. TypeScript MUST use strict mode — no `any` type.
9. C# MUST enable nullable reference types.

## Testing
10. xUnit for .NET tests, Karma/Jasmine for Angular.
11. Test coverage MUST be >80% for Services.
12. Angular components MUST have at least smoke tests.

## Security
13. NEVER hardcode connection strings — use configuration + secrets.
14. ASP.NET must enable CORS explicitly (no AllowAnyOrigin in prod).
15. Angular MUST use HttpInterceptors for auth tokens.
16. Input validation: FluentValidation on backend, Angular Validators on frontend.
