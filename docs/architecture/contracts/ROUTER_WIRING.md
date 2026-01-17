# ROUTER WIRING CONTRACT

**Status:** ENFORCED
**Effective:** 2026-01-17
**Scope:** All FastAPI routers, main.py, API modules
**Reference:** PIN-LIM Post-Implementation Design Fix

---

## Prime Directive

> **main.py is a bootloader, not a router warehouse.**

---

## 1. The Registry Pattern (MANDATORY)

All router registration **must** go through a central registry.

### File: `app/api/registry.py`

```python
# Layer: L2 — Product APIs
# Product: system-wide
# Role: Centralized router registration
# Reference: ROUTER_WIRING.md

"""
API Router Registry

All routers MUST be registered here.
main.py calls register(app) — nothing else.
"""

from fastapi import FastAPI

# Domain routers
from app.api.policies import router as policies_router
from app.api.tenants import router as tenants_router
from app.api.runs import router as runs_router

# Limits domain
from app.api.limits.simulate import router as limits_simulate_router
from app.api.limits.override import router as limits_override_router
from app.api.policy_limits_crud import router as policy_limits_crud_router
from app.api.policy_rules_crud import router as policy_rules_crud_router

# Debug (conditional)
from app.core.config import settings


def register(app: FastAPI) -> None:
    """Register all API routers with the application."""

    # Core domain routers
    app.include_router(policies_router, prefix="/api/v1")
    app.include_router(tenants_router, prefix="/api/v1")
    app.include_router(runs_router, prefix="/api/v1")

    # Limits domain
    app.include_router(limits_simulate_router, prefix="/api/v1")
    app.include_router(limits_override_router, prefix="/api/v1")
    app.include_router(policy_limits_crud_router, prefix="/api/v1")
    app.include_router(policy_rules_crud_router, prefix="/api/v1")

    # Debug routes (non-production only)
    if settings.ENVIRONMENT != "production":
        from app.api.debug.auth import router as debug_auth_router
        app.include_router(debug_auth_router)
```

### File: `app/main.py`

```python
from fastapi import FastAPI
from app.api.registry import register

app = FastAPI(...)

# Middleware setup...

# Router registration — ONE LINE
register(app)
```

**Rule:** `main.py` never imports routers directly. It calls `register(app)`.

---

## 2. Router Organization

### Directory Structure

```
app/api/
├── registry.py              # Central registration (MANDATORY)
├── _adapters/               # Response adapters (see RUNTIME_VS_API.md)
│   └── limits.py
├── limits/                  # Domain: Limits
│   ├── __init__.py
│   ├── simulate.py          # POST /limits/simulate
│   └── override.py          # CRUD /limits/overrides
├── policies.py              # GET /policies/*
├── policy_limits_crud.py    # CRUD /policies/limits
├── policy_rules_crud.py     # CRUD /policies/rules
├── tenants.py               # /tenants/*
├── runs.py                  # /runs/*
└── debug/                   # Debug endpoints (non-prod)
    └── auth.py
```

### Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Domain router | `{domain}.py` | `policies.py` |
| CRUD router | `{resource}_crud.py` | `policy_limits_crud.py` |
| Action router | `{action}.py` | `simulate.py` |
| Subdomain dir | `{domain}/` | `limits/` |

---

## 3. Router Declaration Rules

### Router File Header

Every router file **must** have:

```python
# Layer: L2 — Product APIs
# Product: {product}
# Temporal:
#   Trigger: api
#   Execution: async
# Role: {single-line description}
# Callers: {who calls this}
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: {PIN or contract}
```

### Router Instantiation

```python
from fastapi import APIRouter

router = APIRouter(
    prefix="/{domain}",      # Domain prefix
    tags=["{domain}"],       # OpenAPI tag
)
```

### Export Convention

Each router module exports `router`:

```python
# In limits/simulate.py
router = APIRouter(prefix="/limits", tags=["limits"])

# In limits/__init__.py
from app.api.limits.simulate import router as simulate_router
from app.api.limits.override import router as override_router

__all__ = ["simulate_router", "override_router"]
```

---

## 4. Forbidden Patterns

### Direct Import in main.py (VIOLATION)

