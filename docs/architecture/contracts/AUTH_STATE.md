# AUTH STATE CONTRACT

**Status:** ENFORCED
**Effective:** 2026-01-17
**Scope:** All authenticated endpoints, tenant state checks
**Reference:** PIN-LIM Post-Implementation Design Fix

---

## Prime Directive

> **Auth is not just "who". Auth is "who" + "what state" + "what's allowed".**

---

## 1. Authentication vs Authorization vs State

| Concern | Question | Layer | Response Code |
|---------|----------|-------|---------------|
| **Authentication** | Who is this? | Gateway (L2) | 401 Unauthorized |
| **Authorization** | Can they do this? | RBAC (L4) | 403 Forbidden |
| **State Readiness** | Is the tenant ready? | Domain (L4) | 403 + specific code |

**Rule:** These are three separate checks. Do not conflate them.

---

## 2. Tenant State Gate (MANDATORY)

Before any tenant-scoped operation, verify tenant readiness.

### Tenant States

| State | Value | Meaning | Operations Allowed |
|-------|-------|---------|-------------------|
| `CREATED` | 0 | Tenant exists, no setup | None |
| `CONFIGURING` | 1 | Setup in progress | Read-only |
| `VALIDATING` | 2 | Validation pending | Read-only |
| `PROVISIONING` | 3 | Resources provisioning | Read-only |
| `COMPLETE` | 4 | Fully operational | All |
| `SUSPENDED` | 5 | Billing/policy hold | Read-only |
| `ARCHIVED` | 6 | Soft deleted | None |

### State Check Implementation

```python
# app/services/tenant_state_gate.py

from enum import IntEnum
from fastapi import HTTPException

class TenantState(IntEnum):
    CREATED = 0
    CONFIGURING = 1
    VALIDATING = 2
    PROVISIONING = 3
    COMPLETE = 4
    SUSPENDED = 5
    ARCHIVED = 6

def require_tenant_ready(tenant) -> None:
    """Gate check: tenant must be in COMPLETE state for mutations."""
    if tenant.onboarding_state != TenantState.COMPLETE:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "tenant_not_ready",
                "state": tenant.onboarding_state,
                "required_state": TenantState.COMPLETE,
                "message": f"Tenant is in state {tenant.onboarding_state}, requires COMPLETE (4)"
            }
        )

def require_tenant_active(tenant) -> None:
    """Gate check: tenant must not be suspended or archived."""
    if tenant.onboarding_state in (TenantState.SUSPENDED, TenantState.ARCHIVED):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "tenant_inactive",
                "state": tenant.onboarding_state,
                "message": "Tenant is suspended or archived"
            }
        )
```

### Usage in Endpoints

```python
@router.post("/limits/simulate")
async def simulate_execution(request: Request, ...):
    auth_context = get_auth_context(request)
    tenant = await get_tenant(session, auth_context.tenant_id)

    require_tenant_ready(tenant)  # MANDATORY for mutations

    # Proceed with operation
```

---

## 3. Debug Endpoint (Non-Production)

### Endpoint: `GET /debug/auth/context`

**Purpose:** Diagnose authentication and state issues in development/staging.

**Response:**

```json
{
  "auth_present": true,
  "auth_type": "jwt|api_key|stub",
  "jwt_valid": true,
  "tenant_id": "demo-tenant",
  "tenant_state": 4,
  "tenant_state_name": "COMPLETE",
  "principal_type": "human|machine",
  "principal_id": "user_123",
  "roles": ["admin", "viewer"],
  "permissions": ["limits:read", "limits:write"],
  "timestamp": "2026-01-17T12:00:00Z"
}
```

**Implementation:**

```python
# app/api/debug/auth.py

from fastapi import APIRouter, Request
from app.auth.gateway_middleware import get_auth_context
from app.core.config import settings

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/auth/context")
async def get_auth_debug_context(request: Request):
    if settings.ENVIRONMENT == "production":
        raise HTTPException(status_code=404, detail="Not found")

    ctx = get_auth_context(request)
    tenant = await get_tenant(...)

    return {
        "auth_present": ctx is not None,
        "auth_type": ctx.auth_type if ctx else None,
        "tenant_id": ctx.tenant_id if ctx else None,
        "tenant_state": tenant.onboarding_state if tenant else None,
        "tenant_state_name": TenantState(tenant.onboarding_state).name if tenant else None,
        # ... other fields
    }
```

