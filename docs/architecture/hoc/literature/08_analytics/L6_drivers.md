# Analytics — L6 Drivers (8 files)

**Domain:** analytics  
**Layer:** L6_drivers  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

---

## analytics_read_driver.py
**Path:** `backend/app/hoc/cus/analytics/L6_drivers/analytics_read_driver.py`  
**Layer:** L6_drivers | **Domain:** analytics | **Lines:** 376

**Docstring:** Analytics Read Driver (L6 Data Access)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AnalyticsReadDriver` | __init__, fetch_cost_metrics, fetch_llm_usage, fetch_worker_execution, fetch_cost_spend, fetch_cost_by_model, fetch_cost_by_feature | L6 Driver for analytics read operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_analytics_read_driver` | `(session: AsyncSession) -> AnalyticsReadDriver` | no | Get an AnalyticsReadDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime | no |
| `typing` | Any | no |
| `sqlalchemy` | text | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

---

## audit_persistence.py
**Path:** `backend/app/hoc/cus/analytics/L6_drivers/audit_persistence.py`  
**Layer:** L6_drivers | **Domain:** analytics | **Lines:** 169

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CoordinationAuditRecordDB` |  | SQLModel for coordination_audit_records table. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_now_utc` | `() -> datetime` | no | Get current UTC timestamp. |
| `persist_audit_record` | `(db: Session, audit_id: str, envelope_id: str, envelope_class: str, decision: st` | no | Persist a coordination audit record to the database. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.infra` | FeatureIntent, RetryPolicy | no |
| `logging` | logging | no |
| `datetime` | datetime, timezone | no |
| `typing` | Optional | no |
| `uuid` | UUID | no |
| `sqlmodel` | Field, Session, SQLModel | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### Constants
`FEATURE_INTENT`, `RETRY_POLICY`

---

## cost_anomaly_driver.py
**Path:** `backend/app/hoc/cus/analytics/L6_drivers/cost_anomaly_driver.py`  
**Layer:** L6_drivers | **Domain:** analytics | **Lines:** 992

**Docstring:** Cost Anomaly Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CostAnomalyDriver` | __init__, fetch_entity_baseline, fetch_entity_today_spend, fetch_tenant_baseline, fetch_tenant_today_spend, fetch_rolling_avg, fetch_baseline_avg, fetch_daily_spend (+12 more) | L6 driver for cost anomaly detection data access. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_cost_anomaly_driver` | `(session: Session) -> CostAnomalyDriver` | no | Factory function to get CostAnomalyDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | date, datetime | no |
| `typing` | Any, Dict, List, Optional, Tuple | no |
| `sqlalchemy` | text | no |
| `sqlmodel` | Session | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`CostAnomalyDriver`, `get_cost_anomaly_driver`

---

## cost_write_driver.py
**Path:** `backend/app/hoc/cus/analytics/L6_drivers/cost_write_driver.py`  
**Layer:** L6_drivers | **Domain:** analytics | **Lines:** 251

**Docstring:** Cost Write Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CostWriteDriver` | __init__, create_feature_tag, update_feature_tag, create_cost_record, create_or_update_budget | L6 driver for cost write operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_cost_write_driver` | `(session: Session) -> CostWriteDriver` | no | Factory function to get CostWriteDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timezone | no |
| `typing` | Optional | no |
| `sqlmodel` | Session | no |
| `app.db` | CostBudget, CostRecord, FeatureTag | no |
| `app.hoc.cus.general.L5_utils.time` | utc_now | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`CostWriteDriver`, `get_cost_write_driver`

---

## leader.py
**Path:** `backend/app/hoc/cus/analytics/L6_drivers/leader.py`  
**Layer:** L6_drivers | **Domain:** analytics | **Lines:** 359

**Docstring:** Leader election using PostgreSQL advisory locks.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `LeaderContext` | __init__, __aenter__, __aexit__, is_leader | Async context manager for leader election. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `try_acquire_leader_lock` | `(session: AsyncSession, lock_id: int) -> bool` | yes | Try to acquire an advisory lock (non-blocking). |
| `release_leader_lock` | `(session: AsyncSession, lock_id: int) -> bool` | yes | Explicitly release an advisory lock. |
| `is_lock_held` | `(session: AsyncSession, lock_id: int) -> bool` | yes | Check if a lock is currently held by any session. |
| `leader_election` | `(lock_id: int, timeout_seconds: float = 5.0) -> AsyncGenerator[bool, None]` | yes | Context manager for leader election. |
| `with_leader_lock` | `(lock_id: int, callback, *args, **kwargs)` | yes | Execute callback only if we can acquire leadership. |
| `with_canary_lock` | `(callback, *args, **kwargs)` | yes | Execute callback with canary runner lock. |
| `with_alert_worker_lock` | `(callback, *args, **kwargs)` | yes | Execute callback with alert worker lock. |
| `with_archiver_lock` | `(callback, *args, **kwargs)` | yes | Execute callback with provenance archiver lock. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `asyncio` | asyncio | no |
| `logging` | logging | no |
| `contextlib` | asynccontextmanager | no |
| `typing` | AsyncGenerator, Optional | no |
| `sqlalchemy` | text | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.db_async` | AsyncSessionLocal | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### Constants
`LOCK_CANARY_RUNNER`, `LOCK_ALERT_WORKER`, `LOCK_PROVENANCE_ARCHIVER`, `LOCK_BASELINE_BACKFILL`

