# Analytics — L6 Drivers (13 files)

**Domain:** analytics  
**Layer:** L6_drivers  
**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

---

## canary_report_driver.py
**Path:** `backend/app/hoc/cus/analytics/L6_drivers/canary_report_driver.py`  
**Layer:** L6_drivers | **Domain:** analytics | **Lines:** 203

**Docstring:** Canary Report Driver for CostSim V2.

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `write_canary_report` | `(session: AsyncSession, run_id: str, timestamp: datetime, status: str, total_sam` | yes | Write a canary report to the database. |
| `query_canary_reports` | `(status: Optional[str] = None, passed: Optional[bool] = None, start_date: Option` | yes | Query canary reports from the database. |
| `get_canary_report_by_run_id` | `(run_id: str) -> Optional[Dict[str, Any]]` | yes | Get a canary report by run ID. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `json` | json | no |
| `logging` | logging | no |
| `datetime` | datetime | no |
| `typing` | Any, Dict, List, Optional | no |
| `sqlalchemy` | and_, select | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.db_async` | async_session_context | no |
| `app.models.costsim_cb` | CostSimCanaryReportModel | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

---

## coordination_audit_driver.py
**Path:** `backend/app/hoc/cus/analytics/L6_drivers/coordination_audit_driver.py`  
**Layer:** L6_drivers | **Domain:** analytics | **Lines:** 166

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

### __all__ Exports
`CostAnomalyDriver`, `get_cost_anomaly_driver`

---

## cost_anomaly_read_driver.py
**Path:** `backend/app/hoc/cus/analytics/L6_drivers/cost_anomaly_read_driver.py`  
**Layer:** L6_drivers | **Domain:** analytics | **Lines:** 191

**Docstring:** Cost Anomaly Read Driver (PIN-511 Phase 1.2)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CostAnomalyReadDriver` | __init__, fetch_active_budgets, find_existing_anomaly, persist_anomaly, flush_and_refresh, upsert_anomaly | L6 driver for budget reads and anomaly deduplication/persistence. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_cost_anomaly_read_driver` | `(session: Session) -> CostAnomalyReadDriver` | no | Factory for CostAnomalyReadDriver. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `datetime` | datetime | no |
| `typing` | Any, Dict, List, Optional | no |
| `sqlmodel` | Session, select | no |
| `app.db` | CostAnomaly, CostBudget | no |
| `app.hoc.cus.analytics.L5_schemas.cost_anomaly_dtos` | PersistedAnomaly | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

---

## cost_snapshots_driver.py
**Path:** `backend/app/hoc/cus/analytics/L6_drivers/cost_snapshots_driver.py`  
**Layer:** L6_drivers | **Domain:** analytics | **Lines:** 474

**Docstring:** Cost Snapshots Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CostSnapshotsDriver` | __init__, insert_snapshot, update_snapshot, insert_aggregate, get_current_baseline, aggregate_cost_records, insert_baseline, get_snapshot (+4 more) | L6 driver for cost snapshot database operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_cost_snapshots_driver` | `(session: AsyncSession) -> CostSnapshotsDriver` | no | Factory function to get CostSnapshotsDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any | no |
| `sqlalchemy` | text | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `L5_schemas.cost_snapshot_schemas` | AnomalyEvaluation, CostSnapshot, EntityType, SnapshotAggregate, SnapshotBaseline (+2) | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

### __all__ Exports
`CostSnapshotsDriver`, `get_cost_snapshots_driver`

---

## cost_write_driver.py
**Path:** `backend/app/hoc/cus/analytics/L6_drivers/cost_write_driver.py`  
**Layer:** L6_drivers | **Domain:** analytics | **Lines:** 250

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

### __all__ Exports
`CostWriteDriver`, `get_cost_write_driver`

---

## feedback_read_driver.py
**Path:** `backend/app/hoc/cus/analytics/L6_drivers/feedback_read_driver.py`  
**Layer:** L6_drivers | **Domain:** analytics | **Lines:** 121

**Docstring:** Feedback Read Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `FeedbackReadDriver` | __init__, fetch_feedback_list, fetch_feedback_by_id, fetch_feedback_stats | L6 driver for feedback read operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_feedback_read_driver` | `(session: AsyncSession) -> FeedbackReadDriver` | no | Get feedback read driver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, Optional | no |
| `uuid` | UUID | no |
| `sqlalchemy` | func, select | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.models.feedback` | PatternFeedback | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

---

## leader_driver.py
**Path:** `backend/app/hoc/cus/analytics/L6_drivers/leader_driver.py`  
**Layer:** L6_drivers | **Domain:** analytics | **Lines:** 360

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

### __all__ Exports
`PredictionDriver`, `get_prediction_driver`

---

## prediction_read_driver.py
**Path:** `backend/app/hoc/cus/analytics/L6_drivers/prediction_read_driver.py`  
**Layer:** L6_drivers | **Domain:** analytics | **Lines:** 161

**Docstring:** Prediction Read Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PredictionReadDriver` | __init__, fetch_prediction_list, fetch_prediction_by_id, fetch_predictions_for_subject, fetch_prediction_stats | L6 driver for prediction read operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_prediction_read_driver` | `(session: AsyncSession) -> PredictionReadDriver` | no | Get prediction read driver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime | no |
| `typing` | Any, Optional | no |
| `uuid` | UUID | no |
| `sqlalchemy` | func, select | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.models.prediction` | PredictionEvent | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

---

## provenance_driver.py
**Path:** `backend/app/hoc/cus/analytics/L6_drivers/provenance_driver.py`  
**Layer:** L6_drivers | **Domain:** analytics | **Lines:** 476

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

---
