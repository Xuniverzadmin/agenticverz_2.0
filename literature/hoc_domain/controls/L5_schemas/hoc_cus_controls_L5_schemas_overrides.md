# hoc_cus_controls_L5_schemas_overrides

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/controls/L5_schemas/overrides.py` |
| Layer | L5 — Domain Schema |
| Domain | controls |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Limit override request/response schemas

## Intent

**Role:** Limit override request/response schemas
**Reference:** PIN-LIM-05
**Callers:** api/limits/override.py, services/limits/override_service.py

## Purpose

Limit Override Schemas (PIN-LIM-05)

---

## Classes

### `OverrideStatus(str, Enum)`
- **Docstring:** Override lifecycle status.

### `LimitOverrideRequest(BaseModel)`
- **Docstring:** Request model for requesting a temporary limit override.
- **Methods:** validate_override_value
- **Class Variables:** limit_id: str, override_value: Decimal, duration_hours: int, reason: str, start_immediately: bool, scheduled_start: Optional[datetime]

### `LimitOverrideResponse(BaseModel)`
- **Docstring:** Response model for limit override operations.
- **Class Variables:** override_id: str, limit_id: str, limit_name: str, tenant_id: str, original_value: Decimal, override_value: Decimal, effective_value: Decimal, status: OverrideStatus, requested_at: datetime, approved_at: Optional[datetime], starts_at: Optional[datetime], expires_at: Optional[datetime], requested_by: str, approved_by: Optional[str], reason: str, rejection_reason: Optional[str]

### `OverrideApprovalRequest(BaseModel)`
- **Docstring:** Request model for approving/rejecting an override.
- **Methods:** validate_rejection_reason
- **Class Variables:** approved: bool, adjusted_value: Optional[Decimal], adjusted_duration_hours: Optional[int], rejection_reason: Optional[str]

### `OverrideListResponse(BaseModel)`
- **Docstring:** Response model for listing overrides.
- **Class Variables:** items: list[LimitOverrideResponse], total: int, has_more: bool

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `pydantic` |

## Callers

api/limits/override.py, services/limits/override_service.py

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: OverrideStatus
      methods: []
    - name: LimitOverrideRequest
      methods: [validate_override_value]
    - name: LimitOverrideResponse
      methods: []
    - name: OverrideApprovalRequest
      methods: [validate_rejection_reason]
    - name: OverrideListResponse
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
