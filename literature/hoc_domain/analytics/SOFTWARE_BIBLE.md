# Analytics — Software Bible

**Domain:** analytics  
**L2 Features:** 25  
**Scripts:** 29  
**Generator:** `scripts/ops/hoc_software_bible_generator.py`

---

## Reality Delta (2026-02-16, L2.1 Facade Activation Wiring)

- Public facade activation path for analytics is now explicitly wired at L2.1:
- backend/app/hoc/api/facades/cus/analytics/analytics_fac.py
- L2 public boundary module for domain-scoped facade entry is present at:
- backend/app/hoc/api/cus/analytics/analytics_public.py
- Runtime chain is fixed as:
- app.py -> app.hoc.api.facades.cus -> domain facade bundle -> analytics_public.py -> L4 registry.execute(...)
- Current status: analytics_public.py remains scaffold-only (no behavior change yet); existing domain routers stay active during incremental rollout.

## Reality Delta (2026-02-16, PR-7 Analytics Usage Facade Contract Hardening)

- Analytics public facade now implements a concrete read slice at:
- `backend/app/hoc/api/cus/analytics/analytics_public.py`
- Endpoint added:
- `GET /cus/analytics/statistics/usage` (gateway: `/hoc/api/cus/analytics/statistics/usage`)
- Boundary contract now enforces:
- strict query allowlist (`from`, `to`, `resolution`, `scope`)
- timezone-required datetime parsing and max 90-day window
- explicit `as_of` rejection in PR-7
- single dispatch path:
- `analytics_public.py -> registry.execute(\"analytics.query\", method=\"get_usage_statistics\", ...)`

## Reality Delta (2026-02-07)

- Execution topology: analytics L2 routes dispatch via L4 `OperationRegistry` (0 direct L2→L5 gaps).
- L5/L6 purity: `PYTHONPATH=. python3 backend/scripts/ops/hoc_l5_l6_purity_audit.py --domain analytics --json --advisory` reports 0 blocking, 0 advisory.
- Remaining coherence debt (execution boundary): `python3 scripts/ops/l5_spine_pairing_gap_detector.py --domain analytics --json` reports 9 orphaned L5 entry modules: `ai_console_panel_engine.py`, `alert_worker_engine.py`, `coordinator_engine.py`, `cost_model_engine.py`, `cost_write_engine.py`, `costsim_models_engine.py`, `pattern_detection_engine.py`, `provenance_engine.py`, `v2_adapter_engine.py`.
- Plan: `docs/architecture/hoc/DOMAIN_EXECUTION_BOUNDARY_REMEDIATION_PLAN.md`.

## Reality Delta (2026-02-11)

- Canonical UC alignment now includes `UC-008` and `UC-016`, both architecture `GREEN`.
- Analytics reproducibility artifact contract (`dataset_version`, `input_window_hash`, `compute_code_version`, `as_of`) is now covered by UC-MON storage/event validation.
- Deterministic read baseline for priority analytics surfaces is now passing strict validation.

## Reality Delta (2026-02-12)

- Analytics expansion pack `UC-024..UC-028` is now architecture `GREEN`:
- anomaly detection lifecycle (`UC-024`)
- prediction cycle lifecycle (`UC-025`)
- dataset validation lifecycle (`UC-026`)
- snapshot/baseline job lifecycle (`UC-027`)
- cost write lifecycle (`UC-028`)
- Canonical usecase registry/linkage now include these closures with evidence references.
- Production readiness for these UCs is tracked separately in `backend/app/hoc/docs/architecture/usecases/PROD_READINESS_TRACKER.md` and remains independent from architecture status.

## Reality Delta (2026-02-12, Wave-2 Script Coverage Audit)

