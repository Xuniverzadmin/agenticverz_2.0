# Analytics — L5 Engines (18 files)

**Domain:** analytics  
**Layer:** L5_engines  
**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

---

## canary_engine.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/canary_engine.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 716

**Docstring:** Daily canary runner for CostSim V2 validation.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CanarySample` |  | A single canary test sample. |
| `CanaryRunConfig` |  | Configuration for a canary run. |
| `CanaryRunner` | __init__, run, _run_internal, _load_samples, _generate_synthetic_samples, _run_single, _calculate_metrics, _approximate_kl_divergence (+4 more) | Daily canary runner for V2 validation. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `run_canary` | `(sample_count: int = 100, drift_threshold: float = 0.2, session: Any = None) -> ` | yes | Convenience function to run canary. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `asyncio` | asyncio | no |
| `json` | json | no |
| `logging` | logging | no |
| `math` | math | no |
| `uuid` | uuid | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timedelta, timezone | no |
| `pathlib` | Path | no |
| `typing` | Any, Dict, List, Optional, Tuple | no |
| `app.hoc.cus.hoc_spine.services.cross_domain_gateway` | get_circuit_breaker | no |
| `app.hoc.cus.hoc_spine.services.cross_domain_gateway` | report_drift | no |
| `app.hoc.cus.analytics.L5_engines.config_engine` | get_config | no |
| `app.hoc.cus.analytics.L6_drivers.leader_driver` | LOCK_CANARY_RUNNER, leader_election | no |
| `app.hoc.cus.analytics.L5_engines.costsim_models` | CanaryReport, ComparisonResult, ComparisonVerdict, DiffResult | no |
| `app.hoc.cus.analytics.L5_engines.provenance` | get_provenance_logger | no |
| `app.hoc.cus.analytics.L5_engines.v2_adapter` | CostSimV2Adapter | no |
| `app.worker.simulate` | CostSimulator | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

---

## config_engine.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/config_engine.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 48

**Docstring:** CostSim V2 Configuration - BACKWARD COMPATIBILITY RE-EXPORTS

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.hoc.cus.hoc_spine.services.costsim_config` | CostSimConfig, get_commit_sha, get_config, is_v2_disabled_by_drift, is_v2_sandbox_enabled | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### __all__ Exports
`CostSimConfig`, `get_config`, `is_v2_sandbox_enabled`, `is_v2_disabled_by_drift`, `get_commit_sha`

---

## cost_anomaly_detector_engine.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/cost_anomaly_detector_engine.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 990

