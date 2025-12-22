# PIN-126: Test Infrastructure & Prevention Blueprint

**Status:** COMPLETE
**Category:** Testing / Prevention / Code Quality
**Created:** 2025-12-22
**Updated:** 2025-12-22
**Related PINs:** PIN-120, PIN-121, PIN-108, PIN-109, PIN-097

---

## Summary

Comprehensive implementation of the Prevention Blueprint for test infrastructure, including route sanity tests, registry integrity tests, OpenAPI contract snapshots, and pyright integration. This PIN consolidates all testing, prevention, and hygiene mechanisms across the AOS codebase.

---

## Prevention Blueprint Implementation

### 1. Pyright in CI (Non-Blocking)

**File:** `.github/workflows/ci.yml`

Added `pyright-check` job that:
- Runs pyright on `backend/app/`
- Outputs error/warning counts
- Non-blocking (`continue-on-error: true`)
- Generates GitHub summary with metrics

```yaml
pyright-check:
  runs-on: ubuntu-latest
  continue-on-error: true  # Non-blocking initially
  steps:
    - name: Run pyright
      run: |
        cd backend
        pyright app/ --outputjson 2>&1 | tee /tmp/pyright-output.json || true
```

**Purpose:** Catches type errors that mypy misses (e.g., tuple/arg mismatches).

---

### 2. Route Sanity Tests

**File:** `backend/tests/test_route_contracts.py`

Added `TestRouteSanity` class with 3 tests:

| Test | Purpose |
|------|---------|
| `test_all_routes_have_endpoints` | Every route has non-None endpoint |
| `test_all_routes_are_callable` | All endpoints are callable |
| `test_route_count_above_minimum` | At least 50 routes mounted (catches catastrophic failures) |

```python
def test_all_routes_have_endpoints(self):
    """CRITICAL: Every route must have a non-None endpoint."""
    from app.main import app
    broken_routes = []
    for route in app.routes:
        if not hasattr(route, "endpoint") or route.endpoint is None:
            broken_routes.append(route.path)
    assert len(broken_routes) == 0
```

---

### 3. Registry Integrity Tests

**File:** `backend/tests/test_route_contracts.py`

Added `TestRegistryIntegrity` class with 4 tests:

| Test | Purpose |
|------|---------|
| `test_skill_registry_not_empty` | At least 3 skills registered |
| `test_all_skills_have_version` | Every skill has version string |
| `test_all_skills_instantiable` | All skills can be created |
| `test_all_skills_have_execute_method` | Protocol compliance check |

Uses `@pytest.fixture(autouse=True)` to call `load_all_skills()` before tests.

---

### 4. OpenAPI Contract Snapshot

**Files:**
- `backend/tests/snapshots/ops_api_contracts.json` - Baseline snapshot
- `backend/tests/test_route_contracts.py` - `TestOpsAPIContractSnapshot` class

Added 3 contract drift tests:

| Test | Purpose |
|------|---------|
| `test_ops_endpoint_count_matches_snapshot` | Catches additions/removals |
| `test_ops_endpoints_match_snapshot` | Catches endpoint renames |
| `test_typed_endpoints_stay_typed` | Prevents response_model regressions |

**Snapshot Contents (13 endpoints):**
```json
{
  "version": "1.0.0",
  "endpoint_count": 13,
  "contracts": {
    "GET /ops/pulse": {"response_model": "SystemPulse"},
    "GET /ops/events": {"response_model": "OpsEventListResponse"},
    "POST /ops/jobs/compute-stickiness": {"response_model": "OpsJobResult"},
    ...
  }
}
```

---

## Test File Summary

### `test_route_contracts.py` - Complete Test Suite

| Class | Tests | Purpose |
|-------|-------|---------|
| `TestOpsRouteContracts` | 3 | Ops route shadowing prevention |
| `TestOperatorRouteContracts` | 1 | Operator route order |
| `TestTracesRouteContracts` | 1 | Traces route order |
| `TestAgentsRouteContracts` | 1 | Agents route order |
| `TestRouteValidationFunction` | 2 | Route validation function tests |
| `TestStaticBeforeParameterRule` | 1 | Static-before-param rule |
| `TestPIN108Regressions` | 3 | Regression tests for PIN-108 |
| `TestOpsAPIHygiene` | 4 | API response_model enforcement |
| `TestRouteSanity` | 3 | Route sanity checks |
| `TestRegistryIntegrity` | 4 | Skill registry integrity |
| `TestOpsAPIContractSnapshot` | 3 | OpenAPI contract drift |

**Total:** 26 tests, all passing

---

## Prevention Mechanisms Index

### From PIN-120 (Test Suite Stabilization)

| ID | Rule | Enforcement |
|----|------|-------------|
| PREV-1 | Idempotent Prometheus registration | `_get_or_create_*` helpers |
| PREV-2 | Metric naming convention (prefix with module) | Code review |
| PREV-3 | Explicit None checks (not `or` for defaults) | Policy compiler fix |
| PREV-4 | Cache timestamp initialization (never None) | `time.time()` defaults |
| PREV-5 | Test isolation fixtures | Autouse cleanup fixtures |
| PREV-6 | Concurrent claim SQL must use `FOR UPDATE SKIP LOCKED` | SQLModel linter |
| PREV-7 | Test categorization (`@pytest.mark.slow`) | postflight.py |
| PREV-8 | API contract testing (type annotations) | mypy in CI |
| PREV-9 | Config value access patterns | CFG001/CFG002 linter |
| PREV-10 | Slow test class marking | testhygiene check |
| PREV-11 | Migration ON CONFLICT patterns | MIG001 linter |
| PREV-12 | Async event loop management | ASYNC001 linter |