- Wave-2 script coverage (`analytics + incidents + activity`) has been independently audited and reconciled.
- Analytics core-scope classification is complete:
- `22` scripts marked `UC_LINKED`
- `19` scripts marked `NON_UC_SUPPORT`
- Core analytics residual is `0` in Wave-2 target scope.
- Deterministic gates remain clean post-wave and governance suite now runs `219` passing tests in `test_uc018_uc032_expansion.py`.
- Canonical audit artifacts:
- `backend/app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_2_implemented.md`
- `backend/app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_2_AUDIT_2026-02-12.md`

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
| cost_snapshots_engine | L5 | `SnapshotAnomalyDetector.evaluate_snapshot` | CANONICAL | 6 | coordinator, envelope | YES *(updated PIN-508)* |
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
| cost_snapshots_driver | L6 | `CostSnapshotsDriver.fetch_snapshot_data` | LEAF | 0 | L5:cost_snapshots_engine | L5:cost_snapshots_engine | YES *(NEW PIN-508)* |
| cost_write_driver | L6 | `CostWriteDriver.create_feature_tag` | LEAF | 0 | L5:cost_write_engine, coordinator, cost_write_engine +1 | YES |
| leader | L6 | `LeaderContext.__aenter__` | ENTRY | 1 | ?:leader | ?:alert_worker | ?:__init__ | ?:canary | L5:canary | ?:test_integration_real_db | ?:test_leader, canary, coordinator +1 | **OVERLAP** |
| pattern_detection_driver | L6 | `PatternDetectionDriver.fetch_completed_runs_with_costs` | LEAF | 1 | L5:pattern_detection, coordinator, envelope +2 | YES |
| prediction_driver | L6 | `PredictionDriver.fetch_cost_runs` | LEAF | 2 | L6:__init__ | L5:prediction, coordinator, envelope +2 | YES |
| provenance_async | L6 | `write_provenance_batch` | CANONICAL | 4 | ?:provenance_async | ?:test_integration_real_db | YES |

## Uncalled Functions

Functions with no internal or external callers detected.
May be: unused code, missing wiring, or entry points not yet traced.

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

---

## PIN-507 Law 5 Remediation (2026-02-01)

| Script | Change | Reference |
|--------|--------|-----------|
| L4 `analytics_handler.py` | `AnalyticsQueryHandler`: Replaced `getattr()` dispatch with explicit map (3 methods). `AnalyticsDetectionHandler`: Replaced `getattr()` dispatch with explicit map (6 methods). Zero reflection in dispatch paths. | PIN-507 Law 5 |
| `cost_snapshots_engine.py` | Added `from sqlalchemy import text` at top. Replaced 13 `__import__("sqlalchemy").text(...)` → `text(...)`. Updated header: `Forbidden Imports: sqlalchemy ORM (session, query); sqlalchemy.text is permitted (PIN-507 Law 5)`. | PIN-507 Law 5 |

## PIN-508 Phase 1A — Cost Snapshots Hybrid Refactor (2026-02-01)

**Objective:** Eliminate L5/L6 hybrid layer violation in cost_snapshots_engine.py by extracting database operations.

| Component | Change | Detail |
|-----------|--------|--------|
| `cost_snapshots_engine.py` | Layer reassignment | Changed from "L5/L6 — HYBRID" to "L5 — Domain Engine" (pure business logic) |
| `cost_snapshots_engine.py` | Database extraction | All `session.execute()` calls extracted to new L6 driver `cost_snapshots_driver.py` |
| `cost_snapshots_engine.py` | Constructor injection | Now accepts `CostSnapshotsDriverProtocol` for all DB operations (dependency inversion) |
| `cost_snapshot_schemas.py` | Protocol addition | `CostSnapshotsDriverProtocol` added to L5_schemas for engine-driver contract |
| `cost_snapshots_driver.py` | NEW (L6 driver) | Implements `CostSnapshotsDriverProtocol`; contains all session.execute() calls extracted from engine |

**Result:** cost_snapshots_engine.py now pure L5 domain logic; cost_snapshots_driver.py pure L6 data access (per HOC V2.0.0 architecture).

