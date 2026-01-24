# P1.1-3.2 FOPS RBAC Hardening Audit

**Generated:** 2026-01-06
**Phase:** Phase 1.1 - Legacy Resolution & Structural Hardening
**Reference:** PIN-317

---

## Objective

Audit RBAC protection on founder surfaces to ensure customers cannot accidentally access them.

---

## Frontend Route Protection Audit

### ProtectedRoute Analysis

**File:** `website/app-shell/src/routes/ProtectedRoute.tsx`

```typescript
export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, onboardingComplete } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (!onboardingComplete) {
    return <Navigate to="/onboarding/connect" replace />;
  }

  return <>{children}</>;
}
```

**Finding:** CRITICAL GAP

| Check | Status | Issue |
|-------|--------|-------|
| Authentication check | YES | - |
| Onboarding check | YES | - |
| Audience check | NO | ANY authenticated user can access |
| Role/superuser check | NO | No founder role verification |

**Impact:** Any customer with a valid token can navigate to founder routes.

### Founder-Specific Route Guard

**Current:** Does not exist

**Required:** `FounderRoute` wrapper that checks:
- `audience === 'founder' || audience === 'operator'`
- `user.is_superuser === true`

---

## Backend API Protection Audit

### Router-Level Protection (Recommended)

These APIs have router-level `dependencies=[Depends(verify_fops_token)]`:

| API File | Prefix | Status |
|----------|--------|--------|
| `ops.py` | `/ops/*` | PARTIAL (some routes protected) |
| `cost_ops.py` | `/ops/cost/*` | PROTECTED |

### Endpoint-Level Protection

These APIs have endpoint-level `Depends(verify_fops_token)`:

| API File | Prefix | Status | Gaps |
|----------|--------|--------|------|
| `founder_explorer.py` | `/explorer/*` | PARTIAL | `/explorer/info` unprotected |
| `founder_actions.py` | `/ops/actions/*` | PROTECTED | - |

### UNPROTECTED Founder APIs (CRITICAL)

| API File | Prefix | Auth | RISK |
|----------|--------|------|------|
| `founder_timeline.py` | `/fdr/timeline/*` | NONE | CRITICAL |
| `traces.py` | `/traces/*` | NONE | CRITICAL |
| `scenarios.py` | `/scenarios/*` | NONE | CRITICAL |
| `replay.py` | `/replay/*` | NONE | CRITICAL |
| `integration.py` | `/integration/*` | NONE | CRITICAL |

---

## Detailed Findings

### 1. founder_timeline.py - UNPROTECTED

```python
from fastapi import APIRouter, HTTPException, Query  # NO Depends
router = APIRouter(prefix="/fdr/timeline", tags=["founder-timeline"])  # NO dependencies
```

**Endpoints exposed:**
- `GET /fdr/timeline/decisions` - Lists all decision records
- Cross-tenant data visible to anyone

**Risk:** Any authenticated user can view founder decision timeline

### 2. traces.py - UNPROTECTED

```python
router = APIRouter(prefix="/traces", tags=["traces"])  # NO dependencies
```

**Endpoints exposed:**
- `GET /traces` - List all execution traces
- `GET /traces/{run_id}` - Trace details

**Risk:** Any authenticated user can view execution traces

### 3. scenarios.py - UNPROTECTED

```python
from fastapi import APIRouter, HTTPException, Query  # NO Depends
router = APIRouter(prefix="/scenarios", tags=["scenarios"])  # NO dependencies
```

**Endpoints exposed:**
- `GET /scenarios` - List simulation scenarios
- `POST /scenarios/simulate` - Run cost simulation

**Risk:** Any authenticated user can view and run simulations

### 4. replay.py - UNPROTECTED

```python
router = APIRouter(prefix="/replay", tags=["replay"])  # NO dependencies
```

**Endpoints exposed:**
- `GET /replay/{id}` - Replay data
- `GET /replay/{id}/slice` - Replay slice

**Risk:** Any authenticated user can access replay functionality

