# PIN-119: SQLModel Session Safety - Prevention Mechanisms

**Status:** ACTIVE
**Created:** 2025-12-21
**Category:** Developer Tooling / Prevention
**RCA Reference:** PIN-118 M24.2 Bug Fix

---

## Summary

Prevention mechanisms for SQLModel/SQLAlchemy session handling issues discovered during M24 production debugging. Addresses:
1. **DetachedInstanceError** - ORM objects accessed after session closes
2. **Row Tuple Extraction** - SQLModel version differences in `.first()` return type
3. **Session Scope Issues** - Attributes accessed outside session context

---

## Root Cause Analysis

### M24 OTP 500 Error

**Symptoms:**
- 500 Internal Server Error on email OTP verification
- Error: `DetachedInstanceError: Instance <User> is not bound to a Session`

**Root Causes:**
1. Function returned `User` object from `with Session()` block
2. Caller accessed `user.id` after session closed
3. SQLModel `.first()` returned model directly (not Row tuple) in production version

**Fix:** Return dicts instead of ORM objects from session blocks.

---

## Prevention Mechanisms

### 1. Enhanced SQLModel Pattern Linter (v2.0)

**Location:** `scripts/ops/lint_sqlmodel_patterns.py`

**Rules Enforced:**

| Rule ID | Severity | Description |
|---------|----------|-------------|
| ROW001-004 | WARNING | Row tuple extraction issues |
| DETACH001 | WARNING | Function returns ORM model |
| DETACH002 | ERROR | Returning from `with Session()` block |
| DETACH003 | WARNING | Returning refreshed object |
| GET001 | WARNING | Use session.get() for ID lookup |
| SQL001 | ERROR | session.exec() with params dict |
| SCOPE001 | WARNING | Attribute access outside session |

**Usage:**
```bash
# Scan specific path
python scripts/ops/lint_sqlmodel_patterns.py backend/app/api/

# Scan entire codebase
python scripts/ops/lint_sqlmodel_patterns.py --scan-all

# Verbose mode
python scripts/ops/lint_sqlmodel_patterns.py --scan-all -v
```

**Exit Codes:**
- 0: No issues
- 1: Errors found
- 2: Critical issues found

### 2. Safe Query Helpers (db_helpers v2.0)

**Location:** `backend/app/utils/db_helpers.py`

**Functions:**

```python
from app.utils.db_helpers import (
    query_one,       # Safe single-row query
    query_all,       # Safe multi-row query
    model_to_dict,   # Convert model to dict
    safe_get,        # session.get() wrapper
    get_or_create,   # Django-style get_or_create
)
```

#### `query_one(session, statement, model_class)`
Handles SQLModel version differences automatically:
```python
# Replaces:
result = session.exec(stmt).first()
user = result[0] if result else None  # Version-dependent!

# With:
user = query_one(session, stmt, User)  # Always works
```

#### `model_to_dict(model, include, exclude)`
Prevents DetachedInstanceError:
```python
# Replaces:
with Session(engine) as session:
    user = session.get(User, user_id)
    return user  # BREAKS after session closes!

# With:
with Session(engine) as session:
    user = session.get(User, user_id)
    return model_to_dict(user)  # Safe!
```

#### `safe_get(session, model_class, id, to_dict=False)`
Combined get + optional dict conversion:
```python
# Get model
user = safe_get(session, User, user_id)

# Get as dict (safe after session closes)
user_data = safe_get(session, User, user_id, to_dict=True)
```

### 3. Pre-Commit Hook

**Configuration:** `.pre-commit-config.yaml`

```yaml
- id: sqlmodel-patterns
  name: SQLModel Pattern Linter
  entry: python scripts/ops/lint_sqlmodel_patterns.py backend/app/
  language: python
  types: [python]
  pass_filenames: false
```

Runs automatically on every commit.

### 4. CI Integration

**Configuration:** `.github/workflows/ci.yml`

The CI consistency check includes SQLModel pattern linting:
```bash
./scripts/ops/ci_consistency_check.sh
```

---

## Safe Patterns

### Pattern 1: Return Dict from Session Block
```python
def get_user(user_id: str) -> dict:
    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user:
            return {}
        # Extract BEFORE session closes
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
        }
```

### Pattern 2: Handle SQLModel Version Differences
```python
from app.utils.db_helpers import query_one

def find_by_email(email: str) -> Optional[User]:
    with Session(engine) as session:
        stmt = select(User).where(User.email == email)
        return query_one(session, stmt, User)
```

### Pattern 3: Use session.get() for ID Lookups
```python
# Bad: Uses select().where() for ID
stmt = select(User).where(User.id == user_id)
row = session.exec(stmt).first()
user = row[0] if row else None

# Good: Uses session.get()
user = session.get(User, user_id)  # Returns model directly
```

### Pattern 4: Extract Before Refresh
```python
def create_user(email: str) -> dict:
    with Session(engine) as session:
        user = User(email=email)
        session.add(user)
        session.commit()
        session.refresh(user)

        # Extract AFTER refresh, BEFORE session closes
        return model_to_dict(user)
```

---

## Codebase Scan Results (2025-12-21)

Initial scan found 24 potential issues:
- 🔴 Critical: 0
- 🟠 Error: 7 (SQL001, DETACH002)
- 🟡 Warning: 17 (GET001, SCOPE001, DETACH003)

**Notable Files:**
- `backend/app/api/failures.py` - Multiple ID lookup patterns
- `backend/app/api/v1_killswitch.py` - Refresh before return
- `backend/app/api/v1_proxy.py` - Row iteration issues

These are existing patterns that should be addressed in future refactoring.

---

## Quick Reference

### When to Use What

| Situation | Solution |
|-----------|----------|
| Return user from API | Return `model_to_dict(user)` |
| Lookup by ID | Use `session.get(User, id)` |
| Lookup by other field | Use `query_one(session, stmt, User)` |
| Iterate results | Use `query_all(session, stmt, User)` |
| Get or create | Use `get_or_create(session, User, email=...)` |

### Common Mistakes

| Mistake | Fix |
|---------|-----|
| `return user` after session | `return model_to_dict(user)` |
| `row = stmt.first()` | `row = query_one(session, stmt)` |
| `for r in stmt.all()` | `for r in query_all(session, stmt)` |
| `select(X).where(X.id==id)` | `session.get(X, id)` |

---

## Files Created/Modified

**Created:**
- `docs/memory-pins/PIN-119-sqlmodel-session-safety.md`

**Modified:**
- `scripts/ops/lint_sqlmodel_patterns.py` - Enhanced v2.0
- `backend/app/utils/db_helpers.py` - Added v2.0 helpers

---

## Verification

```bash
# Run linter
python scripts/ops/lint_sqlmodel_patterns.py --scan-all

# Pre-commit check
pre-commit run sqlmodel-patterns --all-files

# CI check
./scripts/ops/ci_consistency_check.sh
```

---

## Related PINs

- PIN-099: SQLModel Row Extraction Patterns (original)
- PIN-118: M24 Customer Onboarding (RCA)

---

**Status: ACTIVE - Run linter regularly to catch issues early**