## PIN-510 Phase 1C — Analytics→Incidents L4 Coordinator (2026-02-01)

- `CostAnomalyFact` moved from `incidents/L5_engines/anomaly_bridge.py` to `hoc/cus/hoc_spine/schemas/anomaly_types.py` (schema admission compliant: consumers = analytics, incidents)
- New L4 coordinator: `hoc/cus/hoc_spine/orchestrator/coordinators/anomaly_incident_coordinator.py`
- Stale `L3_adapters` import paths in `cost_anomaly_detector_engine.py` fixed to canonical paths
- Backward-compat re-export left in `anomaly_bridge.py`
- Reference: `docs/memory-pins/PIN-510-domain-remediation-queue.md`

## PIN-509 Tooling Hardening (2026-02-01)

- CI checks 16–18 added to `scripts/ci/check_init_hygiene.py`:
  - Check 16: Frozen import ban (no imports from `_frozen/` paths)
  - Check 17: L5 Session symbol import ban (type erasure enforcement)
  - Check 18: Protocol surface baseline (capability creep prevention, max 12 methods)
- New scripts: `collapse_tombstones.py`, `new_l5_engine.py`, `new_l6_driver.py`
- `app/services/__init__.py` now emits DeprecationWarning
- Reference: `docs/memory-pins/PIN-509-tooling-hardening.md`

## PIN-513 Topology Completion & Hygiene (2026-02-01)

### Phase 1A — Stale L3_adapters Comment Fix

| File | Change | Reference |
|------|--------|-----------|
| `cost_anomaly_detector_engine.py:53` | Comment fixed: `# See: app/hoc/cus/incidents/L3_adapters/anomaly_bridge.py` → `# See: app/hoc/cus/incidents/L5_engines/anomaly_bridge.py` | PIN-513 Phase 1A |

### Phase 1D — Dead Adapter Deletion

| File | Change | Reference |
|------|--------|-----------|
| `adapters/v2_adapter.py` | **DELETED** — 431 LOC, zero active HOC callers. `cost_model_engine.py` callers column updated (was sole caller via legacy L3 path). | PIN-513 Phase 1D |

### Phase 4 — Unused Code Audit

- `UNUSED_CODE_AUDIT.csv` generated (renamed from DEAD_CODE_AUDIT.csv, Phase 7): analytics domain entries sub-typed as UNWIRED_FACTORY, UNWIRED_CORE_LOGIC, etc.
- CI check 26 (`check_no_l3_adapters_references`) added to `check_init_hygiene.py`

## PIN-513 Phase 7 — Reverse Boundary Severing (HOC→services) (2026-02-01)

| File | Change | Reference |
|------|--------|-----------|
| `api/cus/logs/cost_intelligence.py:43` | Import swapped: `app.services.cost_write_service.CostWriteService` → `app.hoc.cus.analytics.L5_engines.cost_write_engine.CostWriteService` | PIN-513 Phase 7, Step 1 |
| `api/cus/logs/cost_intelligence.py:1240` | Import swapped: `app.services.cost_anomaly_detector.run_anomaly_detection` → `app.hoc.cus.analytics.L5_engines.cost_anomaly_detector_engine.run_anomaly_detection` | PIN-513 Phase 7, Step 2 |

**Impact:** 2 HOC→services imports fully severed. Analytics L5 engines (`cost_write_engine`, `cost_anomaly_detector_engine`) confirmed as 100% API-compatible replacements. Debt tracker: `app/hoc/hoc_debt_missing_caller.yaml`.

## PIN-513 Phase C — Costsim Legacy Cutover (2026-02-01)

**Objective:** Rewire analytics domain engines from legacy `app.costsim.*` imports to HOC-internal canonical paths.

