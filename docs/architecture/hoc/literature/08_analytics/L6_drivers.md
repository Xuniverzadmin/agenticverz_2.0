# Analytics — L6 Drivers (5 files)

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`CostWriteDriver`, `get_cost_write_driver`

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
