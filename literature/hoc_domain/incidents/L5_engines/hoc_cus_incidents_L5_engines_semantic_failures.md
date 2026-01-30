# hoc_cus_incidents_L5_engines_semantic_failures

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/incidents/L5_engines/semantic_failures.py` |
| Layer | L5 — Domain Engine |
| Domain | incidents |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Semantic failure taxonomy and fix guidance for incidents domain

## Intent

**Role:** Semantic failure taxonomy and fix guidance for incidents domain
**Reference:** PIN-470, PIN-420, INCIDENTS_PHASE2.5_IMPLEMENTATION_PLAN.md — Phase II.1
**Callers:** Panel adapters (L3), incident engines (L5)

## Purpose

Semantic Failures — Canonical failure taxonomy for two-phase validation.

---

## Functions

### `get_failure_info(code: FailureCode) -> Dict[str, Any]`
- **Async:** No
- **Docstring:** Get failure taxonomy info for a code (INT-* or SEM-*).
- **Calls:** get, hasattr, str

### `get_fix_owner(code: FailureCode) -> str`
- **Async:** No
- **Docstring:** Get the fix owner for a failure code.
- **Calls:** get, get_failure_info

### `get_fix_action(code: FailureCode) -> str`
- **Async:** No
- **Docstring:** Get the fix action for a failure code.
- **Calls:** get, get_failure_info

### `get_violation_class(code: FailureCode) -> ViolationClass`
- **Async:** No
- **Docstring:** Get the violation class for a failure code.
- **Calls:** get, get_failure_info

### `format_violation_message(code: FailureCode, context_msg: str) -> str`
- **Async:** No
- **Docstring:** Format a violation message with context.
- **Calls:** get_failure_info

## Attributes

- `FAILURE_TAXONOMY: Dict[str, Dict[str, Any]]` (line 69)
- `SEMANTIC_FAILURE_TAXONOMY` (line 257)
- `INTENT_FAILURE_TAXONOMY` (line 262)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `semantic_types` |

## Callers

Panel adapters (L3), incident engines (L5)

## Export Contract

```yaml
exports:
  functions:
    - name: get_failure_info
      signature: "get_failure_info(code: FailureCode) -> Dict[str, Any]"
    - name: get_fix_owner
      signature: "get_fix_owner(code: FailureCode) -> str"
    - name: get_fix_action
      signature: "get_fix_action(code: FailureCode) -> str"
    - name: get_violation_class
      signature: "get_violation_class(code: FailureCode) -> ViolationClass"
    - name: format_violation_message
      signature: "format_violation_message(code: FailureCode, context_msg: str) -> str"
  classes: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