### 5. integration.py - UNPROTECTED

```python
router = APIRouter(prefix="/integration", tags=["integration"])  # NO dependencies
```

**Endpoints exposed:**
- `GET /integration/stats` - Integration statistics
- `GET /integration/checkpoints` - Learning checkpoints
- `POST /integration/resolve` - Resolve checkpoint

**Risk:** Any authenticated user can view/modify learning pipeline

### 6. founder_explorer.py - PARTIAL

Most endpoints protected, but:

```python
@router.get("/info")
async def get_explorer_info():  # NO Depends(verify_fops_token)
```

**Gap:** `/explorer/info` endpoint has no auth

---

## Discovery Prevention Audit

### Current State

| Check | Status | Finding |
|-------|--------|---------|
| 404 vs redirect for unauthorized | REDIRECT | Wrong - reveals route existence |
| OpenAPI exposure | EXPOSED | All routes visible in `/docs` |
| Cross-console links | UNKNOWN | Not audited |

### Required Actions

1. **Return 404 (not 403)** for unauthorized founder routes
2. **Exclude from OpenAPI** using `include_in_schema=False`
3. **Audit sidebar** for cross-console links

---

## RBAC Gap Summary

### Critical Gaps (Immediate Action Required)

| Gap ID | Component | Issue | Severity |
|--------|-----------|-------|----------|
| GAP-001 | ProtectedRoute | No audience/role check | CRITICAL |
| GAP-002 | founder_timeline.py | No auth at all | CRITICAL |
| GAP-003 | traces.py | No auth at all | CRITICAL |
| GAP-004 | scenarios.py | No auth at all | CRITICAL |
| GAP-005 | replay.py | No auth at all | CRITICAL |
| GAP-006 | integration.py | No auth at all | CRITICAL |
| GAP-007 | founder_explorer.py | /info endpoint unprotected | HIGH |
| GAP-008 | ops.py | Mixed protection levels | MEDIUM |

### Existing Protections (Verified Working)

| Component | Protection | Status |
|-----------|------------|--------|
| cost_ops.py | Router-level verify_fops_token | OK |
| founder_actions.py | Endpoint-level verify_fops_token | OK |
| founder_explorer.py | Endpoint-level (except /info) | PARTIAL |

---

## Remediation Plan

### Phase 1: Backend API Hardening (Priority)

1. Add `dependencies=[Depends(verify_fops_token)]` to:
   - `founder_timeline.py`
   - `traces.py`
   - `scenarios.py`
   - `replay.py`
   - `integration.py`

2. Add `Depends(verify_fops_token)` to:
   - `founder_explorer.py:/info` endpoint

3. Consolidate `ops.py` protection to router-level

### Phase 2: Frontend Route Hardening

1. Create `FounderRoute` component with audience check
2. Wrap all `/fops/*` routes with `FounderRoute`
3. Return generic 404 for unauthorized access

### Phase 3: Discovery Prevention

1. Add `include_in_schema=False` to founder routers
2. Audit sidebar for cross-console links
3. Test unauthorized access returns 404

---

## Acceptance Criteria

- [ ] All founder API files have router-level auth
- [ ] All founder endpoints require verify_fops_token
- [ ] FounderRoute component created and applied
- [ ] 404 returned for unauthorized founder access
- [ ] Founder routes excluded from customer OpenAPI
- [ ] No cross-console links in customer sidebar

---

## Evidence Commands

```bash
# Check which APIs lack router-level auth
grep -L "dependencies=" backend/app/api/*.py | xargs basename -a

# Find endpoints without auth
grep -n "@router\." backend/app/api/founder_*.py | grep -v "Depends"

# Verify auth imports
grep -l "verify_fops_token" backend/app/api/*.py
```

---

## Related Documents

- P1_1_FOPS_CONSOLE_BOUNDARY_SPEC.md - Boundary specification
- RBAC_AUTHORITY_SEPARATION_DESIGN.md - Auth architecture
- console_auth.py - verify_fops_token implementation
