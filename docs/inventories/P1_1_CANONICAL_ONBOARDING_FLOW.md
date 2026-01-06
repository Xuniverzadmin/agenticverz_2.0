# P1.1-4.1 Canonical Onboarding → Console Journey

**Generated:** 2026-01-06
**Phase:** Phase 1.1 - Legacy Resolution & Structural Hardening
**Reference:** PIN-317

---

## Objective

Document the explicit user journey from first visit to console access.

---

## Journey Questions Answered

### 1. Where does `/` go?

**Answer:** `/guard` (Customer Console)

```typescript
// routes/index.tsx:162
<Route index element={<Navigate to="/guard" replace />} />
```

**Verified:** Root path redirects to customer console.

---

### 2. Where does `/login` go after success?

**Answer:** Depends on onboarding status

```typescript
// LoginPage.tsx:70-75
if (onboardingComplete) {
  navigate('/dashboard', { replace: true });  // → /guard via catch-all
} else {
  navigate('/onboarding/connect', { replace: true });
}
```

**Flow:**
- Onboarding NOT complete → `/onboarding/connect`
- Onboarding complete → `/dashboard` → catch-all → `/guard`

**Issue:** `/dashboard` used as destination but doesn't exist as route.

---

### 3. What is the first screen after onboarding?

**Answer:** `/guard` (Customer Console Overview)

```typescript
// CompletePage.tsx:16
navigate('/guard', { replace: true });
```

**Verified:** Onboarding completion goes directly to customer console.

---

### 4. Is the journey explicit in routes?

**Answer:** PARTIAL - mostly explicit, one gap

| Transition | Source | Destination | Explicit? |
|------------|--------|-------------|-----------|
| First visit | `/` | `/guard` | YES |
| Unauthenticated | any | `/login` | YES |
| Login (not onboarded) | `/login` | `/onboarding/connect` | YES |
| Login (onboarded) | `/login` | `/dashboard` | NO - uses catch-all |
| Onboarding steps | `/onboarding/X` | `/onboarding/Y` | YES |
| Onboarding complete | `/onboarding/complete` | `/guard` | YES |
| Unknown path | `/*` | `/guard` | YES (catch-all) |

---

## Complete User Journey Map

```
┌─────────────────────────────────────────────────────────────┐
│                    USER JOURNEY                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   FIRST VISIT                                               │
│   ───────────                                               │
│   User visits agenticverz.com                               │
│           ↓                                                 │
│   /  ──────────────────────────────────→  /guard            │
│                                           (Customer Console) │
│                                                              │
│   NOT AUTHENTICATED                                          │
│   ─────────────────                                          │
│   Any protected route                                        │
│           ↓                                                 │
│   ProtectedRoute checks isAuthenticated                      │
│           ↓ (false)                                         │
│   /login                                                     │
│                                                              │
│   LOGIN SUCCESS (NEW USER)                                   │
│   ────────────────────────                                   │
│   User completes login                                       │
│           ↓                                                 │
│   onboardingComplete = false                                 │
│           ↓                                                 │
│   /onboarding/connect                                        │
│           ↓                                                 │
│   /onboarding/safety                                         │
│           ↓                                                 │
│   /onboarding/alerts                                         │
│           ↓                                                 │
│   /onboarding/verify                                         │
│           ↓                                                 │
│   /onboarding/complete                                       │
│           ↓                                                 │
│   /guard  (Customer Console)                                 │
│                                                              │
│   LOGIN SUCCESS (RETURNING USER)                             │
│   ──────────────────────────────                             │
│   User completes login                                       │
│           ↓                                                 │
│   onboardingComplete = true                                  │
│           ↓                                                 │
│   /dashboard  ────→  catch-all  ────→  /guard               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Route Guards Summary

### ProtectedRoute

**Location:** `routes/ProtectedRoute.tsx`

```typescript
if (!isAuthenticated) → /login
if (!onboardingComplete) → /onboarding/connect
else → render children
```

### OnboardingRoute

**Location:** `routes/OnboardingRoute.tsx`

```typescript
if (!isAuthenticated) → /login
if (onboardingComplete) → /dashboard  // GAP: should be /guard
else → render children
```

---

## Issues Found

### Issue 1: `/dashboard` Ghost Route

**Location:** Multiple files reference `/dashboard` but it doesn't exist

| File | Line | Reference |
|------|------|-----------|
| LoginPage.tsx | 71 | `navigate('/dashboard', { replace: true })` |
| OnboardingRoute.tsx | 19 | `<Navigate to="/dashboard" replace />` |
| CompletePage.tsx | 21 | `navigate('/dashboard', { replace: true })` |

**Impact:** Low - catch-all redirects to `/guard`, but journey is not explicit

**Recommendation:** Replace all `/dashboard` references with `/guard`

### Issue 2: Inconsistent Destination in CompletePage

**Location:** `CompletePage.tsx`

```typescript
// Line 16 - onClick handler
navigate('/guard', { replace: true });

