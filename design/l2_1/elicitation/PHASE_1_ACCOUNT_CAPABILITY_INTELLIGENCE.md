# PHASE 1 — CAPABILITY INTELLIGENCE EXTRACTION
## Domain: Account (Secondary Navigation - Top-right/Footer)

**Status:** EVIDENCE-BACKED
**Date:** 2026-01-07
**Category:** Secondary Navigation / Account Management
**L2.1 Surfaces:** NOT IN L2.1 SEED (account is NOT a domain per Constitution)

---

## EXECUTIVE SUMMARY

The Account section covers authentication, session management, tenant info, and settings:
- **Auth/Session:** IMPLEMENTED (onboarding.py)
- **Tenant Info:** IMPLEMENTED (tenants.py)
- **Settings (Read-only):** IMPLEMENTED (guard.py)
- **Billing/Plans:** NOT IMPLEMENTED
- **Account Admin (RBAC):** Founder Console only (rbac_api.py)
- **Account Deletion:** NOT IMPLEMENTED

**Critical Finding:** Per Customer Console v1 Constitution:
> "Account is NOT a domain. It manages *who*, *what*, and *billing* — not *what happened*.
> Account pages must NOT display executions, incidents, policies, or logs."

Account is NOT in the L2.1 frozen seed surfaces.

---

## OUTPUT 1 — DERIVED CAPABILITY INTELLIGENCE TABLE

### Auth/Session Capabilities (onboarding.py)

---

### Capability: CAP-AUTH-LOGIN-GOOGLE (Google OAuth Login)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-AUTH-LOGIN-GOOGLE` | `onboarding.py:356` |
| capability_name | Google OAuth Login | `POST /api/v1/auth/login/google` |
| description | Initiate Google OAuth login flow | `onboarding.py:356-382` |
| mode | **READ** | Returns authorization URL |
| scope | **SINGLE** | Single user session |
| mutates_state | **YES** | Stores state in Redis |
| bulk_support | **NO** | Single entity |
| latency_profile | **LOW** | OAuth URL generation |
| execution_style | **ASYNC** | `onboarding.py:357` |
| reversibility | **N/A** | State expires automatically |
| authority_required | **NONE** | Public endpoint |
| adapters | None | Direct OAuth provider |
| operators | `GoogleOAuthProvider.get_authorization_url()` | `oauth_providers.py` |
| input_contracts | `OAuthLoginRequest (optional redirect_url)` | `onboarding.py:82-85` |
| output_contracts | `OAuthLoginResponse {authorization_url, state}` | `onboarding.py:88-92` |
| side_effects | **State stored in Redis** | 10 min TTL |
| failure_modes | 503 OAuth not configured, 400 OAuth error | `onboarding.py:365-367, 381-382` |
| confidence_level | **HIGH** | Full code evidence |
| evidence_refs | `onboarding.py:356-382` |
| l2_1_aligned | **NOT IN SEED** | Account not in L2.1 |
| risk_flags | Requires Google OAuth configuration |

---

### Capability: CAP-AUTH-LOGIN-AZURE (Azure OAuth Login)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-AUTH-LOGIN-AZURE` | `onboarding.py:443` |
| capability_name | Azure OAuth Login | `POST /api/v1/auth/login/azure` |
| description | Initiate Azure AD OAuth login flow | `onboarding.py:443-469` |
| mode | **READ** | Returns authorization URL |
| scope | **SINGLE** | Single user session |
| mutates_state | **YES** | Stores state in Redis |
| bulk_support | **NO** | Single entity |
| latency_profile | **LOW** | OAuth URL generation |
| execution_style | **ASYNC** | `onboarding.py:444` |
| reversibility | **N/A** | State expires automatically |
| authority_required | **NONE** | Public endpoint |
| adapters | None | Direct OAuth provider |
| operators | `AzureOAuthProvider.get_authorization_url()` | `oauth_providers.py` |
| input_contracts | `OAuthLoginRequest (optional redirect_url)` | `onboarding.py:82-85` |
| output_contracts | `OAuthLoginResponse {authorization_url, state}` | `onboarding.py:88-92` |
| side_effects | **State stored in Redis** | 10 min TTL |
| failure_modes | 503 OAuth not configured, 400 OAuth error | `onboarding.py:452-454, 468-469` |
| confidence_level | **HIGH** | Full code evidence |
| evidence_refs | `onboarding.py:443-469` |
| l2_1_aligned | **NOT IN SEED** | Account not in L2.1 |
| risk_flags | Requires Azure OAuth configuration |

