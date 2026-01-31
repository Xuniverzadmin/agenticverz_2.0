# Analytics — Call Graph

**Domain:** analytics  
**Total functions:** 286  
**Generator:** `scripts/ops/hoc_call_chain_tracer.py`

---

## Role Summary

| Role | Count | Description |
|------|-------|-------------|
| CANONICAL | 15 | Owns the algorithm — most decisions, primary logic |
| SUPERSET | 21 | Calls other functions + adds its own decisions |
| WRAPPER | 78 | Thin delegation — ≤3 stmts, no branching |
| LEAF | 118 | Terminal — calls no other domain functions |
| ENTRY | 17 | Entry point — no domain-internal callers |
| INTERNAL | 37 | Called only by other domain functions |

## Canonical Algorithm Owners

### `ai_console_panel_engine.AIConsolePanelEngine.evaluate_panel`
- **Layer:** L5
- **Decisions:** 4
- **Statements:** 3
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** ai_console_panel_engine.AIConsolePanelEngine.evaluate_panel → ai_console_panel_engine.AIConsolePanelEngine._create_short_circuit_response → ai_console_panel_engine.AIConsolePanelEngine._evaluate_panel_slots
- **Calls:** ai_console_panel_engine:AIConsolePanelEngine._create_short_circuit_response, ai_console_panel_engine:AIConsolePanelEngine._evaluate_panel_slots

### `analytics_facade.AnalyticsFacade.get_usage_statistics`
- **Layer:** L5
- **Decisions:** 11
- **Statements:** 20
- **Delegation depth:** 2
- **Persistence:** no
- **Chain:** analytics_facade.AnalyticsFacade.get_usage_statistics → analytics_facade.AnalyticsFacade._calculate_freshness → analytics_facade.SignalAdapter.fetch_cost_metrics → analytics_facade.SignalAdapter.fetch_llm_usage → ...+1
- **Calls:** analytics_facade:AnalyticsFacade._calculate_freshness, analytics_facade:SignalAdapter.fetch_cost_metrics, analytics_facade:SignalAdapter.fetch_llm_usage, analytics_facade:SignalAdapter.fetch_worker_execution

### `canary.CanaryRunner.run`
- **Layer:** L5
- **Decisions:** 2
- **Statements:** 3
- **Delegation depth:** 8
- **Persistence:** no
- **Chain:** canary.CanaryRunner.run → canary.CanaryRunner._run_internal → leader.leader_election
- **Calls:** canary:CanaryRunner._run_internal, leader:leader_election

### `config.is_v2_sandbox_enabled`
- **Layer:** L5
- **Decisions:** 2
- **Statements:** 4
- **Delegation depth:** 2
- **Persistence:** no
- **Chain:** config.is_v2_sandbox_enabled → config.get_config
- **Calls:** config:get_config

### `coordinator.CoordinationManager.apply`
- **Layer:** L5
- **Decisions:** 2
- **Statements:** 14
- **Delegation depth:** 3
- **Persistence:** no
- **Chain:** coordinator.CoordinationManager.apply → coordinator.CoordinationManager._emit_audit_record → coordinator.CoordinationManager._find_preemption_targets → coordinator.CoordinationManager._get_parameter_key → ...+2
- **Calls:** coordinator:CoordinationManager._emit_audit_record, coordinator:CoordinationManager._find_preemption_targets, coordinator:CoordinationManager._get_parameter_key, coordinator:CoordinationManager._revert_envelope, coordinator:CoordinationManager.check_allowed

### `cost_anomaly_detector.CostAnomalyDetector.detect_sustained_drift`
- **Layer:** L5
- **Decisions:** 3
- **Statements:** 12
- **Delegation depth:** 2
- **Persistence:** no
- **Chain:** cost_anomaly_detector.CostAnomalyDetector.detect_sustained_drift → cost_anomaly_detector.CostAnomalyDetector._derive_cause → cost_anomaly_detector.CostAnomalyDetector._reset_drift_tracking → cost_anomaly_detector.CostAnomalyDetector._update_drift_tracking → ...+3
- **Calls:** cost_anomaly_detector:CostAnomalyDetector._derive_cause, cost_anomaly_detector:CostAnomalyDetector._reset_drift_tracking, cost_anomaly_detector:CostAnomalyDetector._update_drift_tracking, cost_anomaly_detector:classify_severity, cost_anomaly_driver:CostAnomalyDriver.fetch_baseline_avg, cost_anomaly_driver:CostAnomalyDriver.fetch_rolling_avg

### `cost_model_engine.estimate_step_cost`
- **Layer:** L5
- **Decisions:** 12
- **Statements:** 7
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** cost_model_engine.estimate_step_cost → cost_model_engine.get_skill_coefficients
- **Calls:** cost_model_engine:get_skill_coefficients

### `cost_snapshots.SnapshotAnomalyDetector.evaluate_snapshot`
- **Layer:** L5
- **Decisions:** 6
- **Statements:** 7
- **Delegation depth:** 1
- **Persistence:** yes
- **Chain:** cost_snapshots.SnapshotAnomalyDetector.evaluate_snapshot → cost_snapshots.SnapshotAnomalyDetector._create_anomaly_from_evaluation → cost_snapshots.SnapshotAnomalyDetector._get_snapshot → cost_snapshots.SnapshotAnomalyDetector._insert_evaluation
- **Calls:** cost_snapshots:SnapshotAnomalyDetector._create_anomaly_from_evaluation, cost_snapshots:SnapshotAnomalyDetector._get_snapshot, cost_snapshots:SnapshotAnomalyDetector._insert_evaluation

### `datasets.DatasetValidator.validate_dataset`
- **Layer:** L5
- **Decisions:** 7
- **Statements:** 12
- **Delegation depth:** 4
- **Persistence:** no
- **Chain:** datasets.DatasetValidator.validate_dataset → datasets.DatasetValidator._calculate_drift_score → sandbox.CostSimSandbox.simulate
- **Calls:** datasets:DatasetValidator._calculate_drift_score, sandbox:CostSimSandbox.simulate

### `divergence.DivergenceAnalyzer.generate_report`
- **Layer:** L5
- **Decisions:** 3
- **Statements:** 8
- **Delegation depth:** 9
- **Persistence:** no
- **Chain:** divergence.DivergenceAnalyzer.generate_report → canary.CanaryRunner._calculate_metrics → canary.CanaryRunner._load_samples → config.get_config → ...+2
- **Calls:** canary:CanaryRunner._calculate_metrics, canary:CanaryRunner._load_samples, config:get_config, divergence:DivergenceAnalyzer._calculate_metrics, divergence:DivergenceAnalyzer._load_samples

### `pattern_detection.detect_cost_spikes`
- **Layer:** L5
- **Decisions:** 6
- **Statements:** 8
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** pattern_detection.detect_cost_spikes → pattern_detection_driver.PatternDetectionDriver.fetch_completed_runs_with_costs
- **Calls:** pattern_detection_driver:PatternDetectionDriver.fetch_completed_runs_with_costs

