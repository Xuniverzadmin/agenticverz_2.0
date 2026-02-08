# PIN-534: Knowledge Planes Phase 0 — Audience Scoping (CUS vs FDR)

**Date:** 2026-02-08  
**Category:** HOC Governance / Surface Contracts  
**Status:** ✅ COMPLETE (Phase 0 wiring + proofs)  

---

## What Changed

Phase 0 of the knowledge plane lifecycle + retrieval harness plan is now **mechanically enforced at the API surface**:

- **CUS surface** exposes only mediated retrieval access:
  - `POST /retrieval/access` in `backend/app/hoc/api/cus/policies/retrieval.py`
- **Founder-only surface** exposes plane registry and evidence query:
  - `GET/POST /retrieval/planes`, `GET /retrieval/planes/{plane_id}`
  - `GET /retrieval/evidence`, `GET /retrieval/evidence/{evidence_id}`
  - Implemented in `backend/app/hoc/api/fdr/ops/retrieval_admin.py` and guarded by `verify_fops_token`
  - Requires explicit `tenant_id` (query param or request body) because founders are not tenant-scoped

This prevents customer callers from enumerating/registering planes or querying evidence directly, while keeping the mediated access choke point productized.

---

## Why This Exists

Knowledge plane registry + evidence are governance/ops responsibilities. If they are reachable from CUS surfaces, policy bypass and ontology drift become mechanically possible.

This PIN records the Phase 0 “surface separation” step so future refactors (Phase 1+) don’t accidentally re-expose these endpoints.

---

## Relationship to Tenant Lifecycle

Tenant lifecycle is a **separate SSOT** (account domain; `Tenant.status`) and remains authoritative for tenant eligibility.

Knowledge plane lifecycle does **not** replace tenant lifecycle. Instead, tenant lifecycle remains a **transitive prerequisite gate** for knowledge plane operations (register/transition/access/evidence), per:

- `docs/architecture/hoc/KNOWLEDGE_PLANE_CONTRACTS_V1.md`
- `docs/architecture/hoc/KNOWLEDGE_PLANE_LIFECYCLE_HARNESS_PLAN_V2.md`

---

## Mechanical Proof (Post-Change)

All proof gates remain green after the router split:

- `cd backend && PYTHONPATH=. pytest tests/governance/t0 -q`:
  - `601 passed, 18 xfailed, 1 xpassed`
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
- `cd backend && PYTHONPATH=. python3 scripts/ops/l5_spine_pairing_gap_detector.py`:
  - `69 wired, 0 orphaned, 0 direct`

---

## Canonical Plan Artifacts

- Plan: `docs/architecture/hoc/KNOWLEDGE_PLANE_LIFECYCLE_HARNESS_PLAN_V2.md`
- Contracts: `docs/architecture/hoc/KNOWLEDGE_PLANE_CONTRACTS_V1.md`
- Phase 0 intent + inventory: `docs/architecture/hoc/KNOWLEDGE_PLANE_PHASE0_INTENT_AND_INVENTORY_V1.md`

