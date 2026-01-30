# hoc_cus_policies_L5_engines_learning_proof_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/learning_proof_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Learning proof generation (graduation gates, regret tracking)

## Intent

**Role:** Learning proof generation (graduation gates, regret tracking)
**Reference:** PIN-470, HOC_LAYER_TOPOLOGY_V1.md, INTEGRATIONS_PHASE2.5_IMPLEMENTATION_PLAN.md
**Callers:** learning workers, policy engines

## Purpose

M25 Learning Proof System

---

## Classes

### `PreventionOutcome(str, Enum)`
- **Docstring:** Outcome of a prevention attempt.

### `PreventionRecord`
- **Docstring:** Evidence that a policy prevented a recurrence.
- **Methods:** create_prevention, to_console_timeline
- **Class Variables:** record_id: str, policy_id: str, pattern_id: str, original_incident_id: str, blocked_incident_id: str, tenant_id: str, outcome: PreventionOutcome, created_at: datetime, signature_match_confidence: float, time_since_policy: timedelta, calls_evaluated: int

### `PreventionTracker`
- **Docstring:** Tracks prevention effectiveness across policies.
- **Methods:** record_prevention, record_failure, prevention_rate, has_proven_prevention, get_top_preventing_patterns
- **Class Variables:** policies_with_prevention: set[str], prevention_by_pattern: dict[str, list[PreventionRecord]], total_preventions: int, total_failures: int

### `RegretType(str, Enum)`
- **Docstring:** Types of policy regret.

### `RegretEvent`
- **Docstring:** A single regret event - when a policy caused harm.
- **Class Variables:** regret_id: str, policy_id: str, tenant_id: str, regret_type: RegretType, description: str, severity: int, created_at: datetime, affected_calls: int, affected_users: int, impact_duration: timedelta, was_auto_rolled_back: bool, manual_override_by: Optional[str]

### `PolicyRegretTracker`
- **Docstring:** Tracks regret for individual policies.
- **Methods:** add_regret, _trigger_demotion, decay_regret, is_demoted, to_rollback_timeline
- **Class Variables:** policy_id: str, regret_events: list[RegretEvent], regret_score: float, demoted_at: Optional[datetime], demoted_reason: Optional[str], auto_demote_score: float, auto_demote_count: int, decay_rate: float

### `GlobalRegretTracker`
- **Docstring:** System-wide regret tracking.
- **Methods:** get_or_create_tracker, record_regret, has_proven_rollback, system_regret_rate
- **Class Variables:** policy_trackers: dict[str, PolicyRegretTracker], total_regret_events: int, total_auto_demotions: int

### `PatternCalibration`
- **Docstring:** Per-pattern confidence calibration based on actual outcomes.
- **Methods:** record_outcome, _recalibrate, accuracy, is_calibrated, get_calibrated_band
- **Class Variables:** pattern_id: str, predictions: list[tuple[float, bool]], empirical_strong_threshold: float, empirical_weak_threshold: float, total_matches: int, correct_matches: int, false_positives: int, false_negatives: int

### `AdaptiveConfidenceSystem`
- **Docstring:** System-wide adaptive confidence management.
- **Methods:** get_or_create_calibration, record_outcome, get_threshold_for_pattern, get_confidence_report
- **Class Variables:** pattern_calibrations: dict[str, PatternCalibration], total_predictions: int, global_accuracy: float

### `CheckpointPriority(str, Enum)`
- **Docstring:** Priority levels for human checkpoints.

### `CheckpointConfig`
- **Docstring:** Per-tenant checkpoint configuration.
- **Methods:** is_blocking, get_priority, should_auto_dismiss
- **Class Variables:** tenant_id: str, enabled_types: set[str], priority_overrides: dict[str, CheckpointPriority], auto_approve_confidence: float, auto_dismiss_after_hours: int, max_pending_checkpoints: int, blocking_checkpoints: set[str]

### `PrioritizedCheckpoint`
- **Docstring:** Enhanced checkpoint with priority and configurability.
- **Methods:** create, check_auto_dismiss
- **Class Variables:** checkpoint_id: str, checkpoint_type: str, incident_id: str, tenant_id: str, description: str, confidence: float, priority: CheckpointPriority, is_blocking: bool, created_at: datetime, expires_at: Optional[datetime], resolved_at: Optional[datetime], auto_dismissed: bool

### `M25GraduationStatus`
- **Docstring:** The three gates that graduate M25 from "loop-enabled" to "loop-proven".
- **Methods:** gate1_passed, gate2_passed, gate3_passed, is_graduated, status_label, to_dashboard, _get_next_action
- **Class Variables:** prevention_tracker: PreventionTracker, regret_tracker: GlobalRegretTracker, console_proof_incidents: list[str]

### `PreventionTimeline`
- **Docstring:** Console-ready timeline showing the learning loop in action.
- **Methods:** add_incident_created, add_policy_born, add_prevention, add_regret, add_rollback, to_console, _generate_narrative
- **Class Variables:** incident_id: str, tenant_id: str, events: list[dict]

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__` |

## Callers

learning workers, policy engines

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: PreventionOutcome
      methods: []
    - name: PreventionRecord
      methods: [create_prevention, to_console_timeline]
    - name: PreventionTracker
      methods: [record_prevention, record_failure, prevention_rate, has_proven_prevention, get_top_preventing_patterns]
    - name: RegretType
      methods: []
    - name: RegretEvent
      methods: []
    - name: PolicyRegretTracker
      methods: [add_regret, decay_regret, is_demoted, to_rollback_timeline]
    - name: GlobalRegretTracker
      methods: [get_or_create_tracker, record_regret, has_proven_rollback, system_regret_rate]
    - name: PatternCalibration
      methods: [record_outcome, accuracy, is_calibrated, get_calibrated_band]
    - name: AdaptiveConfidenceSystem
      methods: [get_or_create_calibration, record_outcome, get_threshold_for_pattern, get_confidence_report]
    - name: CheckpointPriority
      methods: []
    - name: CheckpointConfig
      methods: [is_blocking, get_priority, should_auto_dismiss]
    - name: PrioritizedCheckpoint
      methods: [create, check_auto_dismiss]
    - name: M25GraduationStatus
      methods: [gate1_passed, gate2_passed, gate3_passed, is_graduated, status_label, to_dashboard]
    - name: PreventionTimeline
      methods: [add_incident_created, add_policy_born, add_prevention, add_regret, add_rollback, to_console]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
