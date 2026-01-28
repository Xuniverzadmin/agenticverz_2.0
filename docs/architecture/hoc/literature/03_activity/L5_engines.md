# Activity — L5 Engines (8 files)

**Domain:** activity  
**Layer:** L5_engines  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

---

## activity_enums.py
**Path:** `backend/app/hoc/cus/activity/L5_engines/activity_enums.py`  
**Layer:** L5_engines | **Domain:** activity | **Lines:** 120

**Docstring:** Activity Domain Enums

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SignalType` |  | Canonical signal types for activity domain. |
| `SeverityLevel` | from_score, from_risk_level | Canonical severity levels for display/UI. |
| `RunState` |  | Run lifecycle state. |
| `RiskType` |  | Types of risk for threshold signals. |
| `EvidenceHealth` |  | Evidence health status. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `enum` | Enum | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### __all__ Exports
`SignalType`, `SeverityLevel`, `RunState`, `RiskType`, `EvidenceHealth`

---

## activity_facade.py
**Path:** `backend/app/hoc/cus/activity/L5_engines/activity_facade.py`  
**Layer:** L5_engines | **Domain:** activity | **Lines:** 1387

**Docstring:** Activity Facade (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyContextResult` |  | Policy context for a run. |
| `RunSummaryResult` |  | Run summary for list view. |
| `RunSummaryV2Result` |  | Run summary with policy context (V2). |
| `RunListResult` |  | Result of listing runs. |
| `RunsResult` |  | Unified result for getting runs (V2). |
| `RunDetailResult` |  | Run detail (O3) - extends summary with additional fields. |
| `RunEvidenceResult` |  | Run evidence context (O4). |
| `RunProofResult` |  | Run integrity proof (O5). |
| `StatusCount` |  | Status count item. |
| `StatusSummaryResult` |  | Summary by status. |
| `SignalProjectionResult` |  | A signal projection. |
| `SignalsResult` |  | Result of getting signals (V2). |
| `MetricsResult` |  | Activity metrics (V2). |
| `ThresholdSignalResult` |  | A threshold proximity signal. |
| `ThresholdSignalsResult` |  | Result of getting threshold signals (V2). |
| `RiskSignalsResult` |  | Risk signal aggregates. |
| `ActivityFacade` | __init__, _get_driver, _get_pattern_service, _get_cost_service, _get_attention_service, _get_feedback_service, get_runs, get_run_detail (+18 more) | Unified facade for Activity domain operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_activity_facade` | `() -> ActivityFacade` | no | Get the singleton ActivityFacade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `typing` | TYPE_CHECKING, Any | no |
| `app.hoc.cus.activity.L6_drivers.activity_read_driver` | get_activity_read_driver | no |
| `app.hoc.cus.activity.L5_engines.attention_ranking_engine` | AttentionRankingService | no |
| `app.hoc.cus.activity.L5_engines.cost_analysis_engine` | CostAnalysisService | no |
| `app.hoc.cus.activity.L5_engines.pattern_detection_engine` | PatternDetectionService | no |
| `app.hoc.cus.activity.L5_engines.signal_feedback_engine` | SignalFeedbackService, AcknowledgeResult, SuppressResult, SignalFeedbackStatus | no |
| `app.hoc.cus.activity.L5_engines.signal_identity` | compute_signal_fingerprint_from_row | no |
| `app.hoc.cus.activity.L5_engines.activity_enums` | SignalType, SeverityLevel, RunState | no |
| `app.hoc.cus.activity.L5_engines.pattern_detection_engine` | PatternDetectionResult, DetectedPattern | no |
| `app.hoc.cus.activity.L5_engines.cost_analysis_engine` | CostAnalysisResult, CostAnomaly | no |
| `app.hoc.cus.activity.L5_engines.attention_ranking_engine` | AttentionQueueResult, AttentionSignal | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## attention_ranking_engine.py
**Path:** `backend/app/hoc/cus/activity/L5_engines/attention_ranking_engine.py`  
**Layer:** L5_engines | **Domain:** activity | **Lines:** 99

**Docstring:** Attention ranking engine for prioritizing signals.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AttentionSignal` |  | A signal in the attention queue. |
| `AttentionQueueResult` |  | Result of attention queue query. |
| `AttentionRankingService` | __init__, get_attention_queue, compute_attention_score | Service for ranking and prioritizing activity signals. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime | no |
| `typing` | Any, Optional | no |
| `app.hoc.cus.general.L5_utils.time` | utc_now | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## cost_analysis_engine.py
**Path:** `backend/app/hoc/cus/activity/L5_engines/cost_analysis_engine.py`  
**Layer:** L5_engines | **Domain:** activity | **Lines:** 93

