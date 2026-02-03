# PIN-518: Analytics Storage Wiring Follow-ups

**Status:** ACTIVE
**Created:** 2026-02-03
**Predecessor:** PIN-517 (cus_vault Authority Refactor)
**Reference:** Analytics Storage Wiring Implementation

---

## Context

Analytics storage wiring was implemented to connect:
- `provenance_engine.py` → DB (via `write_provenance_batch`)
- `canary_engine.py` → DB (via `write_canary_report`)
- `costsim.py:/canary/reports` → DB (via `query_canary_reports`)

Migration 121 (`121_add_costsim_canary_reports.py`) creates the `costsim_canary_reports` table.

---

## Completed Fixes

### Fix 1: L2→L4 Routing (Gap 1 Resolution)

**Problem:** L2 `costsim.py` was calling L6 `provenance_driver.py` directly.

**Solution:** Added `CanaryReportHandler` to `analytics_handler.py` (L4) and routed `/canary/reports` endpoint through operation registry.

**Files Changed:**
- `app/hoc/cus/hoc_spine/orchestrator/handlers/analytics_handler.py`
- `app/hoc/api/cus/analytics/costsim.py`

### Fix 2: Artifact-Before-DB Invariant (Gap 3 Resolution)

**Problem:** `_persist_report_to_db` could write to DB without artifacts being saved first.

**Solution:** Added guard in `canary_engine.py:_persist_report_to_db()`:
```python
if self.config.save_artifacts and not report.artifact_paths:
    raise RuntimeError("Canary artifacts missing; refusing DB write.")
```

**Files Changed:**
- `app/hoc/cus/analytics/L5_engines/canary_engine.py`

---

## Completed Follow-ups

### FOLLOWUP-1: Split Provenance and Canary L6 Drivers (Gap 2) ✅

**Status:** COMPLETE
**Completed:** 2026-02-03

**Solution:**
Created `canary_report_driver.py` with canary-specific functions:
```
analytics/L6_drivers/
  ├── provenance_driver.py      # Provenance records only
  └── canary_report_driver.py   # Canary reports only
```

**Acceptance Criteria:**
- [x] `canary_report_driver.py` contains `write_canary_report`, `query_canary_reports`, `get_canary_report_by_run_id`
- [x] `provenance_driver.py` contains only provenance functions
- [x] L5 engines updated to import from correct driver (`canary_engine.py`)
- [x] L4 handler updated to import from correct driver (`analytics_handler.py`)
- [x] `__init__.py` exports canary report functions

---

## Pending Follow-ups

### FOLLOWUP-2: Index Performance Audit

**Priority:** Low (optimization)
**Severity:** Low unless query volume increases

**Current Indexes:**
- `idx_costsim_canary_run_id` (unique)
- `idx_costsim_canary_timestamp`
- `idx_costsim_canary_status`
- `idx_costsim_canary_passed`

**When to revisit:**
- If `/canary/reports` latency exceeds 100ms p95
- If canary report count exceeds 10,000 rows
- If new query patterns emerge (e.g., date range + status)

**Potential optimization:**
- Composite index on `(timestamp, status)` for filtered time-series queries
- Partial index on `passed = false` for failure analysis

---

### FOLLOWUP-3: Golden Comparison Implementation

**Priority:** Deferred (design decision required)
**Severity:** N/A until feature is scoped

**Current State:**
- `golden_comparison_json` column exists (nullable)
- No code populates it
- No code depends on it

**Required Design Decisions:**
1. What constitutes a "golden" reference dataset?
2. Where are golden datasets stored?
3. How is golden comparison computed?
4. What triggers golden dataset creation/update?

**Acceptance Criteria (when scoped):**
- [ ] Golden dataset storage location defined
- [ ] Golden comparison algorithm implemented
- [ ] `golden_comparison_json` populated in canary reports
- [ ] Dashboard surfaces golden comparison results

---

## Verification

```bash
# Verify L2→L4 routing works
curl -s http://localhost:8000/api/v1/costsim/canary/reports | jq '.reports | length'

# Verify migration applied
PYTHONPATH=. python3 -c "
from app.models.costsim import CostSimCanaryReportModel
print(f'Table: {CostSimCanaryReportModel.__tablename__}')
"

# Verify handler registration
PYTHONPATH=. python3 -c "
from app.hoc.cus.hoc_spine.orchestrator.handlers.analytics_handler import register
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import get_operation_registry
registry = get_operation_registry()
register(registry)
print('analytics.canary_reports registered:', 'analytics.canary_reports' in registry._handlers)
"
```

---

## Architecture Diagram (After Fixes)

```
L2 API (costsim.py)
    │
    ▼
L4 Handler (analytics_handler.py)
    │  CanaryReportHandler.execute()
    ▼
L6 Driver (provenance_driver.py)  ← FOLLOWUP-1: Split to canary_report_driver.py
    │  query_canary_reports()
    ▼
L7 Model (CostSimCanaryReportModel)
    │
    ▼
PostgreSQL (costsim_canary_reports table)
```

---

## References

- Migration: `alembic/versions/121_add_costsim_canary_reports.py`
- L4 Handler: `app/hoc/cus/hoc_spine/orchestrator/handlers/analytics_handler.py`
- L5 Engine: `app/hoc/cus/analytics/L5_engines/canary_engine.py`
- L6 Driver: `app/hoc/cus/analytics/L6_drivers/provenance_driver.py`
- L2 API: `app/hoc/api/cus/analytics/costsim.py`
