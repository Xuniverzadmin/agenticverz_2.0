# Analytics — Software Bible

**Domain:** analytics  
**L2 Features:** 25  
**Scripts:** 29  
**Generator:** `scripts/ops/hoc_software_bible_generator.py`

---

## Script Registry

Each script's unique contribution and canonical function.

| Script | Layer | Canonical Function | Role | Decisions | Callers | Unique? |
|--------|-------|--------------------|------|-----------|---------|---------|
| ai_console_panel_engine | L5 | `AIConsolePanelEngine.evaluate_panel` | CANONICAL | 4 | ?:__init__, coordinator, envelope +2 | YES |
| analytics_facade | L5 | `AnalyticsFacade.get_usage_statistics` | CANONICAL | 11 | ?:analytics | L2:analytics | L4:analytics_handler, coordinator, envelope | YES |
| canary | L5 | `CanaryRunner.run` | CANONICAL | 2 | ?:__init__ | ?:test_canary, config, coordinator +2 | YES |
| config | L5 | `is_v2_sandbox_enabled` | CANONICAL | 2 | ?:jwt_auth | ?:costsim | ?:retry_policy | ?:llm_invoke_governed | ?:__init__ | ?:s1_rollback | ?:artifact | L3:webhook_adapter | ?:storage | ?:cus_health_driver, canary, divergence +3 | YES |
| coordinator | L5 | `CoordinationManager.apply` | CANONICAL | 2 | ?:__init__ | ?:check_priority4_intent | ?:test_c4_s1_coordination, envelope | YES |
| cost_anomaly_detector | L5 | `CostAnomalyDetector.detect_sustained_drift` | CANONICAL | 3 | ?:cost_intelligence | ?:facade | L5:detection_facade | L2:cost_intelligence | ?:anomaly_severity | ?:test_m26_prevention | ?:test_category4_cost_intelligence, coordinator, detection_facade +1 | YES |
| cost_model_engine | L5 | `estimate_step_cost` | CANONICAL | 12 | ?:v2_adapter | L3:v2_adapter | YES |
| cost_snapshot_schemas | L5 | `CostSnapshot.create` | LEAF | 0 | L5:cost_snapshots | L5s:__init__, canary, cost_snapshots +3 | YES |
| cost_snapshots | L5 | `SnapshotAnomalyDetector.evaluate_snapshot` | CANONICAL | 6 | coordinator, envelope | YES |
| cost_write_engine | L5 | `CostWriteService.__init__` | WRAPPER | 0 | coordinator, envelope | INTERFACE |
| costsim_models | L5 | `V2SimulationResult.compute_output_hash` | LEAF | 0 | canary, datasets, provenance +1 | YES |
| datasets | L5 | `DatasetValidator.validate_dataset` | CANONICAL | 7 | ?:costsim | L2:costsim, canary, coordinator +3 | YES |
| detection_facade | L5 | `DetectionFacade._run_cost_detection` | SUPERSET | 2 | L4:analytics_handler | ?:anomaly_severity, canary, coordinator +4 | YES |
| divergence | L5 | `DivergenceAnalyzer.generate_report` | CANONICAL | 3 | ?:costsim | ?:__init__ | L2:costsim, canary, coordinator +1 | YES |
| envelope | L5 | `calculate_bounded_value` | LEAF | 6 | ?:coordinator | ?:manager | ?:__init__ | ?:s1_retry_backoff | ?:s2_cost_smoothing | ?:logs | ?:s1_rollback | L5:coordinator | L5:s1_retry_backoff | L5:s2_cost_smoothing, coordinator | INTERFACE |
| metrics | L5 | `CostSimMetrics.__init__` | INTERNAL | 1 | ?:rbac_middleware | ?:rbac_integration | ?:tier_gating | ?:incidents | ?:activity | ?:recovery | ?:analytics | ?:recovery_ingest | ?:governance | ?:__init__, coordinator, envelope | **OVERLAP** |
| pattern_detection | L5 | `detect_cost_spikes` | CANONICAL | 6 | — | YES |
| prediction | L5 | `predict_failure_likelihood` | CANONICAL | 6 | ?:predictions | ?:prediction | ?:api | L6:prediction_driver | L2:predictions | ?:test_pb_s5_prediction | YES |
| provenance | L5 | `ProvenanceLogger.query` | CANONICAL | 8 | ?:feedback | ?:nodes | ?:panel_response_assembler | ?:pattern_detection | ?:divergence | ?:__init__ | ?:canary | ?:v2_adapter | L5:nodes | L3:v2_adapter, ai_console_panel_engine, canary +6 | YES |
| s1_retry_backoff | L5 | `create_s1_envelope` | LEAF | 0 | ?:__init__ | ?:test_c3_s3_failure_matrix | ?:test_c3_failure_scenarios | YES |
| sandbox | L5 | `CostSimSandbox.simulate` | CANONICAL | 4 | ?:engine | ?:__init__, coordinator, datasets +1 | YES |
| analytics_read_driver | L6 | `AnalyticsReadDriver.fetch_cost_by_feature` | LEAF | 0 | L5:analytics_facade, analytics_facade, coordinator +1 | YES |
| audit_persistence | L6 | `persist_audit_record` | LEAF | 1 | ?:coordinator | L5:coordinator | ?:check_priority4_intent, coordinator | YES |
| cost_anomaly_driver | L6 | `CostAnomalyDriver.fetch_baseline_avg` | LEAF | 0 | L6:__init__ | L5:cost_anomaly_detector, coordinator, cost_anomaly_detector +1 | YES |
| cost_write_driver | L6 | `CostWriteDriver.create_feature_tag` | LEAF | 0 | L5:cost_write_engine, coordinator, cost_write_engine +1 | YES |
| leader | L6 | `LeaderContext.__aenter__` | ENTRY | 1 | ?:leader | ?:alert_worker | ?:__init__ | ?:canary | L5:canary | ?:test_integration_real_db | ?:test_leader, canary, coordinator +1 | **OVERLAP** |
| pattern_detection_driver | L6 | `PatternDetectionDriver.fetch_completed_runs_with_costs` | LEAF | 1 | L5:pattern_detection, coordinator, envelope +2 | YES |
| prediction_driver | L6 | `PredictionDriver.fetch_cost_runs` | LEAF | 2 | L6:__init__ | L5:prediction, coordinator, envelope +2 | YES |
| provenance_async | L6 | `write_provenance_batch` | CANONICAL | 4 | ?:provenance_async | ?:test_integration_real_db | YES |

