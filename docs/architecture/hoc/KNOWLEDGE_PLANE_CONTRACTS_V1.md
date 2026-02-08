# Knowledge Planes — Contracts (V1)

**Status:** DRAFT (Phase 0 contract freeze)  
**Date:** 2026-02-08  
**Plan:** `docs/architecture/hoc/KNOWLEDGE_PLANE_LIFECYCLE_HARNESS_PLAN_V2.md`  

This document exists to prevent ontology drift by making authority, identity, and failure semantics mechanically enforceable.

---

## Contract 1 — Canonical Authority

**Rule:** Only the knowledge plane lifecycle authority may declare lifecycle `ACTIVE`.

- Lifecycle state is defined by `KnowledgePlaneLifecycleState` (GAP-089).
- Operational runtimes may report readiness, but must not claim lifecycle authority.

**Implication:** Any module that writes “active” must be audited for whether it is writing lifecycle state or runtime readiness.

---

## Contract 2 — `plane_id` Ownership (SSOT)

**Rule:** `plane_id` is generated once by the governed knowledge plane registry and is immutable.

- `plane_id` must not be caller-controlled.
- `plane_id` must not be reused as a generic namespace key (e.g., `plane_id=tenant_id`).

**Derived identifiers:** runtime/index identifiers must be derived from `plane_id` (e.g., `index_id = {plane_id}_{version}_{engine}`).

---

## Contract 3 — Failure Propagation

**Rule:** operational runtime `ERROR` must be reflected into lifecycle `FAILED` (or a defined non-terminal degraded state) through the lifecycle authority.

- `FAILED` is a lifecycle outcome, not a log-only event.
- Evidence must record failures deterministically (allow/deny + reason + snapshot id if present).

---

## Contract 4 — Tenant Lifecycle as Transitive Gate

**Rule:** tenant lifecycle is a separate SSOT but is a transitive prerequisite for knowledge plane operations.

- Tenant lifecycle SSOT remains in account domain (Tenant.status).
- Knowledge plane operations MUST consult tenant lifecycle gating.

**Implication:** a plane cannot be registered/activated/accessed when tenant state forbids execution.

---

## Contract 5 — Audience Surface Separation (CUS / INT / FDR)

**Rule:** audience surfaces are separate and must be wired intentionally.

- hoc_spine is execution authority and system runtime; it is not an audience surface.
- Any plane management exposure (register/transition/evidence query) must be explicitly assigned to one or more audience surfaces (CUS/INT/FDR) and wired through the HOC topology (L2.1 → L2 → L4 registry → L5 → L6 → L7).

**Phase 0 wiring (2026-02-08):**
- CUS exposes only `POST /retrieval/access` in `backend/app/hoc/api/cus/policies/retrieval.py`.
- Plane registry + evidence query are founder-only (guarded by `verify_fops_token`) in `backend/app/hoc/api/fdr/ops/retrieval_admin.py`.

**Phase 3 wiring (2026-02-08):**
- Founder retrieval admin routes dispatch through `OperationRegistry` to L4 operations:
  - `knowledge.planes.*`, `knowledge.evidence.*`

---

## Contract 6 — Protected Transition Intent Must Be Persisted

**Rule:** protected lifecycle transitions require explicit, persisted intent in `knowledge_plane_registry.config`.

Reserved config keys (no secrets):
- `bound_policy_ids: list[str]` (required before lifecycle can transition `→ ACTIVE`)
- `purge_approved: bool` (required before lifecycle can transition `→ PURGED`)

Mutation rule:
- These keys must be mutated only via founder/admin ops (config-only; no state change):
  - `knowledge.planes.bind_policy`
  - `knowledge.planes.unbind_policy`
  - `knowledge.planes.approve_purge`

---

## Mechanical Checks (Phase 0)

Phase 0 should add mechanical checks that fail fast when the contracts are violated:

1. Multiple “active writers” (string/enum) outside lifecycle authority.
2. `plane_id` reused as namespace outside knowledge plane/retrieval contexts.
3. Evidence stored in-memory instead of `retrieval_evidence` persistence.
