# TODO — Iteration 3.6 (Global Severance of Legacy `app.services/**`)

**Date:** 2026-02-06
**Purpose:** Enforce “one system” by severing all runtime imports of legacy `app.services.*` outside `backend/app/services/**`.
**Rule:** No assumptions. Changes must be accepted by evidence scans and CI guards.

---

## First Principles (Definition)

- Legacy package: `backend/app/services/**`
- Target invariant: **No file under `backend/app/**` may import `app.services.*`** unless it is itself within `backend/app/services/**`.
- Also disallow legacy-relative imports that resolve into `backend/app/services/**` (e.g., `from ..services.tenant_service import ...` from `backend/app/api/**`).

---

## Current Reality (Evidence-Backed Baseline)

### A) Absolute legacy imports outside `app/services/**` (FAIL)

- Scope: `backend/app/**` excluding `backend/app/services/**`
- Count: **28 import hits across 19 files**

**Files with absolute `from app.services` / `import app.services` imports:**
- `backend/app/adapters/customer_activity_adapter.py`
- `backend/app/adapters/customer_incidents_adapter.py`
- `backend/app/adapters/customer_keys_adapter.py`
- `backend/app/adapters/customer_killswitch_adapter.py`
- `backend/app/adapters/customer_logs_adapter.py`
- `backend/app/adapters/customer_policies_adapter.py`
- `backend/app/adapters/founder_contract_review_adapter.py`
- `backend/app/adapters/founder_ops_adapter.py`
- `backend/app/adapters/platform_eligibility_adapter.py`
- `backend/app/costsim/v2_adapter.py`
- `backend/app/domain/failure_intelligence.py`
- `backend/app/integrations/cost_bridges.py`
- `backend/app/jobs/failure_classification_engine.py`
- `backend/app/main.py`
- `backend/app/quarantine/founder_review.py`
- `backend/app/quarantine/founder_review_adapter.py`
- `backend/app/skills/adapters/openai_adapter.py`
- `backend/app/skills/adapters/tenant_config.py`
- `backend/app/workers/business_builder/worker.py`

### B) Legacy-relative imports in `backend/app/api/**` (FAIL)

- Scope: `backend/app/api/**`
- Count: **3 import sites across 2 files**

**Files:**
- `backend/app/api/tenants.py` (`from ..services.tenant_service ...`, `from ..services.worker_registry_service ...`)
- `backend/app/api/policy_proposals.py` (`from ..services.policy_proposal import review_policy_proposal`)

---

## Acceptance Criteria

1. `rg -n --type py --glob '!backend/app/services/**' "^from app\\.services\\b|^import app\\.services\\b" backend/app` → **0 matches**
2. `rg -n --type py "^from \\.\\.services\\b|^import \\.\\.services\\b" backend/app/api` → **0 matches**
3. `cd backend && python3 scripts/ci/check_init_hygiene.py --ci` passes `LEGACY_SERVICES_IMPORT` (already scoped to hoc/worker/startup; keep it green while iterating)
4. `cd backend && python3 -m pytest -q tests/hoc_spine/test_no_legacy_services.py tests/hoc_spine/test_hoc_spine_import_guard.py` → **pass**

---

## Plan (Order Matters)

1. Convert `backend/app/main.py` away from `app.services.*` imports.
2. Convert `backend/app/api/**` legacy modules to HOC canonical routers (or hard fail if no HOC equivalent exists).
3. Convert `backend/app/adapters/**` legacy adapters to HOC equivalents or re-home into `backend/app/hoc/**` (keep layer headers accurate).
4. Convert remaining non-HOC runtime modules (`backend/app/integrations/**`, `backend/app/domain/**`, `backend/app/jobs/**`, `backend/app/quarantine/**`, `backend/app/skills/**`, `backend/app/workers/**`).
5. Add/extend a CI guard that blocks any future `app.services.*` imports outside `backend/app/services/**`.

---

## Evidence Commands (Copy/Paste)

```bash
cd /root/agenticverz2.0

# 1) Absolute legacy imports outside app/services
rg -n --type py --glob '!backend/app/services/**' '^from app\.services\b|^import app\.services\b' backend/app

# 2) Legacy-relative imports inside app/api
rg -n --type py '^from \.\.services\b|^import \.\.services\b' backend/app/api

# 3) Smoke gates
cd backend
python3 scripts/ci/check_init_hygiene.py
python3 -m pytest -q tests/hoc_spine/test_no_legacy_services.py tests/hoc_spine/test_hoc_spine_import_guard.py
```

