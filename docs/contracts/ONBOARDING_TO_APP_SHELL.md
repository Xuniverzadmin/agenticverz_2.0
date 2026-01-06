# Onboarding to App-Shell Handoff Contract

**Status:** NORMATIVE
**Effective:** 2026-01-06
**Reference:** PIN-319 (Frontend Realignment), R3-1

---

## Purpose

This contract defines the handoff protocol between the onboarding flow
(`website/onboarding/`) and the main application shell (`website/app-shell/`).

---

## Flow Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        ONBOARDING FLOW                          │
│                                                                 │
│  /onboarding/connect → /onboarding/safety → /onboarding/alerts  │
│            ↓                                                    │
│  /onboarding/verify → /onboarding/complete                      │
│            ↓                                                    │
│        SET: onboardingComplete = true                           │
│        REDIRECT: /guard (customer console)                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Authentication Prerequisites

### Required JWT Claims

Before entering onboarding, the user must have a valid JWT with:

| Claim | Type | Required | Description |
|-------|------|----------|-------------|
| `sub` | string | YES | User ID |
| `tenant_id` | string | YES | Tenant ID |
| `email` | string | YES | User email |
| `aud` | string | YES | Audience (`console` for customer) |
| `exp` | number | YES | Expiration timestamp |

### Auth State

```typescript
interface OnboardingAuthState {
  isAuthenticated: true;
  tenantId: string;
  userId: string;
  onboardingComplete: false;  // Must be false to enter onboarding
}
```

---

## 2. Onboarding Flow Steps

| Step | Route | Purpose | Required Actions |
|------|-------|---------|------------------|
| 1 | `/onboarding/connect` | API key setup | Generate/validate API key |
| 2 | `/onboarding/safety` | Safety preferences | Configure safety settings |
| 3 | `/onboarding/alerts` | Alert configuration | Set up alerts |
| 4 | `/onboarding/verify` | Verify setup | Confirm all settings |
| 5 | `/onboarding/complete` | Completion | Final confirmation |

### Step Requirements

- Each step must be completed in order
- Backend validates step completion
- User cannot skip steps

---

## 3. Handoff Protocol

### On Completion

When the user completes `/onboarding/complete`:

```typescript
// 1. Backend marks onboarding complete
await api.post('/api/v1/onboarding/complete', { tenant_id });

// 2. Update local auth state
authStore.setState({ onboardingComplete: true });

// 3. Redirect to customer console
navigate('/guard', { replace: true });
```

### State After Handoff

```typescript
interface PostOnboardingAuthState {
  isAuthenticated: true;
  tenantId: string;
  userId: string;
  onboardingComplete: true;  // Now true
}
```

---

## 4. Route Guards

### OnboardingRoute Guard

```typescript
// website/app-shell/src/routes/OnboardingRoute.tsx

function OnboardingRoute({ children }) {
  const { isAuthenticated, onboardingComplete } = useAuthStore();

  // Not authenticated → login
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Already completed → customer console
  if (onboardingComplete) {
    return <Navigate to="/guard" replace />;
  }

  // Show onboarding
  return children;
}
```

### ProtectedRoute Guard (App-Shell)

```typescript
// website/app-shell/src/routes/ProtectedRoute.tsx

function ProtectedRoute({ children }) {
  const { isAuthenticated, onboardingComplete } = useAuthStore();

  // Not authenticated → login
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Not onboarded → onboarding
  if (!onboardingComplete) {
    return <Navigate to="/onboarding/connect" replace />;
  }

  // Show protected content
  return children;
}
```

---

## 5. Failure Modes

### Invalid Token

**Trigger:** JWT missing, expired, or invalid
**Response:** Redirect to `/login`
**Log:** `AUTH_INVALID_TOKEN`

### Missing Tenant

**Trigger:** `tenant_id` claim missing
**Response:** Redirect to `/login` with error
**Log:** `AUTH_MISSING_TENANT`

### Incomplete Onboarding (accessing /guard)

**Trigger:** User accesses `/guard/*` with `onboardingComplete: false`
**Response:** Redirect to `/onboarding/connect`
**Log:** `ONBOARDING_INCOMPLETE`

### Re-entering Onboarding (completed user)

**Trigger:** User accesses `/onboarding/*` with `onboardingComplete: true`
**Response:** Redirect to `/guard`
**Log:** `ONBOARDING_ALREADY_COMPLETE`

---

## 6. Backend Contract

### Onboarding Status Endpoint

```
GET /api/v1/onboarding/status
Authorization: Bearer <token>

Response:
{
  "tenant_id": "...",
  "onboarding_complete": boolean,
  "current_step": "connect" | "safety" | "alerts" | "verify" | "complete",
  "completed_steps": ["connect", "safety", ...]
}
```

### Onboarding Complete Endpoint

```
POST /api/v1/onboarding/complete
Authorization: Bearer <token>

Request:
{
  "tenant_id": "..."
}

Response:
{
  "success": true,
  "onboarding_complete": true
}
```

---

## 7. Testing Requirements

### Manual Smoke Test (R3-2)

1. Login as new user (onboardingComplete: false)
2. Verify redirect to `/onboarding/connect`
3. Complete all onboarding steps
4. Verify redirect to `/guard`
5. Verify cannot re-enter `/onboarding/*`
6. Verify founder console is blocked

### Automated Tests (Phase 2)

- [ ] Unit tests for route guards
- [ ] Integration tests for onboarding flow
- [ ] E2E tests for complete journey

---

## 8. References

- PIN-319: Frontend Realignment
- `website/app-shell/src/routes/OnboardingRoute.tsx`
- `website/app-shell/src/routes/ProtectedRoute.tsx`
- `website/onboarding/src/pages/`
