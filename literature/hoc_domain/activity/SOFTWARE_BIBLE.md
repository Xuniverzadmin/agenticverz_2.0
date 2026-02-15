# Activity — Software Bible

**Domain:** activity  
**L2 Features:** 19  
**Scripts:** 13  
**Generator:** `scripts/ops/hoc_software_bible_generator.py`

---

## Reality Delta (2026-02-11)

- UC alignment: activity-related usecases are now tracked as `UC-006` and `UC-010` in canonical usecase docs and marked architecture `GREEN`.
- Determinism alignment: priority activity read surfaces include `as_of` contract enforcement in verifier suite (`uc_mon_deterministic_read_check.py`).
- Lifecycle closure: activity feedback lifecycle (ack/suppress/ttl/expiry/reopen/bulk) is now part of the canonical closure pack and reflected in linkage docs.
- Validation baseline: UC-MON strict validation now passes with `0 WARN` / `0 FAIL`.

## Reality Delta (2026-02-12, Wave-2 Script Coverage Audit)

- Wave-2 script coverage (`analytics + incidents + activity`) has been independently audited and reconciled.
- Activity core-scope classification is complete:
- `7` scripts marked `UC_LINKED`
- `13` scripts marked `NON_UC_SUPPORT`
- Core activity residual is `0` in Wave-2 target scope.
- Deterministic gates remain clean post-wave and governance suite now runs `219` passing tests in `test_uc018_uc032_expansion.py`.
- Canonical audit artifacts:
- `backend/app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_2_implemented.md`
- `backend/app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_2_AUDIT_2026-02-12.md`

## Script Registry

Each script's unique contribution and canonical function.

| Script | Layer | Canonical Function | Role | Decisions | Callers | Unique? |
|--------|-------|--------------------|------|-----------|---------|---------|
| activity_enums | L5 | `SeverityLevel.from_risk_level` | LEAF | 2 | L5:activity_facade, activity_facade | YES |
| activity_facade | L5 | `ActivityFacade.get_runs` | CANONICAL | 15 | ?:activity | L3:customer_activity_adapter | L5:__init__ | L5:customer_activity_adapter | L4:activity_handler | YES |
| attention_ranking | L5 | `AttentionRankingService.compute_attention_score` | LEAF | 0 | L5:activity_facade, activity_facade | YES |
| cost_analysis | L5 | `CostAnalysisService.__init__` | WRAPPER | 0 | L5:activity_facade, activity_facade | **OVERLAP** |
| cus_telemetry_engine | L5 | `CusTelemetryEngine.ingest` | CANONICAL | 5 | ?:cus_telemetry | ?:cus_telemetry_service | L4:activity_handler | ?:shim_guard | YES |
| pattern_detection | L5 | `PatternDetectionService.__init__` | WRAPPER | 0 | L5:activity_facade, activity_facade | **OVERLAP** |
| signal_feedback_engine | L5 | `SignalFeedbackService.suppress_signal` | LEAF | 0 | L5:activity_facade | L4:activity_handler, activity_facade | YES |
| signal_identity | L5 | `compute_signal_fingerprint_from_row` | LEAF | 0 | ?:activity | ?:__init__ | ?:activity_facade | L5:activity_facade | L4:activity_handler | ?:test_signal_feedback, activity_facade | YES |
| activity_read_driver | L6 | `ActivityReadDriver.count_runs` | LEAF | 0 | L5:activity_facade, activity_facade | YES |
| cus_telemetry_driver | L6 | `CusTelemetryDriver.list_usage` | LEAF | 0 | L5:cus_telemetry_engine, cus_telemetry_engine | YES |
| orphan_recovery_driver | L6 | `recover_orphaned_runs` | CANONICAL | 3 | ?:main | ?:check_priority5_intent | YES |
| run_signal_driver | L6 | `RunSignalDriver.get_risk_level` | LEAF | 1 | ?:llm_threshold_service | L6:threshold_driver | YES |
| run_metrics_driver | L6 | `RunMetricsDriver.mark_policy_violation` | LEAF | 0 | L4:run_governance_handler | L4:policies_handler | YES |

