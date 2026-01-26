# Frontend Authentication Contract

**Status:** LOCKED
**Effective:** 2026-01-13
**Reference:** PIN-407, PIN-398

---

## RULE-AUTH-UI-001: Human Authentication via Clerk Only

> **The backend never authenticates humans.**
> **All human authentication happens via Clerk in the frontend.**
> **The backend only verifies identity tokens.**

---

## Architecture

```
Browser
  └── Clerk UI (SignIn/SignUp components)
        └── Clerk Session (JWT)
              └── Authorization: Bearer <jwt>
                    └── Gateway Middleware
                          └── HumanAuthContext
                                └── Route Handlers
```

---

## What the Backend NEVER Does

| Action | Why Forbidden |
|--------|---------------|
| Store passwords | Security risk, Clerk handles this |
| Validate credentials | Clerk handles this |
| Manage sessions | Clerk handles this |
| Implement `/auth/login/*` endpoints | No backend login |
| Handle MFA | Clerk handles this |
| Rate limit auth attempts | Clerk handles this |

---

## What the Backend ONLY Does

| Action | Implementation |
|--------|----------------|
| Verify JWT issuer | Gateway checks `iss` claim |
| Verify JWT signature | Gateway validates with Clerk public key |
| Extract identity | Map JWT claims to HumanAuthContext |
| Enforce authorization | RBAC rules after identity established |

---

## Frontend Requirements

### 1. ClerkProvider Wrapper

```tsx
// main.tsx
import { ClerkProvider } from '@clerk/clerk-react';

<ClerkProvider publishableKey={CLERK_KEY}>
  <App />
</ClerkProvider>
```

### 2. SignIn Component (No Custom Forms)

```tsx
// LoginPage.tsx
import { SignIn } from '@clerk/clerk-react';

export default function LoginPage() {
  return <SignIn afterSignInUrl="/console" />;
}
```

### 3. Token Flow

```tsx
// ClerkAuthSync.tsx
const { getToken } = useAuth();
const token = await getToken(); // Clerk JWT
// Token sent via Authorization header
```

---

## Console Separation

| Console | Auth Method | Token Issuer |
|---------|-------------|--------------|
| Customer Console | Clerk | clerk.agenticverz.com |
| Preflight Console | Clerk | clerk.agenticverz.com |
| Founder Console | FOPS Token | agenticverz-fops |
| Ops Console | FOPS Token | agenticverz-fops |

**Rule:** Never mix authentication methods across console types.

---

## Environment Variables

```env
# Required for Clerk
VITE_CLERK_PUBLISHABLE_KEY=pk_test_xxx

# Removed (no backend auth)
# VITE_AUTH_LOGIN_URL - deleted
```

---

## Forbidden Patterns

### ❌ Backend Login Endpoint

```python
# FORBIDDEN - do not implement
@router.post("/auth/login/password")
def login(email: str, password: str):
    ...
```

### ❌ Custom Password Form

```tsx
// FORBIDDEN - do not implement
<form onSubmit={handlePasswordLogin}>
  <input type="password" />
</form>
```

### ❌ Backend Session Management

```python
# FORBIDDEN - do not implement
sessions = {}  # No backend sessions
```

---

## Allowed Patterns

### ✅ Clerk SignIn Component

```tsx
import { SignIn } from '@clerk/clerk-react';
<SignIn />
```

### ✅ JWT Verification in Gateway

```python
# Gateway verifies, doesn't authenticate
token = request.headers.get("Authorization")
claims = verify_clerk_jwt(token)  # Signature check only
```

### ✅ Auth Sync to Store

```tsx
// For backward compatibility with existing components
const token = await getToken();
setTokens(token, '');
```

---

## Migration Notes

**Deleted:**
- `/api/v1/auth/login/password` endpoint expectation
- Custom password forms in LoginPage.tsx
- Backend session management

**Added:**
- ClerkProvider in main.tsx
- ClerkAuthSync component
- Clerk SignIn in LoginPage.tsx

---

## Enforcement

This contract is enforced by:

1. **Code Review:** No password handling in backend
2. **CI Check:** No `/auth/login/` endpoints
3. **Runtime:** Gateway rejects non-Clerk tokens for human consoles

---

## References

- PIN-407: Success as First-Class Data
- PIN-398: Founder Operations Auth
- Clerk Documentation: https://clerk.com/docs
