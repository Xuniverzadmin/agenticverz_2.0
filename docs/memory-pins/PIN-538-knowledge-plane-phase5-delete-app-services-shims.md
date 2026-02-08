# PIN-538: Knowledge Planes Phase 5 — Delete Legacy `app.services.*` Shims

**Date:** 2026-02-08  
**Category:** HOC Governance / Canonicalization  
**Status:** ✅ COMPLETE  

---

## What Changed

Phase 5 deletes the legacy `backend/app/services/*` knowledge and retrieval shims now that HOC hoc_spine is the canonical runtime surface.

Deleted legacy modules:
- `backend/app/services/mediation/__init__.py`
- `backend/app/services/mediation/retrieval_mediator.py`
- `backend/app/services/retrieval/facade.py`
- `backend/app/services/knowledge/__init__.py`
- `backend/app/services/knowledge/knowledge_plane.py`
- `backend/app/services/knowledge_lifecycle_manager.py`

Updated tests to import canonical HOC equivalents:
- `backend/tests/governance/t0/test_retrieval_mediator.py` now imports `app.hoc.cus.hoc_spine.services.retrieval_mediator`
- `backend/tests/governance/t2/test_knowledge_plane.py` now imports `app.hoc.cus.hoc_spine.orchestrator.lifecycle.drivers.knowledge_plane`
- `backend/tests/governance/t3/test_knowledge_domain.py` now imports `app.hoc.cus.hoc_spine.orchestrator.lifecycle.drivers.knowledge_plane`

---

## Why This Exists

The legacy `app.services.*` layer created duplicate “plane” and “retrieval” implementations that were not part of the HOC topology. Keeping them around makes contracts ambiguous and encourages bypass patterns.

Phase 5 enforces the rule:
> `backend/app/hoc/**` is canonical runtime; legacy shims are deleted once no longer imported.

---

## Mechanical Proof (Post-Change)

- `cd backend && PYTHONPATH=. pytest tests/governance/t0 -q`:
  - `607 passed, 18 xfailed, 1 xpassed`
- `cd backend && PYTHONPATH=. pytest tests/governance/t4 -q`:
  - `429 passed`
- `cd backend && PYTHONPATH=. pytest tests/governance/t2/test_knowledge_plane.py -q`:
  - `29 passed`
- `cd backend && PYTHONPATH=. pytest tests/governance/t3/test_knowledge_domain.py -q`:
  - `76 passed`
- `cd backend && PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci`:
  - `0 blocking violations`
- `cd backend && PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py --ci`:
  - `CLEAN`
- `cd backend && PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py`:
  - `CLEAN`

