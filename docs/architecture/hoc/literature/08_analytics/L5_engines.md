# Analytics — L5 Engines (4 files)

**Domain:** analytics  
**Layer:** L5_engines  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

---

## analytics_facade.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/analytics_facade.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 628

**Docstring:** Analytics Facade (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `TimeWindowResult` |  | Time window specification. |
| `UsageTotalsResult` |  | Aggregate usage totals. |
| `UsageDataPointResult` |  | Single data point in usage time series. |
| `SignalSourceResult` |  | Signal source metadata. |
| `UsageStatisticsResult` |  | Usage statistics result. |
| `CostTotalsResult` |  | Aggregate cost totals. |
| `CostDataPointResult` |  | Single data point in cost time series. |
| `CostByModelResult` |  | Cost breakdown by model. |
| `CostByFeatureResult` |  | Cost breakdown by feature tag. |
| `CostStatisticsResult` |  | Cost statistics result. |
| `TopicStatusResult` |  | Status of a topic within a subdomain. |
| `AnalyticsStatusResult` |  | Analytics domain status. |
| `SignalAdapter` | fetch_cost_metrics, fetch_llm_usage, fetch_worker_execution, fetch_cost_spend, fetch_cost_by_model, fetch_cost_by_feature | Signal adapters for fetching data from various sources. |
| `AnalyticsFacade` | __init__, get_usage_statistics, get_cost_statistics, get_status, _calculate_freshness, _calculate_freshness_from_cost | Unified facade for Analytics domain operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_analytics_facade` | `() -> AnalyticsFacade` | no | Get the singleton AnalyticsFacade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | TYPE_CHECKING, Any | no |
| `app.hoc.cus.analytics.L6_drivers.analytics_read_driver` | get_analytics_read_driver | no |
| `app.hoc.cus.analytics.L5_schemas.query_types` | ResolutionType, ScopeType | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## costsim_models.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/costsim_models.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 306

**Docstring:** Data models for CostSim V2 sandbox evaluation.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `V2SimulationStatus` |  | V2 simulation result status. |
| `ComparisonVerdict` |  | Verdict from V1 vs V2 comparison. |
| `V2SimulationResult` | to_dict, compute_output_hash | Result from CostSim V2 simulation. |
| `ComparisonResult` | to_dict | Result of comparing V2 vs V1 simulation. |
| `DiffResult` | to_dict | Detailed diff between two simulation results. |
| `CanaryReport` | to_dict | Report from daily canary run. |
| `DivergenceReport` | to_dict | Cost divergence report between V1 and V2. |
| `ValidationResult` | to_dict | Result of validating V2 against a reference dataset. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `hashlib` | hashlib | no |
| `json` | json | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## detection_facade.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/detection_facade.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 615

**Docstring:** Detection Facade (L5 Domain Engine)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AnomalyCoordinatorPort` | detect_and_ingest | Protocol for anomaly detection + incident ingestion (PIN-520 L5 purity). |
| `DetectionType` |  | Types of anomaly detection. |
| `AnomalyStatus` |  | Anomaly resolution status. |
| `DetectionResult` | to_dict | Result of a detection run. |
| `AnomalyInfo` | to_dict | Anomaly information. |
| `DetectionStatusInfo` | to_dict | Detection engine status. |
| `DetectionFacade` | __init__, cost_detector, run_detection, _run_cost_detection, list_anomalies, get_anomaly, resolve_anomaly, acknowledge_anomaly (+1 more) | Facade for anomaly detection operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_detection_facade` | `(anomaly_coordinator: Optional[AnomalyCoordinatorPort] = None) -> DetectionFacad` | no | Get the detection facade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional, Protocol | no |
| `uuid` | uuid | no |
| `app.hoc.cus.analytics.L5_engines.cost_anomaly_detector_engine` | AnomalySeverity | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## provenance.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/provenance.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 413

**Docstring:** Full provenance logging for CostSim V2 sandbox.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ProvenanceLog` | to_dict, from_dict, get_decompressed_input, get_decompressed_output | Single provenance log entry. |
| `ProvenanceLogger` | __init__, log, _store, _flush, _write_to_file, _write_to_db, close, query | Logger for CostSim V2 provenance. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `compute_hash` | `(data: Any) -> str` | no | Compute SHA256 hash of data. |
| `compress_json` | `(data: Any) -> str` | no | Compress JSON data to base64-encoded gzip. |
| `get_provenance_logger` | `() -> ProvenanceLogger` | no | Get the global provenance logger. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `asyncio` | asyncio | no |
| `base64` | base64 | no |
| `gzip` | gzip | no |
| `hashlib` | hashlib | no |
| `json` | json | no |
| `logging` | logging | no |
| `uuid` | uuid | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `pathlib` | Path | no |
| `typing` | Any, Dict, List, Optional | no |
| `app.hoc.cus.analytics.L5_engines.config_engine` | get_commit_sha, get_config | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---
