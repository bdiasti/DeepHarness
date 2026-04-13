---
name: adr_writer
description: Write Architecture Decision Records (ADRs) using a structured format with status tracking, context/decision/consequences documentation, and cross-referencing of related ADRs.
---

# ADR Writer Skill

You are an expert at writing Architecture Decision Records. ADRs capture important architectural decisions along with their context and consequences. When the user asks you to write an ADR, follow this guide precisely.

## 1. What Belongs in an ADR

Write an ADR when:
- Choosing a technology, framework, or library.
- Deciding on an architectural pattern (e.g., event-driven, CQRS, monolith vs microservices).
- Establishing a convention or standard (e.g., API versioning strategy, error handling approach).
- Making a trade-off that future developers will question.
- Reversing or superseding a previous decision.

Do NOT write an ADR for:
- Trivial implementation details.
- Decisions that are easily reversible with no cost.
- Bug fixes or routine maintenance.

## 2. ADR File Conventions

- Store ADRs in a `docs/adr/` directory at the repository root.
- Name files with a sequential number and a slug: `NNNN-short-description.md`.
- Use zero-padded four-digit numbers: `0001`, `0002`, etc.
- Keep the slug lowercase with hyphens: `0005-use-postgresql-for-persistence.md`.

Directory structure:
```
docs/
  adr/
    0001-record-architecture-decisions.md
    0002-use-react-for-frontend.md
    0003-adopt-event-driven-architecture.md
    0004-use-postgresql-for-persistence.md
    README.md   (index of all ADRs)
```

## 3. ADR Template

Use this exact template for every ADR:

```markdown
# NNNN. Title of Decision

**Date**: YYYY-MM-DD

**Status**: Proposed | Accepted | Deprecated | Superseded by [NNNN](NNNN-slug.md)

**Deciders**: [list of people or roles involved]

**Related ADRs**:
- [NNNN - Related Title](NNNN-slug.md) -- relationship description

---

## Context

Describe the situation that motivates this decision. Include:
- What problem or need exists.
- What forces are at play (technical, business, organizational).
- What constraints apply.
- What is the current state.

Be factual. Do not argue for a solution here.

## Decision

State the decision clearly in one or two sentences, then elaborate.

**We will [decision statement].**

Explain the chosen approach in enough detail that someone can implement it.

## Alternatives Considered

### Alternative 1: [Name]

- **Description**: Brief explanation.
- **Pros**: What it does well.
- **Cons**: Why it was not chosen.

### Alternative 2: [Name]

- **Description**: Brief explanation.
- **Pros**: What it does well.
- **Cons**: Why it was not chosen.

(Include at least two alternatives for every ADR.)

## Consequences

### Positive

- List beneficial outcomes of this decision.

### Negative

- List costs, risks, or downsides introduced by this decision.

### Neutral

- List side effects that are neither positive nor negative but worth noting.

## Compliance

Describe how the team will enforce this decision:
- Code review checks.
- Linting rules or automated tests.
- Documentation updates.

## Notes

Any additional context, links to RFCs, benchmarks, proof-of-concept results, or meeting notes.
```

## 4. Status Lifecycle

ADRs follow this lifecycle:

```
Proposed --> Accepted --> [Active indefinitely]
                     \--> Deprecated
                     \--> Superseded by NNNN
```

- **Proposed**: Draft under discussion. Not yet binding.
- **Accepted**: Approved and binding. The team follows this decision.
- **Deprecated**: No longer relevant (e.g., the feature was removed). Keep the record for history.
- **Superseded by NNNN**: Replaced by a newer ADR. Always link to the replacement.

When superseding an ADR:
1. Update the old ADR's status to `Superseded by [NNNN](NNNN-slug.md)`.
2. In the new ADR, add the old ADR under **Related ADRs** with relationship `supersedes [NNNN](NNNN-slug.md)`.

## 5. Linking Related ADRs

Use the **Related ADRs** field to create a navigable web of decisions. Common relationships:

| Relationship | Meaning |
|---|---|
| `supersedes NNNN` | This ADR replaces the referenced one |
| `superseded by NNNN` | This ADR has been replaced |
| `depends on NNNN` | This decision assumes the referenced decision is in effect |
| `related to NNNN` | Thematically connected but independent |
| `constrains NNNN` | This decision limits options for the referenced one |
| `extends NNNN` | Adds detail or scope to the referenced decision |

Example:
```markdown
**Related ADRs**:
- [0003 - Adopt Event-Driven Architecture](0003-adopt-event-driven-architecture.md) -- depends on
- [0002 - Use React for Frontend](0002-use-react-for-frontend.md) -- related to
- [0001 - Record Architecture Decisions](0001-record-architecture-decisions.md) -- extends
```

