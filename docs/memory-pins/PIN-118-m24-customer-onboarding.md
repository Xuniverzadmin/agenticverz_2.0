# PIN-118: M24 Customer Onboarding - OAuth & Email Verification

**Status:** DEPLOYED
**Created:** 2025-12-21
**Category:** Authentication / Onboarding
**Migration:** 040_m24_onboarding (Applied)

---

## Summary

Implemented customer onboarding system with three authentication methods:
1. **Google OAuth** - Sign in with Google
2. **Azure AD OAuth** - Sign in with Microsoft
3. **Email OTP** - Email-based signup with 6-digit verification code

---

## Components

### 1. OAuth Providers (`backend/app/auth/oauth_providers.py`)

**Google OAuth:**
- Authorization URL generation with state
- Code exchange for tokens
- User info retrieval from Google API
- Email verification check

**Azure AD OAuth:**
- Multi-tenant support (`AZURE_TENANT_ID`)
- Microsoft Graph API integration
- User info retrieval

**Configuration:**
```bash
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
AZURE_CLIENT_ID=...
AZURE_CLIENT_SECRET=...
AZURE_TENANT_ID=common  # or specific tenant
OAUTH_REDIRECT_BASE=https://agenticverz.com
```

### 2. Email Verification (`backend/app/services/email_verification.py`)

**Features:**
- 6-digit OTP generation (cryptographically secure)
- Redis-based storage with TTL (10 minutes default)
- Rate limiting (60 second cooldown between requests)
- Attempt tracking (max 3 attempts)
- HTML + text email templates via Resend API

**Configuration:**
```bash
RESEND_API_KEY=...
EMAIL_FROM=Agenticverz <noreply@agenticverz.com>
EMAIL_VERIFICATION_TTL=600  # 10 minutes
REDIS_URL=redis://localhost:6379/0
```

### 3. Onboarding API (`backend/app/api/onboarding.py`)

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login/google` | Initiate Google OAuth |
| GET | `/api/v1/auth/callback/google` | Google OAuth callback |
| POST | `/api/v1/auth/login/azure` | Initiate Azure OAuth |
| GET | `/api/v1/auth/callback/azure` | Azure OAuth callback |
| POST | `/api/v1/auth/signup/email` | Send OTP to email |
| POST | `/api/v1/auth/verify/email` | Verify OTP, create user |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Invalidate session |
| GET | `/api/v1/auth/me` | Get current user |
| GET | `/api/v1/auth/providers` | List available providers |

**Token Management:**
- JWT-based access tokens (24 hour default)
- Refresh tokens with Redis-backed revocation (7 day default)
- Configurable via `JWT_SECRET`, `SESSION_TTL_HOURS`, `REFRESH_TTL_DAYS`

### 4. Database Migration (`alembic/versions/040_m24_onboarding.py`)

**Columns added to `users` table:**
- `oauth_provider` - Provider name (google, azure, email)
- `oauth_provider_id` - Provider's user ID
- `email_verified` - Email verification status
- `email_verified_at` - Timestamp of verification

---

## User Flow

### OAuth Flow (Google/Azure)
```
1. User clicks "Sign in with Google"
2. Frontend calls POST /api/v1/auth/login/google
3. Backend returns authorization_url + state
4. Frontend redirects to Google
5. User authorizes
6. Google redirects to /api/v1/auth/callback/google?code=...&state=...
7. Backend exchanges code for tokens
8. Backend fetches user info
9. Backend creates/updates user + tenant
10. Backend redirects to frontend with access_token + refresh_token
```

### Email Flow
```
1. User enters email
2. Frontend calls POST /api/v1/auth/signup/email
3. Backend sends OTP via Resend
4. User enters OTP
5. Frontend calls POST /api/v1/auth/verify/email
6. Backend verifies OTP
7. Backend creates/updates user + tenant
8. Backend returns access_token + refresh_token
```

---

## Auto-Provisioning

When a new user signs up:
1. User record created in `users` table
2. Personal tenant created (name: "{email}'s Workspace")
3. Owner membership created in `tenant_memberships`
4. `default_tenant_id` set on user

---

## Security Features

- **CSRF Protection:** State parameter for OAuth flows
- **Rate Limiting:** 60-second cooldown between OTP requests
- **Attempt Limiting:** Max 3 OTP verification attempts
- **Token Revocation:** Redis-backed refresh token invalidation
- **Email Hashing:** Redis keys use SHA-256 hash of email

---

## Files Created/Modified

**Created:**
- `backend/app/auth/oauth_providers.py`
- `backend/app/services/email_verification.py`
- `backend/app/api/onboarding.py`
- `backend/alembic/versions/040_m24_onboarding.py`

**Modified:**
- `backend/app/main.py` - Router registration
- `backend/app/models/tenant.py` - User model OAuth fields

---

## Environment Variables

```bash
# OAuth
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
AZURE_TENANT_ID=common
OAUTH_REDIRECT_BASE=https://agenticverz.com

# Email
RESEND_API_KEY=
EMAIL_FROM=Agenticverz <noreply@agenticverz.com>
EMAIL_VERIFICATION_TTL=600

# Session
JWT_SECRET=  # Auto-generated if not set
SESSION_TTL_HOURS=24
REFRESH_TTL_DAYS=7

# Frontend
FRONTEND_URL=https://agenticverz.com
```

---

## Testing

```bash
# Check available providers
curl https://agenticverz.com/api/v1/auth/providers

# Initiate Google OAuth
curl -X POST https://agenticverz.com/api/v1/auth/login/google

