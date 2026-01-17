# Linting Technical Debt Declaration

**Status:** DEFERRED
**Effective:** 2026-01-17
**Reference:** PIN-437 (API-002 Counter-Rules)

## Scope

Ruff and Pyright warnings in the codebase are **pre-existing technical debt** and are explicitly **out of scope** for:

- API-002 Response Envelope governance work
- BLCA layer validation enforcement
- Governance guardrail compliance checks

## Rationale

The codebase has accumulated linting warnings over time that are structural in nature:

| Category | Count | Examples |
|----------|-------|----------|
| Import sorting (I001) | ~50+ | Alembic migrations, API modules |
| Unused imports (F401) | ~30+ | Conditional imports, optional deps |
| Module-level imports (E402) | ~20+ | Deferred imports (FastAPI pattern) |
| Unused variables (F841) | ~10+ | Various modules |
| Pyright type warnings | ~100+ | SQLAlchemy/SQLModel typing |

## Governance Position

1. **BLCA (Layer Validator)** is the authoritative governance check
2. **Ruff/Pyright** are code quality tools, not governance blockers
3. **New violations** are blocked; existing debt is tolerated

## Enforcement Model

| Tool | Scope | Blocking? |
|------|-------|-----------|
| BLCA | All backend files | YES - 0 violations required |
| Ruff | Staged files only | YES - for new violations only |
| Pyright | Zone A modules | Warning only |
| Mypy | Zone A modules | Warning only |

## Cleanup Strategy

Linting cleanup is a **separate workstream** and should NOT be mixed with:

- Feature development
- Governance fixes
- Bug fixes

When cleanup is prioritized:
1. Fix one category at a time (e.g., all I001 first)
2. Use `make lint-fix` for batch remediation
3. Create dedicated PR per category

## References

- `backend/pyproject.toml` - Ruff configuration with per-file-ignores
- `.pre-commit-config.yaml` - Pre-commit hook configuration
- `docs/HOUSEKEEPING_CLASSIFICATION.md` - Bucket B structural debt
- PIN-121 - Mypy technical debt baseline (572 errors)