### `prediction.predict_failure_likelihood`
- **Layer:** L5
- **Decisions:** 6
- **Statements:** 12
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** prediction.predict_failure_likelihood → pattern_detection_driver.PatternDetectionDriver.fetch_failed_runs → prediction_driver.PredictionDriver.fetch_failed_runs → prediction_driver.PredictionDriver.fetch_failure_patterns → ...+1
- **Calls:** pattern_detection_driver:PatternDetectionDriver.fetch_failed_runs, prediction_driver:PredictionDriver.fetch_failed_runs, prediction_driver:PredictionDriver.fetch_failure_patterns, prediction_driver:PredictionDriver.fetch_run_totals

### `provenance.ProvenanceLogger.query`
- **Layer:** L5
- **Decisions:** 8
- **Statements:** 3
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** provenance.ProvenanceLogger.query → provenance.ProvenanceLog.from_dict
- **Calls:** provenance:ProvenanceLog.from_dict

### `provenance_async.write_provenance_batch`
- **Layer:** L6
- **Decisions:** 4
- **Statements:** 4
- **Delegation depth:** 5
- **Persistence:** yes
- **Chain:** provenance_async.write_provenance_batch → ai_console_panel_engine.AIConsolePanelEngine.close → provenance.ProvenanceLogger.close
- **Calls:** ai_console_panel_engine:AIConsolePanelEngine.close, provenance:ProvenanceLogger.close

### `sandbox.CostSimSandbox.simulate`
- **Layer:** L5
- **Decisions:** 4
- **Statements:** 8
- **Delegation depth:** 3
- **Persistence:** no
- **Chain:** sandbox.CostSimSandbox.simulate → config.is_v2_sandbox_enabled → sandbox.CostSimSandbox._get_v2_adapter → sandbox.CostSimSandbox._log_comparison
- **Calls:** config:is_v2_sandbox_enabled, sandbox:CostSimSandbox._get_v2_adapter, sandbox:CostSimSandbox._log_comparison

## Supersets (orchestrating functions)

### `canary.CanaryRunner._approximate_kl_divergence`
- **Decisions:** 4, **Statements:** 21
- **Subsumes:** provenance:ProvenanceLogger.log

### `canary.CanaryRunner._load_samples`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** canary:CanaryRunner._generate_synthetic_samples, provenance:ProvenanceLog.get_decompressed_input, provenance:ProvenanceLogger.query, provenance:get_provenance_logger

### `canary.CanaryRunner._run_internal`
- **Decisions:** 9, **Statements:** 16
- **Subsumes:** canary:CanaryRunner._calculate_metrics, canary:CanaryRunner._compare_with_golden, canary:CanaryRunner._evaluate_results, canary:CanaryRunner._load_samples, canary:CanaryRunner._run_single, canary:CanaryRunner._save_artifacts, divergence:DivergenceAnalyzer._calculate_metrics, divergence:DivergenceAnalyzer._load_samples

### `coordinator.CoordinationManager._find_preemption_targets`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** envelope:has_higher_priority

### `coordinator.CoordinationManager._revert_envelope`
- **Decisions:** 3, **Statements:** 8
- **Subsumes:** coordinator:CoordinationManager._emit_audit_record, coordinator:CoordinationManager._get_parameter_key

### `coordinator.CoordinationManager.check_allowed`
- **Decisions:** 3, **Statements:** 7
- **Subsumes:** coordinator:CoordinationManager._emit_audit_record, coordinator:CoordinationManager._find_preemption_targets, coordinator:CoordinationManager._get_parameter_key

### `coordinator.CoordinationManager.expire_envelope`
- **Decisions:** 2, **Statements:** 10
- **Subsumes:** coordinator:CoordinationManager._get_parameter_key

### `cost_anomaly_detector.CostAnomalyDetector._derive_cause`
- **Decisions:** 9, **Statements:** 10
- **Subsumes:** cost_anomaly_driver:CostAnomalyDriver.fetch_feature_concentration, cost_anomaly_driver:CostAnomalyDriver.fetch_prompt_comparison, cost_anomaly_driver:CostAnomalyDriver.fetch_request_comparison, cost_anomaly_driver:CostAnomalyDriver.fetch_retry_comparison

### `cost_anomaly_detector.CostAnomalyDetector._detect_entity_spikes`
- **Decisions:** 3, **Statements:** 8
- **Subsumes:** cost_anomaly_detector:CostAnomalyDetector._derive_cause, cost_anomaly_detector:CostAnomalyDetector._format_spike_message, cost_anomaly_detector:CostAnomalyDetector._record_breach_and_get_consecutive_count, cost_anomaly_detector:CostAnomalyDetector._reset_breach_history, cost_anomaly_detector:classify_severity, cost_anomaly_driver:CostAnomalyDriver.fetch_entity_baseline, cost_anomaly_driver:CostAnomalyDriver.fetch_entity_today_spend

### `cost_anomaly_detector.CostAnomalyDetector._detect_tenant_spike`
- **Decisions:** 3, **Statements:** 11
- **Subsumes:** cost_anomaly_detector:CostAnomalyDetector._derive_cause, cost_anomaly_detector:CostAnomalyDetector._format_spike_message, cost_anomaly_detector:CostAnomalyDetector._record_breach_and_get_consecutive_count, cost_anomaly_detector:CostAnomalyDetector._reset_breach_history, cost_anomaly_detector:classify_severity, cost_anomaly_driver:CostAnomalyDriver.fetch_tenant_baseline, cost_anomaly_driver:CostAnomalyDriver.fetch_tenant_today_spend

### `cost_anomaly_detector.CostAnomalyDetector._update_drift_tracking`
- **Decisions:** 2, **Statements:** 2
- **Subsumes:** cost_anomaly_driver:CostAnomalyDriver.fetch_drift_tracking, cost_anomaly_driver:CostAnomalyDriver.insert_drift_tracking, cost_anomaly_driver:CostAnomalyDriver.update_drift_tracking

### `cost_anomaly_detector.CostAnomalyDetector.detect_budget_issues`
- **Decisions:** 4, **Statements:** 6
- **Subsumes:** cost_anomaly_detector:CostAnomalyDetector._check_budget_threshold, cost_anomaly_driver:CostAnomalyDriver.fetch_daily_spend, cost_anomaly_driver:CostAnomalyDriver.fetch_monthly_spend

### `cost_anomaly_detector.run_anomaly_detection_with_governance`
- **Decisions:** 2, **Statements:** 7
- **Subsumes:** cost_anomaly_detector:run_anomaly_detection_with_facts

### `cost_snapshots.SnapshotComputer._compute_snapshot`
- **Decisions:** 2, **Statements:** 6
- **Subsumes:** cost_snapshot_schemas:CostSnapshot.create, cost_snapshots:SnapshotComputer._aggregate_cost_records, cost_snapshots:SnapshotComputer._get_current_baseline, cost_snapshots:SnapshotComputer._insert_aggregate, cost_snapshots:SnapshotComputer._insert_snapshot, cost_snapshots:SnapshotComputer._update_snapshot

