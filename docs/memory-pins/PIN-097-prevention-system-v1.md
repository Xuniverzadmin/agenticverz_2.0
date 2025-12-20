# PIN-097: Prevention System v1.0 - Code Quality Automation

**Status:** ACTIVE
**Category:** Infrastructure / Code Quality / CI
**Created:** 2025-12-19
**Author:** Claude Opus 4.5

---

## Summary

Prevention System v1.0 provides automated detection and prevention of common code quality issues, specifically SQLModel Row tuple extraction bugs and API wiring problems. The system integrates into both pre-commit hooks and CI pipeline.

---

## Problem Statement

SQLModel's `session.exec()` returns Row tuples, not model instances. This caused multiple runtime errors:

```python
# UNSAFE - Returns Row tuple (Model,), not Model
obj = session.exec(select(Model)).first()
obj.id  # AttributeError: 'tuple' object has no attribute 'id'

# UNSAFE - Returns list of Row tuples
for item in session.exec(select(Model)).all():
    item.name  # AttributeError

# UNSAFE - Scalar queries return Row tuple
count = session.exec(select(func.count(...))).one()  # Returns (5,), not 5
```

These bugs slip through unit tests when mocks return model instances directly, only failing in production with real database calls.

---

## Solution Components

### 1. Safe Query Helpers (`backend/app/db_helpers.py`)

```python
from app.db_helpers import query_one, query_all, query_scalar, query_exists

# Safe patterns
user = query_one(session, select(User).where(User.id == id))
users = query_all(session, select(User).where(User.active == True))
count = query_scalar(session, select(func.count(User.id)))
exists = query_exists(session, select(User).where(User.email == email))
```

### 2. Pattern Linter (`scripts/ops/lint_sqlmodel_patterns.py`)

Detects unsafe patterns:
- `.first()` without `[0]` extraction
- `.all()` without list comprehension
- `.one()` on aggregates without extraction
- Direct attribute access on `.first()` result

```bash
python scripts/ops/lint_sqlmodel_patterns.py backend/app/
```

### 3. API Wiring Check (`scripts/ops/check_api_wiring.py`)

Validates:
- Response model presence on endpoints
- Route prefix consistency with filename
- Duplicate route detection

```bash
python scripts/ops/check_api_wiring.py
```

### 4. Interactive Pattern Adder (`scripts/ops/add_lint_pattern.py`)

When a new bug pattern is discovered:
```bash
python scripts/ops/add_lint_pattern.py
# Prompts for: regex, message, suggestion, safe patterns
```

### 5. Pre-commit Hooks (`.pre-commit-config.yaml`)

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
      - id: mypy

  - repo: local
    hooks:
      - id: sqlmodel-patterns
        name: SQLModel Pattern Linter
        entry: python scripts/ops/lint_sqlmodel_patterns.py backend/app/

      - id: api-endpoint-check
        name: API Endpoint Wiring Check
        entry: python scripts/ops/check_api_wiring.py

  - repo: https://github.com/Yelp/detect-secrets
    hooks:
      - id: detect-secrets
```

### 6. CI Integration (`scripts/ops/ci_consistency_check.sh`)

Added two new check functions:
- `check_sqlmodel_patterns()` - Runs pattern linter
- `check_api_wiring()` - Runs wiring validation

---

## Maintenance Process

See `docs/PREVENTION_PLAYBOOK.md` for detailed process. Quick summary:

1. **Bug Found** → Add pattern to linter
2. **Common Operation** → Add helper function
3. **Test** → Run linter locally
4. **Commit** → Pre-commit hooks validate
5. **Push** → CI validates again

---

## Files Created/Modified

| File | Type | Purpose |
|------|------|---------|
| `backend/app/db_helpers.py` | NEW | Safe query helper functions |
| `scripts/ops/lint_sqlmodel_patterns.py` | NEW | Pattern detection linter |
| `scripts/ops/check_api_wiring.py` | NEW | API route validation |
| `scripts/ops/add_lint_pattern.py` | NEW | Interactive pattern adder |
| `.pre-commit-config.yaml` | NEW | Pre-commit hook configuration |
| `docs/PREVENTION_PLAYBOOK.md` | NEW | Maintenance documentation |
| `scripts/ops/ci_consistency_check.sh` | MODIFIED | Added new checks |

---

## Detected Patterns (Initial Set)

### Unsafe Patterns
1. `result.first()` without `[0]` extraction
2. `session.exec(stmt).first().attribute` - direct attribute access
3. `for x in session.exec(stmt).all()` - iteration without extraction
4. `session.exec(func.count(...)).one()` - scalar without extraction
5. **NEW (2025-12-20):** `session.exec(text(...), params)` - exec() doesn't accept params dict

### Safe Patterns (Whitelisted)
1. `row = session.exec(stmt).first()` - using 'row' variable name
2. `row[0]` - explicit extraction
3. `r[0] for r in` - list comprehension extraction
4. `from app.db_helpers import` - using safe helpers
5. `query_one(|query_all(|query_scalar(` - helper function calls
6. **NEW (2025-12-20):** `session.execute(text(...), params)` - correct for raw SQL with params

---

## Success Metrics

- Zero Row tuple extraction bugs in production
- All new patterns added within 24 hours of discovery
- Pre-commit hooks catch issues before push
- CI catches any that slip through

---

## Related PINs

- PIN-096: M22 KillSwitch MVP (where Row tuple bugs were discovered)
- PIN-080: CI Consistency Checker v4.1
- PIN-081: MN-OS Naming Evolution (CI v5.0)

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-19 | Initial release - 4 unsafe patterns, 5 safe patterns, pre-commit hooks |
| 2025-12-20 | Added Pattern #5: session.exec() vs session.execute() for raw SQL with params |

---

## Pattern #5 Details: Raw SQL Parameter Passing

### Discovery Context
Found during M24 Ops Console implementation (PIN-105). All `/ops/*` endpoints using raw SQL with `text()` failed with:
```
Session.exec() takes 2 positional arguments but 3 were given
```

### Root Cause
SQLModel's `session.exec()` is designed for SQLAlchemy Core/ORM statements and only accepts one argument.
For raw SQL with parameters, SQLAlchemy's `session.execute()` must be used.

### Incorrect Pattern (Runtime Error)
```python
from sqlalchemy import text

stmt = text("SELECT * FROM users WHERE id = :id")
row = session.exec(stmt, {"id": user_id}).first()  # FAILS
```

### Correct Patterns

**Option 1: Use session.execute() directly**
```python
from sqlalchemy import text

stmt = text("SELECT * FROM users WHERE id = :id")
row = session.execute(stmt, {"id": user_id}).first()  # WORKS
```

**Option 2: Create helper function**
```python
def exec_sql(session: Session, stmt, params: dict = None):
    """Execute raw SQL with parameters."""
    if params:
        return session.execute(stmt, params)
    return session.execute(stmt)

# Usage
row = exec_sql(session, stmt, {"id": user_id}).first()
```

**Option 3: Use bindparams on the statement**
```python
from sqlalchemy import text, bindparam

stmt = text("SELECT * FROM users WHERE id = :id").bindparams(id=user_id)
row = session.exec(stmt).first()  # WORKS
```

### Detection Rule
```python
# Linter pattern to detect
pattern = r'session\.exec\s*\(\s*text\s*\([^)]+\)\s*,\s*\{'
message = "session.exec() does not accept params dict. Use session.execute() for raw SQL with parameters."
```

### Files Affected in M24
- `backend/app/api/ops.py` (13 occurrences fixed)
- `backend/app/services/event_emitter.py` (1 occurrence fixed)
