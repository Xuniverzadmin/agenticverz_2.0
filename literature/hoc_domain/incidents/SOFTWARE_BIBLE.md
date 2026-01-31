# Incidents — Software Bible

**Domain:** incidents  
**L2 Features:** 22  
**Scripts:** 27  
**Generator:** `scripts/ops/hoc_software_bible_generator.py`

---

## Script Registry

Each script's unique contribution and canonical function.

| Script | Layer | Script Role | Canonical Function | Role | Decisions | Callers | Status |
|--------|-------|-------------|--------------------|----- |-----------|---------|--------|
| anomaly_bridge | L5 | PATTERN_ANALYSIS | `AnomalyIncidentBridge.ingest` | CANONICAL | 3 | L5:cost_anomaly_detector, incident_aggregator, recovery_rule_engine | YES |
| hallucination_detector | L5 | DETECTION | `HallucinationDetector.detect` | CANONICAL | 6 | ?:hallucination_hook | ?:__init__, prevention_engine, recovery_rule_engine | YES |
| incident_driver | L5 | ORCHESTRATION | `IncidentDriver.create_incident_for_run` | CANONICAL | 1 | ?:incident_driver | ?:__init__ | L4:transaction_coordinator, incident_engine, recovery_rule_engine | FACADE_PATTERN |
| incident_engine | L5 | DECISION_ENGINE | `IncidentEngine.create_incident_for_run` | CANONICAL | 6 | ?:hallucination_detector | ?:incident_driver | L5:incident_driver | L5:hallucination_detector | ?:inject_synthetic, incident_driver, recovery_rule_engine | FACADE_PATTERN |
| incident_pattern_engine | L5 | PATTERN_ANALYSIS | `IncidentPatternService._detect_cascade_failures` | INTERNAL | 0 | L5:incidents_facade, incidents_facade, recovery_rule_engine | YES |
| incident_read_engine | L5 | READ_SERVICE | `IncidentReadService.__init__` | WRAPPER | 0 | L5:customer_incidents_adapter | L3:customer_incidents_adapter, recovery_rule_engine | INTERFACE |
| incident_severity_engine | L5 | DECISION_ENGINE | `IncidentSeverityEngine.should_escalate` | SUPERSET | 2 | L6:incident_aggregator, incident_aggregator, recovery_rule_engine | YES |
| incident_write_engine | L5 | WRITE_SERVICE | `IncidentWriteService.resolve_incident` | CANONICAL | 2 | ?:incident_write_service | L5:customer_incidents_adapter | L3:customer_incidents_adapter, recovery_rule_engine | YES |
| incidents_facade | L5 | FACADE | `IncidentsFacade.list_active_incidents` | CANONICAL | 6 | ?:incidents | L4:incidents_handler | ?:learning_insight_result | ?:recurrence_group_result | ?:recurrence_analysis_result | ?:resolution_summary_result | ?:pattern_match_result | ?:learnings_result | ?:pattern_detection_result, incident_driver | YES |
| llm_failure_engine | L5 | DETECTION | `LLMFailureService.persist_failure_and_mark_run` | CANONICAL | 1 | ?:llm_failure_service, recovery_rule_engine | YES |
| policy_violation_engine | L5 | POLICY | `create_policy_evaluation_sync` | CANONICAL | 5 | prevention_engine, recovery_rule_engine | YES |
| postmortem_engine | L5 | ANALYSIS | `PostMortemService.get_category_learnings` | CANONICAL | 1 | L5:incidents_facade, incidents_facade, recovery_rule_engine | YES |
| prevention_engine | L5 | POLICY | `PreventionEngine.evaluate` | CANONICAL | 6 | ?:arbitrator | ?:__init__ | ?:scope_resolver | ?:step_enforcement | L7:override_authority | L7:monitor_config | L7:threshold_signal | ?:alert_emitter | ?:authority_checker | L6:arbitrator, hallucination_detector, policy_violation_engine +1 | FACADE_PATTERN |
| recovery_rule_engine | L5 | RECOVERY | `RecoveryRuleEngine.evaluate` | CANONICAL | 4 | ?:recovery | ?:failure_intelligence | ?:failure_classification_engine | ?:recovery_evaluation_engine | L5:recovery_evaluation_engine | L2:recovery | ?:test_m10_recovery_enhanced, hallucination_detector, prevention_engine | FACADE_PATTERN |
| recurrence_analysis_engine | L5 | PATTERN_ANALYSIS | `RecurrenceAnalysisService.analyze_recurrence` | INTERNAL | 0 | L5:incidents_facade, incidents_facade, recovery_rule_engine | YES |
| semantic_failures | L5 | DETECTION | `get_failure_info` | LEAF | 0 | ?:semantic_validator | ?:__init__ | YES |
| export_bundle_driver | L6 | PERSISTENCE | `ExportBundleService.create_evidence_bundle` | CANONICAL | 4 | L2:incidents, recovery_rule_engine | YES |
| incident_aggregator | L6 | AGGREGATION | `IncidentAggregator._add_call_to_incident` | SUPERSET | 3 | L5:policy_violation_engine, anomaly_bridge, policy_violation_engine +1 | YES |
| incident_pattern_driver | L6 | PERSISTENCE | `IncidentPatternDriver.fetch_cascade_failures` | LEAF | 0 | L5:incident_pattern_engine, incident_pattern_engine, recovery_rule_engine | YES |
| incident_read_driver | L6 | PERSISTENCE | `IncidentReadDriver.count_incidents_since` | LEAF | 0 | L6:__init__ | L5:incident_read_engine, incident_read_engine, recovery_rule_engine | YES |
| incident_write_driver | L6 | PERSISTENCE | `IncidentWriteDriver.fetch_incidents_by_run_id` | LEAF | 0 | ?:incident_write_engine | L6:__init__ | L5:incident_write_engine | L5:incident_engine | L5:anomaly_bridge, anomaly_bridge, incident_engine +2 | YES |
| incidents_facade_driver | L6 | FACADE | `IncidentsFacadeDriver.fetch_active_incidents` | CANONICAL | 7 | L5:incidents_facade, incidents_facade, recovery_rule_engine | YES |
| lessons_driver | L6 | PERSISTENCE | `LessonsDriver.fetch_debounce_count` | LEAF | 1 | L5:lessons_engine, recovery_rule_engine | YES |
| llm_failure_driver | L6 | PERSISTENCE | `LLMFailureDriver.fetch_contamination_check` | LEAF | 0 | ?:llm_failure_engine | L5:llm_failure_engine, llm_failure_engine, recovery_rule_engine | YES |
| policy_violation_driver | L6 | PERSISTENCE | `PolicyViolationDriver.fetch_incident_by_violation` | LEAF | 0 | L5:policy_violation_engine, policy_violation_engine, recovery_rule_engine | YES |
| postmortem_driver | L6 | PERSISTENCE | `PostMortemDriver.fetch_category_stats` | LEAF | 1 | L5:postmortem_engine, postmortem_engine, recovery_rule_engine | YES |
| recurrence_analysis_driver | L6 | PERSISTENCE | `RecurrenceAnalysisDriver.fetch_recurrence_for_category` | LEAF | 1 | ?:incidents_facade | ?:__init__ | L5:recurrence_analysis_engine, recovery_rule_engine, recurrence_analysis_engine | YES |