### `detection_facade.DetectionFacade._run_cost_detection`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** cost_anomaly_detector:run_anomaly_detection_with_governance

### `divergence.DivergenceAnalyzer._calculate_kl_divergence`
- **Decisions:** 4, **Statements:** 21
- **Subsumes:** provenance:ProvenanceLogger.log

### `pattern_detection.detect_failure_patterns`
- **Decisions:** 3, **Statements:** 9
- **Subsumes:** pattern_detection:compute_error_signature, pattern_detection_driver:PatternDetectionDriver.fetch_failed_runs, prediction_driver:PredictionDriver.fetch_failed_runs

### `prediction.predict_cost_overrun`
- **Decisions:** 5, **Statements:** 10
- **Subsumes:** prediction_driver:PredictionDriver.fetch_cost_runs

### `provenance.ProvenanceLogger._flush`
- **Decisions:** 3, **Statements:** 5
- **Subsumes:** provenance:ProvenanceLogger._write_to_db, provenance:ProvenanceLogger._write_to_file

### `provenance_async.query_provenance`
- **Decisions:** 7, **Statements:** 1
- **Subsumes:** cost_snapshot_schemas:CostSnapshot.to_dict, costsim_models:CanaryReport.to_dict, costsim_models:ComparisonResult.to_dict, costsim_models:DiffResult.to_dict, costsim_models:DivergenceReport.to_dict, costsim_models:V2SimulationResult.to_dict, costsim_models:ValidationResult.to_dict, datasets:ReferenceDataset.to_dict, detection_facade:AnomalyInfo.to_dict, detection_facade:DetectionResult.to_dict, detection_facade:DetectionStatusInfo.to_dict, provenance:ProvenanceLog.to_dict

### `provenance_async.write_provenance`
- **Decisions:** 3, **Statements:** 3
- **Subsumes:** ai_console_panel_engine:AIConsolePanelEngine.close, provenance:ProvenanceLogger.close

## Wrappers (thin delegation)

- `ai_console_panel_engine.AIConsolePanelEngine.close` → provenance:ProvenanceLogger.close
- `ai_console_panel_engine.AIConsolePanelEngine.get_panel_ids` → ?
- `ai_console_panel_engine.create_panel_engine` → ?
- `analytics_facade.AnalyticsFacade.__init__` → ?
- `analytics_read_driver.AnalyticsReadDriver.__init__` → ?
- `analytics_read_driver.get_analytics_read_driver` → ?
- `audit_persistence._now_utc` → ?
- `canary.CanaryRunner._compare_with_golden` → ?
- `config.is_v2_disabled_by_drift` → config:get_config
- `coordinator.CoordinationError.__init__` → ai_console_panel_engine:AIConsolePanelEngine.__init__
- `coordinator.CoordinationManager._get_parameter_key` → ?
- `coordinator.CoordinationManager.active_envelope_count` → ?
- `coordinator.CoordinationManager.get_active_envelopes` → ?
- `coordinator.CoordinationManager.get_audit_trail` → ?
- `coordinator.CoordinationManager.get_envelopes_by_class` → ?
- `coordinator.CoordinationManager.is_kill_switch_active` → ?
- `coordinator.CoordinationManager.reset_kill_switch` → ?
- `cost_anomaly_detector.CostAnomalyDetector._format_spike_message` → ?
- `cost_anomaly_detector.CostAnomalyDetector._reset_breach_history` → ?
- `cost_anomaly_detector.CostAnomalyDetector._reset_drift_tracking` → cost_anomaly_driver:CostAnomalyDriver.reset_drift_tracking
- `cost_anomaly_driver.CostAnomalyDriver.__init__` → ?
- `cost_anomaly_driver.CostAnomalyDriver.insert_breach_history` → ?
- `cost_anomaly_driver.CostAnomalyDriver.insert_drift_tracking` → ?
- `cost_anomaly_driver.CostAnomalyDriver.reset_drift_tracking` → ?
- `cost_anomaly_driver.CostAnomalyDriver.update_drift_tracking` → ?
- `cost_anomaly_driver.get_cost_anomaly_driver` → ?
- `cost_model_engine.get_skill_coefficients` → ?
- `cost_model_engine.is_significant_risk` → ?
- `cost_snapshots.BaselineComputer.__init__` → ?
- `cost_snapshots.SnapshotAnomalyDetector.__init__` → ?
- `cost_snapshots.SnapshotComputer.__init__` → ?
- `cost_write_driver.CostWriteDriver.__init__` → ?
- `cost_write_driver.CostWriteDriver.create_cost_record` → ?
- `cost_write_driver.get_cost_write_driver` → ?
- `cost_write_engine.CostWriteService.__init__` → cost_write_driver:get_cost_write_driver
- `cost_write_engine.CostWriteService.create_cost_record` → cost_write_driver:CostWriteDriver.create_cost_record
- `cost_write_engine.CostWriteService.create_feature_tag` → cost_write_driver:CostWriteDriver.create_feature_tag
- `cost_write_engine.CostWriteService.create_or_update_budget` → cost_write_driver:CostWriteDriver.create_or_update_budget
- `cost_write_engine.CostWriteService.update_feature_tag` → cost_write_driver:CostWriteDriver.update_feature_tag
- `costsim_models.CanaryReport.to_dict` → ?
- `costsim_models.ComparisonResult.to_dict` → ?
- `costsim_models.DiffResult.to_dict` → ?
- `costsim_models.DivergenceReport.to_dict` → ?
- `costsim_models.V2SimulationResult.to_dict` → ?
- `costsim_models.ValidationResult.to_dict` → ?
- `datasets.DatasetValidator.__init__` → datasets:DatasetValidator._build_datasets
- `datasets.DatasetValidator.get_dataset` → ?
- `datasets.DatasetValidator.list_datasets` → cost_snapshot_schemas:CostSnapshot.to_dict
- `datasets.ReferenceDataset.to_dict` → ?
- `datasets.validate_all_datasets` → datasets:DatasetValidator.validate_all
- `datasets.validate_dataset` → datasets:DatasetValidator.validate_dataset
- `detection_facade.AnomalyInfo.to_dict` → ?
- `detection_facade.DetectionFacade.__init__` → ?
- `detection_facade.DetectionFacade.cost_detector` → ?
- `detection_facade.DetectionFacade.get_detection_status` → ?
- `detection_facade.DetectionResult.to_dict` → ?
- `detection_facade.DetectionStatusInfo.to_dict` → ?
- `divergence.DivergenceAnalyzer.__init__` → ?
- `divergence.generate_divergence_report` → divergence:DivergenceAnalyzer.generate_report
- `envelope.EnvelopeValidationError.__init__` → ai_console_panel_engine:AIConsolePanelEngine.__init__
- `envelope.create_audit_record` → ?
- `envelope.get_envelope_priority` → ?
- `envelope.has_higher_priority` → envelope:get_envelope_priority
- `leader.LeaderContext.is_leader` → ?
- `leader.with_alert_worker_lock` → leader:with_leader_lock
- `leader.with_archiver_lock` → leader:with_leader_lock
- `leader.with_canary_lock` → leader:with_leader_lock
- `leader.with_leader_lock` → leader:leader_election
- `metrics.get_alert_rules` → ?
- `pattern_detection_driver.PatternDetectionDriver.__init__` → ?
- `pattern_detection_driver.get_pattern_detection_driver` → ?
- `prediction_driver.PredictionDriver.__init__` → ?
- `prediction_driver.get_prediction_driver` → ?
- `provenance.ProvenanceLog.to_dict` → ?
- `provenance.ProvenanceLogger._write_to_db` → ?
- `provenance.ProvenanceLogger.close` → provenance:ProvenanceLogger._flush
- `sandbox.SandboxResult.production_result` → ?
- `sandbox.simulate_with_sandbox` → sandbox:CostSimSandbox.simulate

