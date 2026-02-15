# UC Script Coverage Wave-2: analytics + incidents + activity — Implementation Evidence

- Date: 2026-02-12
- Scope: Classify 80 unlinked scripts in analytics (32) + incidents (30) + activity (18) domains
- Sources: `HOC_CUS_SCRIPT_UC_CLASSIFICATION_2026-02-12.csv`, `HOC_CUS_CORE6_UC_GAP_UNLINKED_2026-02-12.txt`
- Result: 35 UC_LINKED + 45 NON_UC_SUPPORT + 0 DEPRECATED

## 1) Before/After Counts

### Before Wave-2
| Domain | Total Scripts | UC_LINKED | Unlinked | Coverage |
|--------|-------------|-----------|----------|----------|
| activity | 20 | 2 | 18 | 10.0% |
| analytics | 41 | 9 | 32 | 22.0% |
| incidents | 37 | 7 | 30 | 18.9% |
| **Total** | **98** | **18** | **80** | **18.4%** |

### After Wave-2
| Domain | Total Scripts | UC_LINKED | NON_UC_SUPPORT | Unclassified | Coverage |
|--------|-------------|-----------|----------------|--------------|----------|
| activity | 20 | 7 | 13 | 0 | 100% classified |
| analytics | 41 | 22 | 19 | 0 | 100% classified |
| incidents | 37 | 24 | 13 | 0 | 100% classified |
| **Total** | **98** | **53** | **45** | **0** | **100% classified** |

### Delta
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Activity UC_LINKED | 2 | 7 | +5 |
| Analytics UC_LINKED | 9 | 22 | +13 |
| Incidents UC_LINKED | 7 | 24 | +17 |
| Total UC_LINKED | 18 | 53 | +35 |
| Unclassified | 80 | 0 | -80 |

## 2) Classification Breakdown

### Activity Domain (18 unlinked scripts)

**UC_LINKED (5 scripts):**

| Script | UC | Rationale |
|--------|-----|-----------|
| `L5_engines/activity_facade.py` | UC-MON-01 | Unified activity operations facade (get_runs, get_signals, acknowledge) |
| `L5_engines/cus_telemetry_engine.py` | UC-MON-05 | Customer telemetry decisions (ingest, aggregates, usage) |
| `L6_drivers/activity_read_driver.py` | UC-MON-01 | Activity data reads (fetch_runs, fetch_metrics) |
| `L6_drivers/cus_telemetry_driver.py` | UC-MON-05 | Telemetry data persistence (create_usage, upsert_aggregate) |
| `adapters/customer_activity_adapter.py` | UC-MON-01 | Customer boundary adapter (tenant isolation, schema transform) |

**NON_UC_SUPPORT (13 scripts):**

| Group | Count | Examples |
|-------|-------|---------|
| Package init files | 3 | `__init__.py` across L5_engines, L5_schemas, L6_drivers |
| Enum definitions | 1 | `activity_enums.py` (SignalType, SeverityLevel, RunState) |
| Stub/demoted engines | 3 | `attention_ranking.py`, `cost_analysis.py`, `pattern_detection.py` |
| Infrastructure utilities | 1 | `signal_identity.py` (dedup fingerprinting) |
| Internal drivers | 3 | `orphan_recovery_driver.py` (cleanup), `run_metrics_driver.py` (internal metrics), `run_signal_driver.py` (risk updates) |
| Adapters | 2 | `adapters/__init__.py`, `workers_adapter.py` (internal worker) |

### Analytics Domain (32 unlinked scripts)

**UC_LINKED (13 scripts):**

