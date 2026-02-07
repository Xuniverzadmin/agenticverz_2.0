# Incidents — Domain Capability

**Domain:** incidents  
**Total functions:** 267  
**Generator:** `scripts/ops/hoc_capability_doc_generator.py`

---

## Reality Delta (2026-02-07)

- L2 purity preserved: incidents L2 routes dispatch via L4 `OperationRegistry` (no direct L2→L5).
- `policy_violation_engine.py` supports an L4-owned connection path; the legacy L5-owned psycopg2 connection+commit path still exists and remains a known exception until removed.
- Remaining clean-arch debt (mechanical audit): L5 imports `app.models.*` in write paths (`incident_write_engine.py`, `severity_policy.py`).
- Verify now: `python3 scripts/ops/hoc_l5_l6_purity_audit.py --domain incidents`.

## 1. Domain Purpose

Incident lifecycle management — detection, classification, severity assessment, postmortem analysis, prevention rules, and recurrence tracking.

## 2. Customer-Facing Operations

| Function | File | L4 Wired | Entry Point | Side Effects |
|----------|------|----------|-------------|--------------|
| `CompositeRule.evaluate` | recovery_rule_engine | No (gap) | L2:recovery | pure |
| `ErrorCodeRule.evaluate` | recovery_rule_engine | No (gap) | L2:recovery | pure |
| `EvaluationResult.to_dict` | recovery_rule_engine | No (gap) | L2:recovery | pure |
| `HistoricalPatternRule.evaluate` | recovery_rule_engine | No (gap) | L2:recovery | pure |
| `IncidentDriver.check_and_create_incident` | incident_driver | Yes | L4:transaction_coordinator | pure |
| `IncidentDriver.create_incident_for_run` | incident_driver | Yes | L4:transaction_coordinator | pure |
| `IncidentDriver.get_incidents_for_run` | incident_driver | Yes | L4:transaction_coordinator | pure |
| `IncidentsFacade.analyze_cost_impact` | incidents_facade | Yes | L4:incidents_handler | pure |
| `IncidentsFacade.analyze_recurrence` | incidents_facade | Yes | L4:incidents_handler | pure |
| `IncidentsFacade.detect_patterns` | incidents_facade | Yes | L4:incidents_handler | pure |
| `IncidentsFacade.get_incident_detail` | incidents_facade | Yes | L4:incidents_handler | pure |
| `IncidentsFacade.get_incident_learnings` | incidents_facade | Yes | L4:incidents_handler | pure |
| `IncidentsFacade.get_incidents_for_run` | incidents_facade | Yes | L4:incidents_handler | pure |
| `IncidentsFacade.get_metrics` | incidents_facade | Yes | L4:incidents_handler | pure |
| `IncidentsFacade.list_active_incidents` | incidents_facade | Yes | L4:incidents_handler | pure |
| `IncidentsFacade.list_historical_incidents` | incidents_facade | Yes | L4:incidents_handler | pure |
| `IncidentsFacade.list_resolved_incidents` | incidents_facade | Yes | L4:incidents_handler | pure |
| `OccurrenceThresholdRule.evaluate` | recovery_rule_engine | No (gap) | L2:recovery | pure |
| `RecoveryRuleEngine.add_rule` | recovery_rule_engine | No (gap) | L2:recovery | pure |
| `RecoveryRuleEngine.evaluate` | recovery_rule_engine | No (gap) | L2:recovery | pure |
| `RecoveryRuleEngine.remove_rule` | recovery_rule_engine | No (gap) | L2:recovery | pure |
| `Rule.evaluate` | recovery_rule_engine | No (gap) | L2:recovery | pure |
| `RuleContext.to_dict` | recovery_rule_engine | No (gap) | L2:recovery | pure |
| `RuleResult.to_dict` | recovery_rule_engine | No (gap) | L2:recovery | pure |
| `SkillSpecificRule.evaluate` | recovery_rule_engine | No (gap) | L2:recovery | pure |
| `classify_error_category` | recovery_rule_engine | No (gap) | L2:recovery | pure |
| `combine_confidences` | recovery_rule_engine | No (gap) | L2:recovery | pure |
| `evaluate_rules` | recovery_rule_engine | No (gap) | L2:recovery | pure |
| `get_incident_driver` | incident_driver | Yes | L4:transaction_coordinator | pure |
| `get_incidents_facade` | incidents_facade | Yes | L4:incidents_handler | pure |
| `should_auto_execute` | recovery_rule_engine | No (gap) | L2:recovery | pure |
| `should_select_action` | recovery_rule_engine | No (gap) | L2:recovery | pure |
| `suggest_recovery_mode` | recovery_rule_engine | No (gap) | L2:recovery | pure |

