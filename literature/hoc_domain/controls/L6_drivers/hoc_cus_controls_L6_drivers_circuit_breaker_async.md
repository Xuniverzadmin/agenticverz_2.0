# hoc_cus_controls_L6_drivers_circuit_breaker_async

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/controls/L6_drivers/circuit_breaker_async.py` |
| Layer | L6 — Domain Driver |
| Domain | controls |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Async DB-backed circuit breaker state tracking

## Intent

**Role:** Async DB-backed circuit breaker state tracking
**Reference:** PIN-470, M6 CostSim
**Callers:** sandbox.py, canary.py (L5 engines)

## Purpose

_No module docstring._

---

## Functions

### `async _get_or_create_state(session: AsyncSession, lock: bool) -> CostSimCBStateModel`
- **Async:** Yes
- **Docstring:** Get or create circuit breaker state row.  Args:
- **Calls:** CostSimCBStateModel, add, execute, first, flush, now, scalars, select, where, with_for_update

### `async is_v2_disabled(session: Optional[AsyncSession]) -> bool`
- **Async:** Yes
- **Docstring:** Check if V2 is disabled.  Non-blocking async check that also handles TTL-based auto-recovery.
- **Calls:** AsyncSessionLocal, _try_auto_recover, close, execute, first, get_config, limit, now, replace, scalars, select, where

### `async _try_auto_recover(state_id: int) -> bool`
- **Async:** Yes
- **Docstring:** Attempt auto-recovery with proper locking to avoid TOCTOU race.  Uses SELECT FOR UPDATE to ensure only one worker performs recovery.
- **Calls:** AsyncSessionLocal, _build_enable_alert_payload, _enqueue_alert, _resolve_incident, async_session_context, begin, error, execute, first, flush, get_metrics, info, now, record_auto_recovery, record_cb_enabled, replace, scalars, select, set_circuit_breaker_state, set_consecutive_failures

### `async _auto_recover(session: AsyncSession, state: CostSimCBStateModel) -> None`
- **Async:** Yes
- **Docstring:** Legacy auto-recover function (deprecated).  Use _try_auto_recover() instead for proper locking.
- **Calls:** _build_enable_alert_payload, _enqueue_alert, _resolve_incident, info, now

### `async get_state() -> CircuitBreakerState`
- **Async:** Yes
- **Docstring:** Get current circuit breaker state.
- **Calls:** CircuitBreakerState, _get_or_create_state, async_session_context

### `async report_drift(drift_score: float, sample_count: int, details: Optional[Dict[str, Any]]) -> Optional[Incident]`
- **Async:** Yes
- **Docstring:** Report drift observation.  If drift exceeds threshold, trips the circuit breaker.
- **Calls:** AsyncSessionLocal, _get_or_create_state, _trip, begin, get_config, get_metrics, info, now, set_consecutive_failures, warning

### `async report_schema_error(error_count: int, details: Optional[Dict[str, Any]]) -> Optional[Incident]`
- **Async:** Yes
- **Docstring:** Report schema validation errors.  Args:
- **Calls:** AsyncSessionLocal, _get_or_create_state, _trip, begin, get_config

### `async disable_v2(reason: str, disabled_by: str, disabled_until: Optional[datetime]) -> Tuple[bool, Optional[Incident]]`
- **Async:** Yes
- **Docstring:** Manually disable CostSim V2.  Idempotent: returns False if already disabled with same params.
- **Calls:** AsyncSessionLocal, _get_or_create_state, _trip, begin

### `async enable_v2(enabled_by: str, reason: Optional[str]) -> bool`
- **Async:** Yes
- **Docstring:** Manually enable CostSim V2.  Idempotent: returns False if already enabled.
- **Calls:** AsyncSessionLocal, _build_enable_alert_payload, _enqueue_alert, _get_or_create_state, _resolve_incident, begin, get_metrics, info, now, record_cb_enabled, set_circuit_breaker_state, set_consecutive_failures

### `async _trip(session: AsyncSession, state: CostSimCBStateModel, reason: str, drift_score: float, sample_count: int, details: Optional[Dict[str, Any]], severity: str, disabled_by: str, disabled_until: Optional[datetime]) -> Incident`
- **Async:** Yes
- **Docstring:** Trip the circuit breaker.  Args:
- **Calls:** CostSimCBIncidentModel, Incident, _build_disable_alert_payload, _enqueue_alert, add, dumps, error, flush, get_config, get_metrics, now, record_cb_disabled, record_cb_incident, set_circuit_breaker_state, str, timedelta, uuid4

### `async _resolve_incident(session: AsyncSession, incident_id: str, resolved_by: str, resolution_notes: str) -> None`
- **Async:** Yes
- **Docstring:** Resolve an incident.
- **Calls:** execute, first, now, scalars, select, where

### `async get_incidents(include_resolved: bool, limit: int) -> List[Incident]`
- **Async:** Yes
- **Docstring:** Get recent incidents.  Args:
- **Calls:** Incident, append, async_session_context, desc, execute, get_details, limit, order_by, scalars, select, where

### `async _enqueue_alert(session: AsyncSession, alert_type: str, payload: List[Dict[str, Any]], incident_id: Optional[str]) -> None`
- **Async:** Yes
- **Docstring:** Enqueue alert for reliable delivery.  Args:
- **Calls:** CostSimAlertQueueModel, add, debug, flush

### `_build_disable_alert_payload(incident: Incident, disabled_until: Optional[datetime]) -> List[Dict[str, Any]]`
- **Async:** No
- **Docstring:** Build Alertmanager payload for disable alert.
- **Calls:** get_config, isoformat, lower, now

### `_build_enable_alert_payload(enabled_by: str, reason: Optional[str]) -> List[Dict[str, Any]]`
- **Async:** No
- **Docstring:** Build Alertmanager payload for enable/resolved alert.
- **Calls:** get_config, isoformat, now

### `get_async_circuit_breaker() -> AsyncCircuitBreaker`
- **Async:** No
- **Docstring:** Get the global async circuit breaker instance.
- **Calls:** AsyncCircuitBreaker

## Classes

### `CircuitBreakerState`
- **Docstring:** Current state of the circuit breaker.
- **Methods:** to_dict
- **Class Variables:** is_open: bool, opened_at: Optional[datetime], reason: Optional[str], incident_id: Optional[str], consecutive_failures: int, last_failure_at: Optional[datetime], disabled_until: Optional[datetime], disabled_by: Optional[str]

### `Incident`
- **Docstring:** Incident record for circuit breaker trip.
- **Methods:** to_dict
- **Class Variables:** id: str, timestamp: datetime, reason: str, severity: str, drift_score: float, sample_count: int, details: Dict[str, Any], resolved: bool, resolved_at: Optional[datetime], resolved_by: Optional[str], resolution_notes: Optional[str], alert_sent: bool, alert_sent_at: Optional[datetime]

### `AsyncCircuitBreaker`
- **Docstring:** Async circuit breaker class for compatibility with existing code.
- **Methods:** __init__, is_disabled, is_open, is_closed, get_state, report_drift, report_schema_error, disable_v2, enable_v2, reset, reset_v2, get_incidents

## Attributes

- `FEATURE_INTENT` (line 27)
- `RETRY_POLICY` (line 28)
- `logger` (line 84)
- `CB_NAME` (line 87)
- `_async_circuit_breaker: Optional[AsyncCircuitBreaker]` (line 991)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.costsim_cb` |
| External | `__future__`, `app.costsim.cb_sync_wrapper`, `app.costsim.config`, `app.costsim.metrics`, `app.db_async`, `app.infra`, `sqlalchemy`, `sqlalchemy.ext.asyncio` |

