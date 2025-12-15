# PIN-066: External API Keys & Integrations Reference

**Created:** 2025-12-13
**Status:** REFERENCE
**Category:** Infrastructure / Security / Integrations
**Milestone:** M13
**Parent PINs:** PIN-034 (Vault), PIN-059 (Skills), PIN-065 (System Reference)
**Author:** Claude Code + Human Review

---

## Purpose

Document all external API keys, third-party integrations, and their functional dependencies in the AOS system. Essential for:
- Production deployment planning
- Security audits
- Cost tracking (FinOps)
- Service availability planning

---

## 1. Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AOS Backend                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Clerk      │───▶│  API Auth    │───▶│  Endpoints   │      │
│  │ (Required)   │    │              │    │              │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                │                 │
│                                                ▼                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Neon DB    │◀───│   Runtime    │───▶│   Skills     │      │
│  │ (Required)   │    │   Engine     │    │              │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                │                 │
│  ┌──────────────┐                              │                 │
│  │  Upstash     │◀────────────────────────────┘                 │
│  │ (Required)   │                                                │
│  └──────────────┘         OPTIONAL SKILLS                       │
│                     ┌─────────┬─────────┬─────────┐             │
│                     │Anthropic│ OpenAI  │ Voyage  │             │
│                     │   LLM   │   LLM   │ Embed   │             │
│                     └────┬────┴────┬────┴────┬────┘             │
│                          │         │         │                   │
│                     ┌────┴────┬────┴────┬────┴────┐             │
│                     │ Resend  │  Slack  │   R2    │             │
│                     │  Email  │ Notify  │ Archive │             │
│                     └─────────┴─────────┴─────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Required Services (System Won't Function Without)

### 2.1 Neon PostgreSQL

| Property | Value |
|----------|-------|
| **Purpose** | Primary database for all persistent state |
| **Env Vars** | `DATABASE_URL`, `DATABASE_URL_DIRECT` |
| **Region** | `ap-southeast-1` (Singapore) |
| **Endpoint** | `ep-long-surf-a1n0hv91-pooler.ap-southeast-1.aws.neon.tech` |
| **Connection** | Pooled via PgBouncer (port 5432 via pooler) |
| **Direct** | `ep-long-surf-a1n0hv91.ap-southeast-1.aws.neon.tech` (for migrations) |
| **Tables** | agents, runs, steps, traces, failures, recovery_candidates, memory_pins, etc. |
| **Cost** | Free tier / Pay-as-you-go |

**Usage Files:**
- `backend/app/database.py`
- All SQLModel models

---

### 2.2 Upstash Redis

| Property | Value |
|----------|-------|
| **Purpose** | Caching, rate limiting, job queues, pub/sub |
| **Env Vars** | `REDIS_URL`, `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN` |
| **Endpoint** | `on-sunbeam-19994.upstash.io:6379` |
| **Protocol** | `rediss://` (TLS encrypted) |
| **REST API** | `https://on-sunbeam-19994.upstash.io` |
| **Features Used** | String cache, rate limit counters, pub/sub channels |
| **Cost** | Free tier / Pay-as-you-go |

**Usage Files:**
- `backend/app/utils/rate_limit.py`
- `backend/app/worker/outbox_processor.py`
- `backend/app/memory/pin_store.py`

---

### 2.3 Clerk Authentication

| Property | Value |
|----------|-------|
| **Purpose** | User authentication, JWT validation, OIDC |
| **Env Vars** | `CLERK_SECRET_KEY`, `CLERK_PUBLISHABLE_KEY`, `CLERK_ISSUER_URL`, `CLERK_JWKS_URL` |
| **Issuer** | `https://suitable-quail-68.clerk.accounts.dev` |
| **JWKS** | `https://suitable-quail-68.clerk.accounts.dev/.well-known/jwks.json` |
| **Features** | JWT validation, user sessions, RBAC claims |
| **Console Use** | Frontend login, session management |
| **Cost** | Free tier (10,000 MAU) |

**Usage Files:**
- `backend/app/auth/clerk_provider.py`
- `backend/app/auth/rbac.py`
- `backend/app/auth/rbac_middleware.py`

---

## 3. LLM Providers (Core Skills)

### 3.1 Anthropic Claude

| Property | Value |
|----------|-------|
| **Purpose** | Primary LLM for agent planning and `llm_invoke` skill |
| **Env Var** | `ANTHROPIC_API_KEY` |
| **Model** | `claude-sonnet-4-20250514` (default) |
| **Endpoints** | `https://api.anthropic.com/v1/messages` |
| **Skills Using** | `llm_invoke`, planning adapters |
| **Fallback** | OpenAI if unavailable |
| **Cost** | Pay-per-token |

**Usage Files:**
- `backend/app/skills/llm_invoke.py`
- `backend/app/planners/anthropic_adapter.py`
- `backend/app/skills/adapters/claude_adapter.py`

---

### 3.2 OpenAI

| Property | Value |
|----------|-------|
| **Purpose** | Alternative/fallback LLM for `llm_invoke` skill |
| **Env Var** | `OPENAI_API_KEY` |
| **Model** | `gpt-4o` (default) |
| **Endpoints** | `https://api.openai.com/v1/chat/completions` |
| **Skills Using** | `llm_invoke` (when provider=openai) |
| **Cost** | Pay-per-token |

**Usage Files:**
- `backend/app/skills/llm_invoke.py`
- `backend/app/skills/adapters/openai_adapter.py`

---

## 4. Optional Services (Skill-Dependent)

### 4.1 Cloudflare R2

| Property | Value |
|----------|-------|
| **Purpose** | Checkpoint archival, failure pattern storage |
| **Env Vars** | `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_ENDPOINT`, `R2_BUCKET` |
| **Endpoint** | `https://<account_id>.r2.cloudflarestorage.com` |
| **Bucket** | `candidate-failure-patterns` |
| **Features** | S3-compatible API, checkpoint offload |
| **Required?** | No - graceful degradation if not configured |
| **Cost** | Free egress, storage-based pricing |

**Usage Files:**
- `backend/app/stores/__init__.py`
- `backend/app/stores/checkpoint_offload.py`
- `backend/app/jobs/storage.py`

---

### 4.2 Resend (Email)

| Property | Value |
|----------|-------|
| **Purpose** | `email_send` skill - transactional emails |
| **Env Vars** | `RESEND_API_KEY`, `RESEND_FROM_ADDRESS` |
| **Endpoint** | `https://api.resend.com/emails` |
| **Default From** | `notifications@agenticverz.com` |
| **Required?** | No - only if skill invoked |
| **Cost** | Free tier (100 emails/day) |

**Usage Files:**
- `backend/app/skills/email_send.py`

---

### 4.3 Slack Webhooks

| Property | Value |
|----------|-------|
| **Purpose** | `slack_send` skill + mismatch alerts |
| **Env Vars** | `SLACK_WEBHOOK_URL`, `SLACK_MISMATCH_WEBHOOK` |
| **Features** | Incoming webhooks for notifications |
| **Required?** | No - only if skill invoked or alerts enabled |
| **Cost** | Free |

**Usage Files:**
- `backend/app/skills/slack_send.py`
- `backend/app/api/traces.py` (mismatch alerts)

---

### 4.4 Voyage AI (Embeddings)

| Property | Value |
|----------|-------|
| **Purpose** | `voyage_embed` skill - vector embeddings |
| **Env Var** | `VOYAGE_API_KEY` |
| **Endpoint** | `https://api.voyageai.com/v1/embeddings` |
| **Models** | `voyage-3` (1024d), `voyage-3-lite` (512d), `voyage-code-3` |
| **Required?** | No - only if skill invoked |
| **Cost** | Pay-per-token |

**Usage Files:**
- `backend/app/skills/voyage_embed.py`

---

### 4.5 GitHub (Debug/Reporting)

| Property | Value |
|----------|-------|
| **Purpose** | Create gists for trace mismatch reports |
| **Env Var** | `GITHUB_TOKEN` |
| **Repo** | `Xuniverzadmin/agenticverz_2.0` |
| **Required?** | No - debug feature only |
| **Cost** | Free |

**Usage Files:**
- `backend/app/api/traces.py`

---

## 5. Infrastructure Services

### 5.1 HashiCorp Vault

| Property | Value |
|----------|-------|
| **Purpose** | Secure secret storage, dynamic credentials |
| **Env Vars** | `VAULT_ADDR`, `VAULT_TOKEN` |
| **Address** | `http://127.0.0.1:8200` (local) |
| **Secrets Path** | `agenticverz/external-integrations` |
| **Required?** | Optional - can use env vars directly |

**Usage Files:**
- `backend/app/secrets/vault_client.py`
- `backend/app/skills/adapters/tenant_config.py`

---

## 6. Internal Tokens

| Token | Purpose | File |
|-------|---------|------|
| `AOS_API_KEY` | Internal API authentication (X-API-Key header) | `backend/app/auth/__init__.py` |
| `MACHINE_SECRET_TOKEN` | Machine-to-machine auth bypass | `backend/app/auth/rbac_middleware.py` |
| `JWT_SECRET` | JWT signature verification (optional) | `backend/app/auth/rbac_middleware.py` |
| `GOLDEN_SECRET` | HMAC signing for golden runs | `backend/app/workflow/golden.py` |
| `SIGNED_URL_SECRET` | Status history export signing | `backend/app/api/status_history.py` |

---

## 7. Configuration Status

### Currently Configured (in `.env`)

| Service | Status | Notes |
|---------|--------|-------|
| Neon PostgreSQL | ✅ Set | `DATABASE_URL` configured |
| Upstash Redis | ✅ Set | `REDIS_URL` configured |
| Clerk Auth | ✅ Set | All `CLERK_*` vars configured |
| Anthropic | ✅ Set | `ANTHROPIC_API_KEY` configured |
| OpenAI | ✅ Set | `OPENAI_API_KEY` configured |
| AOS Internal | ✅ Set | `AOS_API_KEY`, `MACHINE_SECRET_TOKEN` |
| Cloudflare R2 | ⚠️ Commented | Keys in .env but commented out |
| Resend | ❌ Missing | Not in .env |
| Slack | ❌ Missing | Not in .env |
| Voyage AI | ❌ Missing | Not in .env |
| GitHub | ❌ Missing | Not in .env |
| Vault | ⚠️ Local | Running locally, token in .env |

---

## 8. Skill → API Dependency Matrix

| Skill | Required API | Fallback |
|-------|--------------|----------|
| `llm_invoke` | Anthropic OR OpenAI | Other provider |
| `email_send` | Resend | None (fails gracefully) |
| `slack_send` | Slack Webhook | None (fails gracefully) |
| `voyage_embed` | Voyage AI | None (fails gracefully) |
| `http_call` | None | N/A |
| `json_transform` | None | N/A |
| `postgres_query` | Neon (via DATABASE_URL) | None |
| `kv_store` | Redis | None |
| `calendar_write` | Mock (no real API yet) | N/A |
| `webhook_send` | Target webhook URL | None |

---

## 9. Cost Implications

| Service | Pricing Model | Monthly Estimate |
|---------|---------------|------------------|
| Neon PostgreSQL | Free tier / compute-hours | $0-20 |
| Upstash Redis | Free tier / commands | $0-10 |
| Clerk | Free tier (10K MAU) | $0 |
| Anthropic | $3/M input, $15/M output | Variable |
| OpenAI | ~$5/M input, $15/M output | Variable |
| Cloudflare R2 | $0.015/GB storage | ~$1-5 |
| Resend | Free 100/day | $0 |
| Voyage AI | $0.06/M tokens | Variable |

---

## 10. Security Considerations

1. **Never commit `.env`** - Contains all secrets
2. **Rotate keys regularly** - Especially after any breach
3. **Use Vault in production** - For dynamic secret rotation
4. **Audit API key usage** - Monitor for anomalies
5. **Principle of least privilege** - Only enable needed integrations

---

## 11. Adding New Integrations

To add a new external integration:

1. Add env var to `.env.example` (not `.env`)
2. Create skill adapter in `backend/app/skills/`
3. Register in `backend/app/skills/__init__.py`
4. Add to this PIN document
5. Update cost tracking if billable

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-13 | Initial creation - documented all external APIs |
