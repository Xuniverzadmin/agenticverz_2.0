# Activity — L6 Drivers (3 files)

**Domain:** activity  
**Layer:** L6_drivers  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

---

## activity_read_driver.py
**Path:** `backend/app/hoc/cus/activity/L6_drivers/activity_read_driver.py`  
**Layer:** L6_drivers | **Domain:** activity | **Lines:** 344

**Docstring:** Activity Read Driver (L6 Data Access)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ActivityReadDriver` | __init__, count_runs, fetch_runs, fetch_run_detail, fetch_status_summary, fetch_runs_with_policy_context, fetch_at_risk_runs, fetch_metrics (+1 more) | L6 Driver for activity read operations. |

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

## orphan_recovery.py
**Path:** `backend/app/hoc/cus/activity/L6_drivers/orphan_recovery.py`  
**Layer:** L6_drivers | **Domain:** activity | **Lines:** 259

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `detect_orphaned_runs` | `(session: AsyncSession, threshold_minutes: int = ORPHAN_THRESHOLD_MINUTES) -> li` | yes | Detect runs that appear to be orphaned. |
| `mark_run_as_crashed` | `(session: AsyncSession, run: WorkerRun, reason: str = 'System restart - run was ` | yes | Mark a run as crashed. |
| `recover_orphaned_runs` | `(threshold_minutes: Optional[int] = None) -> dict` | yes | Main recovery function - called on startup. |
| `get_crash_recovery_summary` | `() -> dict` | yes | Get a summary of crashed runs for operator visibility. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.infra` | FeatureIntent, RetryPolicy | no |
| `logging` | logging | no |
| `os` | os | no |
| `datetime` | datetime, timedelta | no |
| `typing` | Optional | no |
| `sqlalchemy` | select, update | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.db` | get_async_session | no |
| `app.models.tenant` | WorkerRun | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### Constants
`FEATURE_INTENT`, `RETRY_POLICY`, `ORPHAN_THRESHOLD_MINUTES`, `RECOVERY_ENABLED`

---

## run_signal_service.py
**Path:** `backend/app/hoc/cus/activity/L6_drivers/run_signal_service.py`  
**Layer:** L6_drivers | **Domain:** activity | **Lines:** 188

**Docstring:** RunSignalService (L6 Driver)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `RunSignalService` | __init__, update_risk_level, get_risk_level | Service for updating run risk levels based on threshold signals. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Any, List | no |
| `sqlalchemy` | text | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### Constants
`SIGNAL_TO_RISK_LEVEL`, `DEFAULT_RISK_LEVEL`

---