---

### Capability: CAP-AUTH-SIGNUP-EMAIL (Email Signup)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-AUTH-SIGNUP-EMAIL` | `onboarding.py:531` |
| capability_name | Email Signup | `POST /api/v1/auth/signup/email` |
| description | Initiate email-based signup with OTP | `onboarding.py:531-548` |
| mode | **WRITE** | Sends OTP email |
| scope | **SINGLE** | Single user |
| mutates_state | **YES** | Stores OTP in Redis |
| bulk_support | **NO** | Single entity |
| latency_profile | **MEDIUM** | Email sending |
| execution_style | **ASYNC** | `onboarding.py:532` |
| reversibility | **N/A** | OTP expires automatically |
| authority_required | **NONE** | Public endpoint |
| adapters | None | Direct service |
| operators | `EmailVerificationService.send_otp()` | `email_verification.py` |
| input_contracts | `EmailSignupRequest {email, name?}` | `onboarding.py:95-107` |
| output_contracts | `EmailSignupResponse {success, message, expires_in}` | `onboarding.py:110-115` |
| side_effects | **OTP email sent** | Email to user |
| failure_modes | 400 Invalid email, verification error | `onboarding.py:547-548` |
| confidence_level | **HIGH** | Full code evidence |
| evidence_refs | `onboarding.py:531-548` |
| l2_1_aligned | **NOT IN SEED** | Account not in L2.1 |
| risk_flags | Rate limiting on OTP sends |

---

### Capability: CAP-AUTH-VERIFY-EMAIL (Verify Email OTP)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-AUTH-VERIFY-EMAIL` | `onboarding.py:551` |
| capability_name | Verify Email OTP | `POST /api/v1/auth/verify/email` |
| description | Verify email OTP and complete signup | `onboarding.py:551-585` |
| mode | **WRITE** | Creates user, tokens |
| scope | **SINGLE** | Single user |
| mutates_state | **YES** | Creates user, tenant, tokens |
| bulk_support | **NO** | Single entity |
| latency_profile | **MEDIUM** | DB writes + token generation |
| execution_style | **ASYNC** | `onboarding.py:552` |
| reversibility | **NO** | User created |
| authority_required | **NONE** | Public (OTP is auth) |
| adapters | None | Direct service |
| operators | `EmailVerificationService.verify_otp()`, `UserWriteService`, `TenantService` | Multiple |
| input_contracts | `EmailVerifyRequest {email, otp}` | `onboarding.py:118-130` |
| output_contracts | `AuthResponse {access_token, refresh_token, expires_in, user}` | `onboarding.py:133-140` |
| side_effects | **User + Tenant created** | New account |
| failure_modes | 400 Invalid OTP, attempts remaining | `onboarding.py:563-567` |
| confidence_level | **HIGH** | Full code evidence |
| evidence_refs | `onboarding.py:551-585` |
| l2_1_aligned | **NOT IN SEED** | Account not in L2.1 |
| risk_flags | Creates default tenant for new users |

---

### Capability: CAP-AUTH-REFRESH (Refresh Token)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-AUTH-REFRESH` | `onboarding.py:591` |
| capability_name | Refresh Token | `POST /api/v1/auth/refresh` |
| description | Refresh access token using refresh token | `onboarding.py:591-621` |
| mode | **WRITE** | Creates new tokens |
| scope | **SINGLE** | Single session |
| mutates_state | **YES** | Revokes old, creates new tokens |
| bulk_support | **NO** | Single entity |
| latency_profile | **LOW** | Token operations |
| execution_style | **ASYNC** | `onboarding.py:592` |
| reversibility | **NO** | Old token revoked |
| authority_required | **REFRESH_TOKEN** | Valid refresh token required |
| adapters | None | Direct token service |
| operators | `verify_token()`, `revoke_refresh_token()`, `create_tokens()` | Internal |
| input_contracts | `RefreshRequest {refresh_token}` | `onboarding.py:143-145` |
| output_contracts | `AuthResponse {access_token, refresh_token, expires_in, user}` | `onboarding.py:133-140` |
| side_effects | **Old token revoked** | Cannot reuse |
| failure_modes | 401 Invalid/expired/revoked token | `onboarding.py:196-210` |
| confidence_level | **HIGH** | Full code evidence |
| evidence_refs | `onboarding.py:591-621` |
| l2_1_aligned | **NOT IN SEED** | Account not in L2.1 |
| risk_flags | Refresh token rotation (old revoked) |

---

