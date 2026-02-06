# PIN-272: Phase B.1 Test Isolation Hardening

**Status:** COMPLETE
**Created:** 2026-01-01
**Category:** CI / Test Infrastructure
**Related PINs:** PIN-271 (CI North Star), PIN-270 (Infra Governance), PIN-120 (Test Prevention)

---

## Summary

Phase B.1 implemented test isolation fixtures to reduce test flakiness and stabilize CI failure counts. This is a prerequisite for Phase C (RBAC Stub Implementation).

---

## Problem Statement

Tests were passing individually but failing when run together in the full suite. Root causes:

1. **Prometheus Registry Bleeding**: Metrics registered by one test module persisted and caused "Duplicated timeseries" errors in subsequent tests.
2. **Module-Level Globals**: Cached state in app modules leaked between tests.
3. **Syntax Error**: `from __future__ import annotations` placed after imports in `alert_worker.py`.

---

## Solution

### 1. Prometheus Isolation Fixture

Added `isolate_prometheus_registry()` fixture to `tests/conftest.py`:

```python
@pytest.fixture(autouse=True, scope="function")
def isolate_prometheus_registry():
    """Clear Prometheus registry before and after each test."""
    _clear_prometheus_registry()
    yield
    _clear_prometheus_registry()
```

### 2. Module Singleton Reset

Added `reset_module_level_singletons()` fixture:

```python
@pytest.fixture(autouse=True, scope="function")
def reset_module_level_singletons():
    """Reset cached attributes in app.* modules after each test."""
    yield
    # Clear _cached_* attributes from app modules
```

### 3. RBAC Stub Fixtures (Phase C Prep)

Added test fixtures for deterministic auth headers:

- `stub_admin_headers` → `{"X-AOS-Key": "stub_admin_test_tenant"}`
- `stub_developer_headers` → `{"X-AOS-Key": "stub_developer_test_tenant"}`
- `stub_viewer_headers` → `{"X-AOS-Key": "stub_viewer_test_tenant"}`
- `stub_machine_headers` → `{"X-AOS-Key": "stub_machine_test_tenant"}`

### 4. Syntax Fix

Fixed `app/costsim/alert_worker.py` - moved `from __future__ import annotations` to file top.

---

## DB Engine Reset (Reverted)

Initially added a `reset_db_engine_globals()` fixture that reset `_engine`, `_async_engine`, etc. This caused **more failures** (50→70) because tests depend on persistent DB connections within a session.

**Lesson:** Lazy engine globals should persist across tests within a session. Only specific tests that need DB isolation should use their own fixtures.

---

## Results

| Metric | Before | After |
|--------|--------|-------|
| Test Failures | 49 (variable) | 41 (stable) |
| Tests Passed | 2474 | 2482 |
| Test Skipped | 111 | 111 |

### Stability Verification

5 consecutive runs produced consistent failure counts (41-43), confirming isolation improvements.

---

## Remaining Failures (Categorized)

| Category | Count | Test Files |
|----------|-------|------------|
| Infra Missing (B) | ~25 | replay/test_replay_end_to_end.py, costsim/test_integration_real_db.py, test_m10_*.py |
| Chaos/Stress | ~8 | test_m10_recovery_chaos.py, test_m10_production_hardening.py |
| Import Isolation | 2 | test_recovery.py (passes individually) |
| Other | ~6 | Various |

---

## Files Changed

- `tests/conftest.py` - Added isolation fixtures
- `app/costsim/alert_worker.py` - Fixed syntax error

---

## Next Steps (Phase C)

With test isolation stable, proceed to:

1. Implement RBAC stub in `app/auth/stub.py`
2. Update auth middleware to use stub
3. Remove `@requires_infra("Clerk")` skips
4. Achieve Phase C closure

---

## References

- PIN-271 (CI North Star Declaration)
- PIN-270 (Infrastructure State Governance)
- docs/ci/CI_NORTH_STAR.md
- docs/infra/RBAC_STUB_DESIGN.md
