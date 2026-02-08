# PIN-540: Knowledge Planes — Persisted Lifecycle Transitions (`knowledge.planes.transition`)

**Date:** 2026-02-08  
**Category:** HOC Governance / Lifecycle Authority  
**Status:** ✅ COMPLETE  

---

## What Changed

Added a persisted lifecycle transition operation for governed knowledge planes.

### New L4 Operation

- `knowledge.planes.transition`:
  - Validates GAP-089 transition matrix (no skipping).
  - Enforces tenant gate (`tenants.status == "active"`).
  - Persists lifecycle state to `knowledge_plane_registry.lifecycle_state_value`.
  - Applies minimal protected-transition invariants:
    - `→ ACTIVE` requires `config.bound_policy_ids` non-empty.
    - `→ PURGED` requires `config.purge_approved == True`.

Code:
- `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/knowledge_planes_handler.py`

### Founder Surface Endpoint

- `POST /retrieval/planes/{plane_id}/transition` (founder-only)
  - Dispatches to `knowledge.planes.transition` via `OperationRegistry`.
  - Also extends plane registration to accept `config` for runtime/gates.

Code:
- `backend/app/hoc/api/fdr/ops/retrieval_admin.py`

---

## Mechanical Proof (Post-Change)

- `cd backend && PYTHONPATH=. pytest tests/governance/t4 -q`:
  - `240 passed, 3 skipped`
- `cd backend && PYTHONPATH=. pytest tests/governance/t0 -q`:
  - `608 passed, 1 skipped, 18 xfailed, 1 xpassed`
- `cd backend && PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci`:
  - `0 blocking violations`
- `cd backend && PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py --ci`:
  - `CLEAN`
- `cd backend && PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py`:
  - `CLEAN`
