# Activity — L6 Drivers (1 files)

**Domain:** activity  
**Layer:** L6_drivers  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

---

## activity_read_driver.py
**Path:** `backend/app/hoc/cus/activity/L6_drivers/activity_read_driver.py`  
**Layer:** L6_drivers | **Domain:** activity | **Lines:** 385

**Docstring:** Activity Read Driver (L6 Data Access)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ActivityReadDriver` | __init__, count_runs, fetch_runs, fetch_run_detail, fetch_status_summary, fetch_runs_with_policy_context, fetch_at_risk_runs, fetch_metrics (+2 more) | L6 Driver for activity read operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_activity_read_driver` | `(session: AsyncSession) -> ActivityReadDriver` | no | Get an ActivityReadDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any | no |
| `sqlalchemy` | text | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

---
