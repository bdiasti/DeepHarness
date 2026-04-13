---
name: postgresql
description: PostgreSQL — indexes, query optimization, JSONB, partitioning, migrations
---

# PostgreSQL

Robust, ACID, feature-rich relational database. Prefer it as the default OLTP choice.

## Indexes

```sql
-- B-tree (default): equality, range, ORDER BY
CREATE INDEX idx_orders_user_created ON orders(user_id, created_at DESC);

-- Partial: index only rows you query
CREATE INDEX idx_orders_open ON orders(user_id) WHERE status = 'open';

-- Expression
CREATE INDEX idx_users_email_lower ON users (lower(email));

-- Covering (include extra cols to enable index-only scans)
CREATE INDEX idx_orders_cov ON orders(user_id) INCLUDE (total, status);

-- GIN for JSONB / arrays / full-text
CREATE INDEX idx_events_data ON events USING gin (data jsonb_path_ops);
CREATE INDEX idx_docs_fts ON docs USING gin (to_tsvector('english', body));
```

Rules: match leftmost columns of composite indexes; don't over-index (write cost); drop unused ones (`pg_stat_user_indexes`).

## Query Optimization

```sql
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;  -- always use ANALYZE + BUFFERS
```

Look for: `Seq Scan` on large tables (missing index), high `rows removed by filter`, nested loop over millions (needs hash/merge join), mismatched `estimated vs actual` rows (run `ANALYZE`).

Tips: `SELECT` only needed columns; avoid `OFFSET` for pagination (use keyset: `WHERE (created_at, id) < ($1, $2) ORDER BY ... LIMIT 20`); `EXISTS` > `IN (subquery)` usually; batch writes in transactions.

## JSONB

```sql
CREATE TABLE events (id bigserial PRIMARY KEY, data jsonb NOT NULL);

-- query
SELECT data->>'user_id' FROM events WHERE data @> '{"type":"purchase"}';
SELECT * FROM events WHERE data #>> '{meta,source}' = 'ios';

-- update a key
UPDATE events SET data = jsonb_set(data, '{status}', '"done"', true) WHERE id = 1;
```

Use `@>`, `?`, `?&`, `?|` with GIN. Don't use JSONB as a replacement for normalized columns when you always query a field — promote it to a real column.

## Partitioning (large tables)

```sql
CREATE TABLE events (id bigserial, ts timestamptz NOT NULL, data jsonb)
  PARTITION BY RANGE (ts);

CREATE TABLE events_2026_04 PARTITION OF events
  FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');
```

Automate monthly partitions (pg_partman). Drop old partitions instead of `DELETE` (instant, no bloat).

## Migrations

Tools: Flyway, Liquibase, Alembic (Python), Prisma/Knex (Node), golang-migrate.

Safe patterns:
- Add column nullable, backfill in batches, then add NOT NULL
- `CREATE INDEX CONCURRENTLY` (avoids locking writes)
- Avoid `ALTER TABLE ... SET DEFAULT` with rewrite on big tables (PG 11+ is cheap for constants)
- Use `lock_timeout` and `statement_timeout` in migration sessions
- Never rename columns in-place on hot tables — add new, dual-write, migrate reads, drop old

```sql
SET lock_timeout = '2s';
ALTER TABLE users ADD COLUMN plan text;
UPDATE users SET plan = 'free' WHERE plan IS NULL;  -- in batches in app code
CREATE INDEX CONCURRENTLY idx_users_plan ON users(plan);
```

## Operations

- Tune `shared_buffers` (~25% RAM), `effective_cache_size` (~75%), `work_mem` per connection
- Use a **connection pooler** (PgBouncer) — Postgres connections are expensive
- Run `VACUUM (ANALYZE)` automatically; watch `pg_stat_user_tables.n_dead_tup`
- Replication: streaming + logical (for zero-downtime migrations, CDC)
- Back up with `pg_basebackup` + WAL archiving; test restores
- Observability: `pg_stat_statements`, `auto_explain`
