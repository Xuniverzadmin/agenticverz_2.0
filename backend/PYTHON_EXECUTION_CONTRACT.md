# Python Execution Contract

**Status:** FROZEN
**Created:** 2025-12-26
**Purpose:** Eliminate import-time failures and ensure deterministic Python execution

---

## Execution Invariants (Non-Negotiable)

### 1. Working Directory

All Python commands MUST run from `backend/`:

```bash
# CORRECT
cd backend && python3 -m app.api.workers

# WRONG
python3 backend/app/api/workers.py
```

### 2. Package Root

`app/` is the root package. All imports use absolute paths:

```python
# CORRECT
from app.db import get_async_session
from app.models.tenant import WorkerRun

# WRONG
from ..db import get_async_session
from backend.app.db import get_async_session
```

### 3. Environment Variables

`DATABASE_URL` must be set before any database operations, but NOT required for imports:

```bash
# Import-safe (works without DATABASE_URL)
python3 -c "from app.hoc.api.cus.policies.workers import router"

# Execution requires DATABASE_URL
DATABASE_URL=... python3 -c "from app.db import get_engine; get_engine()"
```

### 4. No Import-Time Side Effects

No module may:
- Read environment variables at import time
- Create database connections at import time
- Make network requests at import time
- Raise exceptions at import time

All such operations must be lazy (on first use).

---

## Verification Commands

### Check import hygiene (no DATABASE_URL needed):

```bash
cd backend
python3 -c "from app.hoc.api.cus.policies.workers import router; print('OK')"
```

### Check database connection (requires DATABASE_URL):

```bash
cd backend
DATABASE_URL=... python3 -c "from app.db import get_engine; get_engine(); print('OK')"
```

### Check syntax only:

```bash
cd backend
python3 -m py_compile app/api/workers.py
```

---

## What Happens If Violated

| Violation | Symptom | Fix |
|-----------|---------|-----|
| Wrong CWD | `ModuleNotFoundError: No module named 'app'` | `cd backend` first |
| Missing DATABASE_URL | `RuntimeError: DATABASE_URL...` | Export DATABASE_URL or use lazy imports |
| Relative imports | `ImportError: attempted relative import...` | Convert to absolute imports |
| Import-time side effect | First import fails, second succeeds | Make operation lazy |

---

## Prevention Rules

### Rule 1: All new modules must be import-safe

Before merging any Python file, run:

```bash
cd backend
python3 -c "import app.new_module"
```

If this fails without DATABASE_URL, the module has import-time side effects.

### Rule 2: No relative imports

Search for violations:

```bash
grep -r "from \.\." app/
```

Must return 0 results.

### Rule 3: CI must verify import hygiene

CI job must include:

```bash
cd backend
python3 -m py_compile app/api/workers.py
python3 -c "from app.hoc.api.cus.policies.workers import router"
```

Without DATABASE_URL set.

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-26 | Created execution contract |
| 2025-12-26 | Fixed db.py import-time side effects |
| 2025-12-26 | Converted workers.py to absolute imports |
