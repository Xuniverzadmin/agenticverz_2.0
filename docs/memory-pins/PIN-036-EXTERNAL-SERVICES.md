# PIN-036: External Services Configuration

> **Created:** 2025-12-07
> **Status:** ACTIVE
> **Priority:** HIGH (M8 Dependencies)
> **Last Updated:** 2025-12-07

---

## Overview

This PIN documents all external service accounts created for AgenticVerz 2.0 infrastructure modernization. These services replace self-hosted components and provide managed, scalable alternatives.

---

## Service Summary

| Service | Purpose | Milestone | Status |
|---------|---------|-----------|--------|
| **Neon** | Managed PostgreSQL (replaces local PG + PgBouncer) | M8 | Credentials stored |
| **Clerk** | Auth provider (replaces Keycloak stub) | M8 | Credentials stored |
| **Resend** | Email delivery (`email_send` skill) | M11 | Credentials stored |
| **PostHog** | SDK analytics & beta user tracking | M12 | Credentials stored |
| **Trigger.dev** | Background jobs (failure aggregation) | M9 | Credentials stored |
| **Cloudflare** | Workers for edge compute & recovery engine | M9/M10 | Credentials stored |

---

## Credential Storage

All credentials stored in `/root/agenticverz2.0/secrets/`:

```
secrets/
├── neon.env              # PostgreSQL connection strings
├── clerk.env             # Auth API keys
├── clerk_public_key.pem  # JWT verification key
├── resend.env            # Email API key
├── posthog.env           # Analytics API keys
├── trigger.env           # Background jobs API key
├── cloudflare.env        # Workers API tokens
├── load_all.sh           # Helper to load all credentials
└── README.md             # Usage documentation
```

**Security:**
- All files: `chmod 600`
- Directory: `chmod 700`
- Never commit to git (in `.gitignore`)

---

## Service Details

### 1. Neon PostgreSQL

| Field | Value |
|-------|-------|
| **Account** | admin1@agenticverz.com |
| **Region** | ap-southeast-1 (Singapore) |
| **Endpoint** | ep-long-surf-a1n0hv91 |
| **Database** | neondb |

**Connection Strings:**
```bash
# Pooled (for application - use this)
postgresql://neondb_owner:***@ep-long-surf-a1n0hv91-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require

# Direct (for migrations)
postgresql://neondb_owner:***@ep-long-surf-a1n0hv91.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```

**Replaces:** Local Postgres (5433) + PgBouncer (6432)

**Migration Task:** Export local DB, import to Neon, update `DATABASE_URL`

---

### 2. Clerk Auth

| Field | Value |
|-------|-------|
| **Account** | admin1@agenticverz.com |
| **Instance** | suitable-quail-68 |
| **Mode** | Test (switch to Live for production) |

**URLs:**
- Frontend: `https://suitable-quail-68.clerk.accounts.dev`
- JWKS: `https://suitable-quail-68.clerk.accounts.dev/.well-known/jwks.json`
- Backend API: `https://api.clerk.com`

**Replaces:** Keycloak at `auth-dev.xuniverz.com` + RBAC stub

**Integration Task:**
1. Replace `AUTH_SERVICE_URL` with Clerk
2. Update `backend/app/auth/rbac.py` to use Clerk SDK
3. Remove Keycloak OIDC config

---

### 3. Resend Email

| Field | Value |
|-------|-------|
| **Account** | GitHub Xuniverz |
| **Domain** | agenticverz.com |
| **From Address** | notifications@agenticverz.com |

**Use Case:** M11 `email_send` skill for workflow notifications

---

### 4. PostHog Analytics

| Field | Value |
|-------|-------|
| **Account** | GitHub Xuniverz |
| **Project ID** | 261716 |
| **Region** | US Cloud |
| **Host** | https://us.posthog.com |

**Use Case:**
- SDK usage tracking
- Beta user analytics (M12)
- Feature adoption metrics

---

### 5. Trigger.dev

| Field | Value |
|-------|-------|
| **Project Ref** | proj_urctldvxiglmgcwtftwq |
| **API URL** | https://api.trigger.dev |

**Use Case:**
- M9: Nightly failure aggregation job
- M10: Recovery candidate generation

**Init Command:**
```bash
npx trigger.dev@latest init -p proj_urctldvxiglmgcwtftwq
npx trigger.dev@latest dev
```

---

### 6. Cloudflare

| Field | Value |
|-------|-------|
| **Account** | Maheshwar.rj@gmail.com |
| **Account ID** | 393c589a4c64c2df5b19b864ddfaba6c |
| **Zone ID** | 28854d5b1f01631571a6971e0e580145 |
| **Domain** | agenticverz.com |

**Enabled Features:**
- Workers Scripts
- Workers KV Storage
- Workers R2 Storage
- Cloudflare Pages
- Workers Routes (agenticverz.com)

**Use Case:**
- M9/M10: Edge workers for failure processing
- M10: Recovery suggestion engine at edge
- Future: CDN for SDK/docs

---

## Integration Priority

### Phase 1: M8 (Immediate)

