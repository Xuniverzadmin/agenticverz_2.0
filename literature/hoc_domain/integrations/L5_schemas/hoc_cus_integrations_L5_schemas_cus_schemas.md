# hoc_cus_integrations_L5_schemas_cus_schemas

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_schemas/cus_schemas.py` |
| Layer | L6 — Platform Substrate (Schemas) |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Pydantic schemas for Customer Integration domain (LLM BYOK, SDK, RAG)

## Intent

**Role:** Pydantic schemas for Customer Integration domain (LLM BYOK, SDK, RAG)
**Reference:** Connectivity Domain - Customer Console v1 Constitution
**Callers:** aos_cus_integrations.py, cus_telemetry.py APIs

## Purpose

Customer Integrations API Schemas

---

## Classes

### `CusIntegrationCreate(BaseModel)`
- **Docstring:** Request schema for creating a new integration.
- **Methods:** validate_not_raw_key
- **Class Variables:** name: str, provider_type: CusProviderType, credential_ref: str, config: Dict[str, Any], default_model: Optional[str], budget_limit_cents: int, token_limit_month: int, rate_limit_rpm: int

### `CusIntegrationUpdate(BaseModel)`
- **Docstring:** Request schema for updating an integration.
- **Methods:** validate_not_raw_key
- **Class Variables:** name: Optional[str], credential_ref: Optional[str], config: Optional[Dict[str, Any]], default_model: Optional[str], budget_limit_cents: Optional[int], token_limit_month: Optional[int], rate_limit_rpm: Optional[int]

### `CusLLMUsageIngest(BaseModel)`
- **Docstring:** Request schema for SDK telemetry ingestion.
- **Class Variables:** integration_id: str, call_id: str, session_id: Optional[str], agent_id: Optional[str], provider: str, model: str, tokens_in: int, tokens_out: int, cost_cents: int, latency_ms: Optional[int], policy_result: CusPolicyResult, error_code: Optional[str], error_message: Optional[str], metadata: Dict[str, Any]

### `CusLLMUsageBatchIngest(BaseModel)`
- **Docstring:** Request schema for batch telemetry ingestion.
- **Class Variables:** records: List[CusLLMUsageIngest]

### `CusIntegrationResponse(BaseModel)`
- **Docstring:** Full integration details response.
- **Class Variables:** id: str, tenant_id: str, name: str, provider_type: CusProviderType, status: CusIntegrationStatus, health_state: CusHealthState, health_checked_at: Optional[datetime], health_message: Optional[str], default_model: Optional[str], budget_limit_cents: int, token_limit_month: int, rate_limit_rpm: int, created_at: datetime, updated_at: datetime, created_by: Optional[str]

### `CusIntegrationSummary(BaseModel)`
- **Docstring:** Integration summary for list views.
- **Class Variables:** id: str, name: str, provider_type: CusProviderType, status: CusIntegrationStatus, health_state: CusHealthState, default_model: Optional[str], created_at: datetime

### `CusLimitsStatus(BaseModel)`
- **Docstring:** Current usage vs configured limits.
- **Class Variables:** integration_id: str, integration_name: str, budget_limit_cents: int, budget_used_cents: int, budget_percent: float, token_limit_month: int, tokens_used_month: int, token_percent: float, rate_limit_rpm: int, current_rpm: int, rate_percent: float, period_start: date, period_end: date

### `CusUsageSummary(BaseModel)`
- **Docstring:** Aggregated usage statistics.
- **Class Variables:** tenant_id: str, period_start: date, period_end: date, total_calls: int, total_tokens_in: int, total_tokens_out: int, total_cost_cents: int, avg_latency_ms: Optional[int], error_count: int, blocked_count: int, by_integration: Optional[List['CusIntegrationUsage']]

### `CusIntegrationUsage(BaseModel)`
- **Docstring:** Usage for a single integration within a period.
- **Class Variables:** integration_id: str, integration_name: str, provider_type: CusProviderType, total_calls: int, total_tokens: int, total_cost_cents: int, error_count: int

### `CusLLMUsageResponse(BaseModel)`
- **Docstring:** Individual usage record response.
- **Class Variables:** id: str, integration_id: str, call_id: str, session_id: Optional[str], agent_id: Optional[str], provider: str, model: str, tokens_in: int, tokens_out: int, cost_cents: int, latency_ms: Optional[int], policy_result: CusPolicyResult, error_code: Optional[str], error_message: Optional[str], created_at: datetime

### `CusHealthCheckResponse(BaseModel)`
- **Docstring:** Response from integration health check.
- **Class Variables:** integration_id: str, health_state: CusHealthState, message: Optional[str], latency_ms: Optional[int], checked_at: datetime

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.cus_models` |
| External | `pydantic` |

## Callers

aos_cus_integrations.py, cus_telemetry.py APIs

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: CusIntegrationCreate
      methods: [validate_not_raw_key]
    - name: CusIntegrationUpdate
      methods: [validate_not_raw_key]
    - name: CusLLMUsageIngest
      methods: []
    - name: CusLLMUsageBatchIngest
      methods: []
    - name: CusIntegrationResponse
      methods: []
    - name: CusIntegrationSummary
      methods: []
    - name: CusLimitsStatus
      methods: []
    - name: CusUsageSummary
      methods: []
    - name: CusIntegrationUsage
      methods: []
    - name: CusLLMUsageResponse
      methods: []
    - name: CusHealthCheckResponse
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
