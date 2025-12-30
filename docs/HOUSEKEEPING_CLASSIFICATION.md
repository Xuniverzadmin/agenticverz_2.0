# Housekeeping Error Classification

**Date:** 2025-12-30
**Phase:** H1 — Classify Errors
**Baseline Captured:** 2025-12-30

---

## Baseline Summary

| Tool | Total Errors | Files Affected |
|------|-------------|----------------|
| Pre-commit (ruff) | ~426 | ~80 |
| Mypy | 1,274 | 165 |
| Pytest | 2,628 tests collected | - |

---

## Pre-commit (Ruff) Classification

### Bucket A — Actionable Bugs (FIX)

| Code | Count | Description | Priority |
|------|------:|-------------|----------|
| **F821** | 10 | Undefined name | **P0 CRITICAL** |
| **F811** | 2 | Redefinition of unused variable | P1 |
| **E722** | 12 | Bare except | P1 (runtime risk) |
| **F841** | 104 | Local variable assigned but never used | P2 |
| **F401** | 42 | Imported but unused | P2 |
| **E712** | 27 | Comparison to True/False (use `is`) | P3 |
| **E711** | 3 | Comparison to None (use `is`) | P3 |
| **F405** | 17 | May be undefined from star imports | P2 |

**Total Bucket A:** ~217 errors

### Bucket B — Structural Debt (QUARANTINE)

| Code | Count | Description | Reason |
|------|------:|-------------|--------|
| **E402** | 185 | Module import not at top | Alembic migrations require this pattern |

**Total Bucket B:** 185 errors

### Bucket C — Tool Noise (CONFIGURE)

| Code | Count | Description | Action |
|------|------:|-------------|--------|
| **E741** | 15 | Ambiguous variable name | Configure ruff to allow |
| **E731** | 3 | Lambda assignment | Configure ruff to allow |
| **E501** | 2 | Line too long | Configure line length |
| **ASYNC101** | 3 | Async calling open/sleep | False positive for intentional use |

**Total Bucket C:** ~23 errors

---

## Mypy Classification

### Bucket A — Actionable Bugs (FIX)

| Code | Count | Description | Priority |
|------|------:|-------------|----------|
| **name-defined** | 9 | Undefined name | **P0 CRITICAL** |
| **attr-defined** (real bugs) | ~20 | Attribute not defined | P1 |
| **return-value** | 29 | Wrong return type | P2 |

**Total Bucket A:** ~58 errors

### Bucket B — Structural Debt (QUARANTINE)

| Code | Count | Description | Reason |
|------|------:|-------------|--------|
| **arg-type** | 391 | Wrong argument type | SQLModel/SQLAlchemy typing issues |
| **assignment** | 253 | Type assignment mismatch | SQLModel patterns |
| **call-overload** | 91 | No overload matches | SQLModel `exec()` pattern |
| **union-attr** | 121 | Attribute access on union | Optional handling |
| **attr-defined** | ~85 | Attribute not defined | SQLModel `table=True` |
| **index** | 67 | Not indexable | SQLModel patterns |
| **misc** | 62 | Miscellaneous | Mixed |
| **annotation-unchecked** | 61 | Unchecked annotation | Gradual typing |
| **operator** | 51 | Operator issues | SQLModel comparisons |
| **var-annotated** | 34 | Variable annotation | Type inference |
| **dict-item** | 25 | Dict item type | Schema patterns |
| **valid-type** | 12 | Invalid type | Complex generics |
| **call-arg** | 13 | Wrong call argument | Library typing |

**Total Bucket B:** ~1,166 errors

### Bucket C — Tool Noise (CONFIGURE)

| Code | Count | Description | Action |
|------|------:|-------------|--------|
| **import-untyped** | 2 | Untyped import | Configure ignore |

**Total Bucket C:** ~2 errors

---

## Root Cause Analysis

### SQLModel/SQLAlchemy Typing Issues (Majority of Bucket B)

The majority of mypy errors stem from SQLModel/SQLAlchemy typing patterns:

1. **`Session.exec()` overload**: SQLModel's `exec` method typing doesn't match expected patterns
2. **`table=True` keyword**: SQLModel tables use this pattern which mypy doesn't understand
3. **Column comparisons**: `Model.field == value` produces `bool` but mypy expects `ColumnElement[bool]`
4. **Optional handling**: Many `Model.field` accesses on optional models trigger `union-attr`

**Resolution Strategy:** File-level quarantine for SQLModel-heavy modules

### Alembic E402 Pattern

Alembic migrations require imports after `revision` and `down_revision` declarations. This is intentional and cannot be fixed.

**Resolution Strategy:** Configure ruff to ignore E402 in `alembic/versions/`

---

## Priority Fix Order

### Phase H3.1 — P0 Critical (Must Fix Now)

1. **F821** (10): Undefined names — these are real runtime bugs
2. **name-defined** (9): Undefined names in mypy — real bugs

### Phase H3.2 — P1 High (Fix Soon)

3. **E722** (12): Bare except — runtime risk
4. **F811** (2): Redefinition — potential bugs
5. **attr-defined** (real bugs, ~20): Missing attributes

### Phase H3.3 — P2 Medium (Clean Up)

6. **F841** (104): Unused variables
7. **F401** (42): Unused imports
8. **F405** (17): Star import undefined

### Phase H3.4 — P3 Low (Style)

9. **E712/E711** (30): Comparison style
10. **return-value** (29): Return type mismatches

---

## Quarantine Strategy

### Files to Quarantine (mypy)

Based on error density, quarantine these modules:

```ini
# mypy.ini additions

[mypy-backend.alembic.versions.*]
ignore_errors = True
# Reason: Alembic migrations, not runtime code

[mypy-backend.app.api.guard]
ignore_errors = True
# Reason: 200+ errors, SQLModel-heavy, gradual fix

[mypy-backend.app.api.agents]
ignore_errors = True
# Reason: 150+ errors, SQLModel-heavy, gradual fix

[mypy-backend.app.main]
ignore_errors = True
# Reason: Legacy patterns, gradual fix
```

### Ruff Configuration

```toml
# pyproject.toml or ruff.toml additions

[tool.ruff]
line-length = 120

[tool.ruff.lint.per-file-ignores]
"backend/alembic/versions/*.py" = ["E402"]
"backend/app/contracts/__init__.py" = ["F405"]
```

---

## Success Metrics

| Metric | Before | Target | Status |
|--------|--------|--------|--------|
| F821 (undefined) | 10 | 0 | PENDING |
| name-defined | 9 | 0 | PENDING |
| E722 (bare except) | 12 | 0 | PENDING |
| Pre-commit pass | NO | YES | PENDING |
| Mypy (non-quarantine) | 1274 | <100 | PENDING |

---

## Change Log

| Date | Change |
|------|--------|
| 2025-12-30 | Initial classification complete |
