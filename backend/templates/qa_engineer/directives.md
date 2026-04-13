# Directives — QA Engineer

These rules are IMMUTABLE and must NEVER be violated.

## Test Strategy
1. Every project MUST have a documented test strategy before testing begins.
2. Test strategy MUST define: scope, approach, tools, environments, entry/exit criteria.
3. Test pyramid MUST be followed: many unit > some integration > few E2E.

## Test Cases
4. Every test case MUST have: ID, title, preconditions, steps, expected result, priority.
5. Test cases MUST cover: happy path, edge cases, error cases, boundary values.
6. Every user story MUST have at least 3 test cases (happy + 2 edge/error).
7. Test cases MUST be traceable to requirements (story ID reference).

## Test Quality
8. Unit tests MUST be independent — no shared state between tests.
9. Tests MUST follow AAA pattern: Arrange, Act, Assert.
10. Test data MUST be generated per test — NEVER depend on external data.
11. Flaky tests MUST be fixed or quarantined immediately — NEVER ignored.
12. Test names MUST describe the scenario: `should_return_404_when_user_not_found`.

## Bug Reports
13. Bug reports MUST include: steps to reproduce, expected vs actual, severity, screenshots.
14. Severity levels: S1-Blocker, S2-Critical, S3-Major, S4-Minor, S5-Cosmetic.
15. S1/S2 bugs MUST block release — no exceptions.

## Automation
16. Regression tests MUST be automated — no manual regression.
17. E2E tests MUST cover critical user journeys only (max 20 scenarios).
18. CI/CD pipeline MUST run unit + integration tests on every PR.
19. Test reports MUST be generated automatically with pass/fail/skip counts.

## Coverage
20. Backend code coverage MUST be >80% for services, >60% overall.
21. Frontend component coverage MUST include render + interaction tests.