## Uncalled Functions

Functions with no internal or external callers detected.
May be: dead code, missing wiring, or entry points not yet traced.

- `cost_snapshots.run_daily_snapshot_and_baseline_job`
- `cost_snapshots.run_hourly_snapshot_job`
- `cost_write_engine.CostWriteService.create_cost_record`
- `cost_write_engine.CostWriteService.create_feature_tag`
- `cost_write_engine.CostWriteService.create_or_update_budget`
- `cost_write_engine.CostWriteService.update_feature_tag`
- `pattern_detection.get_feedback_summary`
- `pattern_detection.run_pattern_detection`

## Overlapping Scripts (same purpose, same layer)

These scripts may serve duplicate purposes within the domain.

- `cost_write_engine` — canonical: `CostWriteService.__init__` (WRAPPER)
- `leader` — canonical: `LeaderContext.__aenter__` (ENTRY)
- `metrics` — canonical: `CostSimMetrics.__init__` (INTERNAL)

## L2 Feature Chains

| Status | Count |
|--------|-------|
| COMPLETE (L2→L4→L5→L6) | 25 |
| GAP (L2→L5 direct) | 0 |

### Wired Features (L2→L4→L5→L6)

#### DELETE /{scenario_id}
```
L2:scenarios.delete_scenario → L4:analytics_handler → L6:analytics_read_driver.AnalyticsReadDriver.fetch_cost_by_feature
```

#### GET /canary/reports
```
L2:costsim.get_canary_reports → L4:analytics_handler → L6:analytics_read_driver.AnalyticsReadDriver.fetch_cost_by_feature
```