### From PIN-121 (Mypy Technical Debt)

| ID | Rule | Enforcement |
|----|------|-------------|
| PREV-13 | Mypy pre-commit (warning mode) | `.pre-commit-config.yaml` |
| PREV-14 | CI mypy step (non-blocking) | `.github/workflows/ci.yml` |
| PREV-15 | Postflight mypy category | `postflight.py` |

### From PIN-125 (SDK Parity)

| ID | Rule | Enforcement |
|----|------|-------------|
| PREV-16 | SDK Export Verification | postflight sdkparity |
| PREV-17 | Cross-Language Parity Pre-Commit | postflight sdkparity |
| PREV-18 | SDK Build Freshness | preflight.py + CI |
| PREV-19 | Hash Algorithm Parity Test | CI parity tests |

### From This PIN (PIN-126)

| ID | Rule | Enforcement |
|----|------|-------------|
| PREV-20 | Pyright CI (non-blocking) | `.github/workflows/ci.yml` |
| PREV-21 | Route sanity tests | `test_route_contracts.py::TestRouteSanity` |
| PREV-22 | Registry integrity tests | `test_route_contracts.py::TestRegistryIntegrity` |
| PREV-23 | OpenAPI snapshot diff | `test_route_contracts.py::TestOpsAPIContractSnapshot` |

---

## Hygiene Scripts

### Session Start (`scripts/ops/session_start.sh`)
- Checks working environment
- Shows current phase
- Lists blockers
- Verifies services

### Hygiene Check (`scripts/ops/hygiene_check.sh`)
- Detects stale files
- Checks PIN count
- Validates INDEX.md freshness
- Flags completed checklists
- `--fix` mode for auto-cleanup
- `--json` mode for CI

### Preflight (`scripts/ops/preflight.py`)
- Route shadowing detection
- SDK build freshness
- Import cycle detection
- Config validation

### Postflight (`scripts/ops/postflight.py`)
- Test hygiene checks
- SDK parity verification
- Mypy category checks
- Metric registration patterns

### Dev Sync (`scripts/ops/dev_sync.sh`)
- Combines preflight + postflight
- Runs on session start
- Blocks on failures

---

## Test Reports Reference

| Report | Type | Date | Status |
|--------|------|------|--------|
| TR-001 | CLI Demo | 2025-12-16 | PASS |
| TR-002 | API Smoke | 2025-12-16 | PASS |
| TR-003 | MOAT Integration | 2025-12-16 | PASS (11/13) |
| TR-004 | Scenario Test Matrix | 2025-12-16 | PASS (11/13) |
| TR-005 | PIN-120 Suite | 2025-12-22 | PASS (1715/1715) |

---

## Cleanup Summary

### Phase 1: Unused Parameter Renames (PIN-121)

Renamed 15 unused parameters with `_` prefix across 12 files:

| File | Parameter(s) |
|------|-------------|
| `app/api/runtime.py` | `http_request` → `_http_request` |
| `app/costsim/leader.py` | `exc_val, exc_tb` → `_exc_val, _exc_tb` |
| `app/routing/learning.py` | `current_agent` → `_current_agent` |
| `app/routing/probes.py` | `service_name` → `_service_name` |
| `app/tasks/m10_metrics_collector.py` | `frame` → `_frame` |
| `app/tasks/recovery_queue_stream.py` | `archive_batch_size` → `_archive_batch_size` |
| `app/worker/outbox_processor.py` | `signum, frame` → `_signum, _frame` |
| `app/worker/pool.py` | `frame` → `_frame` |
| `app/worker/recovery_claim_worker.py` | `frame` → `_frame` |
| `app/workers/business_builder/stages/copy.py` | `positioning, tone_guidelines` → `_positioning, _tone_guidelines` |
| `app/workers/business_builder/stages/strategy.py` | `market_report` → `_market_report` |
| `app/workflow/external_guard.py` | `exc_val, exc_tb` → `_exc_val, _exc_tb` |

### Phase 2: API Normalization (PIN-121)

Added typed response models to `app/api/ops.py`:

```python
class OpsEvent(BaseModel):
    event_id: str
    timestamp: Optional[datetime] = None
    event_type: str
    # ... 9 more fields

class OpsEventListResponse(BaseModel):
    events: List[OpsEvent]
    total: int
    window_hours: int

class OpsJobResult(BaseModel):
    status: Literal["completed", "error"]
    message: str
    affected_count: Optional[int] = None
    job_type: Literal["detect-silent-churn", "compute-stickiness"]
```

---

## Current Metrics

| Metric | Value | Target |
|--------|-------|--------|
| Tests Passing | 1715+ | 100% |
| Route Contract Tests | 26 | 26 |
| Ops Endpoints Typed | 8/13 | 13/13 |
| Mypy Errors | 572 | <200 |
| Skills Registered | 10 | 10+ |
| Prevention Mechanisms | 23 | 23+ |

---

## Next Steps

1. **Type remaining ops endpoints** - Add response_model to 5 untyped endpoints
2. **Reduce mypy errors** - Target <200 from 572 baseline
3. **Add coverage reporting** - Track test coverage trends
4. **UI hygiene tests** - Strict TypeScript, golden screen snapshots
5. **Registry negative test** - Add test proving missing `execute()` fails validation (guardrail proof)

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-22 | Created PIN-126 with Prevention Blueprint implementation |
| 2025-12-22 | Added pyright to CI (non-blocking) |
| 2025-12-22 | Added 3 route sanity tests |
| 2025-12-22 | Added 4 registry integrity tests |
| 2025-12-22 | Added 3 OpenAPI contract snapshot tests |
| 2025-12-22 | Created ops_api_contracts.json baseline snapshot |
