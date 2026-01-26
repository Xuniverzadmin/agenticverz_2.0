# Demo Tenant Identity Contract

**Status:** ACTIVE
**Effective:** 2026-01-21
**Reference:** Tenant Resolution Contract, Environment Contract

## Purpose

This document defines the canonical Demo Tenant strategy for AOS. The Demo Tenant enables
local development and testing without requiring a full Clerk/OAuth setup while maintaining
the same tenant isolation guarantees as production.

## Core Principle

> **Tenant identity must be fully resolved before entering the service layer.**
> **Services never infer, parse, or default tenant_id.**
> **Tenant IDs MUST be valid UUIDs.**

## Demo Tenant UUIDs (Canonical)

Each DB authority has its own Demo Tenant to prevent cross-environment confusion:

| DB Authority | Demo Tenant UUID | Slug |
|--------------|------------------|------|
| **LOCAL** | `11111111-1111-1111-1111-111111111101` | `demo-tenant-101` |
| **NEON TEST** | `22222222-2222-2222-2222-222222222101` | `demo-tenant-102` |
| **PROD** | *(no demo tenant - use real tenants)* | - |

## Demo API Keys

Each Demo Tenant has a pre-configured API key:

| DB Authority | API Key ID | Key Prefix |
|--------------|------------|------------|
| LOCAL | `11111111-1111-1111-1111-111111111102` | `aos_demo_te` |
| NEON TEST | `22222222-2222-2222-2222-222222222102` | `aos_demo_te` |

## Usage Pattern

### Machine-Plane Requests (SDK, CLI, Integrations)

For machine-plane requests that use `X-AOS-Key` authentication, the tenant_id is
resolved from the API key's database record:

```bash
# The API key is looked up in the database
# tenant_id is extracted from the key's record
curl -X GET \
  -H "X-AOS-Key: $AOS_API_KEY" \
  "http://localhost:8000/api/v1/integrations"
```

### Header Fallback (Development Only)

When no API key is provided, the `X-Tenant-ID` header can be used as a fallback.
This is primarily for development scenarios:

```bash
# Explicit tenant ID via header (must be valid UUID)
curl -X GET \
  -H "X-Tenant-ID: 11111111-1111-1111-1111-111111111101" \
  "http://localhost:8000/api/v1/integrations"
```

### Human-Plane Requests (Console)

For human-plane requests using Clerk JWT authentication, the tenant_id is
extracted from the JWT claims by the auth middleware.

## Resolution Order

The `resolve_tenant_id()` function follows this order:

1. **Auth Context** (JWT or DB-backed API key) → `auth_context.tenant_id`
2. **X-Tenant-ID Header** (machine-plane fallback) → must be valid UUID
3. **Fail Closed** → 400 error, never guess

## Invalid Tenant ID Handling

If a tenant_id is not a valid UUID, the system returns a 400 error:

```json
{
  "detail": "Invalid tenant_id in auth context: sdsr-tenant-e2e-004"
}
```

This is the **correct behavior**. The error indicates:
- The API key was validated successfully (auth passed)
- The key's `tenant_id` in the database is invalid (data problem)
- Fix the data, not the resolver

## Database Setup

### Create Demo Tenant (LOCAL)

```sql
INSERT INTO tenants (
    id, name, slug, plan, status, onboarding_state
) VALUES (
    '11111111-1111-1111-1111-111111111101',
    'Demo Tenant 101',
    'demo-tenant-101',
    'enterprise',
    'active',
    4  -- COMPLETE
);
```

### Create Demo API Key (LOCAL)

```sql
INSERT INTO api_keys (
    id, tenant_id, name, key_prefix, key_hash, status
) VALUES (
    '11111111-1111-1111-1111-111111111102',
    '11111111-1111-1111-1111-111111111101',
    'Demo Tenant 101 API Key',
    'aos_demo_te',
    '<sha256_hash_of_key>',
    'active'
);
```

### Migration Script

For one-time cleanup of invalid tenant data, use:

```bash
psql "$DATABASE_URL" -f scripts/migrations/fix_demo_tenant_uuid.sql
```

## Forbidden Patterns

| Pattern | Why Forbidden |
|---------|---------------|
| `tenant_id = "demo-tenant"` | Not a UUID, breaks validation |
| `tenant_id = str(None)` | Resolver must not return string "None" |
| `tenant_id = None` (where required) | Fail closed, not silent default |
| Inferring tenant from context | Must be explicitly declared |

## Key Files

| File | Role |
|------|------|
| `app/auth/tenant_resolver.py` | Single authority for tenant resolution |
| `scripts/migrations/fix_demo_tenant_uuid.sql` | Cleanup migration |
| `docs/architecture/ENVIRONMENT_CONTRACT.md` | Environment and auth planes |

## Troubleshooting

### Error: "Invalid tenant_id in auth context: xyz"

**Cause:** The API key's `tenant_id` column contains a non-UUID value.

**Fix:**
1. Query the API key: `SELECT tenant_id FROM api_keys WHERE key_hash = '<hash>'`
2. If `tenant_id` is not a UUID, either:
   - Update the key to reference a valid tenant
   - Delete and recreate the key with proper tenant reference

### Error: "tenant_id required (provide via auth or X-Tenant-ID header)"

**Cause:** No tenant context found in request.

**Fix:**
1. For machine requests: Provide valid `X-AOS-Key` header
2. For development: Provide `X-Tenant-ID: <uuid>` header
3. For human requests: Ensure Clerk JWT is valid

## Related Documents

- [Environment Contract](./ENVIRONMENT_CONTRACT.md)
- [Auth Architecture Baseline](./auth/AUTH_ARCHITECTURE_BASELINE.md)
- [Tenant Resolver Source](../../backend/app/auth/tenant_resolver.py)
