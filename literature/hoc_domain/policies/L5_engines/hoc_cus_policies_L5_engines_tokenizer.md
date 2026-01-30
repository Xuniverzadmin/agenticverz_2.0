# hoc_cus_policies_L5_engines_tokenizer

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/tokenizer.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy language tokenizer (pure lexical analysis)

## Intent

**Role:** Policy language tokenizer (pure lexical analysis)
**Reference:** PIN-470, Policy System
**Callers:** policy/compiler/parser

## Purpose

Tokenizer for PLang v2.0 with M19 category support.

---

## Classes

### `TokenType(Enum)`
- **Docstring:** Token types for PLang v2.0.

### `Token`
- **Docstring:** A token in PLang source code.
- **Methods:** __repr__, is_category, is_action
- **Class Variables:** type: TokenType, value: str, line: int, column: int

### `TokenizerError(Exception)`
- **Docstring:** Error during tokenization.
- **Methods:** __init__

### `Tokenizer`
- **Docstring:** Tokenizer for PLang v2.0.
- **Methods:** __init__, current_char, peek, advance, skip_whitespace, skip_comment, read_string, read_number, read_identifier, read_operator, tokenize, __iter__

## Attributes

- `KEYWORD_TOKENS` (line 96)

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
    - name: TokenType
      methods: []
    - name: Token
      methods: [is_category, is_action]
    - name: TokenizerError
      methods: []
    - name: Tokenizer
      methods: [current_char, peek, advance, skip_whitespace, skip_comment, read_string, read_number, read_identifier, read_operator, tokenize]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
