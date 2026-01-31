# Incidents — Canonical Registry

**Domain:** incidents  
**Scripts:** 27  
**Generator:** `scripts/ops/hoc_software_bible_generator.py`

Each script's purpose, canonical function, role, callers, and delegates.
This is the auditable artifact for domain consolidation.

---

## anomaly_bridge

- **Layer:** L5
- **Script Role:** PATTERN_ANALYSIS
- **Purpose:** Pattern detection and analysis for anomaly bridge
- **Canonical Function:** `AnomalyIncidentBridge.ingest`
- **Canonical Role:** CANONICAL
- **Decisions:** 3
- **Functions:** 8
- **Callers:** L5:cost_anomaly_detector, incident_aggregator, recovery_rule_engine
- **Delegates To:** incident_aggregator, incident_write_driver
- **Status:** ACTIVE

## hallucination_detector

- **Layer:** L5
- **Script Role:** DETECTION
- **Purpose:** Detection and classification for hallucination detector
- **Canonical Function:** `HallucinationDetector.detect`
- **Canonical Role:** CANONICAL
- **Decisions:** 6
- **Functions:** 11
- **Callers:** ?:hallucination_hook | ?:__init__, prevention_engine, recovery_rule_engine
- **Delegates To:** prevention_engine, recovery_rule_engine
- **Status:** ACTIVE

## incident_driver

- **Layer:** L5
- **Script Role:** ORCHESTRATION
- **Purpose:** Internal orchestration facade delegating to domain engines for incident driver
- **Canonical Function:** `IncidentDriver.create_incident_for_run`
- **Canonical Role:** CANONICAL
- **Decisions:** 1
- **Functions:** 7
- **Callers:** ?:incident_driver | ?:__init__ | L4:transaction_coordinator, incident_engine, recovery_rule_engine
- **Delegates To:** incident_engine, incidents_facade
- **Overlap Verdict:** FACADE_PATTERN
- **Status:** ACTIVE

## incident_engine

- **Layer:** L5
- **Script Role:** DECISION_ENGINE
- **Purpose:** Business decision logic for incident engine
- **Canonical Function:** `IncidentEngine.create_incident_for_run`
- **Canonical Role:** CANONICAL
- **Decisions:** 6
- **Functions:** 14
- **Callers:** ?:hallucination_detector | ?:incident_driver | L5:incident_driver | L5:hallucination_detector | ?:inject_synthetic, incident_driver, recovery_rule_engine
- **Delegates To:** incident_driver, incident_write_driver
- **Overlap Verdict:** FACADE_PATTERN
- **Status:** ACTIVE

## incident_pattern_engine

- **Layer:** L5
- **Script Role:** PATTERN_ANALYSIS
- **Purpose:** Pattern detection and analysis for incident pattern engine
- **Canonical Function:** `IncidentPatternService._detect_cascade_failures`
- **Canonical Role:** INTERNAL
- **Decisions:** 0
- **Functions:** 5
- **Callers:** L5:incidents_facade, incidents_facade, recovery_rule_engine
- **Delegates To:** incident_pattern_driver
- **Status:** ACTIVE

## incident_read_engine

- **Layer:** L5
- **Script Role:** READ_SERVICE
- **Purpose:** Read-only query interface for incident read engine
- **Canonical Function:** `IncidentReadService.__init__`
- **Canonical Role:** WRAPPER
- **Decisions:** 0
- **Functions:** 7
- **Callers:** L5:customer_incidents_adapter | L3:customer_incidents_adapter, recovery_rule_engine
- **Delegates To:** incident_read_driver
- **Status:** ACTIVE

## incident_severity_engine

- **Layer:** L5
- **Script Role:** DECISION_ENGINE
- **Purpose:** Business decision logic for incident severity engine
- **Canonical Function:** `IncidentSeverityEngine.should_escalate`
- **Canonical Role:** SUPERSET
- **Decisions:** 2
- **Functions:** 6
- **Callers:** L6:incident_aggregator, incident_aggregator, recovery_rule_engine
- **Status:** ACTIVE

