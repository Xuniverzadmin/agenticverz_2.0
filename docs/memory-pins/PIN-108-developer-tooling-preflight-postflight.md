# PIN-108: Developer Tooling - Preflight, Postflight & Dev Sync

**Status:** ACTIVE
**Category:** Developer Experience / CI / Code Quality
**Created:** 2025-12-20
**Author:** Claude Opus 4.5

---

## Summary

Comprehensive developer tooling suite for pre-implementation evaluation, post-implementation hygiene checks, and automatic code synchronization. These tools catch issues like FastAPI route conflicts before they reach production.

---

## Problem Statement

During ops console development, a route ordering bug caused silent failures:
- `/ops/customers/at-risk` was defined AFTER `/ops/customers/{tenant_id}`
- FastAPI matched "at-risk" as a tenant_id, causing SQL errors
- This pattern existed in 4 different API files

**Root Cause:** No automated tooling to detect route conflicts or enforce static-before-parameter ordering.

---

## Solution Components

### 1. Preflight Evaluation (`scripts/ops/preflight.py`)

**Purpose:** Pre-implementation analysis to catch issues before coding.

**Features:**
- Route conflict detection (static vs parameter ordering)
- File pattern analysis
- Consistency checks
- Route relationship mapping

**Usage:**
```bash
# Check routes only
python3 scripts/ops/preflight.py --routes

# Full preflight
python3 scripts/ops/preflight.py
```

**Route Detection Pattern:**
```python
# Detects decorator patterns like:
@router.get("/customers/at-risk")     # Static route
@router.get("/customers/{tenant_id}") # Parameter route

# Flags if parameter route comes BEFORE static route
```

**Output Example:**
```
Route conflict: /customers/{tenant_id} shadows /customers/at-risk
  - /customers/{tenant_id} at ops.py:45
  - /customers/at-risk at ops.py:89
  FIX: Move static route BEFORE parameter route
```

### 2. Postflight Hygiene (`scripts/ops/postflight.py`)

**Purpose:** Post-implementation code quality verification.

**Check Categories:**
| Category | Description |
|----------|-------------|
| `syntax` | Python syntax validation |
| `imports` | Unused/missing imports |
| `security` | Hardcoded secrets, SQL injection patterns |
| `complexity` | Cyclomatic complexity, function length |
| `consistency` | Naming conventions, style |
| `coverage` | Test coverage gaps |
| `api` | Route conflicts, schema issues |
| `duplication` | Code clones |
| `unused` | Dead code detection |

**Usage:**
```bash
# Quick check (syntax, imports, security)
python3 scripts/ops/postflight.py --quick

# Full hygiene check
python3 scripts/ops/postflight.py

# JSON output for CI
python3 scripts/ops/postflight.py --json
```

**Security Patterns Detected:**
- Hardcoded API keys (32+ char alphanumeric)
- SQL injection (f-string in execute())
- Eval/exec on user input

**Excluded from security scan:**
- Test files (`test_*.py`, `*_test.py`)
- Enum definitions
- Short placeholder values

### 3. Dev Sync (`scripts/ops/dev_sync.sh`)

**Purpose:** Automatic container rebuild on code changes.

**Features:**
- File hash tracking (md5sum)
- Backend/frontend/website detection
- Docker compose rebuild triggers
- Watch mode for continuous sync

**Usage:**
```bash
# Check and sync if needed
./scripts/ops/dev_sync.sh

# Force rebuild all
./scripts/ops/dev_sync.sh --force

# Check only (no rebuild)
./scripts/ops/dev_sync.sh --check

# Continuous watch mode
./scripts/ops/dev_sync.sh --watch

# Quick check (skip website)
./scripts/ops/dev_sync.sh --quick
```

**Hash Storage:**
```
.dev_sync/
├── backend.hash    # backend/**/*.py hash
├── frontend.hash   # website/aos-console/**/*.{ts,tsx} hash
└── website.hash    # website/landing/**/*.{js,jsx} hash
```

---

## CI Integration

### Preflight Workflow (`.github/workflows/ci-preflight.yml`)

Runs before main CI to catch issues early:

```yaml
jobs:
  preflight:
    steps:
      - name: Run CI consistency check
        run: ./scripts/ops/ci_consistency_check.sh --quick

      - name: Check for route conflicts
        run: python3 ./scripts/ops/preflight.py --routes

      - name: Run code hygiene check
        run: python3 ./scripts/ops/postflight.py --quick --json

      - name: Security scan
        run: # Hardcoded secrets detection

      - name: Verify required files exist
        run: # Core files, pgvector infra

      - name: Check for common CI anti-patterns
        run: # || true on pytest, missing PYTHONUNBUFFERED
```

### Main CI Postflight (`.github/workflows/ci.yml`)

Runs after tests pass:

```yaml
postflight:
  needs: [test-unit, test-integration, test-e2e]
  steps:
    - name: Run full code hygiene check
      run: python3 ./scripts/ops/postflight.py --json > hygiene.json

    - name: Generate hygiene report
      run: # Parse JSON, generate summary
```

---

## Route Conflicts Fixed

| File | Conflict | Fix |
|------|----------|-----|
| `api/ops.py` | `/customers/{tenant_id}` before `/customers/at-risk` | Moved at-risk first |
| `api/operator.py` | `/replay/{call_id}` before `/replay/batch` | Moved batch first |
| `api/traces.py` | `/{trace_id}/mismatch` before `/mismatches/bulk-report` | Moved bulk-report first |
| `api/agents.py` | `/sba/{agent_id}` before `/sba/version` | Moved version first |

**Pattern Applied:**
```python
# CORRECT ORDER:
# 1. Static routes first
@router.get("/replay/batch")
async def batch_replay(...): ...

# 2. Parameter routes after
@router.post("/replay/{call_id}")
async def replay_call(...): ...
```

---

## Session Start Integration

`session_start.sh` now includes dev sync check:

```bash
# Check for code changes that need rebuild
if [ -f "./scripts/ops/dev_sync.sh" ]; then
    ./scripts/ops/dev_sync.sh --check
fi
```

---

## Key Files

| File | Purpose |
|------|---------|
| `scripts/ops/preflight.py` | Pre-implementation evaluation |
| `scripts/ops/postflight.py` | Post-implementation hygiene |
| `scripts/ops/dev_sync.sh` | Auto-rebuild on changes |
| `scripts/ops/session_start.sh` | Session initialization (updated) |
| `.github/workflows/ci-preflight.yml` | CI preflight job |
| `.github/workflows/ci.yml` | CI postflight job (added) |

---

## Metrics

- **Route conflicts detected:** 4 (all fixed)
- **Preflight check time:** ~2 seconds
- **Postflight quick check time:** ~5 seconds
- **Postflight full check time:** ~30 seconds
- **CI preflight timeout:** 10 minutes

---

## Future Enhancements

1. **Import resolution** - Detect circular imports
2. **Type coverage** - mypy integration
3. **Docstring coverage** - Missing documentation detection
4. **Breaking change detection** - API signature changes
5. **Pre-commit hooks** - Automatic preflight on commit

---

## References

- PIN-105: Ops Console Phase-1 (where bug was discovered)
- PIN-107: M24 Phase-2 Friction Intelligence
- PIN-106: SQLModel Linter Fixes (related code quality)
