# P1.2-1 Authority Model Formalization

**Generated:** 2026-01-06
**Phase:** Phase 1.2 - Authority & Boundary Hardening
**Reference:** PIN-318

---

## Objective

Remove implicit trust. Define audiences and roles explicitly with allowed surfaces.

---

## P1.2-1.1 Audience Definitions

### Backend Authority (console_auth.py)

| Audience | Token Value | Description | Allowed Surfaces |
|----------|-------------|-------------|------------------|
| **aos-customer** | `aud="console"` | Customer Console users | `/guard/*`, `/api/v1/guard/*` |
| **aos-founder** | `aud="fops"` | Founder Ops Console users | `/fops/*`, `/ops/*`, `/api/v1/ops/*`, founder APIs |

### Token Structure

**CustomerToken (aud="console"):**
```python
@dataclass
class CustomerToken:
    aud: Literal["console"]      # MUST be exactly "console"
    sub: str                     # user_id
    org_id: str                  # organization_id (tenant isolation)
    role: CustomerRole           # OWNER | ADMIN | DEV | VIEWER
    iss: str                     # "agenticverz"
    exp: int                     # expiration timestamp
```

**FounderToken (aud="fops"):**
```python
@dataclass
class FounderToken:
    aud: Literal["fops"]         # MUST be exactly "fops"
    sub: str                     # founder_id
    role: FounderRole            # FOUNDER | OPERATOR
    mfa: bool                    # MUST be true
    iss: str                     # "agenticverz"
    exp: int                     # expiration timestamp
```

### Audience Derivation Points

| Layer | Component | Derivation Method |
|-------|-----------|-------------------|
| L6 (Backend) | `console_auth.py` | JWT `aud` claim parsing |
| L2 (API) | Route middleware | `Depends(verify_console_token)` or `Depends(verify_fops_token)` |
| L1 (Frontend) | `authStore.ts` | **GAP: No audience stored** |

### Backend Middleware

| Middleware | Audience | Target Routes | File |
|------------|----------|---------------|------|
| `verify_console_token` | `console` | `/guard/*` | `console_auth.py:395` |
| `verify_fops_token` | `fops` | `/ops/*` | `console_auth.py:509` |

### Cookie Isolation

| Cookie Name | Audience | Domain (Production) |
|-------------|----------|---------------------|
| `aos_console_session` | `console` | `console.agenticverz.com` |
| `aos_fops_session` | `fops` | `fops.agenticverz.com` |

---

## P1.2-1.2 Role Definitions

### CustomerRole (for aud="console")

| Role | Description | Typical Permissions |
|------|-------------|---------------------|
| **OWNER** | Tenant owner | Full access to tenant |
| **ADMIN** | Tenant administrator | Manage users, settings |
| **DEV** | Developer | View, manage runs |
| **VIEWER** | Read-only | View only |

### FounderRole (for aud="fops")

| Role | Description | Typical Permissions |
|------|-------------|---------------------|
| **FOUNDER** | System founder | Full system access |
| **OPERATOR** | Operations team | Ops console access |

### Role-Surface Matrix

#### Customer Roles → Customer Surfaces

| Surface | OWNER | ADMIN | DEV | VIEWER |
|---------|-------|-------|-----|--------|
| `/guard/overview` | YES | YES | YES | YES |
| `/guard/activity` | YES | YES | YES | YES |
| `/guard/incidents` | YES | YES | YES | YES |
| `/guard/policies` | YES | YES | YES | VIEW |
| `/guard/logs` | YES | YES | YES | YES |
| `/guard/integrations` | YES | YES | YES | VIEW |
| `/guard/keys` | YES | YES | NO | NO |
| `/guard/settings` | YES | YES | NO | NO |
| `/guard/account` | YES | YES | NO | NO |

#### Founder Roles → Founder Surfaces

| Surface | FOUNDER | OPERATOR |
|---------|---------|----------|
| `/ops/*` | YES | YES |
| `/traces/*` | YES | YES |
| `/recovery/*` | YES | YES |
| `/sba/*` | YES | YES |
| `/integration/*` | YES | YES |
| `/fdr/timeline` | YES | YES |
| `/fdr/controls` | YES | NO |
| `/fdr/replay` | YES | YES |
| `/fdr/scenarios` | YES | YES |
| `/fdr/explorer` | YES | YES |
| `/workers/*` | YES | YES |
| `/credits/*` | YES | YES |

---

## Authority Enforcement Points

### Backend (L2 API Layer) — ALL HARDENED ✅

| API File | Auth Status | Reference |
|----------|-------------|-----------|
| `guard/*.py` | `verify_console_token` | OK |
| `cost_ops.py` | `verify_fops_token` | OK |
| `founder_actions.py` | `verify_fops_token` | OK |
| `founder_explorer.py` | `verify_fops_token` (router-level) | ✅ FIXED P1.2-4.1 |
| `founder_timeline.py` | `verify_fops_token` (router-level) | ✅ FIXED P1.2-3.2 |
| `traces.py` | JWT + tenant isolation | OK (shared access) |
| `scenarios.py` | `verify_fops_token` (router-level) | ✅ FIXED P1.2-3.2 |
| `replay.py` | `require_replay_read` (RBAC) | OK |
| `integration.py` | `verify_fops_token` (router-level) | ✅ FIXED P1.2-3.2 |
| `ops.py` | `verify_fops_token` (router-level) | OK |
| `recovery.py` | `verify_fops_token` (router-level) | ✅ FIXED P1.2-4.1 |
| `workers.py` | `verify_api_key` (SDK auth) | OK (different model) |

