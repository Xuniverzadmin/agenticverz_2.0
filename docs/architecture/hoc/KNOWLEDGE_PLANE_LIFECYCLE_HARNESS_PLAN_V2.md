# Knowledge Plane Lifecycle + Retrieval Harness Plan (V2)

**Status:** DRAFT (for review)  
**Date:** 2026-02-08  
**Supersedes:** `docs/architecture/hoc/KNOWLEDGE_PLANE_LIFECYCLE_REFACTOR_PLAN_V1.md` (duplicate-shim focus only)  
**Scope:** Knowledge plane lifecycle + mediated retrieval plane registry/evidence (system runtime)  
**Non-scope:** Tenant/onboarding lifecycle harnessing (covered by `docs/architecture/hoc/DOMAIN_LIFECYCLE_HARNESS_REFACTOR_PLAN_V1.md`)  

---

## 0) Fixed Decisions (Recorded)

1. **Plane cardinality:** many planes per tenant, keyed by `(tenant_id, plane_type, plane_name)` (not “1 plane per tenant”).
2. **Exposure surface:** **internal system runtime component** (INT/founder only; not a public CUS surface).
3. **Transition authority:** hoc_spine authority gates transitions; do not delegate transition authority to CUS domain engines.

---

## 1) Current Reality (Audited)

### 1.1 There Are Multiple “Plane” Implementations (Split-Brain)

1. **Lifecycle state machine (pure):**
   - `backend/app/models/knowledge_lifecycle.py` (GAP-089) defines ordered states + valid transitions.

2. **Knowledge lifecycle orchestrator (in-memory):**
   - `backend/app/hoc/cus/hoc_spine/orchestrator/lifecycle/knowledge_lifecycle_manager.py`
   - Holds `_planes` + `_audit_log` in memory; uses `KnowledgePlane` dataclass (id, tenant_id, name, state, config…).

3. **Knowledge plane registry (in-memory “graph”):**
   - `backend/app/hoc/cus/hoc_spine/orchestrator/lifecycle/drivers/knowledge_plane.py`
   - Separate registry + `KnowledgePlaneRegistry` oriented around nodes/sources and “knowledge graph” semantics.

4. **Retrieval plane registry + evidence (in-memory):**
   - `backend/app/hoc/cus/hoc_spine/services/retrieval_facade.py`
   - Stores `_planes` and `_evidence` in memory “for demo”.

**Net:** the system has *multiple* plane registries with different meanings, all in-memory, and not unified under a single persisted contract.

### 1.2 Mediation Exists, But Plane Registration Is Not Canonical

- Retrieval is mediated via:
  - `backend/app/hoc/cus/hoc_spine/services/retrieval_mediator.py`
  - `backend/app/hoc/int/general/engines/retrieval_hook.py` (mandatory worker hook)
- The “planes” used by mediation are not persisted (in-memory in RetrievalFacade).

### 1.3 Surface Placement Conflict (Needs Resolution)

- There is a CUS router at `backend/app/hoc/api/cus/policies/retrieval.py` exposing plane list/register and evidence endpoints.
- This conflicts with the recorded decision: **knowledge lifecycle is an internal runtime component**.

---

## 2) First-Principles Target (What The System Should Be)

### 2.1 One Canonical Plane Contract

A “Knowledge Plane” is a **policy-governed knowledge access domain**, not a raw DB, and not a “prompt-side convenience”.

Invariants:
- **Deny-by-default** access (policy must explicitly allow a plane).
- The **runtime** resolves `plane → connector/retriever → store/API`; the LLM never chooses DBs.
- Every retrieval emits **evidence** with `plane_id`, `run_id`, `policy_snapshot_id`, `doc_ids`, and redaction-safe query hashes.

### 2.2 Separation Of Concerns (Template + Harness)

1. **hoc_spine owns the template + lifecycle authority:**
   - stage ordering
   - transition gating (authority)
   - audit/evidence requirements
   - operation surfaces (INT/founder)

2. **Domains “harness” the template by providing capabilities, not authority:**
   - integrations: connector registry + ingestion/index workers
   - policies: policy snapshot + knowledge access checker
   - logs: evidence persistence/query

Domains do **not** define their own plane lifecycle state machines.

### 2.3 Persistence Is Mandatory (No In-Memory SSOT)

The canonical plane registry and lifecycle state must be **persisted to Postgres** so:
- workers can restart without state loss
- audit timelines are durable
- policy enforcement can be proven after-the-fact

---

## 3) Canonical Data Model (V2 Proposal)

### 3.1 Identity

- `plane_id`: immutable primary key (`kp_<uuid>` or UUID)
- `tenant_id`: owner tenant
- `plane_type`: coarse type (`vector`, `sql`, `http`, `docs`, …)
- `plane_name`: human label (unique per tenant + type)

