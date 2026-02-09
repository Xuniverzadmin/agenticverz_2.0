# Local DB Equivalence v1 (Authoritative Procedure)

**Date:** 2026-02-09  
**Purpose:** Rebuild local staging DB to match the authoritative Alembic migration history.  
**Audience:** Claude execution instructions  
**Policy:** No workarounds. No stamping. No ORM bootstrap.

---

## Root Cause

Local DB was stamped at head without running migrations. This created a 128‑table gap versus the 156 tables defined across 124 migrations. The only correct fix is a clean rebuild from migrations.

---

## Required Procedure (No Alternatives)

### 1) Stop any app startup that runs ORM bootstrap

Confirm `SQLModel.metadata.create_all()` is **not** called during migration.
If it is, disable it for this run.

### 2) Drop and recreate the local DB

```bash
dropdb nova_aos
createdb nova_aos
```

### 3) Run full Alembic migrations (base → head)

```bash
cd backend
PYTHONPATH=. DB_AUTHORITY=local DB_ROLE=staging DATABASE_URL='postgresql://...' \
  python3 -m alembic -c alembic.ini upgrade head
```

### 4) Verify schema integrity

```sql
SELECT COUNT(*) FROM information_schema.tables
WHERE table_schema='public' AND table_type='BASE TABLE';

SELECT version_num FROM alembic_version;
```

### 5) Confirm no out‑of‑band tables were created

Compare table count against the migration inventory (156).
If mismatch, stop and investigate before proceeding.

---

## Success Criteria

- Table count equals the migration inventory.
- `alembic_version` is `124`.
- No tables created outside migrations.

---

## Execution Checklist (Claude Must Report)

1. DB dropped and recreated.
2. Migrations ran without stamp.
3. Table count verified.
4. `alembic_version` verified.
5. No ORM bootstrap occurred during migration.

