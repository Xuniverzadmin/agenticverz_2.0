# Incidents — Call Graph

**Domain:** incidents  
**Total functions:** 267  
**Generator:** `scripts/ops/hoc_call_chain_tracer.py`

---

## Role Summary

| Role | Count | Description |
|------|-------|-------------|
| CANONICAL | 13 | Owns the algorithm — most decisions, primary logic |
| SUPERSET | 22 | Calls other functions + adds its own decisions |
| WRAPPER | 85 | Thin delegation — ≤3 stmts, no branching |
| LEAF | 102 | Terminal — calls no other domain functions |
| ENTRY | 16 | Entry point — no domain-internal callers |
| INTERNAL | 29 | Called only by other domain functions |

## Canonical Algorithm Owners

### `anomaly_bridge.AnomalyIncidentBridge.ingest`
- **Layer:** L5
- **Decisions:** 3
- **Statements:** 5
- **Delegation depth:** 2
- **Persistence:** no
- **Chain:** anomaly_bridge.AnomalyIncidentBridge.ingest → anomaly_bridge.AnomalyIncidentBridge._check_existing_incident → anomaly_bridge.AnomalyIncidentBridge._create_incident → anomaly_bridge.AnomalyIncidentBridge._is_suppressed → ...+2
- **Calls:** anomaly_bridge:AnomalyIncidentBridge._check_existing_incident, anomaly_bridge:AnomalyIncidentBridge._create_incident, anomaly_bridge:AnomalyIncidentBridge._is_suppressed, anomaly_bridge:AnomalyIncidentBridge._meets_severity_threshold, incident_aggregator:IncidentAggregator._create_incident

### `export_bundle_driver.ExportBundleService.create_evidence_bundle`
- **Layer:** L6
- **Decisions:** 4
- **Statements:** 1
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** export_bundle_driver.ExportBundleService.create_evidence_bundle → export_bundle_driver.ExportBundleService._compute_bundle_hash
- **Calls:** export_bundle_driver:ExportBundleService._compute_bundle_hash

### `hallucination_detector.HallucinationDetector.detect`
- **Layer:** L5
- **Decisions:** 6
- **Statements:** 10
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** hallucination_detector.HallucinationDetector.detect → hallucination_detector.HallucinationDetector._detect_contradictions → hallucination_detector.HallucinationDetector._detect_suspicious_citations → hallucination_detector.HallucinationDetector._detect_suspicious_urls → ...+2
- **Calls:** hallucination_detector:HallucinationDetector._detect_contradictions, hallucination_detector:HallucinationDetector._detect_suspicious_citations, hallucination_detector:HallucinationDetector._detect_suspicious_urls, hallucination_detector:HallucinationDetector._detect_temporal_issues, hallucination_detector:HallucinationDetector._hash_content

### `incident_driver.IncidentDriver.create_incident_for_run`
- **Layer:** L5
- **Decisions:** 1
- **Statements:** 6
- **Delegation depth:** 4
- **Persistence:** no
- **Chain:** incident_driver.IncidentDriver.create_incident_for_run → incident_driver.IncidentDriver._emit_ack → incident_engine.IncidentEngine.create_incident_for_run
- **Calls:** incident_driver:IncidentDriver._emit_ack, incident_engine:IncidentEngine.create_incident_for_run

### `incident_engine.IncidentEngine.create_incident_for_run`
- **Layer:** L5
- **Decisions:** 6
- **Statements:** 1
- **Delegation depth:** 3
- **Persistence:** no
- **Chain:** incident_engine.IncidentEngine.create_incident_for_run → incident_engine.IncidentEngine._check_policy_suppression → incident_engine.IncidentEngine._generate_title → incident_engine.IncidentEngine._get_driver → ...+6
- **Calls:** incident_engine:IncidentEngine._check_policy_suppression, incident_engine:IncidentEngine._generate_title, incident_engine:IncidentEngine._get_driver, incident_engine:IncidentEngine._maybe_create_policy_proposal, incident_engine:IncidentEngine._write_prevention_record, incident_engine:_get_lessons_learned_engine, incident_write_driver:IncidentWriteDriver.insert_incident, incident_write_driver:IncidentWriteDriver.update_run_incident_count, incident_write_driver:IncidentWriteDriver.update_trace_incident_id

### `incident_write_engine.IncidentWriteService.resolve_incident`
- **Layer:** L5
- **Decisions:** 2
- **Statements:** 6
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** incident_write_engine.IncidentWriteService.resolve_incident → incident_write_driver.IncidentWriteDriver.create_incident_event → incident_write_driver.IncidentWriteDriver.refresh_incident → incident_write_driver.IncidentWriteDriver.update_incident_resolved
- **Calls:** incident_write_driver:IncidentWriteDriver.create_incident_event, incident_write_driver:IncidentWriteDriver.refresh_incident, incident_write_driver:IncidentWriteDriver.update_incident_resolved

### `incidents_facade.IncidentsFacade.list_active_incidents`
- **Layer:** L5
- **Decisions:** 6
- **Statements:** 13
- **Delegation depth:** 2
- **Persistence:** no
- **Chain:** incidents_facade.IncidentsFacade.list_active_incidents → incidents_facade.IncidentsFacade._snapshot_to_summary → incidents_facade_driver.IncidentsFacadeDriver.fetch_active_incidents
- **Calls:** incidents_facade:IncidentsFacade._snapshot_to_summary, incidents_facade_driver:IncidentsFacadeDriver.fetch_active_incidents

### `incidents_facade_driver.IncidentsFacadeDriver.fetch_active_incidents`
- **Layer:** L6
- **Decisions:** 7
- **Statements:** 17
- **Delegation depth:** 1
- **Persistence:** yes
- **Chain:** incidents_facade_driver.IncidentsFacadeDriver.fetch_active_incidents → incidents_facade_driver.IncidentsFacadeDriver._to_snapshot
- **Calls:** incidents_facade_driver:IncidentsFacadeDriver._to_snapshot

### `llm_failure_engine.LLMFailureService.persist_failure_and_mark_run`
- **Layer:** L5
- **Decisions:** 1
- **Statements:** 7
- **Delegation depth:** 2
- **Persistence:** no
- **Chain:** llm_failure_engine.LLMFailureService.persist_failure_and_mark_run → llm_failure_engine.LLMFailureService._capture_evidence → llm_failure_engine.LLMFailureService._mark_run_failed → llm_failure_engine.LLMFailureService._persist_failure → ...+1
- **Calls:** llm_failure_engine:LLMFailureService._capture_evidence, llm_failure_engine:LLMFailureService._mark_run_failed, llm_failure_engine:LLMFailureService._persist_failure, llm_failure_engine:LLMFailureService._verify_no_contamination

### `policy_violation_engine.create_policy_evaluation_sync`
- **Layer:** L5
- **Decisions:** 5
- **Statements:** 10
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** policy_violation_engine.create_policy_evaluation_sync → policy_violation_driver.insert_policy_evaluation_sync
- **Calls:** policy_violation_driver:insert_policy_evaluation_sync

