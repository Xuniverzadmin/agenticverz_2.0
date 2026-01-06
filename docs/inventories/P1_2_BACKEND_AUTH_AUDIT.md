# P1.2-3 Backend Authority Enforcement Audit

**Generated:** 2026-01-06
**Phase:** Phase 1.2 - Authority & Boundary Hardening
**Reference:** PIN-318

---

## Objective

Inventory all founder APIs and enforce `verify_fops_token` middleware.

---

## P1.2-3.1 Founder API Inventory

### APIs Requiring Founder Auth (aud="fops")

| API File | Prefix | Current Auth | Required Action |
|----------|--------|--------------|-----------------|
| `founder_timeline.py` | `/founder/timeline/*` | NONE | ADD `verify_fops_token` |
| `scenarios.py` | `/scenarios/*` | NONE | ADD `verify_fops_token` |
| `integration.py` | `/integration/*` | Query param only | ADD `verify_fops_token` |
| `traces.py` | `/traces/*` | JWT (generic) | Keep (tenant-isolated) |
| `replay.py` | `/replay/*` | `require_replay_read` | OK (authority-based) |
| `founder_explorer.py` | `/explorer/*` | Router-level `verify_fops_token` | ✅ FIXED (P1.2-4.1) |
| `ops.py` | `/ops/*` | Router-level `verify_fops_token` | ✅ OK |
| `cost_ops.py` | `/ops/cost/*` | Router-level | ✅ OK |
| `founder_actions.py` | `/ops/actions/*` | Endpoint-level | ✅ OK |
| `recovery.py` | `/recovery/*` | Router-level `verify_fops_token` | ✅ FIXED (P1.2-4.1) |
| `workers.py` | `/workers/*` | `verify_api_key` (SDK auth) | ✅ OK (different auth model) |

### Analysis by File

#### 1. founder_timeline.py - CRITICAL (NO AUTH)

**Current State:**
```python
from fastapi import APIRouter, HTTPException, Query  # No Depends
router = APIRouter(prefix="/founder/timeline", tags=["founder-timeline"])  # No dependencies
```

**Endpoints Exposed:**
- `GET /founder/timeline/decisions` - Lists all decision records

**Risk:** Any authenticated user can view founder decision timeline. CRITICAL.

**Fix:** Add `dependencies=[Depends(verify_fops_token)]` to router.

---

#### 2. scenarios.py - CRITICAL (NO AUTH)

**Current State:**
```python
from fastapi import APIRouter, HTTPException, Query  # No Depends
router = APIRouter(prefix="/scenarios", tags=["scenarios"])  # No dependencies
```

**Endpoints Exposed:**
- `GET /scenarios` - List simulation scenarios
- `POST /scenarios` - Create new scenario
- `GET /scenarios/{id}` - Get scenario
- `DELETE /scenarios/{id}` - Delete scenario
- `POST /scenarios/{id}/simulate` - Run simulation
- `POST /scenarios/simulate-adhoc` - Run ad-hoc simulation
- `GET /scenarios/info/immutability` - Get immutability info

**Risk:** Any user can access cost simulation. CRITICAL.

**Fix:** Add `dependencies=[Depends(verify_fops_token)]` to router.

---

#### 3. integration.py - HIGH (WEAK AUTH)

**Current State:**
```python
def get_tenant_id(tenant_id: str = Query(...)) -> str:
    return tenant_id

def get_current_user(user_id: Optional[str] = Query(None)) -> Optional[dict]:
    if user_id:
        return {"id": user_id}
    return None
```

**Issue:** Uses query parameters for tenant/user - NOT secure. Any user can claim any tenant_id.

**Endpoints Exposed:**
- `GET /integration/loop/{incident_id}` - Loop status
- `GET /integration/loop/{incident_id}/stages` - Stage details
- `GET /integration/loop/{incident_id}/stream` - SSE stream
- `POST /integration/loop/{incident_id}/retry` - Retry stage
- `POST /integration/loop/{incident_id}/revert` - Revert loop
- `GET /integration/checkpoints` - List checkpoints
- `GET /integration/checkpoints/{checkpoint_id}` - Get checkpoint
- `POST /integration/checkpoints/{checkpoint_id}/resolve` - Resolve checkpoint
- `GET /integration/stats` - Integration stats
- `GET /integration/loop/{incident_id}/narrative` - Loop narrative
- `GET /integration/graduation` - Graduation status
- `POST /integration/graduation/simulate/*` - Simulation endpoints
- `GET /integration/timeline/{incident_id}` - Prevention timeline

**Risk:** Anyone can claim any tenant_id via query param. HIGH.

**Fix:** Replace query param auth with `verify_fops_token`.

---

#### 4. traces.py - OK (JWT Auth)

**Current State:**
```python
from ..auth.jwt_auth import JWTAuthDependency, JWTConfig, TokenPayload
_jwt_auth = JWTAuthDependency(JWTConfig())

async def get_current_user(request: Request, token: TokenPayload = Depends(_jwt_auth)) -> User:
    return User.from_token(token)
```

