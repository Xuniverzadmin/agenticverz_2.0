# hoc_cus_policies_L5_engines_grammar

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/grammar.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy language grammar definitions (pure definitions)

## Intent

**Role:** Policy language grammar definitions (pure definitions)
**Reference:** PIN-470, Policy System
**Callers:** policy/compiler/parser

## Purpose

PLang v2.0 Grammar (EBNF):

---

## Classes

### `GrammarNodeType(Enum)`
- **Docstring:** Grammar node types for PLang v2.0.

### `PolicyCategory(Enum)`
- **Docstring:** M19 Policy Categories.

### `ActionType(Enum)`
- **Docstring:** Policy action types.

### `GrammarProduction`
- **Docstring:** A production rule in the grammar.
- **Class Variables:** name: str, node_type: GrammarNodeType, alternatives: List[List[str]], is_terminal: bool

### `PLangGrammar`
- **Docstring:** PLang v2.0 Grammar Definition.
- **Methods:** get_category_priority, get_action_precedence, is_keyword, is_operator, is_category, is_action
- **Class Variables:** KEYWORDS: Set[str], OPERATORS: Set[str], CATEGORY_PRIORITY: Dict[str, int], ACTION_PRECEDENCE: Dict[str, int]

## Attributes

- `PLANG_GRAMMAR` (line 216)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

policy/compiler/parser

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: GrammarNodeType
      methods: []
    - name: PolicyCategory
      methods: []
    - name: ActionType
      methods: []
    - name: GrammarProduction
      methods: []
    - name: PLangGrammar
      methods: [get_category_priority, get_action_precedence, is_keyword, is_operator, is_category, is_action]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
