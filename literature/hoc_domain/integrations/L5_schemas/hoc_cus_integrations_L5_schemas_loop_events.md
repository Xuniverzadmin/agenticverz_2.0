# hoc_cus_integrations_L5_schemas_loop_events

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_schemas/loop_events.py` |
| Layer | L5 — Domain Schemas |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Integration loop event definitions (dataclasses, enums)

## Intent

**Role:** Integration loop event definitions (dataclasses, enums)
**Reference:** HOC_LAYER_TOPOLOGY_V1.md, INTEGRATIONS_PHASE2.5_IMPLEMENTATION_PLAN.md
**Callers:** integrations/engines/*, integrations/drivers/*

## Purpose

M25 Integration Loop Events

---

## Functions

### `ensure_json_serializable(obj: Any, path: str) -> Any`
- **Async:** No
- **Docstring:** Guard function to ensure all objects stored in details are JSON-serializable.  Raises TypeError with clear path if non-serializable object found.
- **Calls:** TypeError, ensure_json_serializable, enumerate, hasattr, isinstance, isoformat, items, to_dict, type

## Classes

### `ConfidenceCalculator`
- **Docstring:** Centralized confidence calculation.
- **Methods:** calculate_recovery_confidence, should_auto_apply, get_confirmation_level

### `ConfidenceBand(str, Enum)`
- **Docstring:** Confidence classification for pattern matching.
- **Methods:** from_confidence, allows_auto_apply, requires_human_review

### `LoopStage(str, Enum)`
- **Docstring:** Stages in the integration feedback loop.

### `LoopFailureState(str, Enum)`
- **Docstring:** Explicit failure states for when the loop doesn't complete.

### `PolicyMode(str, Enum)`
- **Docstring:** Policy activation modes for safety.

### `HumanCheckpointType(str, Enum)`
- **Docstring:** Types of human intervention points.

### `LoopEvent`
- **Docstring:** Base event for integration loop.
- **Methods:** create, is_success, is_blocked, to_dict
- **Class Variables:** event_id: str, incident_id: str, tenant_id: str, stage: LoopStage, timestamp: datetime, details: dict[str, Any], failure_state: Optional[LoopFailureState], confidence_band: Optional[ConfidenceBand], requires_human_review: bool

### `PatternMatchResult`
- **Docstring:** Result of Bridge 1: Incident → Failure Catalog.
- **Methods:** from_match, no_match, should_auto_proceed, to_dict
- **Class Variables:** incident_id: str, pattern_id: Optional[str], confidence: float, confidence_band: ConfidenceBand, is_new_pattern: bool, matched: bool, signature_hash: str, match_details: dict[str, Any]

### `RecoverySuggestion`
- **Docstring:** Result of Bridge 2: Pattern → Recovery.
- **Methods:** create, none_available, add_confirmation, to_dict
- **Class Variables:** recovery_id: str, incident_id: str, pattern_id: str, suggestion_type: Literal['template', 'generated', 'none'], confidence: float, confidence_band: ConfidenceBand, action_type: str, action_params: dict[str, Any], status: Literal['pending', 'approved', 'applied', 'rejected'], auto_applicable: bool, requires_confirmation: int, confirmations_received: int, rejection_reason: Optional[str]

### `PolicyRule`
- **Docstring:** Result of Bridge 3: Recovery → Policy.
- **Methods:** create, record_shadow_evaluation, add_confirmation, record_regret, shadow_block_rate, to_dict
- **Class Variables:** policy_id: str, name: str, description: str, category: Literal['safety', 'privacy', 'operational', 'routing', 'custom'], condition: str, action: Literal['block', 'warn', 'escalate', 'route_away', 'rate_limit'], scope_type: Literal['tenant', 'agent', 'global'], scope_id: Optional[str], source_pattern_id: str, source_recovery_id: str, confidence: float, confidence_band: ConfidenceBand, mode: PolicyMode, confirmations_required: int, confirmations_received: int, regret_count: int, shadow_evaluations: int, shadow_would_block: int, created_at: datetime, activated_at: Optional[datetime]

### `RoutingAdjustment`
- **Docstring:** Result of Bridge 4: Policy → CARE Routing.
- **Methods:** create, check_kpi_regression, rollback, effective_magnitude, to_dict
- **Class Variables:** adjustment_id: str, agent_id: str, capability: Optional[str], adjustment_type: Literal['confidence_penalty', 'route_block', 'escalation_add', 'weight_shift'], magnitude: float, reason: str, source_policy_id: str, max_delta: float, decay_days: int, rollback_threshold: float, created_at: datetime, expires_at: Optional[datetime], is_active: bool, was_rolled_back: bool, rollback_reason: Optional[str], kpi_baseline: Optional[float], kpi_current: Optional[float]

### `HumanCheckpoint`
- **Docstring:** Human intervention point in the loop.
- **Methods:** create, resolve, is_pending
- **Class Variables:** checkpoint_id: str, checkpoint_type: HumanCheckpointType, incident_id: str, tenant_id: str, stage: LoopStage, target_id: str, description: str, options: list[str], created_at: datetime, resolved_at: Optional[datetime], resolved_by: Optional[str], resolution: Optional[str]

### `LoopStatus`
- **Docstring:** Complete status of an integration loop instance.
- **Methods:** completion_pct, to_console_display, _generate_narrative, to_dict
- **Class Variables:** loop_id: str, incident_id: str, tenant_id: str, current_stage: LoopStage, stages_completed: list[str], stages_failed: list[str], total_stages: int, started_at: datetime, completed_at: Optional[datetime], is_complete: bool, is_blocked: bool, failure_state: Optional[LoopFailureState], pending_checkpoints: list[str], pattern_match_result: Optional[PatternMatchResult], recovery_suggestion: Optional[RecoverySuggestion], policy_rule: Optional[PolicyRule], routing_adjustment: Optional[RoutingAdjustment]

## Attributes

- `LOOP_MECHANICS_VERSION` (line 46)
- `LOOP_MECHANICS_FROZEN_AT` (line 47)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__` |

## Callers

integrations/engines/*, integrations/drivers/*

## Export Contract

```yaml
exports:
  functions:
    - name: ensure_json_serializable
      signature: "ensure_json_serializable(obj: Any, path: str) -> Any"
  classes:
    - name: ConfidenceCalculator
      methods: [calculate_recovery_confidence, should_auto_apply, get_confirmation_level]
    - name: ConfidenceBand
      methods: [from_confidence, allows_auto_apply, requires_human_review]
    - name: LoopStage
      methods: []
    - name: LoopFailureState
      methods: []
    - name: PolicyMode
      methods: []
    - name: HumanCheckpointType
      methods: []
    - name: LoopEvent
      methods: [create, is_success, is_blocked, to_dict]
    - name: PatternMatchResult
      methods: [from_match, no_match, should_auto_proceed, to_dict]
    - name: RecoverySuggestion
      methods: [create, none_available, add_confirmation, to_dict]
    - name: PolicyRule
      methods: [create, record_shadow_evaluation, add_confirmation, record_regret, shadow_block_rate, to_dict]
    - name: RoutingAdjustment
      methods: [create, check_kpi_regression, rollback, effective_magnitude, to_dict]
    - name: HumanCheckpoint
      methods: [create, resolve, is_pending]
    - name: LoopStatus
      methods: [completion_pct, to_console_display, to_dict]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
