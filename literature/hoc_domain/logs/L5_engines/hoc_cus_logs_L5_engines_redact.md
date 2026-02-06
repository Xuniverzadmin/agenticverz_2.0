# hoc_cus_logs_L5_engines_redact

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L5_engines/redact.py` |
| Layer | L5 — Domain Engine |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Trace data redaction for security

## Intent

**Role:** Trace data redaction for security
**Reference:** PIN-470, Trace System
**Callers:** trace store

## Purpose

PII Redaction Utility for Trace Storage
M8 Deliverable: Secure trace storage with PII masking

---

## Functions

### `redact_json_string(json_str: str) -> str`
- **Async:** No
- **Docstring:** Apply PII redaction patterns to a JSON string.  Args:
- **Calls:** sub

### `redact_dict(data: dict[str, Any], depth: int, max_depth: int) -> dict[str, Any]`
- **Async:** No
- **Docstring:** Recursively redact sensitive fields in a dictionary.  Args:
- **Calls:** isinstance, items, lower, redact_dict, redact_list, redact_string_value

### `redact_list(data: list[Any], depth: int, max_depth: int) -> list[Any]`
- **Async:** No
- **Docstring:** Recursively redact sensitive fields in a list.
- **Calls:** append, isinstance, redact_dict, redact_list, redact_string_value

### `redact_string_value(value: str) -> str`
- **Async:** No
- **Docstring:** Redact sensitive patterns in a string value.
- **Calls:** lower, search, sub

### `redact_trace_data(trace: dict[str, Any]) -> dict[str, Any]`
- **Async:** No
- **Docstring:** Redact PII from a complete trace object.  This is the main entry point for trace redaction.
- **Calls:** deepcopy, isinstance, redact_dict, redact_list

### `is_sensitive_field(field_name: str) -> bool`
- **Async:** No
- **Docstring:** Check if a field name indicates sensitive data.
- **Calls:** lower

### `add_sensitive_field(field_name: str) -> None`
- **Async:** No
- **Docstring:** Add a custom field name to the sensitive fields set.
- **Calls:** add, lower

### `add_redaction_pattern(pattern: str, replacement: str) -> None`
- **Async:** No
- **Docstring:** Add a custom redaction pattern.
- **Calls:** append, compile

## Attributes

- `PII_PATTERNS` (line 44)
- `SENSITIVE_FIELD_NAMES` (line 79)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

trace store

## Export Contract

```yaml
exports:
  functions:
    - name: redact_json_string
      signature: "redact_json_string(json_str: str) -> str"
    - name: redact_dict
      signature: "redact_dict(data: dict[str, Any], depth: int, max_depth: int) -> dict[str, Any]"
    - name: redact_list
      signature: "redact_list(data: list[Any], depth: int, max_depth: int) -> list[Any]"
    - name: redact_string_value
      signature: "redact_string_value(value: str) -> str"
    - name: redact_trace_data
      signature: "redact_trace_data(trace: dict[str, Any]) -> dict[str, Any]"
    - name: is_sensitive_field
      signature: "is_sensitive_field(field_name: str) -> bool"
    - name: add_sensitive_field
      signature: "add_sensitive_field(field_name: str) -> None"
    - name: add_redaction_pattern
      signature: "add_redaction_pattern(pattern: str, replacement: str) -> None"
  classes: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
