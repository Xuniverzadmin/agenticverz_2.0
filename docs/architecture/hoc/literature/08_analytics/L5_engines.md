# Analytics — L5 Engines (20 files)

**Domain:** analytics  
**Layer:** L5_engines  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

---

## ai_console_panel_engine.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/ai_console_panel_engine.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 338

**Docstring:** AI Console Panel Engine — Main orchestration for panel evaluation

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AIConsolePanelEngine` | __init__, evaluate_panel, _evaluate_panel_slots, _create_short_circuit_response, evaluate_all_panels, get_panel_ids, get_panel_spec, close | Main orchestration engine for AI Console panel evaluation. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `create_panel_engine` | `(api_base_url: Optional[str] = None) -> AIConsolePanelEngine` | yes | Create and initialize panel engine. |
| `get_panel_engine` | `() -> AIConsolePanelEngine` | yes | Get singleton panel engine. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `time` | time | no |
| `typing` | Any, Dict, List, Optional | no |
| `panel_consistency_checker` | PanelConsistencyChecker, create_consistency_checker | yes |
| `panel_dependency_resolver` | PanelDependencyResolver | yes |
| `panel_metrics_emitter` | PanelMetricsEmitter, get_panel_metrics_emitter | yes |
| `panel_response_assembler` | PanelResponseAssembler, create_response_assembler | yes |
| `panel_signal_collector` | PanelSignalCollector, create_signal_collector | yes |
| `panel_slot_evaluator` | PanelSlotEvaluator | yes |
| `panel_spec_loader` | PanelSpecLoader, get_panel_spec_loader | yes |
| `panel_types` | PanelSlotResult, SlotState, VerificationSignals | yes |
| `panel_verification_engine` | PanelVerificationEngine | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## analytics_facade.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/analytics_facade.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 639

**Docstring:** Analytics Facade (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ResolutionType` |  | Time resolution for analytics data. |
| `ScopeType` |  | Scope of analytics aggregation. |
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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## canary.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/canary.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 648

**Docstring:** Daily canary runner for CostSim V2 validation.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CanarySample` |  | A single canary test sample. |
| `CanaryRunConfig` |  | Configuration for a canary run. |
| `CanaryRunner` | __init__, run, _run_internal, _load_samples, _generate_synthetic_samples, _run_single, _calculate_metrics, _approximate_kl_divergence (+3 more) | Daily canary runner for V2 validation. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `run_canary` | `(sample_count: int = 100, drift_threshold: float = 0.2) -> CanaryReport` | yes | Convenience function to run canary. |

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
| `app.costsim.circuit_breaker` | get_circuit_breaker | no |
| `app.costsim.circuit_breaker_async` | report_drift | no |
| `app.costsim.config` | get_config | no |
| `app.costsim.leader` | LOCK_CANARY_RUNNER, leader_election | no |
| `app.costsim.models` | CanaryReport, ComparisonResult, ComparisonVerdict, DiffResult | no |
| `app.costsim.provenance` | get_provenance_logger | no |
| `app.costsim.v2_adapter` | CostSimV2Adapter | no |
| `app.worker.simulate` | CostSimulator | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## config.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/config.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 169

**Docstring:** Feature flags and configuration for CostSim V2 sandbox.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CostSimConfig` | from_env | Configuration for CostSim V2. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_config` | `() -> CostSimConfig` | no | Get the global CostSim configuration. |
| `is_v2_sandbox_enabled` | `() -> bool` | no | Check if V2 sandbox is enabled. |
| `is_v2_disabled_by_drift` | `() -> bool` | no | Check if V2 was auto-disabled due to drift. |
| `get_commit_sha` | `() -> str` | no | Get current git commit SHA. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `os` | os | no |
| `dataclasses` | dataclass | no |
| `typing` | Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## coordinator.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/coordinator.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 565

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CoordinationError` | __init__ | Raised when coordination fails in an unrecoverable way. |
| `CoordinationManager` | __init__, active_envelope_count, is_kill_switch_active, get_active_envelopes, get_audit_trail, _get_parameter_key, _emit_audit_record, check_allowed (+10 more) | C4 Multi-Envelope Coordination Manager. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.infra` | FeatureIntent, RetryPolicy | no |
| `logging` | logging | no |
| `uuid` | uuid | no |
| `datetime` | datetime, timezone | no |
| `typing` | Dict, List, Optional, Tuple | no |
| `sqlmodel` | Session | no |
| `app.optimization.audit_persistence` | persist_audit_record | no |
| `app.optimization.envelope` | CoordinationAuditRecord, CoordinationDecision, CoordinationDecisionType, Envelope, EnvelopeClass (+3) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Violations
| Import | Rule Broken | Required Fix | Line |
|--------|-------------|-------------|------|
| `from sqlmodel import Session` | L5 MUST NOT import sqlmodel at runtime | Move DB logic to L6 driver | 47 |

### Constants
`FEATURE_INTENT`, `RETRY_POLICY`

---

## cost_anomaly_detector.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/cost_anomaly_detector.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 1072

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
| `run_anomaly_detection` | `(session: Session, tenant_id: str) -> List[CostAnomaly]` | yes | Run anomaly detection and persist results. |
| `run_anomaly_detection_with_facts` | `(session: Session, tenant_id: str) -> dict` | yes | Run anomaly detection and emit CostAnomalyFact for HIGH anomalies. |
| `run_anomaly_detection_with_governance` | `(session: Session, tenant_id: str) -> dict` | yes | DEPRECATED: Use run_anomaly_detection_with_facts + AnomalyIncidentBridge. |

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
| `sqlmodel` | Session, select | no |
| `app.db` | CostAnomaly, CostBudget, utc_now | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Violations
| Import | Rule Broken | Required Fix | Line |
|--------|-------------|-------------|------|
| `from sqlmodel import Session, select` | L5 MUST NOT import sqlmodel at runtime | Move DB logic to L6 driver | 46 |
| `from app.db import CostAnomaly, CostBudget, utc_now` | L5 MUST NOT access DB directly | Use L6 driver for DB access | 48 |

### Constants
`ABSOLUTE_SPIKE_THRESHOLD`, `CONSECUTIVE_INTERVALS_REQUIRED`, `SUSTAINED_DRIFT_THRESHOLD`, `DRIFT_DAYS_REQUIRED`, `SEVERITY_BANDS`

---

## cost_model_engine.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/cost_model_engine.py`  
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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`DRIFT_THRESHOLD_MATCH`, `DRIFT_THRESHOLD_MINOR`, `DRIFT_THRESHOLD_MAJOR`, `DEFAULT_RISK_THRESHOLD`, `SIGNIFICANT_RISK_THRESHOLD`, `CONFIDENCE_DEGRADATION_LONG_PROMPT`, `CONFIDENCE_DEGRADATION_VERY_LONG_PROMPT`