## incident_write_engine

- **Layer:** L5
- **Script Role:** WRITE_SERVICE
- **Purpose:** Write operations interface for incident write engine
- **Canonical Function:** `IncidentWriteService.resolve_incident`
- **Canonical Role:** CANONICAL
- **Decisions:** 2
- **Functions:** 5
- **Callers:** ?:incident_write_service | L5:customer_incidents_adapter | L3:customer_incidents_adapter, recovery_rule_engine
- **Delegates To:** incident_write_driver
- **Status:** ACTIVE

## incidents_facade

- **Layer:** L5
- **Script Role:** FACADE
- **Purpose:** Customer-facing API projection for incidents facade
- **Canonical Function:** `IncidentsFacade.list_active_incidents`
- **Canonical Role:** CANONICAL
- **Decisions:** 6
- **Functions:** 12
- **Callers:** ?:incidents | L4:incidents_handler | ?:learning_insight_result | ?:recurrence_group_result | ?:recurrence_analysis_result | ?:resolution_summary_result | ?:pattern_match_result | ?:learnings_result | ?:pattern_detection_result, incident_driver
- **Delegates To:** incident_pattern_engine, incidents_facade_driver, postmortem_engine, recurrence_analysis_engine
- **Status:** ACTIVE

## llm_failure_engine

- **Layer:** L5
- **Script Role:** DETECTION
- **Purpose:** Detection and classification for llm failure engine
- **Canonical Function:** `LLMFailureService.persist_failure_and_mark_run`
- **Canonical Role:** CANONICAL
- **Decisions:** 1
- **Functions:** 8
- **Callers:** ?:llm_failure_service, recovery_rule_engine
- **Delegates To:** llm_failure_driver
- **Status:** ACTIVE

## policy_violation_engine

- **Layer:** L5
- **Script Role:** POLICY
- **Purpose:** Policy validation and enforcement for policy violation engine
- **Canonical Function:** `create_policy_evaluation_sync`
- **Canonical Role:** CANONICAL
- **Decisions:** 5
- **Functions:** 13
- **Callers:** prevention_engine, recovery_rule_engine
- **Delegates To:** incident_aggregator, policy_violation_driver, prevention_engine
- **Uncalled Functions:**
  - `PolicyViolationService.check_policy_enabled` → PENDING (PIN-470): Design-ahead infrastructure
  - `PolicyViolationService.verify_violation_truth` → PENDING (PIN-470): Design-ahead infrastructure
  - `create_policy_evaluation_sync` → PENDING (PIN-470): Design-ahead infrastructure
  - `handle_policy_evaluation_for_run` → PENDING (PIN-470): Design-ahead infrastructure
  - `handle_policy_violation` → PENDING (PIN-470): Design-ahead infrastructure
- **Status:** ACTIVE

## postmortem_engine

- **Layer:** L5
- **Script Role:** ANALYSIS
- **Purpose:** Post-incident analysis for postmortem engine
- **Canonical Function:** `PostMortemService.get_category_learnings`
- **Canonical Role:** CANONICAL
- **Decisions:** 1
- **Functions:** 7
- **Callers:** L5:incidents_facade, incidents_facade, recovery_rule_engine
- **Delegates To:** postmortem_driver
- **Status:** ACTIVE

## prevention_engine

- **Layer:** L5
- **Script Role:** POLICY
- **Purpose:** Policy validation and enforcement for prevention engine
- **Canonical Function:** `PreventionEngine.evaluate`
- **Canonical Role:** CANONICAL
- **Decisions:** 6
- **Functions:** 28
- **Callers:** ?:arbitrator | ?:__init__ | ?:scope_resolver | ?:step_enforcement | L7:override_authority | L7:monitor_config | L7:threshold_signal | ?:alert_emitter | ?:authority_checker | L6:arbitrator, hallucination_detector, policy_violation_engine, recovery_rule_engine
- **Delegates To:** hallucination_detector, policy_violation_engine, recovery_rule_engine
- **Overlap Verdict:** FACADE_PATTERN
- **Status:** ACTIVE