### 3.2 Plane State (Lifecycle)

- `lifecycle_state`: `KnowledgePlaneLifecycleState` (GAP-089)
- `config`: JSON blob (connector binding, indexing config, sensitivity, tags)
- `created_at`, `updated_at`, `created_by`

### 3.3 Evidence

- Retrieval evidence persisted (append-only):
  - `evidence_id`, `tenant_id`, `run_id`, `plane_id`, `connector_id`, `query_hash`, `doc_ids`, `token_count`, `policy_snapshot_id`, `timestamp`

---

## 4) Refactor Plan (Phases)

### Phase 0 — Contract Freeze + Surface Audit

1. Inventory all plane-related call paths:
   - lifecycle (knowledge_lifecycle_manager / knowledge_sdk)
   - mediation (retrieval_mediator / retrieval_hook / retrieval_facade)
2. Decide which “plane” meaning is canonical:
   - **access plane** (mediation) is canonical for governance/RAG
   - **graph plane** (`lifecycle/drivers/knowledge_plane.py`) is either:
     - retired, or
     - renamed and explicitly separated as “knowledge graph” (not access plane)
3. Re-home the L2 router surface:
   - move plane registration/listing out of `hoc/api/cus/` into **INT/founder** surface,
   - keep `retrieval/access` as the external retrieval choke point only if intended.

**Exit criteria:** written decision on plane meaning + updated routing map.

### Phase 1 — Template Contracts In hoc_spine (Harnessable)

1. Add hoc_spine schemas/protocols for:
   - `KnowledgePlaneKey` (tenant_id, plane_type, plane_name)
   - `KnowledgePlaneRecord` (persisted facts)
   - `KnowledgePlaneTransitionIntent` + `TransitionOutcome`
2. Define ports to be implemented/injected:
   - `KnowledgePlaneStorePort` (read/write plane records)
   - `KnowledgeEvidenceStorePort` (append evidence)
   - `KnowledgePolicyGatePort` (deny-by-default access checks)
   - `KnowledgeConnectorRegistryPort` (resolve connector for plane)

**Exit criteria:** hoc_spine template compiles with Protocol-only dependencies.

### Phase 2 — Persistence + Alembic Migration

1. Add Postgres tables for planes + events/evidence (or adapt existing tables if present).
2. Implement L6 drivers (no commit/rollback):
   - `hoc_spine/drivers/knowledge_plane_driver.py`
   - `hoc_spine/drivers/retrieval_evidence_driver.py`
3. Provide a migration to backfill any existing in-memory usage expectations (minimal seed).

**Exit criteria:** planes and evidence durable; drivers covered by t4/governance tests.

### Phase 3 — L4 Operations (INT Runtime Surface)

1. Create L4 handler(s) that register operations such as:
   - `knowledge.planes.register`
   - `knowledge.planes.transition`
   - `knowledge.planes.get`
   - `knowledge.planes.list`
   - `knowledge.evidence.list` / `knowledge.evidence.get`
2. Enforce:
   - hoc_spine authority gate on transitions (protected actions)
   - transaction boundaries owned by orchestrator context

**Exit criteria:** no direct “manager singleton” usage from routes/workers.

### Phase 4 — Unify Retrieval With Persisted Planes

1. Rewrite `RetrievalFacade` to use persisted plane registry (driver/port), not in-memory `_planes`.
2. Enforce plane lifecycle state in retrieval:
   - only `ACTIVE` planes can be accessed.
3. Persist evidence (no in-memory `_evidence`).

**Exit criteria:** retrieval path is durable + provable.

### Phase 5 — Delete Duplicates / Shims

1. Remove `app.services.knowledge.*` plane registry if unused after repointing.
2. Remove or demote legacy plane registries once importers are zero.

**Exit criteria:** one canonical plane SSOT; no duplicate managers.

---

## 5) Domain Harness Candidates (Non-Blind Adoption)

| Domain | Harness Role | What It Should Provide | What It Must Not Own |
|--------|--------------|------------------------|----------------------|
| integrations | capability provider | connectors, ingestion/index jobs, health checks | plane lifecycle authority |
| policies | gate provider | deny-by-default plane access policy checks | connector resolution |
| logs | evidence provider | evidence persistence + export | policy decisions |
| hoc_spine | template owner | lifecycle, operations, authority, orchestration | domain-specific connector business logic |

---

## 6) Mechanical Verification (Must Stay Green)

- `PYTHONPATH=. pytest backend/tests/governance/t4 -q`
- `PYTHONPATH=. pytest backend/tests/governance/t0 -q`
- `PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci`
- `PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py --ci`
- `PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py`
- `PYTHONPATH=. python3 backend/scripts/ops/hoc_l5_l6_purity_audit.py --json --advisory`

