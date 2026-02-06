# TODO — Iteration 3.3

**Date:** 2026-02-06
**Status:** COMPLETE ✅
**Purpose:** HOC Spine "system runtime" hardening (first principles, no workarounds)

---

## Task Summary

Fix 6 import failures in `app.hoc.cus.hoc_spine` and add registry hardening.

---

## 1) Fix Scope: 6 Import Failures ✅

### 1.1) `consequences/adapters/export_bundle_adapter.py`
- **Issue:** NameError — `RunSnapshot`, `TraceSummarySnapshot`, `IncidentSnapshot` used without imports
- **Fix:** Added import from `app.hoc.cus.logs.L6_drivers.export_bundle_store`

### 1.2) `drivers/guard_cache.py`
- **Issue:** ModuleNotFoundError — `from .metrics_helpers import ...` but no such module
- **Fix:** Changed to `from app.hoc.cus.hoc_spine.services.metrics_helpers import ...`

### 1.3) `drivers/idempotency.py`
- **Issue:** ModuleNotFoundError — `from ..db import Run, engine` but `..db` doesn't exist
- **Fix:** Changed to `from app.db import Run, engine`

### 1.4) `orchestrator/lifecycle/engines/onboarding.py`
- **Issue:** ModuleNotFoundError — `from .base import ...` but `.base` doesn't exist
- **Fix:** Changed to `from app.hoc.cus.hoc_spine.services.lifecycle_stages_base import ...`

### 1.5) `orchestrator/lifecycle/engines/offboarding.py`
- **Issue:** ModuleNotFoundError — same as onboarding
- **Fix:** Changed to `from app.hoc.cus.hoc_spine.services.lifecycle_stages_base import ...`

### 1.6) `orchestrator/plan_generation_engine.py`
- **Issue:** ImportError — `from app.hoc.int.platform.facades import get_planner` doesn't exist
- **Fix:** Changed to `from app.planners import get_planner`

---

## 2) Acceptance Criterion #1: Package Import Scan ✅

```
=== ITER3.3 Full Package Import Scan: app.hoc.cus.hoc_spine ===

Summary: 150 passed, 0 failed
```

---

## 3) Acceptance Criterion #2: Pytest Guard ✅

Created: `tests/hoc_spine/test_hoc_spine_import_guard.py`

Tests:
- `test_all_hoc_spine_modules_import_successfully` — walks all 150+ modules
- `test_critical_modules_import` — tests the 6 fixed modules explicitly
- `test_operation_registry_importable` — verifies OperationRegistry singleton

```
============================= test session starts ==============================
tests/hoc_spine/test_hoc_spine_import_guard.py::TestHocSpineImportGuard::test_all_hoc_spine_modules_import_successfully PASSED [ 33%]
tests/hoc_spine/test_hoc_spine_import_guard.py::TestHocSpineImportGuard::test_critical_modules_import PASSED [ 66%]
tests/hoc_spine/test_hoc_spine_import_guard.py::TestHocSpineImportGuard::test_operation_registry_importable PASSED [100%]

============================== 3 passed in 3.14s ===============================
```

---

## 4) Acceptance Criterion #3: Registry Hardening ✅

### Bootstrap Function
Created: `app/hoc/cus/hoc_spine/orchestrator/handlers/__init__.py::bootstrap_hoc_spine()`

Performs:
1. Validates all hoc_spine modules import successfully (fail-fast)
2. Registers all operation handlers via `register_all_handlers()`
3. Calls `registry.freeze()` to prevent runtime registration

### Startup Wiring
Added to: `app/main.py:417-423` (inside `lifespan()`)

```python
# ITER3.3: HOC Spine Bootstrap (Registry Hardening)
from app.hoc.cus.hoc_spine.orchestrator.handlers import bootstrap_hoc_spine

try:
    bootstrap_hoc_spine()
    logger.info("hoc_spine_bootstrap_complete")
except RuntimeError as e:
    logger.critical(f"STARTUP ABORTED - HOC Spine bootstrap failed: {e}")
    raise
```

### Freeze Call Proof
```
app/main.py:420:        bootstrap_hoc_spine()
app/hoc/cus/hoc_spine/orchestrator/handlers/__init__.py:178:    registry.freeze()
```

---

## 5) Evidence Summary

| Criterion | Result |
|-----------|--------|
| Package import scan passes | ✅ 150/150 modules (0 failures) |
| Pytest guard added | ✅ 3 tests, all passing |
| Registry freeze in startup | ✅ `bootstrap_hoc_spine()` → `registry.freeze()` |
| 6 modules fixed | ✅ All import successfully |

---

## Files Modified

1. `app/hoc/cus/hoc_spine/consequences/adapters/export_bundle_adapter.py` — added snapshot imports
2. `app/hoc/cus/hoc_spine/drivers/guard_cache.py` — fixed metrics_helpers path
3. `app/hoc/cus/hoc_spine/drivers/idempotency.py` — fixed Run/engine imports
4. `app/hoc/cus/hoc_spine/orchestrator/lifecycle/engines/onboarding.py` — fixed base imports
5. `app/hoc/cus/hoc_spine/orchestrator/lifecycle/engines/offboarding.py` — fixed base imports
6. `app/hoc/cus/hoc_spine/orchestrator/plan_generation_engine.py` — fixed get_planner import
7. `app/hoc/cus/hoc_spine/orchestrator/handlers/__init__.py` — added `bootstrap_hoc_spine()`
8. `app/main.py` — wired bootstrap into lifespan startup

## Files Created

1. `tests/hoc_spine/test_hoc_spine_import_guard.py` — pytest import guard
2. `docs/memory-pins/TODO_ITER3.3.md` — this evidence note