### Frontend (L1 UI Layer)

| Component | Current Auth | Required Auth |
|-----------|--------------|---------------|
| `ProtectedRoute` | `isAuthenticated + onboardingComplete` | **ADD** `audience + role` |
| Customer routes | Via ProtectedRoute | OK after hardening |
| Founder routes | Via ProtectedRoute | **NEED** `FounderRoute` |

---

## Frontend Authority Gap Analysis

### Current authStore State

```typescript
interface AuthState {
  token: string | null;
  refreshToken: string | null;
  tenantId: string | null;
  user: User | null;           // Has role, but no audience
  isAuthenticated: boolean;
  onboardingComplete: boolean;
  // MISSING: audience
  // MISSING: is_founder / is_superuser
}
```

### Required Additions

```typescript
interface AuthState {
  // ... existing fields ...
  audience: 'console' | 'fops' | null;  // NEW
  is_founder: boolean;                   // NEW
}
```

### ProtectedRoute Current Implementation

```typescript
// Current (INSUFFICIENT)
export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, onboardingComplete } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }
  if (!onboardingComplete) {
    return <Navigate to="/onboarding/connect" />;
  }
  return <>{children}</>;  // NO audience check!
}
```

### Required Implementation

```typescript
// Required (WITH audience check)
interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredAudience?: 'console' | 'fops';
  requiredRole?: string[];
}

export function ProtectedRoute({
  children,
  requiredAudience,
  requiredRole
}: ProtectedRouteProps) {
  const { isAuthenticated, onboardingComplete, audience, user } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }
  if (!onboardingComplete) {
    return <Navigate to="/onboarding/connect" />;
  }

  // Audience check
  if (requiredAudience && audience !== requiredAudience) {
    return <Navigate to="/guard" />;  // Or show 404
  }

  // Role check
  if (requiredRole && user && !requiredRole.includes(user.role)) {
    return <Navigate to="/guard" />;  // Or show 403
  }

  return <>{children}</>;
}
```

---

## Authority Invariants

### INV-AUTH-001: Token Audience Immutability
> A token's audience cannot be changed after creation. A customer token cannot become a founder token.

### INV-AUTH-002: Audience-Surface Binding
> A request with `aud="console"` MUST be rejected from `/ops/*` routes. A request with `aud="fops"` MAY access any route (superuser).

### INV-AUTH-003: MFA Requirement for Founders
> `aud="fops"` tokens MUST have `mfa=true`. Token creation without MFA is rejected.

### INV-AUTH-004: No Shared Cookies
> `aos_console_session` and `aos_fops_session` are separate. Never combine or share.

### INV-AUTH-005: Explicit Denial
> Customer tokens attempting founder routes MUST receive 403/404, never silent redirect.

---

## Cross-Reference to Gaps (ALL RESOLVED ✅)

| Gap ID | Description | Fix Reference | Status |
|--------|-------------|---------------|--------|
| GAP-001 | ProtectedRoute lacks audience check | P1.2-2.1 (FounderRoute) | ✅ FIXED |
| GAP-002 | founder_timeline.py no auth | P1.2-3.2 | ✅ FIXED |
| GAP-003 | traces.py no auth | N/A (JWT + tenant isolation) | ✅ OK |
| GAP-004 | scenarios.py no auth | P1.2-3.2 | ✅ FIXED |
| GAP-005 | replay.py no auth | N/A (RBAC authority) | ✅ OK |
| GAP-006 | integration.py no auth | P1.2-3.2 | ✅ FIXED |
| GAP-007 | founder_explorer.py /info unprotected | P1.2-4.1 | ✅ FIXED |
| GAP-008 | ops.py mixed protection | Verified OK | ✅ OK |
| GAP-009 | recovery.py no auth | P1.2-4.1 | ✅ FIXED |

---

## Acceptance Criteria

- [x] Audience semantics documented (`aos-customer`, `aos-founder`)
- [x] Audience → allowed surfaces mapped
- [x] Token structures documented
- [x] Derivation points identified (JWT, middleware, store)
- [x] Role semantics documented (CustomerRole, FounderRole)
- [x] Role → surface permissions documented
- [x] Frontend authority gap identified (authStore lacks audience)
- [x] Required ProtectedRoute changes documented

---

## Related Documents

- `backend/app/auth/console_auth.py` - Backend authority implementation
- `website/app-shell/src/stores/authStore.ts` - Frontend state
- `website/app-shell/src/routes/ProtectedRoute.tsx` - Route guard
- `P1_1_FOPS_RBAC_HARDENING_AUDIT.md` - RBAC gap findings