**Docstring:** Cost analysis engine for detecting cost anomalies.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CostAnomaly` |  | A detected cost anomaly. |
| `CostAnalysisResult` |  | Result of cost analysis. |
| `CostAnalysisService` | __init__, analyze_costs, get_cost_breakdown | Service for analyzing cost patterns and detecting anomalies. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime | no |
| `typing` | Optional | no |
| `app.hoc.cus.general.L5_utils.time` | utc_now | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## cus_telemetry_service.py
**Path:** `backend/app/hoc/cus/activity/L5_engines/cus_telemetry_service.py`  
**Layer:** L5_engines | **Domain:** activity | **Lines:** 77

**Docstring:** CusTelemetryService (SWEEP-03 Batch 2)

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_cus_telemetry_service` | `() -> CusTelemetryService` | no | Get the CusTelemetryService instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | TYPE_CHECKING | no |
| `app.services.cus_telemetry_engine` | BatchIngestResult, CusTelemetryEngine, IngestResult, get_cus_telemetry_engine | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### __all__ Exports
`CusTelemetryService`, `CusTelemetryEngine`, `IngestResult`, `BatchIngestResult`, `get_cus_telemetry_service`, `get_cus_telemetry_engine`

---

## pattern_detection_engine.py
**Path:** `backend/app/hoc/cus/activity/L5_engines/pattern_detection_engine.py`  
**Layer:** L5_engines | **Domain:** activity | **Lines:** 92

**Docstring:** Pattern detection engine for identifying recurring patterns.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `DetectedPattern` |  | A detected activity pattern. |
| `PatternDetectionResult` |  | Result of pattern detection. |
| `PatternDetectionService` | __init__, detect_patterns, get_pattern_detail | Service for detecting patterns in activity data. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime | no |
| `typing` | Optional | no |
| `app.hoc.cus.general.L5_utils.time` | utc_now | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## signal_feedback_engine.py
**Path:** `backend/app/hoc/cus/activity/L5_engines/signal_feedback_engine.py`  
**Layer:** L5_engines | **Domain:** activity | **Lines:** 140

**Docstring:** Signal feedback engine for user interactions with signals.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AcknowledgeResult` |  | Result of acknowledging a signal. |
| `SuppressResult` |  | Result of suppressing a signal. |
| `SignalFeedbackStatus` |  | Current feedback status for a signal. |
| `SignalFeedbackService` | __init__, acknowledge_signal, suppress_signal, get_signal_feedback_status, get_bulk_signal_feedback | Service for managing user feedback on signals. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime | no |
| `typing` | Optional | no |
| `app.hoc.cus.general.L5_utils.time` | utc_now | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## signal_identity.py
**Path:** `backend/app/hoc/cus/activity/L5_engines/signal_identity.py`  
**Layer:** L5_engines | **Domain:** activity | **Lines:** 79

**Docstring:** Signal identity utilities for fingerprinting and deduplication.

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `compute_signal_fingerprint_from_row` | `(row: dict[str, Any]) -> str` | no | Compute a stable fingerprint for a signal row. |
| `compute_signal_fingerprint` | `(signal_type: str, dimension: str, source: str, tenant_id: str) -> str` | no | Compute a stable fingerprint for signal identity fields. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `json` | json | no |
| `typing` | Any | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---
