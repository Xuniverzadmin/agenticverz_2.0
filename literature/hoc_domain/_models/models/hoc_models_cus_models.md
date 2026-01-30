# hoc_models_cus_models

| Field | Value |
|-------|-------|
| Path | `backend/app/models/cus_models.py` |
| Layer | L6 — Platform Substrate |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

Customer integration data models

## Intent

**Role:** Customer integration data models
**Reference:** docs/architecture/CUSTOMER_INTEGRATIONS_ARCHITECTURE.md
**Callers:** cus_* services, cus_* APIs

## Purpose

Customer Integrations Models

---

## Functions

### `utc_now() -> datetime`
- **Async:** No
- **Docstring:** Return current UTC time with timezone info.
- **Calls:** now

### `generate_uuid() -> str`
- **Async:** No
- **Docstring:** Generate a new UUID string.
- **Calls:** str, uuid4

## Classes

### `CusProviderType(str, Enum)`
- **Docstring:** Supported LLM provider types.

### `CusIntegrationStatus(str, Enum)`
- **Docstring:** Integration lifecycle status.

### `CusHealthState(str, Enum)`
- **Docstring:** Integration health state.

### `CusPolicyResult(str, Enum)`
- **Docstring:** Policy enforcement result for LLM calls.

### `CusIntegration(SQLModel)`
- **Docstring:** Customer LLM Provider Integration.
- **Methods:** enable, disable, mark_error, update_health, is_usable, is_deleted, has_budget_limit, has_token_limit, has_rate_limit
- **Class Variables:** id: str, tenant_id: str, name: str, provider_type: str, credential_ref: str, config: Optional[dict], status: str, health_state: str, health_checked_at: Optional[datetime], health_message: Optional[str], default_model: Optional[str], budget_limit_cents: int, token_limit_month: int, rate_limit_rpm: int, created_at: datetime, updated_at: datetime, created_by: Optional[str], deleted_at: Optional[datetime]

### `CusLLMUsage(SQLModel)`
- **Docstring:** Individual LLM Call Telemetry Record.
- **Methods:** total_tokens, is_error, was_blocked
- **Class Variables:** id: str, tenant_id: str, integration_id: str, session_id: Optional[str], agent_id: Optional[str], call_id: str, provider: str, model: str, tokens_in: int, tokens_out: int, cost_cents: int, latency_ms: Optional[int], policy_result: CusPolicyResult, error_code: Optional[str], error_message: Optional[str], extra_data: Optional[dict], created_at: datetime

### `CusUsageDaily(SQLModel)`
- **Docstring:** Pre-aggregated Daily Usage Statistics.
- **Methods:** total_tokens, success_rate, cost_dollars
- **Class Variables:** tenant_id: str, integration_id: str, date: DateType, total_calls: int, total_tokens_in: int, total_tokens_out: int, total_cost_cents: int, avg_latency_ms: Optional[int], error_count: int, blocked_count: int, updated_at: datetime

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `sqlalchemy`, `sqlalchemy.dialects.postgresql`, `sqlmodel` |

## Callers

cus_* services, cus_* APIs

## Export Contract

```yaml
exports:
  functions:
    - name: utc_now
      signature: "utc_now() -> datetime"
    - name: generate_uuid
      signature: "generate_uuid() -> str"
  classes:
    - name: CusProviderType
      methods: []
    - name: CusIntegrationStatus
      methods: []
    - name: CusHealthState
      methods: []
    - name: CusPolicyResult
      methods: []
    - name: CusIntegration
      methods: [enable, disable, mark_error, update_health, is_usable, is_deleted, has_budget_limit, has_token_limit, has_rate_limit]
    - name: CusLLMUsage
      methods: [total_tokens, is_error, was_blocked]
    - name: CusUsageDaily
      methods: [total_tokens, success_rate, cost_dollars]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
