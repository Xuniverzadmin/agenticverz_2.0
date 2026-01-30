# hoc_cus_controls_L6_drivers_circuit_breaker

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/controls/L6_drivers/circuit_breaker.py` |
| Layer | L6 — Domain Driver |
| Domain | controls |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

DB-backed circuit breaker state tracking (sync) — L6 DOES NOT COMMIT

## Intent

**Role:** DB-backed circuit breaker state tracking (sync) — L6 DOES NOT COMMIT
**Reference:** PIN-470, M6 CostSim, TRANSACTION_BYPASS_REMEDIATION_CHECKLIST.md
**Callers:** L5 engines (must provide session, must own transaction boundary)

## Purpose

_No module docstring._

---

## Functions

### `create_circuit_breaker(session: Session, failure_threshold: Optional[int], drift_threshold: Optional[float], name: str) -> CircuitBreaker`
- **Async:** No
- **Docstring:** Create CircuitBreaker with required session.  L6 drivers are NOT singletons — each operation gets its own instance
- **Calls:** CircuitBreaker

### `async is_v2_disabled(session: Session) -> bool`
- **Async:** Yes
- **Docstring:** Check if CostSim V2 is disabled.
- **Calls:** create_circuit_breaker, is_disabled

### `async disable_v2(session: Session, reason: str, disabled_by: str, disabled_until: Optional[datetime]) -> Tuple[bool, Optional[Incident]]`
- **Async:** Yes
- **Docstring:** Disable CostSim V2.
- **Calls:** create_circuit_breaker, disable_v2

### `async enable_v2(session: Session, enabled_by: str, reason: Optional[str]) -> bool`
- **Async:** Yes
- **Docstring:** Enable CostSim V2.
- **Calls:** create_circuit_breaker, enable_v2

## Classes

### `CircuitBreakerState`
- **Docstring:** Current state of the circuit breaker (in-memory representation).
- **Methods:** to_dict
- **Class Variables:** is_open: bool, opened_at: Optional[datetime], reason: Optional[str], incident_id: Optional[str], consecutive_failures: int, last_failure_at: Optional[datetime], disabled_until: Optional[datetime], disabled_by: Optional[str]

### `Incident`
- **Docstring:** Incident record for circuit breaker trip.
- **Methods:** to_dict
- **Class Variables:** id: str, timestamp: datetime, reason: str, severity: str, drift_score: float, sample_count: int, details: Dict[str, Any], resolved: bool, resolved_at: Optional[datetime], resolved_by: Optional[str], resolution_notes: Optional[str], alert_sent: bool, alert_sent_at: Optional[datetime]

### `CircuitBreaker`
- **Docstring:** DB-backed circuit breaker for CostSim V2 auto-disable.
- **Methods:** __init__, _get_or_create_state, is_disabled, _auto_recover, is_open, is_closed, get_state, report_drift, report_schema_error, disable_v2, enable_v2, reset, _trip, _resolve_incident_db, _save_incident_file, get_incidents, _send_alert_disable, _send_alert_enable, _post_alertmanager

## Attributes

- `FEATURE_INTENT` (line 28)
- `RETRY_POLICY` (line 29)
- `logger` (line 89)
- `CB_NAME` (line 92)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__`, `app.costsim.config`, `app.db`, `app.infra`, `httpx`, `sqlmodel` |

## Callers

L5 engines (must provide session, must own transaction boundary)

## Export Contract

```yaml
exports:
  functions:
    - name: create_circuit_breaker
      signature: "create_circuit_breaker(session: Session, failure_threshold: Optional[int], drift_threshold: Optional[float], name: str) -> CircuitBreaker"
    - name: is_v2_disabled
      signature: "async is_v2_disabled(session: Session) -> bool"
    - name: disable_v2
      signature: "async disable_v2(session: Session, reason: str, disabled_by: str, disabled_until: Optional[datetime]) -> Tuple[bool, Optional[Incident]]"
    - name: enable_v2
      signature: "async enable_v2(session: Session, enabled_by: str, reason: Optional[str]) -> bool"
  classes:
    - name: CircuitBreakerState
      methods: [to_dict]
    - name: Incident
      methods: [to_dict]
    - name: CircuitBreaker
      methods: [is_disabled, is_open, is_closed, get_state, report_drift, report_schema_error, disable_v2, enable_v2, reset, get_incidents]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
