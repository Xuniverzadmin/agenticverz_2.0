# TODO — Iteration 3.5 (Reality Snapshot)

**Date:** 2026-02-06
**Scope:** `backend/app/hoc/**`, `backend/app/worker/**`, `backend/app/startup/**`
**Goal:** Sever runtime-path imports of legacy `app.services.*` (no assumptions; evidence via scans/tests).

---

## What Is True Right Now (Evidence-Backed)

### A) No legacy `app.services.*` imports in HOC runtime paths (PASS)

**Evidence scan (Python files only; excludes docs):**
- Command: `rg -n --type py --glob '!**/docs/**' "^from app\\.services\\b|^import app\\.services\\b" backend/app/hoc backend/app/worker backend/app/startup`
- Result: **0 matches**

**CI check (Check 32):** `LEGACY_SERVICES_IMPORT`
- Source: `backend/scripts/ci/check_init_hygiene.py` → `check_no_legacy_services_imports(...)`
- Result: **0 violations** (confirmed in latest full run; see “Blocking Reality” below)

### B) hoc_spine import guard tests (PASS when run from `backend/`)

- Command: `cd backend && python3 -m pytest -q tests/hoc_spine/test_no_legacy_services.py tests/hoc_spine/test_hoc_spine_import_guard.py`
- Result: **5 passed**

**Important:** `backend/tests/hoc_spine/test_hoc_spine_import_guard.py` currently walks packages using a CWD-relative path (`app/hoc/cus/hoc_spine`). Running from repo root can yield `0` scanned modules.

---

## Blocking Reality (Full Hygiene Run)

Running the full hygiene gate still fails:

- Command: `cd backend && python3 scripts/ci/check_init_hygiene.py`
- Result: `Blocking: 26 violations` (current)

**Iter3.5-specific blockers are now resolved:**

1. `L2_BYPASS_L4` (RESOLVED)
   - Previous: `backend/app/hoc/api/cus/logs/tenants.py` imported `app.hoc.cus.account.L5_engines.tenant_engine`
   - Current: `backend/app/hoc/api/cus/logs/tenants.py` routes tenant operations via `registry.execute("account.tenant", OperationContext(...))`
   - Evidence: latest hygiene output contains **no** `L2_BYPASS_L4` category, and file header shows `get_operation_registry` usage.

2. `LEGACY_SERVICES_NEW_FILE` (RESOLVED)
   - Previous: `backend/app/services/_audit_shim.py` existed and was not allowlisted
   - Current: `backend/app/services/_audit_shim.py` is **absent**
   - Evidence: hygiene output contains **no** `LEGACY_SERVICES_NEW_FILE` category; `_audit_shim.py` references remain only in docs.

---

## TODO (Next Fixes)

**No remaining Iter3.5-scoped TODOs.**

Next work is Iter3.6: global severance of `app.services.*` imports across the rest of `backend/app/**` (outside the Iter3.5 runtime-path scope).
