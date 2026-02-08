# PIN-539: Knowledge Planes Phase 6 — Policy Snapshot Gate + SQL Connector Runtime

**Date:** 2026-02-08  
**Category:** HOC Governance / Retrieval Enablement  
**Status:** ✅ COMPLETE  

---

## What Changed

Phase 6 makes mediated retrieval runnable (still deny-by-default) by adding:
1. a DB-backed `PolicyChecker` that reads the run’s persisted policy snapshot, and
2. a real connector runtime factory for SQL gateway planes.

### 1) Policy Snapshot Gate (Deny-by-Default)

- `backend/app/hoc/cus/hoc_spine/services/retrieval_policy_checker_engine.py`
  - Looks up `Run.policy_snapshot_id` from `runs`.
  - Loads `policy_snapshots.thresholds_json`.
  - Enforces an explicit allowlist for governed plane access via one of:
    - `allowed_plane_ids`
    - `allowed_rag_sources`
    - `allowed_knowledge_planes`
    - `knowledge_access.allowed_planes`
  - Missing/empty allowlist => deny (contract invariant).

The RetrievalMediator singleton now injects this policy checker by default:
- `backend/app/hoc/cus/hoc_spine/services/retrieval_mediator.py`

### 2) SQL Connector Runtime (Plane Config -> SqlGatewayService)

- `backend/app/hoc/cus/hoc_spine/services/knowledge_plane_connector_registry_engine.py`
  - Resolves the governed plane record from `knowledge_plane_registry`.
  - Requires lifecycle `ACTIVE`.
  - Builds a `SqlGatewayService` when `connector_type in {"sql","sql_gateway"}` using governed plane `config`:
    - `connection_string_ref` (credential ref)
    - `templates` (template registry)
    - `allowed_templates` (optional)

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