```
1. Neon PostgreSQL
   - Export local DB: pg_dump
   - Import to Neon: pg_restore
   - Update DATABASE_URL in .env
   - Remove PgBouncer from docker-compose.yml

2. Clerk Auth
   - Create Clerk integration in backend/app/auth/
   - Remove Keycloak OIDC config
   - Update RBAC to use Clerk roles
   - Remove AUTH_SERVICE_URL stub
```

### Phase 2: M9 (Failure Persistence)

```
3. Trigger.dev
   - Init project in backend/
   - Create nightly aggregation job
   - Wire to failure_matches table

4. Cloudflare Workers (optional)
   - Create failure processing worker
   - Set up KV for pattern caching
```

### Phase 3: M11-M12 (Skills & Beta)

```
5. Resend
   - Create email_send skill
   - Verify domain DNS records

6. PostHog
   - Add SDK telemetry
   - Create beta user dashboard
```

---

## Environment Variable Updates

When integrating, update `.env`:

```bash
# === M8: Database (Neon) ===
DATABASE_URL=postgresql://neondb_owner:npg_cVfk6XMYdt4G@ep-long-surf-a1n0hv91-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
DATABASE_URL_DIRECT=postgresql://neondb_owner:npg_cVfk6XMYdt4G@ep-long-surf-a1n0hv91.ap-southeast-1.aws.neon.tech/neondb?sslmode=require

# === M8: Auth (Clerk) ===
CLERK_SECRET_KEY=sk_test_***
CLERK_PUBLISHABLE_KEY=pk_test_***
OIDC_ISSUER_URL=https://suitable-quail-68.clerk.accounts.dev
# Remove: AUTH_SERVICE_URL, OIDC_CLIENT_SECRET (Keycloak)

# === M9: Background Jobs ===
TRIGGER_API_KEY=tr_dev_***

# === M11: Email ===
RESEND_API_KEY=re_***

# === M12: Analytics ===
POSTHOG_API_KEY=phc_***
POSTHOG_HOST=https://us.posthog.com

# === M9/M10: Edge Workers ===
CLOUDFLARE_API_TOKEN=***
CLOUDFLARE_ACCOUNT_ID=393c589a4c64c2df5b19b864ddfaba6c
```

---

## Account Access Reference

| Service | Login Email | Password | Notes |
|---------|-------------|----------|-------|
| Neon | admin1@agenticverz.com | Vettri@2026 | - |
| Clerk | admin1@agenticverz.com | Vettri@2026 | - |
| Resend | GitHub Xuniverz | - | GitHub OAuth |
| PostHog | GitHub Xuniverz | - | GitHub OAuth |
| Trigger.dev | - | - | API key only |
| Cloudflare | Maheshwar.rj@gmail.com | - | Existing account |

---

## Deprecation Plan

After successful migration to external services:

| Remove | When | Notes |
|--------|------|-------|
| Local PgBouncer | After Neon verified | Remove from docker-compose.yml |
| Keycloak OIDC config | After Clerk verified | Remove OIDC_* vars |
| AUTH_SERVICE_URL stub | After Clerk verified | Remove from .env |
| Local Postgres (optional) | After Neon stable 1 week | Keep for dev/backup |

---

## Verification Commands

```bash
# Load all credentials
source /root/agenticverz2.0/secrets/load_all.sh

# Test Neon connection
psql "$NEON_DATABASE_URL" -c "SELECT version();"

# Test Clerk (verify token)
curl -H "Authorization: Bearer $CLERK_SECRET_KEY" \
  https://api.clerk.com/v1/users?limit=1

# Test Resend
curl -X POST https://api.resend.com/emails \
  -H "Authorization: Bearer $RESEND_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"from":"test@agenticverz.com","to":"admin1@agenticverz.com","subject":"Test","text":"Hello"}'

# Test PostHog
curl "https://us.posthog.com/api/projects/$POSTHOG_PROJECT_ID/" \
  -H "Authorization: Bearer $POSTHOG_ACCOUNT_API_KEY"

# Test Cloudflare
curl "https://api.cloudflare.com/client/v4/user/tokens/verify" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"
```

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-07 | **CI UPDATED** - Workflow uses Neon/Upstash if secrets set, Docker fallback |
| 2025-12-07 | **EMAIL_SEND SKILL CREATED** - Resend integration complete with 21 tests |
| 2025-12-07 | **NEON MIGRATION COMPLETE** - Database migrated to Neon PostgreSQL |
| 2025-12-07 | **CLERK INTEGRATION COMPLETE** - Auth provider integrated |
| 2025-12-07 | Test users created: admin (level 5), team_member (level 2) |
| 2025-12-07 | Backend and worker running on Neon + Clerk |
| 2025-12-07 | PIN created with 6 external services documented |
| 2025-12-07 | Credentials stored in /root/agenticverz2.0/secrets/ |
| 2025-12-07 | Load helper script created (load_all.sh) |

---

## Related PINs

- PIN-009: External Rollout Pending (auth blocker)
- PIN-033: M8-M14 Machine-Native Realignment
- PIN-035: SDK Package Registry
