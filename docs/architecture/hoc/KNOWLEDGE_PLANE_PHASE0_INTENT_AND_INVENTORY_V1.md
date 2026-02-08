# Knowledge Planes — Phase 0 Intent + Inventory (V1)

**Status:** DRAFT (Phase 0 artifact)  
**Date:** 2026-02-08  
**Plan:** `docs/architecture/hoc/KNOWLEDGE_PLANE_LIFECYCLE_HARNESS_PLAN_V2.md`  

This document exists to make the existing engine blocks mechanically explicit before any consolidation, renaming, or migrations.

---

## 1) Engine Blocks (What They Are)

### 1.1 Tenant Lifecycle (Account Domain SSOT)

- **Purpose:** global tenant eligibility state (transitive gate for all capabilities).
- **SSOT:** `Tenant.status` (account domain).
- **Orchestration surface:** hoc_spine operations:
  - `account.lifecycle.query`
  - `account.lifecycle.transition`
- **Code:**
  - L5: `backend/app/hoc/cus/account/L5_engines/tenant_lifecycle_engine.py`
  - L6: `backend/app/hoc/cus/account/L6_drivers/tenant_lifecycle_driver.py`
  - L4 handler: `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/lifecycle_handler.py`
  - Audience boundary gate (INT): `backend/app/hoc/api/int/general/lifecycle_gate.py`

**Invariant:** knowledge plane operations MUST consult tenant lifecycle gating (block when forbidden).

---

### 1.2 Knowledge Plane Lifecycle (Governance Control-Plane)

- **Purpose:** governs whether a knowledge plane may be used (policy-gated lifecycle).
- **State machine:** `KnowledgePlaneLifecycleState` (GAP-089).
- **Authority:** hoc_spine lifecycle orchestration + policy gates + audit events.
- **Code:**
  - State machine: `backend/app/models/knowledge_lifecycle.py`
  - Orchestrator/manager: `backend/app/hoc/cus/hoc_spine/orchestrator/lifecycle/knowledge_lifecycle_manager.py`
  - SDK facade: `backend/app/hoc/cus/hoc_spine/orchestrator/lifecycle/knowledge_sdk.py`

**Invariant:** lifecycle is the sole authority for lifecycle state (especially `ACTIVE`).

---

### 1.3 Retrieval / Index Runtime (Data-Plane Execution Substrate)

- **Purpose:** operational substrate for indexing/query execution (nodes/embeddings/indexing readiness).
- **Non-authoritative:** runtime readiness statuses must not be confused with lifecycle states.
- **Code (current):**
  - Graph/index registry + statuses: `backend/app/hoc/cus/hoc_spine/orchestrator/lifecycle/drivers/knowledge_plane.py`

**Open decision:** retire or rename/separate as “index runtime” vs “governed plane”.

---

### 1.4 Mediated Retrieval (Access Choke Point + Evidence)

- **Purpose:** deny-by-default access mediation for external data retrieval.
- **Choke point:** `RetrievalMediator` checks policy, resolves connector, emits evidence.
- **Code:**
  - Mediator: `backend/app/hoc/cus/hoc_spine/services/retrieval_mediator.py`
  - Worker enforcement hook: `backend/app/hoc/int/general/engines/retrieval_hook.py`
  - Retrieval facade (currently also holds in-memory plane registry/evidence): `backend/app/hoc/cus/hoc_spine/services/retrieval_facade.py`

**Invariant:** mediated retrieval must accept only governed `plane_id` identifiers.

---

## 2) Persistence Reality (Already Exists vs Missing)

### 2.1 Retrieval Evidence Is Already a Real Table

- SQLModel: `backend/app/models/retrieval_evidence.py`
- Alembic migration + immutability trigger: `backend/alembic/versions/113_add_retrieval_evidence.py`

**Current mismatch:** runtime uses `RetrievalFacade._evidence` in-memory, and `RetrievalMediator` is not configured with a real EvidenceService by default.

### 2.2 Knowledge Plane Registry Is Not Persisted (Missing)

- `KnowledgeLifecycleManager` stores `self._planes` in-memory: `backend/app/hoc/cus/hoc_spine/orchestrator/lifecycle/knowledge_lifecycle_manager.py`
- Retrieval plane registry stores `self._planes` in-memory: `backend/app/hoc/cus/hoc_spine/services/retrieval_facade.py`

---

## 3) Surface Wiring Reality (Where the API Is Today)

- CUS router for retrieval access (CUS-only): `backend/app/hoc/api/cus/policies/retrieval.py`
  - Exposes `POST /retrieval/access` only.
- Founder-only retrieval administration router:
  - `backend/app/hoc/api/fdr/ops/retrieval_admin.py`
  - Exposes plane list/register + evidence query behind `verify_fops_token`.
- Wiring:
  - CUS: included via `backend/app/hoc/api/facades/cus/policies.py`
  - FDR: included via `backend/app/hoc/api/facades/fdr/ops.py`
- Both routes currently import the L4 service facade directly (no `OperationRegistry` dispatch yet).

**Implication:** plane registration is currently possible without knowledge lifecycle authority.

---

## 4) Mechanical Violations (What Must Be Eliminated)

1. Multiple writers of “ACTIVE” across unrelated systems:
   - lifecycle `KnowledgePlaneLifecycleState.ACTIVE`
   - runtime `KnowledgePlaneStatus.ACTIVE`
   - retrieval facade `status="active"`
2. `plane_id` is not canonical (multiple generators + reuse as namespace):
   - lifecycle generates `kp_*`
   - retrieval facade generates UUIDs
   - job queue worker uses `plane_id=tenant_id` for idempotency
3. Failure semantics are split (`FAILED` vs `ERROR`) and do not propagate.

---

## 5) Phase 0 Outputs (Definition of Done)

1. This inventory is kept current.
2. A short contract doc is written:
   - canonical authority of lifecycle state,
   - ownership of `plane_id`,
   - runtime readiness as non-authoritative,
   - failure propagation rules,
   - tenant lifecycle as transitive gate.
3. A wiring map update is written (audience surfaces + operations).
