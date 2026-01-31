---
paths:
  - "hoc/**"
  - "backend/app/hoc/**"
---

# HOC Layer Topology Rules (BL-HOC-LAYER-001)

**Status:** RATIFIED | **Version:** 2.0.0
**Reference:** docs/architecture/topology/HOC_LAYER_TOPOLOGY_V2.0.0.md
**Ratified:** 2026-01-28

## Layer Reference (V2.0.0 — 6 Layers)

| Layer | Name | Location Pattern | Purpose |
|-------|------|------------------|---------|
| L1 | Frontend | website/app-shell/ | UI (DEFERRED) |
| L2.1 | API Facade | hoc/api/facades/cus/{domain}.py | Route grouping |
| L2 | APIs | hoc/api/cus/{domain}/*.py | HTTP handlers (thin) |
| L4 | hoc_spine | hoc/hoc_spine/ | **SINGLE ORCHESTRATOR** — cross-domain, lifecycle |
| L5 | Engines | hoc/cus/{domain}/L5_engines/ | Domain business logic |
| L6 | Drivers | hoc/cus/{domain}/L6_drivers/ | Domain DB operations |
| L7 | Models | app/models/ | ORM tables |

**NOTE:** L3 (Adapters) has been **REMOVED** in V2.0.0. Do not create L3_adapters/ directories.

## Naming Rules (LOCKED)

| Pattern | Status | Use |
|---------|--------|-----|
| *_service.py | ❌ BANNED | Never use |
| *_engine.py | ✅ Required | L5 business logic |
| *_driver.py | ✅ Required | L6 data access |
| *_adapter.py | ❌ REMOVED | L3 no longer exists |
| *_facade.py | ✅ Allowed | L2.1 API composition |

## Critical Contracts

| Layer | Rule |
|-------|------|
| L2 API | Calls L4 orchestrator. MUST NOT call L5 directly. |
| L4 hoc_spine | SINGLE OWNER of cross-domain. MUST NOT contain L5 engines. |
| L5 Engine | MUST NOT import sqlalchemy, sqlmodel, Session. MUST NOT call other domain L5. |
| L6 Driver | Pure data access. NO business logic. Returns domain objects, not ORM. |

## Import Flow (V2.0.0)

```
L2.1 → L2 → L4 → L5 → L6 → L7
              ↓
    (L4 owns ALL cross-domain)
```

**FORBIDDEN:**
- L2 → L5 direct (must go through L4)
- L5 → L5 cross-domain (L4 handles this)
- L5 → L6 cross-domain (L4 handles this)

## Cross-Domain Rule (BINDING)

**Only L4 (hoc_spine) may coordinate across domains.**

- L5 never calls another domain's L5
- L5 never calls another domain's L6
- L2 never coordinates multiple domains
- Cross-domain data is fetched by L4 and passed to L5 via typed context

## hoc_spine Structure

```
hoc/hoc_spine/
├── orchestrator/     ← Entry point (executor.py, registry.py)
├── authority/        ← Permission decisions
├── consequences/     ← Post-execution reactions
├── services/         ← Shared infrastructure (stateless, idempotent)
├── schemas/          ← Shared types
└── drivers/          ← Cross-domain DB coordination
```

## API-002 Counter-Rules (PIN-437)

### API-002-CR-001: Input Integrity
wrap_dict() must ONLY receive model_dump() output or fully constructed dicts. Never raw ORM entities.

### API-002-CR-002: Total Computation
For paginated endpoints, total MUST come from separate COUNT(*) query, not len(results).
