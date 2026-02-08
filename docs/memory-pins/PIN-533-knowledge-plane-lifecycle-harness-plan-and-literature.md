# PIN-533: Knowledge Plane Lifecycle Harness Plan + Canonical Literature

**Date:** 2026-02-08  
**Category:** HOC Governance / System Runtime  
**Status:** ✅ COMPLETE (docs-only: plan + literature recorded)  

---

## Why This PIN Exists

Knowledge planes sit at the intersection of:
- mediated retrieval (RAG access),
- lifecycle staging (register→verify→ingest→index→classify→activate),
- and audit/evidence (SOC2-defensible proof).

Without a canonical contract and a single owner (hoc_spine), the codebase drifts into split-brain plane registries and non-durable in-memory SSOTs.

---

## Locked Decisions (Recorded)

1. **Plane cardinality:** many planes per tenant, keyed by `(tenant_id, plane_type, plane_name)`.
2. **Exposure:** hoc_spine is **system runtime** for customer-domain components. Audience surfaces (**CUS / INT / FDR**) are separate and must be wired intentionally; knowledge plane surfaces must not be assumed “internal-only” or “customer-only”.
3. **Authority:** hoc_spine is the transition authority; CUS domain engines provide capabilities but must not own lifecycle authority.

---

## Artifacts Created / Updated

### New Plan (V2)

- `docs/architecture/hoc/KNOWLEDGE_PLANE_LIFECYCLE_HARNESS_PLAN_V2.md`
  - Captures current split-brain reality (multiple in-memory “planes”).
  - Defines the target: hoc_spine template + harness ports + Postgres durability + surface re-home.
  - Provides a phased implementation plan and mechanical verification gates.

### New Canonical Literature

- `literature/hoc_spine/KNOWLEDGE_PLANE_LITERATURE.md`
  - First-principles model: knowledge access is authorization, deny-by-default.
  - Asset vs Plane distinction.
  - Runtime enforcement + evidence requirements.
- `literature/hoc_spine/KNOWLEDGE_PLANE_LIFECYCLE_HARNESS_LITERATURE.md`
  - Canonical harness template: authority, identity, audience surfaces, and ports.
  - Explicitly separates tenant lifecycle SSOT vs knowledge plane lifecycle SSOT.

### Cross-References Added

- `docs/architecture/hoc/INDEX.md` now links the V2 plan.
- `docs/architecture/hoc/KNOWLEDGE_PLANE_LIFECYCLE_REFACTOR_PLAN_V1.md` now points to V2 as the canonical end-state plan.
- `literature/hoc_spine/HOC_SPINE_CONSTITUTION.md` now references the new literature + plan.
- Domain canonical literature cross-links:
  - `literature/hoc_domain/policies/POLICIES_CANONICAL_SOFTWARE_LITERATURE.md`
  - `literature/hoc_domain/integrations/INTEGRATIONS_CANONICAL_SOFTWARE_LITERATURE.md`

---

## Next Implementation Work (Not In This PIN)

This PIN records the plan and literature only. The next execution phases are:
- remove in-memory plane/evidence registries by persisting to Postgres (alembic),
- register L4 operations for knowledge plane management (INT surface),
- unify retrieval plane registry with lifecycle plane registry,
- delete duplicate plane registries after importers are zero.
