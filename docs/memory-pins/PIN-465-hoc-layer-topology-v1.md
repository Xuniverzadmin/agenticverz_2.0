# PIN-465: HOC Layer Topology V1

**Status:** RATIFIED
**Created:** 2026-01-23
**Category:** Architecture / Layer Model
**Reference:** `docs/architecture/HOC_LAYER_TOPOLOGY_V1.md`

---

## Summary

Formal architecture document defining the 8-layer topology for House of Cards (HOC) structure. Establishes audience-first, domain-second organization with governed runtime layer.

---

## Key Decisions

### Layer Structure (L1-L8)

| Layer | Location | Purpose |
|-------|----------|---------|
| L1 | Frontend | AI Console (UI projection + Panel Engine) |
| L2.1 | `houseofcards/api/facades/{audience}/{domain}/` | API Organizer |
| L2 | `houseofcards/api/{audience}/{domain}/` | HTTP APIs |
| L3 | `houseofcards/{audience}/{domain}/adapters/` | Adapters (cross-domain allowed) |
| L4 | `houseofcards/{audience}/general/runtime/` | Governed Runtime (shared) |
| L5 | `houseofcards/{audience}/{domain}/engines,workers,schemas/` | Business Logic |
| L6 | `houseofcards/{audience}/{domain}/drivers/` | DB Operations |
| L7 | `app/models/` + `app/{audience}/models/` | Database Tables |
| L8 | Database | PostgreSQL |

### Key Architecture Choices

1. **Everything under HOC** — APIs, adapters, engines all in `houseofcards/`
2. **Audience-first** — `{audience}/{domain}` pattern throughout
3. **Cross-domain at L3 only** — Adapters are the aggregation point
4. **Shared runtime per audience** — `general/runtime/` not per domain
5. **Hybrid models** — Shared + audience-specific tables
6. **Panel engine location** — `houseofcards/{audience}/frontend/{domain}/`

### L7 Models Decision (Option B)

| Category | Location |
|----------|----------|
| Shared | `app/models/` (tenant, audit_ledger, base) |
| Customer-specific | `app/customer/models/` (policy, killswitch) |
| Founder-specific | `app/founder/models/` (ops_events) |
| Internal-specific | `app/internal/models/` (recovery, agent) |

---

## Document Location

```
docs/architecture/HOC_LAYER_TOPOLOGY_V1.md
```

---

## Supersedes

- Partially supersedes: `docs/architecture/LAYER_MODEL.md`
- Replaces draft: `API_FACADE_COEXISTENCE_PLAN.md` (deleted)
- Replaces draft: `LAYER_TOPOLOGY_REVISED_PLAN.md` (deleted)

---

## Next Steps

1. Map existing files to new structure
2. Create migration plan
3. Implement Phase 1 (L2.1 facades)

---

## Related PINs

- PIN-464: HOC Customer Domain Comprehensive Audit
- PIN-399: Layer Model (Function-Route Separation)
