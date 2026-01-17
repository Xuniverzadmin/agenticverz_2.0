# API Key Governance

**Status:** ACTIVE
**Effective:** 2026-01-17
**Reference:** Analytics Cost Wiring Session

---

## Purpose

This document establishes governance rules for API key management to prevent authentication confusion during development and testing.

---

## 1. Canonical API Keys

### Production/Demo Keys (Neon Database)

| Environment Variable | Tenant ID | Purpose | Rotation Date |
|---------------------|-----------|---------|---------------|
| `DEMO_TENANT_API_KEY` | `demo-tenant` | Analytics, Cost, Console demo | 2026-01-17 |
| `AOS_API_KEY` | `sdsr-tenant-e2e-004` | SDSR E2E testing | - |

### Key Location

- **Plaintext**: `.env` file (never committed)
- **Hash**: `api_keys` table in Neon database

---

## 2. Governance Rules

### APIKEY-001: Key-Tenant Mapping Must Be Documented

Before using an API key for testing:
1. Verify which tenant_id the key maps to
2. Confirm test data exists for that tenant
3. Document the mapping in this file

**Violation Response:**
```
APIKEY-001 VIOLATION: Unknown key-tenant mapping.

Before testing, verify:
1. SELECT tenant_id FROM api_keys WHERE key_hash = sha256(your_key);
2. Confirm test data exists: SELECT COUNT(*) FROM <table> WHERE tenant_id = '<tenant>';
3. If no mapping exists, rotate/create key per Section 3.
```

### APIKEY-002: Key Rotation Protocol

When rotating API keys:

1. Generate new key: `openssl rand -hex 32`
2. Compute hash: `echo -n "$KEY" | sha256sum | cut -d' ' -f1`
3. Update database:
   ```sql
   -- Invalidate old key (optional)
   UPDATE api_keys SET status = 'revoked', revoked_at = NOW()
   WHERE tenant_id = '<tenant>' AND status = 'active';

   -- Insert new key
   INSERT INTO api_keys (id, tenant_id, name, key_prefix, key_hash, status, ...)
   VALUES (...);
   ```
4. Store plaintext in `.env`
5. Update this document

### APIKEY-003: Never Guess Key Mappings

**Forbidden:**
- Assuming `AOS_API_KEY` works for all tenants
- Testing with keys without verifying tenant mapping
- Using local database keys against Neon (or vice versa)

**Required:**
- Always verify key → tenant mapping before testing
- Use environment-specific keys

---

## 3. Key Rotation Procedure

```bash
# 1. Generate new key
NEW_KEY=$(openssl rand -hex 32)
KEY_HASH=$(echo -n "$NEW_KEY" | sha256sum | cut -d' ' -f1)
KEY_PREFIX=$(echo "$NEW_KEY" | cut -c1-8)

# 2. Insert into database
psql $DATABASE_URL -c "
INSERT INTO api_keys (id, tenant_id, name, key_prefix, key_hash, status, total_requests, is_synthetic)
VALUES (
  '<unique-id>',
  '<tenant-id>',
  '<descriptive-name>',
  '$KEY_PREFIX',
  '$KEY_HASH',
  'active',
  0,
  false
);"

# 3. Add to .env
echo "NEW_VAR_NAME=$NEW_KEY" >> .env

# 4. Update this document
```

---

## 4. Database Connection Awareness

### Backend Database Authority

| Environment | Database | Notes |
|-------------|----------|-------|
| Docker backend | Neon (production) | `DATABASE_URL` in docker-compose |
| Local scripts | Depends on `DATABASE_URL` | Check before running |
| Docker postgres | Local only | Test data isolation |

**Rule:** Always verify which database the backend is connected to before testing API endpoints.

```bash
# Check backend's database
docker exec nova_agent_manager env | grep DATABASE
```

---

## 5. Quick Reference

### Test Analytics/Cost Endpoint

```bash
# Use demo-tenant key
curl -s -X GET \
  -H "X-AOS-Key: $DEMO_TENANT_API_KEY" \
  "http://localhost:8000/api/v1/analytics/statistics/cost?from=2025-12-01T00:00:00Z&to=2025-12-31T23:59:59Z"
```

### Verify Key Mapping

```bash
# Hash your key
echo -n "$YOUR_KEY" | sha256sum | cut -d' ' -f1

# Check in database
psql $DATABASE_URL -c "SELECT tenant_id FROM api_keys WHERE key_hash = '<hash>';"
```

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-01-17 | Initial creation, DEMO_TENANT_API_KEY rotated | Claude |