---

## pattern_detection_driver.py
**Path:** `backend/app/hoc/cus/analytics/L6_drivers/pattern_detection_driver.py`  
**Layer:** L6_drivers | **Domain:** analytics | **Lines:** 209

**Docstring:** Pattern Detection Driver (L6 Data Access)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PatternDetectionDriver` | __init__, fetch_failed_runs, fetch_completed_runs_with_costs, insert_feedback, fetch_feedback_records | L6 Driver for pattern detection data operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_pattern_detection_driver` | `(session: AsyncSession) -> PatternDetectionDriver` | no | Get a PatternDetectionDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timedelta | no |
| `typing` | Any, Optional | no |
| `uuid` | UUID | no |
| `sqlalchemy` | func, select | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.models.feedback` | PatternFeedback | no |
| `app.models.tenant` | WorkerRun | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

---

## prediction_driver.py
**Path:** `backend/app/hoc/cus/analytics/L6_drivers/prediction_driver.py`  
**Layer:** L6_drivers | **Domain:** analytics | **Lines:** 319

**Docstring:** Prediction Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PredictionDriver` | __init__, fetch_failure_patterns, fetch_failed_runs, fetch_run_totals, fetch_cost_runs, fetch_predictions, insert_prediction | L6 driver for prediction data access. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_prediction_driver` | `(session: AsyncSession) -> PredictionDriver` | no | Factory function to get PredictionDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timedelta | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | UUID | no |
| `sqlalchemy` | func, select | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.models.feedback` | PatternFeedback | no |
| `app.models.prediction` | PredictionEvent | no |
| `app.models.tenant` | WorkerRun | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`PredictionDriver`, `get_prediction_driver`

---

## provenance_async.py
**Path:** `backend/app/hoc/cus/analytics/L6_drivers/provenance_async.py`  
**Layer:** L6_drivers | **Domain:** analytics | **Lines:** 463

**Docstring:** Async provenance logging for CostSim V2.

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `write_provenance` | `(run_id: Optional[str] = None, tenant_id: Optional[str] = None, variant_slug: st` | yes | Write a single provenance record. |
| `write_provenance_batch` | `(records: List[Dict[str, Any]], session: Optional[AsyncSession] = None) -> List[` | yes | Write multiple provenance records in a single transaction. |
| `query_provenance` | `(tenant_id: Optional[str] = None, variant_slug: Optional[str] = None, source: Op` | yes | Query provenance records. |
| `count_provenance` | `(tenant_id: Optional[str] = None, variant_slug: Optional[str] = None, start_date` | yes | Count provenance records matching filters. |
| `get_drift_stats` | `(start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> ` | yes | Get drift statistics between V1 and V2 costs. |
| `check_duplicate` | `(input_hash: str) -> bool` | yes | Check if a record with this input hash already exists. |
| `compute_input_hash` | `(payload: Dict[str, Any]) -> str` | no | Compute deterministic hash of input payload. |
| `backfill_v1_baseline` | `(records: List[Dict[str, Any]], batch_size: int = 100) -> Dict[str, int]` | yes | Backfill V1 baseline records from historical data. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `hashlib` | hashlib | no |
| `json` | json | no |
| `logging` | logging | no |
| `datetime` | datetime | no |
| `typing` | Any, Dict, List, Optional | no |
| `sqlalchemy` | and_, func, select | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.db_async` | AsyncSessionLocal, async_session_context | no |
| `app.models.costsim_cb` | CostSimProvenanceModel | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

---
