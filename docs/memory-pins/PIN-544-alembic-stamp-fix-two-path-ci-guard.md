# PIN-544: Alembic Stamp Fix + Two-Path CI Guard

**Status:** ✅ COMPLETE
**Created:** 2026-02-09
**Category:** Database

---

## Summary

Fixed alembic stamp commit for SA 2.x (env.py uses connectable.begin()), added two-path migration CI guard (check_migrations_two_path.py), formalized ORM bootstrap contract in DB_AUTHORITY.md.

---

## Context

Follow-up to PIN-542 (Local DB Migration Issues). The user fixed the alembic stamp persistence bug,
added a CI guard to prevent future migration chain breakage, and formalized the ORM bootstrap contract.

---

## Changes Made (by user)

### 1. Fixed Alembic Stamp Commit (SQLAlchemy 2.x)

**File:** `backend/alembic/env.py`

`run_migrations_online()` now uses `connectable.begin()` instead of `connectable.connect()`.
This ensures DDL (CREATE TABLE alembic_version) and INSERT writes are committed under
SQLAlchemy 2.x, which defaults to non-autocommit mode.

**Before (broken):**
```python
with connectable.connect() as connection:
    # DDL + INSERT never committed in SA 2.x
```

**After (fixed):**
```python
with connectable.begin() as connection:
    # Auto-commits on successful context exit
```

Manual SQL stamping is no longer required for fresh DBs.

### 2. Added CI Two-Path Migration Guard

**New file:** `scripts/ci/check_migrations_two_path.py`

Validates that migrations work on both bootstrap paths:

| Path | Procedure | Guards Against |
|------|-----------|----------------|
| **A — Clean DB** | `alembic upgrade head` on empty database | Missing CREATE TABLE for ORM-owned tables |
| **B — ORM Bootstrap** | `init_db()` then `alembic stamp head` | Non-idempotent migrations, stamp failures |

**Run:**
```bash
DB_ROLE=staging DATABASE_URL="postgresql://..." \
  python3 scripts/ci/check_migrations_two_path.py
```

### 3. Formalized ORM Bootstrap Contract

**File:** `docs/runtime/DB_AUTHORITY.md`

Updated sections:
- **Fresh DB Bootstrap:** Updated procedure — step 2 now uses `alembic stamp head` (no manual SQL)
- **Alembic Stamp Commit Fix:** Documents the SA 2.x `connectable.begin()` fix
- **Two-Path Migration Contract:** Formalizes Path A + Path B as CI requirement
- **Governance Tools table:** Added `check_migrations_two_path.py` entry

---

## Files Touched

| File | Change |
|------|--------|
| `backend/alembic/env.py` | `connectable.connect()` → `connectable.begin()` |
| `scripts/ci/check_migrations_two_path.py` | New CI guard script |
| `docs/runtime/DB_AUTHORITY.md` | Bootstrap procedure, two-path contract, governance tools |

---

## Docs Updated in This Session (Cumulative)

| Doc | Updates |
|-----|---------|
| `docs/architecture/hoc/domain_linkage_plan_v1.md` | Domain inventory, L4 handlers, bridges, CI guards, transaction ownership |
| `docs/architecture/console_domains/general_domain/governance/ENVIRONMENT_CONTRACT.md` | Sections 12-15: env var registry, vault paths, canonical sources, DB bootstrap vars |
| `docs/runtime/DB_AUTHORITY.md` | Alembic config, migration inventory, governance tools, ORM bootstrap, two-path CI |
| `docs/runbooks/SECRETS_ROTATION.md` | Active Vault procedures, Neon/Upstash/Clerk/Resend rotation flows, 17 secrets |
| `scripts/deploy/backend/.env.production.example` | Complete rewrite aligned with .env.example, Vault-aware |
| `hoc/doc/architeture/alembic/*` | 250 per-migration audit files (125 CSV + 125 summary MD) |

---

## Related PINs

- **PIN-542:** Local DB Migration Issues & Fixes (5 blocking issues)
- **PIN-543:** Alembic Migration Audit Docs Generated (250 files)

---

## Commit

All changes committed and pushed in `ee87a605` (2026-02-09).

---

## Open Item

psql client in the current environment returns blank errors. Direct DB schema verification
via psql may need troubleshooting. Application-level verification (`init_db()`, `alembic current`)
works correctly.
