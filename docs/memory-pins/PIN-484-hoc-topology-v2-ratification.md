# PIN-484: HOC Layer Topology V2.0.0 Ratification

**Status:** RATIFIED
**Created:** 2026-01-28
**Category:** Architecture
**Supersedes:** HOC_LAYER_TOPOLOGY_V1.4.0

---

## Summary

HOC Layer Topology V2.0.0 has been ratified as the binding architecture specification. This is a major simplification from V1.4.0, removing L3 and establishing L4 (hoc_spine) as the single orchestrator.

---

## Key Changes

| Aspect | V1.4.0 | V2.0.0 |
|--------|--------|--------|
| Layer count | 7 | 6 |
| L3 (Adapter) | Required | **REMOVED** |
| Cross-domain owner | Split (L3 + L4) | **Single (L4 only)** |
| `general` domain | Exists | **Abolished → hoc_spine** |
| Execution trace | L2 → L3 → L4 → L5 → L6 | **L2 → L4 → L5 → L6** |

---

## New 6-Layer Topology

```
L2.1 Facade
    ↓
L2 API (thin)
    ↓
L4 hoc_spine / Orchestrator   ← SINGLE OWNER
    ↓
L5 Domain Engine(s)
    ↓
L6 Driver(s)
    ↓
L7 Models
```

---

## Binding Constraints

1. **NO L3 LAYER** — L3 does not exist. No `L3_adapters/` directories.
2. **NO L5 IN HOC_SPINE** — hoc_spine has orchestrator, services, schemas, drivers — but NO L5 engines.
3. **SINGLE ORCHESTRATOR** — ALL execution enters L4 exactly once. No bypassing.
4. **L5 ISOLATION** — L5 engines never call other domains. Ever.
5. **LINEAR TRACE** — Every request follows: L2 → L4 → L5 → L6
6. **STATIC REGISTRY** — L4 → L5 binding via static operation registry. No dynamic dispatch.
7. **TYPED CONTEXT** — Context passed to L5 must be typed, immutable, versioned, and bounded.
8. **STATELESS SERVICES** — hoc_spine/services must be stateless, idempotent, and domain-agnostic.

---

## Authoritative Documents

- **Spec:** `docs/architecture/topology/HOC_LAYER_TOPOLOGY_V2.0.0.md`
- **Index:** `docs/architecture/topology/INDEX.md`
- **Review:** `docs/architecture/topology/HOC_SPINE_TOPOLOGY_REVIEW.md`

---

## Migration Required

1. Remove all `L3_adapters/` directories
2. Move `general/L4_runtime/` → `hoc_spine/orchestrator/`
3. Move shared services from `general/L5_engines/` → `hoc_spine/services/`
4. Abolish `general` domain entirely

---

## Rationale

- **Traceability** — Linear execution path, easy to debug
- **Single ownership** — One orchestrator owns all cross-domain
- **Simplicity** — 6 layers instead of 7, no ambiguous L3
- **First principles** — Execution-centric, not request-centric

---

## References

- PIN-470: HOC Layer Inventory
- PIN-483: HOC Domain Migration Complete
- HOC_SPINE_TOPOLOGY_PROPOSAL V1.5.0 (superseded)
