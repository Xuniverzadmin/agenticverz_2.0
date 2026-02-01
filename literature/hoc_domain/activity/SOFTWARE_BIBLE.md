# Activity — Software Bible

**Domain:** activity  
**L2 Features:** 19  
**Scripts:** 11  
**Generator:** `scripts/ops/hoc_software_bible_generator.py`

---

## Script Registry

Each script's unique contribution and canonical function.

| Script | Layer | Canonical Function | Role | Decisions | Callers | Unique? |
|--------|-------|--------------------|------|-----------|---------|---------|
| activity_enums | L5 | `SeverityLevel.from_risk_level` | LEAF | 2 | L5:activity_facade, activity_facade | YES |
| activity_facade | L5 | `ActivityFacade.get_runs` | CANONICAL | 15 | ?:activity | L3:customer_activity_adapter | L5:__init__ | L5:customer_activity_adapter | L4:activity_handler | YES |
| attention_ranking_engine | L5 | `AttentionRankingService.compute_attention_score` | LEAF | 0 | L5:activity_facade, activity_facade | YES |
| cost_analysis_engine | L5 | `CostAnalysisService.__init__` | WRAPPER | 0 | L5:activity_facade, activity_facade | **OVERLAP** |
| cus_telemetry_service | L5 | `get_cus_telemetry_service` | WRAPPER | 0 | ?:cus_telemetry | ?:cus_telemetry_service | L4:activity_handler | ?:shim_guard | YES |
| pattern_detection_engine | L5 | `PatternDetectionService.__init__` | WRAPPER | 0 | L5:activity_facade, activity_facade | **OVERLAP** |
| signal_feedback_engine | L5 | `SignalFeedbackService.suppress_signal` | LEAF | 0 | L5:activity_facade | L4:activity_handler, activity_facade | YES |
| signal_identity | L5 | `compute_signal_fingerprint_from_row` | LEAF | 0 | ?:activity | ?:__init__ | ?:activity_facade | L5:activity_facade | L4:activity_handler | ?:test_signal_feedback, activity_facade | YES |
| activity_read_driver | L6 | `ActivityReadDriver.count_runs` | LEAF | 0 | L5:activity_facade, activity_facade | YES |
| orphan_recovery | L6 | `recover_orphaned_runs` | CANONICAL | 3 | ?:main | ?:check_priority5_intent | YES |
| run_signal_service | L6 | `RunSignalService.get_risk_level` | LEAF | 1 | ?:llm_threshold_service | L6:threshold_driver | YES |

## Overlapping Scripts (same purpose, same layer)

These scripts may serve duplicate purposes within the domain.

- `cost_analysis_engine` — canonical: `CostAnalysisService.__init__` (WRAPPER)
- `pattern_detection_engine` — canonical: `PatternDetectionService.__init__` (WRAPPER)

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
| `recover_orphaned_runs` | orphan_recovery | CANONICAL | 3 | 6 | no | orphan_recovery:detect_orphaned_runs | orphan_recovery:mark_ |

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
- `attention_ranking_engine.AttentionRankingService.__init__` → ?
- `attention_ranking_engine.AttentionRankingService.get_attention_queue` → ?
- `cost_analysis_engine.CostAnalysisService.__init__` → ?
- `cost_analysis_engine.CostAnalysisService.analyze_costs` → ?
- `cost_analysis_engine.CostAnalysisService.get_cost_breakdown` → ?
- `pattern_detection_engine.PatternDetectionService.__init__` → ?
- `pattern_detection_engine.PatternDetectionService.detect_patterns` → ?
- `pattern_detection_engine.PatternDetectionService.get_pattern_detail` → ?
- `run_signal_service.RunSignalService.__init__` → ?
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
| `L6_drivers/__init__.py` | Removed all controls domain re-exports (`ThresholdDriver`, `ThresholdDriverSync`, signal functions). Only exports `LimitSnapshot` from `hoc_spine.schemas.threshold_types`. | PIN-504 Phases 1, 3 |

## PIN-507 Law 5 Remediation (2026-02-01)

| Script | Change | Reference |
|--------|--------|-----------|
| L4 `activity_handler.py` | `ActivityQueryHandler`: Replaced `getattr()` dispatch with explicit map (16 methods). `ActivityTelemetryHandler`: Replaced `getattr()` dispatch with explicit map (4 methods). Zero reflection in dispatch paths. | PIN-507 Law 5 |
