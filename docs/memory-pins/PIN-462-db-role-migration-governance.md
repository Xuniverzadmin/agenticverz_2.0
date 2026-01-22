# PIN-462: DB_ROLE Migration Governance Model

**Status:** COMPLETE
**Created:** 2026-01-21
**Category:** Governance / Infrastructure

---

## Summary

Fixed migration governance by introducing `DB_ROLE` as the authoritative control for migration eligibility. The previous model incorrectly assumed "only Neon is authoritative", blocking legitimate local staging migrations. The new model correctly separates database role (staging/prod/replica) from location (local/neon).

---

## Problem Statement

The migration gate in `alembic/env.py` enforced:

```
if DB_AUTHORITY != "neon":
    block_migrations()
```

This was a **governance misclassification**. The intended model was:
- **Local** = staging authority (mutable, migratable for rehearsal)
- **Neon** = production authority (canonical)

But the code assumed:
- **Neon** = only authoritative
- **Local** = disposable dev (no migrations)

This blocked all local staging migrations, preventing proper migration rehearsal.

---

## Solution: DB_ROLE Semantic

Replaced location-based authority with role-based authority.

### New Environment Variables

| Variable | Purpose |
|----------|---------|
| `DB_AUTHORITY` | Location (local, neon) - informational |
| `DB_ROLE` | Role (staging, prod, replica) - **authoritative for migrations** |
| `CONFIRM_PROD_MIGRATIONS` | Safety gate for production |

### DB_ROLE Values

| DB_ROLE | Meaning | Migrations |
|---------|---------|------------|
| **staging** | Pre-prod / local / CI | ✅ Allowed |
| **prod** | Production canonical | ✅ Allowed (with confirmation) |
| **replica** | Read-only / analytics | ❌ Blocked |

### Environment Mapping

| Environment | DB_AUTHORITY | DB_ROLE |
|-------------|--------------|---------|
| Local dev   | local        | staging |
| Neon test   | neon         | staging |
| Neon prod   | neon         | prod    |

---

## Files Modified

### `backend/alembic/env.py`

New `validate_db_authority()` function:
- Requires `DB_ROLE` (not just `DB_AUTHORITY`)
- Blocks `replica` role
- Requires `CONFIRM_PROD_MIGRATIONS=true` for `prod` role
- Warns on role-URL mismatches (but doesn't block)

### `docs/architecture/ENVIRONMENT_CONTRACT.md`

Added Section 4.5 "Database Roles (Migration Governance)":
- Documents the three-role model
- Provides migration command examples
- Explains safety rules

### `docs/runtime/DB_AUTHORITY.md`

Updated to reflect role-based migration governance:
- Changed header to show staging role for local
- Added "Database Roles" section
- Updated migration examples

---

## Migration Commands

### Local Staging (Rehearsal)

```bash
export DB_AUTHORITY=local
export DB_ROLE=staging
export DATABASE_URL=postgresql://...
alembic upgrade head
```

### Production (With Confirmation)

```bash
export DB_AUTHORITY=neon
export DB_ROLE=prod
export CONFIRM_PROD_MIGRATIONS=true
export DATABASE_URL=postgresql://...neon.tech/...
alembic upgrade head
```

### CI/Test

```bash
export DB_ROLE=staging
alembic upgrade head
```

---

## Safety Rules

1. **replica is always blocked** — Read-only databases never accept migrations
2. **prod requires confirmation** — Set `CONFIRM_PROD_MIGRATIONS=true`
3. **DB_ROLE is authoritative** — `DB_AUTHORITY` is informational only
4. **Warnings don't block** — Role-URL mismatches warn but proceed

---

## Why This Is Correct

The previous model was:
```
Local (toy) → Neon (real)
```

The correct enterprise model is:
```
Local (staging) → Neon (prod)
```

This matches:
- Real staging → prod pipelines
- Deterministic migration rehearsal
- Zero hacks or bypasses

---

## Invariants Established

1. **Migrations governed by role, not location** — `DB_ROLE` is authoritative
2. **Production requires explicit confirmation** — Safety gate prevents accidents
3. **Replica is read-only** — Never accepts schema changes
4. **No bypasses** — This is governance, not convenience

---

## Related

- `backend/alembic/env.py` — Migration gate implementation
- `docs/architecture/ENVIRONMENT_CONTRACT.md` — Section 4.5
- `docs/runtime/DB_AUTHORITY.md` — Updated authority contract
- PIN-460 — Tenant resolver UUID enforcement (used this migration)

---

## Reference

This fix was not a bypass — it was correcting a false assumption in the governance model. The system now correctly supports enterprise staging → prod workflows.
