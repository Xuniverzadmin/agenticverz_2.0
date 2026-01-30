# hoc_models_override_authority

| Field | Value |
|-------|-------|
| Path | `backend/app/models/override_authority.py` |
| Layer | L4 — Domain Engine |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

Define emergency override rules for policies

## Intent

**Role:** Define emergency override rules for policies
**Reference:** POLICY_CONTROL_LEVER_IMPLEMENTATION_PLAN.md PCL-010
**Callers:** policy/prevention_engine.py, api/policy_overrides.py

## Purpose

Override Authority Model

---

## Classes

### `OverrideAuthority(SQLModel)`
- **Docstring:** Override authority configuration for a policy.
- **Methods:** allowed_roles, allowed_roles, can_override, is_override_active, apply_override, clear_override, reset_daily_count
- **Class Variables:** id: Optional[int], policy_id: str, tenant_id: str, override_allowed: bool, allowed_roles_json: str, requires_reason: bool, max_duration_seconds: int, max_overrides_per_day: int, currently_overridden: bool, override_started_at: Optional[datetime], override_expires_at: Optional[datetime], override_by: Optional[str], override_reason: Optional[str], total_overrides: int, overrides_today: int, last_override_date: Optional[datetime], created_at: datetime, updated_at: datetime

### `OverrideRecord(SQLModel)`
- **Docstring:** Immutable record of a policy override.
- **Methods:** create_record
- **Class Variables:** id: Optional[int], record_id: str, policy_id: str, tenant_id: str, run_id: Optional[str], override_by: str, override_role: str, reason: str, duration_seconds: int, started_at: datetime, expires_at: datetime, ended_at: Optional[datetime], was_manually_ended: bool, ended_by: Optional[str]

### `OverrideAuthorityCreate(BaseModel)`
- **Docstring:** Request model for creating override authority.
- **Class Variables:** policy_id: str, override_allowed: bool, allowed_roles: list[str], requires_reason: bool, max_duration_seconds: int, max_overrides_per_day: int

### `OverrideAuthorityUpdate(BaseModel)`
- **Docstring:** Request model for updating override authority.
- **Class Variables:** override_allowed: Optional[bool], allowed_roles: Optional[list[str]], requires_reason: Optional[bool], max_duration_seconds: Optional[int], max_overrides_per_day: Optional[int]

### `ApplyOverrideRequest(BaseModel)`
- **Docstring:** Request model for applying an override.
- **Class Variables:** reason: str, duration_seconds: Optional[int], run_id: Optional[str]

### `OverrideAuthorityResponse(BaseModel)`
- **Docstring:** Response model for override authority.
- **Class Variables:** policy_id: str, tenant_id: str, override_allowed: bool, allowed_roles: list[str], requires_reason: bool, max_duration_seconds: int, max_overrides_per_day: int, currently_overridden: bool, override_expires_at: Optional[datetime], override_by: Optional[str], total_overrides: int, overrides_today: int

### `OverrideRecordResponse(BaseModel)`
- **Docstring:** Response model for override record.
- **Class Variables:** record_id: str, policy_id: str, run_id: Optional[str], override_by: str, override_role: str, reason: str, duration_seconds: int, started_at: datetime, expires_at: datetime, ended_at: Optional[datetime], was_manually_ended: bool

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `pydantic`, `sqlmodel` |

## Callers

policy/prevention_engine.py, api/policy_overrides.py

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: OverrideAuthority
      methods: [allowed_roles, allowed_roles, can_override, is_override_active, apply_override, clear_override, reset_daily_count]
    - name: OverrideRecord
      methods: [create_record]
    - name: OverrideAuthorityCreate
      methods: []
    - name: OverrideAuthorityUpdate
      methods: []
    - name: ApplyOverrideRequest
      methods: []
    - name: OverrideAuthorityResponse
      methods: []
    - name: OverrideRecordResponse
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
