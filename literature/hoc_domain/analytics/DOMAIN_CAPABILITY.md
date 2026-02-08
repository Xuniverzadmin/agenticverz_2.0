# Analytics — Domain Capability

**Domain:** analytics  
**Total functions:** 286  
**Generator:** `scripts/ops/hoc_capability_doc_generator.py`

---

## Reality Delta (2026-02-07)

- L2 purity preserved: analytics L2 routes dispatch via L4 `OperationRegistry` (0 direct L2→L5).
- L5/L6 purity: `PYTHONPATH=. python3 backend/scripts/ops/hoc_l5_l6_purity_audit.py --domain analytics --json --advisory` reports 0 blocking, 0 advisory.
- Remaining coherence debt (execution boundary): `python3 scripts/ops/l5_spine_pairing_gap_detector.py --domain analytics --json` reports 9 orphaned L5 entry modules.
- Plan: `docs/architecture/hoc/DOMAIN_EXECUTION_BOUNDARY_REMEDIATION_PLAN.md`.

## 1. Domain Purpose

Aggregates operational metrics, trends, and insights across all customer domains. Powers dashboards, reports, and data exports.

## 2. Customer-Facing Operations

| Function | File | L4 Wired | Entry Point | Side Effects |
|----------|------|----------|-------------|--------------|
| `AnalyticsFacade.get_cost_statistics` | analytics_facade | Yes | L2:analytics | pure |
| `AnalyticsFacade.get_status` | analytics_facade | Yes | L2:analytics | pure |
| `AnalyticsFacade.get_usage_statistics` | analytics_facade | Yes | L2:analytics | pure |
| `AnomalyInfo.to_dict` | detection_facade | Yes | L4:analytics_handler | pure |
| `CostAnomalyDetector.detect_absolute_spikes` | cost_anomaly_detector | No (gap) | L2:cost_intelligence | pure |
| `CostAnomalyDetector.detect_all` | cost_anomaly_detector | No (gap) | L2:cost_intelligence | pure |
| `CostAnomalyDetector.detect_budget_issues` | cost_anomaly_detector | No (gap) | L2:cost_intelligence | pure |
| `CostAnomalyDetector.detect_sustained_drift` | cost_anomaly_detector | No (gap) | L2:cost_intelligence | pure |
| `CostAnomalyDetector.persist_anomalies` | cost_anomaly_detector | No (gap) | L2:cost_intelligence | db_write |
| `DatasetValidator.get_dataset` | datasets | No (gap) | L2:costsim | pure |
| `DatasetValidator.list_datasets` | datasets | No (gap) | L2:costsim | pure |
| `DatasetValidator.validate_all` | datasets | No (gap) | L2:costsim | pure |
| `DatasetValidator.validate_dataset` | datasets | No (gap) | L2:costsim | pure |
| `DetectionFacade.acknowledge_anomaly` | detection_facade | Yes | L4:analytics_handler | pure |
| `DetectionFacade.cost_detector` | detection_facade | Yes | L4:analytics_handler | pure |
| `DetectionFacade.get_anomaly` | detection_facade | Yes | L4:analytics_handler | pure |
| `DetectionFacade.get_detection_status` | detection_facade | Yes | L4:analytics_handler | pure |
| `DetectionFacade.list_anomalies` | detection_facade | Yes | L4:analytics_handler | pure |
| `DetectionFacade.resolve_anomaly` | detection_facade | Yes | L4:analytics_handler | pure |
| `DetectionFacade.run_detection` | detection_facade | Yes | L4:analytics_handler | pure |
| `DetectionResult.to_dict` | detection_facade | Yes | L4:analytics_handler | pure |
| `DetectionStatusInfo.to_dict` | detection_facade | Yes | L4:analytics_handler | pure |
| `DivergenceAnalyzer.generate_report` | divergence | No (gap) | L2:costsim | pure |
| `ReferenceDataset.to_dict` | datasets | No (gap) | L2:costsim | pure |
| `SignalAdapter.fetch_cost_by_feature` | analytics_facade | Yes | L2:analytics | pure |
| `SignalAdapter.fetch_cost_by_model` | analytics_facade | Yes | L2:analytics | pure |
| `SignalAdapter.fetch_cost_metrics` | analytics_facade | Yes | L2:analytics | pure |
| `SignalAdapter.fetch_cost_spend` | analytics_facade | Yes | L2:analytics | pure |
| `SignalAdapter.fetch_llm_usage` | analytics_facade | Yes | L2:analytics | pure |
| `SignalAdapter.fetch_worker_execution` | analytics_facade | Yes | L2:analytics | pure |
| `classify_severity` | cost_anomaly_detector | No (gap) | L2:cost_intelligence | pure |
| `emit_prediction` | prediction | No (gap) | L2:predictions | pure |
| `generate_divergence_report` | divergence | No (gap) | L2:costsim | pure |
| `get_analytics_facade` | analytics_facade | Yes | L2:analytics | pure |
| `get_dataset_validator` | datasets | No (gap) | L2:costsim | pure |
| `get_detection_facade` | detection_facade | Yes | L4:analytics_handler | pure |
| `get_prediction_summary` | prediction | No (gap) | L2:predictions | pure |
| `predict_cost_overrun` | prediction | No (gap) | L2:predictions | pure |
| `predict_failure_likelihood` | prediction | No (gap) | L2:predictions | pure |
| `run_anomaly_detection` | cost_anomaly_detector | No (gap) | L2:cost_intelligence | pure |
| `run_anomaly_detection_with_facts` | cost_anomaly_detector | No (gap) | L2:cost_intelligence | pure |
| `run_anomaly_detection_with_governance` | cost_anomaly_detector | No (gap) | L2:cost_intelligence | pure |
| `run_prediction_cycle` | prediction | No (gap) | L2:predictions | pure |
| `validate_all_datasets` | datasets | No (gap) | L2:costsim | pure |
| `validate_dataset` | datasets | No (gap) | L2:costsim | pure |