# Send OTP
curl -X POST https://agenticverz.com/api/v1/auth/signup/email \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "name": "Test User"}'

# Verify OTP
curl -X POST https://agenticverz.com/api/v1/auth/verify/email \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "otp": "123456"}'
```

---

## Deployment Verification

```bash
# All endpoints verified working (2025-12-21)
curl https://agenticverz.com/api/v1/auth/providers
# → google: enabled, azure: enabled, email: enabled

curl -X POST https://agenticverz.com/api/v1/auth/login/google
# → Returns authorization_url with correct redirect_uri

curl -X POST https://agenticverz.com/api/v1/auth/signup/email \
  -d '{"email": "test@example.com"}'
# → OTP sent via Resend (confirmed delivery)
```

---

## Frontend Onboarding UI

### 5. Login Page (`website/aos-console/console/src/pages/auth/LoginPage.tsx`)

**Features:**
- Google OAuth button (Continue with Google)
- Microsoft OAuth button (Continue with Microsoft)
- Email OTP flow (Continue with Email)
- 6-digit OTP input with countdown timer
- Auto-redirect on successful auth

### 6. Onboarding Flow

**5-Step Onboarding Wizard:**

| Step | Route | Purpose |
|------|-------|---------|
| 1 | `/onboarding/connect` | Display API key, quick start code |
| 2 | `/onboarding/safety` | Configure killswitch, auto-block, budget limits |
| 3 | `/onboarding/alerts` | Set up email/Slack notifications |
| 4 | `/onboarding/verify` | **REAL** guardrail test - creates actual incident |
| 5 | `/onboarding/complete` | "Your AI is Now Protected" with active status |

**Files Created:**
- `src/pages/onboarding/OnboardingLayout.tsx` - Shared layout with progress bar
- `src/pages/onboarding/ConnectPage.tsx` - API key display
- `src/pages/onboarding/SafetyPage.tsx` - Safety defaults configuration
- `src/pages/onboarding/AlertsPage.tsx` - Notification channel setup
- `src/pages/onboarding/VerifyPage.tsx` - Safety test
- `src/pages/onboarding/CompletePage.tsx` - Onboarding success

**Routing:**
- `src/routes/OnboardingRoute.tsx` - Auth required, not onboarding complete
- `src/routes/ProtectedRoute.tsx` - Updated to redirect to onboarding if incomplete
- `src/stores/authStore.ts` - Added `onboardingComplete`, `onboardingStep` state

---

## Next Steps

- [x] Wire Google OAuth credentials in Vault
- [x] Wire Azure OAuth credentials in Vault
- [x] Run migration 040_m24_onboarding
- [x] Verify email delivery (Resend)
- [x] Create frontend login/signup pages
- [x] Add social login buttons to console
- [x] Build 5-step onboarding wizard
- [x] Implement hybrid auth in Guard Console (OAuth primary, API key fallback)
- [x] Deploy and verify Guard Console login flow
- [ ] Add redirect URIs in Google Cloud Console (external portal)
- [ ] Add redirect URIs in Azure Portal (external portal)

---

## Verification (2025-12-21)

```bash
# Auth providers check
curl https://agenticverz.com/api/v1/auth/providers
# → google: enabled, azure: enabled, email: enabled

# Guard Console accessible
curl https://agenticverz.com/console/guard
# → HTML loads with React app

# JS bundle contains all login options
# ✅ "Sign in with Google or Microsoft"
# ✅ "or use API key"
# ✅ "Try Demo Mode"
```

**Status: DEPLOYED AND VERIFIED**

---

## M24.1 Update: REAL Safety Verification (2025-12-21)

### Problem Solved
Step 4 was previously a simulation - users could sense it was fake. Now it:
1. Evaluates REAL guardrails (same logic as proxy)
2. Creates REAL incidents in the database
3. Shows REAL incident in Guard Console
4. Demonstrates experienced safety, not perceived safety

### New Endpoint: `/guard/onboarding/verify`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/guard/onboarding/verify?tenant_id=X` | Real guardrail evaluation |

**Request:**
```json
{
  "test_type": "guardrail_block",  // or "killswitch_demo"
  "trigger_alert": false
}
```

**Response:**
```json
{
  "success": true,
  "was_blocked": true,
  "blocked_by": "prompt_injection_block",
  "incident_id": "inc_verify_196269a9",
  "message": "Your guardrails are actively protecting your AI."
}
```

### Test Types

| Type | What It Does |
|------|--------------|
| `guardrail_block` | Fires prompt injection pattern, triggers block |
| `killswitch_demo` | Shows what cost-spike protection looks like |

### Files Modified

- `backend/app/api/guard.py` - Added `/guard/onboarding/verify` endpoint
- `website/aos-console/console/src/pages/onboarding/VerifyPage.tsx` - Calls real endpoint
- `website/aos-console/console/src/pages/onboarding/CompletePage.tsx` - Active protection messaging

### Verification

```bash
# Test guardrail block
curl -X POST "https://agenticverz.com/guard/onboarding/verify?tenant_id=demo-tenant" \
  -H "Content-Type: application/json" \
  -d '{"test_type": "guardrail_block"}'
# → incident_id: inc_verify_XXXXX (visible in /guard/incidents)

# Incidents appear in Guard Console
curl "https://agenticverz.com/guard/incidents?tenant_id=demo-tenant"
# → Shows verification incidents with title "Safety Test: Guardrail Blocked"
```

**Key Insight:** Replace perceived safety with experienced safety.