## Full Call Graph

```
[LEAF] ai_console_panel_engine.AIConsolePanelEngine.__init__
[LEAF] ai_console_panel_engine.AIConsolePanelEngine._create_short_circuit_response
[LEAF] ai_console_panel_engine.AIConsolePanelEngine._evaluate_panel_slots
[WRAPPER] ai_console_panel_engine.AIConsolePanelEngine.close → provenance:ProvenanceLogger.close
[ENTRY] ai_console_panel_engine.AIConsolePanelEngine.evaluate_all_panels → ai_console_panel_engine:AIConsolePanelEngine.evaluate_panel
[CANONICAL] ai_console_panel_engine.AIConsolePanelEngine.evaluate_panel → ai_console_panel_engine:AIConsolePanelEngine._create_short_circuit_response, ai_console_panel_engine:AIConsolePanelEngine._evaluate_panel_slots
[WRAPPER] ai_console_panel_engine.AIConsolePanelEngine.get_panel_ids
[LEAF] ai_console_panel_engine.AIConsolePanelEngine.get_panel_spec
[WRAPPER] ai_console_panel_engine.create_panel_engine
[ENTRY] ai_console_panel_engine.get_panel_engine → ai_console_panel_engine:create_panel_engine
[WRAPPER] analytics_facade.AnalyticsFacade.__init__
[LEAF] analytics_facade.AnalyticsFacade._calculate_freshness
[LEAF] analytics_facade.AnalyticsFacade._calculate_freshness_from_cost
[ENTRY] analytics_facade.AnalyticsFacade.get_cost_statistics → analytics_facade:AnalyticsFacade._calculate_freshness_from_cost, analytics_facade:SignalAdapter.fetch_cost_by_feature, analytics_facade:SignalAdapter.fetch_cost_by_model, analytics_facade:SignalAdapter.fetch_cost_spend
[LEAF] analytics_facade.AnalyticsFacade.get_status
[CANONICAL] analytics_facade.AnalyticsFacade.get_usage_statistics → analytics_facade:AnalyticsFacade._calculate_freshness, analytics_facade:SignalAdapter.fetch_cost_metrics, analytics_facade:SignalAdapter.fetch_llm_usage, analytics_facade:SignalAdapter.fetch_worker_execution
[INTERNAL] analytics_facade.SignalAdapter.fetch_cost_by_feature → analytics_read_driver:AnalyticsReadDriver.fetch_cost_by_feature, analytics_read_driver:get_analytics_read_driver
[INTERNAL] analytics_facade.SignalAdapter.fetch_cost_by_model → analytics_read_driver:AnalyticsReadDriver.fetch_cost_by_model, analytics_read_driver:get_analytics_read_driver
[INTERNAL] analytics_facade.SignalAdapter.fetch_cost_metrics → analytics_read_driver:AnalyticsReadDriver.fetch_cost_metrics, analytics_read_driver:get_analytics_read_driver
[INTERNAL] analytics_facade.SignalAdapter.fetch_cost_spend → analytics_read_driver:AnalyticsReadDriver.fetch_cost_spend, analytics_read_driver:get_analytics_read_driver
[INTERNAL] analytics_facade.SignalAdapter.fetch_llm_usage → analytics_read_driver:AnalyticsReadDriver.fetch_llm_usage, analytics_read_driver:get_analytics_read_driver
[INTERNAL] analytics_facade.SignalAdapter.fetch_worker_execution → analytics_read_driver:AnalyticsReadDriver.fetch_worker_execution, analytics_read_driver:get_analytics_read_driver
[LEAF] analytics_facade.get_analytics_facade
[WRAPPER] analytics_read_driver.AnalyticsReadDriver.__init__
[LEAF] analytics_read_driver.AnalyticsReadDriver.fetch_cost_by_feature
[LEAF] analytics_read_driver.AnalyticsReadDriver.fetch_cost_by_model
[LEAF] analytics_read_driver.AnalyticsReadDriver.fetch_cost_metrics
[LEAF] analytics_read_driver.AnalyticsReadDriver.fetch_cost_spend
[LEAF] analytics_read_driver.AnalyticsReadDriver.fetch_llm_usage
[LEAF] analytics_read_driver.AnalyticsReadDriver.fetch_worker_execution
[WRAPPER] analytics_read_driver.get_analytics_read_driver
[WRAPPER] audit_persistence._now_utc
[LEAF] audit_persistence.persist_audit_record
[INTERNAL] canary.CanaryRunner.__init__ → config:get_config
[SUPERSET] canary.CanaryRunner._approximate_kl_divergence → provenance:ProvenanceLogger.log
[INTERNAL] canary.CanaryRunner._calculate_metrics → canary:CanaryRunner._approximate_kl_divergence
[WRAPPER] canary.CanaryRunner._compare_with_golden
[LEAF] canary.CanaryRunner._evaluate_results
[LEAF] canary.CanaryRunner._generate_synthetic_samples
[SUPERSET] canary.CanaryRunner._load_samples → canary:CanaryRunner._generate_synthetic_samples, provenance:ProvenanceLog.get_decompressed_input, provenance:ProvenanceLogger.query, provenance:get_provenance_logger
[SUPERSET] canary.CanaryRunner._run_internal → canary:CanaryRunner._calculate_metrics, canary:CanaryRunner._compare_with_golden, canary:CanaryRunner._evaluate_results, canary:CanaryRunner._load_samples, canary:CanaryRunner._run_single, ...+3
[INTERNAL] canary.CanaryRunner._run_single → costsim_models:V2SimulationResult.compute_output_hash
[INTERNAL] canary.CanaryRunner._save_artifacts → cost_snapshot_schemas:CostSnapshot.to_dict, costsim_models:CanaryReport.to_dict, costsim_models:ComparisonResult.to_dict, costsim_models:DiffResult.to_dict, costsim_models:DivergenceReport.to_dict, ...+7
[CANONICAL] canary.CanaryRunner.run → canary:CanaryRunner._run_internal, leader:leader_election
[ENTRY] canary.run_canary → canary:CanaryRunner.run
[LEAF] config.CostSimConfig.from_env
[INTERNAL] config.get_commit_sha → canary:CanaryRunner.run
[INTERNAL] config.get_config → config:CostSimConfig.from_env
[WRAPPER] config.is_v2_disabled_by_drift → config:get_config
[CANONICAL] config.is_v2_sandbox_enabled → config:get_config
[WRAPPER] coordinator.CoordinationError.__init__ → ai_console_panel_engine:AIConsolePanelEngine.__init__, analytics_facade:AnalyticsFacade.__init__, analytics_read_driver:AnalyticsReadDriver.__init__, canary:CanaryRunner.__init__, coordinator:CoordinationManager.__init__, ...+17
[LEAF] coordinator.CoordinationManager.__init__
[INTERNAL] coordinator.CoordinationManager._emit_audit_record → audit_persistence:persist_audit_record
[SUPERSET] coordinator.CoordinationManager._find_preemption_targets → envelope:has_higher_priority
[WRAPPER] coordinator.CoordinationManager._get_parameter_key
[SUPERSET] coordinator.CoordinationManager._revert_envelope → coordinator:CoordinationManager._emit_audit_record, coordinator:CoordinationManager._get_parameter_key
[WRAPPER] coordinator.CoordinationManager.active_envelope_count
[CANONICAL] coordinator.CoordinationManager.apply → coordinator:CoordinationManager._emit_audit_record, coordinator:CoordinationManager._find_preemption_targets, coordinator:CoordinationManager._get_parameter_key, coordinator:CoordinationManager._revert_envelope, coordinator:CoordinationManager.check_allowed
[SUPERSET] coordinator.CoordinationManager.check_allowed → coordinator:CoordinationManager._emit_audit_record, coordinator:CoordinationManager._find_preemption_targets, coordinator:CoordinationManager._get_parameter_key
[SUPERSET] coordinator.CoordinationManager.expire_envelope → coordinator:CoordinationManager._get_parameter_key
[WRAPPER] coordinator.CoordinationManager.get_active_envelopes
[WRAPPER] coordinator.CoordinationManager.get_audit_trail
[ENTRY] coordinator.CoordinationManager.get_coordination_stats → coordinator:CoordinationManager.get_envelopes_by_class
[LEAF] coordinator.CoordinationManager.get_envelope_for_parameter
[WRAPPER] coordinator.CoordinationManager.get_envelopes_by_class
[WRAPPER] coordinator.CoordinationManager.is_kill_switch_active
[ENTRY] coordinator.CoordinationManager.kill_switch → coordinator:CoordinationManager._revert_envelope
[WRAPPER] coordinator.CoordinationManager.reset_kill_switch
[ENTRY] coordinator.CoordinationManager.revert → coordinator:CoordinationManager._revert_envelope
[INTERNAL] cost_anomaly_detector.CostAnomalyDetector.__init__ → cost_anomaly_driver:get_cost_anomaly_driver
[LEAF] cost_anomaly_detector.CostAnomalyDetector._check_budget_threshold
[SUPERSET] cost_anomaly_detector.CostAnomalyDetector._derive_cause → cost_anomaly_driver:CostAnomalyDriver.fetch_feature_concentration, cost_anomaly_driver:CostAnomalyDriver.fetch_prompt_comparison, cost_anomaly_driver:CostAnomalyDriver.fetch_request_comparison, cost_anomaly_driver:CostAnomalyDriver.fetch_retry_comparison
[SUPERSET] cost_anomaly_detector.CostAnomalyDetector._detect_entity_spikes → cost_anomaly_detector:CostAnomalyDetector._derive_cause, cost_anomaly_detector:CostAnomalyDetector._format_spike_message, cost_anomaly_detector:CostAnomalyDetector._record_breach_and_get_consecutive_count, cost_anomaly_detector:CostAnomalyDetector._reset_breach_history, cost_anomaly_detector:classify_severity, ...+2
[SUPERSET] cost_anomaly_detector.CostAnomalyDetector._detect_tenant_spike → cost_anomaly_detector:CostAnomalyDetector._derive_cause, cost_anomaly_detector:CostAnomalyDetector._format_spike_message, cost_anomaly_detector:CostAnomalyDetector._record_breach_and_get_consecutive_count, cost_anomaly_detector:CostAnomalyDetector._reset_breach_history, cost_anomaly_detector:classify_severity, ...+2
[WRAPPER] cost_anomaly_detector.CostAnomalyDetector._format_spike_message
[INTERNAL] cost_anomaly_detector.CostAnomalyDetector._record_breach_and_get_consecutive_count → cost_anomaly_driver:CostAnomalyDriver.fetch_breach_exists_today, cost_anomaly_driver:CostAnomalyDriver.fetch_consecutive_breaches, cost_anomaly_driver:CostAnomalyDriver.insert_breach_history
[WRAPPER] cost_anomaly_detector.CostAnomalyDetector._reset_breach_history
[WRAPPER] cost_anomaly_detector.CostAnomalyDetector._reset_drift_tracking → cost_anomaly_driver:CostAnomalyDriver.reset_drift_tracking
[SUPERSET] cost_anomaly_detector.CostAnomalyDetector._update_drift_tracking → cost_anomaly_driver:CostAnomalyDriver.fetch_drift_tracking, cost_anomaly_driver:CostAnomalyDriver.insert_drift_tracking, cost_anomaly_driver:CostAnomalyDriver.update_drift_tracking
[INTERNAL] cost_anomaly_detector.CostAnomalyDetector.detect_absolute_spikes → cost_anomaly_detector:CostAnomalyDetector._detect_entity_spikes, cost_anomaly_detector:CostAnomalyDetector._detect_tenant_spike
[INTERNAL] cost_anomaly_detector.CostAnomalyDetector.detect_all → cost_anomaly_detector:CostAnomalyDetector.detect_absolute_spikes, cost_anomaly_detector:CostAnomalyDetector.detect_budget_issues, cost_anomaly_detector:CostAnomalyDetector.detect_sustained_drift
[SUPERSET] cost_anomaly_detector.CostAnomalyDetector.detect_budget_issues → cost_anomaly_detector:CostAnomalyDetector._check_budget_threshold, cost_anomaly_driver:CostAnomalyDriver.fetch_daily_spend, cost_anomaly_driver:CostAnomalyDriver.fetch_monthly_spend
[CANONICAL] cost_anomaly_detector.CostAnomalyDetector.detect_sustained_drift → cost_anomaly_detector:CostAnomalyDetector._derive_cause, cost_anomaly_detector:CostAnomalyDetector._reset_drift_tracking, cost_anomaly_detector:CostAnomalyDetector._update_drift_tracking, cost_anomaly_detector:classify_severity, cost_anomaly_driver:CostAnomalyDriver.fetch_baseline_avg, ...+1
[LEAF] cost_anomaly_detector.CostAnomalyDetector.persist_anomalies
[LEAF] cost_anomaly_detector.classify_severity
[INTERNAL] cost_anomaly_detector.run_anomaly_detection → cost_anomaly_detector:CostAnomalyDetector.detect_all, cost_anomaly_detector:CostAnomalyDetector.persist_anomalies
[INTERNAL] cost_anomaly_detector.run_anomaly_detection_with_facts → cost_anomaly_detector:run_anomaly_detection
[SUPERSET] cost_anomaly_detector.run_anomaly_detection_with_governance → cost_anomaly_detector:run_anomaly_detection_with_facts
[WRAPPER] cost_anomaly_driver.CostAnomalyDriver.__init__
[LEAF] cost_anomaly_driver.CostAnomalyDriver.fetch_baseline_avg
[LEAF] cost_anomaly_driver.CostAnomalyDriver.fetch_breach_exists_today
[LEAF] cost_anomaly_driver.CostAnomalyDriver.fetch_consecutive_breaches
[LEAF] cost_anomaly_driver.CostAnomalyDriver.fetch_daily_spend
[LEAF] cost_anomaly_driver.CostAnomalyDriver.fetch_drift_tracking
[LEAF] cost_anomaly_driver.CostAnomalyDriver.fetch_entity_baseline
[LEAF] cost_anomaly_driver.CostAnomalyDriver.fetch_entity_today_spend
[LEAF] cost_anomaly_driver.CostAnomalyDriver.fetch_feature_concentration
[LEAF] cost_anomaly_driver.CostAnomalyDriver.fetch_monthly_spend
[LEAF] cost_anomaly_driver.CostAnomalyDriver.fetch_prompt_comparison
[LEAF] cost_anomaly_driver.CostAnomalyDriver.fetch_request_comparison
[LEAF] cost_anomaly_driver.CostAnomalyDriver.fetch_retry_comparison
[LEAF] cost_anomaly_driver.CostAnomalyDriver.fetch_rolling_avg
[LEAF] cost_anomaly_driver.CostAnomalyDriver.fetch_tenant_baseline
[LEAF] cost_anomaly_driver.CostAnomalyDriver.fetch_tenant_today_spend
[WRAPPER] cost_anomaly_driver.CostAnomalyDriver.insert_breach_history
[WRAPPER] cost_anomaly_driver.CostAnomalyDriver.insert_drift_tracking
[WRAPPER] cost_anomaly_driver.CostAnomalyDriver.reset_drift_tracking
[WRAPPER] cost_anomaly_driver.CostAnomalyDriver.update_drift_tracking
[WRAPPER] cost_anomaly_driver.get_cost_anomaly_driver
[LEAF] cost_model_engine.calculate_cumulative_risk
[LEAF] cost_model_engine.check_feasibility
[LEAF] cost_model_engine.classify_drift
[CANONICAL] cost_model_engine.estimate_step_cost → cost_model_engine:get_skill_coefficients
[WRAPPER] cost_model_engine.get_skill_coefficients
[WRAPPER] cost_model_engine.is_significant_risk
[LEAF] cost_snapshot_schemas.CostSnapshot.create
[LEAF] cost_snapshot_schemas.CostSnapshot.to_dict
[LEAF] cost_snapshot_schemas.SnapshotAggregate.create
[LEAF] cost_snapshot_schemas.SnapshotBaseline.create
[WRAPPER] cost_snapshots.BaselineComputer.__init__
[LEAF] cost_snapshots.BaselineComputer._insert_baseline
[INTERNAL] cost_snapshots.BaselineComputer.compute_baselines → cost_snapshot_schemas:SnapshotBaseline.create, cost_snapshots:BaselineComputer._insert_baseline
[WRAPPER] cost_snapshots.SnapshotAnomalyDetector.__init__
[LEAF] cost_snapshots.SnapshotAnomalyDetector._create_anomaly_from_evaluation
[LEAF] cost_snapshots.SnapshotAnomalyDetector._get_snapshot
[LEAF] cost_snapshots.SnapshotAnomalyDetector._insert_evaluation
[CANONICAL] cost_snapshots.SnapshotAnomalyDetector.evaluate_snapshot → cost_snapshots:SnapshotAnomalyDetector._create_anomaly_from_evaluation, cost_snapshots:SnapshotAnomalyDetector._get_snapshot, cost_snapshots:SnapshotAnomalyDetector._insert_evaluation
[WRAPPER] cost_snapshots.SnapshotComputer.__init__
[INTERNAL] cost_snapshots.SnapshotComputer._aggregate_cost_records → cost_snapshot_schemas:SnapshotAggregate.create
[SUPERSET] cost_snapshots.SnapshotComputer._compute_snapshot → cost_snapshot_schemas:CostSnapshot.create, cost_snapshots:SnapshotComputer._aggregate_cost_records, cost_snapshots:SnapshotComputer._get_current_baseline, cost_snapshots:SnapshotComputer._insert_aggregate, cost_snapshots:SnapshotComputer._insert_snapshot, ...+1
[LEAF] cost_snapshots.SnapshotComputer._get_current_baseline
[LEAF] cost_snapshots.SnapshotComputer._insert_aggregate
[LEAF] cost_snapshots.SnapshotComputer._insert_snapshot
[LEAF] cost_snapshots.SnapshotComputer._update_snapshot
[INTERNAL] cost_snapshots.SnapshotComputer.compute_daily_snapshot → cost_snapshots:SnapshotComputer._compute_snapshot
[INTERNAL] cost_snapshots.SnapshotComputer.compute_hourly_snapshot → cost_snapshots:SnapshotComputer._compute_snapshot
[ENTRY] cost_snapshots.run_daily_snapshot_and_baseline_job → cost_snapshots:BaselineComputer.compute_baselines, cost_snapshots:SnapshotAnomalyDetector.evaluate_snapshot, cost_snapshots:SnapshotComputer.compute_daily_snapshot
[ENTRY] cost_snapshots.run_hourly_snapshot_job → cost_snapshots:SnapshotComputer.compute_hourly_snapshot
[WRAPPER] cost_write_driver.CostWriteDriver.__init__
[WRAPPER] cost_write_driver.CostWriteDriver.create_cost_record
[LEAF] cost_write_driver.CostWriteDriver.create_feature_tag
[LEAF] cost_write_driver.CostWriteDriver.create_or_update_budget
[LEAF] cost_write_driver.CostWriteDriver.update_feature_tag
[WRAPPER] cost_write_driver.get_cost_write_driver
[WRAPPER] cost_write_engine.CostWriteService.__init__ → cost_write_driver:get_cost_write_driver
[WRAPPER] cost_write_engine.CostWriteService.create_cost_record → cost_write_driver:CostWriteDriver.create_cost_record
[WRAPPER] cost_write_engine.CostWriteService.create_feature_tag → cost_write_driver:CostWriteDriver.create_feature_tag
[WRAPPER] cost_write_engine.CostWriteService.create_or_update_budget → cost_write_driver:CostWriteDriver.create_or_update_budget
[WRAPPER] cost_write_engine.CostWriteService.update_feature_tag → cost_write_driver:CostWriteDriver.update_feature_tag
[WRAPPER] costsim_models.CanaryReport.to_dict
[WRAPPER] costsim_models.ComparisonResult.to_dict
[WRAPPER] costsim_models.DiffResult.to_dict
[WRAPPER] costsim_models.DivergenceReport.to_dict
[LEAF] costsim_models.V2SimulationResult.compute_output_hash
[WRAPPER] costsim_models.V2SimulationResult.to_dict
[WRAPPER] costsim_models.ValidationResult.to_dict
[WRAPPER] datasets.DatasetValidator.__init__ → datasets:DatasetValidator._build_datasets
[INTERNAL] datasets.DatasetValidator._build_datasets → datasets:DatasetValidator._build_high_variance_dataset, datasets:DatasetValidator._build_historical_dataset, datasets:DatasetValidator._build_low_variance_dataset, datasets:DatasetValidator._build_mixed_city_dataset, datasets:DatasetValidator._build_noise_injected_dataset
[LEAF] datasets.DatasetValidator._build_high_variance_dataset
[LEAF] datasets.DatasetValidator._build_historical_dataset
[LEAF] datasets.DatasetValidator._build_low_variance_dataset
[LEAF] datasets.DatasetValidator._build_mixed_city_dataset
[LEAF] datasets.DatasetValidator._build_noise_injected_dataset
[LEAF] datasets.DatasetValidator._calculate_drift_score
[WRAPPER] datasets.DatasetValidator.get_dataset
[WRAPPER] datasets.DatasetValidator.list_datasets → cost_snapshot_schemas:CostSnapshot.to_dict, costsim_models:CanaryReport.to_dict, costsim_models:ComparisonResult.to_dict, costsim_models:DiffResult.to_dict, costsim_models:DivergenceReport.to_dict, ...+7
[INTERNAL] datasets.DatasetValidator.validate_all → datasets:DatasetValidator.validate_dataset, datasets:validate_dataset
[CANONICAL] datasets.DatasetValidator.validate_dataset → datasets:DatasetValidator._calculate_drift_score, sandbox:CostSimSandbox.simulate
[WRAPPER] datasets.ReferenceDataset.to_dict
[LEAF] datasets.get_dataset_validator
[WRAPPER] datasets.validate_all_datasets → datasets:DatasetValidator.validate_all, datasets:get_dataset_validator
[WRAPPER] datasets.validate_dataset → datasets:DatasetValidator.validate_dataset, datasets:get_dataset_validator
[WRAPPER] detection_facade.AnomalyInfo.to_dict
[WRAPPER] detection_facade.DetectionFacade.__init__
[SUPERSET] detection_facade.DetectionFacade._run_cost_detection → cost_anomaly_detector:run_anomaly_detection_with_governance
[LEAF] detection_facade.DetectionFacade.acknowledge_anomaly
[WRAPPER] detection_facade.DetectionFacade.cost_detector
[LEAF] detection_facade.DetectionFacade.get_anomaly
[WRAPPER] detection_facade.DetectionFacade.get_detection_status
[LEAF] detection_facade.DetectionFacade.list_anomalies
[LEAF] detection_facade.DetectionFacade.resolve_anomaly
[ENTRY] detection_facade.DetectionFacade.run_detection → detection_facade:DetectionFacade._run_cost_detection
[WRAPPER] detection_facade.DetectionResult.to_dict
[WRAPPER] detection_facade.DetectionStatusInfo.to_dict
[LEAF] detection_facade.get_detection_facade
[WRAPPER] divergence.DivergenceAnalyzer.__init__
[SUPERSET] divergence.DivergenceAnalyzer._calculate_kl_divergence → provenance:ProvenanceLogger.log
[INTERNAL] divergence.DivergenceAnalyzer._calculate_metrics → divergence:DivergenceAnalyzer._calculate_kl_divergence
[INTERNAL] divergence.DivergenceAnalyzer._load_samples → divergence:DivergenceAnalyzer._parse_provenance_log, provenance:ProvenanceLogger.query, provenance:get_provenance_logger
[INTERNAL] divergence.DivergenceAnalyzer._parse_provenance_log → provenance:ProvenanceLog.get_decompressed_output
[CANONICAL] divergence.DivergenceAnalyzer.generate_report → canary:CanaryRunner._calculate_metrics, canary:CanaryRunner._load_samples, config:get_config, divergence:DivergenceAnalyzer._calculate_metrics, divergence:DivergenceAnalyzer._load_samples
[WRAPPER] divergence.generate_divergence_report → divergence:DivergenceAnalyzer.generate_report
[WRAPPER] envelope.EnvelopeValidationError.__init__ → ai_console_panel_engine:AIConsolePanelEngine.__init__, analytics_facade:AnalyticsFacade.__init__, analytics_read_driver:AnalyticsReadDriver.__init__, canary:CanaryRunner.__init__, coordinator:CoordinationError.__init__, ...+17
[LEAF] envelope.calculate_bounded_value
[WRAPPER] envelope.create_audit_record
[WRAPPER] envelope.get_envelope_priority
[WRAPPER] envelope.has_higher_priority → envelope:get_envelope_priority
[LEAF] envelope.validate_envelope
[ENTRY] leader.LeaderContext.__aenter__ → leader:try_acquire_leader_lock
[ENTRY] leader.LeaderContext.__aexit__ → ai_console_panel_engine:AIConsolePanelEngine.close, provenance:ProvenanceLogger.close
[LEAF] leader.LeaderContext.__init__
[WRAPPER] leader.LeaderContext.is_leader
[LEAF] leader.is_lock_held
[INTERNAL] leader.leader_election → ai_console_panel_engine:AIConsolePanelEngine.close, leader:try_acquire_leader_lock, provenance:ProvenanceLogger.close
[LEAF] leader.release_leader_lock
[LEAF] leader.try_acquire_leader_lock
[WRAPPER] leader.with_alert_worker_lock → leader:with_leader_lock
[WRAPPER] leader.with_archiver_lock → leader:with_leader_lock
[WRAPPER] leader.with_canary_lock → leader:with_leader_lock
[WRAPPER] leader.with_leader_lock → leader:leader_election
[INTERNAL] metrics.CostSimMetrics.__init__ → metrics:CostSimMetrics._init_metrics
[INTERNAL] metrics.CostSimMetrics._init_metrics → config:get_config
[LEAF] metrics.CostSimMetrics.record_alert_send_failure
[LEAF] metrics.CostSimMetrics.record_auto_recovery
[LEAF] metrics.CostSimMetrics.record_canary_run
[LEAF] metrics.CostSimMetrics.record_cb_disabled
[LEAF] metrics.CostSimMetrics.record_cb_enabled
[LEAF] metrics.CostSimMetrics.record_cb_incident
[LEAF] metrics.CostSimMetrics.record_cost_delta
[LEAF] metrics.CostSimMetrics.record_drift
[LEAF] metrics.CostSimMetrics.record_provenance_log
[LEAF] metrics.CostSimMetrics.record_schema_error
[LEAF] metrics.CostSimMetrics.record_simulation
[LEAF] metrics.CostSimMetrics.record_simulation_duration
[LEAF] metrics.CostSimMetrics.set_alert_queue_depth
[LEAF] metrics.CostSimMetrics.set_circuit_breaker_state
[LEAF] metrics.CostSimMetrics.set_consecutive_failures
[LEAF] metrics.CostSimMetrics.set_kl_divergence
[WRAPPER] metrics.get_alert_rules
[LEAF] metrics.get_metrics
[LEAF] pattern_detection.compute_error_signature
[CANONICAL] pattern_detection.detect_cost_spikes → pattern_detection_driver:PatternDetectionDriver.fetch_completed_runs_with_costs
[SUPERSET] pattern_detection.detect_failure_patterns → pattern_detection:compute_error_signature, pattern_detection_driver:PatternDetectionDriver.fetch_failed_runs, prediction_driver:PredictionDriver.fetch_failed_runs
[INTERNAL] pattern_detection.emit_feedback → pattern_detection_driver:PatternDetectionDriver.insert_feedback
[ENTRY] pattern_detection.get_feedback_summary → pattern_detection_driver:PatternDetectionDriver.fetch_feedback_records, pattern_detection_driver:get_pattern_detection_driver
[ENTRY] pattern_detection.run_pattern_detection → pattern_detection:detect_cost_spikes, pattern_detection:detect_failure_patterns, pattern_detection:emit_feedback, pattern_detection_driver:get_pattern_detection_driver
[WRAPPER] pattern_detection_driver.PatternDetectionDriver.__init__
[LEAF] pattern_detection_driver.PatternDetectionDriver.fetch_completed_runs_with_costs
[LEAF] pattern_detection_driver.PatternDetectionDriver.fetch_failed_runs
[LEAF] pattern_detection_driver.PatternDetectionDriver.fetch_feedback_records
[LEAF] pattern_detection_driver.PatternDetectionDriver.insert_feedback
[WRAPPER] pattern_detection_driver.get_pattern_detection_driver
[INTERNAL] prediction.emit_prediction → prediction_driver:PredictionDriver.insert_prediction
[ENTRY] prediction.get_prediction_summary → prediction_driver:PredictionDriver.fetch_predictions, prediction_driver:get_prediction_driver
[SUPERSET] prediction.predict_cost_overrun → prediction_driver:PredictionDriver.fetch_cost_runs
[CANONICAL] prediction.predict_failure_likelihood → pattern_detection_driver:PatternDetectionDriver.fetch_failed_runs, prediction_driver:PredictionDriver.fetch_failed_runs, prediction_driver:PredictionDriver.fetch_failure_patterns, prediction_driver:PredictionDriver.fetch_run_totals
[ENTRY] prediction.run_prediction_cycle → prediction:emit_prediction, prediction:predict_cost_overrun, prediction:predict_failure_likelihood, prediction_driver:get_prediction_driver
[WRAPPER] prediction_driver.PredictionDriver.__init__
[LEAF] prediction_driver.PredictionDriver.fetch_cost_runs
[LEAF] prediction_driver.PredictionDriver.fetch_failed_runs
[LEAF] prediction_driver.PredictionDriver.fetch_failure_patterns
[LEAF] prediction_driver.PredictionDriver.fetch_predictions
[LEAF] prediction_driver.PredictionDriver.fetch_run_totals
[LEAF] prediction_driver.PredictionDriver.insert_prediction
[WRAPPER] prediction_driver.get_prediction_driver
[LEAF] provenance.ProvenanceLog.from_dict
[LEAF] provenance.ProvenanceLog.get_decompressed_input
[LEAF] provenance.ProvenanceLog.get_decompressed_output
[WRAPPER] provenance.ProvenanceLog.to_dict
[INTERNAL] provenance.ProvenanceLogger.__init__ → config:get_config
[SUPERSET] provenance.ProvenanceLogger._flush → provenance:ProvenanceLogger._write_to_db, provenance:ProvenanceLogger._write_to_file
[INTERNAL] provenance.ProvenanceLogger._store → provenance:ProvenanceLogger._flush
[WRAPPER] provenance.ProvenanceLogger._write_to_db
[INTERNAL] provenance.ProvenanceLogger._write_to_file → cost_snapshot_schemas:CostSnapshot.to_dict, costsim_models:CanaryReport.to_dict, costsim_models:ComparisonResult.to_dict, costsim_models:DiffResult.to_dict, costsim_models:DivergenceReport.to_dict, ...+7
[WRAPPER] provenance.ProvenanceLogger.close → provenance:ProvenanceLogger._flush
[INTERNAL] provenance.ProvenanceLogger.log → config:get_commit_sha, config:get_config, provenance:ProvenanceLogger._store, provenance:compress_json, provenance:compute_hash
[CANONICAL] provenance.ProvenanceLogger.query → provenance:ProvenanceLog.from_dict
[LEAF] provenance.compress_json
[LEAF] provenance.compute_hash
[LEAF] provenance.get_provenance_logger
[ENTRY] provenance_async.backfill_v1_baseline → provenance_async:check_duplicate, provenance_async:write_provenance
[LEAF] provenance_async.check_duplicate
[LEAF] provenance_async.compute_input_hash
[LEAF] provenance_async.count_provenance
[LEAF] provenance_async.get_drift_stats
[SUPERSET] provenance_async.query_provenance → cost_snapshot_schemas:CostSnapshot.to_dict, costsim_models:CanaryReport.to_dict, costsim_models:ComparisonResult.to_dict, costsim_models:DiffResult.to_dict, costsim_models:DivergenceReport.to_dict, ...+7
[SUPERSET] provenance_async.write_provenance → ai_console_panel_engine:AIConsolePanelEngine.close, provenance:ProvenanceLogger.close
[CANONICAL] provenance_async.write_provenance_batch → ai_console_panel_engine:AIConsolePanelEngine.close, provenance:ProvenanceLogger.close
[LEAF] s1_retry_backoff.create_s1_envelope
[LEAF] sandbox.CostSimSandbox.__init__
[LEAF] sandbox.CostSimSandbox._get_v2_adapter
[LEAF] sandbox.CostSimSandbox._log_comparison
[CANONICAL] sandbox.CostSimSandbox.simulate → config:is_v2_sandbox_enabled, sandbox:CostSimSandbox._get_v2_adapter, sandbox:CostSimSandbox._log_comparison
[WRAPPER] sandbox.SandboxResult.production_result
[LEAF] sandbox.get_sandbox
[WRAPPER] sandbox.simulate_with_sandbox → sandbox:CostSimSandbox.simulate
```
