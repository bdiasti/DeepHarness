---
name: test_strategy
description: Define comprehensive test strategies covering the test pyramid, scope, tools selection, environments, entry/exit criteria, and risk-based testing prioritization.
---

# Test Strategy Skill

You are an expert QA Engineer. When asked to define a test strategy, follow the structure and guidelines below.

## Test Strategy Template

```markdown
# Test Strategy: <Project or Feature Name>

**Author:** <name>
**Date:** <date>
**Version:** <x.y>

---

## 1. Objectives
## 2. Scope
## 3. Test Pyramid and Test Types
## 4. Tools and Infrastructure
## 5. Environments
## 6. Entry and Exit Criteria
## 7. Risk-Based Testing
## 8. Defect Management
## 9. Reporting
```

## Section-by-Section Guidance

### 1. Objectives

State what the test strategy aims to achieve. Be specific:

- "Ensure all P0 functional requirements (FR-001 through FR-012) are verified before release."
- "Achieve >= 80% code coverage on business logic modules."
- "Validate performance under expected peak load (500 concurrent users)."

Do NOT write vague objectives like "ensure quality" or "find bugs."

### 2. Scope

Define explicitly what is and is not covered:

**In Scope:**
- List the modules, services, APIs, and user flows that will be tested.
- Reference the PRD or requirements document by ID.

**Out of Scope:**
- Third-party components that are not modified (e.g., "Stripe payment SDK internals").
- Modules unchanged in this release.

### 3. Test Pyramid and Test Types

Always structure testing according to the test pyramid. The distribution below is a guideline — adjust based on project context.

```
        /  E2E  \          ~10% of tests
       /  (UI)   \         Slow, brittle, high confidence
      /___________\
     / Integration \        ~20% of tests
    /  (API, DB)    \       Moderate speed, moderate confidence
   /________________\
  /    Unit Tests    \      ~70% of tests
 /  (functions, logic) \    Fast, stable, high coverage
/______________________\
```

For each test type, specify:

| Test Type | What It Covers | Speed | Scope |
|---|---|---|---|
| **Unit** | Individual functions, methods, pure business logic | < 5 ms per test | Single function or class |
| **Integration** | API endpoints, database queries, service-to-service communication | < 2 s per test | Multiple components working together |
| **E2E (UI)** | Complete user flows through the browser or app | < 30 s per test | Full stack, from UI to database |
| **Performance** | Response time, throughput, resource consumption under load | Minutes | Target endpoints or flows |
| **Security** | Authentication, authorization, injection vulnerabilities, OWASP Top 10 | Minutes | Attack surface |
| **Accessibility** | WCAG compliance, screen reader compatibility, keyboard navigation | Seconds | UI components and pages |

Include or exclude test types based on the project. Not every project needs performance or security testing, but always justify the exclusion.

### 4. Tools and Infrastructure

Select tools based on the technology stack. Here are common recommendations:

| Purpose | Java / Spring | React / Node.js | Python / Django | Mobile |
|---|---|---|---|---|
| Unit tests | JUnit 5 + Mockito | Jest + React Testing Library | pytest + unittest.mock | XCTest / JUnit (Android) |
| Integration tests | Spring Boot Test + Testcontainers | Supertest + Testcontainers | pytest + Testcontainers | - |
| E2E tests | Playwright | Playwright | Playwright | Appium / Detox |
| API tests | REST Assured | Playwright API / Supertest | requests + pytest | REST Assured |
| Performance | Gatling / k6 | k6 | Locust / k6 | - |
| Security | OWASP ZAP | OWASP ZAP | Bandit + OWASP ZAP | MobSF |
| Accessibility | axe-core | axe-core + Lighthouse | axe-core | Accessibility Scanner |

Rules:
- Prefer tools that integrate with the existing CI/CD pipeline.
- Minimize the number of distinct tools. Each new tool has a maintenance cost.
- Every tool choice must include a one-line justification.

### 5. Environments

Define each environment and its purpose:

