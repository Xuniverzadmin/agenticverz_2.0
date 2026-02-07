# Phase 5 Master Plan — HOC Surfacing via L2.1 (Facade) + Veil Controls

**Date:** 2026-02-07  
**Status:** DRAFT (execution plan; evidence-driven)  
**Scope:** `backend/app/**` (HOC API surfacing + hoc_spine authority)

---

## North Star

1. **L2.1 exists** as an explicit, canonical surface map for CUS domains (triage-first).
2. **main.py is not a router directory.** Entry points import exactly one HOC wiring module, not 76 routers.
3. **Veil controls live in hoc_spine authority** + entrypoint config, not in L2 routers.
4. URL surface remains stable:
   - `/api/v1/*` remains **legacy-only (410)**.
   - Canonical HOC routes remain unprefixed (e.g. `/activity/*`, `/policies/*`).
5. Canonical audiences under `backend/app/hoc/api/`: **CUS / INT / FDR only**. No additional audience roots.

---

## Binding References

- Topology: `docs/architecture/topology/HOC_LAYER_TOPOLOGY_V2.0.0.md`
- Layer rules: `docs/architecture/architecture_core/LAYER_MODEL.md`
- Driver/Engine: `docs/architecture/architecture_core/DRIVER_ENGINE_PATTERN_LOCKED.md`
- Coherence plan: `docs/COHERENCE_GLOBAL_PLAN.md`

---

## Problem Statement (Reality)

`backend/app/main.py` currently:
- Imports ~76 routers directly from `backend/app/hoc/api/**`.
- Calls `app.include_router(...)` dozens of times.

This makes triage harder (no single canonical domain surface map) and makes the entrypoint an attack-surface “directory listing”.

---

## Phase 5 Outcomes

### Outcome A — L2.1 Surface Map (Triage)

Create `L2.1` facades that represent the canonical 10 CUS domains as files:

`backend/app/hoc/api/facades/cus/{domain}.py`

Each facade:
- Imports **L2 routers only**
- Exports a `ROUTERS` list (and optionally stable metadata for tooling)
- Never imports hoc_spine / engines / drivers / db

### Outcome B — Entrypoint Severance

Create `backend/app/hoc/app.py`:
- A single HOC wiring entry for `main.py`
- Includes routers from L2.1 facades into a single `hoc_router`

Then `backend/app/main.py`:
- Stops importing individual HOC routers
- Imports `include_hoc(app)` (or `hoc_router`) once

### Outcome C — Veil Controls (Security Hygiene)

Implement veil controls in:
- `backend/app/hoc/cus/hoc_spine/authority/*` (policy)
- `backend/app/main.py` (FastAPI config)
- Existing middleware behavior (Auth + RBAC) consults hoc_spine authority

Veil controls are not “security”, they are **attack-surface hygiene**:
- Docs/OpenAPI gating in prod
- Optional “deny-as-404” posture for unauthorized paths (prod)
- Optional rate limiting for unauthenticated probes (prod)

---

## Always-On Gates (Run After Every Batch)

From repo root:

```bash
cd backend
PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci
PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py
PYTHONPATH=. pytest -q tests/hoc_spine/test_api_v1_legacy_only.py tests/hoc_spine/test_hoc_spine_import_guard.py
```

Route surface snapshot (must stay stable):

```bash
cd backend
PYTHONPATH=. python3 - <<'PY'
from __future__ import annotations
import importlib
from fastapi import FastAPI

mod = importlib.import_module("app.main")
app: FastAPI = mod.app
routes = [r for r in app.routes if hasattr(r, "path")]
print("total_routes", len(routes))
print("v1_routes", len([r for r in routes if r.path.startswith('/api/v1')]))
print("controls_routes", len([r for r in routes if r.path.startswith('/controls')]))
print("predictions_routes", len([r for r in routes if r.path.startswith('/predictions')]))
PY
```

---

## Execution (Streamed Batches)

### Batch 5.1 — L2.1 Design + Skeleton

- Create `backend/app/hoc/api/facades/cus/` directory.
- Add one facade file per canonical domain:
  - overview, activity, incidents, policies, controls, logs, analytics, integrations, api_keys, account
- Facades only export `ROUTERS` list.

### Batch 5.2 — HOC Wiring Module

- Create `backend/app/hoc/app.py`:
  - `include_hoc(app: FastAPI) -> None`
  - `hoc_router: APIRouter` (optional)
  - Uses facades to include routers in canonical order

### Batch 5.3 — Entrypoint Severance

- Update `backend/app/main.py`:
  - Remove all direct HOC router imports
  - Remove corresponding `app.include_router(...)` calls
  - Replace with one call: `include_hoc(app)`

### Batch 5.4 — Veil Controls

- Add hoc_spine authority policy: `veil_policy.py`
- Wire docs/openapi gating in `FastAPI(...)` initialization via veil policy
- Wire deny-as-404 + rate limiting in auth/RBAC middleware, controlled by veil policy

---

## Definition of Done (Phase 5)

- `backend/app/main.py` contains **0** direct imports from `backend/app/hoc/api/**`
- Canonical 10 CUS domains each have a facade file in `backend/app/hoc/api/facades/cus/`
- Veil policy is centralized in hoc_spine authority
- All gates pass and route snapshot is unchanged

## Follow-Up: Audience Cleansing (CUS Domain Purity)

Phase 5 severance establishes L2.1 + single entrypoint wiring. Next, cleanse audience/domain placement:
- Abolish any non-canonical audience roots under `backend/app/hoc/api/`.
- Ensure `backend/app/hoc/api/cus/` contains only the canonical 10 customer domains.

Canonical plan: `docs/architecture/hoc/HOC_AUDIENCE_CLEANSING_PLAN_V1.md`.
