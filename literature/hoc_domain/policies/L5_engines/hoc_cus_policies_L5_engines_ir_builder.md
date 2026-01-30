# hoc_cus_policies_L5_engines_ir_builder

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/ir_builder.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy intermediate representation builder

## Intent

**Role:** Policy intermediate representation builder
**Reference:** PIN-470, Policy System
**Callers:** policy/engine

## Purpose

IR Builder for PLang v2.0.

---

## Classes

### `IRBuilder(BaseVisitor)`
- **Docstring:** Builds IR from PLang AST.
- **Methods:** __init__, build, _next_id, _next_block_name, _emit, _new_block, visit_program, visit_policy_decl, visit_rule_decl, visit_import, visit_rule_ref, visit_priority, visit_condition_block, visit_action_block, visit_route_target, visit_binary_op, visit_unary_op, visit_ident, visit_literal, visit_func_call, visit_attr_access

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.policy.ast.nodes`, `app.policy.ast.visitors`, `app.policy.compiler.grammar`, `app.policy.ir.ir_nodes`, `app.policy.ir.symbol_table` |

## Callers

policy/engine

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: IRBuilder
      methods: [build, visit_program, visit_policy_decl, visit_rule_decl, visit_import, visit_rule_ref, visit_priority, visit_condition_block, visit_action_block, visit_route_target, visit_binary_op, visit_unary_op, visit_ident, visit_literal, visit_func_call, visit_attr_access]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