**Environment Guard:** Only available when `ENVIRONMENT != production`.

---

## 4. Error Response Standards

### Authentication Failure (401)

```json
{
  "error": "missing_auth",
  "message": "No authentication provided",
  "expected_headers": ["Authorization", "X-AOS-Key"]
}
```

```json
{
  "error": "jwt_invalid",
  "message": "JWT token is invalid or expired",
  "hint": "Check token expiration and signing key"
}
```

### Authorization Failure (403)

```json
{
  "error": "permission_denied",
  "required_permission": "limits:write",
  "principal_permissions": ["limits:read"],
  "message": "Principal lacks required permission"
}
```

### State Failure (403)

```json
{
  "error": "tenant_not_ready",
  "state": 1,
  "required_state": 4,
  "message": "Tenant is in state CONFIGURING (1), requires COMPLETE (4)"
}
```

**Rule:** Error responses must be **diagnosable** — include actual state, required state, and specific error code.

---

## 5. Testing Auth Flows

### Local Development (Stub Mode)

```bash
# With stub auth enabled
curl -H "Authorization: Bearer stub_admin_demo-tenant" \
  http://localhost:8000/api/v1/limits/simulate
```

### Staging/Production (Real Auth)

```bash
# With Clerk JWT
curl -H "Authorization: Bearer $CLERK_JWT" \
  https://api.agenticverz.com/api/v1/limits/simulate

# With API Key (machine clients)
curl -H "X-AOS-Key: $AOS_API_KEY" \
  https://api.agenticverz.com/api/v1/limits/simulate
```

### Debug Flow

```bash
# Step 1: Check auth context
curl http://localhost:8000/debug/auth/context \
  -H "Authorization: Bearer $TOKEN"

# Step 2: Verify tenant state
# Response shows tenant_state: 4 (COMPLETE) — good
# Response shows tenant_state: 1 (CONFIGURING) — need to complete onboarding
```

---

## 6. State Transition Visibility

### Endpoint: `GET /debug/tenant/state-history`

Returns state transitions for debugging:

```json
{
  "tenant_id": "demo-tenant",
  "current_state": 4,
  "transitions": [
    {"from": 0, "to": 1, "at": "2026-01-15T10:00:00Z", "trigger": "setup_started"},
    {"from": 1, "to": 2, "at": "2026-01-15T10:05:00Z", "trigger": "config_complete"},
    {"from": 2, "to": 3, "at": "2026-01-15T10:06:00Z", "trigger": "validation_passed"},
    {"from": 3, "to": 4, "at": "2026-01-15T10:10:00Z", "trigger": "provisioning_complete"}
  ]
}
```

---

## 7. Violation Response

```
AUTH STATE CONTRACT VIOLATION

Location: {endpoint}
Issue: {description}

Found: Endpoint allows operation in state {current_state}
Required: State must be {required_state}

Fix: Add require_tenant_ready(tenant) check before operation

Reference: docs/architecture/contracts/AUTH_STATE.md
```

---

## Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│                   AUTH STATE CHECKLIST                      │
├─────────────────────────────────────────────────────────────┤
│  Authentication (Gateway):                                  │
│    - JWT present and valid? → 401 if no                     │
│    - API key present and valid? → 401 if no                 │
│                                                             │
│  Authorization (RBAC):                                      │
│    - Permission granted? → 403 if no                        │
│                                                             │
│  State Readiness (Domain):                                  │
│    - Tenant state == COMPLETE (4)? → 403 if no              │
│    - Include state in error response                        │
│                                                             │
│  Debug (Non-Prod Only):                                     │
│    - /debug/auth/context → full auth diagnosis              │
│    - /debug/tenant/state-history → transition log           │
└─────────────────────────────────────────────────────────────┘
```
