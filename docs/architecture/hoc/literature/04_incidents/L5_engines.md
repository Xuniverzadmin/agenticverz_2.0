# Incidents — L5 Engines (14 files)

**Domain:** incidents  
**Layer:** L5_engines  
**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

**Layer Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

---

## anomaly_bridge.py
**Path:** `backend/app/hoc/cus/incidents/L5_engines/anomaly_bridge.py`  
**Layer:** L5_engines | **Domain:** incidents | **Lines:** 297

**Docstring:** Anomaly-to-Incident Bridge

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AnomalyIncidentBridge` | __init__, ingest, _meets_severity_threshold, _is_suppressed, _check_existing_incident, _create_incident | Bridge that accepts cost anomaly facts and creates incidents. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_anomaly_incident_bridge` | `(session) -> AnomalyIncidentBridge` | no | Factory function to get AnomalyIncidentBridge instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `uuid` | uuid | no |
| `datetime` | datetime, timezone | no |
| `decimal` | Decimal | no |
| `typing` | Optional | no |
| `app.errors.governance` | GovernanceError | no |
| `app.hoc.cus.incidents.L6_drivers.incident_write_driver` | IncidentWriteDriver, get_incident_write_driver | no |
| `app.metrics` | governance_incidents_created_total | no |
| `app.hoc.cus.hoc_spine.schemas.anomaly_types` | CostAnomalyFact | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### Constants
`INCIDENT_SEVERITY_THRESHOLD`, `ANOMALY_SEVERITY_MAP`, `ANOMALY_TRIGGER_TYPE_MAP`

### __all__ Exports
`AnomalyIncidentBridge`, `get_anomaly_incident_bridge`, `INCIDENT_SEVERITY_THRESHOLD`

---

## export_engine.py
**Path:** `backend/app/hoc/cus/incidents/L5_engines/export_engine.py`  
**Layer:** L5_engines | **Domain:** incidents | **Lines:** 225

**Docstring:** Export Engine (PIN-511 Phase 2.1)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ExportEngine` | __init__, export_evidence, export_soc2, export_executive_debrief, export_with_integrity | L5 engine for incident export operations. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Any, Dict, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

---

## hallucination_detector.py
**Path:** `backend/app/hoc/cus/incidents/L5_engines/hallucination_detector.py`  
**Layer:** L5_engines | **Domain:** incidents | **Lines:** 467

**Docstring:** Module: hallucination_detector

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `HallucinationType` |  | Types of hallucination indicators. |
| `HallucinationSeverity` |  | Severity levels for hallucination detections. |
| `HallucinationIndicator` | to_dict | Individual hallucination indicator. |
| `HallucinationResult` | to_incident_data, _derive_severity | Result of hallucination detection. |
| `HallucinationConfig` |  | Configuration for hallucination detection. |
| `HallucinationDetector` | __init__, detect, _detect_suspicious_urls, _detect_suspicious_citations, _detect_contradictions, _detect_temporal_issues, _hash_content | Hallucination detection service. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `create_detector_for_tenant` | `(tenant_config: Optional[dict[str, Any]] = None) -> HallucinationDetector` | no | Create a detector configured for a specific tenant. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `re` | re | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

---

## incident_engine.py
**Path:** `backend/app/hoc/cus/incidents/L5_engines/incident_engine.py`  
**Layer:** L5_engines | **Domain:** incidents | **Lines:** 910

**Docstring:** Incident Engine (L4 Domain Logic)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IncidentEngine` | __init__, _get_driver, _check_policy_suppression, _write_prevention_record, create_incident_for_run, create_incident_for_failed_run, _maybe_create_policy_proposal, _generate_title (+4 more) | L4 Domain Engine for incident creation. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_incident_engine` | `(evidence_recorder: Any = None) -> IncidentEngine` | no | Get or create singleton incident engine instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `uuid` | uuid | no |
| `datetime` | datetime, timezone | no |
| `typing` | TYPE_CHECKING, Any, Dict, List, Optional | no |
| `app.hoc.cus.hoc_spine.services.time` | utc_now | no |
| `app.hoc.cus.incidents.L6_drivers.incident_write_driver` | IncidentWriteDriver, get_incident_write_driver | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### Constants
`INCIDENT_OUTCOME_SUCCESS`, `INCIDENT_OUTCOME_FAILURE`, `INCIDENT_OUTCOME_BLOCKED`, `INCIDENT_OUTCOME_ABORTED`, `SEVERITY_NONE`, `FAILURE_SEVERITY_MAP`, `FAILURE_CATEGORY_MAP`

---

## incident_pattern.py
**Path:** `backend/app/hoc/cus/incidents/L5_engines/incident_pattern.py`  
**Layer:** L5_engines | **Domain:** incidents | **Lines:** 281

**Docstring:** Incident Pattern Engine - L4 Domain Logic

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PatternMatch` |  | A detected incident pattern. |
| `PatternResult` |  | Result of pattern detection. |
| `IncidentPatternService` | __init__, detect_patterns, _detect_category_clusters, _detect_severity_spikes, _detect_cascade_failures | Detect structural patterns across incidents. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timedelta | no |
| `typing` | TYPE_CHECKING, Optional | no |
| `app.hoc.cus.incidents.L6_drivers.incident_pattern_driver` | IncidentPatternDriver, get_incident_pattern_driver | no |
| `app.hoc.cus.hoc_spine.services.time` | utc_now | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