| Script | Change | Reference |
|--------|--------|-----------|
| `divergence_engine.py` | Rewired 3 imports: `config`→`config_engine`, `models`→`costsim_models_engine`, `provenance`→`provenance_engine` | PIN-513 Phase C |
| `sandbox_engine.py` | Rewired 3 imports: `circuit_breaker_async`→`circuit_breaker_async_driver`, `config`→`config_engine`, `models`→`costsim_models_engine`. 1 TRANSITIONAL: `v2_adapter` | PIN-513 Phase C |
| `metrics_engine.py` | Rewired 1 import: `config`→`config_engine` | PIN-513 Phase C |
| `provenance_engine.py` | Rewired 1 import: `config`→`config_engine` | PIN-513 Phase C |
| `canary_engine.py` | Rewired 5 imports: `circuit_breaker_async`, `config`, `leader`, `models`, `provenance`. 2 TRANSITIONAL: `circuit_breaker`, `v2_adapter` | PIN-513 Phase C |
| `datasets_engine.py` | Rewired 1 import: `models`→`costsim_models_engine`. 1 TRANSITIONAL: `v2_adapter` | PIN-513 Phase C |
| `leader_driver.py` (L6) | No code change (docstring reference only) | PIN-513 Phase C |
| `provenance_driver.py` (L6) | No code change (docstring reference only) | PIN-513 Phase C |

**TRANSITIONAL imports remaining:**
- `app.costsim.v2_adapter` (3 files: `sandbox_engine`, `canary_engine`, `datasets_engine`)
- `app.costsim.circuit_breaker.get_circuit_breaker` (1 file: `canary_engine`)

**Key Dependency:** `costsim_models_engine.py` now serves as HOC replacement for legacy `app/costsim/models.py`, providing canonical model classes (`V2SimulationResult`, `CanaryReport`, etc.) within HOC domain structure.

### PIN-513 TRANSITIONAL Resolution — v2_adapter_engine + circuit_breaker (2026-02-01)

**New file:** `analytics/L5_engines/v2_adapter_engine.py`
- HOC version of `app/costsim/v2_adapter.py` (375 lines)
- All imports rewired to HOC paths (config_engine, costsim_models_engine, provenance_engine)
- Delegates cost model logic to L4 via lazy imports from `app.services.cost_model_engine` (separate cutover scope)
- Callers: sandbox_engine, datasets_engine, canary_engine

**TRANSITIONAL imports severed:**

| Import | Files | Resolution |
|--------|-------|------------|
| `from app.costsim.v2_adapter import CostSimV2Adapter` | sandbox_engine, datasets_engine, canary_engine | → `from app.hoc.cus.analytics.L5_engines.v2_adapter_engine import CostSimV2Adapter` |
| `from app.costsim.circuit_breaker import get_circuit_breaker` | api/costsim, hoc/api/cus/analytics/costsim, canary_engine | → `from app.hoc.cus.controls.L6_drivers.circuit_breaker_async_driver import get_circuit_breaker` |

**Alias added:** `circuit_breaker_async_driver.get_circuit_breaker = get_async_circuit_breaker` (drop-in singleton replacement for legacy no-arg factory).

**Result:** Zero `from app.costsim` imports remain in HOC callers or API layer. Costsim legacy tree is now fully decoupled from HOC.

### PIN-513 Step 9 — cost_model_engine Severing (2026-02-01)

Rewired 3 lazy imports in `v2_adapter_engine.py` from `app.services.cost_model_engine` to `app.hoc.cus.analytics.L5_engines.cost_model_engine` (HOC copy already existed with identical code body). Zero `from app.services` code imports remain in analytics domain.

### PIN-513 Phase 8 — Zero-Caller Wiring (2026-02-01)

