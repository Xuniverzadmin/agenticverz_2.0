# Housekeeping Baseline

**Date:** 2025-12-30
**Reference:** docs/HOUSEKEEPING_CLASSIFICATION.md

---

## Executive Summary

This document captures the hygiene baseline for the Agenticverz 2.0 codebase after the housekeeping initiative. The goal was to restore signal quality by properly classifying, quarantining, or fixing all linter and type-checker errors.

**Core Principle:** No repeated errors. No permanent noise. Either FIX or QUARANTINE with intent.

---

## Baseline Metrics

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Ruff errors | ~426 | 164 | -262 (-62%) |
| Critical bugs (F821) | 10 | 0 | -10 |
| Bare except (E722) | 11 | 0 | -11 |
| Mypy errors | 1274 | 1274* | 0 |

*Mypy errors are quarantined via mypy.ini, not fixed. See Quarantine Strategy below.

---

## Classification Buckets

### Bucket A: FIX (Actionable Bugs)

These were real bugs that could cause runtime errors or unexpected behavior.

| Code | Count | Status | Notes |
|------|-------|--------|-------|
| F821 | 10 | FIXED | Undefined names - real runtime bugs |
| E722 | 11 | FIXED | Bare except blocks - now use `except Exception` |
| F402 | 1 | FIXED | Import shadowed by loop variable |

### Bucket B: QUARANTINE (Structural Debt)

These are intentional patterns or known limitations that are acknowledged, not ignored.

| Code | Count | Reason | Location |
|------|-------|--------|----------|
| E402 | ~185 | Deferred imports (FastAPI, circular deps) | pyproject.toml per-file-ignores |
| F841 | 88 | Unused variables (often intentional `_`) | Acknowledged baseline |
| F401 | 32 | Unused imports (re-exports, conditional) | Acknowledged baseline |
| F405 | 17 | Star imports in contracts | pyproject.toml per-file-ignores |
| E712 | 27 | SQLModel `== True` comparisons | Global ignore |
| E741 | 15 | Ambiguous variable names | Global ignore |
| E731 | 3 | Lambda assignment | Global ignore |
| ASYNC* | 23 | Blocking calls in async | Acknowledged baseline |
| Mypy | 1274 | SQLModel/SQLAlchemy typing | mypy.ini quarantine |

### Bucket C: CONFIGURE (Tool Noise)

These are not errors - they're tool configuration issues.

| Code | Resolution |
|------|------------|
| E501 | Line length - handled by formatter (ignored) |
| I001 | Import sorting - auto-fixable with `ruff --fix` |

---

## Quarantine Strategy

### Ruff Configuration

Located in `backend/pyproject.toml`:

```toml
[tool.ruff.lint]
ignore = [
    "E501",   # line too long (handled by formatter)
    "E741",   # ambiguous variable names (intentional)
    "E712",   # comparison to True/False (SQLAlchemy)
    "E731",   # lambda assignment (intentional)
]

[tool.ruff.lint.per-file-ignores]
# See pyproject.toml for full list
"app/main.py" = ["E402"]
"alembic/versions/*.py" = ["E402", "F401"]
# ... etc
```

### Mypy Configuration

Located in `mypy.ini`:

```ini
# Quarantined modules (SQLModel-heavy)
[mypy-backend.app.api.guard]
ignore_errors = True
# QUARANTINED: SQLModel exec() typing, gradual fix in Phase B

[mypy-backend.app.api.agents]
ignore_errors = True
# QUARANTINED: SQLModel patterns, gradual fix in Phase B
# ... etc
```

### Key Principle

> Quarantine is NOT suppression. It is ACKNOWLEDGMENT.
> Every quarantined pattern has a comment explaining WHY.

---

## Regression Guard

### Script

`scripts/ci/lint_regression_guard.sh`

### Frozen Baselines

```bash
BASELINE_RUFF=164
BASELINE_MYPY=1274
```

### Rules

1. **No Increase:** Error counts must never exceed baseline
2. **Lock Improvements:** When errors decrease, update baseline
3. **Fail Fast:** CI fails on regression

### Usage

```bash
# Full check
./scripts/ci/lint_regression_guard.sh

# Skip mypy (faster)
SKIP_MYPY=true ./scripts/ci/lint_regression_guard.sh
```

---

## Files Modified

### Critical Bug Fixes

| File | Fix |
|------|-----|
| `backend/app/api/guard.py` | Added logger import, changed bare except |
| `backend/app/integrations/L3_adapters.py` | Added TYPE_CHECKING import |
| `backend/app/policy/engine.py` | Added TYPE_CHECKING, future annotations |
| `backend/app/routing/models.py` | Added timezone import |
| `backend/app/memory/store.py` | Changed bare except |
| `backend/app/skills/http_call_v2.py` | Changed bare except (2x) |
| `backend/app/skills/registry_v2.py` | Renamed loop variable |
| `backend/cli/aos.py` | Changed bare except (4x) |
| `backend/cli/aos_workflow.py` | Changed bare except |
| `backend/tests/test_category3_data_contracts.py` | Removed dead code |

### Configuration Files

| File | Purpose |
|------|---------|
| `backend/pyproject.toml` | Updated ruff configuration with quarantine |
| `mypy.ini` | Mypy quarantine configuration |
| `scripts/ci/lint_regression_guard.sh` | CI regression guard |
| `docs/HOUSEKEEPING_CLASSIFICATION.md` | Error classification document |

---

## Remaining Work (Phase B)

The following are acknowledged debt to be addressed in Phase B:

1. **F841 (88):** Review unused variables for intentional vs dead code
2. **F401 (32):** Review unused imports for re-exports vs dead code
3. **ASYNC* (23):** Evaluate blocking calls in async context
4. **Mypy (1274):** Gradual SQLModel typing improvements

---

## Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Zero critical bugs (F821, E722) | 0 | ACHIEVED |
| Regression guard active | Yes | ACHIEVED |
| All errors classified | 100% | ACHIEVED |
| Quarantine documented | 100% | ACHIEVED |
| Baseline frozen | Yes | ACHIEVED |

---

## Maintenance Protocol

### Weekly

1. Run `./scripts/ci/lint_regression_guard.sh`
2. Review any new errors
3. Classify and fix or quarantine

### On Any PR

1. CI runs regression guard
2. Fails on any error count increase
3. Documents any improvements

### Quarterly

1. Review quarantined patterns
2. Consider promoting to Phase B fix list
3. Update baselines if improved

---

## References

- `docs/HOUSEKEEPING_CLASSIFICATION.md` - Full error classification
- `logs/precommit_baseline.txt` - Original pre-commit output
- `logs/mypy_baseline.txt` - Original mypy output
- `backend/pyproject.toml` - Ruff configuration
- `mypy.ini` - Mypy configuration
