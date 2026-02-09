# PIN-537: Knowledge Planes Phase 4 — Retrieval Uses Persisted Planes + DB Evidence

**Date:** 2026-02-08  
**Category:** HOC Governance / Retrieval Durability  
**Status:** ✅ COMPLETE (Phase 4 wiring + proofs)  

---

## What Changed

Phase 4 removes the remaining in-memory “planes/evidence” registries from retrieval and wires the retrieval mediator for durable plane resolution and evidence emission.

### RetrievalMediator Default Wiring

- `backend/app/hoc/cus/hoc_spine/services/retrieval_mediator.py`
  - Default singleton now wires:
    - `DbKnowledgePlaneConnectorRegistry` (SSOT-backed plane resolution)
    - `DbRetrievalEvidenceService` (DB evidence writer)
  - Evidence record contract updated to include `action`, `requested_at`, `completed_at`, `duration_ms`.

### DB-Backed Connector Resolution

- `backend/app/hoc/cus/hoc_spine/services/knowledge_plane_connector_registry_engine.py`
  - Resolves `(tenant_id, plane_id)` via `knowledge_plane_registry`.
  - Only returns a connector binding for lifecycle `ACTIVE` planes.
  - Uses a placeholder connector implementation until real connector runtime factories exist.

### DB-Backed Evidence Persistence

- `backend/app/hoc/cus/hoc_spine/services/retrieval_evidence_engine.py`
  - Persists retrieval evidence via `RetrievalEvidenceDriver.append()` (append-only).
  - Writes a single immutable row containing `requested_at/completed_at/duration_ms`.

### RetrievalFacade: No In-Memory Stores

- `backend/app/hoc/cus/hoc_spine/services/retrieval_facade.py`
  - Removed in-memory `_planes`/`_evidence`.
  - Plane/evidence list/get/register/record now use Postgres drivers + L4 session context.

---

## Why This Exists

This closes the Phase 4 contract in the plan:
- “Plane registry” and “evidence” must be durable and restart-safe.
- Retrieval must resolve only governed planes and enforce lifecycle `ACTIVE` before connector execution.
- Retrieval evidence must be provable via Postgres, not process memory.

---

## Mechanical Proof (Post-Change)

- `cd backend && PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci`:
  - `0 blocking violations`
- `cd backend && PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py --ci`:
  - `CLEAN`
- `cd backend && PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py`:
  - `CLEAN`
- `cd backend && PYTHONPATH=. pytest tests/hoc_spine/test_hoc_spine_import_guard.py -q`:
  - `3 passed`
- `cd backend && PYTHONPATH=. pytest tests/governance/t4 -q`:
  - `429 passed`
- `cd backend && PYTHONPATH=. pytest tests/governance/t0 -q`:
  - `607 passed, 18 xfailed, 1 xpassed`

---

## What’s Still Missing (Next Phase)

- Implement a real `PolicyChecker` that enforces deny-by-default based on policy snapshots.
- Implement real connector runtime factories for `(connector_type, connector_id)` (Phase 4 resolves bindings only).
- Phase 5: remove/demote remaining legacy plane registries once importers are zero.
---

## Updates

### Update (2026-02-09)

- Added idempotent DB bootstrapper `backend/scripts/ops/bootstrap_knowledge_governance_tables.py` to ensure `knowledge_plane_registry`, `retrieval_evidence`, `policy_snapshots`, and required tenant/run rows for governance tests.
- Fixed L4 handler config mutation persistence (JSONB copy) in `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/knowledge_planes_handler.py`.
- Fixed evidence writer to work inside SAVEPOINT-based tests in `backend/app/hoc/cus/hoc_spine/services/retrieval_evidence_engine.py`.
- Fixed asyncpg naive/aware timestamp mismatch in `backend/app/db.py` and `backend/app/hoc/int/agent/drivers/db.py`.
- Updated governance E2E to use `env://DEV_DATABASE_URL` via `backend/tests/conftest.py`.
- Reality check: `tests/governance/t0` = `609 passed, 18 xfailed, 1 xpassed`; `tests/governance/t4` = `243 passed`.

### How to run on dev/staging DB

```bash
cd backend
PYTHONPATH=. DATABASE_URL='postgresql://…' python3 scripts/ops/bootstrap_knowledge_governance_tables.py
PYTHONPATH=. DATABASE_URL='postgresql://…' pytest tests/governance/t0 -q
PYTHONPATH=. DATABASE_URL='postgresql://…' pytest tests/governance/t4 -q
```
