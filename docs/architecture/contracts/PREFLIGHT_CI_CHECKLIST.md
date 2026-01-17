# PREFLIGHT CI CHECKLIST

**Status:** ENFORCED
**Effective:** 2026-01-17
**Scope:** All code changes before merge
**Reference:** Design Fix Contracts

---

## Prime Directive

> **If preflight fails, code does not merge. No exceptions.**

---

## 1. Checklist Overview

| Check | Script | Blocking | Contract |
|-------|--------|----------|----------|
| Naming Contract | `check_naming_contract.py` | YES | NAMING.md |
| Migration Lineage | `check_alembic_parent.py` | YES | MIGRATIONS.md |
| Runtime/API Boundary | `check_runtime_api_boundary.py` | YES | RUNTIME_VS_API.md |
| Router Wiring | `check_router_registry.py` | YES | ROUTER_WIRING.md |
| DB Authority | `check_db_authority.py` | YES | DB_AUTH_001 |
| Layer Violations | `layer_validator.py` | YES | LAYER_MODEL.md |

---

## 2. Running Preflight Locally

### Full Suite

```bash
./scripts/preflight/run_all_checks.sh
```

### Individual Checks

```bash
# Naming contract
python scripts/preflight/check_naming_contract.py

# Migration lineage
python scripts/preflight/check_alembic_parent.py --all

# Runtime/API boundary
python scripts/preflight/check_runtime_api_boundary.py

# Router wiring
python scripts/preflight/check_router_registry.py

# DB authority (requires DATABASE_URL)
python scripts/preflight/check_db_authority.py

# Layer violations (BLCA)
python scripts/ops/layer_validator.py --backend --ci
```

---

## 3. Check Details

### 3.1 Naming Contract Check

**Script:** `scripts/preflight/check_naming_contract.py`

**Detects:**
- Runtime schemas with `_remaining`, `_current`, `_total` suffixes
- Database columns with camelCase
- Enum values not in UPPER_SNAKE_CASE

**Pass criteria:**
```
NAMING CONTRACT CHECK: PASSED
  - Runtime schemas: 0 violations
  - Database columns: 0 violations
  - Enum values: 0 violations
```

**Fail example:**
```
NAMING CONTRACT CHECK: FAILED

Violation 1:
  File: app/schemas/limits/simulation.py:15
  Field: tokens_remaining
  Rule: NC-001 (No context suffix in runtime schemas)
  Fix: Rename to 'tokens', move context to API adapter
```

---

### 3.2 Migration Lineage Check

**Script:** `scripts/preflight/check_alembic_parent.py`

**Detects:**
- Missing MIGRATION_CONTRACT header
- Parent revision not found in versions/
- down_revision mismatch with MIGRATION_CONTRACT.parent
- Multiple heads

**Pass criteria:**
```
MIGRATION LINEAGE CHECK: PASSED
  - All migrations have MIGRATION_CONTRACT header
  - All parent revisions exist
  - Single head: 094_limit_overrides
```

**Fail example:**
```
MIGRATION LINEAGE CHECK: FAILED

Migration: 095_new_feature.py
Issue: Parent revision not found

MIGRATION_CONTRACT.parent: 094_limit_override  (TYPO)
Available revisions:
  - 094_limit_overrides  ← Did you mean this?

Fix: Update MIGRATION_CONTRACT.parent to exact revision ID
```

---

### 3.3 Runtime/API Boundary Check

**Script:** `scripts/preflight/check_runtime_api_boundary.py`

**Detects:**
- API endpoints directly accessing runtime schema fields
- Missing adapters for domain responses
- Business logic in adapter functions

**Pass criteria:**
```
RUNTIME/API BOUNDARY CHECK: PASSED
  - All API responses use adapters
  - No direct runtime field access in L2
  - Adapters contain only transformations
```

**Fail example:**
```
RUNTIME/API BOUNDARY CHECK: FAILED

Violation 1:
  File: app/api/limits/simulate.py:45
  Code: result.headroom.tokens
  Rule: RAB-001 (No direct runtime access in API)
  Fix: Use adapter from app/api/_adapters/limits.py
```

---

### 3.4 Router Wiring Check

**Script:** `scripts/preflight/check_router_registry.py`

**Detects:**
- `include_router` calls outside registry.py
- Router imports in main.py
- Routers not registered in registry.py
- Missing `__all__` exports

**Pass criteria:**
```
ROUTER WIRING CHECK: PASSED
  - main.py only imports registry
  - All include_router in registry.py
  - All routers registered
```

**Fail example:**
```
ROUTER WIRING CHECK: FAILED

Violation 1:
  File: app/main.py:25
  Code: from app.api.limits import router
  Rule: RW-001 (No router imports in main.py)
  Fix: Move import to app/api/registry.py
```

---

### 3.5 DB Authority Check

**Script:** `scripts/preflight/check_db_authority.py`

**Detects:**
- Missing DB_AUTHORITY environment variable
- DATABASE_URL pointing to wrong tier
- Mismatch between declared authority and actual connection

**Pass criteria:**
```
DB AUTHORITY CHECK: PASSED
  - DB_AUTHORITY: neon
  - DATABASE_URL: postgresql://...neon.tech/...
  - Connection verified
```

**Fail example:**
```
DB AUTHORITY CHECK: FAILED

Issue: Authority mismatch

DB_AUTHORITY: neon
DATABASE_URL: postgresql://localhost:5432/nova_aos

Fix: Set DATABASE_URL to Neon connection string
```

---

## 4. CI Integration

### GitHub Actions Workflow

