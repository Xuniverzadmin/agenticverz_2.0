# Auth Blocker Notes (PIN-009)

**Status:** BLOCKING M8 COMPLETION
**Source:** PIN-009-EXTERNAL-ROLLOUT-PENDING.md
**Priority:** CRITICAL

---

## The Problem

RBAC is currently using a **STUB** that returns mock roles. External users cannot be onboarded until real auth is wired.

### Current State

```python
# backend/app/auth/rbac.py:84-92
if not RBAC_ENABLED:
    # Return mock response when RBAC is disabled
    logger.debug(f"RBAC disabled, returning mock roles for {approver_id}")
    return {
        "user_id": approver_id,
        "roles": ["team_member"],
        "max_approval_level": 3,  # Default to team lead level
        "tenant_id": tenant_id,
    }
```

### Risk

- **Unauthorized actions** - Anyone can approve anything
- **Compliance violations** - No audit trail of real users
- **Security breach** - No real identity verification

---

## Required Changes

### 1. Deploy Real Auth Provider

Options:
- **Keycloak** (self-hosted, open source)
- **Auth0** (managed, paid)
- **Custom auth service** (if existing)

### 2. Environment Configuration

```bash
# .env changes required
AUTH_SERVICE_URL=https://your-auth-provider.com  # Currently: http://localhost:8001 (stub)
AUTH_SERVICE_TIMEOUT=5.0
RBAC_ENABLED=true  # Already set
```

### 3. Required API Endpoint

Auth service must implement:

```
GET /api/v1/users/{user_id}/roles?tenant_id={tenant_id}

Response:
{
  "user_id": "user-123",
  "roles": ["admin", "team_lead"],
  "max_approval_level": 4,
  "tenant_id": "tenant-abc"
}
```

### 4. Files Affected

| File | Change |
|------|--------|
| `.env` | Add AUTH_SERVICE_URL |
| `docker-compose.yml` | Add AUTH_SERVICE_URL to backend env |
| `backend/app/auth/rbac.py` | Already coded, just needs real URL |

---

## Verification Steps

After wiring real auth:

```bash
# 1. Test unauthorized access is blocked
curl -X POST http://localhost:8000/api/v1/policy/requests/{id}/approve \
  -H "Content-Type: application/json" \
  -d '{"approver_id": "low_level_user", "level": 5}'
# Expected: HTTP 403

# 2. Test authorized access works
curl -X POST http://localhost:8000/api/v1/policy/requests/{id}/approve \
  -H "Authorization: Bearer <valid_token>" \
  -H "Content-Type: application/json" \
  -d '{"approver_id": "admin_user", "level": 5}'
# Expected: HTTP 200

# 3. Verify audit log
psql -h localhost -p 6432 -U nova -d nova_aos \
  -c "SELECT * FROM rbac_audit ORDER BY created_at DESC LIMIT 5"
```

---

## Auth Service Requirements Doc

Full specification at: `/root/agenticverz2.0/docs/AUTH_SERVICE_REQUIREMENTS.md`

### Key Requirements

1. **JWT or Session-based auth**
2. **Role retrieval endpoint** - GET /users/{id}/roles
3. **Tenant isolation** - Roles scoped to tenant
4. **Audit logging** - All auth decisions logged
5. **Timeout handling** - 5 second default

---

## Acceptance Criteria for M8

- [ ] Real auth provider deployed (Keycloak/Auth0/custom)
- [ ] AUTH_SERVICE_URL configured with real endpoint
- [ ] RBAC smoke tests pass with real tokens
- [ ] 403 responses verified for unauthorized actors
- [ ] Level 5 (owner override) audit logging works
- [ ] No stub auth anywhere in production path

---

## Timeline Impact

| If Auth Delayed | Impact |
|-----------------|--------|
| 1-2 days | Acceptable, parallel SDK work |
| 3-5 days | M8 slips, rearrange to SDK-first |
| 1+ week | Critical path risk, escalate |

---

## Decision Required

**Which auth provider will you use?**

1. **Keycloak** - Self-hosted, full control, more setup
2. **Auth0** - Managed, quick start, cost scales with users
3. **Custom** - If you have existing auth infrastructure

This decision must be made before M8 Day 1.
