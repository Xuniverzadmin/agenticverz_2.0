# hoc_cus_integrations_L5_engines_webhook_adapter

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/external_adapters/webhook_adapter.py` |
| Layer | L3 — Boundary Adapters |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Webhook notification adapter with retry logic

## Intent

**Role:** Webhook notification adapter with retry logic
**Reference:** GAP-153 (Webhook Retry Logic)
**Callers:** NotificationService, AlertManager

## Purpose

Webhook Notification Adapter with Retry Logic (GAP-153)

---

## Classes

### `CircuitState(str, Enum)`
- **Docstring:** Circuit breaker states.

### `CircuitBreakerConfig`
- **Docstring:** Configuration for circuit breaker.
- **Class Variables:** failure_threshold: int, success_threshold: int, timeout_seconds: float, half_open_max_calls: int

### `CircuitBreaker`
- **Docstring:** Circuit breaker for webhook endpoint.
- **Methods:** can_execute, record_success, record_failure
- **Class Variables:** config: CircuitBreakerConfig, state: CircuitState, failure_count: int, success_count: int, last_failure_time: Optional[float], half_open_calls: int

### `WebhookDeliveryAttempt`
- **Docstring:** Record of a webhook delivery attempt.
- **Class Variables:** attempt_number: int, timestamp: datetime, status_code: Optional[int], error: Optional[str], response_time_ms: Optional[int], success: bool

### `WebhookDelivery`
- **Docstring:** Full record of webhook delivery with all attempts.
- **Methods:** to_dict
- **Class Variables:** message_id: str, webhook_url: str, payload: Dict[str, Any], attempts: List[WebhookDeliveryAttempt], final_status: NotificationStatus, created_at: datetime

### `WebhookAdapter(NotificationAdapter)`
- **Docstring:** Webhook notification adapter with retry logic.
- **Methods:** __init__, connect, disconnect, _get_circuit_breaker, _sign_payload, send, _deliver_with_retry, _attempt_delivery, send_batch, get_status, get_delivery_details, get_circuit_breaker_status

## Attributes

- `logger` (line 43)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `base`, `httpx` |

## Callers

NotificationService, AlertManager

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: CircuitState
      methods: []
    - name: CircuitBreakerConfig
      methods: []
    - name: CircuitBreaker
      methods: [can_execute, record_success, record_failure]
    - name: WebhookDeliveryAttempt
      methods: []
    - name: WebhookDelivery
      methods: [to_dict]
    - name: WebhookAdapter
      methods: [connect, disconnect, send, send_batch, get_status, get_delivery_details, get_circuit_breaker_status]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
