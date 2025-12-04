# Auth Service Integration Requirements

> **Status:** Phase 5 of M5 GA Learning Path
> **Last Updated:** 2025-12-04
> **Purpose:** Document requirements for replacing RBAC stub with real auth service

---

## Current State

The RBAC module (`backend/app/auth/rbac.py`) is implemented with a **stub mode** that:
- Returns mock roles when `RBAC_ENABLED=false` (default)
- Grants `max_approval_level=3` (team lead) to all users
- Allows all approvals at levels 1-3 without real verification

When `RBAC_ENABLED=true`:
- Calls auth service at `AUTH_SERVICE_URL` (default: `http://localhost:8001`)
- Fails closed (denies) if auth service is unavailable
- Enforces real role-based permissions

---

## Auth Service API Contract

The AOS backend expects the auth service to implement this endpoint:

### GET `/api/v1/users/{user_id}/roles`

**Request:**
```
GET /api/v1/users/user-123/roles?tenant_id=tenant-abc
```

**Response (200 OK):**
```json
{
  "user_id": "user-123",
  "roles": ["team_lead", "engineer"],
  "max_approval_level": 3,
  "tenant_id": "tenant-abc"
}
```

**Response (404 Not Found):**
```json
{
  "error": "user_not_found",
  "message": "User user-123 not found"
}
```

---

## Role Hierarchy

| Role | Approval Level | Description |
|------|----------------|-------------|
| `owner`, `admin` | 5 | Owner override, requires audit |
| `manager`, `policy_admin`, `director` | 4 | Manager-level approval |
| `team_lead`, `senior_engineer`, `tech_lead` | 3 | Team lead approval |
| `team_member`, `engineer`, `developer` | 2 | Standard team member |
| `guest`, `readonly` | 1 | Self-approval only |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RBAC_ENABLED` | `false` | Enable real RBAC checks |
| `AUTH_SERVICE_URL` | `http://localhost:8001` | Auth service base URL |
| `AUTH_SERVICE_TIMEOUT` | `5.0` | Request timeout in seconds |

---

## Integration Steps

### Step 1: Deploy Auth Service

Deploy an auth service that implements the API contract above. Options:
- **Keycloak** with custom REST API adapter
- **Auth0** with Rules/Actions to expose roles endpoint
- **Custom service** with user/role database

### Step 2: Configure Environment

Add to `docker-compose.yml` or `.env`:
```bash
RBAC_ENABLED=true
AUTH_SERVICE_URL=http://your-auth-service:8001
AUTH_SERVICE_TIMEOUT=5.0
```

### Step 3: Test with curl

```bash
# Test auth service directly
curl http://your-auth-service:8001/api/v1/users/test-user/roles

# Test AOS approval with RBAC
curl -X POST http://127.0.0.1:8000/api/v1/policy/approval-requests/{id}/approve \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $AOS_API_KEY" \
  -d '{"approver_id": "real-user-id", "approved": true}'
```

### Step 4: Monitor

Watch for these log entries:
```
nova.auth.rbac - rbac_check - allowed=true/false
nova.auth.rbac - owner_level_approval_attempt (for level 5)
```

---

## Failure Modes

| Scenario | Behavior |
|----------|----------|
| Auth service down | **Fail closed** - all approvals denied |
| User not found | 403 Forbidden with error message |
| Timeout | 403 Forbidden with "service unavailable" |
| Invalid level | ValueError (5xx error) |

---

## Security Considerations

1. **Fail Closed:** Always deny if auth service is unavailable
2. **Audit Logging:** Level 5 approvals are logged with warning level
3. **Tenant Isolation:** Pass `tenant_id` for multi-tenant environments
4. **No Token Caching:** Each request validates fresh (consider adding short TTL cache)

---

## Testing Checklist

Before enabling in production:

- [ ] Auth service deployed and healthy
- [ ] Test user with level 5 role exists
- [ ] Test user with level 2 role exists
- [ ] Verify 403 returned for insufficient permissions
- [ ] Verify approval succeeds for sufficient permissions
- [ ] Test auth service failure handling
- [ ] Monitor alert rules configured for RBAC failures

---

## Rollback Plan

If issues occur after enabling RBAC:

```bash
# Immediate rollback
export RBAC_ENABLED=false
docker compose up -d backend worker

# Or in docker-compose.yml:
# RBAC_ENABLED: "false"
```

All approvals will return to stub mode (level 3 granted to all).

---

## Next Steps

1. Choose auth provider (Keycloak/Auth0/Custom)
2. Implement `/api/v1/users/{id}/roles` endpoint
3. Deploy to staging environment
4. Run integration tests with real users
5. Enable `RBAC_ENABLED=true` in production
6. Monitor for 24-48 hours before removing fallback