#### GET /datasets
```
L2:costsim.list_datasets → L4:analytics_handler → L6:analytics_read_driver.AnalyticsReadDriver.fetch_cost_by_feature
```

#### GET /datasets/{dataset_id}
```
L2:costsim.get_dataset_info → L4:analytics_handler → L6:analytics_read_driver.AnalyticsReadDriver.fetch_cost_by_feature
```

#### GET /divergence
```
L2:costsim.get_divergence_report → L4:analytics_handler → L6:analytics_read_driver.AnalyticsReadDriver.fetch_cost_by_feature
```

#### GET /info/immutability
```
L2:scenarios.get_immutability_info → L4:analytics_handler → L6:analytics_read_driver.AnalyticsReadDriver.fetch_cost_by_feature
```

#### GET /stats/summary
```
L2:feedback.get_feedback_stats → L4:analytics_handler → L6:analytics_read_driver.AnalyticsReadDriver.fetch_cost_by_feature
```

#### GET /stats/summary
```
L2:predictions.get_prediction_stats → L4:analytics_handler → L6:analytics_read_driver.AnalyticsReadDriver.fetch_cost_by_feature
```

#### GET /subject/{subject_type}/{subject_id}
```
L2:predictions.get_predictions_for_subject → L4:analytics_handler → L6:analytics_read_driver.AnalyticsReadDriver.fetch_cost_by_feature
```

#### GET /v2/incidents
```
L2:costsim.get_incidents → L4:analytics_handler → L6:analytics_read_driver.AnalyticsReadDriver.fetch_cost_by_feature
```

#### GET /v2/status
```
L2:costsim.get_sandbox_status → L4:analytics_handler → L6:analytics_read_driver.AnalyticsReadDriver.fetch_cost_by_feature
```

#### GET /{feedback_id}
```
L2:feedback.get_feedback → L4:analytics_handler → L6:analytics_read_driver.AnalyticsReadDriver.fetch_cost_by_feature
```

#### GET /{prediction_id}
```
L2:predictions.get_prediction → L4:analytics_handler → L6:analytics_read_driver.AnalyticsReadDriver.fetch_cost_by_feature
```

#### GET /{scenario_id}
```
L2:scenarios.get_scenario → L4:analytics_handler → L6:analytics_read_driver.AnalyticsReadDriver.fetch_cost_by_feature
```

#### POST /canary/run
```
L2:costsim.trigger_canary_run → L4:analytics_handler → L6:analytics_read_driver.AnalyticsReadDriver.fetch_cost_by_feature
```

#### POST /datasets/validate-all
```
L2:costsim.validate_all → L4:analytics_handler → L6:analytics_read_driver.AnalyticsReadDriver.fetch_cost_by_feature
```

#### POST /datasets/{dataset_id}/validate
```
L2:costsim.validate_against_dataset → L4:analytics_handler → L6:analytics_read_driver.AnalyticsReadDriver.fetch_cost_by_feature
```

#### POST /simulate-adhoc
```
L2:scenarios.simulate_adhoc → L4:analytics_handler → L6:analytics_read_driver.AnalyticsReadDriver.fetch_cost_by_feature
```

#### POST /v2/reset
```
L2:costsim.reset_circuit_breaker → L4:analytics_handler → L6:analytics_read_driver.AnalyticsReadDriver.fetch_cost_by_feature
```

#### POST /v2/simulate
```
L2:costsim.simulate_v2 → L4:analytics_handler → L6:analytics_read_driver.AnalyticsReadDriver.fetch_cost_by_feature
```

#### POST /{scenario_id}/simulate
```
L2:scenarios.simulate_scenario → L4:analytics_handler → L6:analytics_read_driver.AnalyticsReadDriver.fetch_cost_by_feature
```

#### create_scenario
```
L2:scenarios.create_scenario → L4:analytics_handler → L6:analytics_read_driver.AnalyticsReadDriver.fetch_cost_by_feature
```