## 3. Internal Functions

### Decisions

| Function | File | Confidence |
|----------|------|------------|
| `BaseValidator.validate` | prevention_engine | medium |
| `BudgetValidator.validate` | prevention_engine | medium |
| `ContentAccuracyValidatorV2.validate` | prevention_engine | medium |
| `HallucinationValidator.validate` | prevention_engine | medium |
| `IncidentEngine.check_and_create_incident` | incident_engine | medium |
| `IncidentSeverityEngine.should_escalate` | incident_severity_engine | medium |
| `PIIValidator.validate` | prevention_engine | medium |
| `PolicyViolationService.check_incident_exists` | policy_violation_engine | ambiguous |
| `PolicyViolationService.check_policy_enabled` | policy_violation_engine | ambiguous |
| `PolicyViolationService.check_violation_persisted` | policy_violation_engine | ambiguous |
| `PolicyViolationService.verify_violation_truth` | policy_violation_engine | ambiguous |
| `PreventionEngine.evaluate` | prevention_engine | medium |
| `SafetyValidator.validate` | prevention_engine | medium |
| `evaluate_prevention` | prevention_engine | medium |

### Coordinators

| Function | File | Confidence |
|----------|------|------------|
| `IncidentWriteService.resolve_incident` | incident_write_engine | medium |

### Helpers

_107 internal helper functions._