## Uncalled Functions

Functions with no internal or external callers detected, classified by analysis.

| Function | Classification | Reason |
|----------|----------------|--------|
| `policy_violation_engine.PolicyViolationService.check_policy_enabled` | **PENDING** (PIN-470) | Design-ahead infrastructure |
| `policy_violation_engine.PolicyViolationService.verify_violation_truth` | **PENDING** (PIN-470) | Design-ahead infrastructure |
| `policy_violation_engine.create_policy_evaluation_sync` | **PENDING** (PIN-470) | Design-ahead infrastructure |
| `policy_violation_engine.handle_policy_evaluation_for_run` | **PENDING** (PIN-470) | Design-ahead infrastructure |
| `policy_violation_engine.handle_policy_violation` | **PENDING** (PIN-470) | Design-ahead infrastructure |

## Facade Patterns (same noun, different roles — NOT duplicates)

These scripts share a noun but serve structurally distinct roles.

- `incident_driver` (ORCHESTRATION) — canonical: `IncidentDriver.create_incident_for_run` (CANONICAL)
- `incident_engine` (DECISION_ENGINE) — canonical: `IncidentEngine.create_incident_for_run` (CANONICAL)
- `prevention_engine` (POLICY) — canonical: `PreventionEngine.evaluate` (CANONICAL)
- `recovery_rule_engine` (RECOVERY) — canonical: `RecoveryRuleEngine.evaluate` (CANONICAL)

