# Activity — Domain Capability

**Domain:** activity  
**Total functions:** 63  
**Generator:** `scripts/ops/hoc_capability_doc_generator.py`

---

## Reality Delta (2026-02-16, L2.1 Facade Activation Wiring)

- Public facade activation path for activity is now explicitly wired at L2.1:
- backend/app/hoc/api/facades/cus/activity/activity_fac.py
- L2 public boundary module for domain-scoped facade entry remains:
- backend/app/hoc/api/cus/activity/runs_facade.py and backend/app/hoc/api/cus/activity/activity.py
- Runtime chain is fixed as:
- app.py -> app.hoc.api.facades.cus -> domain facade bundle -> activity routers -> L4 registry.execute(...)
- Current status: activity routes are live (not scaffold-only) and preserve existing behavior while package-form facade naming is standardized.

## 1. Domain Purpose

Tracks and surfaces user and system activity streams. Provides audit trail and activity feeds for the customer console.

## 2. Customer-Facing Operations

| Function | File | L4 Wired | Entry Point | Side Effects |
|----------|------|----------|-------------|--------------|
| `ActivityFacade.acknowledge_signal` | activity_facade | Yes | L4:activity_handler | pure |
| `ActivityFacade.get_attention_queue` | activity_facade | Yes | L4:activity_handler | pure |
| `ActivityFacade.get_completed_runs` | activity_facade | Yes | L4:activity_handler | pure |
| `ActivityFacade.get_cost_analysis` | activity_facade | Yes | L4:activity_handler | pure |
| `ActivityFacade.get_live_runs` | activity_facade | Yes | L4:activity_handler | pure |
| `ActivityFacade.get_metrics` | activity_facade | Yes | L4:activity_handler | pure |
| `ActivityFacade.get_patterns` | activity_facade | Yes | L4:activity_handler | pure |
| `ActivityFacade.get_risk_signals` | activity_facade | Yes | L4:activity_handler | pure |
| `ActivityFacade.get_run_detail` | activity_facade | Yes | L4:activity_handler | pure |
| `ActivityFacade.get_run_evidence` | activity_facade | Yes | L4:activity_handler | pure |
| `ActivityFacade.get_run_proof` | activity_facade | Yes | L4:activity_handler | pure |
| `ActivityFacade.get_runs` | activity_facade | Yes | L4:activity_handler | pure |
| `ActivityFacade.get_signals` | activity_facade | Yes | L4:activity_handler | pure |
| `ActivityFacade.get_status_summary` | activity_facade | Yes | L4:activity_handler | pure |
| `ActivityFacade.get_threshold_signals` | activity_facade | Yes | L4:activity_handler | pure |
| `ActivityFacade.suppress_signal` | activity_facade | Yes | L4:activity_handler | pure |
| `SignalFeedbackService.acknowledge_signal` | signal_feedback_engine | Yes | L4:activity_handler | pure |
| `SignalFeedbackService.get_bulk_signal_feedback` | signal_feedback_engine | Yes | L4:activity_handler | pure |
| `SignalFeedbackService.get_signal_feedback_status` | signal_feedback_engine | Yes | L4:activity_handler | pure |
| `SignalFeedbackService.suppress_signal` | signal_feedback_engine | Yes | L4:activity_handler | pure |
| `compute_signal_fingerprint` | signal_identity | Yes | L4:activity_handler | pure |
| `compute_signal_fingerprint_from_row` | signal_identity | Yes | L4:activity_handler | pure |
| `get_activity_facade` | activity_facade | Yes | L4:activity_handler | pure |
| `get_cus_telemetry_service` | cus_telemetry_service | Yes | L4:activity_handler | pure |

## 3. Internal Functions

### Helpers

_18 internal helper functions._

- **activity_enums:** `SeverityLevel.from_risk_level`, `SeverityLevel.from_score`
- **activity_facade:** `ActivityFacade.__init__`, `ActivityFacade._compute_severity`, `ActivityFacade._compute_signal_summary`, `ActivityFacade._compute_signal_type`, `ActivityFacade._get_attention_service`, `ActivityFacade._get_cost_service`, `ActivityFacade._get_driver`, `ActivityFacade._get_feedback_service`, `ActivityFacade._get_pattern_service`, `ActivityFacade._get_runs_with_policy_context`
- **activity_read_driver:** `ActivityReadDriver.__init__`
- **attention_ranking_engine:** `AttentionRankingService.__init__`
- **cost_analysis_engine:** `CostAnalysisService.__init__`
- **pattern_detection_engine:** `PatternDetectionService.__init__`
- **run_signal_service:** `RunSignalService.__init__`
- **signal_feedback_engine:** `SignalFeedbackService.__init__`

### Persistence

| Function | File | Side Effects |
|----------|------|--------------|
| `ActivityReadDriver.count_runs` | activity_read_driver | db_write |
| `ActivityReadDriver.fetch_at_risk_runs` | activity_read_driver | db_write |
| `ActivityReadDriver.fetch_metrics` | activity_read_driver | db_write |
| `ActivityReadDriver.fetch_run_detail` | activity_read_driver | db_write |
| `ActivityReadDriver.fetch_runs` | activity_read_driver | db_write |
| `ActivityReadDriver.fetch_runs_with_policy_context` | activity_read_driver | db_write |
| `ActivityReadDriver.fetch_status_summary` | activity_read_driver | db_write |
| `ActivityReadDriver.fetch_threshold_signals` | activity_read_driver | db_write |
| `RunSignalService.get_risk_level` | run_signal_service | db_write |
| `RunSignalService.update_risk_level` | run_signal_service | db_write |
| `detect_orphaned_runs` | orphan_recovery | db_write |
| `get_activity_read_driver` | activity_read_driver | pure |
| `get_crash_recovery_summary` | orphan_recovery | db_write |
| `mark_run_as_crashed` | orphan_recovery | db_write |
| `recover_orphaned_runs` | orphan_recovery | pure |

### Unclassified (needs review)

_6 functions need manual classification._

- `AttentionRankingService.compute_attention_score` (attention_ranking_engine)
- `AttentionRankingService.get_attention_queue` (attention_ranking_engine)
- `CostAnalysisService.analyze_costs` (cost_analysis_engine)
- `CostAnalysisService.get_cost_breakdown` (cost_analysis_engine)
- `PatternDetectionService.detect_patterns` (pattern_detection_engine)
- `PatternDetectionService.get_pattern_detail` (pattern_detection_engine)

## 4. Explicit Non-Features

_No explicit non-feature declarations found in ACTIVITY_DOMAIN_LOCK_FINAL.md._
