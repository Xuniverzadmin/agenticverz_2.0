# hoc_cus_policies_L5_engines_ast

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/ast.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy DSL AST node definitions (immutable, typed)

## Intent

**Role:** Policy DSL AST node definitions (immutable, typed)
**Reference:** PIN-470, PIN-341 Section 1.8, PIN-345
**Callers:** policy/compiler, policy/engine

## Purpose

Policy DSL Abstract Syntax Tree (AST) Definitions

---

## Functions

### `is_predicate(condition: Condition) -> bool`
- **Async:** No
- **Docstring:** Check if condition is a simple predicate.
- **Calls:** isinstance

### `is_exists_predicate(condition: Condition) -> bool`
- **Async:** No
- **Docstring:** Check if condition is an exists predicate.
- **Calls:** isinstance

### `is_logical_condition(condition: Condition) -> bool`
- **Async:** No
- **Docstring:** Check if condition is a compound logical condition.
- **Calls:** isinstance

### `is_warn_action(action: Action) -> bool`
- **Async:** No
- **Docstring:** Check if action is a WARN action.
- **Calls:** isinstance

### `is_block_action(action: Action) -> bool`
- **Async:** No
- **Docstring:** Check if action is a BLOCK action.
- **Calls:** isinstance

### `is_require_approval_action(action: Action) -> bool`
- **Async:** No
- **Docstring:** Check if action is a REQUIRE_APPROVAL action.
- **Calls:** isinstance

## Classes

### `Scope(str, Enum)`
- **Docstring:** Policy scope determines visibility boundaries.

### `Mode(str, Enum)`
- **Docstring:** Policy mode determines enforcement semantics.

### `Comparator(str, Enum)`
- **Docstring:** Comparison operators for predicates.

### `LogicalOperator(str, Enum)`
- **Docstring:** Logical operators for compound conditions.

### `WarnAction`
- **Docstring:** Emit a warning message.
- **Methods:** to_dict
- **Class Variables:** message: str, type: Literal['WARN']

### `BlockAction`
- **Docstring:** Block execution.
- **Methods:** to_dict
- **Class Variables:** type: Literal['BLOCK']

### `RequireApprovalAction`
- **Docstring:** Require human approval before proceeding.
- **Methods:** to_dict
- **Class Variables:** type: Literal['REQUIRE_APPROVAL']

### `Predicate`
- **Docstring:** A simple comparison predicate.
- **Methods:** to_dict
- **Class Variables:** metric: str, comparator: Comparator, value: Union[int, float, str, bool]

### `ExistsPredicate`
- **Docstring:** Check if a metric exists.
- **Methods:** to_dict
- **Class Variables:** metric: str

### `LogicalCondition`
- **Docstring:** A compound condition combining two conditions with AND/OR.
- **Methods:** to_dict
- **Class Variables:** left: Condition, operator: LogicalOperator, right: Condition

### `Clause`
- **Docstring:** A single when-then clause.
- **Methods:** __post_init__, to_dict
- **Class Variables:** when: Condition, then: tuple[Action, ...]

### `PolicyMetadata`
- **Docstring:** Policy metadata header.
- **Methods:** __post_init__, to_dict
- **Class Variables:** name: str, version: int, scope: Scope, mode: Mode

### `PolicyAST`
- **Docstring:** Root AST node for a complete policy.
- **Methods:** __post_init__, to_dict, to_json, compute_hash, name, version, scope, mode
- **Class Variables:** metadata: PolicyMetadata, clauses: tuple[Clause, ...]

## Attributes

- `Action` (line 131)
- `Condition` (line 199)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__` |

## Callers

policy/compiler, policy/engine

## Export Contract

```yaml
exports:
  functions:
    - name: is_predicate
      signature: "is_predicate(condition: Condition) -> bool"
    - name: is_exists_predicate
      signature: "is_exists_predicate(condition: Condition) -> bool"
    - name: is_logical_condition
      signature: "is_logical_condition(condition: Condition) -> bool"
    - name: is_warn_action
      signature: "is_warn_action(action: Action) -> bool"
    - name: is_block_action
      signature: "is_block_action(action: Action) -> bool"
    - name: is_require_approval_action
      signature: "is_require_approval_action(action: Action) -> bool"
  classes:
    - name: Scope
      methods: []
    - name: Mode
      methods: []
    - name: Comparator
      methods: []
    - name: LogicalOperator
      methods: []
    - name: WarnAction
      methods: [to_dict]
    - name: BlockAction
      methods: [to_dict]
    - name: RequireApprovalAction
      methods: [to_dict]
    - name: Predicate
      methods: [to_dict]
    - name: ExistsPredicate
      methods: [to_dict]
    - name: LogicalCondition
      methods: [to_dict]
    - name: Clause
      methods: [to_dict]
    - name: PolicyMetadata
      methods: [to_dict]
    - name: PolicyAST
      methods: [to_dict, to_json, compute_hash, name, version, scope, mode]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
