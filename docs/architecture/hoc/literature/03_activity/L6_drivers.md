# Activity — L6 Drivers (4 files)

**Domain:** activity  
**Layer:** L6_drivers  
**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

---

## cus_telemetry_driver.py
**Path:** `backend/app/hoc/cus/activity/L6_drivers/cus_telemetry_driver.py`  
**Layer:** L6_drivers | **Domain:** activity | **Lines:** 620

**Docstring:** Customer Telemetry Driver

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `UsageRow` |  | Immutable usage record DTO. |
| `UsageSummaryRow` |  | Immutable usage summary DTO. |
| `IntegrationUsageRow` |  | Immutable per-integration usage DTO. |
| `DailyAggregateRow` |  | Immutable daily aggregate DTO. |
| `CusTelemetryDriver` | __init__, fetch_by_call_id, fetch_call_ids_batch, fetch_integration, fetch_usage_summary, fetch_per_integration_usage, fetch_usage_history, fetch_daily_aggregates (+4 more) | L6 driver for customer telemetry data access. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `utc_now` | `() -> datetime` | no | Return current UTC time with timezone info. |
| `get_cus_telemetry_driver` | `(session: AsyncSession) -> CusTelemetryDriver` | no | Get driver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | date, datetime, timezone | no |
| `typing` | Any, Dict, List, Optional, Tuple | no |
| `uuid` | uuid4 | no |
| `sqlalchemy` | func, select, and_ | no |
| `sqlalchemy.dialects.postgresql` | insert | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.models.cus_models` | CusIntegration, CusLLMUsage, CusPolicyResult, CusUsageDaily | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

---

## orphan_recovery_driver.py
**Path:** `backend/app/hoc/cus/activity/L6_drivers/orphan_recovery_driver.py`  
**Layer:** L6_drivers | **Domain:** activity | **Lines:** 139

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `detect_orphaned_runs` | `(session: AsyncSession, threshold_minutes: int = ORPHAN_THRESHOLD_MINUTES) -> li` | yes | Detect runs that appear to be orphaned. |
| `mark_run_as_crashed` | `(session: AsyncSession, run: WorkerRun, reason: str = 'System restart - run was ` | yes | Mark a run as crashed. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.infra` | FeatureIntent, RetryPolicy | no |
| `logging` | logging | no |
| `os` | os | no |
| `datetime` | datetime, timedelta | no |
| `sqlalchemy` | select, update | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.models.tenant` | WorkerRun | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

### Constants
`FEATURE_INTENT`, `RETRY_POLICY`, `ORPHAN_THRESHOLD_MINUTES`

---

## run_signal_driver.py
**Path:** `backend/app/hoc/cus/activity/L6_drivers/run_signal_driver.py`  
**Layer:** L6_drivers | **Domain:** activity | **Lines:** 193

**Docstring:** RunSignalService (L6 Driver)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `RunSignalDriver` | __init__, update_risk_level, get_risk_level | Service for updating run risk levels based on threshold signals. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Any, List | no |
| `sqlalchemy` | text | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

### Constants
`SIGNAL_TO_RISK_LEVEL`, `DEFAULT_RISK_LEVEL`

---
