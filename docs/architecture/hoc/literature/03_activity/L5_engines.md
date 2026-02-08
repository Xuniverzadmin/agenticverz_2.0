# Activity — L5 Engines (8 files)

**Domain:** activity  
**Layer:** L5_engines  
**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### __all__ Exports
`SignalType`, `SeverityLevel`, `RunState`, `RiskType`, `EvidenceHealth`

---

## activity_facade.py
**Path:** `backend/app/hoc/cus/activity/L5_engines/activity_facade.py`  
**Layer:** L5_engines | **Domain:** activity | **Lines:** 1731

**Docstring:** Activity Facade (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `RunEvidenceCoordinatorPort` | get_run_evidence | Protocol for run evidence coordinator (PIN-520 L5 purity). |
| `RunProofCoordinatorPort` | get_run_proof | Protocol for run proof coordinator (PIN-520 L5 purity). |
| `SignalFeedbackCoordinatorPort` | get_signal_feedback | Protocol for signal feedback coordinator (PIN-520 L5 purity). |
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
| `DimensionGroupResult` |  | A dimension group with count and percentage. |
| `DimensionBreakdownResult` |  | Dimension breakdown result. |
| `ActivityFacade` | __init__, _get_driver, _get_pattern_service, _get_cost_service, _get_attention_service, _get_feedback_service, get_runs, get_run_detail (+20 more) | Unified facade for Activity domain operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_activity_facade` | `(run_evidence_coordinator: RunEvidenceCoordinatorPort | None = None, run_proof_c` | no | Get the singleton ActivityFacade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `typing` | TYPE_CHECKING, Any, Protocol | no |
| `app.hoc.cus.activity.L6_drivers.activity_read_driver` | get_activity_read_driver | no |
| `app.hoc.cus.activity.L5_engines.attention_ranking` | AttentionRankingService | no |
| `app.hoc.cus.activity.L5_engines.cost_analysis` | CostAnalysisService | no |
| `app.hoc.cus.activity.L5_engines.pattern_detection` | PatternDetectionService | no |
| `app.hoc.cus.activity.L5_engines.signal_feedback_engine` | SignalFeedbackService, AcknowledgeResult, SuppressResult, SignalFeedbackStatus | no |
| `app.hoc.cus.activity.L5_engines.signal_identity` | compute_signal_fingerprint_from_row | no |
| `app.hoc.cus.activity.L5_engines.activity_enums` | SignalType, SeverityLevel, RunState | no |
| `app.hoc.cus.activity.L5_engines.pattern_detection` | PatternDetectionResult, DetectedPattern | no |
| `app.hoc.cus.activity.L5_engines.cost_analysis` | CostAnalysisResult, CostAnomaly | no |
| `app.hoc.cus.activity.L5_engines.attention_ranking` | AttentionQueueResult, AttentionSignal | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

---

## attention_ranking.py
**Path:** `backend/app/hoc/cus/activity/L5_engines/attention_ranking.py`  
**Layer:** L5_engines | **Domain:** activity | **Lines:** 110

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
| `app.hoc.cus.hoc_spine.services.time` | utc_now | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

---

## cost_analysis.py
**Path:** `backend/app/hoc/cus/activity/L5_engines/cost_analysis.py`  
**Layer:** L5_engines | **Domain:** activity | **Lines:** 95

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
| `app.hoc.cus.hoc_spine.services.time` | utc_now | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

---

## cus_telemetry_engine.py
**Path:** `backend/app/hoc/cus/activity/L5_engines/cus_telemetry_engine.py`  
**Layer:** L5_engines | **Domain:** activity | **Lines:** 384

**Docstring:** Customer Telemetry Engine

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IngestResult` |  | Result of single usage ingestion. |
| `BatchIngestResult` |  | Result of batch usage ingestion. |
| `CusTelemetryEngine` | __init__, ingest_usage, ingest_batch, get_usage_summary, get_usage_history, get_daily_aggregates, compute_daily_aggregates | L4 engine for customer telemetry decisions. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_cus_telemetry_engine` | `() -> CusTelemetryEngine` | no | Get engine instance with default driver. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | date | no |
| `typing` | TYPE_CHECKING, Any, Dict, List, Optional (+1) | no |
| `app.schemas.cus_schemas` | CusIntegrationUsage, CusLLMUsageIngest, CusLLMUsageResponse, CusUsageSummary | no |
| `app.hoc.cus.activity.L6_drivers.cus_telemetry_driver` | CusTelemetryDriver, get_cus_telemetry_driver | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

---

## pattern_detection.py
**Path:** `backend/app/hoc/cus/activity/L5_engines/pattern_detection.py`  
**Layer:** L5_engines | **Domain:** activity | **Lines:** 94

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
| `app.hoc.cus.hoc_spine.services.time` | utc_now | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

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
| `app.hoc.cus.hoc_spine.services.time` | utc_now | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

---
