# hoc_cus_policies_L5_engines_dsl_parser

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/dsl_parser.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy DSL text parser (DSL → AST) - pure parsing

## Intent

**Role:** Policy DSL text parser (DSL → AST) - pure parsing
**Reference:** PIN-470, PIN-341 Section 1.8, PIN-345
**Callers:** policy/compiler

## Purpose

Policy DSL Parser

---

## Functions

### `parse(source: str) -> PolicyAST`
- **Async:** No
- **Docstring:** Parse Policy DSL text into AST.  Args:
- **Calls:** Lexer, Parser, parse, tokenize

### `parse_condition(source: str) -> Condition`
- **Async:** No
- **Docstring:** Parse a standalone condition expression.  Useful for testing or building conditions programmatically.
- **Calls:** Lexer, Parser, _parse_condition, error, tokenize

## Classes

### `ParseLocation`
- **Docstring:** Source location for error reporting.
- **Methods:** __str__
- **Class Variables:** line: int, column: int

### `ParseError(Exception)`
- **Docstring:** Raised when parsing fails.
- **Methods:** __init__

### `Token`
- **Docstring:** A lexical token with position info.
- **Class Variables:** type: str, value: Any, line: int, column: int

### `Lexer`
- **Docstring:** Tokenizer for Policy DSL.
- **Methods:** __init__, tokenize, _advance, _convert_value

### `Parser`
- **Docstring:** Recursive descent parser for Policy DSL.
- **Methods:** __init__, current, error, expect, accept, parse, _parse_header, _parse_clauses, _parse_clause, _parse_condition, _parse_or_expr, _parse_and_expr, _parse_atom, _parse_predicate, _parse_value, _parse_actions, _try_parse_action

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__`, `app.dsl.ast` |

## Callers

policy/compiler

## Export Contract

```yaml
exports:
  functions:
    - name: parse
      signature: "parse(source: str) -> PolicyAST"
    - name: parse_condition
      signature: "parse_condition(source: str) -> Condition"
  classes:
    - name: ParseLocation
      methods: []
    - name: ParseError
      methods: []
    - name: Token
      methods: []
    - name: Lexer
      methods: [tokenize]
    - name: Parser
      methods: [current, error, expect, accept, parse]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
