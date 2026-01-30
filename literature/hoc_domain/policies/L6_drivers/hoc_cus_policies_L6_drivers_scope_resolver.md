# hoc_cus_policies_L6_drivers_scope_resolver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L6_drivers/scope_resolver.py` |
| Layer | L6 — Domain Driver |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Resolve which policies apply to a given run context

## Intent

**Role:** Resolve which policies apply to a given run context
**Reference:** PIN-470, POLICY_CONTROL_LEVER_IMPLEMENTATION_PLAN.md PCL-002
**Callers:** policy/prevention_engine.py, worker/runner.py

## Purpose

Scope Resolver Engine

---

## Functions

### `get_scope_resolver() -> ScopeResolver`
- **Async:** No
- **Docstring:** Get or create ScopeResolver singleton.
- **Calls:** ScopeResolver

## Classes

### `RunContext`
- **Docstring:** Context for scope resolution.
- **Class Variables:** tenant_id: str, agent_id: Optional[str], api_key_id: Optional[str], human_actor_id: Optional[str], run_id: Optional[str]

### `ScopeResolutionResult`
- **Docstring:** Result of scope resolution.
- **Methods:** to_snapshot
- **Class Variables:** matching_policy_ids: list[str], all_runs_policies: list[str], agent_policies: list[str], api_key_policies: list[str], human_actor_policies: list[str], context: RunContext, scopes_evaluated: int, resolution_timestamp: str

### `ScopeResolver`
- **Docstring:** Resolves which policies apply to a given run context.
- **Methods:** __init__, resolve_applicable_policies, _load_scopes, matches_scope, get_scope_for_policy, _get_scope

## Attributes

- `logger` (line 44)
- `_scope_resolver: Optional[ScopeResolver]` (line 251)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.policy_scope` |
| External | `app.db`, `sqlmodel` |

## Callers

policy/prevention_engine.py, worker/runner.py

## Export Contract

```yaml
exports:
  functions:
    - name: get_scope_resolver
      signature: "get_scope_resolver() -> ScopeResolver"
  classes:
    - name: RunContext
      methods: []
    - name: ScopeResolutionResult
      methods: [to_snapshot]
    - name: ScopeResolver
      methods: [resolve_applicable_policies, matches_scope, get_scope_for_policy]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
