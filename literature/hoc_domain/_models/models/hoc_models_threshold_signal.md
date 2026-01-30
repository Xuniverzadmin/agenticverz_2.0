# hoc_models_threshold_signal

| Field | Value |
|-------|-------|
| Path | `backend/app/models/threshold_signal.py` |
| Layer | L4 — Domain Engine |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

Record near-threshold and breach events for alerting and audit

## Intent

**Role:** Record near-threshold and breach events for alerting and audit
**Reference:** POLICY_CONTROL_LEVER_IMPLEMENTATION_PLAN.md PCL-006
**Callers:** policy/prevention_engine.py, services/alert_emitter.py

## Purpose

Threshold Signal Model

---

## Classes

### `SignalType(str, Enum)`
- **Docstring:** Type of threshold signal.

### `ThresholdMetric(str, Enum)`
- **Docstring:** Metrics that can trigger threshold signals.

### `ThresholdSignal(SQLModel)`
- **Docstring:** Immutable record of a threshold event.
- **Methods:** create_near_signal, create_breach_signal, acknowledge, mark_alert_sent, to_evidence
- **Class Variables:** id: Optional[int], signal_id: str, run_id: str, policy_id: str, tenant_id: str, step_index: Optional[int], signal_type: str, metric: str, current_value: float, threshold_value: float, percentage: Optional[float], action_taken: Optional[str], timestamp: datetime, acknowledged: bool, acknowledged_by: Optional[str], acknowledged_at: Optional[datetime], alert_sent: bool, alert_sent_at: Optional[datetime], alert_channels: Optional[str]

### `ThresholdSignalResponse(BaseModel)`
- **Docstring:** Response model for threshold signal.
- **Class Variables:** signal_id: str, run_id: str, policy_id: str, tenant_id: str, step_index: Optional[int], signal_type: SignalType, metric: ThresholdMetric, current_value: float, threshold_value: float, percentage: Optional[float], action_taken: Optional[str], timestamp: datetime, acknowledged: bool, acknowledged_by: Optional[str], acknowledged_at: Optional[datetime]

### `ThresholdSignalListResponse(BaseModel)`
- **Docstring:** Response model for list of threshold signals.
- **Class Variables:** signals: list[ThresholdSignalResponse], total: int, page: int, page_size: int

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `pydantic`, `sqlmodel` |

## Callers

policy/prevention_engine.py, services/alert_emitter.py

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: SignalType
      methods: []
    - name: ThresholdMetric
      methods: []
    - name: ThresholdSignal
      methods: [create_near_signal, create_breach_signal, acknowledge, mark_alert_sent, to_evidence]
    - name: ThresholdSignalResponse
      methods: []
    - name: ThresholdSignalListResponse
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
