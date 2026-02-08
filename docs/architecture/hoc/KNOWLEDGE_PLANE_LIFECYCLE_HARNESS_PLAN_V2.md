# Knowledge Plane Lifecycle + Retrieval Harness Plan (V2)

**Status:** DRAFT (for review)  
**Date:** 2026-02-08  
**Supersedes:** `docs/architecture/hoc/KNOWLEDGE_PLANE_LIFECYCLE_REFACTOR_PLAN_V1.md` (duplicate-shim focus only)  
**Scope:** Knowledge plane lifecycle + mediated retrieval plane registry/evidence (system runtime)  
**Non-scope:** Tenant/onboarding lifecycle harnessing (covered by `docs/architecture/hoc/DOMAIN_LIFECYCLE_HARNESS_REFACTOR_PLAN_V1.md`)  

---

## 0) Fixed Decisions (Recorded)

1. **Plane cardinality:** many planes per tenant, keyed by `(tenant_id, plane_type, plane_name)` (not “1 plane per tenant”).
2. **Exposure surface:** hoc_spine is **system runtime** for customer-domain components (policies, account, integrations, logs). Audience surfaces (**CUS / INT / FDR**) are separate and must be wired intentionally; do not assume “internal-only” or “customer-only” for knowledge plane operations.
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

### 1.3 Audience Scoping Is Not Explicit (Needs Resolution)

- Plane management and evidence query surfaces must be explicitly scoped to an audience runtime (CUS/INT/FDR).
- Phase 0 wiring change (2026-02-08):
  - CUS retrieval surface now exposes **only** `POST /retrieval/access` in `backend/app/hoc/api/cus/policies/retrieval.py`.
  - Plane registry + evidence query are founder-only endpoints guarded by `verify_fops_token` in `backend/app/hoc/api/fdr/ops/retrieval_admin.py`.

### 1.4 Phase 0 Artifacts (This Workstream)

- Intent + inventory: `docs/architecture/hoc/KNOWLEDGE_PLANE_PHASE0_INTENT_AND_INVENTORY_V1.md`
- Contracts (freeze): `docs/architecture/hoc/KNOWLEDGE_PLANE_CONTRACTS_V1.md`

---

## 2) First-Principles Target (What The System Should Be)

### 2.1 One Canonical Plane Contract

A “Knowledge Plane” is a **policy-governed knowledge access domain**, not a raw DB, and not a “prompt-side convenience”.

Invariants:
- **Deny-by-default** access (policy must explicitly allow a plane).
- The **runtime** resolves `plane → connector/retriever → store/API`; the LLM never chooses DBs.
- Every retrieval emits **evidence** with `plane_id`, `run_id`, `policy_snapshot_id`, `doc_ids`, and redaction-safe query hashes.

### 2.1a Tenant Lifecycle (Transitive Gate, Separate SSOT)

Tenant lifecycle is not part of knowledge plane lifecycle, but it is a **transitive prerequisite**:
- Tenant lifecycle SSOT remains in the **account domain** (Tenant.status), with domain-owned rules and persistence:
  - L5: `backend/app/hoc/cus/account/L5_engines/tenant_lifecycle_engine.py`
  - L6: `backend/app/hoc/cus/account/L6_drivers/tenant_lifecycle_driver.py`
- hoc_spine exposes tenant lifecycle operations for audiences via registry handlers:
  - `account.lifecycle.query`, `account.lifecycle.transition` in `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/lifecycle_handler.py`
- Audience boundary gates can enforce tenant state at request/runtime boundaries:
  - `backend/app/hoc/api/int/general/lifecycle_gate.py`

**Invariant:** Knowledge plane operations (register/transition/access/evidence) MUST be blocked when the tenant lifecycle forbids execution (e.g. suspended/terminated), regardless of plane readiness.

### 2.2 Separation Of Concerns (Template + Harness)

1. **hoc_spine owns the template + lifecycle authority:**
   - stage ordering
   - transition gating (authority)
   - audit/evidence requirements
   - audience-scoped operation surfaces (CUS/INT/FDR) wired via entrypoints (L2.1) and orchestrator registry

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
   - tenant lifecycle gate surfaces that must be consulted (account tenant lifecycle + audience lifecycle gates)
2. Decide which “plane” meaning is canonical:
   - **access plane** (mediation) is canonical for governance/RAG
   - **graph plane** (`lifecycle/drivers/knowledge_plane.py`) is either:
     - retired, or
     - renamed and explicitly separated as “knowledge graph” (not access plane)
3. Make audience scoping explicit for plane operations:
   - decide which audience runtime(s) own plane registration/listing and evidence query,
   - keep `retrieval/access` as the external retrieval choke point only if intentionally productized for CUS (deny-by-default remains mandatory).
4. Freeze ID semantics:
   - `plane_id` is owned by the governed plane registry and is immutable.
   - runtime/index identifiers must be derived from `plane_id` (never reusing `plane_id` as a free-form namespace key).

**Exit criteria (DONE 2026-02-08):** written decision on plane meaning + routing map updated (CUS access only; founder-only plane/evidence surfaces).

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

**Phase 1 implementation (2026-02-08):**
- Harness kit (stdlib-only) added: `backend/app/hoc/cus/hoc_spine/schemas/knowledge_plane_harness.py`
- Canonical harness literature: `literature/hoc_spine/KNOWLEDGE_PLANE_LIFECYCLE_HARNESS_LITERATURE.md`

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
