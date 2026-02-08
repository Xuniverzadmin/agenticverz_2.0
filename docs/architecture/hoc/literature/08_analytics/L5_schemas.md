# Analytics — L5 Schemas (5 files)

**Domain:** analytics  
**Layer:** L5_schemas  
**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

**Layer Contract:** Data contracts — Pydantic models, dataclasses, type references only

---

## cost_anomaly_dtos.py
**Path:** `backend/app/hoc/cus/analytics/L5_schemas/cost_anomaly_dtos.py`  
**Layer:** L5_schemas | **Domain:** analytics | **Lines:** 44

**Docstring:** Cost Anomaly Persistence DTOs

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PersistedAnomaly` |  | DTO returned by L6 after persisting a CostAnomaly ORM row. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass, field | no |
| `typing` | Any, Dict, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L4_spine, L5_engines, L6_drivers
**Called by:** L5_engines, L4_spine

---

## cost_anomaly_schemas.py
**Path:** `backend/app/hoc/cus/analytics/L5_schemas/cost_anomaly_schemas.py`  
**Layer:** L5_schemas | **Domain:** analytics | **Lines:** 52

**Docstring:** Cost Anomaly Schemas (PIN-511 Phase 1.2)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CostAnomalyReadProtocol` | fetch_active_budgets, find_existing_anomaly, persist_anomaly, flush_and_refresh | Protocol for cost anomaly read/persist operations. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `datetime` | datetime | no |
| `typing` | TYPE_CHECKING, List, Optional, Protocol, runtime_checkable | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L4_spine, L5_engines, L6_drivers
**Called by:** L5_engines, L4_spine

---

## cost_snapshot_schemas.py
**Path:** `backend/app/hoc/cus/analytics/L5_schemas/cost_snapshot_schemas.py`  
**Layer:** L5_schemas | **Domain:** analytics | **Lines:** 302

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
| `CostSnapshotsDriverProtocol` | insert_snapshot, update_snapshot, insert_aggregate, get_current_baseline, aggregate_cost_records, insert_baseline, get_snapshot, get_aggregates_with_baseline (+3 more) | Typed boundary contract for cost snapshot database operations. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `hashlib` | hashlib | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timedelta, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Protocol, runtime_checkable | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L4_spine, L5_engines, L6_drivers
**Called by:** L5_engines, L4_spine

### Constants
`SEVERITY_THRESHOLDS`

---

## feedback_schemas.py
**Path:** `backend/app/hoc/cus/analytics/L5_schemas/feedback_schemas.py`  
**Layer:** L5_schemas | **Domain:** analytics | **Lines:** 44

**Docstring:** Pattern feedback DTO mirror.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PatternFeedbackCreate` |  | Input model for creating pattern feedback. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Optional | no |
| `pydantic` | BaseModel | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L4_spine, L5_engines, L6_drivers
**Called by:** L5_engines, L4_spine

---

## query_types.py
**Path:** `backend/app/hoc/cus/analytics/L5_schemas/query_types.py`  
**Layer:** L5_schemas | **Domain:** analytics | **Lines:** 36

**Docstring:** Analytics Query Types

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ResolutionType` |  | Time resolution for analytics data. |
| `ScopeType` |  | Scope of analytics aggregation. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `enum` | Enum | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L4_spine, L5_engines, L6_drivers
**Called by:** L5_engines, L4_spine

### __all__ Exports
`ResolutionType`, `ScopeType`

---
