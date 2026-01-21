# Environment Contract — Agenticverz (MANDATORY)

**Status:** ACTIVE
**Effective:** 2026-01-18
**Scope:** All automation, AI agents, and engineers

This file is **not documentation**. It is a **system rulebook**.
Any automation, AI agent, or engineer must follow this contract.

---

## 1. Environment Modes (Canonical)

The system has exactly four modes:

| Mode    | AOS_MODE | DB_AUTHORITY | Purpose |
|---------|----------|--------------|---------|
| LOCAL   | local    | local        | Developer sandbox |
| TEST    | test     | neon         | Customer-grade testing |
| PREPROD | preprod  | neon         | Pre-production staging (current) |
| PROD    | prod     | neon         | Production |

**No other combinations are valid.**

**Current Environment:** This codebase runs as `AOS_MODE=preprod`. Production will be a separate deployment with `AOS_MODE=prod`.

---

## 2. Auth Rules Per Mode

### LOCAL
- Sandbox auth allowed (`CUSTOMER_SANDBOX_ENABLED=true`)
- Header: `X-AOS-Customer-Key`
- No Clerk JWT required
- No production data
- Disposable database

### TEST
- Sandbox auth optional (if explicitly enabled)
- Clerk JWT allowed (test project)
- Machine API key allowed (`X-AOS-Key`)
- Neon test database only
- No billing impact
- All actions logged but non-billable

### PREPROD
- Same auth rules as PROD (Clerk JWT + machine keys)
- Debug endpoints **enabled** (PIN-444)
- Neon database (staging data)
- Used for final validation before production
- All actions logged, non-billable

### PROD
- Sandbox auth **forbidden**
- Clerk JWT **required** for human endpoints
- Machine API key **only** for machine endpoints
- Neon production database
- All actions billable and auditable
- No bypasses, no stubs, no fakes

---

## 3. Auth Planes (Non-Negotiable)

| Plane | Auth Header | Endpoints | Purpose |
|-------|-------------|-----------|---------|
| **Human** | `Authorization: Bearer <clerk_jwt>` | `/api/v1/accounts/*`, console APIs | User-initiated actions |
| **Machine** | `X-AOS-Key: <api_key>` | `/api/v1/runs/*`, `/api/v1/telemetry/*`, SDK | Automated/programmatic access |
| **Database** | `DATABASE_URL` (connection string) | Migrations, seeds | Schema operations |

**Planes never cross:**
- Human endpoints reject machine keys
- Machine endpoints reject Clerk JWTs
- Database operations never use HTTP APIs

---

## 4. What Is Allowed Per Plane

### Database Plane (Migrations, Seeds)
- Uses `DATABASE_URL` only
- Never uses HTTP APIs
- Never requires auth headers
- Controlled by `DB_AUTHORITY` environment variable

### API Plane (Control / Governance)
- Requires correct auth for the environment
- Human endpoints require Clerk JWT
- Machine endpoints require `X-AOS-Key`
- Both reject wrong auth type (fail-closed)

### SDK Plane
- Always treated as external
- Never bypasses auth
- Never imports backend code directly
- Uses `X-AOS-Key` for all operations

---

## 5. Absolute Prohibitions

The following are **forbidden in all environments**:

| Prohibition | Reason |
|-------------|--------|
| Fake JWTs | Undermines trust model |
| Stub users | Creates ghost principals |
| `PUBLIC_PATHS` for protected APIs | Opens security holes |
| API calls during migrations | Mixes planes |
| Production DB for testing | Data contamination |
| Machine keys on human endpoints | Privilege escalation |
| Clerk JWT on machine endpoints | Identity confusion |
| Dev bypass flags | Security theater |

---

## 6. AI / Automation Instruction (CRITICAL)

When an AI agent (Claude, etc.) is used:

### MUST DO
- Always ask: "What is the current AOS_MODE?"
- Read this contract before suggesting auth changes
- Respect plane separation
- Stop and ask if environment is ambiguous

### MUST NOT
- Assume environment intent
- Suggest weakening auth to make tests pass
- Create stub users or fake tokens
- Suggest adding machine auth to human endpoints
- Mix database operations with API calls

### REJECTION RULE
If a task violates this contract, the task must be **rejected**, not "fixed" by weakening auth.

---

## 7. Correct Testing Methods

### Human Plane Endpoints (e.g., `/api/v1/accounts/*`)