```python
# WRONG — main.py importing routers
from app.api.limits.simulate import router as limits_simulate_router
app.include_router(limits_simulate_router, prefix="/api/v1")
```

```python
# RIGHT — main.py uses registry
from app.api.registry import register
register(app)
```

### Router Registration Outside Registry (VIOLATION)

```python
# WRONG — Router registered in domain module
# In app/api/limits/__init__.py
def setup(app):
    app.include_router(simulate_router)
```

```python
# RIGHT — All registration in registry.py
# In app/api/registry.py
from app.api.limits.simulate import router as limits_simulate_router
app.include_router(limits_simulate_router, prefix="/api/v1")
```

### Relative Imports Across Domains (VIOLATION)

```python
# WRONG — Relative import from different domain
from ..policies import get_policy  # Crosses domain boundary
```

```python
# RIGHT — Absolute import
from app.services.policies import PolicyService
```

---

## 5. Registry Verification

### CI Check: `scripts/ci/check_router_registry.py`

Detects:
- `include_router` calls in `main.py`
- Router imports in `main.py` (except registry)
- Routers not present in `registry.py`
- Routers missing from `__all__` exports

### Manual Verification

```bash
# Find all router definitions
grep -rn "router = APIRouter" app/api/ --include="*.py"

# Find all include_router calls (should only be in registry.py)
grep -rn "include_router" app/ --include="*.py"

# Verify main.py only imports registry
grep "from app.api" app/main.py
# Expected: from app.api.registry import register
```

---

## 6. Adding a New Router

### Step 1: Create Router File

```python
# app/api/{domain}/{action}.py

# Layer: L2 — Product APIs
# Product: {product}
# Role: {description}
# Reference: PIN-XXX

from fastapi import APIRouter

router = APIRouter(prefix="/{domain}", tags=["{domain}"])

@router.post("/{endpoint}")
async def my_endpoint(...):
    ...
```

### Step 2: Export from Domain __init__.py

```python
# app/api/{domain}/__init__.py

from app.api.{domain}.{action} import router as {action}_router

__all__ = ["{action}_router"]
```

### Step 3: Register in Registry

```python
# app/api/registry.py

from app.api.{domain}.{action} import router as {domain}_{action}_router

def register(app: FastAPI) -> None:
    # ... existing routers
    app.include_router({domain}_{action}_router, prefix="/api/v1")
```

### Step 4: Verify

```bash
# Start server and check routes
curl http://localhost:8000/openapi.json | jq '.paths | keys'
```

---

## 7. Conditional Registration

For environment-specific routers (debug, admin, internal):

```python
# app/api/registry.py

def register(app: FastAPI) -> None:
    # Core routers (always)
    app.include_router(...)

    # Debug routers (non-production only)
    if settings.ENVIRONMENT != "production":
        from app.api.debug.auth import router as debug_auth_router
        app.include_router(debug_auth_router)

    # Admin routers (requires flag)
    if settings.ADMIN_API_ENABLED:
        from app.api.admin import router as admin_router
        app.include_router(admin_router, prefix="/admin")
```

**Rule:** Conditional imports happen inside `register()`, not at module level.

---

## 8. Violation Response

```
ROUTER WIRING CONTRACT VIOLATION

Location: {file}:{line}
Issue: {description}

Found: {code_snippet}
Expected: Router registration in app/api/registry.py

Fix:
1. Remove router import from {file}
2. Add router to app/api/registry.py
3. Use register(app) in main.py

Reference: docs/architecture/contracts/ROUTER_WIRING.md
```

---

## Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│                ROUTER WIRING RULES                          │
├─────────────────────────────────────────────────────────────┤
│  main.py:                                                   │
│    - ONLY imports: from app.api.registry import register    │
│    - ONLY calls: register(app)                              │
│    - NEVER imports routers directly                         │
│                                                             │
│  registry.py:                                               │
│    - ALL router imports                                     │
│    - ALL include_router calls                               │
│    - Conditional registration inside register()             │
│                                                             │
│  Router files:                                              │
│    - Header with layer, product, role                       │
│    - Export: router = APIRouter(...)                        │
│    - Domain __init__.py exports                             │
└─────────────────────────────────────────────────────────────┘
```