---

## incident_read_engine.py
**Path:** `backend/app/hoc/cus/incidents/L5_engines/incident_read_engine.py`  
**Layer:** L5_engines | **Domain:** incidents | **Lines:** 153

**Docstring:** Incident Read Service (L4)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IncidentReadService` | __init__, list_incidents, get_incident, get_incident_events, count_incidents_since, get_last_incident | L4 service for incident read operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_incident_read_service` | `(session: 'Session') -> IncidentReadService` | no | Factory function to get IncidentReadService instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime | no |
| `typing` | TYPE_CHECKING, List, Optional, Tuple | no |
| `app.hoc.cus.incidents.L6_drivers.incident_read_driver` | IncidentReadDriver, get_incident_read_driver | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### __all__ Exports
`IncidentReadService`, `get_incident_read_service`

---

## incident_write_engine.py
**Path:** `backend/app/hoc/cus/incidents/L5_engines/incident_write_engine.py`  
**Layer:** L5_engines | **Domain:** incidents | **Lines:** 317

**Docstring:** Incident Write Service (L4)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IncidentWriteService` | __init__, acknowledge_incident, resolve_incident, manual_close_incident | L5 engine for incident write operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_incident_write_service` | `(session: 'Session', audit: Any = None) -> IncidentWriteService` | no | Factory function to get IncidentWriteService instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timezone | no |
| `typing` | TYPE_CHECKING, Any, Optional | no |
| `app.hoc.cus.incidents.L6_drivers.incident_write_driver` | IncidentWriteDriver, get_incident_write_driver | no |
| `app.hoc.cus.hoc_spine.schemas.domain_enums` | ActorType | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### __all__ Exports
`IncidentWriteService`, `get_incident_write_service`

---

## incidents_facade.py
**Path:** `backend/app/hoc/cus/incidents/L5_engines/incidents_facade.py`  
**Layer:** L5_engines | **Domain:** incidents | **Lines:** 1195

