# hoc_cus_account_L5_engines_email_verification

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/account/L5_engines/email_verification.py` |
| Layer | L5 — Domain Engine |
| Domain | account |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Email OTP verification engine for customer onboarding

## Intent

**Role:** Email OTP verification engine for customer onboarding
**Reference:** PIN-470, PIN-240, PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md
**Callers:** onboarding.py (auth flow)

## Purpose

Email Verification Service

---

## Functions

### `get_email_verification_service() -> EmailVerificationService`
- **Async:** No
- **Docstring:** Get email verification service singleton.
- **Calls:** EmailVerificationService

## Classes

### `VerificationResult`
- **Docstring:** Result of OTP verification.
- **Class Variables:** success: bool, message: str, email: Optional[str], attempts_remaining: Optional[int]

### `EmailVerificationError(Exception)`
- **Docstring:** Email verification error.
- **Methods:** __init__

### `EmailVerificationService`
- **Docstring:** Handles OTP generation, sending, and verification for email signup.
- **Methods:** __init__, _otp_key, _attempts_key, _cooldown_key, _generate_otp, send_otp, _send_otp_email, verify_otp

## Attributes

- `logger` (line 45)
- `RESEND_API_KEY` (line 48)
- `EMAIL_FROM` (line 49)
- `EMAIL_VERIFICATION_TTL` (line 50)
- `REDIS_URL` (line 51)
- `OTP_LENGTH` (line 54)
- `MAX_OTP_ATTEMPTS` (line 55)
- `OTP_COOLDOWN_SECONDS` (line 56)
- `_service: Optional[EmailVerificationService]` (line 294)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `httpx`, `redis` |

## Callers

onboarding.py (auth flow)

## Export Contract

```yaml
exports:
  functions:
    - name: get_email_verification_service
      signature: "get_email_verification_service() -> EmailVerificationService"
  classes:
    - name: VerificationResult
      methods: []
    - name: EmailVerificationError
      methods: []
    - name: EmailVerificationService
      methods: [send_otp, verify_otp]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