## 3. Internal Functions

### Decisions

| Function | File | Confidence |
|----------|------|------------|
| `AIConsolePanelEngine.evaluate_all_panels` | ai_console_panel_engine | medium |
| `AIConsolePanelEngine.evaluate_panel` | ai_console_panel_engine | medium |
| `CoordinationManager.check_allowed` | coordinator | medium |
| `SnapshotAnomalyDetector.evaluate_snapshot` | cost_snapshots | medium |
| `check_feasibility` | cost_model_engine | medium |
| `validate_envelope` | envelope | medium |

### Helpers

_107 internal helper functions._

- **ai_console_panel_engine:** `AIConsolePanelEngine.__init__`, `AIConsolePanelEngine._create_short_circuit_response`, `AIConsolePanelEngine._evaluate_panel_slots`
- **analytics_facade:** `AnalyticsFacade.__init__`, `AnalyticsFacade._calculate_freshness`, `AnalyticsFacade._calculate_freshness_from_cost`
- **analytics_read_driver:** `AnalyticsReadDriver.__init__`
- **audit_persistence:** `_now_utc`
- **canary:** `CanaryRunner.__init__`, `CanaryRunner._approximate_kl_divergence`, `CanaryRunner._calculate_metrics`, `CanaryRunner._compare_with_golden`, `CanaryRunner._evaluate_results`, `CanaryRunner._generate_synthetic_samples`, `CanaryRunner._load_samples`, `CanaryRunner._run_internal`, `CanaryRunner._run_single`, `CanaryRunner._save_artifacts`
- **config:** `CostSimConfig.from_env`
- **coordinator:** `CoordinationError.__init__`, `CoordinationManager.__init__`, `CoordinationManager._emit_audit_record`, `CoordinationManager._find_preemption_targets`, `CoordinationManager._get_parameter_key`, `CoordinationManager._revert_envelope`
- **cost_anomaly_detector:** `CostAnomalyDetector.__init__`, `CostAnomalyDetector._check_budget_threshold`, `CostAnomalyDetector._derive_cause`, `CostAnomalyDetector._detect_entity_spikes`, `CostAnomalyDetector._detect_tenant_spike`, `CostAnomalyDetector._format_spike_message`, `CostAnomalyDetector._record_breach_and_get_consecutive_count`, `CostAnomalyDetector._reset_breach_history`, `CostAnomalyDetector._reset_drift_tracking`, `CostAnomalyDetector._update_drift_tracking`
- **cost_anomaly_driver:** `CostAnomalyDriver.__init__`
- **cost_snapshot_schemas:** `CostSnapshot.to_dict`
- **cost_snapshots:** `BaselineComputer.__init__`, `BaselineComputer._insert_baseline`, `SnapshotAnomalyDetector.__init__`, `SnapshotAnomalyDetector._create_anomaly_from_evaluation`, `SnapshotAnomalyDetector._get_snapshot`, `SnapshotAnomalyDetector._insert_evaluation`, `SnapshotComputer.__init__`, `SnapshotComputer._aggregate_cost_records`, `SnapshotComputer._compute_snapshot`, `SnapshotComputer._get_current_baseline`
  _...and 7 more_
