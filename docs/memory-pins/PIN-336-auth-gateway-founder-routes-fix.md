# PIN-336: Auth Gateway Founder Routes Fix

**Created:** 2026-01-06
**Status:** COMPLETE
**Category:** Infrastructure / Auth Gateway
**Related:** PIN-335 (Build Verification), PIN-334 (CRM Unquarantine)

---

## Problem Statement

The auth gateway middleware blocks `/founder/` API routes before they reach the route handler's `verify_fops_token` dependency. This prevents FOPS-authenticated requests from reaching founder endpoints.

**Symptom:**
```bash
curl -H "X-API-Key: $AOS_FOPS_KEY" "http://localhost:8000/founder/contracts/review-queue"
# Returns: {"error":"missing_auth","message":"Authentication required"}
```

---

## Root Cause Analysis

### Auth Flow (Current)
```
Request → Gateway Middleware → RBAC Middleware → Route Handler
              ↓
    Checks X-AOS-Key against AOS_API_KEY
    (Does NOT recognize AOS_FOPS_KEY)
              ↓
    Returns 401 before reaching verify_fops_token
```

### Gateway Configuration
File: `app/auth/gateway_config.py`

```python
"public_paths": [
    "/health",
    "/metrics",
    "/docs",
    # ... no /founder/ paths
]
```

### Route Handler Auth
File: `app/api/founder_contract_review.py`

```python
@router.get("/review-queue")
async def get_review_queue(
    token: FounderToken = Depends(verify_fops_token),  # Never reached
    ...
)
```

---

## Solution

Add `/founder/` to gateway's public paths. The route handlers use their own auth (`verify_fops_token`) which validates FOPS tokens/keys.

**Rationale:**
- Founder routes are designed with dedicated auth dependencies
- `verify_fops_token` handles both session cookies AND X-API-Key with AOS_FOPS_KEY
- Gateway middleware is redundant for these routes
- Same pattern used by `/api/v1/auth/` (public at gateway, auth at handler)

---

## Implementation

### Change Required
File: `app/auth/gateway_config.py`

Add to `public_paths`:
- `/founder/` - All founder API routes (contract review, evidence review)
- `/ops/` - Ops console routes (also FOPS auth)
- `/platform/` - Platform health routes (also FOPS auth)

---

## Verification

After fix:
```bash
source .env
curl -H "X-API-Key: $AOS_FOPS_KEY" "http://localhost:8000/founder/contracts/review-queue"
# Should return: {"items": [...], "total": N, ...}
```

---

## Risk Assessment

**Low Risk:**
- Gateway public paths just skip gateway auth, not all auth
- Route handlers still enforce FOPS token validation
- No change to customer routes (`/api/v1/*`)

---

## Updates

### 2026-01-06: Implementation Complete

**Two middleware layers required fixes:**

1. **Gateway Middleware** (`app/auth/gateway_config.py`):
   - Added `/founder/`, `/ops/`, `/platform/` to `public_paths` in `get_gateway_middleware_config()`
   - These routes now bypass gateway auth check

2. **RBAC Middleware** (`app/auth/rbac_middleware.py`):
   - Added `/founder/`, `/ops/`, `/platform/` to `PUBLIC_PATHS` in `get_policy_for_path()`
   - These routes now return `None` (no policy) so RBAC is skipped

**Error progression during debugging:**
- Initial: `{"error":"missing_auth","message":"Authentication required"}` (Gateway blocking)
- After gateway fix: `{"error":"forbidden","reason":"no-credentials"}` (RBAC blocking)
- After RBAC fix: `{"error":"AUTH_DOMAIN_MISMATCH"}` (verify_fops_token checking key)
- Final: `{"total":0,"contracts":[],"as_of":"..."}` (Success!)

**Verification:**
```bash
curl -H "X-API-Key: $AOS_FOPS_KEY" "http://localhost:8000/founder/contracts/review-queue"
# Returns: {"total":0,"contracts":[],"as_of":"2026-01-06T17:43:57.363557+00:00"}
```

**Files Modified:**
- `backend/app/auth/gateway_config.py` - Added founder routes to public_paths
- `backend/app/auth/rbac_middleware.py` - Added founder routes to PUBLIC_PATHS