**Docstring:** M29 Cost Anomaly Detector - Aligned Rules

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AnomalyType` |  | Cost anomaly types - minimal set. |
| `AnomalySeverity` |  | Aligned severity bands per plan. |
| `DerivedCause` |  | Deterministic cause derivation. |
| `DetectedAnomaly` |  | A detected cost anomaly. |
| `CostAnomalyDetector` | __init__, detect_all, detect_absolute_spikes, _detect_entity_spikes, _detect_tenant_spike, detect_sustained_drift, detect_budget_issues, _check_budget_threshold (+7 more) | Detects cost anomalies with aligned rules. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `classify_severity` | `(deviation_pct: float) -> AnomalySeverity` | no | Classify severity based on percentage deviation. |
| `run_anomaly_detection` | `(session, tenant_id: str) -> List[PersistedAnomaly]` | yes | Run anomaly detection and persist results. |
| `_run_anomaly_detection_with_facts` | `(session, tenant_id: str) -> dict` | yes | Run anomaly detection and emit CostAnomalyFact for HIGH anomalies. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `uuid` | uuid | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | date, datetime, timedelta | no |
| `enum` | Enum | no |
| `typing` | List, Optional | no |
| `app.hoc.cus.hoc_spine.services.time` | utc_now | no |
| `app.hoc.cus.analytics.L5_schemas.cost_anomaly_dtos` | PersistedAnomaly | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### Constants
`ABSOLUTE_SPIKE_THRESHOLD`, `CONSECUTIVE_INTERVALS_REQUIRED`, `SUSTAINED_DRIFT_THRESHOLD`, `DRIFT_DAYS_REQUIRED`, `SEVERITY_BANDS`

---

## cost_model.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/cost_model.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 455

**Docstring:** L4 Cost Model Engine - Domain Authority for Cost/Risk Estimation

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `DriftVerdict` |  | Classification of drift between V1 and V2 simulation results. |
| `StepCostEstimate` |  | Enhanced step estimate with confidence (L4 domain output). |
| `FeasibilityResult` |  | Result of feasibility check (L4 domain output). |
| `DriftAnalysis` |  | Result of drift analysis between V1 and V2 (L4 domain output). |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_skill_coefficients` | `(skill_id: str) -> Dict[str, float]` | no | Get cost model coefficients for a skill (L4 domain function). |
| `estimate_step_cost` | `(step_index: int, skill_id: str, params: Dict[str, Any]) -> StepCostEstimate` | no | Estimate cost and latency for a single step (L4 domain function). |
| `calculate_cumulative_risk` | `(risks: List[Dict[str, float]]) -> float` | no | Calculate cumulative risk from individual risk factors (L4 domain function). |
| `check_feasibility` | `(estimated_cost_cents: int, budget_cents: int, permission_gaps: List[str], cumul` | no | Check if a plan is feasible (L4 domain function). |
| `classify_drift` | `(v1_cost_cents: int, v2_cost_cents: int, v1_feasible: bool, v2_feasible: bool) -` | no | Classify drift between V1 and V2 simulation results (L4 domain function). |
| `is_significant_risk` | `(probability: float) -> bool` | no | Check if a risk factor is significant enough to report (L4 domain function). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### Constants
`DRIFT_THRESHOLD_MATCH`, `DRIFT_THRESHOLD_MINOR`, `DRIFT_THRESHOLD_MAJOR`, `DEFAULT_RISK_THRESHOLD`, `SIGNIFICANT_RISK_THRESHOLD`, `CONFIDENCE_DEGRADATION_LONG_PROMPT`, `CONFIDENCE_DEGRADATION_VERY_LONG_PROMPT`

### __all__ Exports
`SKILL_COST_COEFFICIENTS`, `UNKNOWN_SKILL_COEFFICIENTS`, `DEFAULT_RISK_THRESHOLD`, `SIGNIFICANT_RISK_THRESHOLD`, `DRIFT_THRESHOLD_MATCH`, `DRIFT_THRESHOLD_MINOR`, `DRIFT_THRESHOLD_MAJOR`, `DriftVerdict`, `StepCostEstimate`, `FeasibilityResult`, `DriftAnalysis`, `get_skill_coefficients`, `estimate_step_cost`, `calculate_cumulative_risk`, `check_feasibility`, `classify_drift`, `is_significant_risk`

---

## cost_snapshots_engine.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/cost_snapshots_engine.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 409

**Docstring:** M27 Cost Snapshots - Deterministic Enforcement Barrier

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SnapshotComputer` | __init__, compute_hourly_snapshot, compute_daily_snapshot, _compute_snapshot | Computes cost snapshots from raw cost_records. |
| `BaselineComputer` | __init__, compute_baselines | Computes rolling baselines from historical snapshots. |
| `SnapshotAnomalyDetector` | __init__, evaluate_snapshot | Detects anomalies from complete snapshots only. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `run_hourly_snapshot_job` | `(driver: CostSnapshotsDriverProtocol, tenant_ids: list[str]) -> dict` | yes | Run hourly snapshot job for multiple tenants. |
| `run_daily_snapshot_and_baseline_job` | `(driver: CostSnapshotsDriverProtocol, tenant_ids: list[str]) -> dict` | yes | Run daily snapshot and baseline computation for multiple tenants. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `hashlib` | hashlib | no |
| `logging` | logging | no |
| `datetime` | datetime, timedelta, timezone | no |
| `L5_schemas.cost_snapshot_schemas` | SEVERITY_THRESHOLDS, AnomalyEvaluation, CostSnapshot, CostSnapshotsDriverProtocol, EntityType (+4) | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

---

## cost_write.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/cost_write.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 49

**Docstring:** Cost Write Engine (L5)

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_cost_write_service` | `(session: Session) -> CostWriteService` | no | Get cost write service instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `typing` | TYPE_CHECKING | no |
| `app.hoc.cus.analytics.L6_drivers.cost_write_driver` | CostWriteDriver, get_cost_write_driver | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### __all__ Exports
`CostWriteService`, `get_cost_write_service`

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

