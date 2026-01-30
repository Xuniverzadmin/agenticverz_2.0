# hoc_models_policy_scope

| Field | Value |
|-------|-------|
| Path | `backend/app/models/policy_scope.py` |
| Layer | L4 — Domain Engine |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

Define policy scope selectors for targeting runs by agent, API key, or human actor

## Intent

**Role:** Define policy scope selectors for targeting runs by agent, API key, or human actor
**Reference:** POLICY_CONTROL_LEVER_IMPLEMENTATION_PLAN.md PCL-001
**Callers:** policy/scope_resolver.py, api/policy_scopes.py

## Purpose

Policy Scope Model

---

## Classes

### `ScopeType(str, Enum)`
- **Docstring:** Type of scope selector.

### `PolicyScope(SQLModel)`
- **Docstring:** Scope selector that defines WHO a policy applies to.
- **Methods:** agent_ids, agent_ids, api_key_ids, api_key_ids, human_actor_ids, human_actor_ids, matches, to_snapshot, create_all_runs_scope, create_agent_scope, create_api_key_scope, create_human_actor_scope
- **Class Variables:** id: Optional[int], scope_id: str, policy_id: str, tenant_id: str, scope_type: str, agent_ids_json: Optional[str], api_key_ids_json: Optional[str], human_actor_ids_json: Optional[str], description: Optional[str], created_at: datetime, updated_at: datetime, created_by: Optional[str]

### `PolicyScopeCreate(BaseModel)`
- **Docstring:** Request model for creating a policy scope.
- **Class Variables:** policy_id: str, scope_type: ScopeType, agent_ids: Optional[list[str]], api_key_ids: Optional[list[str]], human_actor_ids: Optional[list[str]], description: Optional[str]

### `PolicyScopeUpdate(BaseModel)`
- **Docstring:** Request model for updating a policy scope.
- **Class Variables:** scope_type: Optional[ScopeType], agent_ids: Optional[list[str]], api_key_ids: Optional[list[str]], human_actor_ids: Optional[list[str]], description: Optional[str]

### `PolicyScopeResponse(BaseModel)`
- **Docstring:** Response model for policy scope.
- **Class Variables:** scope_id: str, policy_id: str, tenant_id: str, scope_type: ScopeType, agent_ids: list[str], api_key_ids: list[str], human_actor_ids: list[str], description: Optional[str], created_at: datetime, updated_at: datetime

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `pydantic`, `sqlmodel` |

## Callers

policy/scope_resolver.py, api/policy_scopes.py

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: ScopeType
      methods: []
    - name: PolicyScope
      methods: [agent_ids, agent_ids, api_key_ids, api_key_ids, human_actor_ids, human_actor_ids, matches, to_snapshot, create_all_runs_scope, create_agent_scope, create_api_key_scope, create_human_actor_scope]
    - name: PolicyScopeCreate
      methods: []
    - name: PolicyScopeUpdate
      methods: []
    - name: PolicyScopeResponse
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
