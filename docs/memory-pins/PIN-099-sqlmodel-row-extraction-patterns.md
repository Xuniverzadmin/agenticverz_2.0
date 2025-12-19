# PIN-099: SQLModel Row Extraction Patterns - Prevention Guide

**Status:** ACTIVE
**Created:** 2025-12-19
**Author:** Claude Opus 4.5
**Type:** Prevention / Best Practices

---

## Overview

This PIN documents issues encountered during M22.1 UI Console implementation and establishes patterns to prevent recurrence. These issues caused Internal Server Errors (500) in production endpoints.

---

## Issues Encountered

### Issue #1: File Permission Denied in Docker

**Symptom:**
```
PermissionError: [Errno 13] Permission denied: '/app/app/auth/tenant_auth.py'
```

**Root Cause:**
File created with restrictive permissions (600) that Docker container couldn't read.

**Fix Applied:**
```bash
chmod 644 /root/agenticverz2.0/backend/app/auth/tenant_auth.py
```

**Files Affected:**
- `backend/app/auth/tenant_auth.py`

---

### Issue #2: Incorrect Import Path

**Symptom:**
```
ModuleNotFoundError: No module named 'app.auth.dependencies'
```

**Root Cause:**
Import statement referenced non-existent module. The auth functions were in `tenant_auth.py`, not `dependencies.py`.

**Fix Applied:**
```python
# Before (broken):
from app.auth.dependencies import get_current_tenant

# After (fixed):
from app.auth.tenant_auth import get_tenant_context, TenantContext
```

**Files Affected:**
- `backend/app/api/guard.py`

---

### Issue #3: SQLModel Scalar Query Extraction

**Symptom:**
```
TypeError: '>' not supported between instances of 'tuple' and 'int'
```

**Root Cause:**
`session.exec(stmt).first()` returns a `Row` object, not a scalar value. The pattern `result or 0` doesn't work because Row objects are truthy even when containing 0.

**Anti-Pattern (WRONG):**
```python
# This does NOT work - Row is truthy even if first element is 0
incidents_count = session.exec(stmt).first() or 0

# This does NOT work - Row doesn't support comparison operators
if session.exec(stmt).first() > 10:
    ...
```

**Correct Pattern:**
```python
# For scalar queries (func.count, func.sum, func.avg):
row = session.exec(stmt).first()
incidents_count = row[0] if row else 0

# For nullable scalar queries:
row = session.exec(stmt).first()
value = row[0] if row and row[0] is not None else default_value
```

**Files Affected:**
- `backend/app/api/guard.py` (6 occurrences)
- `backend/app/api/operator.py` (11 occurrences)

---

### Issue #4: SQLModel Model Extraction from `.all()` Results

**Symptom:**
```
AttributeError: 'Row' object has no attribute 'tenant_id'
```

**Root Cause:**
`session.exec(stmt).all()` can return either:
1. Model instances directly (when selecting a single model)
2. Row objects (when using joins, specific columns, or order_by with expressions)

The check `isinstance(row, tuple)` fails because SQLAlchemy `Row` is not a Python `tuple`.

**Anti-Pattern (WRONG):**
```python
# This does NOT work - Row is not a Python tuple
for row in session.exec(stmt).all():
    if isinstance(row, tuple):
        model = row[0]
    else:
        model = row
```

**Correct Pattern:**
```python
# Check for model attributes, not tuple type
for row in session.exec(stmt).all():
    if hasattr(row, 'id'):  # Or any model-specific attribute
        model = row
    elif hasattr(row, '__getitem__'):
        model = row[0]
    else:
        model = row
```

**Files Affected:**
- `backend/app/api/guard.py` (3 occurrences)
- `backend/app/api/operator.py` (5 occurrences)

---

## Prevention Mechanisms

### 1. Code Review Checklist

Before merging any SQLModel/SQLAlchemy code, verify:

- [ ] All `.first()` results are extracted with `row[0] if row else default`
- [ ] All `.all()` iterations use `hasattr()` checks, not `isinstance(row, tuple)`
- [ ] No direct comparison operators on Row objects
- [ ] File permissions are 644 for Python files

### 2. Linting Rules (Add to `.pre-commit-config.yaml`)

```yaml
# Custom SQLModel anti-pattern detection
- repo: local
  hooks:
    - id: sqlmodel-patterns
      name: SQLModel Pattern Check
      entry: bash -c 'grep -rn "\.first() or " backend/app/ && exit 1 || exit 0'
      language: system
      types: [python]
```

### 3. Helper Functions (Add to `backend/app/utils/db_helpers.py`)

```python
"""Database helper functions for SQLModel row extraction."""
from typing import TypeVar, Optional, Any
from sqlalchemy import Row

T = TypeVar('T')


def scalar_or_default(row: Optional[Row], default: Any = 0) -> Any:
    """Extract scalar value from Row or return default.

    Usage:
        row = session.exec(select(func.count(Model.id))).first()
        count = scalar_or_default(row, 0)
    """
    if row is None:
        return default
    return row[0] if row[0] is not None else default


def extract_model(row: Any, model_attr: str = 'id') -> Any:
    """Extract model instance from Row or return as-is.

    Usage:
        for row in session.exec(stmt).all():
            model = extract_model(row, 'id')
    """
    if hasattr(row, model_attr):
        return row
    elif hasattr(row, '__getitem__'):
        return row[0]
    return row
```

### 4. Test Template (Add to new endpoint tests)

```python
def test_scalar_extraction():
    """Verify scalar queries return proper values, not Row objects."""
    with get_session() as session:
        stmt = select(func.count(Model.id))
        row = session.exec(stmt).first()

        # This should be an int, not a Row
        count = row[0] if row else 0
        assert isinstance(count, int)


def test_model_extraction():
    """Verify .all() results are properly extracted."""
    with get_session() as session:
        stmt = select(Model).limit(10)
        results = session.exec(stmt).all()

        for row in results:
            model = extract_model(row, 'id')
            assert hasattr(model, 'id')
```

### 5. Documentation Comment Pattern

Add this comment above any SQLModel query code:

```python
# SQLModel Row Extraction Pattern (PIN-099):
# - .first() returns Row, use row[0] if row else default
# - .all() may return Row objects, use hasattr() checks
```

---

## Quick Reference Card

| Operation | Anti-Pattern | Correct Pattern |
|-----------|--------------|-----------------|
| Scalar from `.first()` | `session.exec(stmt).first() or 0` | `row = session.exec(stmt).first(); row[0] if row else 0` |
| Model from `.first()` | `model = session.exec(stmt).first()` | Same (works correctly for model queries) |
| Model from `.all()` | `isinstance(row, tuple)` | `hasattr(row, 'model_attr')` |
| Comparison on Row | `if result > 10:` | `if row[0] > 10:` |

---

## Files Created/Modified During Fix

| File | Changes |
|------|---------|
| `backend/app/api/guard.py` | Fixed 6 scalar extractions, 3 model extractions |
| `backend/app/api/operator.py` | Fixed 11 scalar extractions, 5 model extractions |
| `backend/app/auth/tenant_auth.py` | Fixed file permissions (600 → 644) |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-19 | Initial creation after M22.1 endpoint debugging |
