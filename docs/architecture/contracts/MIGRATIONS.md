# MIGRATIONS CONTRACT

**Status:** ENFORCED
**Effective:** 2026-01-17
**Scope:** All Alembic migrations
**Reference:** PIN-LIM Post-Implementation Design Fix

---

## Prime Directive

> **Migration lineage is a chain. Broken links are unrecoverable.**

---

## 1. Migration Header Contract (MANDATORY)

Every migration file **must** begin with this header block:

```python
# MIGRATION_CONTRACT:
#   domain: {domain_name}
#   parent: {exact_parent_revision_id}
#   creates_tables: {table1, table2} | none
#   modifies_tables: {table1, table2} | none
#   irreversible: true | false
#   requires_backfill: true | false
```

Then the standard Alembic docstring and revision variables.

**Example:**

```python
# MIGRATION_CONTRACT:
#   domain: limits
#   parent: 093_llm_run_records_system_records
#   creates_tables: limit_overrides
#   modifies_tables: none
#   irreversible: false
#   requires_backfill: false

"""
094 — Limit Overrides Table
...
"""

revision = "094_limit_overrides"
down_revision = "093_llm_run_records_system_records"
```

---

## 2. Revision ID Format

| Component | Format | Example |
|-----------|--------|---------|
| Sequence number | 3-digit zero-padded | `094` |
| Separator | underscore | `_` |
| Description | snake_case, max 40 chars | `limit_overrides` |

**Full format:** `{NNN}_{description}`

**Examples:**
- `094_limit_overrides`
- `095_add_policy_audit_columns`
- `096_create_cost_alerts`

**Forbidden:**
- UUIDs as revision IDs
- Timestamps in revision IDs
- CamelCase in description
- Spaces or hyphens

---

## 3. Parent Verification (Pre-Migration Guard)

Before any migration runs, the guard script verifies:

```bash
python scripts/preflight/check_alembic_parent.py 094_limit_overrides
```

**Checks:**
1. `MIGRATION_CONTRACT.parent` exists in `alembic/versions/`
2. `down_revision` matches `MIGRATION_CONTRACT.parent` exactly
3. No multiple heads exist (single lineage)

**Failure response:**

```
MIGRATION PARENT VERIFICATION FAILED

Migration: 094_limit_overrides
Declared parent: 093_llm_run_records_system_records
Found in versions/: NO

Available migrations:
  - 093_llm_run_records_system_records  ← Did you mean this?
  - 092_...

Fix: Update MIGRATION_CONTRACT.parent to exact revision ID
```

---

## 4. Database Target Enforcement

Migrations **must** run against the correct database tier.

### Environment Guard (in alembic/env.py)

```python
import os

def validate_db_target():
    db_url = os.getenv("DATABASE_URL", "")
    db_authority = os.getenv("DB_AUTHORITY", "")

    # Production migrations require explicit authority
    if "neon" in db_url.lower() or "prod" in db_url.lower():
        if db_authority != "neon":
            raise RuntimeError(
                "MIGRATION BLOCKED: Production DB detected but DB_AUTHORITY != 'neon'\n"
                "Set DB_AUTHORITY=neon to confirm intent"
            )

    # Log target for visibility
    print(f"[MIGRATION] Target: {db_authority or 'unspecified'}")
    print(f"[MIGRATION] Host: {db_url.split('@')[1].split('/')[0] if '@' in db_url else 'unknown'}")
```

### Required Environment Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `DATABASE_URL` | Connection string | Target database |
| `DB_AUTHORITY` | `neon` or `local` | Explicit declaration |

**Rule:** If `DB_AUTHORITY` is missing, migration fails.

---

## 5. Migration Execution Protocol

### Step 1: Verify Parent

```bash
python scripts/preflight/check_alembic_parent.py {revision_id}
```

### Step 2: Set Authority

```bash
export DB_AUTHORITY=neon
export DATABASE_URL=$(grep DATABASE_URL .env | cut -d= -f2-)
```

### Step 3: Dry Run (Optional but Recommended)

```bash
cd backend && alembic upgrade {revision_id} --sql > /tmp/migration_preview.sql
```

### Step 4: Execute

```bash
cd backend && alembic upgrade head
```

### Step 5: Verify

```bash
cd backend && alembic current
```

---

## 6. Rollback Rules

| Condition | Allowed | Notes |
|-----------|---------|-------|
| `irreversible: false` | Yes | `alembic downgrade -1` |
| `irreversible: true` | No | Manual intervention required |
| Data loss involved | Ask | Requires explicit approval |

**Rule:** Never `alembic downgrade` in production without explicit approval.

---

## 7. Multi-Head Prevention

**Invariant:** Only one head may exist at any time.

**Check:**

```bash
cd backend && alembic heads
```

Expected output: Single revision ID

**If multiple heads:**

```
MIGRATION BLOCKED: Multiple heads detected

Heads:
  - 094_limit_overrides
  - 094_other_migration

Resolution required before proceeding.
Options:
  1. Merge migrations
  2. Rebase one migration
  3. Request human decision
```

---

## 8. CI Integration

**.github/workflows/migration-check.yml**

```yaml
- name: Check migration lineage
  run: |
    cd backend
    python scripts/preflight/check_alembic_parent.py --all

- name: Check for multiple heads
  run: |
    cd backend
    heads=$(alembic heads | wc -l)
    if [ "$heads" -gt 1 ]; then
      echo "Multiple heads detected"
      exit 1
    fi
```

---

## 9. Violation Response

```
MIGRATIONS CONTRACT VIOLATION

Migration: {revision_id}
Rule violated: {rule_id}

Issue: {description}
Expected: {expected}
Found: {actual}

Resolution: {specific steps}
```

---

## Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│                 MIGRATION SAFETY CHECKLIST                  │
├─────────────────────────────────────────────────────────────┤
│  [ ] MIGRATION_CONTRACT header present                      │
│  [ ] parent matches down_revision exactly                   │
│  [ ] Revision ID format: NNN_description                    │
│  [ ] DB_AUTHORITY explicitly set                            │
│  [ ] Parent verification script passed                      │
│  [ ] No multiple heads                                      │
│  [ ] Dry run reviewed (if modifying existing tables)        │
└─────────────────────────────────────────────────────────────┘
```
