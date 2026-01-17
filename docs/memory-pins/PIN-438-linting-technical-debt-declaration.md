# PIN-438: Linting Technical Debt Declaration

**Status:** ENFORCED
**Created:** 2026-01-17
**Category:** Governance / Technical Debt

---

## Summary

Declares that Ruff and Pyright warnings are pre-existing technical debt, explicitly out of scope for API-002 and governance enforcement work. Configures the system to fail only on new violations (no regression), not on existing debt.

---

## Rationale

The codebase has accumulated linting warnings over time that are structural in nature:

| Category | Count | Examples |
|----------|-------|----------|
| Import sorting (I001) | ~50+ | Alembic migrations, API modules |
| Unused imports (F401) | ~30+ | Conditional imports, optional deps |
| Module-level imports (E402) | ~20+ | Deferred imports (FastAPI pattern) |
| Unused variables (F841) | ~10+ | Various modules |
| Pyright type warnings | ~100+ | SQLAlchemy/SQLModel typing |

These are **code quality issues**, not **governance violations**.

---

## Governance Position

1. **BLCA (Layer Validator)** is the authoritative governance check
2. **Ruff/Pyright** are code quality tools, not governance blockers
3. **New violations** are blocked; existing debt is tolerated

---

## Enforcement Model

| Tool | Scope | Blocking? |
|------|-------|-----------
| BLCA | All backend files | YES - 0 violations required |
| Ruff | Staged files only | YES - for new violations only |
| Pyright | Zone A modules | Warning only |
| Mypy | Zone A modules | Warning only |

---

## Configuration Changes

### 1. Root `pyproject.toml` (NEW)

Created workspace-level Ruff configuration covering:
- `budgetllm/**/*.py`
- `l2_1/**/*.py`
- `design/**/*.py`
- `examples/**/*.py`
- `monitoring/**/*.py`
- `scripts/**/*.py`
- `sdk/**/*.py`
- `tests/**/*.py`
- `tools/**/*.py`
- `website/**/*.py`

### 2. `backend/pyproject.toml` (UPDATED)

Extensive per-file-ignores section covering all modules with known debt:
- API modules (app/api/)
- Auth modules (app/auth/)
- Skills modules (app/skills/)
- Worker modules (app/worker/, app/workers/)
- Workflow modules (app/workflow/)
- All other app/* directories
- Tests and scripts

Uses ASYNC101 (compatible with ruff 0.1.6 in pre-commit).

### 3. `sdk/python/pyproject.toml` (UPDATED)

Migrated deprecated Ruff config to new `tool.ruff.lint.*` format.
Added per-file-ignores for SDK patterns.

---

## Documentation

Created `docs/governance/LINTING_TECHNICAL_DEBT.md` with:
- Scope declaration (out of scope for API-002, BLCA, governance)
- Enforcement model table
- Cleanup strategy (separate workstream, one category at a time)
- References to pyproject.toml files and pre-commit config

---

## Key Decisions

1. **Freeze existing debt** - Per-file-ignores lock in current violations
2. **Catch new violations** - Any file not in ignores gets full linting
3. **Separate cleanup** - Linting cleanup is NOT mixed with feature work
4. **Ruff version compatibility** - Use ASYNC101 (available in ruff 0.1.6)

---

## Ruff Version Note

Pre-commit uses ruff v0.1.6 which has different ASYNC rule codes than newer versions:
- ASYNC101 (old) = ASYNC230/ASYNC109/ASYNC251 (new)
- Configuration uses ASYNC101 for compatibility

---

## Cleanup Strategy (Deferred)

When cleanup is prioritized:
1. Fix one category at a time (e.g., all I001 first)
2. Use `make lint-fix` for batch remediation
3. Create dedicated PR per category
4. Remove per-file-ignores as categories are cleaned

---

## Related

- `docs/governance/LINTING_TECHNICAL_DEBT.md` - Full documentation
- `backend/pyproject.toml` - Backend Ruff configuration
- `pyproject.toml` - Root workspace Ruff configuration
- `sdk/python/pyproject.toml` - SDK Ruff configuration
- PIN-437 - API-002 Counter-Rules (same session)
- PIN-121 - Mypy Technical Debt (related debt acknowledgment)
