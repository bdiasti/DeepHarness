# Directives — Developer

These rules are IMMUTABLE and must NEVER be violated.

## Code Standards
1. Code MUST follow the project's established patterns — consistency over preference.
2. Functions MUST do one thing — max 30 lines. Extract when larger.
3. Classes MUST follow Single Responsibility Principle — one reason to change.
4. Variable names MUST be descriptive — no single letters except loop counters.
5. NEVER leave TODO comments in committed code — create a task instead.

## Implementation Process
6. ALWAYS read the SDD/task description before writing code.
7. ALWAYS check existing code for similar patterns before creating new ones.
8. Write tests BEFORE or ALONGSIDE implementation — never after as afterthought.
9. Every PR MUST be small and focused — one feature or fix per PR.
10. Commit messages MUST follow: `type(scope): description` (feat, fix, refactor, test, docs).

## Code Quality
11. NEVER copy-paste code — extract shared logic into functions/utilities.
12. Error handling MUST be explicit — catch specific exceptions, not generic.
13. All external calls MUST have timeouts and retry logic.
14. Logging MUST be structured with appropriate levels (DEBUG, INFO, WARN, ERROR).
15. Comments explain WHY, not WHAT — the code should be self-documenting.

## Security
16. NEVER log sensitive data (passwords, tokens, PII).
17. NEVER trust user input — validate and sanitize everything.
18. Dependencies MUST be from trusted sources with known versions.

## Testing
19. Every public function MUST have at least one unit test.
20. Tests MUST be deterministic — no random, no time-dependent.
21. Test edge cases: null, empty, boundary values, concurrent access.
22. Mock external dependencies — tests MUST run offline.

## Git Workflow
23. NEVER push directly to main — always use feature branches.
24. Branch naming: `feat/description`, `fix/description`, `refactor/description`.
25. Resolve ALL linting errors before committing.
