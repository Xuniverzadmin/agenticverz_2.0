# PIN-542: Local DB Migration Issues & Fixes

**Status:** ✅ COMPLETE
**Created:** 2026-02-09
**Category:** Database

---

## Summary

Documents 5 blocking issues encountered during alembic upgrade head on local staging DB (nova_aos) after Neon branch deletion. Covers schema mismatches, duplicate tables, ORM-vs-migration conflicts, and SQLAlchemy 2.0 stamp bug.

---

## Context

Neon DB branch was deleted to save compute hours. Local `nova_db` (PostgreSQL via Docker) was used as staging DB. Running `alembic upgrade head` (124 migrations) revealed 5 blocking issues. All resolved; DB now at head `122_knowledge_plane_registry` with 20 tables.

---

## Issue 1: Migration 023 — Schema Mismatch (DEFERRED Migration)

**File:** `alembic/versions/023_m10_archive_partitioning.py`
**Error:** `column "stream_key" does not exist`

Migration 022 creates `dead_letter_archive` with columns:
`dl_msg_id, original_msg_id, candidate_id, failure_match_id, payload, reason, reclaim_count, dead_lettered_at, archived_at, archived_by`

Migration 023 tries to partition with **different columns**:
`original_msg_id, dl_msg_id, stream_key, payload, failure_reason, retry_count, archived_at, archived_by`

Same mismatch for `replay_log` (022: `idempotency_key, status, error_message`; 023: `recovery_id`).

Header says **"STATUS: DEFERRED (PIN-058)"** — never meant to run until tables exceed 100K rows.

**Fix:** Made upgrade/downgrade a no-op (`pass`). Partitioning deferred to future migration with correct schema.

---

## Issue 2: Migration 026 — Duplicate Table

**File:** `alembic/versions/026_m12_credit_tables_fix.py`
**Error:** `relation "credit_balances" already exists`

Migration 025 already creates `agents.credit_balances`. Migration 026 uses `op.create_table()` which has no `IF NOT EXISTS` semantics.

**Fix:** Replaced `op.create_table()` with raw SQL `CREATE TABLE IF NOT EXISTS agents.credit_balances (...)`.

---

## Issue 3: Migration 036 — Pre-existing Table Conflict

**File:** `alembic/versions/036_m21_tenant_auth_billing.py`
**Error:** `relation "tenants" already exists`

The `tenants` table was created by `SQLModel.metadata.create_all()` during app bootstrap, not by any alembic migration. Migration 036 tries to create it, conflicting with the pre-existing ORM-created table.

**Root cause:** Migration chain designed for already-bootstrapped Neon DB where ORM tables existed before alembic was introduced.

---

## Issue 4: Migration 065 — Missing ORM Table

**File:** `alembic/versions/065_precomputed_auth.py`
**Error:** `relation "runs" does not exist`

After dropping pre-existing tables (attempting clean migration), migration 065 tries `ALTER TABLE runs ADD COLUMN` but `runs` is NEVER created by any migration — only by `SQLModel.metadata.create_all()` in `app/db.py:init_db()`.

**Root cause:** Core tables (`runs`, `tenants`, `agents`, `memories`, etc.) are ORM-defined tables that predate the migration chain. Alembic only handles incremental schema changes.

---

## Issue 5: Alembic `stamp` Not Persisting

**Command:** `alembic stamp head`
**Symptom:** Reports success but `alembic_version` table never created.

Tested on PgBouncer (6432) and direct PostgreSQL (5433) — same behavior. The `env.py` uses `connectable.connect()` without explicit commit. In SQLAlchemy 2.0+, connections default to non-autocommit mode. The `context.begin_transaction()` context manager doesn't commit the DDL.

**Fix:** Manually created table and inserted version via psql:
```sql
CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(128) NOT NULL);
INSERT INTO alembic_version (version_num) VALUES ('122_knowledge_plane_registry');
```

---

## Resolution: Correct Fresh DB Bootstrap Procedure

For a fresh staging DB (no Neon), the correct sequence is:

```bash
# 1. Create all ORM tables via app bootstrap
DATABASE_URL="postgresql://nova:novapass@localhost:6432/nova_aos" \
  PYTHONPATH=. python3 -c "from app.db import init_db; init_db()"

# 2. Manually stamp alembic at head
PGPASSWORD=novapass psql -h localhost -p 5433 -U nova -d nova_aos -c "
  CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(128) NOT NULL);
  INSERT INTO alembic_version (version_num) VALUES ('122_knowledge_plane_registry');
"

# 3. Verify
DB_ROLE=staging DATABASE_URL="postgresql://nova:novapass@localhost:5433/nova_aos" \
  PYTHONPATH=. python3 -m alembic current
# Expected: 122_knowledge_plane_registry (head)
```

**DO NOT** run `alembic upgrade head` on a clean DB — it will fail because core ORM tables are not created by migrations.

---

## Files Modified

| File | Change |
|------|--------|
| `alembic/versions/023_m10_archive_partitioning.py` | upgrade/downgrade → no-op (PIN-058 deferred) |
| `alembic/versions/026_m12_credit_tables_fix.py` | `op.create_table` → `CREATE TABLE IF NOT EXISTS` |

---

## Final State

| Metric | Value |
|--------|-------|
| DB | `nova_aos` on `localhost:5433` (direct) / `6432` (PgBouncer) |
| Alembic Head | `123_incidents_source_run_fk` |
| Tables | 20 (19 ORM + alembic_version) |
| Schema | public only (no custom schemas from skipped 023) |
| DB_ROLE | staging |
| Commit | `ee87a605` (pushed to origin/main 2026-02-09) |

---

## Lessons Learned

1. **ORM tables predate alembic** — `init_db()` must run before any alembic operations on a fresh DB
2. **alembic stamp is broken with SQLAlchemy 2.0** — env.py needs `connectable.begin()` (fixed in PIN-544)
3. **DEFERRED migrations must be truly inert** — migration 023 had active DDL despite being marked deferred
4. **Duplicate CREATE TABLE across migrations** — always use `IF NOT EXISTS` for idempotency
5. **Neon deletion = full DB rebuild** — local staging requires ORM bootstrap + alembic stamp, not migration replay