## L2 Feature Chains

| Status | Count |
|--------|-------|
| COMPLETE (L2→L4→L5→L6) | 22 |
| GAP (L2→L5 direct) | 0 |

### Wired Features (L2→L4→L5→L6)

#### GET /active
```
L2:incidents.list_active_incidents → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /by-run/{run_id}
```
L2:incidents.get_incidents_for_run → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /cost-impact
```
L2:incidents.analyze_cost_impact → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /explained
```
L2:cost_guard.get_cost_explained → L4:incidents_handler → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /historical
```
L2:incidents.list_historical_incidents → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /historical/cost-trend
```
L2:incidents.get_historical_cost_trend → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /historical/distribution
```
L2:incidents.get_historical_distribution → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /historical/trend
```
L2:incidents.get_historical_trend → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /incidents
```
L2:cost_guard.get_cost_incidents → L4:incidents_handler → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /metrics
```
L2:incidents.get_incident_metrics → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /patterns
```
L2:incidents.detect_patterns → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /recurring
```
L2:incidents.analyze_recurrence → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /resolved
```
L2:incidents.list_resolved_incidents → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /summary
```
L2:cost_guard.get_cost_summary → L4:incidents_handler → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /{incident_id}
```
L2:incidents.get_incident_detail → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /{incident_id}/evidence
```
L2:incidents.get_incident_evidence → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /{incident_id}/learnings
```
L2:incidents.get_incident_learnings → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### GET /{incident_id}/proof
```
L2:incidents.get_incident_proof → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### POST /{incident_id}/export/evidence
```
L2:incidents.export_evidence → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### POST /{incident_id}/export/executive-debrief
```
L2:incidents.export_executive_debrief → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### POST /{incident_id}/export/soc2
```
L2:incidents.export_soc2 → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

#### list_incidents
```
L2:incidents.list_incidents → L4:OperationContext | get_operation_registry → L6:incident_aggregator.IncidentAggregator._add_call_to_incident
```

## Canonical Algorithm Inventory

| Function | File | Role | Decisions | Stmts | Persistence | Delegates To |
|----------|------|------|-----------|-------|-------------|--------------|
| `AnomalyIncidentBridge.ingest` | anomaly_bridge | CANONICAL | 3 | 5 | no | anomaly_bridge:AnomalyIncidentBridge._check_existing_inciden |
| `CompositeRule.evaluate` | recovery_rule_engine | SUPERSET | 2 | 6 | no | hallucination_detector:HallucinationIndicator.to_dict | prev |
| `ContentAccuracyValidatorV2.validate` | prevention_engine | SUPERSET | 4 | 8 | no | prevention_engine:ContentAccuracyValidatorV2._extract_claim  |
| `ExportBundleService.create_evidence_bundle` | export_bundle_driver | CANONICAL | 4 | 1 | no | export_bundle_driver:ExportBundleService._compute_bundle_has |
| `ExportBundleService.create_executive_debrief` | export_bundle_driver | SUPERSET | 4 | 1 | no | export_bundle_driver:ExportBundleService._assess_business_im |
| `HallucinationDetector.detect` | hallucination_detector | CANONICAL | 6 | 10 | no | hallucination_detector:HallucinationDetector._detect_contrad |
| `HallucinationValidator.validate` | prevention_engine | SUPERSET | 2 | 3 | no | prevention_engine:HallucinationValidator._claim_in_context |
| `IncidentAggregator._add_call_to_incident` | incident_aggregator | SUPERSET | 3 | 7 | yes | incident_aggregator:IncidentAggregator._add_incident_event | |
| `IncidentAggregator.get_or_create_incident` | incident_aggregator | SUPERSET | 2 | 7 | no | anomaly_bridge:AnomalyIncidentBridge._create_incident | inci |
| `IncidentAggregator.resolve_stale_incidents` | incident_aggregator | SUPERSET | 2 | 10 | yes | incident_aggregator:IncidentAggregator._add_incident_event |
| `IncidentDriver.create_incident_for_run` | incident_driver | CANONICAL | 1 | 6 | no | incident_driver:IncidentDriver._emit_ack | incident_engine:I |
| `IncidentEngine._get_driver` | incident_engine | SUPERSET | 3 | 4 | no | incident_write_driver:get_incident_write_driver |
| `IncidentEngine.check_and_create_incident` | incident_engine | SUPERSET | 2 | 4 | no | incident_engine:IncidentEngine._extract_error_code | inciden |
| `IncidentEngine.create_incident_for_failed_run` | incident_engine | SUPERSET | 3 | 1 | no | incident_engine:IncidentEngine._check_policy_suppression | i |
| `IncidentEngine.create_incident_for_run` | incident_engine | CANONICAL | 6 | 1 | no | incident_engine:IncidentEngine._check_policy_suppression | i |
| `IncidentSeverityEngine.should_escalate` | incident_severity_engine | SUPERSET | 2 | 3 | no | incident_severity_engine:IncidentSeverityEngine.calculate_se |
| `IncidentWriteService.resolve_incident` | incident_write_engine | CANONICAL | 2 | 6 | no | incident_write_driver:IncidentWriteDriver.create_incident_ev |
| `IncidentsFacade.get_metrics` | incidents_facade | SUPERSET | 2 | 7 | no | incidents_facade_driver:IncidentsFacadeDriver.fetch_metrics_ |
| `IncidentsFacade.list_active_incidents` | incidents_facade | CANONICAL | 6 | 13 | no | incidents_facade:IncidentsFacade._snapshot_to_summary | inci |
| `IncidentsFacade.list_historical_incidents` | incidents_facade | SUPERSET | 3 | 11 | no | incidents_facade:IncidentsFacade._snapshot_to_summary | inci |
| `IncidentsFacade.list_resolved_incidents` | incidents_facade | SUPERSET | 6 | 13 | no | incidents_facade:IncidentsFacade._snapshot_to_summary | inci |
| `IncidentsFacadeDriver.fetch_active_incidents` | incidents_facade_driver | CANONICAL | 7 | 17 | yes | incidents_facade_driver:IncidentsFacadeDriver._to_snapshot |
| `IncidentsFacadeDriver.fetch_historical_incidents` | incidents_facade_driver | SUPERSET | 4 | 14 | yes | incidents_facade_driver:IncidentsFacadeDriver._to_snapshot |
| `IncidentsFacadeDriver.fetch_resolved_incidents` | incidents_facade_driver | SUPERSET | 7 | 17 | yes | incidents_facade_driver:IncidentsFacadeDriver._to_snapshot |
| `LLMFailureService._verify_no_contamination` | llm_failure_engine | SUPERSET | 3 | 4 | no | llm_failure_driver:LLMFailureDriver.fetch_contamination_chec |
| `LLMFailureService.persist_failure_and_mark_run` | llm_failure_engine | CANONICAL | 1 | 7 | no | llm_failure_engine:LLMFailureService._capture_evidence | llm |
| `PolicyViolationService.create_incident_from_violation` | policy_violation_engine | SUPERSET | 3 | 7 | no | incident_aggregator:IncidentAggregator.get_or_create_inciden |
| `PolicyViolationService.persist_violation_and_create_incident` | policy_violation_engine | SUPERSET | 3 | 7 | no | policy_violation_engine:PolicyViolationService.check_inciden |
| `PolicyViolationService.persist_violation_fact` | policy_violation_engine | SUPERSET | 4 | 8 | no | policy_violation_driver:PolicyViolationDriver.insert_violati |
| `PostMortemService.get_category_learnings` | postmortem_engine | CANONICAL | 1 | 11 | no | postmortem_driver:PostMortemDriver.fetch_category_stats | po |
| `PreventionEngine.evaluate` | prevention_engine | CANONICAL | 6 | 14 | no | prevention_engine:BaseValidator.validate | prevention_engine |
| `RecoveryRuleEngine.evaluate` | recovery_rule_engine | CANONICAL | 4 | 11 | no | prevention_engine:PreventionEngine.evaluate | recovery_rule_ |
| `create_incident_from_violation` | prevention_engine | SUPERSET | 2 | 4 | no | prevention_engine:_create_incident_with_service |
| `create_policy_evaluation_sync` | policy_violation_engine | CANONICAL | 5 | 10 | no | policy_violation_driver:insert_policy_evaluation_sync |
| `handle_policy_evaluation_for_run` | policy_violation_engine | SUPERSET | 3 | 3 | no | policy_violation_engine:create_policy_evaluation_record |

## Wrapper Inventory

_85 thin delegation functions._

- `anomaly_bridge.AnomalyIncidentBridge.__init__` → incident_write_driver:get_incident_write_driver
- `anomaly_bridge.AnomalyIncidentBridge._build_incident_insert_sql` → ?
- `anomaly_bridge.AnomalyIncidentBridge._check_existing_incident` → ?
- `anomaly_bridge.AnomalyIncidentBridge._meets_severity_threshold` → ?
- `prevention_engine.BaseValidator.validate` → ?
- `prevention_engine.BudgetValidator.__init__` → ?
- `prevention_engine.ContentAccuracyValidatorV2.__init__` → ?
- `recovery_rule_engine.EvaluationResult.to_dict` → hallucination_detector:HallucinationIndicator.to_dict
- `export_bundle_driver.ExportBundleService.__init__` → ?
- `export_bundle_driver.ExportBundleService._assess_business_impact` → ?
- `export_bundle_driver.ExportBundleService._generate_attestation` → ?
- `export_bundle_driver.ExportBundleService._generate_incident_summary` → ?
- `export_bundle_driver.ExportBundleService._generate_recommendations` → ?
- `hallucination_detector.HallucinationIndicator.to_dict` → ?
- `prevention_engine.HallucinationValidator.__init__` → ?
- `recovery_rule_engine.HistoricalPatternRule.__init__` → anomaly_bridge:AnomalyIncidentBridge.__init__
- `incident_driver.IncidentDriver.__init__` → ?
- `incident_driver.IncidentDriver.check_and_create_incident` → incident_engine:IncidentEngine.check_and_create_incident
- `incident_driver.IncidentDriver.get_incidents_for_run` → incident_engine:IncidentEngine.get_incidents_for_run
- `incident_engine.IncidentEngine.__init__` → ?
- `incident_aggregator.IncidentKey.__hash__` → ?
- `incident_pattern_driver.IncidentPatternDriver.__init__` → ?
- `incident_pattern_engine.IncidentPatternService.__init__` → incident_pattern_driver:get_incident_pattern_driver
- `incident_read_driver.IncidentReadDriver.__init__` → ?
- `incident_read_engine.IncidentReadService.__init__` → incident_read_driver:get_incident_read_driver
- `incident_read_engine.IncidentReadService.count_incidents_since` → incident_read_driver:IncidentReadDriver.count_incidents_since
- `incident_read_engine.IncidentReadService.get_incident` → incident_read_driver:IncidentReadDriver.get_incident
- `incident_read_engine.IncidentReadService.get_incident_events` → incident_read_driver:IncidentReadDriver.get_incident_events
- `incident_read_engine.IncidentReadService.get_last_incident` → incident_read_driver:IncidentReadDriver.get_last_incident
- `incident_read_engine.IncidentReadService.list_incidents` → incident_read_driver:IncidentReadDriver.list_incidents
- _...and 55 more_

---

## PIN-504 Amendments (2026-01-31)

| Script | Change | Reference |
|--------|--------|-----------|
| `incident_write_engine` | Removed cross-domain `AuditLedgerService` import. Accepts `audit: Any = None` via dependency injection from L4 handler. | PIN-504 Phase 2 |
