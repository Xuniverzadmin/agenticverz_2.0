# hoc_cus_policies_L6_drivers_symbol_table

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L6_drivers/symbol_table.py` |
| Layer | L6 — Domain Driver |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy symbol table management

## Intent

**Role:** Policy symbol table management
**Reference:** PIN-470, Policy System
**Callers:** policy/ir/ir_builder

## Purpose

Symbol table for PLang v2.0 compilation.

---

## Classes

### `SymbolType(Enum)`
- **Docstring:** Types of symbols in PLang.

### `Symbol`
- **Docstring:** A symbol in the symbol table.
- **Methods:** __repr__
- **Class Variables:** name: str, symbol_type: SymbolType, category: Optional[PolicyCategory], priority: int, value_type: Optional[str], value: Any, defined_at: Optional[str], referenced_by: List[str], requires_approval: bool, audit_level: int

### `Scope`
- **Docstring:** A scope in the symbol table.
- **Methods:** define, lookup, lookup_by_category, get_all_symbols
- **Class Variables:** name: str, parent: Optional['Scope'], symbols: Dict[str, Symbol], children: List['Scope'], category: Optional[PolicyCategory]

### `SymbolTable`
- **Docstring:** Symbol table for PLang compilation.
- **Methods:** __init__, _define_builtins, enter_scope, exit_scope, define, lookup, lookup_policy, lookup_rule, get_symbols_by_category, get_policies, get_rules, add_reference, get_unreferenced_symbols, __str__

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.policy.compiler.grammar` |

## Callers

policy/ir/ir_builder

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: SymbolType
      methods: []
    - name: Symbol
      methods: []
    - name: Scope
      methods: [define, lookup, lookup_by_category, get_all_symbols]
    - name: SymbolTable
      methods: [enter_scope, exit_scope, define, lookup, lookup_policy, lookup_rule, get_symbols_by_category, get_policies, get_rules, add_reference, get_unreferenced_symbols]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
