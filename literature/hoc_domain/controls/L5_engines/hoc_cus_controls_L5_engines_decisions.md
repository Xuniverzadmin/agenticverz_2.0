# hoc_cus_controls_L5_engines_decisions

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/controls/L5_engines/decisions.py` |
| Layer | L5 — Domain Engine |
| Domain | controls |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Phase-7 Decision enum and result types

## Intent

**Role:** Phase-7 Decision enum and result types
**Reference:** PIN-470, PIN-399 Phase-7 (Abuse & Protection Layer)
**Callers:** AbuseProtectionProvider, protection middleware

## Purpose

Phase-7 Abuse Protection — Decision Types

---

## Functions

### `allow() -> ProtectionResult`
- **Async:** No
- **Docstring:** Create an ALLOW result.
- **Calls:** ProtectionResult

### `reject_rate_limit(dimension: str, retry_after_ms: int, message: Optional[str]) -> ProtectionResult`
- **Async:** No
- **Docstring:** Create a REJECT result for rate limiting.
- **Calls:** ProtectionResult

### `reject_cost_limit(current_value: float, allowed_value: float, message: Optional[str]) -> ProtectionResult`
- **Async:** No
- **Docstring:** Create a REJECT result for cost limit.
- **Calls:** ProtectionResult

### `throttle(dimension: str, retry_after_ms: int, message: Optional[str]) -> ProtectionResult`
- **Async:** No
- **Docstring:** Create a THROTTLE result.
- **Calls:** ProtectionResult

### `warn(dimension: str, message: Optional[str]) -> ProtectionResult`
- **Async:** No
- **Docstring:** Create a WARN result (non-blocking).
- **Calls:** ProtectionResult

## Classes

### `Decision(Enum)`
- **Docstring:** Phase-7 Protection Decisions (Finite, Locked).
- **Methods:** blocks_request, is_warning_only

### `ProtectionResult`
- **Docstring:** Result of a protection check.
- **Methods:** to_error_response
- **Class Variables:** decision: Decision, dimension: str, retry_after_ms: Optional[int], current_value: Optional[float], allowed_value: Optional[float], message: Optional[str]

### `AnomalySignal`
- **Docstring:** Anomaly detection signal (non-blocking per ABUSE-003).
- **Methods:** to_signal_response
- **Class Variables:** baseline: float, observed: float, window: str, severity: str

## Attributes

- `__all__` (line 212)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

AbuseProtectionProvider, protection middleware

## Export Contract

```yaml
exports:
  functions:
    - name: allow
      signature: "allow() -> ProtectionResult"
    - name: reject_rate_limit
      signature: "reject_rate_limit(dimension: str, retry_after_ms: int, message: Optional[str]) -> ProtectionResult"
    - name: reject_cost_limit
      signature: "reject_cost_limit(current_value: float, allowed_value: float, message: Optional[str]) -> ProtectionResult"
    - name: throttle
      signature: "throttle(dimension: str, retry_after_ms: int, message: Optional[str]) -> ProtectionResult"
    - name: warn
      signature: "warn(dimension: str, message: Optional[str]) -> ProtectionResult"
  classes:
    - name: Decision
      methods: [blocks_request, is_warning_only]
    - name: ProtectionResult
      methods: [to_error_response]
    - name: AnomalySignal
      methods: [to_signal_response]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
