# Database Authority Contract

**Status:** LOCKED (Updated 2026-01-21)
**Effective:** 2026-01-10
**Reference:** DB-AUTH-001

---

## Authority Declaration (Non-Negotiable)

```
AUTHORITATIVE_DB = neon (for production data)
LOCAL_DB_ROLE = staging (for migration rehearsal)
```

---

## Database Roles (Migration Governance)

Migrations are governed by `DB_ROLE`, not `DB_AUTHORITY`.

| DB_ROLE | Meaning | Migrations |
|---------|---------|------------|
| **staging** | Pre-prod / local / CI | ✅ Allowed |
| **prod** | Production canonical | ✅ Allowed (with CONFIRM_PROD_MIGRATIONS=true) |
| **replica** | Read-only / analytics | ❌ Blocked |

### Migration Environment Setup

**Local staging:**
```bash
DB_AUTHORITY=local DB_ROLE=staging alembic upgrade head
```

**Production:**
```bash
DB_AUTHORITY=neon DB_ROLE=prod CONFIRM_PROD_MIGRATIONS=true alembic upgrade head
```

---

## Rules

### Neon is the ONLY source of truth for:

- Capability registry
- Run history
- Production-like validation
- Governance checks
- SDSR scenario verification
- Trace and incident records
- Policy proposal state

### Local DB is for:

- **Migration rehearsal** (staging role)
- Unit/integration tests
- Synthetic or disposable data
- Schema experiments

---

## Enforcement

**Violation = protocol breach.**

This is not documentation. This is **law**.

---

## Environment Variables (Required)

Every execution context MUST define:

```env
DB_AUTHORITY=<neon|local>
DB_ENV=<prod-like|dev|test>
```

Absence = **hard failure**.

---

## Connection Mapping

| Authority | DATABASE_URL Pattern |
|-----------|---------------------|
| neon | `*neon.tech*` |
| local | `localhost:*` or `127.0.0.1:*` or Docker service |

---

## Decision Table

| Task Type | DB to Use | Reason |
|-----------|-----------|--------|
| Historical truth | Neon | Authoritative |
| Capability state | Neon | Source of truth |
| Run verification | Neon | Non-ephemeral |
| SDSR execution | Neon | Canonical validation |
| Migration testing | Local | Disposable |
| Schema experiments | Local | Safe |
| Unit tests | Local | Isolated |

If the task spans both:
- **Neon = read**
- **Local = write/test**

No exceptions.

---

## The Core Rule

> **Claude must never infer database authority from evidence. Authority is declared, not discovered.**

Discovery is forbidden.
Inference is a violation.
Guessing is not intelligence.

---

## Related

- `docs/governance/DB_AUTH_001_INVARIANT.md` - Formal invariant
- `backend/scripts/_db_guard.py` - Enforcement script

---

## Alembic Configuration

**Config:** `backend/alembic.ini`
**Env module:** `backend/alembic/env.py` (245 lines)

### Validation Gate (env.py)

`validate_db_authority()` enforces:
1. `DB_ROLE` must be explicitly set (`staging`, `prod`, or `replica`)
2. Only `staging` and `prod` allow migrations
3. `prod` requires `CONFIRM_PROD_MIGRATIONS=true`
4. `replica` always blocked
5. `DATABASE_URL` must be set
6. Warns on mismatches (e.g., `DB_ROLE=prod` with localhost)

Version column widened to `VARCHAR(128)` for descriptive revision IDs.

---

## Migration Inventory (124 files)

**Location:** `backend/alembic/versions/`

### Naming Conventions

| Pattern | Meaning | Example |
|---------|---------|---------|
| `NNN_description.py` | Sequential | `096_incidents_domain_model.py` |
| `mNN_description.py` | Milestone-bound | `m10_recovery_enhancements.py` |
| `sN_description.py` | S-phase (truth gates) | `s6_trace_immutability.py` |
| `pb_sN_description.py` | Post-baseline fix | `pb_s2_crashed_status.py` |
| `cN_description.py` | C-phase (compliance) | `c2_prediction_hardening.py` |
| `wN_description.py` | W-phase (workload) | `w2_audit_events.py` |

### Latest Migrations (as of 2026-02-09)