- **cost_write_driver:** `CostWriteDriver.__init__`
- **cost_write_engine:** `CostWriteService.__init__`, `CostWriteService.create_cost_record`, `CostWriteService.create_feature_tag`, `CostWriteService.create_or_update_budget`, `CostWriteService.update_feature_tag`
- **costsim_models:** `CanaryReport.to_dict`, `ComparisonResult.to_dict`, `DiffResult.to_dict`, `DivergenceReport.to_dict`, `V2SimulationResult.compute_output_hash`, `V2SimulationResult.to_dict`, `ValidationResult.to_dict`
- **datasets:** `DatasetValidator.__init__`, `DatasetValidator._build_datasets`, `DatasetValidator._build_high_variance_dataset`, `DatasetValidator._build_historical_dataset`, `DatasetValidator._build_low_variance_dataset`, `DatasetValidator._build_mixed_city_dataset`, `DatasetValidator._build_noise_injected_dataset`, `DatasetValidator._calculate_drift_score`
- **detection_facade:** `DetectionFacade.__init__`, `DetectionFacade._run_cost_detection`
- **divergence:** `DivergenceAnalyzer.__init__`, `DivergenceAnalyzer._calculate_kl_divergence`, `DivergenceAnalyzer._calculate_metrics`, `DivergenceAnalyzer._load_samples`, `DivergenceAnalyzer._parse_provenance_log`
- **envelope:** `EnvelopeValidationError.__init__`
- **leader:** `LeaderContext.__aenter__`, `LeaderContext.__aexit__`, `LeaderContext.__init__`
- **metrics:** `CostSimMetrics.__init__`, `CostSimMetrics._init_metrics`, `CostSimMetrics.record_auto_recovery`
- **pattern_detection:** `compute_error_signature`, `detect_cost_spikes`, `detect_failure_patterns`, `emit_feedback`, `get_feedback_summary`, `run_pattern_detection`
- **pattern_detection_driver:** `PatternDetectionDriver.__init__`
- **prediction_driver:** `PredictionDriver.__init__`
- **provenance:** `ProvenanceLog.from_dict`, `ProvenanceLog.to_dict`, `ProvenanceLogger.__init__`, `ProvenanceLogger._flush`, `ProvenanceLogger._store`, `ProvenanceLogger._write_to_db`, `ProvenanceLogger._write_to_file`
- **sandbox:** `CostSimSandbox.__init__`, `CostSimSandbox._get_v2_adapter`, `CostSimSandbox._log_comparison`

### Persistence