## Overlapping Scripts (same purpose, same layer)

These scripts may serve duplicate purposes within the domain.

- `cost_analysis` — canonical: `CostAnalysisService.__init__` (WRAPPER)
- `pattern_detection` — canonical: `PatternDetectionService.__init__` (WRAPPER)

## L2 Feature Chains

| Status | Count |
|--------|-------|
| COMPLETE (L2→L4→L5→L6) | 19 |
| GAP (L2→L5 direct) | 0 |

### Wired Features (L2→L4→L5→L6)

#### GET /attention-queue
```
L2:activity.get_attention_queue → L4:OperationContext | get_operation_registry → L6:activity_read_driver.ActivityReadDriver.count_runs
```

#### GET /completed
```
L2:activity.list_completed_runs → L4:OperationContext | get_operation_registry → L6:activity_read_driver.ActivityReadDriver.count_runs
```

#### GET /cost-analysis
```
L2:activity.get_cost_analysis → L4:OperationContext | get_operation_registry → L6:activity_read_driver.ActivityReadDriver.count_runs
```

#### GET /live
```
L2:activity.list_live_runs → L4:OperationContext | get_operation_registry → L6:activity_read_driver.ActivityReadDriver.count_runs
```

#### GET /metrics
```
L2:activity.get_activity_metrics → L4:OperationContext | get_operation_registry → L6:activity_read_driver.ActivityReadDriver.count_runs
```

#### GET /patterns
```
L2:activity.get_patterns → L4:OperationContext | get_operation_registry → L6:activity_read_driver.ActivityReadDriver.count_runs
```

#### GET /risk-signals
```
L2:activity.get_risk_signals → L4:OperationContext | get_operation_registry → L6:activity_read_driver.ActivityReadDriver.count_runs
```

#### GET /runs
```
L2:activity.list_runs → L4:OperationContext | get_operation_registry → L6:activity_read_driver.ActivityReadDriver.count_runs
```

#### GET /runs/by-dimension
```
L2:activity.get_runs_by_dimension → L4:OperationContext | get_operation_registry → L6:activity_read_driver.ActivityReadDriver.count_runs
```

#### GET /runs/completed/by-dimension
```
L2:activity.get_completed_runs_by_dimension → L4:OperationContext | get_operation_registry → L6:activity_read_driver.ActivityReadDriver.count_runs
```

#### GET /runs/live/by-dimension
```
L2:activity.get_live_runs_by_dimension → L4:OperationContext | get_operation_registry → L6:activity_read_driver.ActivityReadDriver.count_runs
```

#### GET /runs/{run_id}
```
L2:activity.get_run_detail → L4:OperationContext | get_operation_registry → L6:activity_read_driver.ActivityReadDriver.count_runs
```

#### GET /runs/{run_id}/evidence
```
L2:activity.get_run_evidence → L4:OperationContext | get_operation_registry → L6:activity_read_driver.ActivityReadDriver.count_runs
```

#### GET /runs/{run_id}/proof
```
L2:activity.get_run_proof → L4:OperationContext | get_operation_registry → L6:activity_read_driver.ActivityReadDriver.count_runs
```

#### GET /signals
```
L2:activity.list_signals → L4:OperationContext | get_operation_registry → L6:activity_read_driver.ActivityReadDriver.count_runs
```

#### GET /summary/by-status
```
L2:activity.get_summary_by_status → L4:OperationContext | get_operation_registry → L6:activity_read_driver.ActivityReadDriver.count_runs
```

#### GET /threshold-signals
```
L2:activity.get_threshold_signals → L4:OperationContext | get_operation_registry → L6:activity_read_driver.ActivityReadDriver.count_runs
```

#### POST /signals/{signal_fingerprint}/ack
```
L2:activity.acknowledge_signal → L4:OperationContext | get_operation_registry → L6:activity_read_driver.ActivityReadDriver.count_runs
```

#### POST /signals/{signal_fingerprint}/suppress
```
L2:activity.suppress_signal → L4:OperationContext | get_operation_registry → L6:activity_read_driver.ActivityReadDriver.count_runs
```

## Canonical Algorithm Inventory

