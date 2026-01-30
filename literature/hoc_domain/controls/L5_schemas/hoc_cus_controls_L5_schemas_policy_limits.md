# hoc_cus_controls_L5_schemas_policy_limits

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/controls/L5_schemas/policy_limits.py` |
| Layer | L5 — Domain Schema |
| Domain | controls |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy limits request/response schemas

## Intent

**Role:** Policy limits request/response schemas
**Reference:** PIN-LIM-01
**Callers:** api/policies.py, services/limits/policy_limits_service.py

## Purpose

Policy Limits Schemas (PIN-LIM-01)

---

## Classes

### `LimitCategoryEnum(str, Enum)`
- **Docstring:** Limit categories.

### `LimitScopeEnum(str, Enum)`
- **Docstring:** Limit scope levels.

### `LimitEnforcementEnum(str, Enum)`
- **Docstring:** Limit enforcement behaviors.

### `ResetPeriodEnum(str, Enum)`
- **Docstring:** Budget limit reset periods.

### `CreatePolicyLimitRequest(BaseModel)`
- **Docstring:** Request model for creating a policy limit.
- **Methods:** validate_reset_period, validate_window_seconds
- **Class Variables:** name: str, description: Optional[str], limit_category: LimitCategoryEnum, limit_type: str, scope: LimitScopeEnum, scope_id: Optional[str], max_value: Decimal, enforcement: LimitEnforcementEnum, reset_period: Optional[ResetPeriodEnum], window_seconds: Optional[int]

### `UpdatePolicyLimitRequest(BaseModel)`
- **Docstring:** Request model for updating a policy limit.
- **Class Variables:** name: Optional[str], description: Optional[str], max_value: Optional[Decimal], enforcement: Optional[LimitEnforcementEnum], reset_period: Optional[ResetPeriodEnum], window_seconds: Optional[int], status: Optional[str]

### `PolicyLimitResponse(BaseModel)`
- **Docstring:** Response model for policy limit operations.
- **Class Variables:** limit_id: str, tenant_id: str, name: str, description: Optional[str], limit_category: str, limit_type: str, scope: str, scope_id: Optional[str], max_value: Decimal, enforcement: str, status: str, reset_period: Optional[str], window_seconds: Optional[int], created_at: datetime, updated_at: datetime

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `pydantic` |

## Callers

api/policies.py, services/limits/policy_limits_service.py

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: LimitCategoryEnum
      methods: []
    - name: LimitScopeEnum
      methods: []
    - name: LimitEnforcementEnum
      methods: []
    - name: ResetPeriodEnum
      methods: []
    - name: CreatePolicyLimitRequest
      methods: [validate_reset_period, validate_window_seconds]
    - name: UpdatePolicyLimitRequest
      methods: []
    - name: PolicyLimitResponse
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
