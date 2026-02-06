# hoc_cus_logs_L5_engines_completeness_checker

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L5_engines/completeness_checker.py` |
| Layer | L5 — Domain Engine |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Evidence PDF completeness validation for SOC2 compliance

## Intent

**Role:** Evidence PDF completeness validation for SOC2 compliance
**Reference:** PIN-470, GAP-027 (Evidence PDF Completeness)
**Callers:** pdf_renderer, evidence_report, export APIs

## Purpose

Module: completeness_checker
Purpose: Validate evidence bundle completeness before PDF generation.

---

## Functions

### `check_evidence_completeness(bundle: Any, export_type: str, validation_enabled: bool, strict_mode: bool) -> CompletenessCheckResponse`
- **Async:** No
- **Docstring:** Quick helper to check evidence completeness.  Args:
- **Calls:** EvidenceCompletenessChecker, check

### `ensure_evidence_completeness(bundle: Any, export_type: str, validation_enabled: bool, strict_mode: bool) -> None`
- **Async:** No
- **Docstring:** Quick helper to ensure evidence completeness or raise error.  Args:
- **Calls:** EvidenceCompletenessChecker, ensure_complete

## Classes

### `CompletenessCheckResult(str, Enum)`
- **Docstring:** Result of a completeness check.

### `EvidenceCompletenessError(Exception)`
- **Docstring:** Raised when evidence bundle is incomplete for PDF generation.
- **Methods:** __init__, to_dict

### `CompletenessCheckResponse`
- **Docstring:** Response from a completeness check.
- **Methods:** to_dict
- **Class Variables:** result: CompletenessCheckResult, is_complete: bool, validation_enabled: bool, export_type: str, missing_required: Set[str], missing_recommended: Set[str], completeness_percentage: float, message: str

### `EvidenceCompletenessChecker`
- **Docstring:** Checks evidence bundle completeness before PDF generation.
- **Methods:** __init__, from_governance_config, validation_enabled, strict_mode, get_required_fields, get_field_value, is_field_present, check, ensure_complete, should_allow_export, get_completeness_summary

## Attributes

- `REQUIRED_EVIDENCE_FIELDS: FrozenSet[str]` (line 57)
- `SOC2_REQUIRED_FIELDS: FrozenSet[str]` (line 73)
- `RECOMMENDED_FIELDS: FrozenSet[str]` (line 81)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

pdf_renderer, evidence_report, export APIs

## Export Contract

```yaml
exports:
  functions:
    - name: check_evidence_completeness
      signature: "check_evidence_completeness(bundle: Any, export_type: str, validation_enabled: bool, strict_mode: bool) -> CompletenessCheckResponse"
    - name: ensure_evidence_completeness
      signature: "ensure_evidence_completeness(bundle: Any, export_type: str, validation_enabled: bool, strict_mode: bool) -> None"
  classes:
    - name: CompletenessCheckResult
      methods: []
    - name: EvidenceCompletenessError
      methods: [to_dict]
    - name: CompletenessCheckResponse
      methods: [to_dict]
    - name: EvidenceCompletenessChecker
      methods: [from_governance_config, validation_enabled, strict_mode, get_required_fields, get_field_value, is_field_present, check, ensure_complete, should_allow_export, get_completeness_summary]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
