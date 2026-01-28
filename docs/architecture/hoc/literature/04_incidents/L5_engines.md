# Incidents — L5 Engines (16 files)

**Domain:** incidents  
**Layer:** L5_engines  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## incident_driver.py
**Path:** `backend/app/hoc/cus/incidents/L5_engines/incident_driver.py`  
**Layer:** L5_engines | **Domain:** incidents | **Lines:** 279

**Docstring:** Incident Domain Driver (INTERNAL)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IncidentDriver` | __init__, _engine, check_and_create_incident, create_incident_for_run, _emit_ack, get_incidents_for_run | Driver for Incident domain operations (INTERNAL). |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_incident_driver` | `(db_url: Optional[str] = None) -> IncidentDriver` | no | Get the incident driver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | UUID | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`RAC_ENABLED`

---

## incident_engine.py
**Path:** `backend/app/hoc/cus/incidents/L5_engines/incident_engine.py`  
**Layer:** L5_engines | **Domain:** incidents | **Lines:** 905

**Docstring:** Incident Engine (L4 Domain Logic)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IncidentEngine` | __init__, _get_driver, _check_policy_suppression, _write_prevention_record, create_incident_for_run, create_incident_for_failed_run, _maybe_create_policy_proposal, _generate_title (+4 more) | L4 Domain Engine for incident creation. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_get_lessons_learned_engine` | `()` | no | Get the LessonsLearnedEngine singleton (lazy import). |
| `get_incident_engine` | `() -> IncidentEngine` | no | Get or create singleton incident engine instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `uuid` | uuid | no |
| `datetime` | datetime, timezone | no |
| `typing` | TYPE_CHECKING, Any, Dict, List, Optional | no |
| `app.hoc.cus.general.L5_utils.time` | utc_now | no |
| `app.hoc.cus.incidents.L6_drivers.incident_write_driver` | IncidentWriteDriver, get_incident_write_driver | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`INCIDENT_OUTCOME_SUCCESS`, `INCIDENT_OUTCOME_FAILURE`, `INCIDENT_OUTCOME_BLOCKED`, `INCIDENT_OUTCOME_ABORTED`, `SEVERITY_NONE`, `FAILURE_SEVERITY_MAP`, `FAILURE_CATEGORY_MAP`

---

## incident_pattern_engine.py
**Path:** `backend/app/hoc/cus/incidents/L5_engines/incident_pattern_engine.py`  
**Layer:** L5_engines | **Domain:** incidents | **Lines:** 279

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
| `app.hoc.cus.general.L5_utils.time` | utc_now | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### __all__ Exports
`IncidentReadService`, `get_incident_read_service`

---

## incident_severity_engine.py
**Path:** `backend/app/hoc/cus/incidents/L5_engines/incident_severity_engine.py`  
**Layer:** L5_engines | **Domain:** incidents | **Lines:** 218