| Script | UC | Rationale |
|--------|-----|-----------|
| `L5_engines/analytics_facade.py` | UC-024 | Analytics entry point for cost/trace queries |
| `L5_engines/canary_engine.py` | UC-027 | Daily canary runner for CostSim V2 validation |
| `L5_engines/detection_facade.py` | UC-024 | Anomaly detection facade entry point |
| `L5_engines/feedback_read_engine.py` | UC-MON-04 | Feedback read business logic |
| `L5_engines/prediction_read_engine.py` | UC-025 | Prediction read logic (PB-S5 compliant) |
| `L5_engines/sandbox_engine.py` | UC-027 | CostSim V2 sandbox routing (V1/V2 comparison) |
| `L5_engines/v2_adapter.py` | UC-027 | CostSim V2 translation + comparison layer |
| `L6_drivers/analytics_read_driver.py` | UC-024 | Analytics data access (cost_records, traces) |
| `L6_drivers/canary_report_driver.py` | UC-027 | Canary validation report persistence |
| `L6_drivers/cost_anomaly_read_driver.py` | UC-024 | Budget/anomaly read operations |
| `L6_drivers/cost_snapshots_driver.py` | UC-027 | Cost snapshot DB operations |
| `L6_drivers/feedback_read_driver.py` | UC-MON-04 | Feedback read persistence |
| `L6_drivers/prediction_read_driver.py` | UC-025 | Prediction event read persistence |

**NON_UC_SUPPORT (19 scripts):**

| Group | Count | Examples |
|-------|-------|---------|
| Package init files | 3 | `__init__.py` across L5_engines, L5_schemas, L6_drivers |
| L5 schemas | 5 | `cost_anomaly_dtos.py`, `cost_anomaly_schemas.py`, `cost_snapshot_schemas.py`, `feedback_schemas.py`, `query_types.py` |
| Re-export engines | 2 | `config_engine.py` (hoc_spine re-export), `metrics_engine.py` (hoc_spine re-export) |
| Pure data structures | 2 | `cost_model.py` (coefficients dict), `costsim_models.py` (V2 dataclasses) |
| Computation utilities | 1 | `divergence_engine.py` (KL divergence metrics) |
| Audit/provenance | 2 | `provenance.py` (logging utility), `provenance_driver.py` (async logging) |
| Infrastructure drivers | 3 | `coordination_audit_driver.py` (C4 audit), `leader_driver.py` (advisory locks), `pattern_detection_driver.py` |
| Adapters | 1 | `adapters/__init__.py` |

### Incidents Domain (30 unlinked scripts)

**UC_LINKED (17 scripts):**

| Script | UC | Rationale |
|--------|-----|-----------|
| `L5_engines/anomaly_bridge.py` | UC-MON-07 | Bridges cost anomalies to incidents (severity mapping) |
| `L5_engines/export_engine.py` | UC-031 | Evidence/SOC2/executive bundle export |
| `L5_engines/hallucination_detector.py` | UC-030 | Hallucination detection (INV-002 blocking) |
| `L5_engines/incident_engine.py` | UC-MON-07 | Core incident creation from run failures (SDSR) |
| `L5_engines/incident_read_engine.py` | UC-031 | Incident investigation read operations |
| `L5_engines/incident_write_engine.py` | UC-031 | Incident lifecycle writes (acknowledge, resolve) |
| `L5_engines/incidents_facade.py` | UC-MON-07 | Incidents domain facade (list, metrics, patterns) |
| `L5_engines/recurrence_analysis.py` | UC-031 | Recurrence pattern analysis (group by category) |
| `L6_drivers/cost_guard_driver.py` | UC-MON-07 | Cost data access for incident detection |
| `L6_drivers/export_bundle_driver.py` | UC-031 | Export bundle persistence |
| `L6_drivers/incident_aggregator.py` | UC-MON-07 | Intelligent incident grouping under load |
| `L6_drivers/incident_read_driver.py` | UC-031 | Incident read persistence (list, count, queries) |
| `L6_drivers/incident_run_read_driver.py` | UC-031 | Run-scoped incident queries |
| `L6_drivers/incident_write_driver.py` | UC-031 | Incident write persistence (create, transitions) |
| `L6_drivers/incidents_facade_driver.py` | UC-MON-07 | Facade data access (snapshots, lists, metrics) |
| `L6_drivers/recurrence_analysis_driver.py` | UC-031 | Recurrence data access |
| `adapters/customer_incidents_adapter.py` | UC-MON-07 | Customer boundary adapter for incidents API |

**NON_UC_SUPPORT (13 scripts):**

