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

## 4.5. Database Roles (Migration Governance)

Databases have **roles** independent of location. Migrations are governed by `DB_ROLE`, not `DB_AUTHORITY`.

### DB_ROLE Values

| DB_ROLE | Meaning | Migrations Allowed |
|---------|---------|-------------------|
| **staging** | Pre-prod / local / CI authority | ✅ YES |
| **prod** | Production canonical authority | ✅ YES (with confirmation) |
| **replica** | Read-only / analytics | ❌ NO |

### Environment Mapping

| Environment | DB_AUTHORITY | DB_ROLE |
|-------------|--------------|---------|
| Local       | local        | staging |
| Neon Test   | neon         | staging |
| Neon Prod   | neon         | prod    |

### Migration Commands

**Local staging (rehearsal):**
```bash
export DB_AUTHORITY=local
export DB_ROLE=staging
export DATABASE_URL=postgresql://...
alembic upgrade head
```

**Production (with confirmation):**
```bash
export DB_AUTHORITY=neon
export DB_ROLE=prod
export CONFIRM_PROD_MIGRATIONS=true
export DATABASE_URL=postgresql://...neon.tech/...
alembic upgrade head
```

### Safety Rules

1. **replica is always blocked** — Read-only databases never accept migrations
2. **prod requires confirmation** — Set `CONFIRM_PROD_MIGRATIONS=true`
3. **DB_ROLE is authoritative** — `DB_AUTHORITY` is informational only

### Why This Model

The previous model assumed "only Neon is authoritative", which blocked local staging migrations. The correct model is:

- **staging**: local/CI rehearsal, used to validate migrations before production
- **prod**: production canonical, requires explicit confirmation for safety
- **replica**: read-only, never accepts migrations

This matches enterprise staging → prod pipelines.

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

## 12. Complete Environment Variable Registry

### 12.1 Core Platform

| Variable | Owner |
|----------|-------|
| `ENV` | Platform |
| `PORT` | Platform |
| `HOST` | Platform |
| `DATABASE_URL` | Platform / Vault |
| `DATABASE_URL_ASYNC` | Platform |
| `REDIS_URL` | Platform / Vault |
| `DB_AUTHORITY` | Platform |
| `DB_POOL_SIZE` | Platform |
| `DB_MAX_OVERFLOW` | Platform |
| `AOS_MODE` | Platform |
| `AOS_ENVIRONMENT` | Platform |
| `GIT_COMMIT_SHA` | Platform |
| `HOSTNAME` | Platform |

### 12.2 Authentication

| Variable | Owner |
|----------|-------|
| `AOS_API_KEY` | Auth (Vault: agenticverz/app-prod) |
| `AOS_FOPS_SECRET` | Auth |
| `AOS_MACHINE_TOKEN` | Auth |
| `AOS_OPERATOR_TOKEN` | Auth |
| `AOS_USE_LEGACY_AUTH` | Auth |
| `AOS_VERIFICATION_MODE` | Auth |
| `MACHINE_SECRET_TOKEN` | Auth (Vault: agenticverz/app-prod) |
| `RBAC_ENABLED` | Auth |
| `RBAC_ENFORCE` | Auth |
| `RBAC_FAIL_OPEN` | Auth |
| `RBAC_AUDIT_ENABLED` | Auth |
| `RBAC_SHADOW_AUDIT` | Auth |
| `RBAC_POLICY_FILE` | Auth |
| `AUTHZ_PHASE` | Auth |
| `AUTHZ_STRICT_MODE` | Auth |
| `AUTH_GATEWAY_ENABLED` | Auth |
| `AUTH_GATEWAY_REQUIRED` | Auth |
| `AUTH_SERVICE_URL` | Auth |
| `AUTH_SERVICE_TIMEOUT` | Auth |
| `DEV_AUTH_ENABLED` | Auth |
| `DEV_DEFAULT_ROLE` | Auth |
| `NEW_AUTH_SHADOW_ENABLED` | Auth |

### 12.3 OIDC / Clerk / JWT