### `postmortem_engine.PostMortemService.get_category_learnings`
- **Layer:** L5
- **Decisions:** 1
- **Statements:** 11
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** postmortem_engine.PostMortemService.get_category_learnings → postmortem_driver.PostMortemDriver.fetch_category_stats → postmortem_driver.PostMortemDriver.fetch_recurrence_data → postmortem_driver.PostMortemDriver.fetch_resolution_methods → ...+1
- **Calls:** postmortem_driver:PostMortemDriver.fetch_category_stats, postmortem_driver:PostMortemDriver.fetch_recurrence_data, postmortem_driver:PostMortemDriver.fetch_resolution_methods, postmortem_engine:PostMortemService._generate_category_insights

### `prevention_engine.PreventionEngine.evaluate`
- **Layer:** L5
- **Decisions:** 6
- **Statements:** 14
- **Delegation depth:** 2
- **Persistence:** no
- **Chain:** prevention_engine.PreventionEngine.evaluate → prevention_engine.BaseValidator.validate → prevention_engine.BudgetValidator.validate → prevention_engine.ContentAccuracyValidatorV2.validate → ...+5
- **Calls:** prevention_engine:BaseValidator.validate, prevention_engine:BudgetValidator.validate, prevention_engine:ContentAccuracyValidatorV2.validate, prevention_engine:HallucinationValidator.validate, prevention_engine:PIIValidator.validate, prevention_engine:PreventionEngine._emit_metrics, prevention_engine:PreventionEngine._generate_safe_response, prevention_engine:SafetyValidator.validate

### `recovery_rule_engine.RecoveryRuleEngine.evaluate`
- **Layer:** L5
- **Decisions:** 4
- **Statements:** 11
- **Delegation depth:** 4
- **Persistence:** no
- **Chain:** recovery_rule_engine.RecoveryRuleEngine.evaluate → prevention_engine.PreventionEngine.evaluate → recovery_rule_engine.CompositeRule.evaluate → recovery_rule_engine.ErrorCodeRule.evaluate → ...+4
- **Calls:** prevention_engine:PreventionEngine.evaluate, recovery_rule_engine:CompositeRule.evaluate, recovery_rule_engine:ErrorCodeRule.evaluate, recovery_rule_engine:HistoricalPatternRule.evaluate, recovery_rule_engine:OccurrenceThresholdRule.evaluate, recovery_rule_engine:Rule.evaluate, recovery_rule_engine:SkillSpecificRule.evaluate

## Supersets (orchestrating functions)

### `export_bundle_driver.ExportBundleService.create_executive_debrief`
- **Decisions:** 4, **Statements:** 1
- **Subsumes:** export_bundle_driver:ExportBundleService._assess_business_impact, export_bundle_driver:ExportBundleService._assess_risk_level, export_bundle_driver:ExportBundleService._generate_incident_summary, export_bundle_driver:ExportBundleService._generate_recommendations

### `incident_aggregator.IncidentAggregator._add_call_to_incident`
- **Decisions:** 3, **Statements:** 7
- **Subsumes:** incident_aggregator:IncidentAggregator._add_incident_event, incident_severity_engine:IncidentSeverityEngine.should_escalate

### `incident_aggregator.IncidentAggregator.get_or_create_incident`
- **Decisions:** 2, **Statements:** 7
- **Subsumes:** anomaly_bridge:AnomalyIncidentBridge._create_incident, incident_aggregator:IncidentAggregator._add_call_to_incident, incident_aggregator:IncidentAggregator._can_create_incident, incident_aggregator:IncidentAggregator._create_incident, incident_aggregator:IncidentAggregator._find_open_incident, incident_aggregator:IncidentAggregator._get_rate_limit_incident, incident_aggregator:IncidentKey.from_event

### `incident_aggregator.IncidentAggregator.resolve_stale_incidents`
- **Decisions:** 2, **Statements:** 10
- **Subsumes:** incident_aggregator:IncidentAggregator._add_incident_event

### `incident_engine.IncidentEngine._get_driver`
- **Decisions:** 3, **Statements:** 4
- **Subsumes:** incident_write_driver:get_incident_write_driver

### `incident_engine.IncidentEngine.check_and_create_incident`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** incident_engine:IncidentEngine._extract_error_code, incident_engine:IncidentEngine.create_incident_for_failed_run

### `incident_engine.IncidentEngine.create_incident_for_failed_run`
- **Decisions:** 3, **Statements:** 1
- **Subsumes:** incident_engine:IncidentEngine._check_policy_suppression, incident_engine:IncidentEngine._generate_title, incident_engine:IncidentEngine._get_driver, incident_engine:IncidentEngine._maybe_create_policy_proposal, incident_engine:IncidentEngine._write_prevention_record, incident_engine:_get_lessons_learned_engine, incident_write_driver:IncidentWriteDriver.insert_incident, incident_write_driver:IncidentWriteDriver.update_run_incident_count, incident_write_driver:IncidentWriteDriver.update_trace_incident_id

### `incident_severity_engine.IncidentSeverityEngine.should_escalate`
- **Decisions:** 2, **Statements:** 3
- **Subsumes:** incident_severity_engine:IncidentSeverityEngine.calculate_severity_for_calls

### `incidents_facade.IncidentsFacade.get_metrics`
- **Decisions:** 2, **Statements:** 7
- **Subsumes:** incidents_facade_driver:IncidentsFacadeDriver.fetch_metrics_aggregates

### `incidents_facade.IncidentsFacade.list_historical_incidents`
- **Decisions:** 3, **Statements:** 11
- **Subsumes:** incidents_facade:IncidentsFacade._snapshot_to_summary, incidents_facade_driver:IncidentsFacadeDriver.fetch_historical_incidents

### `incidents_facade.IncidentsFacade.list_resolved_incidents`
- **Decisions:** 6, **Statements:** 13
- **Subsumes:** incidents_facade:IncidentsFacade._snapshot_to_summary, incidents_facade_driver:IncidentsFacadeDriver.fetch_resolved_incidents

### `incidents_facade_driver.IncidentsFacadeDriver.fetch_historical_incidents`
- **Decisions:** 4, **Statements:** 14
- **Subsumes:** incidents_facade_driver:IncidentsFacadeDriver._to_snapshot

### `incidents_facade_driver.IncidentsFacadeDriver.fetch_resolved_incidents`
- **Decisions:** 7, **Statements:** 17
- **Subsumes:** incidents_facade_driver:IncidentsFacadeDriver._to_snapshot

### `llm_failure_engine.LLMFailureService._verify_no_contamination`
- **Decisions:** 3, **Statements:** 4
- **Subsumes:** llm_failure_driver:LLMFailureDriver.fetch_contamination_check

### `policy_violation_engine.PolicyViolationService.create_incident_from_violation`
- **Decisions:** 3, **Statements:** 7
- **Subsumes:** incident_aggregator:IncidentAggregator.get_or_create_incident, incident_aggregator:create_incident_aggregator, policy_violation_engine:PolicyViolationService.check_violation_persisted

### `policy_violation_engine.PolicyViolationService.persist_violation_and_create_incident`
- **Decisions:** 3, **Statements:** 7
- **Subsumes:** policy_violation_engine:PolicyViolationService.check_incident_exists, policy_violation_engine:PolicyViolationService.create_incident_from_violation, policy_violation_engine:PolicyViolationService.persist_evidence, policy_violation_engine:PolicyViolationService.persist_violation_fact, prevention_engine:create_incident_from_violation