### Capability: CAP-AUTH-LOGOUT (Logout)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-AUTH-LOGOUT` | `onboarding.py:624` |
| capability_name | Logout | `POST /api/v1/auth/logout` |
| description | Logout and invalidate refresh token | `onboarding.py:624-632` |
| mode | **WRITE** | Revokes token |
| scope | **SINGLE** | Single session |
| mutates_state | **YES** | Revokes refresh token |
| bulk_support | **NO** | Single entity |
| latency_profile | **LOW** | Redis delete |
| execution_style | **ASYNC** | `onboarding.py:625` |
| reversibility | **NO** | Token revoked |
| authority_required | **NONE** | Optional token |
| adapters | None | Direct |
| operators | `revoke_refresh_token()` | Internal |
| input_contracts | `LogoutRequest {refresh_token?}` | `onboarding.py:148-151` |
| output_contracts | `{success, message}` | `onboarding.py:632` |
| side_effects | **Token revoked** | Session ended |
| failure_modes | None (graceful) | Always succeeds |
| confidence_level | **HIGH** | Full code evidence |
| evidence_refs | `onboarding.py:624-632` |
| l2_1_aligned | **NOT IN SEED** | Account not in L2.1 |
| risk_flags | None |

---

### Capability: CAP-AUTH-ME (Get Current User)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-AUTH-ME` | `onboarding.py:635` |
| capability_name | Get Current User | `GET /api/v1/auth/me` |
| description | Get current authenticated user info | `onboarding.py:635-654` |
| mode | **READ** | User info |
| scope | **SINGLE** | Current user |
| mutates_state | **NO** | Pure read |
| bulk_support | **NO** | Single entity |
| latency_profile | **LOW** | DB query |
| execution_style | **ASYNC** | `onboarding.py:636` |
| reversibility | **N/A** | Read operation |
| authority_required | **ACCESS_TOKEN** | Bearer token |
| adapters | None | Direct |
| operators | `verify_token()`, `session.get(User)` | Internal |
| input_contracts | `Authorization: Bearer <token>` | Header |
| output_contracts | `{user: {...}}` | `onboarding.py:654` |
| side_effects | **NONE** | Pure read |
| failure_modes | 401 Missing token, 404 User not found | `onboarding.py:641-642, 652` |
| confidence_level | **HIGH** | Full code evidence |
| evidence_refs | `onboarding.py:635-654` |
| l2_1_aligned | **NOT IN SEED** | Account not in L2.1 |
| risk_flags | None |

---

### Capability: CAP-AUTH-PROVIDERS (Get Auth Providers)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-AUTH-PROVIDERS` | `onboarding.py:657` |
| capability_name | Get Auth Providers | `GET /api/v1/auth/providers` |
| description | Get available authentication providers | `onboarding.py:657-683` |
| mode | **READ** | Provider list |
| scope | **BULK** | All providers |
| mutates_state | **NO** | Pure read |
| bulk_support | **YES** | List |
| latency_profile | **LOW** | Config check |
| execution_style | **ASYNC** | `onboarding.py:658` |
| reversibility | **N/A** | Read operation |
| authority_required | **NONE** | Public endpoint |
| adapters | None | Direct |
| operators | `get_google_provider()`, `get_azure_provider()` | Internal |
| input_contracts | None | - |
| output_contracts | `{providers: [{id, name, enabled}]}` | `onboarding.py:665-682` |
| side_effects | **NONE** | Pure read |
| failure_modes | None | Always succeeds |
| confidence_level | **HIGH** | Full code evidence |
| evidence_refs | `onboarding.py:657-683` |
| l2_1_aligned | **NOT IN SEED** | Account not in L2.1 |
| risk_flags | None |

---

### Tenant Info Capabilities (tenants.py)

---

### Capability: CAP-TENANT-GET (Get Current Tenant)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-TENANT-GET` | `tenants.py:189` |
| capability_name | Get Current Tenant | `GET /api/v1/tenant` |
| description | Get tenant information from API key | `tenants.py:189-216` |
| mode | **READ** | Tenant info |
| scope | **SINGLE** | Current tenant |
| mutates_state | **NO** | Pure read |
| bulk_support | **NO** | Single entity |
| latency_profile | **LOW** | DB query |
| execution_style | **ASYNC** | `tenants.py:190` |
| reversibility | **N/A** | Read operation |
| authority_required | **API_KEY** | TenantContext |
| adapters | None | Direct service |
| operators | `TenantService.get_tenant()` | `tenants.py:197` |
| input_contracts | TenantContext from API key | Header |
| output_contracts | `TenantResponse` | `tenants.py:58-74` |
| side_effects | **NONE** | Pure read |
| failure_modes | 404 Tenant not found | `tenants.py:198-199` |
| confidence_level | **HIGH** | Full code evidence |
| evidence_refs | `tenants.py:189-216` |
| l2_1_aligned | **NOT IN SEED** | Account not in L2.1 |
| risk_flags | None |