---

## datasets_engine.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/datasets_engine.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 724

**Docstring:** Reference datasets for V2 validation.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `DatasetSample` |  | A single sample in a reference dataset. |
| `ReferenceDataset` | to_dict | A reference dataset for validation. |
| `DatasetValidator` | __init__, _build_datasets, _build_low_variance_dataset, _build_high_variance_dataset, _build_mixed_city_dataset, _build_noise_injected_dataset, _build_historical_dataset, list_datasets (+4 more) | Validator for V2 against reference datasets. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_dataset_validator` | `() -> DatasetValidator` | no | Get the global dataset validator. |
| `validate_dataset` | `(dataset_id: str) -> ValidationResult` | yes | Convenience function to validate a dataset. |
| `validate_all_datasets` | `() -> Dict[str, ValidationResult]` | yes | Convenience function to validate all datasets. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `math` | math | no |
| `random` | random | no |
| `dataclasses` | dataclass, field | no |
| `typing` | Any, Dict, List, Optional | no |
| `app.hoc.cus.analytics.L5_engines.costsim_models` | ValidationResult | no |
| `app.hoc.cus.analytics.L5_engines.v2_adapter` | CostSimV2Adapter | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

---

## divergence_engine.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/divergence_engine.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 366

**Docstring:** Cost divergence reporting between V1 and V2.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `DivergenceSample` |  | A single sample for divergence analysis. |
| `DivergenceAnalyzer` | __init__, generate_report, _load_samples, _parse_provenance_log, _calculate_metrics, _calculate_kl_divergence | Analyzer for V1 vs V2 cost divergence. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `generate_divergence_report` | `(start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, ten` | yes | Convenience function to generate a divergence report. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `math` | math | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timedelta, timezone | no |
| `typing` | Any, Dict, List, Optional | no |
| `app.hoc.cus.analytics.L5_engines.config_engine` | get_config | no |
| `app.hoc.cus.analytics.L5_engines.costsim_models` | DivergenceReport | no |
| `app.hoc.cus.analytics.L5_engines.provenance` | ProvenanceLog, get_provenance_logger | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

---

## feedback_read_engine.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/feedback_read_engine.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 181

**Docstring:** Feedback Read Engine (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `FeedbackReadEngine` | list_feedback, get_feedback, get_feedback_stats | L5 engine for feedback read operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_feedback_read_engine` | `() -> FeedbackReadEngine` | no | Get feedback read engine singleton. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, Optional | no |
| `uuid` | UUID | no |
| `app.hoc.cus.analytics.L6_drivers.feedback_read_driver` | get_feedback_read_driver | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

---

## metrics_engine.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/metrics_engine.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 107

**Docstring:** CostSim V2 Prometheus Metrics - BACKWARD COMPATIBILITY RE-EXPORTS

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_alert_rules` | `() -> str` | no | Get Prometheus alert rules YAML. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.hoc.cus.hoc_spine.services.costsim_metrics` | COST_DELTA_BUCKETS, DRIFT_SCORE_BUCKETS, DURATION_BUCKETS, CostSimMetrics, get_metrics | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### Constants
`ALERT_RULES_YAML`

### __all__ Exports
`CostSimMetrics`, `get_metrics`, `DRIFT_SCORE_BUCKETS`, `COST_DELTA_BUCKETS`, `DURATION_BUCKETS`, `ALERT_RULES_YAML`, `get_alert_rules`

---

## prediction_engine.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/prediction_engine.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 473

**Docstring:** Prediction Service (PB-S5)

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `predict_failure_likelihood` | `(driver: 'PredictionDriver', tenant_id: Optional[UUID] = None, worker_id: Option` | yes | Predict likelihood of failure for upcoming runs. |
| `predict_cost_overrun` | `(driver: 'PredictionDriver', tenant_id: Optional[UUID] = None, worker_id: Option` | yes | Predict likelihood of cost overrun for upcoming runs. |
| `emit_prediction` | `(driver: 'PredictionDriver', tenant_id: str, prediction_type: str, subject_type:` | yes | Emit a prediction event. |
| `run_prediction_cycle` | `(tenant_id: Optional[UUID] = None, session: 'AsyncSession | None' = None) -> dic` | yes | Run full prediction cycle. |
| `get_prediction_summary` | `(tenant_id: Optional[UUID] = None, prediction_type: Optional[str] = None, includ` | yes | Get prediction summary for ops visibility. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `datetime` | timedelta | no |
| `typing` | Optional | no |
| `uuid` | UUID | no |
| `app.hoc.cus.hoc_spine.services.time` | utc_now | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### Constants
`FAILURE_CONFIDENCE_THRESHOLD`, `COST_OVERRUN_THRESHOLD_PERCENT`, `PREDICTION_VALIDITY_HOURS`

---

## prediction_read_engine.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/prediction_read_engine.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 240

**Docstring:** Prediction Read Engine (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PredictionReadEngine` | list_predictions, get_prediction, get_predictions_for_subject, get_prediction_stats | L5 engine for prediction read operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_prediction_read_engine` | `() -> PredictionReadEngine` | no | Get prediction read engine singleton. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime | no |
| `typing` | Any, Optional | no |
| `uuid` | UUID | no |
| `app.hoc.cus.analytics.L6_drivers.prediction_read_driver` | get_prediction_read_driver | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

---

## sandbox_engine.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/sandbox_engine.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 308

**Docstring:** Sandbox routing layer for CostSim V1 vs V2.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SandboxResult` | production_result | Result from sandbox routing. |
| `CostSimSandbox` | __init__, _get_v2_adapter, simulate, _log_comparison | Sandbox router for CostSim V1 vs V2. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `simulate_with_sandbox` | `(plan: List[Dict[str, Any]], budget_cents: int = 1000, allowed_skills: Optional[` | yes | Convenience function for sandbox simulation. |
| `get_sandbox` | `(budget_cents: int = 1000, tenant_id: Optional[str] = None) -> CostSimSandbox` | no | Get a sandbox instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `dataclasses` | dataclass | no |
| `typing` | Any, Dict, List, Optional | no |
| `app.hoc.cus.hoc_spine.services.cross_domain_gateway` | is_v2_disabled, report_drift | no |
| `app.hoc.cus.analytics.L5_engines.config_engine` | is_v2_sandbox_enabled | no |
| `app.hoc.cus.analytics.L5_engines.costsim_models` | ComparisonResult, ComparisonVerdict, V2SimulationResult | no |
| `app.hoc.cus.analytics.L5_engines.v2_adapter` | CostSimV2Adapter | no |
| `app.worker.simulate` | CostSimulator, SimulationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

---

## v2_adapter.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/v2_adapter.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 434

**Docstring:** CostSim V2 Adapter - Enhanced simulation with confidence scoring.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `V2StepEstimate` |  | Enhanced step estimate with confidence. |
| `CostSimV2Adapter` | __init__, _get_coefficients, _estimate_step_v2, simulate, simulate_with_comparison, _compare_results | CostSim V2 Adapter with enhanced modeling. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `simulate_v2` | `(plan: List[Dict[str, Any]], budget_cents: int = 1000, allowed_skills: Optional[` | yes | Convenience function for V2 simulation. |
| `simulate_v2_with_comparison` | `(plan: List[Dict[str, Any]], budget_cents: int = 1000, allowed_skills: Optional[` | yes | Convenience function for V2 simulation with V1 comparison. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `time` | time | no |
| `dataclasses` | dataclass | no |
| `typing` | Any, Dict, List, Optional | no |
| `app.hoc.cus.analytics.L5_engines.config_engine` | get_commit_sha, get_config | no |
| `app.hoc.cus.analytics.L5_engines.costsim_models` | ComparisonResult, ComparisonVerdict, V2SimulationResult, V2SimulationStatus | no |
| `app.hoc.cus.analytics.L5_engines.provenance` | get_provenance_logger | no |
| `app.worker.simulate` | CostSimulator, SimulationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

---
