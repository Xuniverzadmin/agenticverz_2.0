---
paths:
  - "hoc/**"
  - "backend/app/hoc/**"
  - "houseofcards/**"
---

# HOC Layer Topology Rules (BL-HOC-LAYER-001)

**Status:** RATIFIED | **Version:** 1.2.0
**Reference:** docs/architecture/HOC_LAYER_TOPOLOGY_V1.md

## Layer Reference

| Layer | Name | Location Pattern | Purpose |
|-------|------|------------------|---------|
| L1 | Frontend | website/app-shell/ | UI |
| L2.1 | API Facade | houseofcards/api/facades/{audience}/ | Route grouping |
| L2 | APIs | houseofcards/api/{audience}/ | HTTP handlers |
| L3 | Adapters | houseofcards/{audience}/{domain}/adapters/ | Translation (cross-domain OK) |
| L4 | Runtime | houseofcards/{audience}/general/runtime/ | Control plane |
| L5 | Engines/Workers | houseofcards/{audience}/{domain}/engines/ | Business logic |
| L6 | Drivers | houseofcards/{audience}/{domain}/drivers/ | DB operations |
| L7 | Models | app/models/ or app/{audience}/models/ | ORM tables |

## Naming Rules (LOCKED)

| Pattern | Status | Use |
|---------|--------|-----|
| *_service.py | ❌ BANNED | Never use |
| *_engine.py | ✅ Required | L5 business logic |
| *_driver.py | ✅ Required | L6 data access |
| *_adapter.py | ✅ Allowed | L3 translation |
| *_facade.py | ✅ Allowed | L2.1 API composition |

## Critical Contracts

| Layer | Rule |
|-------|------|
| L5 Engine | MUST NOT import sqlalchemy, sqlmodel, Session at runtime |
| L6 Driver | Pure data access. NO business logic |
| L3 Adapter | Translation only. No state mutation, no retries |

## Import Flow

```
L2.1 → L2 → L3 → L4/L5 → L6 → L7
              ↓
         (cross-domain allowed at L3 only)
```

## Cross-Domain Location Rule

Cross-domain items go in {audience}/general/, never outside {audience}/ folder.

## API-002 Counter-Rules (PIN-437)

### API-002-CR-001: Input Integrity
wrap_dict() must ONLY receive model_dump() output or fully constructed dicts. Never raw ORM entities.

### API-002-CR-002: Total Computation
For paginated endpoints, total MUST come from separate COUNT(*) query, not len(results).
