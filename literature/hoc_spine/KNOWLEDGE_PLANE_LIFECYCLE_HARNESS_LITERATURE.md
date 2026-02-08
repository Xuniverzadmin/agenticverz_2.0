# Knowledge Plane Lifecycle Harness (Canonical Literature)

**Audience:** system designers + domain owners  
**Status:** CANONICAL (hoc_spine runtime literature)  
**Date:** 2026-02-08  
**Plan:** `docs/architecture/hoc/KNOWLEDGE_PLANE_LIFECYCLE_HARNESS_PLAN_V2.md`  
**Contracts:** `docs/architecture/hoc/KNOWLEDGE_PLANE_CONTRACTS_V1.md`  

---

## 1) What This Document Is

This document defines the **canonical control-plane template** for knowledge planes:

- *What* a knowledge plane is (governed access domain)
- *Who* has authority over lifecycle state
- *How* domains harness the template without duplicating lifecycles
- *How* retrieval is mediated (deny-by-default) and evidenced

This is intentionally separate from tenant lifecycle:
- Tenant lifecycle = **who may execute** (account SSOT)
- Knowledge plane lifecycle = **what knowledge may be used** (knowledge SSOT)

---

## 2) Non-Negotiable Separation (Three “Planes”, One Canonical)

The codebase historically used the noun “plane” for multiple concerns. The canonical split is:

1. **Governed Knowledge Plane (canonical)**
   - A policy-governed knowledge access domain.
   - Identified by immutable `plane_id`.
   - Has governance lifecycle states (e.g., `DRAFT → … → ACTIVE`).

2. **Index / Retrieval Runtime (non-authoritative)**
   - Operational substrate (indexing readiness, query execution).
   - May report operational status (e.g., `INDEXING`, `ERROR`) but **must not** claim lifecycle authority.

3. **Tenant Lifecycle (separate SSOT)**
   - Global eligibility state (active/suspended/terminated).
   - Transitive prerequisite gate for all knowledge plane operations.

Only (1) is “knowledge plane” for policy and evidence.

---

## 3) Authority and Identity (First Principles)

### 3.1 Authority

- hoc_spine is the **single execution authority**.
- hoc_spine owns:
  - lifecycle transition gating,
  - transition semantics (what is allowed when),
  - failure propagation rules,
  - audience-scoped operation surfaces (CUS/INT/FDR).

Domains must not declare lifecycle `ACTIVE`.

### 3.2 Identity

`plane_id` is **owned by the governed plane registry**:
- generated once,
- immutable,
- never caller-controlled.

Any runtime/index identifiers must be **derived** from `plane_id` (never reused as a free-form namespace).

---

## 4) Audience Surfaces (CUS / INT / FDR)

hoc_spine is not an audience surface; it is system runtime.

Canonical exposure rules (Phase 0 enforced):
- **CUS**: mediated retrieval only (`POST /retrieval/access`)
- **FDR (founder)**: plane registry + evidence query

These are surface contracts, not implementation details.

Phase 3 wiring note:
- Founder plane registry + evidence query now dispatch via L4 `OperationRegistry` operations
  (`knowledge.planes.*`, `knowledge.evidence.*`).
 - Plane lifecycle transitions also dispatch via L4 operations:
   `knowledge.planes.transition` (founder surface).

---

## 5) What “Harnessable Template” Means

The template is **not** “hoc_spine owns domain states”.

It means:

- hoc_spine defines *the lifecycle protocol* and *the orchestration contract*.
- each domain supplies **capabilities** behind stable ports:
  - policies: deny-by-default access decisions (policy snapshot)
  - integrations: connector resolution + ingestion/index job execution
  - logs: evidence durability + export

The domains provide “how” (capability), hoc_spine provides “when/why” (authority).

---

## 6) Minimal Port Vocabulary (Phase 1)

The Phase 1 deliverable is a protocol surface in hoc_spine that is:
- stdlib-only schemas + `Protocol` ports,
- safe to import across domains without DB/ORM coupling,
- sufficient to persist planes/evidence later (Phase 2).

See implementation in:
- `backend/app/hoc/cus/hoc_spine/schemas/knowledge_plane_harness.py`

---

## 7) Relationship to Retrieval

Retrieval (RAG/data access) is **authorization**, not monitoring.

At runtime:
1. policy binds allowed planes (deny-by-default),
2. the mediator resolves connector for a governed `plane_id`,
3. the mediator emits evidence (allow/deny + provenance),
4. the system can prove later what was and wasn’t accessible.

Phase 4 (implemented 2026-02-08):
- Retrieval mediation now resolves planes against the persisted SSOT (`knowledge_plane_registry`) and only resolves governed planes in lifecycle `ACTIVE`.
- Retrieval evidence is persisted to `retrieval_evidence` (append-only) with `requested_at`, `completed_at`, and `duration_ms`.
- The mediator remains deny-by-default until a concrete policy gate is injected; connector runtime factories are still pending beyond the registry binding.

Phase 6 (implemented 2026-02-08):
- Retrieval mediation now injects a DB-backed policy gate that enforces an explicit `plane_id` allowlist from the run’s persisted `policy_snapshot_id`.
- Connector runtime now supports `connector_type in {"sql","sql_gateway"}` by constructing `SqlGatewayService` from the governed plane `config` (connection ref + template registry).

---

## 8) What Happens to Tenant Lifecycle Manager

Nothing is “replaced”.

- Tenant lifecycle remains the SSOT for tenant eligibility (account domain).
- Knowledge plane lifecycle is a different SSOT (knowledge plane eligibility).
- Knowledge plane operations must consult tenant lifecycle as a transitive gate.

This avoids semantic duplication of “active/suspended/terminated”:
those are tenant-global, not plane-local.
