# PIN-149: Category 2 Auth Boundary - Full Spec Implementation

**Status:** ✅ COMPLETE
**Category:** Security / Authentication
**Created:** 2025-12-23
**Milestone:** M29 Transition
**Related:** [PIN-148](PIN-148-m29-categorical-next-steps.md)

---

## Overview

This PIN documents the full implementation of Category 2: Auth Boundary Verification per the M29 transition spec. The implementation enforces strict domain separation between Customer Console (`/guard/*`) and Founder Ops Console (`/ops/*`).

---

## The Invariants

1. **A token belongs to exactly one domain** (`aud=console` OR `aud=fops`, never both)
2. **A session belongs to exactly one console** (separate cookies)
3. **A role escalation is impossible by accident** (separate middleware, no shared logic)
4. **Failure must be loud and logged** (structured audit events)

---

## Token Model

### Customer Token (Console)

```python
class CustomerToken:
    aud: Literal["console"]     # STRICT - no other value allowed
    sub: str                    # user_id
    org_id: str                 # tenant_id (REQUIRED)
    role: CustomerRole          # OWNER, ADMIN, DEV, VIEWER
    iss: str                    # "agenticverz"
    exp: int                    # Unix timestamp
    iat: int                    # Issued at
```

### Founder Token (FOPS)

```python
class FounderToken:
    aud: Literal["fops"]        # STRICT - no other value allowed
    sub: str                    # founder_id
    role: FounderRole           # FOUNDER, OPERATOR
    mfa: bool                   # MUST be True
    iss: str                    # "agenticverz"
    exp: int                    # Unix timestamp
    iat: int                    # Issued at
```

---

## Cookie Separation

| Cookie | Domain | Audience | Settings |
|--------|--------|----------|----------|
| `aos_console_session` | console.agenticverz.com | console | httpOnly, secure, sameSite=strict |
| `aos_fops_session` | fops.agenticverz.com | fops | httpOnly, secure, sameSite=strict |

---

## Middleware Separation

### Console Middleware

```python
async def verify_console_token(request: Request) -> CustomerToken:
    """
    Customer Console middleware - strict aud=console check.

    Validates:
    - Token exists (cookie or X-API-Key header)
    - aud == "console"
    - org_id is present
    - role in [OWNER, ADMIN, DEV, VIEWER]

    Rejects with audit log:
    - FOPS tokens (AUD_MISMATCH)
    - Missing org_id (ORG_ID_MISSING)
    - Invalid role (ROLE_INVALID)
    """
```

### FOPS Middleware

```python
async def verify_fops_token(request: Request) -> FounderToken:
    """
    Founder Ops middleware - strict aud=fops, mfa=true check.

    Validates:
    - Token exists (cookie or X-API-Key header)
    - aud == "fops"
    - role in [FOUNDER, OPERATOR]
    - mfa == True

    Rejects with audit log:
    - Console tokens (AUD_MISMATCH)
    - mfa=false (MFA_REQUIRED)
    - Invalid role (ROLE_INVALID)
    """
```

---

## Audit Logging

All auth rejections are logged with structured data:

```python
class AuthAuditEvent:
    event: str = "AUTH_DOMAIN_REJECT"
    actor_id: str                  # Who attempted
    attempted_domain: str          # "console" or "fops"
    token_aud: str                 # What was in the token
    reason: AuthRejectReason       # Why rejected
    ip: str                        # Client IP
    ts: str                        # ISO8601 timestamp
```

### Rejection Reasons

| Reason | Description |
|--------|-------------|
| `MISSING_TOKEN` | No token provided |
| `INVALID_TOKEN` | Token failed validation |
| `EXPIRED_TOKEN` | Token past expiration |
| `AUD_MISMATCH` | Token audience wrong for domain |
| `ROLE_INVALID` | Role not allowed for domain |
| `MFA_REQUIRED` | FOPS requires mfa=true |
| `ORG_ID_MISSING` | Console requires org_id |