## Callers

sandbox.py, canary.py (L5 engines)

## Export Contract

```yaml
exports:
  functions:
    - name: is_v2_disabled
      signature: "async is_v2_disabled(session: Optional[AsyncSession]) -> bool"
    - name: get_state
      signature: "async get_state() -> CircuitBreakerState"
    - name: report_drift
      signature: "async report_drift(drift_score: float, sample_count: int, details: Optional[Dict[str, Any]]) -> Optional[Incident]"
    - name: report_schema_error
      signature: "async report_schema_error(error_count: int, details: Optional[Dict[str, Any]]) -> Optional[Incident]"
    - name: disable_v2
      signature: "async disable_v2(reason: str, disabled_by: str, disabled_until: Optional[datetime]) -> Tuple[bool, Optional[Incident]]"
    - name: enable_v2
      signature: "async enable_v2(enabled_by: str, reason: Optional[str]) -> bool"
    - name: get_incidents
      signature: "async get_incidents(include_resolved: bool, limit: int) -> List[Incident]"
    - name: get_async_circuit_breaker
      signature: "get_async_circuit_breaker() -> AsyncCircuitBreaker"
  classes:
    - name: CircuitBreakerState
      methods: [to_dict]
    - name: Incident
      methods: [to_dict]
    - name: AsyncCircuitBreaker
      methods: [is_disabled, is_open, is_closed, get_state, report_drift, report_schema_error, disable_v2, enable_v2, reset, reset_v2, get_incidents]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