**Auth Model:** Uses JWT authentication with tenant isolation.

**Assessment:** This is acceptable for shared trace endpoints that both customers and founders can access. The tenant isolation is enforced.

**Action:** No change needed. Traces are legitimately accessible to both audiences with tenant isolation.

---

#### 5. replay.py - OK (Authority-Based Auth)

**Current State:**
```python
from ..auth.authority import AuthorityResult, require_replay_read, verify_tenant_access

@router.get("/{incident_id}/slice")
async def get_replay_slice(..., auth: AuthorityResult = Depends(require_replay_read), ...):
    verify_tenant_access(auth, incident.tenant_id)
```

**Auth Model:** Uses RBAC authority system with explicit permission checks.

**Assessment:** Properly implemented. Has `require_replay_read` permission check and tenant isolation.

**Action:** No change needed.

---

## P1.2-3.2 Auth Middleware Implementation

### Files to Modify

1. **founder_timeline.py** - Add router-level `verify_fops_token`
2. **scenarios.py** - Add router-level `verify_fops_token`
3. **integration.py** - Replace query param auth with `verify_fops_token`
4. **founder_explorer.py** - Add `verify_fops_token` to `/info` endpoint

### Implementation Pattern

```python
# Import
from ..auth.console_auth import verify_fops_token, FounderToken

# Router-level protection (for all endpoints)
router = APIRouter(
    prefix="/founder/timeline",
    tags=["founder-timeline"],
    dependencies=[Depends(verify_fops_token)]  # ADD THIS
)

# Or endpoint-level (for specific endpoints)
@router.get("/info")
async def get_info(
    token: FounderToken = Depends(verify_fops_token)  # ADD THIS
):
    ...
```

---

## P1.2-3.3 Explicit Deny for Customer Tokens

### Implementation Strategy

`verify_fops_token` already rejects non-fops tokens:

```python
# In console_auth.py
async def verify_fops_token(request: Request) -> FounderToken:
    # ... token extraction ...

    if payload.get("aud") != "fops":
        raise HTTPException(status_code=403, detail="Founder access required")

    if not payload.get("mfa"):
        raise HTTPException(status_code=403, detail="MFA required for founder access")
```

When a customer token (aud="console") attempts a founder endpoint, they receive:
- `403 Founder access required` - explicit denial

### Additional Hardening (Optional)

Return `404 Not Found` instead of `403 Forbidden` to prevent route discovery:

```python
# In console_auth.py - stealth mode
async def verify_fops_token_stealth(request: Request) -> FounderToken:
    try:
        return await verify_fops_token(request)
    except HTTPException:
        # Hide route existence from non-founders
        raise HTTPException(status_code=404, detail="Not found")
```

---

## Summary

### Critical Gaps (All Fixed)

| Gap ID | File | Issue | Severity | Status |
|--------|------|-------|----------|--------|
| GAP-002 | founder_timeline.py | No auth at all | CRITICAL | ✅ FIXED (P1.2-3.2) |
| GAP-004 | scenarios.py | No auth at all | CRITICAL | ✅ FIXED (P1.2-3.2) |
| GAP-006 | integration.py | Query param auth (insecure) | HIGH | ✅ FIXED (P1.2-3.2) |
| GAP-007 | recovery.py | No auth at all | CRITICAL | ✅ FIXED (P1.2-4.1) |
| GAP-008 | founder_explorer.py | /info endpoint unprotected | MEDIUM | ✅ FIXED (P1.2-4.1) |

### Already Protected (No Change Needed)

| File | Auth Method | Status |
|------|-------------|--------|
| traces.py | JWT + tenant isolation | ✅ OK |
| replay.py | RBAC authority | ✅ OK |
| cost_ops.py | Router-level verify_fops_token | ✅ OK |
| founder_actions.py | Endpoint-level verify_fops_token | ✅ OK |
| ops.py | Router-level verify_fops_token | ✅ OK |
| workers.py | verify_api_key (SDK clients) | ✅ OK (different auth model) |

---

## Acceptance Criteria

- [x] founder_timeline.py has router-level verify_fops_token ✅ (P1.2-3.2)
- [x] scenarios.py has router-level verify_fops_token ✅ (P1.2-3.2)
- [x] integration.py uses verify_fops_token (not query params) ✅ (P1.2-3.2)
- [x] founder_explorer.py has router-level verify_fops_token ✅ (P1.2-4.1)
- [x] recovery.py has router-level verify_fops_token ✅ (P1.2-4.1)
- [x] Customer tokens (aud="console") receive 403/404 from founder APIs ✅
- [x] All founder APIs require MFA (via verify_fops_token) ✅

---

## Related Documents

- `backend/app/auth/console_auth.py` - Auth middleware
- `P1_2_AUTHORITY_MODEL.md` - Authority model
- `P1_1_FOPS_RBAC_HARDENING_AUDIT.md` - Phase 1.1 audit