| Environment | Purpose | Data | Refresh Cadence |
|---|---|---|---|
| **Local** | Developer runs unit and integration tests | In-memory / mocked | On demand |
| **CI** | Automated pipeline runs all test suites | Ephemeral containers (Testcontainers) | Every commit / PR |
| **Staging** | QA runs manual exploratory tests, E2E suite, and performance tests | Anonymized copy of production data | Weekly |
| **Pre-production** | Final validation before release, smoke tests | Production-like data | Before each release |

Rules:
- Staging must NEVER use real customer data without anonymization.
- Document how to provision and tear down each environment.
- Specify who has access to each environment.

### 6. Entry and Exit Criteria

**Entry Criteria** (testing can start when):
- Code is merged to the test branch and builds successfully.
- All unit tests pass in CI (zero failures).
- Test environment is provisioned and accessible.
- Test data is seeded.
- Requirements are reviewed and acceptance criteria are clear.

**Exit Criteria** (testing is complete when):
- 100% of P0 test cases pass.
- >= 95% of P1 test cases pass.
- No open Severity 1 (blocker) or Severity 2 (critical) defects.
- Code coverage meets the agreed threshold (e.g., >= 80% line coverage on business logic).
- Performance benchmarks meet NFR targets.
- QA sign-off is recorded.

Present these as checklists so they can be verified before each release.

### 7. Risk-Based Testing

Prioritize testing effort based on risk. Use this matrix:

| Risk Factor | Weight | How to Assess |
|---|---|---|
| **Business impact** | High | Revenue-affecting flows, SLA-bound features |
| **Complexity** | High | Algorithmic logic, multi-system integrations |
| **Change frequency** | Medium | Modules with frequent code changes (check git history) |
| **Defect history** | Medium | Modules with past production incidents |
| **Newness** | Medium | Newly written code vs. stable, battle-tested code |
| **User exposure** | Low-Medium | Features used by all users vs. admin-only features |

Apply risk levels to determine test depth:

| Risk Level | Test Depth |
|---|---|
| **High** | Full coverage: unit + integration + E2E + edge cases + performance. Exploratory testing session. |
| **Medium** | Standard coverage: unit + integration + E2E for happy path. Boundary value tests. |
| **Low** | Minimal coverage: unit tests + smoke E2E. |

### Example Risk Assessment

| Module | Business Impact | Complexity | Change Frequency | Risk Level | Test Depth |
|---|---|---|---|---|---|
| Payment processing | High | High | Low | **High** | Full |
| User registration | High | Low | Low | **Medium** | Standard |
| Admin settings page | Low | Low | Low | **Low** | Minimal |
| Inventory reconciliation | High | High | High | **High** | Full |

### 8. Defect Management

Define severity and priority classifications:

| Severity | Description | Example | SLA |
|---|---|---|---|
| **S1 — Blocker** | System unusable, no workaround | Cannot log in, data loss | Fix before release, hotfix if in production |
| **S2 — Critical** | Major feature broken, workaround exists | Payment fails for one card type | Fix in current sprint |
| **S3 — Major** | Feature partially broken, user can proceed | Filter does not reset properly | Fix in next sprint |
| **S4 — Minor** | Cosmetic, minor UX issue | Button misaligned by 2px | Backlog |

Define the defect workflow: **New -> Triaged -> In Progress -> Fixed -> Verified -> Closed**.

### 9. Reporting

Specify what metrics to report and how often:

| Metric | Frequency | Audience |
|---|---|---|
| Test case pass/fail rate | Daily during test cycles | QA lead, engineering manager |
| Defect open/closed trend | Daily during test cycles | QA lead, product owner |
| Code coverage | Per CI build | Engineering team |
| Requirements coverage (% of FRs with test cases) | Weekly | Product owner, QA lead |
| Escaped defects (bugs found in production) | Monthly | Leadership, product owner |

## Output Checklist

Before delivering a test strategy, verify:

- [ ] Objectives are specific and measurable
- [ ] Scope clearly states what is in and out
- [ ] Test types follow the test pyramid with justified distribution
- [ ] Tools are selected for the actual tech stack with justification
- [ ] Environments are defined with data strategy and access rules
- [ ] Entry and exit criteria are concrete and verifiable checklists
- [ ] Risk-based prioritization is applied to modules or features
- [ ] Defect severity levels and SLAs are defined
- [ ] Reporting metrics and cadence are specified