// Line 21 - somewhere else
navigate('/dashboard', { replace: true });
```

**Impact:** Inconsistent behavior depending on how user completes onboarding

**Recommendation:** Standardize to `/guard`

---

## Recommended Fixes

### Fix 1: LoginPage.tsx

```typescript
// Before
if (onboardingComplete) {
  navigate('/dashboard', { replace: true });

// After
if (onboardingComplete) {
  navigate('/guard', { replace: true });
```

### Fix 2: OnboardingRoute.tsx

```typescript
// Before
if (onboardingComplete) {
  return <Navigate to="/dashboard" replace />;

// After
if (onboardingComplete) {
  return <Navigate to="/guard" replace />;
```

### Fix 3: CompletePage.tsx

```typescript
// Standardize all navigation to /guard
navigate('/guard', { replace: true });
```

---

## Onboarding Pages Sequence

| Step | Route | Page | Purpose |
|------|-------|------|---------|
| 1 | `/onboarding/connect` | ConnectPage | Connect to tenant |
| 2 | `/onboarding/safety` | SafetyPage | Safety settings |
| 3 | `/onboarding/alerts` | AlertsPage | Alert preferences |
| 4 | `/onboarding/verify` | VerifyPage | Verify configuration |
| 5 | `/onboarding/complete` | CompletePage | Completion confirmation |

**Note:** Steps are sequential but not enforced by routes. User could navigate directly to any step.

---

## Backend API Support

| Endpoint | Purpose | Used By |
|----------|---------|---------|
| `POST /api/v1/auth/login` | Authentication | LoginPage |
| `GET /api/v1/tenants/me` | Current tenant | ConnectPage |
| `POST /api/v1/onboarding/complete` | Mark complete | CompletePage |
| `GET /api/v1/auth/session` | Session validation | All routes |

---

## Console Entry Points

| Console | Route | Entry Component |
|---------|-------|-----------------|
| Customer | `/guard/*` | AIConsoleApp |
| Founder/Ops | `/ops/*` | OpsConsoleEntry |
| Founder Pages | Various legacy | AppLayout (via ProtectedRoute) |

**Issue:** Founder pages under AppLayout share same layout as could-be customer pages.

---

## Journey Verification Checklist

| Check | Status | Notes |
|-------|--------|-------|
| `/` → `/guard` | OK | Explicit redirect |
| `/login` is public | OK | No route guard |
| Auth failure → `/login` | OK | ProtectedRoute handles |
| Not onboarded → `/onboarding/connect` | OK | ProtectedRoute handles |
| Onboarding steps in sequence | PARTIAL | Not enforced |
| Onboarding complete → `/guard` | PARTIAL | Uses `/dashboard` ghost |
| Returning user → `/guard` | PARTIAL | Uses `/dashboard` ghost |
| Unknown path → `/guard` | OK | Catch-all handles |

---

## Acceptance Criteria

- [x] Journey from `/` documented
- [x] Journey from `/login` documented
- [x] First screen after onboarding identified
- [x] Route explicitness audited
- [x] Issues found and documented
- [ ] Ghost route `/dashboard` fixed (requires code change)

---

## Related Documents

- routes/index.tsx - Main route configuration
- routes/ProtectedRoute.tsx - Auth guard
- routes/OnboardingRoute.tsx - Onboarding guard
- pages/onboarding/* - Onboarding pages