## recovery_rule_engine

- **Layer:** L5
- **Script Role:** RECOVERY
- **Purpose:** Failure recovery rule evaluation for recovery rule engine
- **Canonical Function:** `RecoveryRuleEngine.evaluate`
- **Canonical Role:** CANONICAL
- **Decisions:** 4
- **Functions:** 26
- **Callers:** ?:recovery | ?:failure_intelligence | ?:failure_classification_engine | ?:recovery_evaluation_engine | L5:recovery_evaluation_engine | L2:recovery | ?:test_m10_recovery_enhanced, hallucination_detector, prevention_engine
- **Delegates To:** anomaly_bridge, export_bundle_driver, hallucination_detector, incident_aggregator, incident_driver, incident_engine, incident_pattern_driver, incident_pattern_engine, incident_read_driver, incident_read_engine, incident_severity_engine, incident_write_driver, incident_write_engine, incidents_facade_driver, lessons_driver, llm_failure_driver, llm_failure_engine, policy_violation_driver, policy_violation_engine, postmortem_driver, postmortem_engine, prevention_engine, recurrence_analysis_driver, recurrence_analysis_engine
- **Overlap Verdict:** FACADE_PATTERN
- **Status:** ACTIVE

## recurrence_analysis_engine

- **Layer:** L5
- **Script Role:** PATTERN_ANALYSIS
- **Purpose:** Pattern detection and analysis for recurrence analysis engine
- **Canonical Function:** `RecurrenceAnalysisService.analyze_recurrence`
- **Canonical Role:** INTERNAL
- **Decisions:** 0
- **Functions:** 4
- **Callers:** L5:incidents_facade, incidents_facade, recovery_rule_engine
- **Delegates To:** recurrence_analysis_driver
- **Status:** ACTIVE

## semantic_failures

- **Layer:** L5
- **Script Role:** DETECTION
- **Purpose:** Detection and classification for semantic failures
- **Canonical Function:** `get_failure_info`
- **Canonical Role:** LEAF
- **Decisions:** 0
- **Functions:** 5
- **Callers:** ?:semantic_validator | ?:__init__
- **Status:** ACTIVE

## export_bundle_driver

- **Layer:** L6
- **Script Role:** PERSISTENCE
- **Purpose:** Database operations (L6 driver) for export bundle driver
- **Canonical Function:** `ExportBundleService.create_evidence_bundle`
- **Canonical Role:** CANONICAL
- **Decisions:** 4
- **Functions:** 12
- **Callers:** L2:incidents, recovery_rule_engine
- **Status:** ACTIVE

## incident_aggregator

- **Layer:** L6
- **Script Role:** AGGREGATION
- **Purpose:** Incident aggregation and lifecycle management for incident aggregator
- **Canonical Function:** `IncidentAggregator._add_call_to_incident`
- **Canonical Role:** SUPERSET
- **Decisions:** 3
- **Functions:** 14
- **Callers:** L5:policy_violation_engine, anomaly_bridge, policy_violation_engine, recovery_rule_engine
- **Delegates To:** anomaly_bridge, incident_severity_engine
- **Status:** ACTIVE

## incident_pattern_driver

- **Layer:** L6
- **Script Role:** PERSISTENCE
- **Purpose:** Database operations (L6 driver) for incident pattern driver
- **Canonical Function:** `IncidentPatternDriver.fetch_cascade_failures`
- **Canonical Role:** LEAF
- **Decisions:** 0
- **Functions:** 6
- **Callers:** L5:incident_pattern_engine, incident_pattern_engine, recovery_rule_engine
- **Status:** ACTIVE