**Docstring:** Incidents Domain Facade (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IncidentSummaryResult` |  | Incident summary for list view (O2). |
| `PaginationResult` |  | Pagination metadata. |
| `IncidentListResult` |  | Incidents list response. |
| `IncidentDetailResult` |  | Incident detail response (O3). |
| `IncidentsByRunResult` |  | Incidents by run response. |
| `PatternMatchResult` |  | A detected incident pattern. |
| `PatternDetectionResult` |  | Pattern detection response. |
| `RecurrenceGroupResult` |  | A group of recurring incidents. |
| `RecurrenceAnalysisResult` |  | Recurrence analysis response. |
| `CostImpactSummaryResult` |  | Cost impact summary for an incident category. |
| `CostImpactResult` |  | Cost impact analysis response. |
| `IncidentMetricsResult` |  | Incident metrics response. |
| `HistoricalTrendDataPointResult` |  | A single data point in a historical trend. |
| `HistoricalTrendResult` |  | Historical trend response. |
| `HistoricalDistributionEntryResult` |  | A single entry in the distribution. |
| `HistoricalDistributionResult` |  | Historical distribution response. |
| `CostTrendDataPointResult` |  | A single data point in the cost trend. |
| `CostTrendResult` |  | Cost trend response. |
| `LearningInsightResult` |  | A learning insight from incident analysis. |
| `ResolutionSummaryResult` |  | Summary of incident resolution. |
| `LearningsResult` |  | Incident learnings response. |
| `IncidentsFacade` | list_active_incidents, list_resolved_incidents, list_historical_incidents, list_incidents, get_incident_detail, get_incidents_for_run, get_metrics, analyze_cost_impact (+7 more) | Unified facade for incident management. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_incidents_facade` | `() -> IncidentsFacade` | no | Get the singleton IncidentsFacade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timedelta, timezone | no |
| `typing` | TYPE_CHECKING, Any, Optional | no |
| `app.hoc.cus.incidents.L6_drivers.incidents_facade_driver` | IncidentsFacadeDriver, IncidentSnapshot | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### __all__ Exports
`IncidentsFacade`, `get_incidents_facade`, `IncidentSummaryResult`, `PaginationResult`, `IncidentListResult`, `IncidentDetailResult`, `IncidentsByRunResult`, `PatternMatchResult`, `PatternDetectionResult`, `RecurrenceGroupResult`, `RecurrenceAnalysisResult`, `CostImpactSummaryResult`, `CostImpactResult`, `IncidentMetricsResult`, `HistoricalTrendDataPointResult`, `HistoricalTrendResult`, `HistoricalDistributionEntryResult`, `HistoricalDistributionResult`, `CostTrendDataPointResult`, `CostTrendResult`, `LearningInsightResult`, `ResolutionSummaryResult`, `LearningsResult`

---

## incidents_types.py
**Path:** `backend/app/hoc/cus/incidents/L5_engines/incidents_types.py`  
**Layer:** L5_engines | **Domain:** incidents | **Lines:** 44

**Docstring:** Incidents Domain Shared Types

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime | no |
| `typing` | Callable | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### __all__ Exports
`UuidFn`, `ClockFn`

---

## policy_violation_engine.py
**Path:** `backend/app/hoc/cus/incidents/L5_engines/policy_violation_engine.py`  
**Layer:** L5_engines | **Domain:** incidents | **Lines:** 725

**Docstring:** Policy Violation Service - S3 Hardening for Phase A.5 Verification

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ViolationFact` |  | Authoritative violation fact - must be persisted before incident creation. |
| `ViolationIncident` |  | Result of creating an incident from a violation. |
| `PolicyViolationService` | __init__, persist_violation_fact, check_violation_persisted, check_policy_enabled, persist_evidence, check_incident_exists, create_incident_from_violation, persist_violation_and_create_incident (+1 more) | Service for handling policy violations with S3 truth guarantees. |
| `PolicyEvaluationResult` |  | Result of policy evaluation (PIN-407: Success as First-Class Data). |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `create_policy_evaluation_record` | `(session: 'AsyncSession', run_id: str, tenant_id: str, outcome: str, policies_ch` | yes | Create a policy evaluation record for ANY run (PIN-407). |
| `handle_policy_evaluation_for_run` | `(session: 'AsyncSession', run_id: str, tenant_id: str, run_status: str, policies` | yes | Create a policy evaluation record for ANY run (PIN-407). |
| `handle_policy_violation` | `(session: 'AsyncSession', run_id: str, tenant_id: str, policy_type: str, policy_` | yes | Handle a policy violation with S3 truth guarantees. |
| `create_policy_evaluation_sync` | `(run_id: str, tenant_id: str, run_status: str, policies_checked: int = 0, is_syn` | no | Create a policy evaluation record for ANY run (PIN-407) - SYNC VERSION. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `decimal` | Decimal | no |
| `typing` | TYPE_CHECKING, Any, Dict, Optional | no |
| `app.hoc.cus.incidents.L6_drivers.policy_violation_driver` | PolicyViolationDriver, get_policy_violation_driver | no |
| `app.utils.runtime` | generate_uuid | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### Constants
`VERIFICATION_MODE`, `POLICY_OUTCOME_NO_VIOLATION`, `POLICY_OUTCOME_VIOLATION`, `POLICY_OUTCOME_ADVISORY`, `POLICY_OUTCOME_NOT_APPLICABLE`

---

## postmortem.py
**Path:** `backend/app/hoc/cus/incidents/L5_engines/postmortem.py`  
**Layer:** L5_engines | **Domain:** incidents | **Lines:** 466

**Docstring:** Post-Mortem Engine - L4 Domain Logic

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ResolutionSummary` |  | Summary of how an incident was resolved. |
| `LearningInsight` |  | A learning extracted from incident analysis. |
| `PostMortemResult` |  | Result of post-mortem analysis for an incident. |
| `CategoryLearnings` |  | Aggregated learnings for a category. |
| `PostMortemService` | __init__, get_incident_learnings, get_category_learnings, _get_resolution_summary, _find_similar_incidents, _extract_insights, _generate_category_insights | Extract learnings and post-mortem insights from incidents. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `typing` | TYPE_CHECKING, Optional | no |
| `app.hoc.cus.incidents.L6_drivers.postmortem_driver` | PostMortemDriver, get_postmortem_driver | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

---

## recovery_rule_engine.py
**Path:** `backend/app/hoc/cus/incidents/L5_engines/recovery_rule_engine.py`  
**Layer:** L5_engines | **Domain:** incidents | **Lines:** 802

**Docstring:** Rule-based evaluation engine for recovery suggestions.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `RuleContext` | to_dict | Context provided to rules for evaluation. |
| `RuleResult` | to_dict | Result from evaluating a single rule. |
| `EvaluationResult` | to_dict | Complete result from rule evaluation. |
| `Rule` | __init__, evaluate, __repr__ | Base class for recovery rules. |
| `ErrorCodeRule` | __init__, evaluate | Match based on error code patterns. |
| `HistoricalPatternRule` | __init__, evaluate | Match based on historical success patterns. |
| `SkillSpecificRule` | __init__, evaluate | Rules specific to certain skills. |
| `OccurrenceThresholdRule` | __init__, evaluate | Escalate based on occurrence count. |
| `CompositeRule` | __init__, evaluate | Combine multiple rules with AND/OR logic. |
| `RecoveryRuleEngine` | __init__, add_rule, remove_rule, evaluate | Evaluates rules against failure context to recommend recovery actions. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `combine_confidences` | `(rule_confidence: float, match_confidence: float) -> float` | no | Combine rule and matcher confidence scores. |
| `should_select_action` | `(combined_confidence: float) -> bool` | no | Determine if an action should be selected based on combined confidence. |
| `should_auto_execute` | `(confidence: float) -> bool` | no | Determine if a recovery action should be auto-executed based on confidence. |
| `classify_error_category` | `(error_codes: List[str]) -> str` | no | Classify error codes into a category. |
| `suggest_recovery_mode` | `(error_codes: List[str]) -> str` | no | Suggest a recovery mode based on error codes. |
| `evaluate_rules` | `(error_code: str, error_message: str, skill_id: Optional[str] = None, tenant_id:` | no | Convenience function to evaluate rules against a failure. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `time` | time | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any, Dict, List, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### Constants
`DEBUG_MODE`

### __all__ Exports
`Rule`, `RuleContext`, `RuleResult`, `EvaluationResult`, `ErrorCodeRule`, `HistoricalPatternRule`, `SkillSpecificRule`, `OccurrenceThresholdRule`, `CompositeRule`, `RecoveryRuleEngine`, `evaluate_rules`, `DEFAULT_RULES`, `AUTO_EXECUTE_CONFIDENCE_THRESHOLD`, `should_auto_execute`, `ERROR_CATEGORY_RULES`, `classify_error_category`, `RECOVERY_MODE_RULES`, `suggest_recovery_mode`, `ACTION_SELECTION_THRESHOLD`, `combine_confidences`, `should_select_action`

---

## recurrence_analysis.py
**Path:** `backend/app/hoc/cus/incidents/L5_engines/recurrence_analysis.py`  
**Layer:** L5_engines | **Domain:** incidents | **Lines:** 191

**Docstring:** Recurrence Analysis Service (L4 Engine)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `RecurrenceGroup` |  | A group of recurring incidents. |
| `RecurrenceResult` |  | Result of recurrence analysis. |
| `RecurrenceAnalysisService` | __init__, analyze_recurrence, get_recurrence_for_category, _snapshot_to_group | Analyze recurring incident patterns. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime | no |
| `typing` | TYPE_CHECKING | no |
| `app.hoc.cus.hoc_spine.services.time` | utc_now | no |
| `app.hoc.cus.incidents.L6_drivers.recurrence_analysis_driver` | RecurrenceAnalysisDriver, RecurrenceGroupSnapshot | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

---

## semantic_failures.py
**Path:** `backend/app/hoc/cus/incidents/L5_engines/semantic_failures.py`  
**Layer:** L5_engines | **Domain:** incidents | **Lines:** 298

**Docstring:** Semantic Failures — Canonical failure taxonomy for two-phase validation.

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_failure_info` | `(code: FailureCode) -> Dict[str, Any]` | no | Get failure taxonomy info for a code (INT-* or SEM-*). |
| `get_fix_owner` | `(code: FailureCode) -> str` | no | Get the fix owner for a failure code. |
| `get_fix_action` | `(code: FailureCode) -> str` | no | Get the fix action for a failure code. |
| `get_violation_class` | `(code: FailureCode) -> ViolationClass` | no | Get the violation class for a failure code. |
| `format_violation_message` | `(code: FailureCode, context_msg: str) -> str` | no | Format a violation message with context. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, Dict, Union | no |
| `semantic_types` | FailureCode, IntentFailureCode, SemanticFailureCode, SemanticSeverity, ViolationClass | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### Constants
`SEMANTIC_FAILURE_TAXONOMY`, `INTENT_FAILURE_TAXONOMY`

---
