# hoc_cus_policies_L5_engines_folds

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/folds.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy constant folding optimizations (pure logic)

## Intent

**Role:** Policy constant folding optimizations (pure logic)
**Reference:** PIN-470, Policy System
**Callers:** policy/optimizer

## Purpose

IR optimizations for PLang v2.0.

---

## Classes

### `FoldResult`
- **Docstring:** Result of a folding operation.
- **Class Variables:** folded: bool, value: Any, instruction: Optional[IRInstruction]

### `ConstantFolder`
- **Docstring:** Constant folding optimization.
- **Methods:** __init__, fold_module, fold_function, fold_block, try_fold, _fold_binary_op, _fold_unary_op, _fold_compare

### `DeadCodeEliminator`
- **Docstring:** Dead code elimination.
- **Methods:** __init__, eliminate, _mark_governance_critical, _eliminate_function, _find_reachable_blocks, _find_used_instructions

### `PolicySimplifier`
- **Docstring:** Policy-specific simplifications.
- **Methods:** __init__, simplify, _find_mergeable_policies, _merge_policies

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.policy.ir.ir_nodes` |

## Callers

policy/optimizer

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: FoldResult
      methods: []
    - name: ConstantFolder
      methods: [fold_module, fold_function, fold_block, try_fold]
    - name: DeadCodeEliminator
      methods: [eliminate]
    - name: PolicySimplifier
      methods: [simplify]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
