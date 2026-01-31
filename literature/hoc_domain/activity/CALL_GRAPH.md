# Activity — Call Graph

**Domain:** activity  
**Total functions:** 63  
**Generator:** `scripts/ops/hoc_call_chain_tracer.py`

---

## Role Summary

| Role | Count | Description |
|------|-------|-------------|
| CANONICAL | 2 | Owns the algorithm — most decisions, primary logic |
| SUPERSET | 4 | Calls other functions + adds its own decisions |
| WRAPPER | 30 | Thin delegation — ≤3 stmts, no branching |
| LEAF | 21 | Terminal — calls no other domain functions |
| ENTRY | 5 | Entry point — no domain-internal callers |
| INTERNAL | 1 | Called only by other domain functions |

## Canonical Algorithm Owners

### `activity_facade.ActivityFacade.get_runs`
- **Layer:** L5
- **Decisions:** 15
- **Statements:** 26
- **Delegation depth:** 2
- **Persistence:** no
- **Chain:** activity_facade.ActivityFacade.get_runs → activity_facade.ActivityFacade._get_driver → activity_read_driver.ActivityReadDriver.count_runs → activity_read_driver.ActivityReadDriver.fetch_runs
- **Calls:** activity_facade:ActivityFacade._get_driver, activity_read_driver:ActivityReadDriver.count_runs, activity_read_driver:ActivityReadDriver.fetch_runs

### `orphan_recovery.recover_orphaned_runs`
- **Layer:** L6
- **Decisions:** 3
- **Statements:** 6
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** orphan_recovery.recover_orphaned_runs → orphan_recovery.detect_orphaned_runs → orphan_recovery.mark_run_as_crashed
- **Calls:** orphan_recovery:detect_orphaned_runs, orphan_recovery:mark_run_as_crashed

## Supersets (orchestrating functions)

### `activity_facade.ActivityFacade._get_runs_with_policy_context`
- **Decisions:** 2, **Statements:** 13
- **Subsumes:** activity_facade:ActivityFacade._get_driver, activity_read_driver:ActivityReadDriver.count_runs, activity_read_driver:ActivityReadDriver.fetch_runs_with_policy_context

### `activity_facade.ActivityFacade.get_metrics`
- **Decisions:** 2, **Statements:** 8
- **Subsumes:** activity_facade:ActivityFacade._get_driver, activity_read_driver:ActivityReadDriver.fetch_metrics

### `activity_facade.ActivityFacade.get_signals`
- **Decisions:** 2, **Statements:** 11
- **Subsumes:** activity_facade:ActivityFacade._compute_severity, activity_facade:ActivityFacade._compute_signal_summary, activity_facade:ActivityFacade._compute_signal_type, activity_facade:ActivityFacade._get_driver, activity_read_driver:ActivityReadDriver.count_runs, activity_read_driver:ActivityReadDriver.fetch_at_risk_runs, signal_identity:compute_signal_fingerprint_from_row

### `activity_facade.ActivityFacade.get_threshold_signals`
- **Decisions:** 2, **Statements:** 12
- **Subsumes:** activity_facade:ActivityFacade._get_driver, activity_read_driver:ActivityReadDriver.count_runs, activity_read_driver:ActivityReadDriver.fetch_threshold_signals

## Wrappers (thin delegation)

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
- `activity_read_driver.get_activity_read_driver` → ?
- `attention_ranking_engine.AttentionRankingService.__init__` → ?
- `attention_ranking_engine.AttentionRankingService.get_attention_queue` → ?
- `cost_analysis_engine.CostAnalysisService.__init__` → ?
- `cost_analysis_engine.CostAnalysisService.analyze_costs` → ?
- `cost_analysis_engine.CostAnalysisService.get_cost_breakdown` → ?
- `cus_telemetry_service.get_cus_telemetry_service` → ?
- `pattern_detection_engine.PatternDetectionService.__init__` → ?
- `pattern_detection_engine.PatternDetectionService.detect_patterns` → ?
- `pattern_detection_engine.PatternDetectionService.get_pattern_detail` → ?
- `run_signal_service.RunSignalService.__init__` → ?
- `signal_feedback_engine.SignalFeedbackService.__init__` → ?
- `signal_feedback_engine.SignalFeedbackService.acknowledge_signal` → ?
- `signal_feedback_engine.SignalFeedbackService.get_bulk_signal_feedback` → ?
- `signal_feedback_engine.SignalFeedbackService.get_signal_feedback_status` → ?
- `signal_identity.compute_signal_fingerprint` → signal_identity:compute_signal_fingerprint_from_row

## Full Call Graph

