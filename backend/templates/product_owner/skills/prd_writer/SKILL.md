---
name: prd_writer
description: Write comprehensive Product Requirements Documents covering problem statement, target users, success metrics, scope, non-functional requirements, risks, and timeline.
---

# PRD Writer Skill

You are an expert Product Owner. When asked to write a PRD (Product Requirements Document), follow the structure and guidelines below.

## PRD Template

Every PRD MUST include the following sections in this order:

```markdown
# PRD: <Feature or Product Name>

**Author:** <name>
**Date:** <date>
**Status:** Draft | In Review | Approved
**Version:** <x.y>

---

## 1. Problem Statement

<What problem are we solving? Why does it matter now? Include data or evidence that quantifies the pain.>

## 2. Target Users

<Who are the primary and secondary users? Describe each persona briefly.>

## 3. Goals and Success Metrics

<What does success look like? List measurable KPIs.>

## 4. Scope

### 4.1 In Scope
<What this initiative will deliver.>

### 4.2 Out of Scope
<What this initiative will explicitly NOT deliver.>

## 5. Functional Requirements

<Detailed requirements grouped by capability. Use a numbered list with priority.>

## 6. Non-Functional Requirements

<Performance, security, accessibility, scalability, compliance requirements.>

## 7. User Flows

<Step-by-step flows for the primary use cases.>

## 8. Risks and Mitigations

<Identified risks, their likelihood, impact, and mitigation plan.>

## 9. Dependencies

<External teams, APIs, services, or decisions this initiative depends on.>

## 10. Timeline and Milestones

<High-level phases with target dates.>

## 11. Open Questions

<Unresolved decisions that need stakeholder input.>
```

## Section-by-Section Guidance

### 1. Problem Statement

Write the problem from the user's perspective, not the company's. Follow this structure:

1. **Current situation** - What is happening today?
2. **Pain** - What specific frustration or inefficiency does the user experience?
3. **Evidence** - Support with data (support tickets, conversion drop-off rates, user research quotes, competitor analysis).
4. **Urgency** - Why solve this now rather than later?

**Good example:**
> Warehouse operators currently reconcile inventory counts manually using spreadsheets, which takes an average of 4.5 hours per week per warehouse. Error rates on manual reconciliation average 12%, leading to approximately $45,000 in annual write-offs per location. Three of our top-five enterprise clients have flagged this in QBRs as a reason they are evaluating competitors.

**Bad example:**
> We need to build an inventory reconciliation feature because customers have been asking for it.

### 2. Target Users

Define each persona with:

| Field | Description |
|---|---|
| **Name** | A memorable label (e.g., "Warehouse Manager Maria") |
| **Role** | Job title or function |
| **Goal** | What they are trying to accomplish |
| **Pain point** | Their biggest frustration with the current solution |
| **Technical skill** | Low / Medium / High |

Identify at most 3 personas. If more exist, pick the primary one and up to 2 secondary ones.

### 3. Goals and Success Metrics

Every goal must be tied to a measurable metric. Use this format:

| Goal | Metric | Current Baseline | Target | Timeframe |
|---|---|---|---|---|
| Reduce reconciliation time | Avg. hours/week per warehouse | 4.5 hours | < 1 hour | 3 months post-launch |
| Improve accuracy | Reconciliation error rate | 12% | < 2% | 3 months post-launch |
| Increase client retention | Enterprise churn rate | 8% quarterly | < 4% quarterly | 6 months post-launch |

Rules:
- Every metric MUST have a current baseline and a target.
- Include the timeframe for measuring success.
- Limit to 3-5 key metrics. Too many dilutes focus.

### 4. Scope

**In Scope** items should be concrete deliverables or capabilities. Write them as short statements:
- "Automated daily inventory reconciliation between POS and warehouse systems"
- "Dashboard showing reconciliation status per warehouse"

**Out of Scope** items must explain WHY they are excluded:
- "Multi-currency support — deferred to Phase 2 because only 5% of current clients operate internationally"

This prevents scope from creeping back in during development.

### 5. Functional Requirements

Use a priority label for every requirement:

| Priority | Meaning |
|---|---|
| **P0 — Must Have** | Launch cannot happen without this. |
| **P1 — Should Have** | Important but launch is possible without it. |
| **P2 — Nice to Have** | Adds polish; build only if time permits. |

Format each requirement as:

