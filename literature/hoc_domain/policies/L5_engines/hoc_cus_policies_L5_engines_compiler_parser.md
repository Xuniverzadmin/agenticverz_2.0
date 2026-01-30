# hoc_cus_policies_L5_engines_compiler_parser

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/compiler_parser.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy language parser

## Intent

**Role:** Policy language parser
**Reference:** PIN-470, Policy System
**Callers:** policy/engine

## Purpose

Parser for PLang v2.0 with M19 category support.

---

## Classes

### `ParseError(Exception)`
- **Docstring:** Error during parsing.
- **Methods:** __init__

### `Parser`
- **Docstring:** Parser for PLang v2.0.
- **Methods:** __init__, from_source, current, peek, advance, expect, match, parse, parse_policy_decl, parse_category, parse_policy_body, parse_rule_decl, parse_rule_body, parse_rule_ref, parse_condition_block, parse_action_block, parse_route_target, parse_priority, parse_import, parse_expr, parse_or_expr, parse_and_expr, parse_not_expr, parse_comparison, parse_value, parse_func_call

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.policy.ast.nodes`, `app.policy.compiler.grammar`, `app.policy.compiler.tokenizer` |

## Callers

policy/engine

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: ParseError
      methods: []
    - name: Parser
      methods: [from_source, current, peek, advance, expect, match, parse, parse_policy_decl, parse_category, parse_policy_body, parse_rule_decl, parse_rule_body, parse_rule_ref, parse_condition_block, parse_action_block, parse_route_target, parse_priority, parse_import, parse_expr, parse_or_expr, parse_and_expr, parse_not_expr, parse_comparison, parse_value, parse_func_call]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
