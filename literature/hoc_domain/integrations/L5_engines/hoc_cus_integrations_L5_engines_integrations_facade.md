# hoc_cus_integrations_L5_engines_integrations_facade

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/integrations_facade.py` |
| Layer | L5 — Domain Engine |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Integrations domain facade - unified entry point for integration management

## Intent

**Role:** Integrations domain facade - unified entry point for integration management
**Reference:** PIN-470, Connectivity Domain - Customer Console v1 Constitution
**Callers:** L2 integrations API (aos_cus_integrations.py)

## Purpose

Integrations Domain Facade (L4)

---

## Functions

### `get_integrations_facade() -> IntegrationsFacade`
- **Async:** No
- **Docstring:** Get the singleton IntegrationsFacade instance.
- **Calls:** IntegrationsFacade

## Classes

### `IntegrationSummaryResult`
- **Docstring:** Integration summary for list view.
- **Class Variables:** id: str, name: str, provider_type: str, status: str, health_state: str, default_model: Optional[str], created_at: datetime

### `IntegrationListResult`
- **Docstring:** Integration list response.
- **Class Variables:** items: list[IntegrationSummaryResult], total: int

### `IntegrationDetailResult`
- **Docstring:** Integration detail response.
- **Class Variables:** id: str, tenant_id: str, name: str, provider_type: str, status: str, health_state: str, health_checked_at: Optional[datetime], health_message: Optional[str], default_model: Optional[str], budget_limit_cents: int, token_limit_month: int, rate_limit_rpm: int, created_at: datetime, updated_at: Optional[datetime], created_by: Optional[str]

### `IntegrationLifecycleResult`
- **Docstring:** Result of enable/disable operation.
- **Class Variables:** integration_id: str, status: str, message: str

### `IntegrationDeleteResult`
- **Docstring:** Result of delete operation.
- **Class Variables:** deleted: bool, integration_id: str

### `HealthCheckResult`
- **Docstring:** Health check result.
- **Class Variables:** integration_id: str, health_state: str, message: Optional[str], latency_ms: Optional[int], checked_at: datetime

### `HealthStatusResult`
- **Docstring:** Cached health status.
- **Class Variables:** integration_id: str, health_state: str, health_message: Optional[str], health_checked_at: Optional[datetime]

### `LimitsStatusResult`
- **Docstring:** Usage vs limits status.
- **Class Variables:** integration_id: str, budget_limit_cents: int, budget_used_cents: int, budget_percent: float, token_limit_month: int, tokens_used_month: int, token_percent: float, rate_limit_rpm: int, requests_this_minute: int, rate_percent: float, period_start: datetime, period_end: datetime

### `IntegrationsFacade`
- **Docstring:** Unified facade for LLM integration management.
- **Methods:** __init__, list_integrations, get_integration, create_integration, update_integration, delete_integration, enable_integration, disable_integration, get_health_status, test_credentials, get_limits_status

## Attributes

- `_facade_instance: IntegrationsFacade | None` (line 467)
- `__all__` (line 478)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L5 Engine | `app.hoc.cus.integrations.L5_engines.cus_integration_service` |

## Callers

L2 integrations API (aos_cus_integrations.py)

## Export Contract

```yaml
exports:
  functions:
    - name: get_integrations_facade
      signature: "get_integrations_facade() -> IntegrationsFacade"
  classes:
    - name: IntegrationSummaryResult
      methods: []
    - name: IntegrationListResult
      methods: []
    - name: IntegrationDetailResult
      methods: []
    - name: IntegrationLifecycleResult
      methods: []
    - name: IntegrationDeleteResult
      methods: []
    - name: HealthCheckResult
      methods: []
    - name: HealthStatusResult
      methods: []
    - name: LimitsStatusResult
      methods: []
    - name: IntegrationsFacade
      methods: [list_integrations, get_integration, create_integration, update_integration, delete_integration, enable_integration, disable_integration, get_health_status, test_credentials, get_limits_status]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
