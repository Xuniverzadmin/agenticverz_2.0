# hoc_cus_integrations_L5_engines_graduation_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/graduation_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Agent graduation evaluation domain logic (pure computation)

## Intent

**Role:** Agent graduation evaluation domain logic (pure computation)
**Reference:** PIN-470, PIN-256 Phase E FIX-01
**Callers:** graduation_evaluator.py (L5)

## Purpose

M25 Graduation Engine

---

## Classes

### `GraduationThresholds`
- **Docstring:** Configurable thresholds for graduation gates.
- **Class Variables:** min_preventions: int, prevention_rate_min: float, prevention_window_days: int, min_auto_demotions: int, max_regret_rate: float, regret_window_days: int, min_timeline_views: int, timeline_window_days: int, downgrade_if_prevention_rate_below: float, downgrade_if_regret_rate_above: float, downgrade_if_no_prevention_days: int

### `GateEvidence(NamedTuple)`
- **Docstring:** Evidence for a single gate - computed from database.
- **Class Variables:** name: str, passed: bool, score: float, evidence: dict, last_evaluated: datetime, degraded: bool

### `GraduationEvidence`
- **Docstring:** All evidence needed to compute graduation status.
- **Class Variables:** total_preventions: int, total_prevention_attempts: int, last_prevention_at: Optional[datetime], prevention_rate: float, total_regret_events: int, total_auto_demotions: int, last_demotion_at: Optional[datetime], regret_rate: float, timeline_views_with_prevention: int, last_timeline_view_at: Optional[datetime], evaluated_at: datetime, evidence_window_start: Optional[datetime], evidence_window_end: Optional[datetime]

### `GraduationLevel(str, Enum)`
- **Docstring:** Graduation levels - derived from evidence.

### `ComputedGraduationStatus`
- **Docstring:** Graduation status computed from evidence.
- **Methods:** is_graduated, is_degraded, status_label, to_api_response
- **Class Variables:** level: GraduationLevel, gates: dict[str, GateEvidence], thresholds: GraduationThresholds, computed_at: datetime, previous_level: Optional[GraduationLevel], degraded_from: Optional[GraduationLevel], degraded_at: Optional[datetime], degradation_reason: Optional[str]

### `GraduationEngine`
- **Docstring:** Computes graduation status from evidence.
- **Methods:** __init__, compute, _evaluate_gate1, _evaluate_gate2, _evaluate_gate3, _check_degradation

### `CapabilityGates`
- **Docstring:** Capabilities that are LOCKED until graduation passes specific gates.
- **Methods:** can_auto_apply_recovery, can_auto_activate_policy, can_full_auto_routing, get_blocked_capabilities, get_unlocked_capabilities

### `SimulationState`
- **Docstring:** Simulation state - SEPARATE from real graduation.
- **Methods:** is_demo_mode, to_display
- **Class Variables:** simulated_gate1: bool, simulated_gate2: bool, simulated_gate3: bool, simulated_at: Optional[datetime]

## Attributes

- `logger` (line 53)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__` |

## Callers

graduation_evaluator.py (L5)

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: GraduationThresholds
      methods: []
    - name: GateEvidence
      methods: []
    - name: GraduationEvidence
      methods: []
    - name: GraduationLevel
      methods: []
    - name: ComputedGraduationStatus
      methods: [is_graduated, is_degraded, status_label, to_api_response]
    - name: GraduationEngine
      methods: [compute]
    - name: CapabilityGates
      methods: [can_auto_apply_recovery, can_auto_activate_policy, can_full_auto_routing, get_blocked_capabilities, get_unlocked_capabilities]
    - name: SimulationState
      methods: [is_demo_mode, to_display]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