| Function | File | Role | Decisions | Stmts | Persistence | Delegates To |
|----------|------|------|-----------|-------|-------------|--------------|
| `ActivityFacade._get_runs_with_policy_context` | activity_facade | SUPERSET | 2 | 13 | no | activity_facade:ActivityFacade._get_driver | activity_read_d |
| `ActivityFacade.get_metrics` | activity_facade | SUPERSET | 2 | 8 | no | activity_facade:ActivityFacade._get_driver | activity_read_d |
| `ActivityFacade.get_runs` | activity_facade | CANONICAL | 15 | 26 | no | activity_facade:ActivityFacade._get_driver | activity_read_d |
| `ActivityFacade.get_signals` | activity_facade | SUPERSET | 2 | 11 | no | activity_facade:ActivityFacade._compute_severity | activity_ |
| `ActivityFacade.get_threshold_signals` | activity_facade | SUPERSET | 2 | 12 | no | activity_facade:ActivityFacade._get_driver | activity_read_d |
| `recover_orphaned_runs` | orphan_recovery_driver | CANONICAL | 3 | 6 | no | orphan_recovery_driver:detect_orphaned_runs | orphan_recovery_driver:mark_ |

## Wrapper Inventory

_30 thin delegation functions._

- `activity_facade.ActivityFacade.__init__` → ?
- `activity_facade.ActivityFacade._compute_signal_summary` → ?
- `activity_facade.ActivityFacade._get_attention_service` → ?
- `activity_facade.ActivityFacade._get_cost_service` → ?
- `activity_facade.ActivityFacade._get_driver` → activity_read_driver:get_activity_read_driver
- `activity_facade.ActivityFacade._get_feedback_service` → ?
- `activity_facade.ActivityFacade._get_pattern_service` → ?
- `activity_facade.ActivityFacade.acknowledge_signal` → activity_facade:ActivityFacade._get_feedback_service
- `activity_facade.ActivityFacade.get_completed_runs` → activity_facade:ActivityFacade._get_runs_with_policy_context
- `activity_facade.ActivityFacade.get_live_runs` → activity_facade:ActivityFacade._get_runs_with_policy_context
- `activity_facade.ActivityFacade.get_risk_signals` → activity_facade:ActivityFacade.get_metrics
- `activity_facade.ActivityFacade.get_run_evidence` → ?
- `activity_facade.ActivityFacade.suppress_signal` → activity_facade:ActivityFacade._get_feedback_service
- `activity_read_driver.ActivityReadDriver.__init__` → ?
- `attention_ranking.AttentionRankingService.__init__` → ?
- `attention_ranking.AttentionRankingService.get_attention_queue` → ?
- `cost_analysis.CostAnalysisService.__init__` → ?
- `cost_analysis.CostAnalysisService.analyze_costs` → ?
- `cost_analysis.CostAnalysisService.get_cost_breakdown` → ?
- `pattern_detection.PatternDetectionService.__init__` → ?
- `pattern_detection.PatternDetectionService.detect_patterns` → ?
- `pattern_detection.PatternDetectionService.get_pattern_detail` → ?
- `run_signal_driver.RunSignalDriver.__init__` → ?
- `signal_feedback_engine.SignalFeedbackService.__init__` → ?
- `signal_feedback_engine.SignalFeedbackService.acknowledge_signal` → ?
- `signal_feedback_engine.SignalFeedbackService.get_bulk_signal_feedback` → ?
- `signal_feedback_engine.SignalFeedbackService.get_signal_feedback_status` → ?
- `signal_identity.compute_signal_fingerprint` → signal_identity:compute_signal_fingerprint_from_row
- `activity_read_driver.get_activity_read_driver` → ?
- `cus_telemetry_service.get_cus_telemetry_service` → ?

---

## PIN-504 Amendments (2026-01-31)

| Script | Change | Reference |
|--------|--------|-----------|
| `L6_drivers/__init__.py` | Removed all controls domain re-exports (`ThresholdDriver`, `ThresholdDriverSync`, signal functions). Only exports `LimitSnapshot` from `hoc.cus.hoc_spine.schemas.threshold_types`. | PIN-504 Phases 1, 3 |