**Docstring:** Incident Severity Engine (L4)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SeverityConfig` | default | Configuration for severity decisions. |
| `IncidentSeverityEngine` | __init__, get_initial_severity, calculate_severity_for_calls, should_escalate | L4 Engine for incident severity decisions. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `generate_incident_title` | `(trigger_type: str, trigger_value: str) -> str` | no | Generate human-readable incident title. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `typing` | Dict, Tuple | no |
| `app.models.killswitch` | IncidentSeverity | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Violations
| Import | Rule Broken | Required Fix | Line |
|--------|-------------|-------------|------|
| `from app.models.killswitch import IncidentSeverity` | L5 MUST NOT import L7 models directly | Route through L6 driver | 39 |

### Constants
`DEFAULT_SEVERITY`

### __all__ Exports
`IncidentSeverityEngine`, `SeverityConfig`, `TRIGGER_SEVERITY_MAP`, `DEFAULT_SEVERITY`, `generate_incident_title`

---

## incident_write_engine.py
**Path:** `backend/app/hoc/cus/incidents/L5_engines/incident_write_engine.py`  
**Layer:** L5_engines | **Domain:** incidents | **Lines:** 303

**Docstring:** Incident Write Service (L4)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IncidentWriteService` | __init__, acknowledge_incident, resolve_incident, manual_close_incident | L4 service for incident write operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_incident_write_service` | `(session: 'Session') -> IncidentWriteService` | no | Factory function to get IncidentWriteService instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timezone | no |
| `typing` | TYPE_CHECKING, Optional | no |
| `app.hoc.cus.incidents.L6_drivers.incident_write_driver` | IncidentWriteDriver, get_incident_write_driver | no |
| `app.models.audit_ledger` | ActorType | no |
| `app.hoc.cus.logs.L5_engines.audit_ledger_service` | AuditLedgerService | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Violations
| Import | Rule Broken | Required Fix | Line |
|--------|-------------|-------------|------|
| `from app.models.audit_ledger import ActorType` | L5 MUST NOT import L7 models directly | Route through L6 driver | 57 |

### __all__ Exports
`IncidentWriteService`, `get_incident_write_service`

---

## incidents_facade.py
**Path:** `backend/app/hoc/cus/incidents/L5_engines/incidents_facade.py`  
**Layer:** L5_engines | **Domain:** incidents | **Lines:** 983

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
| `IncidentsFacade` | list_active_incidents, list_resolved_incidents, list_historical_incidents, get_incident_detail, get_incidents_for_run, get_metrics, analyze_cost_impact, _snapshot_to_summary (+3 more) | Unified facade for incident management. |

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### __all__ Exports
`UuidFn`, `ClockFn`

---

## llm_failure_engine.py
**Path:** `backend/app/hoc/cus/incidents/L5_engines/llm_failure_engine.py`  
**Layer:** L5_engines | **Domain:** incidents | **Lines:** 348

**Docstring:** LLMFailureService - S4 Failure Truth Implementation

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `LLMFailureFact` | __post_init__ | Authoritative LLM failure fact. |
| `LLMFailureResult` |  | Result of failure persistence operation. |
| `LLMFailureService` | __init__, persist_failure_and_mark_run, _persist_failure, _capture_evidence, _mark_run_failed, _verify_no_contamination, get_failure_by_run_id | Service for handling LLM failures with S4 truth guarantees. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `os` | os | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime | no |
| `typing` | TYPE_CHECKING, Any, Callable, Dict, Optional | no |
| `app.hoc.cus.incidents.L6_drivers.llm_failure_driver` | LLMFailureDriver, get_llm_failure_driver | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`VERIFICATION_MODE`

---

## policy_violation_engine.py
**Path:** `backend/app/hoc/cus/incidents/L5_engines/policy_violation_engine.py`  
**Layer:** L5_engines | **Domain:** incidents | **Lines:** 713

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
| `app.hoc.cus.incidents.L6_drivers.policy_violation_driver` | PolicyViolationDriver, get_policy_violation_driver, insert_policy_evaluation_sync | no |
| `app.utils.runtime` | generate_uuid | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`VERIFICATION_MODE`, `POLICY_OUTCOME_NO_VIOLATION`, `POLICY_OUTCOME_VIOLATION`, `POLICY_OUTCOME_ADVISORY`, `POLICY_OUTCOME_NOT_APPLICABLE`

---

## postmortem_engine.py
**Path:** `backend/app/hoc/cus/incidents/L5_engines/postmortem_engine.py`  
**Layer:** L5_engines | **Domain:** incidents | **Lines:** 444

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## prevention_engine.py
**Path:** `backend/app/hoc/cus/incidents/L5_engines/prevention_engine.py`  
**Layer:** L5_engines | **Domain:** incidents | **Lines:** 890

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyType` |  | Types of policies that can be evaluated. |
| `Severity` |  | Severity levels for policy violations. |
| `PreventionAction` |  | Action to take when prevention triggers. |
| `PolicyViolation` | to_dict | A single policy violation detected. |
| `PreventionContext` | hash_output | Context for prevention evaluation. |
| `PreventionResult` | highest_severity, primary_violation, to_dict | Result of prevention engine evaluation. |
| `BaseValidator` | validate | Base class for policy validators. |
| `ContentAccuracyValidatorV2` | __init__, validate, _get_value, _extract_claim | Enhanced content accuracy validator. |
| `PIIValidator` | __init__, validate, _redact | Detects PII in LLM output that shouldn't be exposed. |
| `SafetyValidator` | __init__, validate | Detects harmful, dangerous, or inappropriate content. |
| `HallucinationValidator` | __init__, validate, _claim_in_context | Detects potential hallucinations by checking for unsupported claims. |
| `BudgetValidator` | __init__, validate | Validates that response doesn't exceed budget limits. |
| `PreventionEngine` | __init__, evaluate, _generate_safe_response, _emit_metrics | Multi-policy prevention engine with severity levels and async incident creation. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_prevention_engine` | `() -> PreventionEngine` | no | Get global prevention engine instance. |
| `evaluate_prevention` | `(tenant_id: str, call_id: str, user_query: str, llm_output: str, context_data: D` | no | Convenience function to evaluate prevention. |
| `create_incident_from_violation` | `(ctx: PreventionContext, result: PreventionResult, session: Optional[Any] = None` | yes | Create an incident from prevention violation. |
| `_create_incident_with_service` | `(session: Any, ctx: PreventionContext, primary: PolicyViolation, evidence: dict)` | yes | Helper to create incident using PolicyViolationService. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `re` | re | no |
| `time` | time | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional, Set | no |
| `uuid` | uuid4 | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### __all__ Exports
`PolicyType`, `Severity`, `PreventionAction`, `PolicyViolation`, `PreventionContext`, `PreventionResult`, `BaseValidator`, `ContentAccuracyValidatorV2`, `PIIValidator`, `SafetyValidator`, `HallucinationValidator`, `BudgetValidator`, `PreventionEngine`, `get_prevention_engine`, `evaluate_prevention`, `create_incident_from_violation`

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`DEBUG_MODE`

### __all__ Exports
`Rule`, `RuleContext`, `RuleResult`, `EvaluationResult`, `ErrorCodeRule`, `HistoricalPatternRule`, `SkillSpecificRule`, `OccurrenceThresholdRule`, `CompositeRule`, `RecoveryRuleEngine`, `evaluate_rules`, `DEFAULT_RULES`, `AUTO_EXECUTE_CONFIDENCE_THRESHOLD`, `should_auto_execute`, `ERROR_CATEGORY_RULES`, `classify_error_category`, `RECOVERY_MODE_RULES`, `suggest_recovery_mode`, `ACTION_SELECTION_THRESHOLD`, `combine_confidences`, `should_select_action`

---

## recurrence_analysis_engine.py
**Path:** `backend/app/hoc/cus/incidents/L5_engines/recurrence_analysis_engine.py`  
**Layer:** L5_engines | **Domain:** incidents | **Lines:** 189

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
| `app.hoc.cus.general.L5_utils.time` | utc_now | no |
| `app.hoc.cus.incidents.L6_drivers.recurrence_analysis_driver` | RecurrenceAnalysisDriver, RecurrenceGroupSnapshot | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`SEMANTIC_FAILURE_TAXONOMY`, `INTENT_FAILURE_TAXONOMY`

---