---

### Capability: CAP-TENANT-USAGE (Get Tenant Usage)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-TENANT-USAGE` | `tenants.py:219` |
| capability_name | Get Tenant Usage | `GET /api/v1/tenant/usage` |
| description | Get usage summary for current tenant | `tenants.py:219-228` |
| mode | **READ** | Usage metrics |
| scope | **SINGLE** | Current tenant |
| mutates_state | **NO** | Pure read |
| bulk_support | **NO** | Single entity |
| latency_profile | **LOW** | Aggregation query |
| execution_style | **ASYNC** | `tenants.py:220` |
| reversibility | **N/A** | Read operation |
| authority_required | **API_KEY** | TenantContext |
| adapters | None | Direct service |
| operators | `TenantService.get_usage_summary()` | `tenants.py:227` |
| input_contracts | TenantContext from API key | Header |
| output_contracts | `UsageSummaryResponse {tenant_id, period, meters, total_records}` | `tenants.py:107-113` |
| side_effects | **NONE** | Pure read |
| failure_modes | Standard | 500 |
| confidence_level | **HIGH** | Full code evidence |
| evidence_refs | `tenants.py:219-228` |
| l2_1_aligned | **NOT IN SEED** | Account not in L2.1 |
| risk_flags | None |

---

### Capability: CAP-SETTINGS-GET (Get Read-Only Settings)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-SETTINGS-GET` | `guard.py:1163` |
| capability_name | Get Settings | `GET /guard/settings` |
| description | Get read-only settings (guardrails, budget, kill switch) | `guard.py:1163-1225` |
| mode | **READ** | Settings view |
| scope | **SINGLE** | Tenant settings |
| mutates_state | **NO** | Pure read |
| bulk_support | **NO** | Single entity |
| latency_profile | **LOW** | DB queries |
| execution_style | **ASYNC** | `guard.py:1164` |
| reversibility | **N/A** | Read operation |
| authority_required | **NONE** | tenant_id query param |
| adapters | None | Direct SQL |
| operators | Direct SQLModel queries | `guard.py:1176-1208` |
| input_contracts | `tenant_id (REQUIRED query param)` | Route |
| output_contracts | `TenantSettings` | Custom model |
| side_effects | **NONE** | Pure read |
| failure_modes | Falls back to demo defaults | `guard.py:1174` |
| confidence_level | **HIGH** | Full code evidence |
| evidence_refs | `guard.py:1163-1225` |
| l2_1_aligned | **NOT IN SEED** | Account not in L2.1 |
| risk_flags | **READ-ONLY** - customers cannot modify |

---

## OUTPUT 2 — ADAPTER & OPERATOR CROSSWALK

### Auth/Session Operations

| adapter_id | operator_name | capability_id | sync/async | side_effects | layer_route |
|------------|---------------|---------------|------------|--------------|-------------|
| (direct) | GoogleOAuthProvider.get_authorization_url() | CAP-AUTH-LOGIN-GOOGLE | async | State in Redis | L2 |
| (direct) | AzureOAuthProvider.get_authorization_url() | CAP-AUTH-LOGIN-AZURE | async | State in Redis | L2 |
| (direct) | EmailVerificationService.send_otp() | CAP-AUTH-SIGNUP-EMAIL | async | OTP sent | L2 |
| (direct) | EmailVerificationService.verify_otp() | CAP-AUTH-VERIFY-EMAIL | async | User created | L2→L4 |
| (direct) | create_tokens() | CAP-AUTH-REFRESH | async | Tokens rotated | L2 |
| (direct) | revoke_refresh_token() | CAP-AUTH-LOGOUT | async | Token revoked | L2 |
| (direct) | verify_token() | CAP-AUTH-ME | async | None | L2 |
| (direct) | Config check | CAP-AUTH-PROVIDERS | async | None | L2 |

### Tenant Info Operations

| adapter_id | operator_name | capability_id | sync/async | side_effects | layer_route |
|------------|---------------|---------------|------------|--------------|-------------|
| (direct) | TenantService.get_tenant() | CAP-TENANT-GET | async | None | L2→L4 |
| (direct) | TenantService.get_usage_summary() | CAP-TENANT-USAGE | async | None | L2→L4 |
| (direct) | Direct SQL | CAP-SETTINGS-GET | async | None | L2→L6 |

