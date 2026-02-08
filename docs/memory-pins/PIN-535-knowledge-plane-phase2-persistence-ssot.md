# PIN-535: Knowledge Planes Phase 2 — Persisted SSOT (knowledge_plane_registry)

**Date:** 2026-02-08  
**Category:** HOC Governance / Durability  
**Status:** ✅ COMPLETE (Phase 2 persistence primitives landed)  

---

## What Changed

Phase 2 introduces a canonical persisted SSOT for governed knowledge planes:

- **Model:** `backend/app/models/knowledge_plane_registry.py`
- **Migration:** `backend/alembic/versions/122_knowledge_plane_registry.py`
- **L6 Drivers (no commit/rollback):**
  - `backend/app/hoc/cus/hoc_spine/drivers/knowledge_plane_registry_driver.py`
  - `backend/app/hoc/cus/hoc_spine/drivers/retrieval_evidence_driver.py`

This does **not** yet rewire the runtime off in-memory registries (that wiring is Phase 3/4 in the plan).

---

## Why This Exists

The codebase previously had:
- hoc_spine knowledge lifecycle state in-memory (`KnowledgeLifecycleManager._planes`)
- retrieval plane registry/evidence in-memory (`RetrievalFacade._planes/_evidence`)

Without persistence, workers can restart and lose state, and evidence cannot be proven after-the-fact.

`knowledge_plane_registry` provides durable identity + lifecycle state storage aligned with GAP-089 ordering (`lifecycle_state_value`).

---

## Alembic Repair (Mechanical)

Alembic revision graph was mechanically broken:
- `backend/alembic/versions/121_add_costsim_canary_reports.py` referenced a non-existent `down_revision`.

Fixed:
- `down_revision` now correctly points to `120_is_frozen_api_keys`.

---

## Related Non-Canonical Persistence

A legacy/index-runtime persistence track exists but is not SSOT for hoc_spine lifecycle today:
- `backend/alembic/versions/118_w2_knowledge_planes.py` (tables: `knowledge_planes`, `knowledge_sources`, ...)

This PIN does not classify those tables as canonical; it only records the canonical governed SSOT addition.

---

## Mechanical Proof (Post-Change)

- `cd backend && alembic heads`:
  - `122_knowledge_plane_registry (head)`
- `cd backend && PYTHONPATH=. pytest tests/governance/t0 -q`:
  - `604 passed, 18 xfailed, 1 xpassed`
- `cd backend && PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci`:
  - `0 blocking violations`
- `cd backend && PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py --ci`:
  - `CLEAN`
- `cd backend && PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py`:
  - `CLEAN`
- `cd backend && PYTHONPATH=. pytest tests/hoc_spine/test_hoc_spine_import_guard.py -q`:
  - `3 passed`
- `cd backend && PYTHONPATH=. python3 scripts/ops/hoc_l5_l6_purity_audit.py`:
  - `0 blocking, 0 advisory`