| Group | Count | Examples |
|-------|-------|---------|
| Package init files | 4 | `__init__.py` across L5_engines, L5_schemas, L6_drivers, adapters |
| L5 schemas | 3 | `export_schemas.py` (ExportBundleProtocol), `incident_decision_port.py` (DI port), `severity_policy.py` (severity config) |
| Type definitions | 1 | `incidents_types.py` (UuidFn, ClockFn aliases) |
| Taxonomy | 1 | `semantic_failures.py` (failure taxonomy INT-*/SEM-*) |
| Infrastructure drivers | 3 | `incident_driver.py` (protocol wrapper), `lessons_driver.py` (lesson recording), `llm_failure_driver.py` (failure tracking) |
| Adapters | 1 | `founder_ops_adapter.py` (non-customer OpsIncident translation) |

## 3) Fixes Applied

No architecture violations found in Wave-2 scope. All newly-classified UC_LINKED L5 engines pass purity checks (0 runtime DB imports). No code changes were required.

## 4) Test Changes

| File | Before | After | Delta |
|------|--------|-------|-------|
| `test_uc018_uc032_expansion.py` | 163 tests | 219 tests | +56 |

New test class: `TestWave2ScriptCoverage`
- 17 L5 existence checks for UC_LINKED engines
- 16 L6 existence checks for UC_LINKED drivers
- 2 adapter existence checks for UC_LINKED adapters
- 17 L5 purity checks for UC_LINKED engines
- 1 activity NON_UC_SUPPORT stub existence check
- 1 analytics NON_UC_SUPPORT schemas existence check
- 1 incidents NON_UC_SUPPORT schemas existence check
- 1 total classification count validation

## 5) Gate Results

| # | Gate | Result |
|---|------|--------|
| 1 | Cross-domain validator | `status=CLEAN, count=0` |
| 2 | Layer boundaries | `CLEAN: No layer boundary violations found` |
| 3 | CI hygiene (--ci) | `All checks passed. 0 blocking violations` |
| 4 | Pairing gap detector | `wired=70, orphaned=0, direct=0` |
| 5 | UC-MON strict | `Total: 32 | PASS: 32 | WARN: 0 | FAIL: 0` |
| 6 | Governance tests | `219 passed in 2.21s` |

**All 6 gates PASS.**

## 6) Cumulative Coverage (Wave-1 + Wave-2)

| Wave | Domains | Scripts Classified | UC_LINKED | NON_UC_SUPPORT |
|------|---------|-------------------|-----------|----------------|
| Wave-1 | policies, logs | 130 | 33 | 97 |
| Wave-2 | analytics, incidents, activity | 80 | 35 | 45 |
| **Total** | **5 domains** | **210** | **68** | **142** |

## 7) Residual Gap List

### Remaining Wave-3+ domains (unlinked scripts not yet classified):

| Domain | Unlinked Count | Wave |
|--------|---------------|------|
| controls | 21 | Wave-3 |
| account | 28 | Wave-3 |
| hoc_spine | 170+ | Wave-4 |
| integrations | 58 | Wave-4 |
| agent | 4 | Wave-4 |
| api_keys | 8 | Wave-4 |
| apis | 2 | Wave-4 |
| ops | 3 | Wave-4 |
| overview | 5 | Wave-4 |

### Known pre-existing violations (not Wave-2 scope):
- `logs/L6_drivers/trace_store.py`: 7 L6_TRANSACTION_CONTROL violations (`.commit()` calls in L6 driver)
- These pre-date Wave-2 and are tracked separately

## 8) Documents Updated

| Document | Change |
|----------|--------|
| `HOC_USECASE_CODE_LINKAGE.md` | Added Script Coverage Wave-2 section with classification summary, UC_LINKED expansions across 3 domains, NON_UC_SUPPORT groups |
| `test_uc018_uc032_expansion.py` | Added `TestWave2ScriptCoverage` class (56 tests, total now 219) |
| `UC_SCRIPT_COVERAGE_WAVE_2_implemented.md` | Created (this file) |

## 9) Audit Reconciliation Note (2026-02-12)

- Independent Codex audit re-ran all deterministic gates and confirmed `219` governance tests passing.
- Canonical classification and residual gap artifacts were reconciled to avoid stale post-Wave-1 counts.
- Canonical residual snapshot after reconciliation:
- `UNLINKED` (all scripts): `321`
- core-6 residual (core-layer scope): `21` (`controls` only)
- Canonical reference:
- `app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_2_AUDIT_2026-02-12.md`