| Function | File | Side Effects |
|----------|------|--------------|
| `AnalyticsReadDriver.fetch_cost_by_feature` | analytics_read_driver | db_write |
| `AnalyticsReadDriver.fetch_cost_by_model` | analytics_read_driver | db_write |
| `AnalyticsReadDriver.fetch_cost_metrics` | analytics_read_driver | db_write |
| `AnalyticsReadDriver.fetch_cost_spend` | analytics_read_driver | db_write |
| `AnalyticsReadDriver.fetch_llm_usage` | analytics_read_driver | db_write |
| `AnalyticsReadDriver.fetch_worker_execution` | analytics_read_driver | db_write |
| `CostAnomalyDriver.fetch_baseline_avg` | cost_anomaly_driver | db_write |
| `CostAnomalyDriver.fetch_breach_exists_today` | cost_anomaly_driver | db_write |
| `CostAnomalyDriver.fetch_consecutive_breaches` | cost_anomaly_driver | db_write |
| `CostAnomalyDriver.fetch_daily_spend` | cost_anomaly_driver | db_write |
| `CostAnomalyDriver.fetch_drift_tracking` | cost_anomaly_driver | db_write |
| `CostAnomalyDriver.fetch_entity_baseline` | cost_anomaly_driver | db_write |
| `CostAnomalyDriver.fetch_entity_today_spend` | cost_anomaly_driver | db_write |
| `CostAnomalyDriver.fetch_feature_concentration` | cost_anomaly_driver | db_write |
| `CostAnomalyDriver.fetch_monthly_spend` | cost_anomaly_driver | db_write |
| `CostAnomalyDriver.fetch_prompt_comparison` | cost_anomaly_driver | db_write |
| `CostAnomalyDriver.fetch_request_comparison` | cost_anomaly_driver | db_write |
| `CostAnomalyDriver.fetch_retry_comparison` | cost_anomaly_driver | db_write |
| `CostAnomalyDriver.fetch_rolling_avg` | cost_anomaly_driver | db_write |
| `CostAnomalyDriver.fetch_tenant_baseline` | cost_anomaly_driver | db_write |
| `CostAnomalyDriver.fetch_tenant_today_spend` | cost_anomaly_driver | db_write |
| `CostAnomalyDriver.insert_breach_history` | cost_anomaly_driver | db_write |
| `CostAnomalyDriver.insert_drift_tracking` | cost_anomaly_driver | db_write |
| `CostAnomalyDriver.reset_drift_tracking` | cost_anomaly_driver | db_write |
| `CostAnomalyDriver.update_drift_tracking` | cost_anomaly_driver | db_write |
| `CostWriteDriver.create_cost_record` | cost_write_driver | db_write |
| `CostWriteDriver.create_feature_tag` | cost_write_driver | db_write |
| `CostWriteDriver.create_or_update_budget` | cost_write_driver | db_write |
| `CostWriteDriver.update_feature_tag` | cost_write_driver | db_write |
| `LeaderContext.is_leader` | leader | pure |
| `PatternDetectionDriver.fetch_completed_runs_with_costs` | pattern_detection_driver | db_write |
| `PatternDetectionDriver.fetch_failed_runs` | pattern_detection_driver | db_write |
| `PatternDetectionDriver.fetch_feedback_records` | pattern_detection_driver | db_write |
| `PatternDetectionDriver.insert_feedback` | pattern_detection_driver | db_write |
| `PredictionDriver.fetch_cost_runs` | prediction_driver | db_write |
| `PredictionDriver.fetch_failed_runs` | prediction_driver | db_write |
| `PredictionDriver.fetch_failure_patterns` | prediction_driver | db_write |
| `PredictionDriver.fetch_predictions` | prediction_driver | db_write |
| `PredictionDriver.fetch_run_totals` | prediction_driver | db_write |
| `PredictionDriver.insert_prediction` | prediction_driver | db_write |
| `backfill_v1_baseline` | provenance_async | pure |
| `check_duplicate` | provenance_async | db_write |
| `compute_input_hash` | provenance_async | pure |
| `count_provenance` | provenance_async | db_write |
| `get_analytics_read_driver` | analytics_read_driver | pure |
| `get_cost_anomaly_driver` | cost_anomaly_driver | pure |
| `get_cost_write_driver` | cost_write_driver | pure |
| `get_drift_stats` | provenance_async | db_write |
| `get_pattern_detection_driver` | pattern_detection_driver | pure |
| `get_prediction_driver` | prediction_driver | pure |
| `is_lock_held` | leader | db_write |
| `leader_election` | leader | pure |
| `persist_audit_record` | audit_persistence | db_write |
| `query_provenance` | provenance_async | db_write |
| `release_leader_lock` | leader | db_write |
| `try_acquire_leader_lock` | leader | db_write |
| `with_alert_worker_lock` | leader | pure |
| `with_archiver_lock` | leader | pure |
| `with_canary_lock` | leader | pure |
| `with_leader_lock` | leader | pure |
| `write_provenance` | provenance_async | db_write |
| `write_provenance_batch` | provenance_async | db_write |

### Unclassified (needs review)

_66 functions need manual classification._

- `AIConsolePanelEngine.close` (ai_console_panel_engine)
- `AIConsolePanelEngine.get_panel_ids` (ai_console_panel_engine)
- `AIConsolePanelEngine.get_panel_spec` (ai_console_panel_engine)
- `BaselineComputer.compute_baselines` (cost_snapshots)
- `CanaryRunner.run` (canary)
- `CoordinationManager.active_envelope_count` (coordinator)
- `CoordinationManager.apply` (coordinator)
- `CoordinationManager.expire_envelope` (coordinator)
- `CoordinationManager.get_active_envelopes` (coordinator)
- `CoordinationManager.get_audit_trail` (coordinator)
- `CoordinationManager.get_coordination_stats` (coordinator)
- `CoordinationManager.get_envelope_for_parameter` (coordinator)
- `CoordinationManager.get_envelopes_by_class` (coordinator)
- `CoordinationManager.is_kill_switch_active` (coordinator)
- `CoordinationManager.kill_switch` (coordinator)
- `CoordinationManager.reset_kill_switch` (coordinator)
- `CoordinationManager.revert` (coordinator)
- `CostSimMetrics.record_alert_send_failure` (metrics)
- `CostSimMetrics.record_canary_run` (metrics)
- `CostSimMetrics.record_cb_disabled` (metrics)
- _...and 46 more_

## 4. Explicit Non-Features

_No explicit non-feature declarations found in ANALYTICS_DOMAIN_LOCK_FINAL.md._
