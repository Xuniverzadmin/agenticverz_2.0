# Known Exceptions Elimination — Evidence Report

**Date:** 2026-02-06
**Scope:** `check_init_hygiene.py --ci` known exceptions (14 → 0)
**Status:** COMPLETE

---

## Before

```
Known exceptions (14 — not blocking CI):
  [WARN] app/hoc/api/int/agent/__init__.py:13 — Relative import '.founder_auth' — module not found on disk
  [WARN] app/hoc/int/policies/engines/__init__.py:18 — Relative import '.m7_to_m28' — module not found on disk
  [WARN] app/hoc/int/activity/engines/__init__.py:10 — Relative import '.m10_metrics_collector' — module not found on disk
  [WARN] app/hoc/int/activity/engines/__init__.py:11 — Relative import '.memory_update' — module not found on disk
  [WARN] app/hoc/int/activity/engines/__init__.py:14 — Relative import '.recovery_queue_stream' — module not found on disk
  [WARN] app/hoc/int/account/engines/__init__.py:19 — Relative import '.authorization_choke' — module not found on disk
  [WARN] app/hoc/int/account/engines/__init__.py:31 — Relative import '.clerk_provider' — module not found on disk
  [WARN] app/hoc/int/account/engines/__init__.py:38 — Relative import '.jwt_auth' — module not found on disk
  [WARN] app/hoc/int/account/engines/__init__.py:45 — Relative import '.jwt_auth' — module not found on disk
  [WARN] app/hoc/int/account/engines/__init__.py:48 — Relative import '.oidc_provider' — module not found on disk
  [WARN] app/hoc/int/account/engines/__init__.py:58 — Relative import '.rbac' — module not found on disk
  [WARN] app/hoc/int/account/engines/__init__.py:68 — Relative import '.role_mapping' — module not found on disk
  [WARN] app/hoc/int/account/engines/__init__.py:83 — Relative import '.shadow_audit' — module not found on disk
  [WARN] app/hoc/int/general/drivers/step_enforcement.py:217 — Driver imports L5_engines ... — drivers must not reach up to L5 (PIN-513)
```

## After

```
All checks passed. 0 blocking violations (0 known exceptions)
```

---

## Fix 1: L6 Driver L5 Import Violation (1 exception)

**File:** `app/hoc/int/general/drivers/step_enforcement.py`

**Problem:** Line 217 lazily imported `get_prevention_engine` from
`app.hoc.cus.policies.L5_engines.prevention_engine` — a driver reaching up
to L5, violating PIN-513 layer purity.

**Fix:** Removed the lazy L5 import fallback. The function
`enforce_before_step_completion()` already accepts `prevention_engine` as an
optional parameter. If the caller does not inject one, the driver returns a
safe "engine not injected" result instead of trying to reach up to L5.

**Caller impact:** None. The callers (`app/worker/runner.py`,
`app/hoc/int/analytics/engines/runner.py`) import from the worker-layer copy
at `app/worker/enforcement/step_enforcement.py`, not from this HOC driver.

---

## Fix 2: Stale `__init__.py` Re-Exports (13 exceptions)

All 13 warnings were caused by `__init__.py` files re-exporting modules that
do not exist at the relative import path. The modules exist elsewhere in the
codebase (canonical locations listed below). No code imports from any of
these 4 packages — all were dead re-exports.

### 2A. `app/hoc/api/int/agent/__init__.py` (1 stale import)

| Stale Import | Canonical Location |
|--------------|--------------------|
| `.founder_auth` | `app/api/dependencies/founder_auth.py` |

**Action:** Removed import. Empty `__all__`.

### 2B. `app/hoc/int/policies/engines/__init__.py` (1 stale import)

| Stale Import | Canonical Location |
|--------------|--------------------|
| `.m7_to_m28` | `app/auth/mappings/m7_to_m28.py` |

**Action:** Removed import. Empty `__all__`.

### 2C. `app/hoc/int/activity/engines/__init__.py` (3 stale imports)

| Stale Import | Canonical Location |
|--------------|--------------------|
| `.m10_metrics_collector` | `app/hoc/int/platform/engines/m10_metrics_collector.py` |
| `.memory_update` | `app/tasks/memory_update.py` |
| `.recovery_queue_stream` | `app/hoc/int/policies/engines/recovery_queue_stream.py` |

**Action:** Removed all imports. Empty `__all__`.

### 2D. `app/hoc/int/account/engines/__init__.py` (8 stale imports)

| Stale Import | Canonical Location |
|--------------|--------------------|
| `.authorization_choke` | `app/auth/authorization_choke.py` |
| `.clerk_provider` | `app/auth/clerk_provider.py` |
| `.jwt_auth` (×2) | `app/auth/jwt_auth.py` |
| `.oidc_provider` | `app/auth/oidc_provider.py` |
| `.rbac` | `app/auth/rbac.py` |
| `.role_mapping` | `app/auth/role_mapping.py` |
| `.shadow_audit` | `app/auth/shadow_audit.py` |

**Action:** Removed all stale re-exports. Retained inline `verify_api_key()`
and `AOS_API_KEY` (defined in-file, not re-exports).

---

## Verification

```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci

# Output:
# All checks passed. 0 blocking violations (0 known exceptions)
```

---

## Summary

| Metric | Before | After |
|--------|--------|-------|
| Blocking violations | 0 | 0 |
| Known exceptions | 14 | 0 |
| Files modified | — | 5 |
