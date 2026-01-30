# hoc_cus_policies_L5_engines_authority_checker

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/authority_checker.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Check override authority before policy enforcement

## Intent

**Role:** Check override authority before policy enforcement
**Reference:** PIN-470, GAP-034 (Override Authority Integration)
**Callers:** policy/prevention_engine.py, services/enforcement/

## Purpose

Module: authority_checker
Purpose: Check override authority status for prevention engine.

---

## Functions

### `should_skip_enforcement(override_authority: Any) -> bool`
- **Async:** No
- **Docstring:** Quick helper to check if enforcement should be skipped.  Args:
- **Calls:** OverrideAuthorityChecker, check

## Classes

### `OverrideStatus(str, Enum)`
- **Docstring:** Status of an override check.

### `OverrideCheckResult`
- **Docstring:** Result of an override authority check.
- **Methods:** to_dict
- **Class Variables:** status: OverrideStatus, skip_enforcement: bool, policy_id: str, override_by: Optional[str], override_reason: Optional[str], override_started_at: Optional[datetime], override_expires_at: Optional[datetime], remaining_seconds: Optional[int]

### `OverrideAuthorityChecker`
- **Docstring:** Checks override authority status for the prevention engine.
- **Methods:** check, _is_override_active, check_from_dict

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

policy/prevention_engine.py, services/enforcement/

## Export Contract

```yaml
exports:
  functions:
    - name: should_skip_enforcement
      signature: "should_skip_enforcement(override_authority: Any) -> bool"
  classes:
    - name: OverrideStatus
      methods: []
    - name: OverrideCheckResult
      methods: [to_dict]
    - name: OverrideAuthorityChecker
      methods: [check, check_from_dict]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
