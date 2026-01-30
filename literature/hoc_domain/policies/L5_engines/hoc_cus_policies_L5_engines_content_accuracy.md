# hoc_cus_policies_L5_engines_content_accuracy

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/content_accuracy.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy content accuracy validation (pure logic)

## Intent

**Role:** Policy content accuracy validation (pure logic)
**Reference:** PIN-470, Policy System
**Callers:** policy/engine

## Purpose

_No module docstring._

---

## Functions

### `validate_content_accuracy(output: str, context: Dict[str, Any], user_query: Optional[str], strict_mode: bool) -> ContentAccuracyResult`
- **Async:** No
- **Docstring:** Convenience function to validate content accuracy.  Usage:
- **Calls:** ContentAccuracyValidator, validate

## Classes

### `AssertionType(str, Enum)`
- **Docstring:** Types of assertions detected in output.

### `ValidationResult(str, Enum)`
- **Docstring:** Result of content accuracy validation.

### `AssertionCheck`
- **Docstring:** A single assertion check result.
- **Class Variables:** field_name: str, assertion_type: AssertionType, field_value: Any, field_present: bool, output_claim: str, is_violation: bool, reason: Optional[str]

### `ContentAccuracyResult`
- **Docstring:** Complete result of content accuracy validation.
- **Methods:** to_dict
- **Class Variables:** result: ValidationResult, checks: List[AssertionCheck], violations: List[AssertionCheck], overall_reason: Optional[str], confidence: float, expected_behavior: Optional[str], actual_behavior: Optional[str]

### `ContentAccuracyValidator`
- **Docstring:** Validates that LLM output does not make assertions about missing data.
- **Methods:** __init__, validate, _detect_assertion_type, _get_nested_value, _extract_claim, _claims_affirmative

## Attributes

- `DEFINITIVE_PATTERNS` (line 104)
- `UNCERTAINTY_PATTERNS` (line 119)
- `HEDGED_PATTERNS` (line 135)
- `CONTRACT_TERMS` (line 149)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

policy/engine

## Export Contract

```yaml
exports:
  functions:
    - name: validate_content_accuracy
      signature: "validate_content_accuracy(output: str, context: Dict[str, Any], user_query: Optional[str], strict_mode: bool) -> ContentAccuracyResult"
  classes:
    - name: AssertionType
      methods: []
    - name: ValidationResult
      methods: []
    - name: AssertionCheck
      methods: []
    - name: ContentAccuracyResult
      methods: [to_dict]
    - name: ContentAccuracyValidator
      methods: [validate]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
