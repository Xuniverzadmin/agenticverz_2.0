# PIN-541: Knowledge Planes — Config Mutation Ops + Legacy SSOT Removal

**Date:** 2026-02-08  
**Category:** HOC Governance / Lifecycle Authority  
**Status:** ✅ COMPLETE  

---

## What Changed

### 1) Added Config Mutation Operations (Founder/Admin)

These ops mutate `knowledge_plane_registry.config` only (no lifecycle state change):

- `knowledge.planes.bind_policy`
- `knowledge.planes.unbind_policy`
- `knowledge.planes.approve_purge`

Code:
- `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/knowledge_planes_handler.py`
- `backend/app/hoc/cus/hoc_spine/drivers/knowledge_plane_registry_driver.py` (added `set_config()`)

Founder surface endpoints:
- `POST /retrieval/planes/{plane_id}/bind_policy`
- `POST /retrieval/planes/{plane_id}/unbind_policy`
- `POST /retrieval/planes/{plane_id}/approve_purge`

Code:
- `backend/app/hoc/api/fdr/ops/retrieval_admin.py`

Rationale:
- `knowledge.planes.transition` gates require persisted intent:
  - `→ ACTIVE` requires `config.bound_policy_ids`
  - `→ PURGED` requires `config.purge_approved == true`

### 2) Removed Legacy In-Memory Lifecycle SSOT

Deleted (split-brain lifecycle authority):
- `backend/app/hoc/cus/hoc_spine/orchestrator/lifecycle/knowledge_lifecycle_manager.py`
- `backend/app/hoc/cus/hoc_spine/orchestrator/lifecycle/knowledge_sdk.py`
- `backend/app/services/knowledge_sdk.py` (shim)

### 3) Blocked Non-Canonical Plane Creation Path

- `RetrievalFacade.register_plane()` now hard-errors to prevent bypassing L4 operations.

Code:
- `backend/app/hoc/cus/hoc_spine/services/retrieval_facade.py`

### 4) Testability Improvements (No Global Session Assumptions)

DB-backed hoc_spine components now accept `session_provider` injection (defaults to canonical `get_async_session_context`):
- `DbPolicySnapshotPolicyChecker`
- `DbKnowledgePlaneConnectorRegistry`
- `DbRetrievalEvidenceService`

Code:
- `backend/app/hoc/cus/hoc_spine/services/retrieval_policy_checker_engine.py`
- `backend/app/hoc/cus/hoc_spine/services/knowledge_plane_connector_registry_engine.py`
- `backend/app/hoc/cus/hoc_spine/services/retrieval_evidence_engine.py`

### 5) Alembic Preflight Fix (Revision IDs > 32)

Alembic version table preflight now ensures `alembic_version.version_num` is wide enough for descriptive revision IDs.

Code:
- `backend/alembic/env.py`

---

## Mechanical Proof (Post-Change)

- `cd backend && PYTHONPATH=. pytest tests/governance/t0 -q`:
  - `608 passed, 1 skipped, 18 xfailed, 1 xpassed`
- `cd backend && PYTHONPATH=. pytest tests/governance/t4 -q`:
  - `240 passed, 3 skipped`
- `cd backend && PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci`:
  - `0 blocking violations`
- `cd backend && PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py --ci`:
  - `CLEAN`
- `cd backend && PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py`:
  - `CLEAN`
- `cd backend && PYTHONPATH=. python3 scripts/ops/hoc_l5_l6_purity_audit.py`:
  - `0 blocking, 0 advisory`
- `cd backend && PYTHONPATH=. python3 scripts/ops/l5_spine_pairing_gap_detector.py`:
  - `69 wired, 0 orphaned, 0 direct`

