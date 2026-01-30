# hoc_cus_policies_L5_engines_intent

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/intent.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy intent model and declaration

## Intent

**Role:** Policy intent model and declaration
**Reference:** PIN-470, Policy System
**Callers:** policy engine, evaluators

## Purpose

Intent system for PLang v2.0 runtime.

---

## Classes

### `IntentType(Enum)`
- **Docstring:** Types of intents emitted by policy runtime.

### `IntentPayload`
- **Docstring:** Payload data for an intent.
- **Methods:** to_dict, from_dict
- **Class Variables:** target_agent: Optional[str], target_skill: Optional[str], request_id: Optional[str], user_id: Optional[str], budget_limit: Optional[float], time_limit_ms: Optional[int], retry_limit: int, context: Dict[str, Any], reason: Optional[str], alternatives: List[str]

### `Intent`
- **Docstring:** An intent emitted by the policy runtime.
- **Methods:** __post_init__, _generate_id, to_dict, from_dict
- **Class Variables:** id: str, intent_type: IntentType, payload: IntentPayload, priority: int, requires_confirmation: bool, source_policy: Optional[str], source_rule: Optional[str], category: Optional[str], created_at: str, expires_at: Optional[str], validated: bool, validation_errors: List[str]

### `IntentEmitter`
- **Docstring:** Emits intents from policy runtime to M18.
- **Methods:** __init__, create_intent, validate_intent, emit, emit_all, register_handler, get_pending, get_emitted, clear

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

policy engine, evaluators

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: IntentType
      methods: []
    - name: IntentPayload
      methods: [to_dict, from_dict]
    - name: Intent
      methods: [to_dict, from_dict]
    - name: IntentEmitter
      methods: [create_intent, validate_intent, emit, emit_all, register_handler, get_pending, get_emitted, clear]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
