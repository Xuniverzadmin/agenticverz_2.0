# PIN-142: Secrets & Environment Contract

**Status:** ✅ COMPLETE
**Created:** 2025-12-23
**Category:** Infrastructure / Security
**Milestone:** M26+

---

## Summary

Centralized secret management with fail-fast validation for production-grade environment hygiene.

---

## The Problem

Before this contract:
- 44 scattered `os.environ.get()` calls across 30 files
- Scripts could run with missing secrets and fail silently
- Env var propagation across process boundaries was implicit
- Real money features (M26 Cost Intelligence) had no secret validation

**Root cause of M26 env var issue:**
Script execution context ≠ app runtime context. Backend loaded `.env`, but standalone scripts did not.

---

## The Contract

### Rule 1: No Direct `os.environ.get()` for Secrets

```python
# WRONG
openai_key = os.environ.get("OPENAI_API_KEY")

# RIGHT
from app.config.secrets import Secrets
openai_key = Secrets.openai_api_key()  # Raises if missing
```

### Rule 2: Check Before Use

```python
from app.config.secrets import Secrets

# For optional features
if Secrets.has_openai():
    key = Secrets.openai_api_key()
    # use it
else:
    # handle gracefully
```

### Rule 3: Scripts Must Fail Fast

Every ops/test script that uses secrets MUST:
1. Validate secrets at script start
2. Print clear error message if missing
3. Exit with non-zero status

```python
def validate_script_secrets():
    required = {"OPENAI_API_KEY": "OpenAI API (spends money)"}
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"FATAL: Missing: {missing}")
        sys.exit(1)

if __name__ == "__main__":
    validate_script_secrets()  # FIRST LINE
    main()
```

### Rule 4: App Startup Validation

Backend validates required secrets at startup in `lifespan()`:

```python
from .config.secrets import validate_required_secrets

try:
    validate_required_secrets(include_billing=False, hard_fail=True)
except SecretValidationError:
    raise  # App won't start
```

---

## Secret Categories

| Category | Secrets | Behavior |
|----------|---------|----------|
| REQUIRED | DATABASE_URL, REDIS_URL | App crashes on startup if missing |
| BILLING | OPENAI_API_KEY | Warning on startup, required for cost features |
| EXTERNAL | ANTHROPIC_API_KEY, VAULT_TOKEN, VOYAGE_API_KEY | Warning if missing |
| OPTIONAL | SLACK_WEBHOOK_URL, POSTHOG_API_KEY | Graceful fallback |

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/app/config/secrets.py` | Centralized secret accessor |
| `backend/app/main.py` | Startup validation in lifespan() |
| `scripts/ops/m26_real_cost_test.py` | Example of fail-fast script |

---

## Diagnostic Commands

```bash
# Check secret status (never shows values)
python3 -c "from app.config.secrets import get_secret_status; import json; print(json.dumps(get_secret_status(), indent=2))"

# Validate startup requirements
python3 -c "from app.config.secrets import validate_required_secrets; validate_required_secrets()"

# Test script fail-fast
python3 scripts/ops/m26_real_cost_test.py  # Should fail if env not loaded
```

---

## Migration Path

For existing code using `os.environ.get()`:

1. If it's a secret (API key, password, token) → use `Secrets.xxx()`
2. If it's a config value (LOG_LEVEL, AOS_ENV) → can keep `os.environ.get()`
3. If it's in an ops script → add fail-fast validation at start

---

## Enforcement

| Mechanism | Location |
|-----------|----------|
| Pre-commit hook | `ruff` checks for bare os.environ in secrets |
| CI guard | Could add grep for `os.environ.get(".*KEY")` |
| Startup crash | Backend won't start without REQUIRED secrets |
| Script crash | Real-cost scripts exit immediately if missing |

---


---

## Updates

### Update (2025-12-23)

## 2025-12-23: Implementation Complete

### Files Created/Modified

| File | Purpose |
|------|---------|
| `backend/app/config/secrets.py` | Centralized secret accessor with typed methods |
| `backend/app/main.py` | Startup validation in lifespan() |
| `scripts/ops/m26_real_cost_test.py` | Fail-fast example pattern |

### Validation Results

```
✅ DATABASE_URL: configured (REQ)
✅ REDIS_URL: configured (REQ)
✅ OPENAI_API_KEY: configured (REQ)
✅ ANTHROPIC_API_KEY: configured
✅ VOYAGE_API_KEY: configured
✅ RESEND_API_KEY: configured
✅ GOOGLE_CLIENT_ID: configured
✅ AZURE_CLIENT_ID: configured
```

### Contract Enforced

- No more scattered os.environ.get() for secrets
- Scripts fail immediately with clear error if env missing
- Backend crashes at startup if REQUIRED secrets missing

## Related PINs

- PIN-141: M26 Cost Intelligence (the trigger for this contract)
- PIN-120: Test Suite Stabilization (prevention mechanisms pattern)