### Layer Architecture

**Auth/Session (onboarding.py):**
```
L2 (onboarding.py) — API routes
      ↓
L4 (UserWriteService, TenantService) — Domain logic
      ↓
L6 (Database + Redis)
```

**Settings (guard.py):**
```
L2 (guard.py) — API route
      ↓
L6 (Database) — DIRECT (no L3/L4)
```

**Architectural Status:** MIXED
- Auth: ACCEPTABLE (L2→L4, no L3 needed for auth)
- Settings: BYPASSES L3/L4 (direct SQL in L2)

---

## OUTPUT 3 — CAPABILITY RISK & AMBIGUITY REPORT

### Auth/Session Capabilities

**Risk Flags:**

1. **REFRESH TOKEN ROTATION**
   - Old refresh token revoked on refresh
   - Prevents token reuse but may cause issues with concurrent requests
   - **Mitigation:** Token stored in Redis with TTL

2. **NEW USER AUTO-TENANT**
   - New users automatically get personal tenant
   - Tenant created with "free" plan
   - **Note:** Expected behavior per design

3. **JWT SECRET**
   - Falls back to random secret if not configured
   - **Risk:** Token invalid after restart if not configured
   - **Mitigation:** Configure `JWT_SECRET` env var

**Confidence:** HIGH

---

### Settings Capability

**Risk Flags:**

1. **READ-ONLY**
   - Customers cannot modify settings
   - Must contact support to change
   - **By Design:** Intentional per M21/M22 governance

2. **BYPASSES L3/L4**
   - Direct SQL queries in L2
   - No adapter layer
   - **Low Risk:** Simple read-only operation

3. **DEMO MODE FALLBACK**
   - Returns demo defaults for non-existent tenants
   - **Risk:** May hide real issues

**Confidence:** HIGH

---

### NOT IMPLEMENTED

| Feature | Status | Notes |
|---------|--------|-------|
| **Billing / Plans** | NOT IMPLEMENTED | No billing API exists |
| **Account Deletion** | NOT IMPLEMENTED | No delete endpoint |
| **Account Suspension** | NOT IMPLEMENTED | No suspend endpoint |
| **Sub-tenant RBAC Admin** | FOUNDER ONLY | rbac_api.py requires rbac:read |
| **Profile Updates** | NOT IMPLEMENTED | No profile edit endpoint |
| **Password Management** | NOT APPLICABLE | OAuth/OTP only (no passwords) |

---

## STOP CONDITIONS ENCOUNTERED

1. **Billing NOT IMPLEMENTED** — No billing/subscription API exists
2. **Account Admin NOT IMPLEMENTED** — rbac_api.py is Founder Console only
3. **Account Deletion NOT IMPLEMENTED** — No delete endpoint

---

## L2.1 SURFACE MAPPING

**CRITICAL FINDING: ACCOUNT is NOT in L2.1 seed.**

Per Customer Console v1 Constitution:
> "Account is NOT a domain."

Account manages *who* and *billing*, not *what happened*. It is explicitly excluded from the L2.1 epistemic surface model.

**Recommendation:** Account should remain outside L2.1 governance. It's a secondary navigation section, not an epistemic domain.

---

## PHASE 1 COMPLETION STATUS

| Criterion | Status |
|-----------|--------|
| All capabilities documented | ✅ 12 capabilities |
| All adapters/operators cross-referenced | ✅ |
| All UNKNOWNs explicit | ✅ |
| All risks surfaced | ✅ JWT secret, demo fallback |
| No UI or binding assumptions | ✅ Code-only evidence |

**Phase 1 Status:** COMPLETE (for Account section)

**Overall Assessment:**
- Auth/Session: IMPLEMENTED (8 capabilities)
- Tenant Info: IMPLEMENTED (2 capabilities)
- Settings: IMPLEMENTED (1 capability, read-only)
- Billing: NOT IMPLEMENTED
- Account Admin: FOUNDER ONLY
- NOT in L2.1 seed (account is not a domain)

---

## References

- `backend/app/api/onboarding.py` — Auth/Session API
- `backend/app/api/tenants.py` — Tenant management API
- `backend/app/api/guard.py` — Settings endpoint
- `backend/app/api/rbac_api.py` — RBAC (Founder only)
- `backend/app/auth/oauth_providers.py` — OAuth providers
- `backend/app/services/email_verification.py` — Email OTP
- Customer Console v1 Constitution

