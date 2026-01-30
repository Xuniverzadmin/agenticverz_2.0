# hoc_cus_policies_L6_drivers_optimizer_conflict_resolver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L6_drivers/optimizer_conflict_resolver.py` |
| Layer | L6 — Domain Driver |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy conflict resolution

## Intent

**Role:** Policy conflict resolution
**Reference:** PIN-470, Policy System
**Callers:** policy/engine

## Purpose

Conflict resolution for PLang v2.0.

---

## Classes

### `ConflictType(Enum)`
- **Docstring:** Types of policy conflicts.

### `PolicyConflict`
- **Docstring:** A detected conflict between policies.
- **Methods:** __str__
- **Class Variables:** conflict_type: ConflictType, policies: List[str], description: str, severity: int, resolution: Optional[str], resolved: bool, winner: Optional[str]

### `ConflictResolver`
- **Docstring:** Resolves conflicts between policies.
- **Methods:** __init__, resolve, _detect_action_conflicts, _detect_priority_conflicts, _detect_category_conflicts, _detect_circular_dependencies, _get_condition_signature, _might_override, _get_actions, _resolve_conflict, _resolve_action_conflict, _resolve_priority_conflict, _resolve_category_conflict, _resolve_circular_conflict

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.policy.compiler.grammar`, `app.policy.ir.ir_nodes` |

## Callers

policy/engine

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: ConflictType
      methods: []
    - name: PolicyConflict
      methods: []
    - name: ConflictResolver
      methods: [resolve]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