| Variable | Owner |
|----------|-------|
| `OIDC_ISSUER_URL` | Auth |
| `OIDC_CLIENT_ID` | Auth |
| `OIDC_CLIENT_SECRET` | Auth (Vault: agenticverz/app-prod) |
| `OIDC_VERIFY_SSL` | Auth |
| `OIDC_AUDIENCE` | Auth |
| `OIDC_ALLOWED_AUDIENCES` | Auth |
| `OIDC_JWKS_URI` | Auth |
| `OIDC_JWKS_URL` | Auth |
| `CLERK_ISSUER_URL` | Auth |
| `CLERK_ISSUERS` | Auth |
| `CLERK_JWKS_URL` | Auth |
| `CLERK_SECRET_KEY` | Auth (Vault) |
| `JWT_SECRET` | Auth |
| `JWT_VERIFY_SIGNATURE` | Auth |
| `JWT_ALLOW_DEV_TOKEN` | Auth |
| `JWT_DEV_SECRET` | Auth |

### 12.4 LLM Providers

| Variable | Owner |
|----------|-------|
| `PLANNER_BACKEND` | LLM |
| `LLM_ADAPTER` | LLM |
| `ANTHROPIC_API_KEY` | LLM (Vault: agenticverz/external-apis) |
| `OPENAI_API_KEY` | LLM (Vault: agenticverz/external-apis) |
| `OPENAI_DEFAULT_MODEL` | LLM |
| `DEFAULT_LLM_MODEL` | LLM |
| `DEFAULT_LLM_FALLBACK_MODEL` | LLM |
| `LLM_ALLOWED_MODELS` | LLM |
| `LLM_MAX_TOKENS_PER_REQUEST` | LLM |
| `LLM_MAX_COMPLETION_TOKENS` | LLM |
| `LLM_MAX_COST_CENTS_PER_REQUEST` | LLM |
| `LLM_REQUESTS_PER_MINUTE` | LLM |
| `LLM_DAILY_LIMIT_CENTS` | LLM |
| `LLM_BUDGET_CENTS` | LLM |
| `LLM_CACHE_ENABLED` | LLM |
| `LLM_CACHE_TTL` | LLM |
| `LLM_CACHE_MAX_SIZE` | LLM |
| `LLM_ENFORCE_SAFETY` | LLM |
| `LLM_RISK_THRESHOLD` | LLM |
| `LLM_MAX_TEMPERATURE` | LLM |
| `PROXY_DEFAULT_MODEL` | LLM |

### 12.5 Worker / Runtime

| Variable | Owner |
|----------|-------|
| `WORKER_CONCURRENCY` | Worker |
| `WORKER_POLL_INTERVAL` | Worker |
| `WORKER_BATCH_SIZE` | Worker |
| `RUN_MAX_ATTEMPTS` | Worker |
| `EVENT_PUBLISHER` | Worker |
| `WORKFLOW_EMERGENCY_STOP` | Worker |
| `CONCURRENT_SLOT_TIMEOUT` | Worker |

### 12.6 Multi-Tenancy

| Variable | Owner |
|----------|-------|
| `TENANT_HEADER` | Platform |
| `ENFORCE_TENANCY` | Platform |
| `DEFAULT_TENANT` | Platform |
| `TENANT_MODE` | Platform |
| `TENANT_LLM_CONFIG_SOURCE` | Platform |
| `CUSTOMER_SANDBOX_ENABLED` | Platform |
| `DEFAULT_TENANT_BUDGET_CENTS` | Platform |
| `DEFAULT_TENANT_RATE_LIMIT` | Platform |

### 12.7 Console Modes

| Variable | Owner |
|----------|-------|
| `CONSOLE_MODE` | Console |
| `DATA_MODE` | Console |
| `ACTION_MODE` | Console |
| `HOC_DENY_AS_404` | Console |
| `HOC_DOCS_ENABLED` | Console |
| `GOVERNANCE_PROFILE` | Console |

### 12.8 Storage (R2/S3)