### `policy_violation_engine.PolicyViolationService.persist_violation_fact`
- **Decisions:** 4, **Statements:** 8
- **Subsumes:** policy_violation_driver:PolicyViolationDriver.insert_violation_record

### `policy_violation_engine.handle_policy_evaluation_for_run`
- **Decisions:** 3, **Statements:** 3
- **Subsumes:** policy_violation_engine:create_policy_evaluation_record

### `prevention_engine.ContentAccuracyValidatorV2.validate`
- **Decisions:** 4, **Statements:** 8
- **Subsumes:** prevention_engine:ContentAccuracyValidatorV2._extract_claim, prevention_engine:ContentAccuracyValidatorV2._get_value

### `prevention_engine.HallucinationValidator.validate`
- **Decisions:** 2, **Statements:** 3
- **Subsumes:** prevention_engine:HallucinationValidator._claim_in_context

### `prevention_engine.create_incident_from_violation`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** prevention_engine:_create_incident_with_service

### `recovery_rule_engine.CompositeRule.evaluate`
- **Decisions:** 2, **Statements:** 6
- **Subsumes:** hallucination_detector:HallucinationIndicator.to_dict, prevention_engine:PolicyViolation.to_dict, prevention_engine:PreventionEngine.evaluate, prevention_engine:PreventionResult.to_dict, recovery_rule_engine:ErrorCodeRule.evaluate, recovery_rule_engine:EvaluationResult.to_dict, recovery_rule_engine:HistoricalPatternRule.evaluate, recovery_rule_engine:OccurrenceThresholdRule.evaluate, recovery_rule_engine:RecoveryRuleEngine.evaluate, recovery_rule_engine:Rule.evaluate, recovery_rule_engine:RuleContext.to_dict, recovery_rule_engine:RuleResult.to_dict, recovery_rule_engine:SkillSpecificRule.evaluate

## Wrappers (thin delegation)

- `anomaly_bridge.AnomalyIncidentBridge.__init__` → incident_write_driver:get_incident_write_driver
- `anomaly_bridge.AnomalyIncidentBridge._build_incident_insert_sql` → ?
- `anomaly_bridge.AnomalyIncidentBridge._check_existing_incident` → ?
- `anomaly_bridge.AnomalyIncidentBridge._meets_severity_threshold` → ?
- `anomaly_bridge.get_anomaly_incident_bridge` → ?
- `export_bundle_driver.ExportBundleService.__init__` → ?
- `export_bundle_driver.ExportBundleService._assess_business_impact` → ?
- `export_bundle_driver.ExportBundleService._generate_attestation` → ?
- `export_bundle_driver.ExportBundleService._generate_incident_summary` → ?
- `export_bundle_driver.ExportBundleService._generate_recommendations` → ?
- `hallucination_detector.HallucinationIndicator.to_dict` → ?
- `incident_aggregator.IncidentKey.__hash__` → ?
- `incident_aggregator.create_incident_aggregator` → ?
- `incident_driver.IncidentDriver.__init__` → ?
- `incident_driver.IncidentDriver.check_and_create_incident` → incident_engine:IncidentEngine.check_and_create_incident
- `incident_driver.IncidentDriver.get_incidents_for_run` → incident_engine:IncidentEngine.get_incidents_for_run
- `incident_engine.IncidentEngine.__init__` → ?
- `incident_engine._get_lessons_learned_engine` → ?
- `incident_pattern_driver.IncidentPatternDriver.__init__` → ?
- `incident_pattern_driver.get_incident_pattern_driver` → ?
- `incident_pattern_engine.IncidentPatternService.__init__` → incident_pattern_driver:get_incident_pattern_driver
- `incident_read_driver.IncidentReadDriver.__init__` → ?
- `incident_read_driver.get_incident_read_driver` → ?
- `incident_read_engine.IncidentReadService.__init__` → incident_read_driver:get_incident_read_driver
- `incident_read_engine.IncidentReadService.count_incidents_since` → incident_read_driver:IncidentReadDriver.count_incidents_since
- `incident_read_engine.IncidentReadService.get_incident` → incident_read_driver:IncidentReadDriver.get_incident
- `incident_read_engine.IncidentReadService.get_incident_events` → incident_read_driver:IncidentReadDriver.get_incident_events
- `incident_read_engine.IncidentReadService.get_last_incident` → incident_read_driver:IncidentReadDriver.get_last_incident
- `incident_read_engine.IncidentReadService.list_incidents` → incident_read_driver:IncidentReadDriver.list_incidents
- `incident_read_engine.get_incident_read_service` → ?
- `incident_severity_engine.IncidentSeverityEngine.__init__` → incident_severity_engine:SeverityConfig.default
- `incident_severity_engine.IncidentSeverityEngine.get_initial_severity` → ?
- `incident_severity_engine.SeverityConfig.default` → ?
- `incident_severity_engine.generate_incident_title` → ?
- `incident_write_driver.IncidentWriteDriver.__init__` → ?
- `incident_write_driver.IncidentWriteDriver.create_incident_event` → ?
- `incident_write_driver.IncidentWriteDriver.insert_prevention_record` → ?
- `incident_write_driver.IncidentWriteDriver.refresh_incident` → ?
- `incident_write_driver.IncidentWriteDriver.update_trace_incident_id` → ?
- `incident_write_driver.get_incident_write_driver` → ?
- `incident_write_engine.IncidentWriteService.__init__` → incident_write_driver:get_incident_write_driver
- `incident_write_engine.get_incident_write_service` → ?
- `incidents_facade.IncidentsFacade._snapshot_to_summary` → ?
- `incidents_facade_driver.IncidentsFacadeDriver.__init__` → ?
- `incidents_facade_driver.IncidentsFacadeDriver._to_snapshot` → ?
- `lessons_driver.LessonsDriver.__init__` → ?
- `lessons_driver.LessonsDriver.insert_policy_proposal_from_lesson` → ?
- `lessons_driver.get_lessons_driver` → ?
- `llm_failure_driver.LLMFailureDriver.__init__` → ?
- `llm_failure_driver.get_llm_failure_driver` → ?
- `llm_failure_engine.LLMFailureService._mark_run_failed` → llm_failure_driver:LLMFailureDriver.update_run_failed
- `policy_violation_driver.PolicyViolationDriver.__init__` → ?
- `policy_violation_driver.get_policy_violation_driver` → ?
- `policy_violation_engine.PolicyViolationService.__init__` → policy_violation_driver:get_policy_violation_driver
- `policy_violation_engine.PolicyViolationService.check_incident_exists` → policy_violation_driver:PolicyViolationDriver.fetch_incident_by_violation
- `policy_violation_engine.PolicyViolationService.check_policy_enabled` → policy_violation_driver:PolicyViolationDriver.fetch_policy_enabled
- `policy_violation_engine.PolicyViolationService.check_violation_persisted` → policy_violation_driver:PolicyViolationDriver.fetch_violation_exists
- `postmortem_driver.PostMortemDriver.__init__` → ?
- `postmortem_driver.get_postmortem_driver` → ?
- `postmortem_engine.PostMortemService.__init__` → postmortem_driver:get_postmortem_driver
- `prevention_engine.BaseValidator.validate` → ?
- `prevention_engine.BudgetValidator.__init__` → ?
- `prevention_engine.ContentAccuracyValidatorV2.__init__` → ?
- `prevention_engine.HallucinationValidator.__init__` → ?
- `prevention_engine.PolicyViolation.to_dict` → ?
- `prevention_engine.PreventionResult.to_dict` → hallucination_detector:HallucinationIndicator.to_dict
- `recovery_rule_engine.EvaluationResult.to_dict` → hallucination_detector:HallucinationIndicator.to_dict
- `recovery_rule_engine.HistoricalPatternRule.__init__` → anomaly_bridge:AnomalyIncidentBridge.__init__
- `recovery_rule_engine.RecoveryRuleEngine.__init__` → ?
- `recovery_rule_engine.RecoveryRuleEngine.add_rule` → ?
- `recovery_rule_engine.RecoveryRuleEngine.remove_rule` → ?
- `recovery_rule_engine.Rule.__repr__` → ?
- `recovery_rule_engine.Rule.evaluate` → ?
- `recovery_rule_engine.RuleContext.to_dict` → ?
- `recovery_rule_engine.RuleResult.to_dict` → ?
- `recovery_rule_engine.combine_confidences` → ?
- `recovery_rule_engine.should_auto_execute` → ?
- `recovery_rule_engine.should_select_action` → ?
- `recurrence_analysis_driver.RecurrenceAnalysisDriver.__init__` → ?
- `recurrence_analysis_engine.RecurrenceAnalysisService.__init__` → ?
- `recurrence_analysis_engine.RecurrenceAnalysisService._snapshot_to_group` → ?
- `semantic_failures.format_violation_message` → semantic_failures:get_failure_info
- `semantic_failures.get_fix_action` → semantic_failures:get_failure_info
- `semantic_failures.get_fix_owner` → semantic_failures:get_failure_info
- `semantic_failures.get_violation_class` → semantic_failures:get_failure_info

