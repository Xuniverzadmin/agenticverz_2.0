# Overview — L5 Engines (1 files)

**Domain:** overview  
**Layer:** L5_engines  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

---

## overview_facade.py
**Path:** `backend/app/hoc/cus/overview/L5_engines/overview_facade.py`  
**Layer:** L5_engines | **Domain:** overview | **Lines:** 619

**Docstring:** Overview Engine (L5 Domain Logic)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SystemPulse` | to_dict | System health pulse summary. |
| `DomainCount` | to_dict | Count for a specific domain. |
| `HighlightsResult` | to_dict | Result from get_highlights. |
| `DecisionItem` | to_dict | A pending decision requiring human action. |
| `DecisionsResult` | to_dict | Result from get_decisions. |
| `CostPeriod` | to_dict | Time period for cost calculation. |
| `LimitCostItem` | to_dict | Single limit with cost status. |
| `CostsResult` | to_dict | Result from get_costs. |
| `DecisionsCountResult` | to_dict | Result from get_decisions_count. |
| `RecoveryStatsResult` | to_dict | Result from get_recovery_stats. |
| `OverviewFacade` | __init__, get_highlights, get_decisions, get_costs, get_decisions_count, get_recovery_stats | Overview Facade - Centralized access to overview domain operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_overview_facade` | `() -> OverviewFacade` | no | Get the singleton OverviewFacade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timedelta | no |
| `typing` | TYPE_CHECKING, Any, Dict, List, Optional | no |
| `app.hoc.cus.hoc_spine.services.time` | utc_now | no |
| `app.hoc.cus.overview.L6_drivers.overview_facade_driver` | OverviewFacadeDriver | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### __all__ Exports
`OverviewFacade`, `get_overview_facade`, `SystemPulse`, `DomainCount`, `HighlightsResult`, `DecisionItem`, `DecisionsResult`, `CostPeriod`, `LimitCostItem`, `CostsResult`, `DecisionsCountResult`, `RecoveryStatsResult`

---