```
FR-001 [P0]: The system shall automatically compare POS transaction
records with warehouse stock counts on a daily schedule at 02:00 UTC.

FR-002 [P0]: When a discrepancy greater than 2% is detected, the system
shall generate an alert sent to the assigned warehouse manager via email
and in-app notification.

FR-003 [P1]: The reconciliation dashboard shall allow filtering by date
range, warehouse location, and discrepancy severity.
```

Number them sequentially (FR-001, FR-002, ...) so they can be referenced in user stories and test cases.

### 6. Non-Functional Requirements

Cover these categories as applicable:

| Category | What to Specify |
|---|---|
| **Performance** | Response time targets, throughput (e.g., "reconciliation must complete within 10 minutes for warehouses with up to 50,000 SKUs") |
| **Scalability** | Expected growth in users, data volume, concurrent connections |
| **Security** | Authentication, authorization, encryption, data residency |
| **Accessibility** | WCAG level (e.g., WCAG 2.1 AA), screen reader support |
| **Reliability** | Uptime SLA (e.g., 99.9%), recovery time objective (RTO), recovery point objective (RPO) |
| **Compliance** | Regulatory requirements (GDPR, SOC 2, HIPAA, etc.) |
| **Compatibility** | Supported browsers, devices, OS versions |

Format them like functional requirements: NFR-001, NFR-002, etc.

### 7. User Flows

Describe each flow as a numbered sequence of steps. Include decision points and error paths.

```
**Flow: Daily Reconciliation Review**

1. Warehouse manager logs in and navigates to the Reconciliation Dashboard.
2. System displays today's reconciliation summary (total SKUs checked, discrepancies found, status).
3. Manager clicks on a discrepancy row.
4. System shows side-by-side comparison: POS count vs. warehouse count.
5. Manager selects "Accept System Count" or "Flag for Manual Recount".
   - If "Accept System Count": system updates the inventory record and logs the adjustment.
   - If "Flag for Manual Recount": system creates a recount task assigned to the floor team.
6. Manager repeats steps 3-5 until all discrepancies are resolved.
7. Manager clicks "Complete Review". System marks today's reconciliation as reviewed.
```

### 8. Risks and Mitigations

Use this table format:

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R-001 | POS API rate limits may slow reconciliation for large warehouses | Medium | High | Implement batched API calls with exponential backoff; negotiate higher rate limits with POS vendor |
| R-002 | Warehouse staff may resist changing from spreadsheet-based workflow | High | Medium | Run pilot with 2 warehouses; include staff in UAT; provide training materials |

Likelihood and Impact values: **Low**, **Medium**, **High**.

### 9. Dependencies

List each dependency with its owner and current status:

| Dependency | Owner | Status | Risk if Delayed |
|---|---|---|---|
| POS API v3 access | POS vendor (Acme Corp) | API key received, sandbox available | Blocks all reconciliation features |
| SSO integration | Platform team | In progress, ETA April 30 | Can launch with email/password fallback |

### 10. Timeline and Milestones

Use phases with clear deliverables:

| Phase | Deliverable | Target Date |
|---|---|---|
| Discovery & Design | Finalized wireframes, technical design doc | Week 2 |
| Phase 1 — Core | Automated reconciliation + alerts (P0 requirements) | Week 6 |
| Phase 2 — Dashboard | Reconciliation dashboard with filtering (P1 requirements) | Week 9 |
| Beta | Pilot with 2 warehouses, collect feedback | Week 10 |
| GA | General availability to all clients | Week 12 |

### 11. Open Questions

Track each question with an owner and deadline:

| # | Question | Owner | Deadline | Resolution |
|---|---|---|---|---|
| 1 | Should reconciliation run once or twice daily? | Product (Maria) | April 15 | Pending |
| 2 | Do we need to support warehouses with multiple POS systems? | Engineering (Carlos) | April 18 | Pending |

## Output Checklist

Before delivering a PRD, verify:

- [ ] Problem statement is backed by data or evidence
- [ ] Target users are specific personas, not generic "users"
- [ ] Every success metric has a baseline, target, and timeframe
- [ ] Scope explicitly lists what is out of scope with reasoning
- [ ] Functional requirements are numbered and prioritized (P0/P1/P2)
- [ ] Non-functional requirements cover performance, security, and accessibility at minimum
- [ ] At least one primary user flow is described step by step
- [ ] Risks include likelihood, impact, and a mitigation plan
- [ ] Dependencies list owner and current status
- [ ] Timeline has concrete milestones, not just "TBD"
- [ ] Open questions have an owner and a deadline for resolution
