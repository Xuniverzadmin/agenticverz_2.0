# hoc_cus_policies_L5_engines_visitors

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/visitors.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy AST visitor pattern implementations

## Intent

**Role:** Policy AST visitor pattern implementations
**Reference:** PIN-470, Policy System
**Callers:** policy/engine

## Purpose

AST visitors for PLang v2.0.

---

## Classes

### `BaseVisitor(ASTVisitor)`
- **Docstring:** Base visitor with default implementations.
- **Methods:** visit_program, visit_policy_decl, visit_rule_decl, visit_import, visit_rule_ref, visit_priority, visit_condition_block, visit_action_block, visit_route_target, visit_binary_op, visit_unary_op, visit_ident, visit_literal, visit_func_call, visit_attr_access

### `PrintVisitor(BaseVisitor)`
- **Docstring:** Visitor that prints AST in readable format.
- **Methods:** __init__, _emit, get_output, visit_program, visit_policy_decl, visit_rule_decl, visit_import, visit_rule_ref, visit_priority, visit_condition_block, visit_action_block, visit_route_target, visit_binary_op, visit_unary_op, visit_ident, visit_literal, visit_func_call, visit_attr_access

### `CategoryCollector(BaseVisitor)`
- **Docstring:** Visitor that collects all categories used in the AST.
- **Methods:** __init__, get_categories, visit_policy_decl, visit_rule_decl

### `RuleExtractor(BaseVisitor)`
- **Docstring:** Visitor that extracts all rules with their governance metadata.
- **Methods:** __init__, get_rules, visit_policy_decl, visit_rule_decl, visit_condition_block

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.policy.ast.nodes`, `app.policy.compiler.grammar` |

## Callers

policy/engine

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: BaseVisitor
      methods: [visit_program, visit_policy_decl, visit_rule_decl, visit_import, visit_rule_ref, visit_priority, visit_condition_block, visit_action_block, visit_route_target, visit_binary_op, visit_unary_op, visit_ident, visit_literal, visit_func_call, visit_attr_access]
    - name: PrintVisitor
      methods: [get_output, visit_program, visit_policy_decl, visit_rule_decl, visit_import, visit_rule_ref, visit_priority, visit_condition_block, visit_action_block, visit_route_target, visit_binary_op, visit_unary_op, visit_ident, visit_literal, visit_func_call, visit_attr_access]
    - name: CategoryCollector
      methods: [get_categories, visit_policy_decl, visit_rule_decl]
    - name: RuleExtractor
      methods: [get_rules, visit_policy_decl, visit_rule_decl, visit_condition_block]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