### __all__ Exports
`SKILL_COST_COEFFICIENTS`, `UNKNOWN_SKILL_COEFFICIENTS`, `DEFAULT_RISK_THRESHOLD`, `SIGNIFICANT_RISK_THRESHOLD`, `DRIFT_THRESHOLD_MATCH`, `DRIFT_THRESHOLD_MINOR`, `DRIFT_THRESHOLD_MAJOR`, `DriftVerdict`, `StepCostEstimate`, `FeasibilityResult`, `DriftAnalysis`, `get_skill_coefficients`, `estimate_step_cost`, `calculate_cumulative_risk`, `check_feasibility`, `classify_drift`, `is_significant_risk`

---

## cost_snapshots.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/cost_snapshots.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 933

**Docstring:** M27 Cost Snapshots - Deterministic Enforcement Barrier

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SnapshotComputer` | __init__, compute_hourly_snapshot, compute_daily_snapshot, _compute_snapshot, _aggregate_cost_records, _get_current_baseline, _insert_snapshot, _update_snapshot (+1 more) | Computes cost snapshots from raw cost_records. |
| `BaselineComputer` | __init__, compute_baselines, _insert_baseline | Computes rolling baselines from historical snapshots. |
| `SnapshotAnomalyDetector` | __init__, evaluate_snapshot, _get_snapshot, _insert_evaluation, _create_anomaly_from_evaluation | Detects anomalies from complete snapshots only. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `run_hourly_snapshot_job` | `(session: AsyncSession, tenant_ids: list[str]) -> dict` | yes | Run hourly snapshot job for multiple tenants. |
| `run_daily_snapshot_and_baseline_job` | `(session: AsyncSession, tenant_ids: list[str]) -> dict` | yes | Run daily snapshot and baseline computation for multiple tenants. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `hashlib` | hashlib | no |
| `logging` | logging | no |
| `datetime` | datetime, timedelta, timezone | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `schemas.cost_snapshot_schemas` | SEVERITY_THRESHOLDS, AnomalyEvaluation, CostSnapshot, EntityType, SnapshotAggregate (+3) | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Violations
| Import | Rule Broken | Required Fix | Line |
|--------|-------------|-------------|------|
| `from sqlalchemy.ext.asyncio import AsyncSession` | L5 MUST NOT import sqlalchemy | Move DB logic to L6 driver | 55 |

---

## cost_write_engine.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/cost_write_engine.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 161

**Docstring:** Cost Write Engine (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CostWriteService` | __init__, create_feature_tag, update_feature_tag, create_cost_record, create_or_update_budget | DB write operations for Cost Intelligence. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | TYPE_CHECKING, Optional | no |
| `app.hoc.cus.analytics.L6_drivers.cost_write_driver` | CostWriteDriver, get_cost_write_driver | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## costsim_models.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/costsim_models.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 305

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