## PIN-507 Law 5 Remediation (2026-02-01)

| Script | Change | Reference |
|--------|--------|-----------|
| L4 `activity_handler.py` | `ActivityQueryHandler`: Replaced `getattr()` dispatch with explicit map (16 methods). `ActivityTelemetryHandler`: Replaced `getattr()` dispatch with explicit map (4 methods). Zero reflection in dispatch paths. | PIN-507 Law 5 |

## PIN-508 Stub Classification (2026-02-01)

| Script | Change | Reference |
|--------|--------|-----------|
| `cus_telemetry_engine` | STUB_ENGINE marker added (Phase 5). Legacy bridge to app.services implementation with stub dataclasses (`IngestResult`, `BatchIngestResult`) returning `NotImplementedError`. Scheduled for ideal contractor analysis. | PIN-508 Phase 5 |

## PIN-509 Tooling Hardening (2026-02-01)

- CI checks 16–18 added to `scripts/ci/check_init_hygiene.py`:
  - Check 16: Frozen import ban (no imports from `_frozen/` paths)
  - Check 17: L5 Session symbol import ban (type erasure enforcement)
  - Check 18: Protocol surface baseline (capability creep prevention, max 12 methods)
- New scripts: `collapse_tombstones.py`, `new_l5_engine.py`, `new_l6_driver.py`
- `app/services/__init__.py` now emits DeprecationWarning
- Reference: `docs/memory-pins/PIN-509-tooling-hardening.md`

## PIN-513 Phase C — Activity Domain Changes (2026-02-01)

- orphan_recovery_driver.py (L6): Now canonical source for `recover_orphaned_runs`. 2 callers rewired from `app.services.orphan_recovery` to HOC path (app/main.py, hoc/api/int/agent/main.py).

## PIN-513 Phase 9 — Batch 1A Wiring (2026-02-01)

**Root cause:** L6 driver violated "no implicit execution" — created own sessions, scheduled itself.

- Created `hoc_spine/orchestrator/handlers/orphan_recovery_handler.py` (L4 handler)
- Stripped `recover_orphaned_runs()` and `get_crash_recovery_summary()` from L6 driver (moved to L4)
- L6 now contains only pure data primitives: `detect_orphaned_runs(session, threshold)`, `mark_run_as_crashed(session, run, reason)`
- Rewired `main.py:584` from direct L6 import to `OrphanRecoveryHandler().execute()`
- L4 owns session lifecycle, commit boundary, and scheduling authority
- All 4 CSV entries reclassified: 3 WIRED, 1 REMOVED

## PIN-519 System Run Introspection (2026-02-03)

**Activity facade updated to delegate cross-domain queries to L4 coordinators.**

| Method | Change | Delegates To |
|--------|--------|--------------|
| `get_run_evidence()` | Replaced empty shell with coordinator delegation | `RunEvidenceCoordinator` (L4) |
| `get_run_proof()` | Replaced UNKNOWN integrity with coordinator delegation | `RunProofCoordinator` (L4) |
| `get_signals()` | Now includes signal feedback via coordinator | `SignalFeedbackCoordinator` (L4) |

**New private method:**

| Method | Purpose |
|--------|---------|
| `_get_signal_feedback(session, tenant_id, fingerprint)` | Fetch signal feedback from L4 coordinator |

**Red-line compliance:**

- Activity L5 does not import other domains ✅
- Activity L5 does not write data ✅
- Activity L5 does not evaluate policy ✅
- Activity L5 does not compute integrity (delegated to coordinator) ✅
- Activity L5 does not trigger execution ✅

**L4 coordinators consumed:**

| Coordinator | Purpose | Bridges Used |
|-------------|---------|--------------|
| `RunEvidenceCoordinator` | Cross-domain evidence aggregation | incidents, policies, controls |
| `RunProofCoordinator` | Integrity verification via traces | logs (traces_store) |
| `SignalFeedbackCoordinator` | Signal feedback queries | logs (audit_ledger_read) |

Reference: `docs/memory-pins/PIN-519-system-run-introspection.md`