| Variable | Owner |
|----------|-------|
| `R2_ACCESS_KEY_ID` | Storage (Vault: secret/data/user/r2) |
| `R2_SECRET_ACCESS_KEY` | Storage (Vault: secret/data/user/r2) |
| `R2_ENDPOINT` | Storage (Vault: secret/data/user/r2) |
| `R2_BUCKET` | Storage (Vault: secret/data/user/r2) |
| `R2_ACCOUNT_ID` | Storage |
| `R2_UPLOAD_PREFIX` | Storage |
| `R2_RETENTION_DAYS` | Storage |
| `R2_MAX_RETRIES` | Storage |
| `AGG_LOCAL_FALLBACK` | Storage |
| `ARTIFACT_BACKEND` | Storage |
| `ARTIFACT_LOCAL_PATH` | Storage |
| `ARTIFACT_S3_BUCKET` | Storage |
| `ARTIFACT_S3_ENDPOINT` | Storage |
| `ARTIFACT_S3_PREFIX` | Storage |

### 12.9 Store Configuration

| Variable | Owner |
|----------|-------|
| `BUDGET_STORE` | Platform |
| `CHECKPOINT_STORE` | Platform |
| `CHECKPOINT_RETENTION_DAYS` | Platform |
| `CHECKPOINT_OFFLOAD_OLDER_THAN_DAYS` | Platform |
| `CHECKPOINT_OFFLOAD_BATCH_SIZE` | Platform |
| `CHECKPOINT_OFFLOAD_MAX_RETRIES` | Platform |

### 12.10 Monitoring / Alerting

| Variable | Owner |
|----------|-------|
| `OBSERVABILITY_MODE` | SRE |
| `ALERTMANAGER_URL` | SRE |
| `ALERTMANAGER_TIMEOUT` | SRE |
| `ALERTMANAGER_RETRY_ATTEMPTS` | SRE |
| `ALERTMANAGER_RETRY_DELAY` | SRE |
| `ALERT_FATIGUE_ENABLED` | SRE |
| `ALERT_DEDUP_WINDOW_SECONDS` | SRE |
| `MAX_ALERTS_PER_TENANT_PER_HOUR` | SRE |
| `HEALTH_CHECK_TIMEOUT_SECONDS` | SRE |

### 12.11 Cost / Budget

| Variable | Owner |
|----------|-------|
| `AOS_COST_ENFORCEMENT` | Cost |
| `PER_RUN_MAX_CENTS` | Cost |
| `PER_DAY_MAX_CENTS` | Cost |
| `DEFAULT_EST_COST_CENTS` | Cost |
| `DEFAULT_STEP_CEILING_CENTS` | Cost |
| `DEFAULT_WORKFLOW_CEILING_CENTS` | Cost |
| `BUDGET_ALERT_THRESHOLD` | Cost |
| `AUTO_PAUSE_ON_BREACH` | Cost |
| `GPT4_MAX_CENTS_PER_RUN` | Cost |
| `OPUS_MAX_CENTS_PER_RUN` | Cost |
| `COST_SPIKE_THRESHOLD_PERCENT` | Cost |
| `COST_SPIKE_MIN_RUNS` | Cost |

### 12.12 CostSim

| Variable | Owner |
|----------|-------|
| `COSTSIM_ADAPTER_VERSION` | Analytics |
| `COSTSIM_ARTIFACTS_DIR` | Analytics |
| `COSTSIM_AUTO_RECOVER` | Analytics |
| `COSTSIM_CANARY_ENABLED` | Analytics |
| `COSTSIM_DISABLE_FILE` | Analytics |
| `COSTSIM_DISABLE_TTL_HOURS` | Analytics |
| `COSTSIM_DRIFT_THRESHOLD` | Analytics |
| `COSTSIM_DRIFT_WARNING_THRESHOLD` | Analytics |
| `COSTSIM_FAILURE_THRESHOLD` | Analytics |
| `COSTSIM_MODEL_VERSION` | Analytics |
| `COSTSIM_PROVENANCE_ENABLED` | Analytics |
| `COSTSIM_SCHEMA_ERROR_THRESHOLD` | Analytics |
| `COSTSIM_USE_DB_CB` | Analytics |
| `COSTSIM_V2_AUTO_DISABLE` | Analytics |
| `COSTSIM_V2_SANDBOX` | Analytics |

