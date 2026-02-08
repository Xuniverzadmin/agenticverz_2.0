# Ops — L6 Drivers (1 files)

**Domain:** ops  
**Layer:** L6_drivers  
**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

**Layer Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

---

## cost_read_driver.py
**Path:** `backend/app/hoc/cus/ops/L6_drivers/cost_read_driver.py`  
**Layer:** L6_drivers | **Domain:** ops | **Lines:** 549

**Docstring:** Cost Read Driver (L6 Data Access)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CostReadDriver` | __init__, fetch_global_spend_summary, fetch_anomaly_summary, fetch_largest_deviation, fetch_last_snapshot_time, fetch_daily_cost_series, fetch_anomalies, fetch_tenant_cost_rollup (+13 more) | L6 Driver for cost intelligence read operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_cost_read_driver` | `(session: AsyncSession) -> CostReadDriver` | no | Get a CostReadDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `datetime` | datetime | no |
| `typing` | Any | no |
| `sqlalchemy` | text | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

---