## incident_read_driver

- **Layer:** L6
- **Script Role:** PERSISTENCE
- **Purpose:** Database operations (L6 driver) for incident read driver
- **Canonical Function:** `IncidentReadDriver.count_incidents_since`
- **Canonical Role:** LEAF
- **Decisions:** 0
- **Functions:** 7
- **Callers:** L6:__init__ | L5:incident_read_engine, incident_read_engine, recovery_rule_engine
- **Status:** ACTIVE

## incident_write_driver

- **Layer:** L6
- **Script Role:** PERSISTENCE
- **Purpose:** Database operations (L6 driver) for incident write driver
- **Canonical Function:** `IncidentWriteDriver.fetch_incidents_by_run_id`
- **Canonical Role:** LEAF
- **Decisions:** 0
- **Functions:** 13
- **Callers:** ?:incident_write_engine | L6:__init__ | L5:incident_write_engine | L5:incident_engine | L5:anomaly_bridge, anomaly_bridge, incident_engine, incident_write_engine, recovery_rule_engine
- **Status:** ACTIVE

## incidents_facade_driver

- **Layer:** L6
- **Script Role:** FACADE
- **Purpose:** Customer-facing API projection for incidents facade driver
- **Canonical Function:** `IncidentsFacadeDriver.fetch_active_incidents`
- **Canonical Role:** CANONICAL
- **Decisions:** 7
- **Functions:** 9
- **Callers:** L5:incidents_facade, incidents_facade, recovery_rule_engine
- **Status:** ACTIVE

## lessons_driver

- **Layer:** L6
- **Script Role:** PERSISTENCE
- **Purpose:** Database operations (L6 driver) for lessons driver
- **Canonical Function:** `LessonsDriver.fetch_debounce_count`
- **Canonical Role:** LEAF
- **Decisions:** 1
- **Functions:** 13
- **Callers:** L5:lessons_engine, recovery_rule_engine
- **Status:** ACTIVE

## llm_failure_driver

- **Layer:** L6
- **Script Role:** PERSISTENCE
- **Purpose:** Database operations (L6 driver) for llm failure driver
- **Canonical Function:** `LLMFailureDriver.fetch_contamination_check`
- **Canonical Role:** LEAF
- **Decisions:** 0
- **Functions:** 7
- **Callers:** ?:llm_failure_engine | L5:llm_failure_engine, llm_failure_engine, recovery_rule_engine
- **Status:** ACTIVE

## policy_violation_driver

- **Layer:** L6
- **Script Role:** PERSISTENCE
- **Purpose:** Database operations (L6 driver) for policy violation driver
- **Canonical Function:** `PolicyViolationDriver.fetch_incident_by_violation`
- **Canonical Role:** LEAF
- **Decisions:** 0
- **Functions:** 10
- **Callers:** L5:policy_violation_engine, policy_violation_engine, recovery_rule_engine
- **Status:** ACTIVE

## postmortem_driver

- **Layer:** L6
- **Script Role:** PERSISTENCE
- **Purpose:** Database operations (L6 driver) for postmortem driver
- **Canonical Function:** `PostMortemDriver.fetch_category_stats`
- **Canonical Role:** LEAF
- **Decisions:** 1
- **Functions:** 7
- **Callers:** L5:postmortem_engine, postmortem_engine, recovery_rule_engine
- **Status:** ACTIVE

## recurrence_analysis_driver

- **Layer:** L6
- **Script Role:** PERSISTENCE
- **Purpose:** Database operations (L6 driver) for recurrence analysis driver
- **Canonical Function:** `RecurrenceAnalysisDriver.fetch_recurrence_for_category`
- **Canonical Role:** LEAF
- **Decisions:** 1
- **Functions:** 3
- **Callers:** ?:incidents_facade | ?:__init__ | L5:recurrence_analysis_engine, recovery_rule_engine, recurrence_analysis_engine
- **Status:** ACTIVE