### 12.13 Webhook

| Variable | Owner |
|----------|-------|
| `WEBHOOK_KEY_VERSION` | Platform |
| `WEBHOOK_KEY_GRACE_VERSIONS` | Platform |
| `WEBHOOK_SECRET_V1` | Platform (Vault) |
| `WEBHOOK_SECRET_V2` | Platform (Vault) |
| `WEBHOOK_SIGNING_SECRET` | Platform (Vault) |

### 12.14 Rate Limiting

| Variable | Owner |
|----------|-------|
| `RATE_LIMIT_ENABLED` | Platform |
| `RATE_LIMIT_DEFAULT_RPM` | Platform |
| `RATE_LIMIT_BURST_RPM` | Platform |
| `HOC_PROBE_RATE_LIMIT_ENABLED` | Platform |
| `HOC_PROBE_RATE_PER_MIN` | Platform |
| `SANDBOX_RATE_LIMIT_PER_MINUTE` | Platform |

### 12.15 Vault Configuration

| Variable | Owner |
|----------|-------|
| `VAULT_ADDR` | Platform |
| `VAULT_TOKEN` | Platform |
| `CREDENTIAL_VAULT_PROVIDER` | Platform |

---

## 13. Vault Secret Paths

| Vault Path | Keys | Owner |
|------------|------|-------|
| `agenticverz/app-prod` | AOS_API_KEY, MACHINE_SECRET_TOKEN, OIDC_CLIENT_SECRET | Platform |
| `agenticverz/database` | POSTGRES_USER, POSTGRES_PASSWORD, DATABASE_URL, KEYCLOAK_DB_USER, KEYCLOAK_DB_PASSWORD | Platform |
| `agenticverz/external-apis` | ANTHROPIC_API_KEY, OPENAI_API_KEY, GITHUB_TOKEN | LLM / CI |
| `agenticverz/keycloak-admin` | KEYCLOAK_ADMIN, KEYCLOAK_ADMIN_PASSWORD | Auth |
| `secret/data/user/anthropic` | ANTHROPIC_API_KEY | LLM |
| `secret/data/user/openai` | OPENAI_API_KEY | LLM |
| `secret/data/user/neon` | DATABASE_URL | Platform |
| `secret/data/user/upstash` | REDIS_URL | Platform |
| `secret/data/user/r2` | R2_ENDPOINT, R2_BUCKET, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY | Storage |

---

## 14. Canonical Source Files

| File | Purpose |
|------|---------|
| `.env.example` | Development template (all vars) |
| `scripts/deploy/backend/.env.production.example` | Production template |
| `scripts/ops/vault/vault_env.sh` | Load secrets from Vault |
| `backend/app/secrets/vault_client.py` | Application Vault integration |

---

## 15. Database Bootstrap Required Variables

These environment variables are **required** for fresh DB setup and alembic operations:

| Variable | Required For | Notes |
|----------|-------------|-------|
| `DATABASE_URL` | All DB operations | Must point to valid PostgreSQL instance |
| `DB_ROLE` | Alembic migrations | `staging`, `prod`, or `replica` |
| `DB_AUTHORITY` | Authority governance | `neon` or `local` |
| `CONFIRM_PROD_MIGRATIONS` | Production alembic only | Must be `true` for `DB_ROLE=prod` |

### Fresh Staging DB Setup

A fresh local DB requires ORM bootstrap before alembic:

```bash
# Required env vars
DATABASE_URL=postgresql://nova:novapass@localhost:6432/nova_aos
DB_ROLE=staging
```

`alembic upgrade head` on an empty DB will **fail** — core tables (`runs`, `tenants`, etc.)
are created by `SQLModel.metadata.create_all()`, not by migrations. See `docs/runtime/DB_AUTHORITY.md`
for the correct bootstrap procedure (PIN-542).

---

## Final Rules (Memorize)

1. **If an endpoint requires Clerk JWT, test it like a human.**
2. **If a test requires weaker auth, the test is wrong—not the system.**
3. **Planes don't mix. Ever.**
