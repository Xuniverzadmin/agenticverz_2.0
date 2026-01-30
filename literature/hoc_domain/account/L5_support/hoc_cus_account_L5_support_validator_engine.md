# hoc_cus_account_L5_support_validator_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/account/L5_support/CRM/engines/validator_engine.py` |
| Layer | L4 — Domain Engine |
| Domain | account |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Issue Validator engine - pure analysis, advisory verdicts

## Intent

**Role:** Issue Validator engine - pure analysis, advisory verdicts
**Reference:** VALIDATOR_LOGIC.md (frozen), part2-design-v1
**Callers:** L3 (adapters), L2 (governance APIs)

## Purpose

Part-2 Validator Service (L4)

---

## Classes

### `IssueType(str, Enum)`
- **Docstring:** Issue type classification.

### `Severity(str, Enum)`
- **Docstring:** Issue severity classification.

### `RecommendedAction(str, Enum)`
- **Docstring:** Recommended action from validator.

### `IssueSource(str, Enum)`
- **Docstring:** Issue source for confidence weighting.

### `ValidatorInput`
- **Docstring:** Input to the validator.
- **Class Variables:** issue_id: UUID, source: str, raw_payload: dict[str, Any], received_at: datetime, tenant_id: Optional[UUID], affected_capabilities_hint: Optional[list[str]], priority_hint: Optional[str]

### `ValidatorVerdict`
- **Docstring:** Output from the validator.
- **Class Variables:** issue_type: IssueType, severity: Severity, affected_capabilities: tuple[str, ...], recommended_action: RecommendedAction, confidence_score: Decimal, reason: str, evidence: dict[str, Any], analyzed_at: datetime, validator_version: str

### `ValidatorErrorType(str, Enum)`
- **Docstring:** Error types for validator failures.

### `ValidatorError`
- **Docstring:** Error from validator with fallback verdict.
- **Class Variables:** error_type: ValidatorErrorType, message: str, fallback_verdict: ValidatorVerdict

### `ValidatorService`
- **Docstring:** Part-2 Validator Service (L4)
- **Methods:** __init__, validate, _do_validate, _extract_text, _classify_issue_type, _classify_severity, _find_severity_indicators, _extract_capabilities, _get_source_weight, _get_capability_confidence, _calculate_confidence, _determine_action, _build_reason, _create_fallback_verdict

## Attributes

- `VALIDATOR_VERSION` (line 78)
- `CAPABILITY_REQUEST_KEYWORDS` (line 231)
- `BUG_REPORT_KEYWORDS` (line 246)
- `CONFIGURATION_KEYWORDS` (line 261)
- `ESCALATION_KEYWORDS` (line 275)
- `CRITICAL_INDICATORS` (line 290)
- `HIGH_INDICATORS` (line 302)
- `LOW_INDICATORS` (line 312)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

L3 (adapters), L2 (governance APIs)

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: IssueType
      methods: []
    - name: Severity
      methods: []
    - name: RecommendedAction
      methods: []
    - name: IssueSource
      methods: []
    - name: ValidatorInput
      methods: []
    - name: ValidatorVerdict
      methods: []
    - name: ValidatorErrorType
      methods: []
    - name: ValidatorError
      methods: []
    - name: ValidatorService
      methods: [validate]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
