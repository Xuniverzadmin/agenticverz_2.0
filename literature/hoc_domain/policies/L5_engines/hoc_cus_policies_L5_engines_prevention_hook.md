# hoc_cus_policies_L5_engines_prevention_hook

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/prevention_hook.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Prevention hook for policy enforcement

## Intent

**Role:** Prevention hook for policy enforcement
**Reference:** PIN-470, Policy System
**Callers:** workers, execution runtime

## Purpose

_No module docstring._

---

## Functions

### `create_prevention_hook(strict_mode: bool, block_on_fail: bool) -> PreventionHook`
- **Async:** No
- **Docstring:** Factory function to create a prevention hook.
- **Calls:** PreventionHook

### `get_prevention_hook() -> PreventionHook`
- **Async:** No
- **Docstring:** Get the global prevention hook instance.
- **Calls:** create_prevention_hook

### `evaluate_response(tenant_id: str, call_id: str, user_query: str, context_data: Dict[str, Any], llm_output: str, model: str, user_id: Optional[str]) -> PreventionResult`
- **Async:** No
- **Docstring:** Convenience function to evaluate an LLM response.  Usage:
- **Calls:** PreventionContext, evaluate, get_prevention_hook, len, split

## Classes

### `PreventionAction(str, Enum)`
- **Docstring:** Action to take when prevention hook triggers.

### `PreventionContext`
- **Docstring:** Context for prevention hook evaluation.
- **Methods:** __post_init__
- **Class Variables:** tenant_id: str, call_id: str, user_id: Optional[str], model: str, user_query: str, system_prompt: Optional[str], context_data: Dict[str, Any], llm_output: str, output_tokens: int, timestamp: Optional[datetime]

### `PreventionResult`
- **Docstring:** Result of prevention hook evaluation.
- **Methods:** __post_init__, to_dict
- **Class Variables:** action: PreventionAction, policy: str, result: str, reason: Optional[str], modified_output: Optional[str], expected_behavior: Optional[str], actual_behavior: Optional[str], evaluation_id: Optional[str], evaluation_ms: int

### `PreventionHook`
- **Docstring:** Prevention hook for pre-response validation.
- **Methods:** __init__, evaluate, get_safe_response

## Attributes

- `_prevention_hook: Optional[PreventionHook]` (line 252)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.policy.validators.content_accuracy` |

## Callers

workers, execution runtime

## Export Contract

```yaml
exports:
  functions:
    - name: create_prevention_hook
      signature: "create_prevention_hook(strict_mode: bool, block_on_fail: bool) -> PreventionHook"
    - name: get_prevention_hook
      signature: "get_prevention_hook() -> PreventionHook"
    - name: evaluate_response
      signature: "evaluate_response(tenant_id: str, call_id: str, user_query: str, context_data: Dict[str, Any], llm_output: str, model: str, user_id: Optional[str]) -> PreventionResult"
  classes:
    - name: PreventionAction
      methods: []
    - name: PreventionContext
      methods: []
    - name: PreventionResult
      methods: [to_dict]
    - name: PreventionHook
      methods: [evaluate, get_safe_response]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