| Component | L4 Owner | Action |
|-----------|----------|--------|
| `cost_snapshots_engine` | **NEW** `hoc_spine/orchestrator/handlers/analytics_snapshot_handler.py` | L4 handler dispatches `run_hourly`, `run_daily`, `evaluate_anomalies` to SnapshotComputer/BaselineComputer/SnapshotAnomalyDetector via driver protocol injection |
| `prediction_engine` | **NEW** `hoc_spine/orchestrator/handlers/analytics_prediction_handler.py` | L4 handler dispatches `predict_failure`, `predict_cost_overrun`, `run_cycle`, `get_summary` |
| `s1_retry_backoff_engine` | Moved to `hoc_spine/utilities/s1_retry_backoff.py` | Reclassified L4 Spine Utility / SHARED. Original deleted from analytics/L5_engines. |
| `coordination_audit_driver` | `anomaly_incident_coordinator.py` | Added `persist_coordination_audit()` method — lazy import of `persist_audit_record` from L6 driver |

**Signature audit fix (2026-02-01):** `analytics_snapshot_handler.py` — removed spurious `tenant_id` from `evaluate_snapshot` call. `analytics_prediction_handler.py` — added `get_prediction_driver(session)` for `predict_failure`/`predict_cost_overrun`; removed `session` from `run_cycle`/`get_summary`. All 12 call sites re-verified clean.

---

### PIN-513 Phase 9 Batch 3A Amendment (2026-02-01)

**Scope:** 46 analytics symbols reclassified.

| Category | Count | Details |
|----------|-------|---------|
| PHANTOM_NO_HOC_COPY | 5 | envelope_engine (5) — source deleted, only .pyc remains |
| CSV stale (already wired) | 6 | cost_snapshots_engine (2), prediction_engine (4), s1_retry_backoff_engine (1), coordination_audit_driver (1) |
| WIRED via parent | 3 | prediction_engine sub-functions called by run_prediction_cycle |
| PURE_INFRA_UTILITY | 3 | provenance_engine — imported directly by coordinators |
| WIRED (new) | 29 | canary (1), config (4), datasets+divergence (4), metrics (2), sandbox (2), leader_driver (8), provenance_driver (8) |

**Files created:**
- `hoc_spine/orchestrator/coordinators/canary_coordinator.py` — L4: scheduled canary runs
- `hoc_spine/orchestrator/handlers/analytics_config_handler.py` — L4: CostSim config visibility
- `hoc_spine/orchestrator/handlers/analytics_validation_handler.py` — L4: dataset validation + divergence
- `hoc_spine/orchestrator/handlers/analytics_metrics_handler.py` — L4: metrics + alert rules
- `hoc_spine/orchestrator/handlers/analytics_sandbox_handler.py` — L4: sandbox experimentation
- `hoc_spine/orchestrator/coordinators/leadership_coordinator.py` — L4: distributed locking
- `hoc_spine/orchestrator/coordinators/provenance_coordinator.py` — L4: provenance DB ops

---

### PIN-513 Phase 9 Batch 4 Amendment (2026-02-01)

**Deletions:**
- `cost_write_engine.py` — DELETED (zero-logic passthrough, zero callers)

**Files created:**
- `hoc_spine/orchestrator/coordinators/snapshot_scheduler.py` — L4: multi-tenant snapshot batch scheduler

**Final status:** Zero UNWIRED analytics symbols remain.

### PIN-513 Phase 9 Batch 5 Amendment (2026-02-01)

**CI invariant hardening — analytics domain impact:**

- `costsim.py` frozen in check 27 allowlist (L2→L5/L6 bypass — imports config_engine, canary_engine, sandbox_engine, divergence_engine, datasets_engine, circuit_breaker_async_driver)
- `cost_intelligence.py` frozen in check 27 allowlist (L2→L5/L6 bypass — imports cost_write_engine, cost_anomaly_detector_engine)
- `cost_anomaly_detector_engine.py` frozen in check 28 allowlist (L5→L5 cross-domain — imports incidents/anomaly_bridge)

**No new files may introduce these patterns.** Existing violations are frozen; removal requires routing through L4 spine handlers.
