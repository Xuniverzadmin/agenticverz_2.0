# Activity — L5 Engines (4 files)

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
| `app.hoc.cus.hoc_spine.services.time` | utc_now | no |

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