- **anomaly_bridge:** `AnomalyIncidentBridge.__init__`, `AnomalyIncidentBridge._build_incident_insert_sql`, `AnomalyIncidentBridge._check_existing_incident`, `AnomalyIncidentBridge._create_incident`, `AnomalyIncidentBridge._is_suppressed`, `AnomalyIncidentBridge._meets_severity_threshold`
- **export_bundle_driver:** `ExportBundleService.__init__`, `ExportBundleService._assess_business_impact`, `ExportBundleService._assess_risk_level`, `ExportBundleService._compute_bundle_hash`, `ExportBundleService._generate_attestation`, `ExportBundleService._generate_incident_summary`, `ExportBundleService._generate_recommendations`
- **hallucination_detector:** `HallucinationDetector.__init__`, `HallucinationDetector._detect_contradictions`, `HallucinationDetector._detect_suspicious_citations`, `HallucinationDetector._detect_suspicious_urls`, `HallucinationDetector._detect_temporal_issues`, `HallucinationDetector._hash_content`, `HallucinationIndicator.to_dict`, `HallucinationResult._derive_severity`, `HallucinationResult.to_incident_data`
- **incident_aggregator:** `IncidentAggregator.__init__`, `IncidentAggregator._add_call_to_incident`, `IncidentAggregator._add_incident_event`, `IncidentAggregator._can_create_incident`, `IncidentAggregator._create_incident`, `IncidentAggregator._find_open_incident`, `IncidentAggregator._get_rate_limit_incident`, `IncidentKey.__eq__`, `IncidentKey.__hash__`
- **incident_driver:** `IncidentDriver.__init__`, `IncidentDriver._emit_ack`, `IncidentDriver._engine`
- **incident_engine:** `IncidentEngine.__init__`, `IncidentEngine._check_policy_suppression`, `IncidentEngine._extract_error_code`, `IncidentEngine._generate_title`, `IncidentEngine._get_driver`, `IncidentEngine._maybe_create_policy_proposal`, `IncidentEngine._write_prevention_record`, `_get_lessons_learned_engine`
- **incident_pattern_driver:** `IncidentPatternDriver.__init__`
- **incident_pattern_engine:** `IncidentPatternService.__init__`, `IncidentPatternService._detect_cascade_failures`, `IncidentPatternService._detect_category_clusters`, `IncidentPatternService._detect_severity_spikes`
- **incident_read_driver:** `IncidentReadDriver.__init__`
- **incident_read_engine:** `IncidentReadService.__init__`
- **incident_severity_engine:** `IncidentSeverityEngine.__init__`
- **incident_write_driver:** `IncidentWriteDriver.__init__`
- **incident_write_engine:** `IncidentWriteService.__init__`
- **incidents_facade:** `IncidentsFacade._snapshot_to_summary`
- **incidents_facade_driver:** `IncidentsFacadeDriver.__init__`, `IncidentsFacadeDriver._to_snapshot`
- **lessons_driver:** `LessonsDriver.__init__`
- **llm_failure_driver:** `LLMFailureDriver.__init__`
- **llm_failure_engine:** `LLMFailureFact.__post_init__`, `LLMFailureService.__init__`, `LLMFailureService._capture_evidence`, `LLMFailureService._mark_run_failed`, `LLMFailureService._persist_failure`, `LLMFailureService._verify_no_contamination`
- **policy_violation_driver:** `PolicyViolationDriver.__init__`
- **policy_violation_engine:** `PolicyViolationService.__init__`, `PolicyViolationService.create_incident_from_violation`, `PolicyViolationService.persist_evidence`, `PolicyViolationService.persist_violation_and_create_incident`, `PolicyViolationService.persist_violation_fact`, `create_policy_evaluation_record`, `create_policy_evaluation_sync`, `handle_policy_evaluation_for_run`, `handle_policy_violation`
- **postmortem_driver:** `PostMortemDriver.__init__`
- **postmortem_engine:** `PostMortemService.__init__`, `PostMortemService._extract_insights`, `PostMortemService._find_similar_incidents`, `PostMortemService._generate_category_insights`, `PostMortemService._get_resolution_summary`
- **prevention_engine:** `BudgetValidator.__init__`, `ContentAccuracyValidatorV2.__init__`, `ContentAccuracyValidatorV2._extract_claim`, `ContentAccuracyValidatorV2._get_value`, `HallucinationValidator.__init__`, `HallucinationValidator._claim_in_context`, `PIIValidator.__init__`, `PIIValidator._redact`, `PolicyViolation.to_dict`, `PreventionEngine.__init__`
  _...and 6 more_
- **recovery_rule_engine:** `CompositeRule.__init__`, `ErrorCodeRule.__init__`, `HistoricalPatternRule.__init__`, `OccurrenceThresholdRule.__init__`, `RecoveryRuleEngine.__init__`, `Rule.__init__`, `Rule.__repr__`, `SkillSpecificRule.__init__`
- **recurrence_analysis_driver:** `RecurrenceAnalysisDriver.__init__`
- **recurrence_analysis_engine:** `RecurrenceAnalysisService.__init__`, `RecurrenceAnalysisService._snapshot_to_group`
- **semantic_failures:** `format_violation_message`

### Persistence