#### list_feedback
```
L2:feedback.list_feedback → L4:analytics_handler → L6:analytics_read_driver.AnalyticsReadDriver.fetch_cost_by_feature
```

#### list_predictions
```
L2:predictions.list_predictions → L4:analytics_handler → L6:analytics_read_driver.AnalyticsReadDriver.fetch_cost_by_feature
```

#### list_scenarios
```
L2:scenarios.list_scenarios → L4:analytics_handler → L6:analytics_read_driver.AnalyticsReadDriver.fetch_cost_by_feature
```

## Canonical Algorithm Inventory

| Function | File | Role | Decisions | Stmts | Persistence | Delegates To |
|----------|------|------|-----------|-------|-------------|--------------|
| `AIConsolePanelEngine.evaluate_panel` | ai_console_panel_engine | CANONICAL | 4 | 3 | no | ai_console_panel_engine:AIConsolePanelEngine._create_short_c |
| `AnalyticsFacade.get_usage_statistics` | analytics_facade | CANONICAL | 11 | 20 | no | analytics_facade:AnalyticsFacade._calculate_freshness | anal |
| `CanaryRunner._approximate_kl_divergence` | canary | SUPERSET | 4 | 21 | no | provenance:ProvenanceLogger.log |
| `CanaryRunner._load_samples` | canary | SUPERSET | 2 | 4 | no | canary:CanaryRunner._generate_synthetic_samples | provenance |
| `CanaryRunner._run_internal` | canary | SUPERSET | 9 | 16 | no | canary:CanaryRunner._calculate_metrics | canary:CanaryRunner |
| `CanaryRunner.run` | canary | CANONICAL | 2 | 3 | no | canary:CanaryRunner._run_internal | leader:leader_election |
| `CoordinationManager._find_preemption_targets` | coordinator | SUPERSET | 2 | 4 | no | envelope:has_higher_priority |
| `CoordinationManager._revert_envelope` | coordinator | SUPERSET | 3 | 8 | no | coordinator:CoordinationManager._emit_audit_record | coordin |
| `CoordinationManager.apply` | coordinator | CANONICAL | 2 | 14 | no | coordinator:CoordinationManager._emit_audit_record | coordin |
| `CoordinationManager.check_allowed` | coordinator | SUPERSET | 3 | 7 | no | coordinator:CoordinationManager._emit_audit_record | coordin |
| `CoordinationManager.expire_envelope` | coordinator | SUPERSET | 2 | 10 | no | coordinator:CoordinationManager._get_parameter_key |
| `CostAnomalyDetector._derive_cause` | cost_anomaly_detector | SUPERSET | 9 | 10 | no | cost_anomaly_driver:CostAnomalyDriver.fetch_feature_concentr |
| `CostAnomalyDetector._detect_entity_spikes` | cost_anomaly_detector | SUPERSET | 3 | 8 | no | cost_anomaly_detector:CostAnomalyDetector._derive_cause | co |
| `CostAnomalyDetector._detect_tenant_spike` | cost_anomaly_detector | SUPERSET | 3 | 11 | no | cost_anomaly_detector:CostAnomalyDetector._derive_cause | co |
| `CostAnomalyDetector._update_drift_tracking` | cost_anomaly_detector | SUPERSET | 2 | 2 | no | cost_anomaly_driver:CostAnomalyDriver.fetch_drift_tracking | |
| `CostAnomalyDetector.detect_budget_issues` | cost_anomaly_detector | SUPERSET | 4 | 6 | no | cost_anomaly_detector:CostAnomalyDetector._check_budget_thre |
| `CostAnomalyDetector.detect_sustained_drift` | cost_anomaly_detector | CANONICAL | 3 | 12 | no | cost_anomaly_detector:CostAnomalyDetector._derive_cause | co |
| `CostSimSandbox.simulate` | sandbox | CANONICAL | 4 | 8 | no | config:is_v2_sandbox_enabled | sandbox:CostSimSandbox._get_v |
| `DatasetValidator.validate_dataset` | datasets | CANONICAL | 7 | 12 | no | datasets:DatasetValidator._calculate_drift_score | sandbox:C |
| `DetectionFacade._run_cost_detection` | detection_facade | SUPERSET | 2 | 4 | no | cost_anomaly_detector:run_anomaly_detection_with_governance |
| `DivergenceAnalyzer._calculate_kl_divergence` | divergence | SUPERSET | 4 | 21 | no | provenance:ProvenanceLogger.log |
| `DivergenceAnalyzer.generate_report` | divergence | CANONICAL | 3 | 8 | no | canary:CanaryRunner._calculate_metrics | canary:CanaryRunner |
| `ProvenanceLogger._flush` | provenance | SUPERSET | 3 | 5 | no | provenance:ProvenanceLogger._write_to_db | provenance:Proven |
| `ProvenanceLogger.query` | provenance | CANONICAL | 8 | 3 | no | provenance:ProvenanceLog.from_dict |
| `SnapshotAnomalyDetector.evaluate_snapshot` | cost_snapshots | CANONICAL | 6 | 7 | yes | cost_snapshots:SnapshotAnomalyDetector._create_anomaly_from_ |
| `SnapshotComputer._compute_snapshot` | cost_snapshots | SUPERSET | 2 | 6 | no | cost_snapshot_schemas:CostSnapshot.create | cost_snapshots:S |
| `detect_cost_spikes` | pattern_detection | CANONICAL | 6 | 8 | no | pattern_detection_driver:PatternDetectionDriver.fetch_comple |
| `detect_failure_patterns` | pattern_detection | SUPERSET | 3 | 9 | no | pattern_detection:compute_error_signature | pattern_detectio |
| `estimate_step_cost` | cost_model_engine | CANONICAL | 12 | 7 | no | cost_model_engine:get_skill_coefficients |
| `is_v2_sandbox_enabled` | config | CANONICAL | 2 | 4 | no | config:get_config |
| `predict_cost_overrun` | prediction | SUPERSET | 5 | 10 | no | prediction_driver:PredictionDriver.fetch_cost_runs |
| `predict_failure_likelihood` | prediction | CANONICAL | 6 | 12 | no | pattern_detection_driver:PatternDetectionDriver.fetch_failed |
| `query_provenance` | provenance_async | SUPERSET | 7 | 1 | yes | cost_snapshot_schemas:CostSnapshot.to_dict | costsim_models: |
| `run_anomaly_detection_with_governance` | cost_anomaly_detector | SUPERSET | 2 | 7 | no | cost_anomaly_detector:run_anomaly_detection_with_facts |
| `write_provenance` | provenance_async | SUPERSET | 3 | 3 | yes | ai_console_panel_engine:AIConsolePanelEngine.close | provena |
| `write_provenance_batch` | provenance_async | CANONICAL | 4 | 4 | yes | ai_console_panel_engine:AIConsolePanelEngine.close | provena |

## Wrapper Inventory

_78 thin delegation functions._

- `ai_console_panel_engine.AIConsolePanelEngine.close` → provenance:ProvenanceLogger.close
- `ai_console_panel_engine.AIConsolePanelEngine.get_panel_ids` → ?
- `analytics_facade.AnalyticsFacade.__init__` → ?
- `analytics_read_driver.AnalyticsReadDriver.__init__` → ?
- `detection_facade.AnomalyInfo.to_dict` → ?
- `cost_snapshots.BaselineComputer.__init__` → ?
- `costsim_models.CanaryReport.to_dict` → ?
- `canary.CanaryRunner._compare_with_golden` → ?
- `costsim_models.ComparisonResult.to_dict` → ?
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
- `cost_write_driver.CostWriteDriver.__init__` → ?
- `cost_write_driver.CostWriteDriver.create_cost_record` → ?
- `cost_write_engine.CostWriteService.__init__` → cost_write_driver:get_cost_write_driver
- `cost_write_engine.CostWriteService.create_cost_record` → cost_write_driver:CostWriteDriver.create_cost_record
- `cost_write_engine.CostWriteService.create_feature_tag` → cost_write_driver:CostWriteDriver.create_feature_tag
- _...and 48 more_