| Method | Environment | How |
|--------|-------------|-----|
| Frontend testing | Any | Login via Clerk in Customer Console |
| API testing | TEST | Use real Clerk test JWT |
| Integration testing | TEST | Clerk test users + real JWTs |

**Never:** Use `X-AOS-Key`, stub tokens, or auth bypass.

### Machine Plane Endpoints (e.g., `/api/v1/runs/*`)

| Method | Environment | How |
|--------|-------------|-----|
| SDK testing | LOCAL/TEST | Use `X-AOS-Key` |
| CI testing | TEST | Use machine API key |
| Load testing | TEST | Use dedicated test keys |

**Never:** Use Clerk JWT for machine endpoints.

### Database Operations (Migrations)

| Method | Environment | How |
|--------|-------------|-----|
| Apply migration | Any | `alembic upgrade head` with `DATABASE_URL` |
| Verify schema | Any | Direct SQL query |
| Seed data | Any | SQL or Alembic `op.execute()` |

**Never:** Use HTTP APIs to verify migrations or seed data.

---

## 8. Environment Detection

### Required Environment Variables

```bash
# LOCAL
AOS_MODE=local
DB_AUTHORITY=local
CUSTOMER_SANDBOX_ENABLED=true

# TEST
AOS_MODE=test
DB_AUTHORITY=neon
DATABASE_URL=<neon_test_connection_string>

# PREPROD (current environment)
AOS_MODE=preprod
DB_AUTHORITY=neon
DATABASE_URL=<neon_staging_connection_string>

# PROD
AOS_MODE=prod
DB_AUTHORITY=neon
DATABASE_URL=<neon_prod_connection_string>
CUSTOMER_SANDBOX_ENABLED=false
```

### Validation Rule

If `AOS_MODE` and `DB_AUTHORITY` don't match a valid combination, the system should **fail-stop**, not guess.

---

## 9. Quick Reference

### "I need to test human endpoints"
→ Use Clerk JWT in TEST mode or use the frontend

### "I need to test machine endpoints"
→ Use `X-AOS-Key` in TEST mode

### "I need to run a migration"
→ Use `DATABASE_URL` only, no HTTP calls

### "I need to verify migration worked"
→ Query DB directly, not via API

### "I can't authenticate"
→ Check you're using the right plane's auth method

### "Can I add a stub/bypass?"
→ **No.** Find the correct testing method instead.

---

## 10. Contract Violations

If you observe:
- Machine key accepted on human endpoint → **Security bug**
- Clerk JWT accepted on machine endpoint → **Security bug**
- API call during migration → **Architecture violation**
- Stub/fake auth in production → **Critical violation**

Report immediately. Do not proceed.

---

## 11. Production-Gated Features (PIN-444)

Some features are **disabled in production** (`AOS_MODE=prod`) for security or operational reasons.

### Debug Endpoints

| Endpoint | Purpose | Availability |
|----------|---------|--------------|
| `/__debug/openapi_nocache` | Force OpenAPI regeneration without cache | LOCAL, TEST, PREPROD only |
| `/__debug/openapi_inspect` | Inspect schema for problematic patterns | LOCAL, TEST, PREPROD only |

**Implementation:** These endpoints check `AOS_MODE` at runtime and return 404 if `AOS_MODE=prod`.

**Why gated:**
- Debug endpoints expose operational internals (schema structure, timing)
- Not needed in production (schema should be stable)
- Reduces attack surface

**Reference:** `backend/app/main.py` (PIN-444)

### Adding New Production-Gated Features

If you need to add a feature that should be disabled in production:

```python
_FEATURE_ENABLED = os.getenv("AOS_MODE", "preprod").lower() != "prod"

@app.get("/my-feature")
async def my_feature():
    if not _FEATURE_ENABLED:
        return JSONResponse(status_code=404, content={"error": "not_found"})
    # ... feature implementation
```

**Rule:** All production-gated features must be documented in this section.

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `AUTH_ARCHITECTURE_BASELINE.md` | Auth implementation details |
| `RBAC_AUTHORITY_SEPARATION_DESIGN.md` | Permission model |
| `OPENAPI_SAFE_MODELS.md` | OpenAPI schema health rules (PIN-444) |
| `customer_sandbox.py` | Sandbox auth (LOCAL only) |
| `gateway_middleware.py` | Auth enforcement |

---

## Final Rules (Memorize)

1. **If an endpoint requires Clerk JWT, test it like a human.**
2. **If a test requires weaker auth, the test is wrong—not the system.**
3. **Planes don't mix. Ever.**