| File | Lines | Date |
|------|-------|------|
| 122_knowledge_plane_registry.py | 73 | 2026-02-08 |
| 121_add_costsim_canary_reports.py | 76 | 2026-02-08 |
| 120_add_is_frozen_to_api_keys.py | 45 | 2026-01-23 |
| 119_w2_mcp_servers.py | 508 | 2026-01-21 |
| 118_w2_knowledge_planes.py | 447 | 2026-01-21 |
| 117_w2_budget_envelopes.py | 324 | 2026-01-21 |
| 116_w2_audit_events.py | 215 | 2026-01-21 |

---

## Governance Tools

| Tool | Purpose | Usage |
|------|---------|-------|
| `scripts/_db_guard.py` | Authority validation | Auto-checks on import |
| `scripts/ops/db_authority_drift_detector.py` | Drift scanner | `python db_authority_drift_detector.py --trend` |
| `scripts/ops/alembic_migration_audit.py` | Migration audit CSV | `python alembic_migration_audit.py` |
| `scripts/ci/check_migrations_two_path.py` | Two-path migration validation | `DB_ROLE=staging DATABASE_URL=... python scripts/ci/check_migrations_two_path.py` |
| `.db_authority_drift_history.json` | Drift tracking | Auto-maintained |

### Drift Detector Exit Codes

| Code | Meaning |
|------|---------|
| 0 | No drift |
| 1 | Drift detected |
| 2 | Error |
| 3 | REGRESSION (hard fail) |

### DB Guard Functions

| Function | Purpose |
|----------|---------|
| `get_declared_authority()` | Returns `DB_AUTHORITY` from env |
| `assert_db_authority(expected)` | Fails if mismatch |
| `require_neon()` | Assert neon authority |
| `require_local()` | Assert local authority |

---

## Fresh DB Bootstrap (ORM + Stamp)

**Critical:** Alembic migrations are incremental — they assume core ORM tables already exist.
Running `alembic upgrade head` on an empty DB **will fail** at migrations that ALTER TABLE on ORM-created tables.

### Correct Procedure

```bash
# 1. Create all ORM tables via app bootstrap
DATABASE_URL="postgresql://nova:novapass@localhost:6432/nova_aos" \
  PYTHONPATH=. python3 -c "from app.db import init_db; init_db()"

# 2. Stamp alembic at HEAD
DB_ROLE=staging DATABASE_URL="postgresql://nova:novapass@localhost:5433/nova_aos" \
  PYTHONPATH=. python3 -m alembic stamp head

# 3. Verify
DB_ROLE=staging DATABASE_URL="postgresql://nova:novapass@localhost:5433/nova_aos" \
  PYTHONPATH=. python3 -m alembic current
# Expected: 122_knowledge_plane_registry (head)
```

### Alembic Stamp Commit Fix (SQLAlchemy 2.x)

`backend/alembic/env.py` now uses `connectable.begin()` to ensure DDL and
`alembic_version` writes are committed under SQLAlchemy 2.x. Manual SQL
stamping is no longer required for fresh DBs.

If a stamp still fails, validate `DB_ROLE=staging`, `DATABASE_URL`, and
confirm your DB user has DDL rights.

### ORM Tables (19) Created by init_db()

---

## Two-Path Migration Contract (CI)

All migration changes must pass both paths:

**Path A — Clean DB:** `alembic upgrade head` on an empty database.  
**Path B — ORM Bootstrap:** `init_db()` followed by `alembic stamp head`.

This guards against:
- Missing CREATE TABLE migrations for ORM-owned tables
- Non-idempotent migrations that fail on pre-existing objects
- Stamp inconsistencies under SQLAlchemy 2.x

**CI entrypoint:**
```bash
DB_ROLE=staging DATABASE_URL="postgresql://..." \
  python3 scripts/ci/check_migrations_two_path.py
```

These tables are defined in `app/db.py` via SQLModel and are **never** created by alembic migrations:

`agents`, `approval_requests`, `cost_anomalies`, `cost_breach_history`, `cost_budgets`,
`cost_daily_aggregates`, `cost_drift_tracking`, `cost_records`, `costsim_cb_incidents`,
`costsim_cb_state`, `failure_matches`, `feature_flags`, `feature_tags`, `memories`,
`policy_approval_levels`, `provenance`, `runs`, `sdsr_incidents`, `status_history`

### Reference

- **PIN-542:** Local DB Migration Issues & Fixes (5 blocking issues documented)