---

## Manual Abuse Test Results

All 6 tests passed:

| Test | Expected | Result |
|------|----------|--------|
| Console key on /ops/* | 403 AUD_MISMATCH + audit | ✅ PASS |
| FOPS key on /guard/* | 403 AUD_MISMATCH + audit | ✅ PASS |
| No key on /ops/* | 403 MISSING_TOKEN + audit | ✅ PASS |
| Invalid key on any | 403 INVALID_TOKEN + audit | ✅ PASS |
| FOPS key on /ops/* | 200 OK | ✅ PASS |
| Console key on /guard/* | 200 OK | ✅ PASS |

---

## CI Guardrails

12 tests in `test_category2_auth_boundary.py`:

```
TestAuthBoundaryInvariants:
  - test_console_key_rejected_on_fops_endpoint ✅
  - test_fops_key_rejected_on_console_endpoint ✅
  - test_no_key_rejected_on_fops ✅
  - test_no_key_rejected_on_console ✅
  - test_invalid_key_rejected ✅

TestTokenAudienceSeparation:
  - test_token_audiences_are_separate ✅
  - test_customer_token_claims ✅
  - test_founder_token_requires_mfa ✅

TestAuditLogging:
  - test_auth_audit_event_schema ✅
  - test_reject_reasons_are_explicit ✅

TestCookieSeparation:
  - test_cookie_names_are_separate ✅
  - test_cookie_settings_per_domain ✅
```

---

## Files Created/Modified

### New Files

| File | Purpose |
|------|---------|
| `backend/app/auth/console_auth.py` | Complete auth module with token models, middleware, audit logging |
| `backend/tests/test_category2_auth_boundary.py` | CI guardrails (12 tests) |

### Modified Files

| File | Change |
|------|--------|
| `backend/app/api/guard.py` | Uses `verify_console_token` dependency |
| `backend/app/api/ops.py` | Uses `verify_fops_token` dependency |
| `docker-compose.yml` | Added AOS_FOPS_KEY, AOS_JWT_SECRET env vars |
| `.env` | Added AOS_FOPS_KEY, AOS_JWT_SECRET |

---

## Environment Variables

```bash
# Category 2 Auth: Separate Console/FOPS Authentication
AOS_API_KEY=<console-key>              # Console-only key
AOS_FOPS_KEY=<fops-key>                # FOPS-only key
AOS_JWT_SECRET=<jwt-signing-secret>    # Base JWT secret
CONSOLE_JWT_SECRET=${AOS_JWT_SECRET}   # Console JWT (can differ)
FOPS_JWT_SECRET=${AOS_JWT_SECRET}      # FOPS JWT (can differ)
```

---

## Exit Criteria (ALL MET)

| Criterion | Status |
|-----------|--------|
| Separate tokens with strict `aud` | ✅ |
| Separate cookies per domain | ✅ |
| Separate middleware, no shared logic | ✅ |
| MFA enforced for `/fops` | ✅ |
| Cross-access always returns 403 | ✅ |
| All rejections are audited | ✅ |
| Manual abuse tests passed | ✅ (6/6) |
| CI tests enforce separation | ✅ (12/12) |

---

## Security Guarantees

1. **No Token Reuse**: A console token cannot be used on FOPS, and vice versa
2. **No Cookie Leakage**: Cookies are domain-scoped and cannot be shared
3. **No Privilege Escalation**: Middleware is completely separate, no shared code paths
4. **Full Audit Trail**: Every rejection is logged with actor, reason, IP, timestamp
5. **MFA Enforcement**: FOPS access requires multi-factor authentication

---

## Related Documents

- [PIN-148](PIN-148-m29-categorical-next-steps.md) - M29 Categorical Next Steps
- [backend/app/auth/console_auth.py](../../backend/app/auth/console_auth.py) - Implementation
- [backend/tests/test_category2_auth_boundary.py](../../backend/tests/test_category2_auth_boundary.py) - Tests