## datasets.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/datasets.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 723

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
| `app.costsim.models` | ValidationResult | no |
| `app.costsim.v2_adapter` | CostSimV2Adapter | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## detection_facade.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/detection_facade.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 559

**Docstring:** Detection Facade (L5 Domain Engine)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `DetectionType` |  | Types of anomaly detection. |
| `AnomalyStatus` |  | Anomaly resolution status. |
| `DetectionResult` | to_dict | Result of a detection run. |
| `AnomalyInfo` | to_dict | Anomaly information. |
| `DetectionStatusInfo` | to_dict | Detection engine status. |
| `DetectionFacade` | __init__, cost_detector, run_detection, _run_cost_detection, list_anomalies, get_anomaly, resolve_anomaly, acknowledge_anomaly (+1 more) | Facade for anomaly detection operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_detection_facade` | `() -> DetectionFacade` | no | Get the detection facade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | uuid | no |
| `app.hoc.cus.analytics.L5_engines.cost_anomaly_detector` | AnomalySeverity | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## divergence.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/divergence.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 365

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
| `app.costsim.config` | get_config | no |
| `app.costsim.models` | DivergenceReport | no |
| `app.costsim.provenance` | ProvenanceLog, get_provenance_logger | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## envelope.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/envelope.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 436

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `DeltaType` |  | How bounds are expressed. |
| `EnvelopeClass` |  | C4 Envelope Class (FROZEN priority order). |
| `BaselineSource` |  | Where baseline value comes from. |
| `EnvelopeLifecycle` |  | Fixed envelope lifecycle states. |
| `RevertReason` |  | Why an envelope was reverted. |
| `EnvelopeTrigger` |  | What prediction triggers this envelope. |
| `EnvelopeScope` |  | What this envelope affects. |
| `EnvelopeBounds` |  | Numerical bounds for the envelope. |
| `EnvelopeTimebox` |  | Time constraints for the envelope. |
| `EnvelopeBaseline` |  | Baseline value reference. |
| `EnvelopeAuditRecord` |  | Immutable audit record for envelope lifecycle. |
| `CoordinationDecisionType` |  | C4 coordination decision types. |
| `CoordinationAuditRecord` |  | C4 Coordination audit record. |
| `CoordinationDecision` |  | Result of a coordination check. |
| `Envelope` |  | Declarative optimization envelope. |
| `EnvelopeValidationError` | __init__ | Raised when envelope fails validation. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_envelope_priority` | `(envelope_class: EnvelopeClass) -> int` | no | Get the priority of an envelope class (lower number = higher priority). |
| `has_higher_priority` | `(class_a: EnvelopeClass, class_b: EnvelopeClass) -> bool` | no | Check if class_a has higher priority than class_b. |
| `validate_envelope` | `(envelope: Envelope) -> None` | no | Validate envelope against hard gate rules (V1-V5 + CI-C4-1). |
| `calculate_bounded_value` | `(baseline: float, bounds: EnvelopeBounds, prediction_confidence: float) -> float` | no | Calculate the bounded value based on prediction confidence. |
| `create_audit_record` | `(envelope: Envelope, baseline_value: float) -> EnvelopeAuditRecord` | no | Create an audit record for envelope application. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Dict, List, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## metrics.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/metrics.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 617

**Docstring:** Prometheus metrics for CostSim V2 drift detection.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CostSimMetrics` | __init__, _init_metrics, record_drift, record_cost_delta, record_schema_error, record_simulation_duration, record_simulation, set_circuit_breaker_state (+10 more) | Prometheus metrics for CostSim V2. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_metrics` | `() -> CostSimMetrics` | no | Get the global CostSim metrics instance. |
| `get_alert_rules` | `() -> str` | no | Get Prometheus alert rules YAML. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `typing` | Optional | no |
| `app.costsim.config` | get_config | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`DRIFT_SCORE_BUCKETS`, `COST_DELTA_BUCKETS`, `DURATION_BUCKETS`, `ALERT_RULES_YAML`

---

## pattern_detection.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/pattern_detection.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 409

