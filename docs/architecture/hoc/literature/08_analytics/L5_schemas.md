# Analytics — L5 Schemas (1 files)

**Domain:** analytics  
**Layer:** L5_schemas  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** Data contracts — Pydantic models, dataclasses, type references only

---

## cost_snapshot_schemas.py
**Path:** `backend/app/hoc/cus/analytics/L5_schemas/cost_snapshot_schemas.py`  
**Layer:** L5_schemas | **Domain:** analytics | **Lines:** 243

**Docstring:** M27 Cost Snapshot Schemas

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SnapshotType` |  |  |
| `SnapshotStatus` |  |  |
| `EntityType` |  |  |
| `CostSnapshot` | create, to_dict | Point-in-time cost snapshot definition. |
| `SnapshotAggregate` | create | Aggregated cost data for an entity within a snapshot. |
| `SnapshotBaseline` | create | Rolling baseline for an entity (used for anomaly threshold). |
| `AnomalyEvaluation` |  | Audit record for an anomaly evaluation. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `hashlib` | hashlib | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timedelta, timezone | no |
| `enum` | Enum | no |
| `typing` | Any | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines, L6_drivers
**Called by:** L5_engines, L3_adapters

### Constants
`SEVERITY_THRESHOLDS`

---
