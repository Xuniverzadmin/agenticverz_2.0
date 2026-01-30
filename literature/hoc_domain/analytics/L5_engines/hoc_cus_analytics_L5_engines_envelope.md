# hoc_cus_analytics_L5_engines_envelope

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/analytics/L5_engines/envelope.py` |
| Layer | L5 — Domain Engine |
| Domain | analytics |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Base optimization envelope definition

## Intent

**Role:** Base optimization envelope definition
**Reference:** C3_ENVELOPE_ABSTRACTION.md (FROZEN), C4_ENVELOPE_COORDINATION_CONTRACT.md (FROZEN)
**Callers:** optimization/*

## Purpose

_No module docstring._

---

## Functions

### `get_envelope_priority(envelope_class: EnvelopeClass) -> int`
- **Async:** No
- **Docstring:** Get the priority of an envelope class (lower number = higher priority).

### `has_higher_priority(class_a: EnvelopeClass, class_b: EnvelopeClass) -> bool`
- **Async:** No
- **Docstring:** Check if class_a has higher priority than class_b.
- **Calls:** get_envelope_priority

### `validate_envelope(envelope: Envelope) -> None`
- **Async:** No
- **Docstring:** Validate envelope against hard gate rules (V1-V5 + CI-C4-1).  These rules are evaluated BEFORE an envelope can ever apply.
- **Calls:** EnvelopeValidationError, info, issubset, set

### `calculate_bounded_value(baseline: float, bounds: EnvelopeBounds, prediction_confidence: float) -> float`
- **Async:** No
- **Docstring:** Calculate the bounded value based on prediction confidence.  The value is scaled linearly with confidence within bounds.
- **Calls:** min

### `create_audit_record(envelope: Envelope, baseline_value: float) -> EnvelopeAuditRecord`
- **Async:** No
- **Docstring:** Create an audit record for envelope application.
- **Calls:** EnvelopeAuditRecord, now

## Classes

### `DeltaType(str, Enum)`
- **Docstring:** How bounds are expressed.

### `EnvelopeClass(str, Enum)`
- **Docstring:** C4 Envelope Class (FROZEN priority order).

### `BaselineSource(str, Enum)`
- **Docstring:** Where baseline value comes from.

### `EnvelopeLifecycle(str, Enum)`
- **Docstring:** Fixed envelope lifecycle states.

### `RevertReason(str, Enum)`
- **Docstring:** Why an envelope was reverted.

### `EnvelopeTrigger`
- **Docstring:** What prediction triggers this envelope.
- **Class Variables:** prediction_type: str, min_confidence: float

### `EnvelopeScope`
- **Docstring:** What this envelope affects.
- **Class Variables:** target_subsystem: str, target_parameter: str

### `EnvelopeBounds`
- **Docstring:** Numerical bounds for the envelope.
- **Class Variables:** delta_type: DeltaType, max_increase: float, max_decrease: float, absolute_ceiling: Optional[float]

### `EnvelopeTimebox`
- **Docstring:** Time constraints for the envelope.
- **Class Variables:** max_duration_seconds: int, hard_expiry: bool

### `EnvelopeBaseline`
- **Docstring:** Baseline value reference.
- **Class Variables:** source: BaselineSource, reference_id: str, value: Optional[float]

### `EnvelopeAuditRecord`
- **Docstring:** Immutable audit record for envelope lifecycle.
- **Class Variables:** envelope_id: str, envelope_version: str, prediction_id: str, target_subsystem: str, target_parameter: str, baseline_value: float, applied_value: float, applied_at: datetime, reverted_at: Optional[datetime], revert_reason: Optional[RevertReason]

### `CoordinationDecisionType(str, Enum)`
- **Docstring:** C4 coordination decision types.

### `CoordinationAuditRecord`
- **Docstring:** C4 Coordination audit record.
- **Class Variables:** audit_id: str, envelope_id: str, envelope_class: EnvelopeClass, decision: CoordinationDecisionType, reason: str, timestamp: datetime, conflicting_envelope_id: Optional[str], preempting_envelope_id: Optional[str], active_envelopes_count: int

### `CoordinationDecision`
- **Docstring:** Result of a coordination check.
- **Class Variables:** allowed: bool, decision: CoordinationDecisionType, reason: str, conflicting_envelope_id: Optional[str], preempting_envelope_id: Optional[str]

### `Envelope`
- **Docstring:** Declarative optimization envelope.
- **Class Variables:** envelope_id: str, envelope_version: str, trigger: EnvelopeTrigger, scope: EnvelopeScope, bounds: EnvelopeBounds, timebox: EnvelopeTimebox, baseline: EnvelopeBaseline, envelope_class: Optional[EnvelopeClass], revert_on: List[RevertReason], audit_enabled: bool, lifecycle: EnvelopeLifecycle, applied_at: Optional[datetime], reverted_at: Optional[datetime], revert_reason: Optional[RevertReason], prediction_id: Optional[str], applied_value: Optional[float]

### `EnvelopeValidationError(Exception)`
- **Docstring:** Raised when envelope fails validation.
- **Methods:** __init__

## Attributes

- `logger` (line 43)
- `ENVELOPE_CLASS_PRIORITY: Dict[EnvelopeClass, int]` (line 74)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

optimization/*

## Export Contract

```yaml
exports:
  functions:
    - name: get_envelope_priority
      signature: "get_envelope_priority(envelope_class: EnvelopeClass) -> int"
    - name: has_higher_priority
      signature: "has_higher_priority(class_a: EnvelopeClass, class_b: EnvelopeClass) -> bool"
    - name: validate_envelope
      signature: "validate_envelope(envelope: Envelope) -> None"
    - name: calculate_bounded_value
      signature: "calculate_bounded_value(baseline: float, bounds: EnvelopeBounds, prediction_confidence: float) -> float"
    - name: create_audit_record
      signature: "create_audit_record(envelope: Envelope, baseline_value: float) -> EnvelopeAuditRecord"
  classes:
    - name: DeltaType
      methods: []
    - name: EnvelopeClass
      methods: []
    - name: BaselineSource
      methods: []
    - name: EnvelopeLifecycle
      methods: []
    - name: RevertReason
      methods: []
    - name: EnvelopeTrigger
      methods: []
    - name: EnvelopeScope
      methods: []
    - name: EnvelopeBounds
      methods: []
    - name: EnvelopeTimebox
      methods: []
    - name: EnvelopeBaseline
      methods: []
    - name: EnvelopeAuditRecord
      methods: []
    - name: CoordinationDecisionType
      methods: []
    - name: CoordinationAuditRecord
      methods: []
    - name: CoordinationDecision
      methods: []
    - name: Envelope
      methods: []
    - name: EnvelopeValidationError
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