**.github/workflows/preflight-checks.yml**

```yaml
name: Preflight Checks

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main, develop]

jobs:
  preflight:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pydantic sqlalchemy

      - name: Naming Contract Check
        run: python scripts/preflight/check_naming_contract.py

      - name: Migration Lineage Check
        run: python scripts/preflight/check_alembic_parent.py --all

      - name: Runtime/API Boundary Check
        run: python scripts/preflight/check_runtime_api_boundary.py

      - name: Router Wiring Check
        run: python scripts/preflight/check_router_registry.py

      - name: Layer Violations (BLCA)
        run: python scripts/ops/layer_validator.py --backend --ci
```

---

## 5. Preflight Runner Script

**File:** `scripts/preflight/run_all_checks.sh`

```bash
#!/bin/bash
set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║               PREFLIGHT CHECKS                             ║"
echo "╚════════════════════════════════════════════════════════════╝"

cd "$(dirname "$0")/../.."

FAILED=0

run_check() {
    local name=$1
    local cmd=$2
    echo ""
    echo "▶ Running: $name"
    if $cmd; then
        echo "✓ $name: PASSED"
    else
        echo "✗ $name: FAILED"
        FAILED=1
    fi
}

run_check "Naming Contract" "python scripts/preflight/check_naming_contract.py"
run_check "Migration Lineage" "python scripts/preflight/check_alembic_parent.py --all"
run_check "Runtime/API Boundary" "python scripts/preflight/check_runtime_api_boundary.py"
run_check "Router Wiring" "python scripts/preflight/check_router_registry.py"
run_check "Layer Violations" "python scripts/ops/layer_validator.py --backend --ci"

echo ""
echo "════════════════════════════════════════════════════════════"

if [ $FAILED -eq 0 ]; then
    echo "✓ ALL PREFLIGHT CHECKS PASSED"
    exit 0
else
    echo "✗ PREFLIGHT CHECKS FAILED"
    echo "Fix violations before merging."
    exit 1
fi
```

---

## 6. Skip Policy

### When Skipping is Allowed

| Scenario | Skip Allowed | Approval Required |
|----------|--------------|-------------------|
| Hotfix for production incident | YES | Incident commander |
| Dependency update (no code change) | YES | None |
| Documentation only | YES | None |
| New feature | NO | - |
| Refactoring | NO | - |
| Bug fix | NO | - |

### Skip Mechanism

```bash
# In commit message
[skip-preflight] Emergency hotfix for incident #123
```

**CI respects skip only with:**
- `[skip-preflight]` in commit message
- AND author is in CODEOWNERS
- AND PR has `emergency` label

---

## 7. Failure Escalation

### If Preflight Fails

1. **Read the error message** — it tells you exactly what's wrong
2. **Check the contract** — linked in the error
3. **Fix the violation** — don't work around it
4. **Re-run preflight** — verify fix

### If You Think Preflight is Wrong

1. **Don't bypass** — file an issue
2. **Document the case** — specific file, line, why you think it's wrong
3. **Request review** — architecture team evaluates
4. **If approved** — contract is updated, then code merges

**Rule:** Contracts evolve. Bypasses do not.

---

---

## 8. Continuous Validation (Real-Time)

For real-time enforcement while coding, use the continuous validator daemon.

### Setup

```bash
# One-time setup
./scripts/preflight/setup_continuous_validation.sh

# Or manual:
pip3 install watchdog
sudo ln -sf /root/agenticverz2.0/scripts/preflight/validator /usr/local/bin/validator
```

### Usage

```bash
# Start validator in background
validator start

# Interactive dashboard
validator dashboard

# Compact watch mode
validator watch

# Desktop notifications
validator notify

# Check status
validator status

# View logs
validator log

# Stop validator
validator stop
```

### Systemd Service (Auto-Start on Boot)

```bash
# Enable auto-start
validator service enable

# Service controls
validator service start
validator service stop
validator service status
```

### What Gets Checked

| File Pattern | Checks Run |
|--------------|------------|
| `app/schemas/**/*.py` | naming |
| `app/models/**/*.py` | naming |
| `app/api/**/*.py` | naming, router, boundary |
| `alembic/versions/*.py` | migration |
| `app/main.py` | router |

### Dashboard Display

```
╔══════════════════════════════════════════════════════════════════╗
║           CONTINUOUS VALIDATOR DASHBOARD                         ║
╚══════════════════════════════════════════════════════════════════╝

  Status:        WATCHING
  Files Watched: 894
  Checks Run:    42
  Last Check:    2026-01-17T12:00:00

┌─────────────────────────────────────────────────────────────────┐
│  ✓ NO VIOLATIONS                                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│                 PREFLIGHT QUICK RUN                         │
├─────────────────────────────────────────────────────────────┤
│  Full suite:                                                │
│    ./scripts/preflight/run_all_checks.sh                    │
│                                                             │
│  Individual:                                                │
│    python scripts/preflight/check_naming_contract.py        │
│    python scripts/preflight/check_alembic_parent.py --all   │
│    python scripts/preflight/check_runtime_api_boundary.py   │
│    python scripts/preflight/check_router_registry.py        │
│    python scripts/ops/layer_validator.py --backend --ci     │
│                                                             │
│  Continuous (Real-Time):                                    │
│    validator start      # Start watching                    │
│    validator dashboard  # Live status                       │
│    validator status     # Quick check                       │
│                                                             │
│  CI:                                                        │
│    Runs automatically on PR                                 │
│    Must pass before merge                                   │
└─────────────────────────────────────────────────────────────┘
```
