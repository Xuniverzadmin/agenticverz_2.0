# PIN-089: M21 - Tenant, Authentication & Billing Layer

**Status:** COMPLETE
**Date:** 2024-12-16
**Milestone:** M21
**Depends On:** PIN-088 (Worker Execution Console)

---

## Overview

M21 implements the production-ready multi-tenant infrastructure for AOS:

1. **API Key System** - Database-backed API key authentication with SHA-256 hashing
2. **Tenant Isolation** - Per-tenant resource isolation and data segregation
3. **Quota Enforcement** - Runs per day, tokens per month, concurrent run limits
4. **Billing Layer** - Usage metering and cost tracking
5. **Worker Registry** - Dynamic worker discovery from database
6. **Deployment Config** - NGINX with rate limiting, CORS, SSE support

## Architecture

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         API Request                                  │
│  Header: X-AOS-Key: aos_xxxxxxxxxxxxxxxxxxxx                        │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    tenant_auth.py: get_tenant_context()             │
│  1. Extract API key from header                                     │
│  2. SHA-256 hash the key                                            │
│  3. Look up key_hash in api_keys table                              │
│  4. Validate: status=active, not expired                            │
│  5. Load tenant from tenant_id                                      │
│  6. Check tenant status=active                                      │
│  7. Return TenantContext                                            │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         TenantContext                               │
│  - tenant_id, tenant_slug, tenant_name                              │
│  - plan (free, pro, enterprise)                                     │
│  - api_key_id, api_key_name                                         │
│  - permissions: ["run:*", "read:*"]                                 │
│  - allowed_workers: [] (empty = all)                                │
│  - rate_limit_rpm, max_concurrent_runs                              │
└─────────────────────────────────────────────────────────────────────┘
```

### Database Schema

```
┌─────────────────────────────────────────────────────────────────────┐
│  tenants                                                             │
├─────────────────────────────────────────────────────────────────────┤
│  id (PK)        │ slug (unique)  │ name          │ plan             │
│  max_workers    │ max_runs/day   │ max_tokens/mo │ max_api_keys     │
│  runs_today     │ runs_this_mo   │ tokens_this_mo│ status           │
└─────────────────────────────────────────────────────────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  api_keys                                                            │
├─────────────────────────────────────────────────────────────────────┤
│  id (PK)        │ tenant_id (FK) │ name          │ key_prefix       │
│  key_hash       │ status         │ permissions   │ allowed_workers  │
│  rate_limit_rpm │ max_concurrent │ expires_at    │ total_requests   │
└─────────────────────────────────────────────────────────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  worker_runs                                                         │
├─────────────────────────────────────────────────────────────────────┤
│  id (PK)        │ tenant_id (FK) │ worker_id     │ api_key_id       │
│  task           │ status         │ success       │ total_tokens     │
│  cost_cents     │ created_at     │ completed_at  │                  │
└─────────────────────────────────────────────────────────────────────┘
```

## Plan Quotas

| Plan | Workers | Runs/Day | Tokens/Month | API Keys | Concurrent |
|------|---------|----------|--------------|----------|------------|
| Free | 3 | 100 | 1M | 5 | 5 |
| Pro | 10 | 1,000 | 10M | 20 | 20 |
| Enterprise | 100 | 100,000 | 1B | 100 | 100 |

## API Endpoints

### Tenant Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/tenant` | GET | Get current tenant info |
| `/api/v1/tenant/usage` | GET | Get usage summary |
| `/api/v1/tenant/quota/runs` | GET | Check run quota |
| `/api/v1/tenant/quota/tokens` | GET | Check token quota |

### API Key Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/api-keys` | GET | List API keys |
| `/api/v1/api-keys` | POST | Create new key |
| `/api/v1/api-keys/{id}` | DELETE | Revoke key |

### Worker Registry

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/workers` | GET | List all workers |
| `/api/v1/workers/available` | GET | List workers for tenant |
| `/api/v1/workers/{id}` | GET | Get worker details |
| `/api/v1/workers/{id}/config` | GET | Get worker config |
| `/api/v1/workers/{id}/config` | PUT | Set worker config |

### Run History

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/runs` | GET | List runs for tenant |

## Files Created/Modified

### New Files

```
backend/
├── alembic/versions/036_m21_tenant_auth_billing.py  # Migration
├── app/
│   ├── models/tenant.py                              # SQLModel models
│   ├── auth/tenant_auth.py                           # Auth middleware
│   ├── services/
│   │   ├── tenant_service.py                         # Tenant/billing service
│   │   └── worker_registry_service.py                # Worker registry
│   └── api/tenants.py                                # API endpoints

deploy/
└── nginx/aos-console.conf                            # NGINX config
```

### Modified Files

```
backend/app/
├── auth/__init__.py           # Export tenant auth
├── services/__init__.py       # Export new services
├── models/__init__.py         # Export tenant models
└── main.py                    # Wire tenants router
```

## Usage Examples

### Creating an API Key

```bash
curl -X POST "https://api.agenticverz.com/api/v1/api-keys" \
  -H "X-AOS-Key: aos_admin_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Key",
    "permissions": ["run:*", "read:*"],
    "allowed_workers": ["business-builder"],
    "expires_in_days": 90
  }'

# Response:
{
  "id": "uuid-here",
  "name": "Production Key",
  "key_prefix": "aos_xxxxxxxx",
  "key": "aos_full_key_only_shown_once_store_securely",
  "status": "active",
  "created_at": "2024-12-16T05:00:00Z"
}
```

### Running a Worker with Tenant Isolation

```bash
curl -X POST "https://api.agenticverz.com/api/v1/workers/business-builder/run-streaming" \
  -H "X-AOS-Key: aos_tenant_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Build landing page for AI fitness coach",
    "async_mode": false
  }'
```

### Checking Quota Before Run

```bash
curl "https://api.agenticverz.com/api/v1/tenant/quota/runs" \
  -H "X-AOS-Key: aos_tenant_key_here"

# Response:
{
  "allowed": true,
  "reason": "",
  "quota_name": "runs_per_day",
  "current": 45,
  "limit": 100
}
```

## Rate Limiting (NGINX)

| Zone | Limit | Burst | Description |
|------|-------|-------|-------------|
| api_limit | 60/min | 30 | General API endpoints |
| sse_limit | 5/min | 2 | SSE streaming connections |
| key_limit | 10/min | 5 | API key operations |
| sse_conn | 5 | - | Max concurrent SSE per key |

## Security Considerations

1. **API Keys are SHA-256 hashed** - Only the hash is stored in database
2. **Full key shown once** - On creation only, never retrievable again
3. **Key prefix for identification** - `aos_xxxxxxxx` visible for management
4. **Permissions scoped** - Keys can be limited to specific workers/actions
5. **Rate limiting** - Per-key and per-IP limits prevent abuse
6. **Tenant isolation** - All queries scoped to tenant_id from API key

## Migration Notes

1. Run migration 036 to create tables
2. Default workers are seeded (business-builder, code-debugger, etc.)
3. Existing env-based API key (`AOS_API_KEY`) works via fallback mode
4. Set `AOS_USE_LEGACY_AUTH=false` to disable fallback

## Next Steps

1. **Worker Settings UI** - Frontend for worker configuration
2. **Billing Dashboard** - Usage visualization and alerts
3. **Stripe Integration** - Payment processing for Pro/Enterprise
4. **SSO Integration** - Clerk organization sync

---

## References

- PIN-087: Business Builder Worker API Hosting
- PIN-088: Worker Execution Console
- PIN-086: Business Builder Worker v0.2 Architecture