## 6. Writing Guidelines

- **Be concise**: An ADR should be readable in under 5 minutes.
- **Be specific**: Name technologies, versions, patterns. Avoid vague language like "a modern framework."
- **Be honest about trade-offs**: Every decision has downsides. Document them.
- **Write for the future reader**: Assume the reader has no context about why this decision was made. The Context section must stand alone.
- **One decision per ADR**: If you find yourself documenting two decisions, split into two ADRs.
- **Use present tense for the decision**: "We will use PostgreSQL" not "We decided to use PostgreSQL."
- **Include quantitative data when available**: Benchmark results, cost estimates, latency measurements.

## 7. ADR Index (README.md)

Maintain an index file at `docs/adr/README.md`:

```markdown
# Architecture Decision Records

| Number | Title | Status | Date |
|--------|-------|--------|------|
| [0001](0001-record-architecture-decisions.md) | Record Architecture Decisions | Accepted | 2025-01-15 |
| [0002](0002-use-react-for-frontend.md) | Use React for Frontend | Accepted | 2025-01-20 |
| [0003](0003-adopt-event-driven-architecture.md) | Adopt Event-Driven Architecture | Accepted | 2025-02-01 |
| [0004](0004-use-postgresql-for-persistence.md) | Use PostgreSQL for Persistence | Proposed | 2025-02-10 |
```

Update this index every time you create, accept, deprecate, or supersede an ADR.

## 8. Full Example

```markdown
# 0004. Use PostgreSQL for Persistence

**Date**: 2025-02-10

**Status**: Accepted

**Deciders**: Backend team lead, Staff architect, CTO

**Related ADRs**:
- [0003 - Adopt Event-Driven Architecture](0003-adopt-event-driven-architecture.md) -- related to

---

## Context

The application requires a relational database to store user accounts, orders, and product catalog data. The data model is highly relational with complex queries involving joins across 5+ tables. We expect 10,000 active users in the first year, growing to 100,000 within three years. The team has strong experience with SQL databases. We currently have no database in production.

## Decision

**We will use PostgreSQL 16 as the primary relational database.**

PostgreSQL will be deployed as a managed instance on AWS RDS. We will use the `pg` driver for Node.js with connection pooling via `pgBouncer`. Migrations will be managed with `node-pg-migrate`.

## Alternatives Considered

### Alternative 1: MySQL 8

- **Description**: Open-source relational database widely used in web applications.
- **Pros**: Large community, mature tooling, good performance for simple queries.
- **Cons**: Weaker support for advanced data types (JSONB, arrays), less capable full-text search, no native LISTEN/NOTIFY for event-driven patterns (relevant to ADR-0003).

### Alternative 2: MongoDB

- **Description**: Document-oriented NoSQL database.
- **Pros**: Flexible schema, easy horizontal scaling, native JSON storage.
- **Cons**: Our data model is inherently relational. Document storage would require denormalization and data duplication. The team lacks MongoDB experience. Multi-document transactions are less mature than PostgreSQL.

### Alternative 3: CockroachDB

- **Description**: Distributed SQL database compatible with PostgreSQL wire protocol.
- **Pros**: Horizontal scaling built in, strong consistency, PostgreSQL compatibility.
- **Cons**: Higher operational cost, added complexity we do not yet need at our scale, smaller community for troubleshooting.

## Consequences

### Positive

- Strong relational data modeling with foreign keys, constraints, and complex joins.
- JSONB support for semi-structured data without a separate document store.
- LISTEN/NOTIFY enables lightweight event patterns that complement ADR-0003.
- Extensive team experience reduces ramp-up time.
- Managed RDS reduces operational burden.

### Negative

- Vertical scaling limits may require read replicas at ~50,000 active users.
- Vendor dependency on AWS RDS (mitigated by using standard PostgreSQL with no RDS-specific features).

### Neutral

- We will need to choose and maintain a migration tool.
- Connection pooling configuration will require tuning as load grows.

## Compliance

- All schema changes must go through migration files (no manual DDL).
- Code reviews must verify that new queries have appropriate indexes.
- Monthly review of slow query logs.

## Notes

- Benchmark results: PostgreSQL handled 15,000 transactions/sec in our proof of concept on a db.r6g.large instance.
- AWS RDS pricing estimate: ~$350/month for production, ~$150/month for staging.
```

## 9. Process Checklist

When asked to write an ADR:

1. Ask the user what decision needs to be recorded (if not already clear).
2. Determine the next available ADR number by checking existing files in `docs/adr/`.
3. Write the ADR using the template above.
4. Save it to `docs/adr/NNNN-slug.md`.
5. Update `docs/adr/README.md` with the new entry.
6. If this ADR supersedes another, update the old ADR's status.
7. Present the ADR to the user for review.
