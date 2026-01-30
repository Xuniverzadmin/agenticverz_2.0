# hoc_cus_policies_L6_drivers_policy_read_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L6_drivers/policy_read_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Data access for customer policy read operations

## Intent

**Role:** Data access for customer policy read operations
**Reference:** PIN-470, PIN-281, PHASE2_EXTRACTION_PROTOCOL.md
**Callers:** policy engines (L5)

## Purpose

Policy Read Driver (L6)

---

## Functions

### `get_policy_read_driver(session: Session) -> PolicyReadDriver`
- **Async:** No
- **Docstring:** Get PolicyReadDriver instance.  Args:
- **Calls:** PolicyReadDriver

## Classes

### `TenantBudgetDataDTO(BaseModel)`
- **Docstring:** Raw tenant budget settings from database.
- **Class Variables:** tenant_id: str, budget_limit_cents: int, budget_period: str

### `UsageSumDTO(BaseModel)`
- **Docstring:** Raw usage sum from database.
- **Class Variables:** total_cents: int

### `GuardrailDTO(BaseModel)`
- **Docstring:** Raw guardrail data from database.
- **Class Variables:** id: str, name: str, description: Optional[str], is_enabled: bool, category: str, action: str, priority: int

### `PolicyReadDriver`
- **Docstring:** L6 driver for customer policy read operations.
- **Methods:** __init__, get_tenant_budget_settings, get_usage_sum_since, get_guardrail_by_id, list_all_guardrails, _to_guardrail_dto

## Attributes

- `__all__` (line 236)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.killswitch`, `app.models.tenant` |
| External | `pydantic`, `sqlalchemy`, `sqlmodel` |

## Callers

policy engines (L5)

## Export Contract

```yaml
exports:
  functions:
    - name: get_policy_read_driver
      signature: "get_policy_read_driver(session: Session) -> PolicyReadDriver"
  classes:
    - name: TenantBudgetDataDTO
      methods: []
    - name: UsageSumDTO
      methods: []
    - name: GuardrailDTO
      methods: []
    - name: PolicyReadDriver
      methods: [get_tenant_budget_settings, get_usage_sum_since, get_guardrail_by_id, list_all_guardrails]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
