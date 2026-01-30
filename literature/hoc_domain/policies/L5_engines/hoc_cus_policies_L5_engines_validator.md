# hoc_cus_policies_L5_engines_validator

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/validator.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy DSL semantic validator (pure validation logic)

## Intent

**Role:** Policy DSL semantic validator (pure validation logic)
**Reference:** PIN-470, PIN-341 Section 1.8, PIN-345
**Callers:** policy engine

## Purpose

Policy DSL Semantic Validator

---

## Functions

### `validate(policy: PolicyAST, allowed_metrics: set[str] | None) -> ValidationResult`
- **Async:** No
- **Docstring:** Validate a policy AST.  Args:
- **Calls:** PolicyValidator, validate

### `is_valid(policy: PolicyAST, allowed_metrics: set[str] | None) -> bool`
- **Async:** No
- **Docstring:** Quick check if a policy is valid.  Args:
- **Calls:** validate

## Classes

### `Severity(str, Enum)`
- **Docstring:** Severity level for validation issues.

### `ValidationIssue`
- **Docstring:** A single validation issue found in the policy.
- **Methods:** __str__
- **Class Variables:** code: str, message: str, severity: Severity, path: str

### `ValidationResult`
- **Docstring:** Result of policy validation.
- **Methods:** __post_init__, errors, warnings, __bool__
- **Class Variables:** issues: tuple[ValidationIssue, ...], is_valid: bool

### `PolicyValidator`
- **Docstring:** Validates PolicyAST against semantic rules.
- **Methods:** __init__, validate, _validate_mode_enforcement, _validate_metrics, _extract_metrics, _validate_structure, _check_warnings

## Attributes

- `V001` (line 126)
- `V002` (line 127)
- `V010` (line 130)
- `V020` (line 133)
- `V021` (line 134)
- `W001` (line 137)
- `W002` (line 138)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__`, `app.dsl.ast` |

## Callers

policy engine

## Export Contract

```yaml
exports:
  functions:
    - name: validate
      signature: "validate(policy: PolicyAST, allowed_metrics: set[str] | None) -> ValidationResult"
    - name: is_valid
      signature: "is_valid(policy: PolicyAST, allowed_metrics: set[str] | None) -> bool"
  classes:
    - name: Severity
      methods: []
    - name: ValidationIssue
      methods: []
    - name: ValidationResult
      methods: [errors, warnings]
    - name: PolicyValidator
      methods: [validate]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