```
[LEAF] activity_enums.SeverityLevel.from_risk_level
[LEAF] activity_enums.SeverityLevel.from_score
[WRAPPER] activity_facade.ActivityFacade.__init__
[INTERNAL] activity_facade.ActivityFacade._compute_severity → activity_enums:SeverityLevel.from_risk_level
[WRAPPER] activity_facade.ActivityFacade._compute_signal_summary
[LEAF] activity_facade.ActivityFacade._compute_signal_type
[WRAPPER] activity_facade.ActivityFacade._get_attention_service
[WRAPPER] activity_facade.ActivityFacade._get_cost_service
[WRAPPER] activity_facade.ActivityFacade._get_driver → activity_read_driver:get_activity_read_driver
[WRAPPER] activity_facade.ActivityFacade._get_feedback_service
[WRAPPER] activity_facade.ActivityFacade._get_pattern_service
[SUPERSET] activity_facade.ActivityFacade._get_runs_with_policy_context → activity_facade:ActivityFacade._get_driver, activity_read_driver:ActivityReadDriver.count_runs, activity_read_driver:ActivityReadDriver.fetch_runs_with_policy_context
[WRAPPER] activity_facade.ActivityFacade.acknowledge_signal → activity_facade:ActivityFacade._get_feedback_service, signal_feedback_engine:SignalFeedbackService.acknowledge_signal
[ENTRY] activity_facade.ActivityFacade.get_attention_queue → activity_facade:ActivityFacade._get_attention_service, attention_ranking_engine:AttentionRankingService.get_attention_queue
[WRAPPER] activity_facade.ActivityFacade.get_completed_runs → activity_facade:ActivityFacade._get_runs_with_policy_context
[ENTRY] activity_facade.ActivityFacade.get_cost_analysis → activity_facade:ActivityFacade._get_cost_service, cost_analysis_engine:CostAnalysisService.analyze_costs
[WRAPPER] activity_facade.ActivityFacade.get_live_runs → activity_facade:ActivityFacade._get_runs_with_policy_context
[SUPERSET] activity_facade.ActivityFacade.get_metrics → activity_facade:ActivityFacade._get_driver, activity_read_driver:ActivityReadDriver.fetch_metrics
[ENTRY] activity_facade.ActivityFacade.get_patterns → activity_facade:ActivityFacade._get_pattern_service, pattern_detection_engine:PatternDetectionService.detect_patterns
[WRAPPER] activity_facade.ActivityFacade.get_risk_signals → activity_facade:ActivityFacade.get_metrics
[ENTRY] activity_facade.ActivityFacade.get_run_detail → activity_facade:ActivityFacade._get_driver, activity_read_driver:ActivityReadDriver.fetch_run_detail
[WRAPPER] activity_facade.ActivityFacade.get_run_evidence
[LEAF] activity_facade.ActivityFacade.get_run_proof
[CANONICAL] activity_facade.ActivityFacade.get_runs → activity_facade:ActivityFacade._get_driver, activity_read_driver:ActivityReadDriver.count_runs, activity_read_driver:ActivityReadDriver.fetch_runs
[SUPERSET] activity_facade.ActivityFacade.get_signals → activity_facade:ActivityFacade._compute_severity, activity_facade:ActivityFacade._compute_signal_summary, activity_facade:ActivityFacade._compute_signal_type, activity_facade:ActivityFacade._get_driver, activity_read_driver:ActivityReadDriver.count_runs, ...+2
[ENTRY] activity_facade.ActivityFacade.get_status_summary → activity_facade:ActivityFacade._get_driver, activity_read_driver:ActivityReadDriver.fetch_status_summary
[SUPERSET] activity_facade.ActivityFacade.get_threshold_signals → activity_facade:ActivityFacade._get_driver, activity_read_driver:ActivityReadDriver.count_runs, activity_read_driver:ActivityReadDriver.fetch_threshold_signals
[WRAPPER] activity_facade.ActivityFacade.suppress_signal → activity_facade:ActivityFacade._get_feedback_service, signal_feedback_engine:SignalFeedbackService.suppress_signal
[LEAF] activity_facade.get_activity_facade
[WRAPPER] activity_read_driver.ActivityReadDriver.__init__
[LEAF] activity_read_driver.ActivityReadDriver.count_runs
[LEAF] activity_read_driver.ActivityReadDriver.fetch_at_risk_runs
[LEAF] activity_read_driver.ActivityReadDriver.fetch_metrics
[LEAF] activity_read_driver.ActivityReadDriver.fetch_run_detail
[LEAF] activity_read_driver.ActivityReadDriver.fetch_runs
[LEAF] activity_read_driver.ActivityReadDriver.fetch_runs_with_policy_context
[LEAF] activity_read_driver.ActivityReadDriver.fetch_status_summary
[LEAF] activity_read_driver.ActivityReadDriver.fetch_threshold_signals
[WRAPPER] activity_read_driver.get_activity_read_driver
[WRAPPER] attention_ranking_engine.AttentionRankingService.__init__
[LEAF] attention_ranking_engine.AttentionRankingService.compute_attention_score
[WRAPPER] attention_ranking_engine.AttentionRankingService.get_attention_queue
[WRAPPER] cost_analysis_engine.CostAnalysisService.__init__
[WRAPPER] cost_analysis_engine.CostAnalysisService.analyze_costs
[WRAPPER] cost_analysis_engine.CostAnalysisService.get_cost_breakdown
[WRAPPER] cus_telemetry_service.get_cus_telemetry_service
[LEAF] orphan_recovery.detect_orphaned_runs
[LEAF] orphan_recovery.get_crash_recovery_summary
[LEAF] orphan_recovery.mark_run_as_crashed
[CANONICAL] orphan_recovery.recover_orphaned_runs → orphan_recovery:detect_orphaned_runs, orphan_recovery:mark_run_as_crashed
[WRAPPER] pattern_detection_engine.PatternDetectionService.__init__
[WRAPPER] pattern_detection_engine.PatternDetectionService.detect_patterns
[WRAPPER] pattern_detection_engine.PatternDetectionService.get_pattern_detail
[WRAPPER] run_signal_service.RunSignalService.__init__
[LEAF] run_signal_service.RunSignalService.get_risk_level
[LEAF] run_signal_service.RunSignalService.update_risk_level
[WRAPPER] signal_feedback_engine.SignalFeedbackService.__init__
[WRAPPER] signal_feedback_engine.SignalFeedbackService.acknowledge_signal
[WRAPPER] signal_feedback_engine.SignalFeedbackService.get_bulk_signal_feedback
[WRAPPER] signal_feedback_engine.SignalFeedbackService.get_signal_feedback_status
[LEAF] signal_feedback_engine.SignalFeedbackService.suppress_signal
[WRAPPER] signal_identity.compute_signal_fingerprint → signal_identity:compute_signal_fingerprint_from_row
[LEAF] signal_identity.compute_signal_fingerprint_from_row
```
