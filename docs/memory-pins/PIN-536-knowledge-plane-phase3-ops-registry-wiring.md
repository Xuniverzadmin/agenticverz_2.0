# PIN-536: Knowledge Planes Phase 3 — L4 Operations + FDR Surface Rewire

**Date:** 2026-02-08  
**Category:** HOC Governance / Wiring  
**Status:** ✅ COMPLETE (Phase 3 wiring + proofs)  

---

## What Changed

Phase 3 removes the remaining “direct hoc_spine service calls” from the founder retrieval admin surface.

### L4 Operations Added

New handler registers knowledge-plane operations in the L4 `OperationRegistry`:
- `knowledge.planes.register`
- `knowledge.planes.get`
- `knowledge.planes.list`
- `knowledge.evidence.get`
- `knowledge.evidence.list`

Code:
- `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/knowledge_planes_handler.py`
- Registered in `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/__init__.py`

### FDR Surface Rewired

Founder endpoints now call L4 operations (no direct `RetrievalFacade` plane/evidence calls):
- `backend/app/hoc/api/fdr/ops/retrieval_admin.py`

Plane registry reads/writes now use the persisted SSOT table (`knowledge_plane_registry`) from Phase 2.

---

## Why This Exists

This enforces the HOC topology (L2 → L4 → L6) for system-runtime plane registry and evidence query:
- L2 surfaces are translation only.
- L4 is the single execution authority.
- L6 drivers perform DB IO without commit authority.

This prevents split-brain plane registries from leaking through audience surfaces.

---

## Mechanical Proof (Post-Change)

- `cd backend && alembic heads`:
  - `122_knowledge_plane_registry (head)`
- `cd backend && PYTHONPATH=. pytest tests/governance/t0 -q`:
  - `605 passed, 18 xfailed, 1 xpassed`
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

---

## What’s Still Missing (Next Phase)

Phase 4/5 in the plan is still required to fully eliminate split-brain:
- Replace in-memory retrieval plane registry/evidence in `RetrievalFacade` with the persisted SSOT + DB evidence.
- Replace `KnowledgeLifecycleManager._planes` in-memory with DB-backed store and wire failure propagation.
- Rename/demote the legacy index-runtime “knowledge_plane” runtime module and statuses.