| Function | File | Side Effects |
|----------|------|--------------|
| `ExportBundleService.create_evidence_bundle` | export_bundle_driver | pure |
| `ExportBundleService.create_executive_debrief` | export_bundle_driver | pure |
| `ExportBundleService.create_soc2_bundle` | export_bundle_driver | pure |
| `ExportBundleService.trace_store` | export_bundle_driver | pure |
| `IncidentAggregator.get_incident_stats` | incident_aggregator | pure |
| `IncidentAggregator.get_or_create_incident` | incident_aggregator | pure |
| `IncidentAggregator.resolve_stale_incidents` | incident_aggregator | db_write |
| `IncidentKey.from_event` | incident_aggregator | pure |
| `IncidentPatternDriver.fetch_cascade_failures` | incident_pattern_driver | db_write |
| `IncidentPatternDriver.fetch_category_clusters` | incident_pattern_driver | db_write |
| `IncidentPatternDriver.fetch_incidents_count` | incident_pattern_driver | db_write |
| `IncidentPatternDriver.fetch_severity_spikes` | incident_pattern_driver | db_write |
| `IncidentReadDriver.count_incidents_since` | incident_read_driver | pure |
| `IncidentReadDriver.get_incident` | incident_read_driver | pure |
| `IncidentReadDriver.get_incident_events` | incident_read_driver | pure |
| `IncidentReadDriver.get_last_incident` | incident_read_driver | pure |
| `IncidentReadDriver.list_incidents` | incident_read_driver | pure |
| `IncidentWriteDriver.create_incident_event` | incident_write_driver | db_write |
| `IncidentWriteDriver.fetch_incidents_by_run_id` | incident_write_driver | db_write |
| `IncidentWriteDriver.fetch_suppressing_policy` | incident_write_driver | db_write |
| `IncidentWriteDriver.insert_incident` | incident_write_driver | db_write |
| `IncidentWriteDriver.insert_policy_proposal` | incident_write_driver | db_write |
| `IncidentWriteDriver.insert_prevention_record` | incident_write_driver | db_write |
| `IncidentWriteDriver.refresh_incident` | incident_write_driver | pure |
| `IncidentWriteDriver.update_incident_acknowledged` | incident_write_driver | db_write |
| `IncidentWriteDriver.update_incident_resolved` | incident_write_driver | db_write |
| `IncidentWriteDriver.update_run_incident_count` | incident_write_driver | db_write |
| `IncidentWriteDriver.update_trace_incident_id` | incident_write_driver | db_write |
| `IncidentsFacadeDriver.fetch_active_incidents` | incidents_facade_driver | db_write |
| `IncidentsFacadeDriver.fetch_cost_impact_data` | incidents_facade_driver | db_write |
| `IncidentsFacadeDriver.fetch_historical_incidents` | incidents_facade_driver | db_write |
| `IncidentsFacadeDriver.fetch_incident_by_id` | incidents_facade_driver | db_write |
| `IncidentsFacadeDriver.fetch_incidents_by_run` | incidents_facade_driver | db_write |
| `IncidentsFacadeDriver.fetch_metrics_aggregates` | incidents_facade_driver | db_write |
| `IncidentsFacadeDriver.fetch_resolved_incidents` | incidents_facade_driver | db_write |
| `LLMFailureDriver.fetch_contamination_check` | llm_failure_driver | db_write |
| `LLMFailureDriver.fetch_failure_by_run_id` | llm_failure_driver | db_write |
| `LLMFailureDriver.insert_evidence` | llm_failure_driver | db_write |
| `LLMFailureDriver.insert_failure` | llm_failure_driver | db_write |
| `LLMFailureDriver.update_run_failed` | llm_failure_driver | db_write |
| `LessonsDriver.fetch_debounce_count` | lessons_driver | db_write |
| `LessonsDriver.fetch_expired_deferred` | lessons_driver | db_write |
| `LessonsDriver.fetch_lesson_by_id` | lessons_driver | db_write |
| `LessonsDriver.fetch_lesson_stats` | lessons_driver | db_write |
| `LessonsDriver.fetch_lessons_list` | lessons_driver | db_write |
| `LessonsDriver.insert_lesson` | lessons_driver | db_write |
| `LessonsDriver.insert_policy_proposal_from_lesson` | lessons_driver | db_write |
| `LessonsDriver.update_lesson_converted` | lessons_driver | db_write |
| `LessonsDriver.update_lesson_deferred` | lessons_driver | db_write |
| `LessonsDriver.update_lesson_dismissed` | lessons_driver | db_write |
| `LessonsDriver.update_lesson_reactivated` | lessons_driver | db_write |
| `PolicyViolationDriver.fetch_incident_by_violation` | policy_violation_driver | db_write |
| `PolicyViolationDriver.fetch_policy_enabled` | policy_violation_driver | db_write |
| `PolicyViolationDriver.fetch_violation_exists` | policy_violation_driver | db_write |
| `PolicyViolationDriver.fetch_violation_truth_check` | policy_violation_driver | db_write |
| `PolicyViolationDriver.insert_evidence_event` | policy_violation_driver | db_write |
| `PolicyViolationDriver.insert_policy_evaluation` | policy_violation_driver | db_write |
| `PolicyViolationDriver.insert_violation_record` | policy_violation_driver | db_write |
| `PostMortemDriver.fetch_category_stats` | postmortem_driver | db_write |
| `PostMortemDriver.fetch_recurrence_data` | postmortem_driver | db_write |
| `PostMortemDriver.fetch_resolution_methods` | postmortem_driver | db_write |
| `PostMortemDriver.fetch_resolution_summary` | postmortem_driver | db_write |
| `PostMortemDriver.fetch_similar_incidents` | postmortem_driver | db_write |
| `RecurrenceAnalysisDriver.fetch_recurrence_for_category` | recurrence_analysis_driver | db_write |
| `RecurrenceAnalysisDriver.fetch_recurrence_groups` | recurrence_analysis_driver | db_write |
| `create_incident_aggregator` | incident_aggregator | pure |
| `get_export_bundle_service` | export_bundle_driver | pure |
| `get_incident_pattern_driver` | incident_pattern_driver | pure |
| `get_incident_read_driver` | incident_read_driver | pure |
| `get_incident_write_driver` | incident_write_driver | pure |
| `get_lessons_driver` | lessons_driver | pure |
| `get_llm_failure_driver` | llm_failure_driver | pure |
| `get_policy_violation_driver` | policy_violation_driver | pure |
| `get_postmortem_driver` | postmortem_driver | pure |
| `insert_policy_evaluation_sync` | policy_violation_driver | db_write |