**Docstring:** Pattern Detection Service (PB-S3)

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `compute_error_signature` | `(error: str) -> str` | no | Compute a stable signature for an error message. |
| `detect_failure_patterns` | `(driver: PatternDetectionDriver, tenant_id: Optional[UUID] = None, threshold: in` | yes | Detect repeated failure patterns. |
| `detect_cost_spikes` | `(driver: PatternDetectionDriver, tenant_id: Optional[UUID] = None, spike_thresho` | yes | Detect abnormal cost increases. |
| `emit_feedback` | `(driver: PatternDetectionDriver, feedback: PatternFeedbackCreate) -> dict` | yes | Emit a feedback record. |
| `run_pattern_detection` | `(tenant_id: Optional[UUID] = None) -> dict` | yes | Run full pattern detection cycle. |
| `get_feedback_summary` | `(tenant_id: Optional[UUID] = None, acknowledged: Optional[bool] = None, limit: i` | yes | Get feedback summary for ops visibility. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `logging` | logging | no |
| `os` | os | no |
| `datetime` | timedelta | no |
| `typing` | Optional | no |
| `uuid` | UUID | no |
| `app.hoc.cus.general.L5_utils.time` | utc_now | no |
| `app.db` | get_async_session | no |
| `app.models.feedback` | PatternFeedbackCreate | no |
| `app.hoc.cus.analytics.L6_drivers.pattern_detection_driver` | PatternDetectionDriver, get_pattern_detection_driver | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Violations
| Import | Rule Broken | Required Fix | Line |
|--------|-------------|-------------|------|
| `from app.db import get_async_session` | L5 MUST NOT access DB directly | Use L6 driver for DB access | 55 |
| `from app.models.feedback import PatternFeedbackCreate` | L5 MUST NOT import L7 models directly | Route through L6 driver | 56 |

### Constants
`FAILURE_PATTERN_THRESHOLD`, `FAILURE_PATTERN_WINDOW_HOURS`, `COST_SPIKE_THRESHOLD_PERCENT`, `COST_SPIKE_MIN_RUNS`

---

## prediction.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/prediction.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 463

**Docstring:** Prediction Service (PB-S5)

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `predict_failure_likelihood` | `(driver: 'PredictionDriver', tenant_id: Optional[UUID] = None, worker_id: Option` | yes | Predict likelihood of failure for upcoming runs. |
| `predict_cost_overrun` | `(driver: 'PredictionDriver', tenant_id: Optional[UUID] = None, worker_id: Option` | yes | Predict likelihood of cost overrun for upcoming runs. |
| `emit_prediction` | `(driver: 'PredictionDriver', tenant_id: str, prediction_type: str, subject_type:` | yes | Emit a prediction event. |
| `run_prediction_cycle` | `(tenant_id: Optional[UUID] = None) -> dict` | yes | Run full prediction cycle. |
| `get_prediction_summary` | `(tenant_id: Optional[UUID] = None, prediction_type: Optional[str] = None, includ` | yes | Get prediction summary for ops visibility. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `datetime` | timedelta | no |
| `typing` | Optional | no |
| `uuid` | UUID | no |
| `app.hoc.cus.general.L5_utils.time` | utc_now | no |
| `app.db` | get_async_session | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Violations
| Import | Rule Broken | Required Fix | Line |
|--------|-------------|-------------|------|
| `from app.db import get_async_session` | L5 MUST NOT access DB directly | Use L6 driver for DB access | 66 |

### Constants
`FAILURE_CONFIDENCE_THRESHOLD`, `COST_OVERRUN_THRESHOLD_PERCENT`, `PREDICTION_VALIDITY_HOURS`

---

## provenance.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/provenance.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 385

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
| `app.costsim.config` | get_commit_sha, get_config | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## s1_retry_backoff.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/s1_retry_backoff.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 148

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `create_s1_envelope` | `(baseline_value: float = 100.0, reference_id: str = 'retry_policy_v3') -> Envelo` | no | Create a fresh S1 envelope instance with specified baseline. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.optimization.envelope` | BaselineSource, DeltaType, Envelope, EnvelopeBaseline, EnvelopeBounds (+5) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`S1_RETRY_BACKOFF_ENVELOPE`

---

## sandbox.py
**Path:** `backend/app/hoc/cus/analytics/L5_engines/sandbox.py`  
**Layer:** L5_engines | **Domain:** analytics | **Lines:** 307

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
| `app.costsim.circuit_breaker_async` | is_v2_disabled, report_drift | no |
| `app.costsim.config` | is_v2_sandbox_enabled | no |
| `app.costsim.models` | ComparisonResult, ComparisonVerdict, V2SimulationResult | no |
| `app.costsim.v2_adapter` | CostSimV2Adapter | no |
| `app.worker.simulate` | CostSimulator, SimulationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---