## Full Call Graph

```
[WRAPPER] anomaly_bridge.AnomalyIncidentBridge.__init__ → incident_write_driver:get_incident_write_driver
[WRAPPER] anomaly_bridge.AnomalyIncidentBridge._build_incident_insert_sql
[WRAPPER] anomaly_bridge.AnomalyIncidentBridge._check_existing_incident
[INTERNAL] anomaly_bridge.AnomalyIncidentBridge._create_incident → anomaly_bridge:AnomalyIncidentBridge._build_incident_insert_sql
[INTERNAL] anomaly_bridge.AnomalyIncidentBridge._is_suppressed → incident_write_driver:IncidentWriteDriver.fetch_suppressing_policy
[WRAPPER] anomaly_bridge.AnomalyIncidentBridge._meets_severity_threshold
[CANONICAL] anomaly_bridge.AnomalyIncidentBridge.ingest → anomaly_bridge:AnomalyIncidentBridge._check_existing_incident, anomaly_bridge:AnomalyIncidentBridge._create_incident, anomaly_bridge:AnomalyIncidentBridge._is_suppressed, anomaly_bridge:AnomalyIncidentBridge._meets_severity_threshold, incident_aggregator:IncidentAggregator._create_incident
[WRAPPER] anomaly_bridge.get_anomaly_incident_bridge
[WRAPPER] export_bundle_driver.ExportBundleService.__init__
[WRAPPER] export_bundle_driver.ExportBundleService._assess_business_impact
[LEAF] export_bundle_driver.ExportBundleService._assess_risk_level
[LEAF] export_bundle_driver.ExportBundleService._compute_bundle_hash
[WRAPPER] export_bundle_driver.ExportBundleService._generate_attestation
[WRAPPER] export_bundle_driver.ExportBundleService._generate_incident_summary
[WRAPPER] export_bundle_driver.ExportBundleService._generate_recommendations
[CANONICAL] export_bundle_driver.ExportBundleService.create_evidence_bundle → export_bundle_driver:ExportBundleService._compute_bundle_hash
[SUPERSET] export_bundle_driver.ExportBundleService.create_executive_debrief → export_bundle_driver:ExportBundleService._assess_business_impact, export_bundle_driver:ExportBundleService._assess_risk_level, export_bundle_driver:ExportBundleService._generate_incident_summary, export_bundle_driver:ExportBundleService._generate_recommendations
[ENTRY] export_bundle_driver.ExportBundleService.create_soc2_bundle → export_bundle_driver:ExportBundleService._generate_attestation, export_bundle_driver:ExportBundleService.create_evidence_bundle
[LEAF] export_bundle_driver.ExportBundleService.trace_store
[LEAF] export_bundle_driver.get_export_bundle_service
[LEAF] hallucination_detector.HallucinationDetector.__init__
[LEAF] hallucination_detector.HallucinationDetector._detect_contradictions
[LEAF] hallucination_detector.HallucinationDetector._detect_suspicious_citations
[LEAF] hallucination_detector.HallucinationDetector._detect_suspicious_urls
[LEAF] hallucination_detector.HallucinationDetector._detect_temporal_issues
[LEAF] hallucination_detector.HallucinationDetector._hash_content
[CANONICAL] hallucination_detector.HallucinationDetector.detect → hallucination_detector:HallucinationDetector._detect_contradictions, hallucination_detector:HallucinationDetector._detect_suspicious_citations, hallucination_detector:HallucinationDetector._detect_suspicious_urls, hallucination_detector:HallucinationDetector._detect_temporal_issues, hallucination_detector:HallucinationDetector._hash_content
[WRAPPER] hallucination_detector.HallucinationIndicator.to_dict
[LEAF] hallucination_detector.HallucinationResult._derive_severity
[ENTRY] hallucination_detector.HallucinationResult.to_incident_data → hallucination_detector:HallucinationIndicator.to_dict, hallucination_detector:HallucinationResult._derive_severity, prevention_engine:PolicyViolation.to_dict, prevention_engine:PreventionResult.to_dict, recovery_rule_engine:EvaluationResult.to_dict, ...+2
[LEAF] hallucination_detector.create_detector_for_tenant
[LEAF] incident_aggregator.IncidentAggregator.__init__
[SUPERSET] incident_aggregator.IncidentAggregator._add_call_to_incident → incident_aggregator:IncidentAggregator._add_incident_event, incident_severity_engine:IncidentSeverityEngine.should_escalate
[LEAF] incident_aggregator.IncidentAggregator._add_incident_event
[LEAF] incident_aggregator.IncidentAggregator._can_create_incident
[INTERNAL] incident_aggregator.IncidentAggregator._create_incident → incident_aggregator:IncidentAggregator._add_incident_event, incident_severity_engine:IncidentSeverityEngine.get_initial_severity, incident_severity_engine:generate_incident_title
[LEAF] incident_aggregator.IncidentAggregator._find_open_incident
[LEAF] incident_aggregator.IncidentAggregator._get_rate_limit_incident
[LEAF] incident_aggregator.IncidentAggregator.get_incident_stats
[SUPERSET] incident_aggregator.IncidentAggregator.get_or_create_incident → anomaly_bridge:AnomalyIncidentBridge._create_incident, incident_aggregator:IncidentAggregator._add_call_to_incident, incident_aggregator:IncidentAggregator._can_create_incident, incident_aggregator:IncidentAggregator._create_incident, incident_aggregator:IncidentAggregator._find_open_incident, ...+2
[SUPERSET] incident_aggregator.IncidentAggregator.resolve_stale_incidents → incident_aggregator:IncidentAggregator._add_incident_event
[LEAF] incident_aggregator.IncidentKey.__eq__
[WRAPPER] incident_aggregator.IncidentKey.__hash__
[LEAF] incident_aggregator.IncidentKey.from_event
[WRAPPER] incident_aggregator.create_incident_aggregator
[WRAPPER] incident_driver.IncidentDriver.__init__
[LEAF] incident_driver.IncidentDriver._emit_ack
[LEAF] incident_driver.IncidentDriver._engine
[WRAPPER] incident_driver.IncidentDriver.check_and_create_incident → incident_engine:IncidentEngine.check_and_create_incident
[CANONICAL] incident_driver.IncidentDriver.create_incident_for_run → incident_driver:IncidentDriver._emit_ack, incident_engine:IncidentEngine.create_incident_for_run
[WRAPPER] incident_driver.IncidentDriver.get_incidents_for_run → incident_engine:IncidentEngine.get_incidents_for_run, incidents_facade:IncidentsFacade.get_incidents_for_run
[LEAF] incident_driver.get_incident_driver
[WRAPPER] incident_engine.IncidentEngine.__init__
[INTERNAL] incident_engine.IncidentEngine._check_policy_suppression → incident_engine:IncidentEngine._get_driver, incident_write_driver:IncidentWriteDriver.fetch_suppressing_policy
[LEAF] incident_engine.IncidentEngine._extract_error_code
[LEAF] incident_engine.IncidentEngine._generate_title
[SUPERSET] incident_engine.IncidentEngine._get_driver → incident_write_driver:get_incident_write_driver
[INTERNAL] incident_engine.IncidentEngine._maybe_create_policy_proposal → incident_engine:IncidentEngine._get_driver, incident_write_driver:IncidentWriteDriver.insert_policy_proposal
[INTERNAL] incident_engine.IncidentEngine._write_prevention_record → incident_engine:IncidentEngine._get_driver, incident_write_driver:IncidentWriteDriver.insert_prevention_record
[SUPERSET] incident_engine.IncidentEngine.check_and_create_incident → incident_engine:IncidentEngine._extract_error_code, incident_engine:IncidentEngine.create_incident_for_failed_run
[ENTRY] incident_engine.IncidentEngine.create_incident_for_all_runs → incident_driver:IncidentDriver.create_incident_for_run, incident_engine:IncidentEngine._extract_error_code, incident_engine:IncidentEngine.create_incident_for_run
[SUPERSET] incident_engine.IncidentEngine.create_incident_for_failed_run → incident_engine:IncidentEngine._check_policy_suppression, incident_engine:IncidentEngine._generate_title, incident_engine:IncidentEngine._get_driver, incident_engine:IncidentEngine._maybe_create_policy_proposal, incident_engine:IncidentEngine._write_prevention_record, ...+4
[CANONICAL] incident_engine.IncidentEngine.create_incident_for_run → incident_engine:IncidentEngine._check_policy_suppression, incident_engine:IncidentEngine._generate_title, incident_engine:IncidentEngine._get_driver, incident_engine:IncidentEngine._maybe_create_policy_proposal, incident_engine:IncidentEngine._write_prevention_record, ...+4
[INTERNAL] incident_engine.IncidentEngine.get_incidents_for_run → incident_engine:IncidentEngine._get_driver, incident_write_driver:IncidentWriteDriver.fetch_incidents_by_run_id
[WRAPPER] incident_engine._get_lessons_learned_engine
[LEAF] incident_engine.get_incident_engine
[WRAPPER] incident_pattern_driver.IncidentPatternDriver.__init__
[LEAF] incident_pattern_driver.IncidentPatternDriver.fetch_cascade_failures
[LEAF] incident_pattern_driver.IncidentPatternDriver.fetch_category_clusters
[LEAF] incident_pattern_driver.IncidentPatternDriver.fetch_incidents_count
[LEAF] incident_pattern_driver.IncidentPatternDriver.fetch_severity_spikes
[WRAPPER] incident_pattern_driver.get_incident_pattern_driver
[WRAPPER] incident_pattern_engine.IncidentPatternService.__init__ → incident_pattern_driver:get_incident_pattern_driver
[INTERNAL] incident_pattern_engine.IncidentPatternService._detect_cascade_failures → incident_pattern_driver:IncidentPatternDriver.fetch_cascade_failures
[INTERNAL] incident_pattern_engine.IncidentPatternService._detect_category_clusters → incident_pattern_driver:IncidentPatternDriver.fetch_category_clusters
[INTERNAL] incident_pattern_engine.IncidentPatternService._detect_severity_spikes → incident_pattern_driver:IncidentPatternDriver.fetch_severity_spikes
[INTERNAL] incident_pattern_engine.IncidentPatternService.detect_patterns → incident_pattern_driver:IncidentPatternDriver.fetch_incidents_count, incident_pattern_engine:IncidentPatternService._detect_cascade_failures, incident_pattern_engine:IncidentPatternService._detect_category_clusters, incident_pattern_engine:IncidentPatternService._detect_severity_spikes
[WRAPPER] incident_read_driver.IncidentReadDriver.__init__
[LEAF] incident_read_driver.IncidentReadDriver.count_incidents_since
[LEAF] incident_read_driver.IncidentReadDriver.get_incident
[LEAF] incident_read_driver.IncidentReadDriver.get_incident_events
[LEAF] incident_read_driver.IncidentReadDriver.get_last_incident
[LEAF] incident_read_driver.IncidentReadDriver.list_incidents
[WRAPPER] incident_read_driver.get_incident_read_driver
[WRAPPER] incident_read_engine.IncidentReadService.__init__ → incident_read_driver:get_incident_read_driver
[WRAPPER] incident_read_engine.IncidentReadService.count_incidents_since → incident_read_driver:IncidentReadDriver.count_incidents_since
[WRAPPER] incident_read_engine.IncidentReadService.get_incident → incident_read_driver:IncidentReadDriver.get_incident
[WRAPPER] incident_read_engine.IncidentReadService.get_incident_events → incident_read_driver:IncidentReadDriver.get_incident_events
[WRAPPER] incident_read_engine.IncidentReadService.get_last_incident → incident_read_driver:IncidentReadDriver.get_last_incident
[WRAPPER] incident_read_engine.IncidentReadService.list_incidents → incident_read_driver:IncidentReadDriver.list_incidents
[WRAPPER] incident_read_engine.get_incident_read_service
[WRAPPER] incident_severity_engine.IncidentSeverityEngine.__init__ → incident_severity_engine:SeverityConfig.default
[LEAF] incident_severity_engine.IncidentSeverityEngine.calculate_severity_for_calls
[WRAPPER] incident_severity_engine.IncidentSeverityEngine.get_initial_severity
[SUPERSET] incident_severity_engine.IncidentSeverityEngine.should_escalate → incident_severity_engine:IncidentSeverityEngine.calculate_severity_for_calls
[WRAPPER] incident_severity_engine.SeverityConfig.default
[WRAPPER] incident_severity_engine.generate_incident_title
[WRAPPER] incident_write_driver.IncidentWriteDriver.__init__
[WRAPPER] incident_write_driver.IncidentWriteDriver.create_incident_event
[LEAF] incident_write_driver.IncidentWriteDriver.fetch_incidents_by_run_id
[LEAF] incident_write_driver.IncidentWriteDriver.fetch_suppressing_policy
[LEAF] incident_write_driver.IncidentWriteDriver.insert_incident
[LEAF] incident_write_driver.IncidentWriteDriver.insert_policy_proposal
[WRAPPER] incident_write_driver.IncidentWriteDriver.insert_prevention_record
[WRAPPER] incident_write_driver.IncidentWriteDriver.refresh_incident
[LEAF] incident_write_driver.IncidentWriteDriver.update_incident_acknowledged
[LEAF] incident_write_driver.IncidentWriteDriver.update_incident_resolved
[LEAF] incident_write_driver.IncidentWriteDriver.update_run_incident_count
[WRAPPER] incident_write_driver.IncidentWriteDriver.update_trace_incident_id
[WRAPPER] incident_write_driver.get_incident_write_driver
[WRAPPER] incident_write_engine.IncidentWriteService.__init__ → incident_write_driver:get_incident_write_driver
[ENTRY] incident_write_engine.IncidentWriteService.acknowledge_incident → incident_write_driver:IncidentWriteDriver.create_incident_event, incident_write_driver:IncidentWriteDriver.refresh_incident, incident_write_driver:IncidentWriteDriver.update_incident_acknowledged
[ENTRY] incident_write_engine.IncidentWriteService.manual_close_incident → incident_write_driver:IncidentWriteDriver.create_incident_event, incident_write_driver:IncidentWriteDriver.refresh_incident, incident_write_driver:IncidentWriteDriver.update_incident_resolved
[CANONICAL] incident_write_engine.IncidentWriteService.resolve_incident → incident_write_driver:IncidentWriteDriver.create_incident_event, incident_write_driver:IncidentWriteDriver.refresh_incident, incident_write_driver:IncidentWriteDriver.update_incident_resolved
[WRAPPER] incident_write_engine.get_incident_write_service
[WRAPPER] incidents_facade.IncidentsFacade._snapshot_to_summary
[ENTRY] incidents_facade.IncidentsFacade.analyze_cost_impact → incidents_facade_driver:IncidentsFacadeDriver.fetch_cost_impact_data
[ENTRY] incidents_facade.IncidentsFacade.analyze_recurrence → recurrence_analysis_engine:RecurrenceAnalysisService.analyze_recurrence
[ENTRY] incidents_facade.IncidentsFacade.detect_patterns → incident_pattern_engine:IncidentPatternService.detect_patterns
[ENTRY] incidents_facade.IncidentsFacade.get_incident_detail → incidents_facade_driver:IncidentsFacadeDriver.fetch_incident_by_id
[ENTRY] incidents_facade.IncidentsFacade.get_incident_learnings → postmortem_engine:PostMortemService.get_incident_learnings
[INTERNAL] incidents_facade.IncidentsFacade.get_incidents_for_run → incidents_facade:IncidentsFacade._snapshot_to_summary, incidents_facade_driver:IncidentsFacadeDriver.fetch_incidents_by_run
[SUPERSET] incidents_facade.IncidentsFacade.get_metrics → incidents_facade_driver:IncidentsFacadeDriver.fetch_metrics_aggregates
[CANONICAL] incidents_facade.IncidentsFacade.list_active_incidents → incidents_facade:IncidentsFacade._snapshot_to_summary, incidents_facade_driver:IncidentsFacadeDriver.fetch_active_incidents
[SUPERSET] incidents_facade.IncidentsFacade.list_historical_incidents → incidents_facade:IncidentsFacade._snapshot_to_summary, incidents_facade_driver:IncidentsFacadeDriver.fetch_historical_incidents
[SUPERSET] incidents_facade.IncidentsFacade.list_resolved_incidents → incidents_facade:IncidentsFacade._snapshot_to_summary, incidents_facade_driver:IncidentsFacadeDriver.fetch_resolved_incidents
[LEAF] incidents_facade.get_incidents_facade
[WRAPPER] incidents_facade_driver.IncidentsFacadeDriver.__init__
[WRAPPER] incidents_facade_driver.IncidentsFacadeDriver._to_snapshot
[CANONICAL] incidents_facade_driver.IncidentsFacadeDriver.fetch_active_incidents → incidents_facade_driver:IncidentsFacadeDriver._to_snapshot
[LEAF] incidents_facade_driver.IncidentsFacadeDriver.fetch_cost_impact_data
[SUPERSET] incidents_facade_driver.IncidentsFacadeDriver.fetch_historical_incidents → incidents_facade_driver:IncidentsFacadeDriver._to_snapshot
[INTERNAL] incidents_facade_driver.IncidentsFacadeDriver.fetch_incident_by_id → incidents_facade_driver:IncidentsFacadeDriver._to_snapshot
[INTERNAL] incidents_facade_driver.IncidentsFacadeDriver.fetch_incidents_by_run → incidents_facade_driver:IncidentsFacadeDriver._to_snapshot
[LEAF] incidents_facade_driver.IncidentsFacadeDriver.fetch_metrics_aggregates
[SUPERSET] incidents_facade_driver.IncidentsFacadeDriver.fetch_resolved_incidents → incidents_facade_driver:IncidentsFacadeDriver._to_snapshot
[WRAPPER] lessons_driver.LessonsDriver.__init__
[LEAF] lessons_driver.LessonsDriver.fetch_debounce_count
[LEAF] lessons_driver.LessonsDriver.fetch_expired_deferred
[LEAF] lessons_driver.LessonsDriver.fetch_lesson_by_id
[LEAF] lessons_driver.LessonsDriver.fetch_lesson_stats
[LEAF] lessons_driver.LessonsDriver.fetch_lessons_list
[LEAF] lessons_driver.LessonsDriver.insert_lesson
[WRAPPER] lessons_driver.LessonsDriver.insert_policy_proposal_from_lesson
[LEAF] lessons_driver.LessonsDriver.update_lesson_converted
[LEAF] lessons_driver.LessonsDriver.update_lesson_deferred
[LEAF] lessons_driver.LessonsDriver.update_lesson_dismissed
[LEAF] lessons_driver.LessonsDriver.update_lesson_reactivated
[WRAPPER] lessons_driver.get_lessons_driver
[WRAPPER] llm_failure_driver.LLMFailureDriver.__init__
[LEAF] llm_failure_driver.LLMFailureDriver.fetch_contamination_check
[LEAF] llm_failure_driver.LLMFailureDriver.fetch_failure_by_run_id
[LEAF] llm_failure_driver.LLMFailureDriver.insert_evidence
[LEAF] llm_failure_driver.LLMFailureDriver.insert_failure
[LEAF] llm_failure_driver.LLMFailureDriver.update_run_failed
[WRAPPER] llm_failure_driver.get_llm_failure_driver
[LEAF] llm_failure_engine.LLMFailureFact.__post_init__
[INTERNAL] llm_failure_engine.LLMFailureService.__init__ → llm_failure_driver:get_llm_failure_driver
[INTERNAL] llm_failure_engine.LLMFailureService._capture_evidence → llm_failure_driver:LLMFailureDriver.insert_evidence
[WRAPPER] llm_failure_engine.LLMFailureService._mark_run_failed → llm_failure_driver:LLMFailureDriver.update_run_failed
[INTERNAL] llm_failure_engine.LLMFailureService._persist_failure → llm_failure_driver:LLMFailureDriver.insert_failure
[SUPERSET] llm_failure_engine.LLMFailureService._verify_no_contamination → llm_failure_driver:LLMFailureDriver.fetch_contamination_check
[ENTRY] llm_failure_engine.LLMFailureService.get_failure_by_run_id → llm_failure_driver:LLMFailureDriver.fetch_failure_by_run_id
[CANONICAL] llm_failure_engine.LLMFailureService.persist_failure_and_mark_run → llm_failure_engine:LLMFailureService._capture_evidence, llm_failure_engine:LLMFailureService._mark_run_failed, llm_failure_engine:LLMFailureService._persist_failure, llm_failure_engine:LLMFailureService._verify_no_contamination
[WRAPPER] policy_violation_driver.PolicyViolationDriver.__init__
[LEAF] policy_violation_driver.PolicyViolationDriver.fetch_incident_by_violation
[LEAF] policy_violation_driver.PolicyViolationDriver.fetch_policy_enabled
[LEAF] policy_violation_driver.PolicyViolationDriver.fetch_violation_exists
[LEAF] policy_violation_driver.PolicyViolationDriver.fetch_violation_truth_check
[LEAF] policy_violation_driver.PolicyViolationDriver.insert_evidence_event
[LEAF] policy_violation_driver.PolicyViolationDriver.insert_policy_evaluation
[LEAF] policy_violation_driver.PolicyViolationDriver.insert_violation_record
[WRAPPER] policy_violation_driver.get_policy_violation_driver
[LEAF] policy_violation_driver.insert_policy_evaluation_sync
[WRAPPER] policy_violation_engine.PolicyViolationService.__init__ → policy_violation_driver:get_policy_violation_driver
[WRAPPER] policy_violation_engine.PolicyViolationService.check_incident_exists → policy_violation_driver:PolicyViolationDriver.fetch_incident_by_violation
[WRAPPER] policy_violation_engine.PolicyViolationService.check_policy_enabled → policy_violation_driver:PolicyViolationDriver.fetch_policy_enabled
[WRAPPER] policy_violation_engine.PolicyViolationService.check_violation_persisted → policy_violation_driver:PolicyViolationDriver.fetch_violation_exists
[SUPERSET] policy_violation_engine.PolicyViolationService.create_incident_from_violation → incident_aggregator:IncidentAggregator.get_or_create_incident, incident_aggregator:create_incident_aggregator, policy_violation_engine:PolicyViolationService.check_violation_persisted
[INTERNAL] policy_violation_engine.PolicyViolationService.persist_evidence → policy_violation_driver:PolicyViolationDriver.insert_evidence_event
[SUPERSET] policy_violation_engine.PolicyViolationService.persist_violation_and_create_incident → policy_violation_engine:PolicyViolationService.check_incident_exists, policy_violation_engine:PolicyViolationService.create_incident_from_violation, policy_violation_engine:PolicyViolationService.persist_evidence, policy_violation_engine:PolicyViolationService.persist_violation_fact, prevention_engine:create_incident_from_violation
[SUPERSET] policy_violation_engine.PolicyViolationService.persist_violation_fact → policy_violation_driver:PolicyViolationDriver.insert_violation_record
[ENTRY] policy_violation_engine.PolicyViolationService.verify_violation_truth → policy_violation_driver:PolicyViolationDriver.fetch_violation_truth_check
[INTERNAL] policy_violation_engine.create_policy_evaluation_record → policy_violation_driver:PolicyViolationDriver.insert_policy_evaluation, policy_violation_driver:get_policy_violation_driver
[CANONICAL] policy_violation_engine.create_policy_evaluation_sync → policy_violation_driver:insert_policy_evaluation_sync
[SUPERSET] policy_violation_engine.handle_policy_evaluation_for_run → policy_violation_engine:create_policy_evaluation_record
[ENTRY] policy_violation_engine.handle_policy_violation → policy_violation_engine:PolicyViolationService.persist_violation_and_create_incident
[WRAPPER] postmortem_driver.PostMortemDriver.__init__
[LEAF] postmortem_driver.PostMortemDriver.fetch_category_stats
[LEAF] postmortem_driver.PostMortemDriver.fetch_recurrence_data
[LEAF] postmortem_driver.PostMortemDriver.fetch_resolution_methods
[LEAF] postmortem_driver.PostMortemDriver.fetch_resolution_summary
[LEAF] postmortem_driver.PostMortemDriver.fetch_similar_incidents
[WRAPPER] postmortem_driver.get_postmortem_driver
[WRAPPER] postmortem_engine.PostMortemService.__init__ → postmortem_driver:get_postmortem_driver
[LEAF] postmortem_engine.PostMortemService._extract_insights
[INTERNAL] postmortem_engine.PostMortemService._find_similar_incidents → postmortem_driver:PostMortemDriver.fetch_similar_incidents
[LEAF] postmortem_engine.PostMortemService._generate_category_insights
[INTERNAL] postmortem_engine.PostMortemService._get_resolution_summary → postmortem_driver:PostMortemDriver.fetch_resolution_summary
[CANONICAL] postmortem_engine.PostMortemService.get_category_learnings → postmortem_driver:PostMortemDriver.fetch_category_stats, postmortem_driver:PostMortemDriver.fetch_recurrence_data, postmortem_driver:PostMortemDriver.fetch_resolution_methods, postmortem_engine:PostMortemService._generate_category_insights
[INTERNAL] postmortem_engine.PostMortemService.get_incident_learnings → postmortem_engine:PostMortemService._extract_insights, postmortem_engine:PostMortemService._find_similar_incidents, postmortem_engine:PostMortemService._get_resolution_summary
[WRAPPER] prevention_engine.BaseValidator.validate
[WRAPPER] prevention_engine.BudgetValidator.__init__
[LEAF] prevention_engine.BudgetValidator.validate
[WRAPPER] prevention_engine.ContentAccuracyValidatorV2.__init__
[LEAF] prevention_engine.ContentAccuracyValidatorV2._extract_claim
[LEAF] prevention_engine.ContentAccuracyValidatorV2._get_value
[SUPERSET] prevention_engine.ContentAccuracyValidatorV2.validate → prevention_engine:ContentAccuracyValidatorV2._extract_claim, prevention_engine:ContentAccuracyValidatorV2._get_value
[WRAPPER] prevention_engine.HallucinationValidator.__init__
[LEAF] prevention_engine.HallucinationValidator._claim_in_context
[SUPERSET] prevention_engine.HallucinationValidator.validate → prevention_engine:HallucinationValidator._claim_in_context
[LEAF] prevention_engine.PIIValidator.__init__
[LEAF] prevention_engine.PIIValidator._redact
[INTERNAL] prevention_engine.PIIValidator.validate → prevention_engine:PIIValidator._redact
[WRAPPER] prevention_engine.PolicyViolation.to_dict
[LEAF] prevention_engine.PreventionContext.hash_output
[LEAF] prevention_engine.PreventionEngine.__init__
[LEAF] prevention_engine.PreventionEngine._emit_metrics
[LEAF] prevention_engine.PreventionEngine._generate_safe_response
[CANONICAL] prevention_engine.PreventionEngine.evaluate → prevention_engine:BaseValidator.validate, prevention_engine:BudgetValidator.validate, prevention_engine:ContentAccuracyValidatorV2.validate, prevention_engine:HallucinationValidator.validate, prevention_engine:PIIValidator.validate, ...+3
[LEAF] prevention_engine.PreventionResult.highest_severity
[LEAF] prevention_engine.PreventionResult.primary_violation
[WRAPPER] prevention_engine.PreventionResult.to_dict → hallucination_detector:HallucinationIndicator.to_dict, prevention_engine:PolicyViolation.to_dict, recovery_rule_engine:EvaluationResult.to_dict, recovery_rule_engine:RuleContext.to_dict, recovery_rule_engine:RuleResult.to_dict
[LEAF] prevention_engine.SafetyValidator.__init__
[LEAF] prevention_engine.SafetyValidator.validate
[INTERNAL] prevention_engine._create_incident_with_service → policy_violation_engine:PolicyViolationService.persist_violation_and_create_incident
[SUPERSET] prevention_engine.create_incident_from_violation → prevention_engine:_create_incident_with_service
[ENTRY] prevention_engine.evaluate_prevention → prevention_engine:PreventionEngine.evaluate, prevention_engine:get_prevention_engine, recovery_rule_engine:CompositeRule.evaluate, recovery_rule_engine:ErrorCodeRule.evaluate, recovery_rule_engine:HistoricalPatternRule.evaluate, ...+4
[LEAF] prevention_engine.get_prevention_engine
[INTERNAL] recovery_rule_engine.CompositeRule.__init__ → anomaly_bridge:AnomalyIncidentBridge.__init__, export_bundle_driver:ExportBundleService.__init__, hallucination_detector:HallucinationDetector.__init__, incident_aggregator:IncidentAggregator.__init__, incident_driver:IncidentDriver.__init__, ...+30
[SUPERSET] recovery_rule_engine.CompositeRule.evaluate → hallucination_detector:HallucinationIndicator.to_dict, prevention_engine:PolicyViolation.to_dict, prevention_engine:PreventionEngine.evaluate, prevention_engine:PreventionResult.to_dict, recovery_rule_engine:ErrorCodeRule.evaluate, ...+8
[INTERNAL] recovery_rule_engine.ErrorCodeRule.__init__ → anomaly_bridge:AnomalyIncidentBridge.__init__, export_bundle_driver:ExportBundleService.__init__, hallucination_detector:HallucinationDetector.__init__, incident_aggregator:IncidentAggregator.__init__, incident_driver:IncidentDriver.__init__, ...+30
[LEAF] recovery_rule_engine.ErrorCodeRule.evaluate
[WRAPPER] recovery_rule_engine.EvaluationResult.to_dict → hallucination_detector:HallucinationIndicator.to_dict, prevention_engine:PolicyViolation.to_dict, prevention_engine:PreventionResult.to_dict, recovery_rule_engine:RuleContext.to_dict, recovery_rule_engine:RuleResult.to_dict
[WRAPPER] recovery_rule_engine.HistoricalPatternRule.__init__ → anomaly_bridge:AnomalyIncidentBridge.__init__, export_bundle_driver:ExportBundleService.__init__, hallucination_detector:HallucinationDetector.__init__, incident_aggregator:IncidentAggregator.__init__, incident_driver:IncidentDriver.__init__, ...+30
[LEAF] recovery_rule_engine.HistoricalPatternRule.evaluate
[INTERNAL] recovery_rule_engine.OccurrenceThresholdRule.__init__ → anomaly_bridge:AnomalyIncidentBridge.__init__, export_bundle_driver:ExportBundleService.__init__, hallucination_detector:HallucinationDetector.__init__, incident_aggregator:IncidentAggregator.__init__, incident_driver:IncidentDriver.__init__, ...+30
[LEAF] recovery_rule_engine.OccurrenceThresholdRule.evaluate
[WRAPPER] recovery_rule_engine.RecoveryRuleEngine.__init__
[WRAPPER] recovery_rule_engine.RecoveryRuleEngine.add_rule
[CANONICAL] recovery_rule_engine.RecoveryRuleEngine.evaluate → prevention_engine:PreventionEngine.evaluate, recovery_rule_engine:CompositeRule.evaluate, recovery_rule_engine:ErrorCodeRule.evaluate, recovery_rule_engine:HistoricalPatternRule.evaluate, recovery_rule_engine:OccurrenceThresholdRule.evaluate, ...+2
[WRAPPER] recovery_rule_engine.RecoveryRuleEngine.remove_rule
[LEAF] recovery_rule_engine.Rule.__init__
[WRAPPER] recovery_rule_engine.Rule.__repr__
[WRAPPER] recovery_rule_engine.Rule.evaluate
[WRAPPER] recovery_rule_engine.RuleContext.to_dict
[WRAPPER] recovery_rule_engine.RuleResult.to_dict
[INTERNAL] recovery_rule_engine.SkillSpecificRule.__init__ → anomaly_bridge:AnomalyIncidentBridge.__init__, export_bundle_driver:ExportBundleService.__init__, hallucination_detector:HallucinationDetector.__init__, incident_aggregator:IncidentAggregator.__init__, incident_driver:IncidentDriver.__init__, ...+30
[LEAF] recovery_rule_engine.SkillSpecificRule.evaluate
[LEAF] recovery_rule_engine.classify_error_category
[WRAPPER] recovery_rule_engine.combine_confidences
[ENTRY] recovery_rule_engine.evaluate_rules → prevention_engine:PreventionEngine.evaluate, recovery_rule_engine:CompositeRule.evaluate, recovery_rule_engine:ErrorCodeRule.evaluate, recovery_rule_engine:HistoricalPatternRule.evaluate, recovery_rule_engine:OccurrenceThresholdRule.evaluate, ...+4
[WRAPPER] recovery_rule_engine.should_auto_execute
[WRAPPER] recovery_rule_engine.should_select_action
[LEAF] recovery_rule_engine.suggest_recovery_mode
[WRAPPER] recurrence_analysis_driver.RecurrenceAnalysisDriver.__init__
[LEAF] recurrence_analysis_driver.RecurrenceAnalysisDriver.fetch_recurrence_for_category
[LEAF] recurrence_analysis_driver.RecurrenceAnalysisDriver.fetch_recurrence_groups
[WRAPPER] recurrence_analysis_engine.RecurrenceAnalysisService.__init__
[WRAPPER] recurrence_analysis_engine.RecurrenceAnalysisService._snapshot_to_group
[INTERNAL] recurrence_analysis_engine.RecurrenceAnalysisService.analyze_recurrence → recurrence_analysis_driver:RecurrenceAnalysisDriver.fetch_recurrence_groups, recurrence_analysis_engine:RecurrenceAnalysisService._snapshot_to_group
[ENTRY] recurrence_analysis_engine.RecurrenceAnalysisService.get_recurrence_for_category → recurrence_analysis_driver:RecurrenceAnalysisDriver.fetch_recurrence_for_category, recurrence_analysis_engine:RecurrenceAnalysisService._snapshot_to_group
[WRAPPER] semantic_failures.format_violation_message → semantic_failures:get_failure_info
[LEAF] semantic_failures.get_failure_info
[WRAPPER] semantic_failures.get_fix_action → semantic_failures:get_failure_info
[WRAPPER] semantic_failures.get_fix_owner → semantic_failures:get_failure_info
[WRAPPER] semantic_failures.get_violation_class → semantic_failures:get_failure_info
```