### Unclassified (needs review)

_37 functions need manual classification._

- `AnomalyIncidentBridge.ingest` (anomaly_bridge)
- `HallucinationDetector.detect` (hallucination_detector)
- `IncidentEngine.create_incident_for_all_runs` (incident_engine)
- `IncidentEngine.create_incident_for_failed_run` (incident_engine)
- `IncidentEngine.create_incident_for_run` (incident_engine)
- `IncidentEngine.get_incidents_for_run` (incident_engine)
- `IncidentPatternService.detect_patterns` (incident_pattern_engine)
- `IncidentReadService.count_incidents_since` (incident_read_engine)
- `IncidentReadService.get_incident` (incident_read_engine)
- `IncidentReadService.get_incident_events` (incident_read_engine)
- `IncidentReadService.get_last_incident` (incident_read_engine)
- `IncidentReadService.list_incidents` (incident_read_engine)
- `IncidentSeverityEngine.calculate_severity_for_calls` (incident_severity_engine)
- `IncidentSeverityEngine.get_initial_severity` (incident_severity_engine)
- `IncidentWriteService.acknowledge_incident` (incident_write_engine)
- `IncidentWriteService.manual_close_incident` (incident_write_engine)
- `LLMFailureService.get_failure_by_run_id` (llm_failure_engine)
- `LLMFailureService.persist_failure_and_mark_run` (llm_failure_engine)
- `PostMortemService.get_category_learnings` (postmortem_engine)
- `PostMortemService.get_incident_learnings` (postmortem_engine)
- _...and 17 more_

## 4. Explicit Non-Features

_No explicit non-feature declarations found in INCIDENTS_DOMAIN_LOCK_FINAL.md._
