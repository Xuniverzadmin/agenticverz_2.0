# Accounts Section Audit

**Status:** COMPLETE
**Last Updated:** 2026-01-18
**Reference:** CUSTOMER_CONSOLE_V1_CONSTITUTION.md, ACCOUNTS_ARCHITECTURE.md

---

## 0. Section Characteristics

> **Account is NOT a domain.**
> It manages *who*, *what*, and *billing* — not *what happened*.

**Constitutional Rules:**
- Account is secondary navigation (top-right or footer), NOT sidebar
- Account pages must NOT display executions, incidents, policies, or logs
- Projects are account-scoped containers, not navigation domains
- Users are account members, not activity subjects

**No Capability Registry:** Correct by design. Capabilities are for observable domain behaviors. Account is configuration, not behavior.

**No Intent Files:** Correct by design. Account is not part of the AURORA L2 projection system.

---

## 1. Account Sections

| Section | Question | Status |
|---------|----------|--------|
| **Projects** | What projects (tenants) do I have? | ✅ COMPLETE |
| **Users** | Who has access to my projects? | ✅ COMPLETE |
| **Profile** | Who am I and what's my context? | ✅ COMPLETE |
| **Billing** | What's my plan and usage? | ✅ COMPLETE |
| **API Keys** | What keys exist for API access? | ✅ COMPLETE |
| **Support** | How do I get help? | ✅ COMPLETE |

---

## 2. API Routes

### Primary Facade: `/api/v1/accounts/*`

**File:** `backend/app/api/accounts.py` (~1600 lines, 17 routes)

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/v1/accounts/projects` | GET | List projects | ✅ COMPLETE |
| `/api/v1/accounts/projects/{id}` | GET | Project detail (quotas, usage) | ✅ COMPLETE |
| `/api/v1/accounts/users` | GET | List users in tenant | ✅ COMPLETE |
| `/api/v1/accounts/users/{id}` | GET | User detail (permissions) | ✅ COMPLETE |
| `/api/v1/accounts/users/{id}/role` | PUT | Update user role (owner only) | ✅ COMPLETE |
| `/api/v1/accounts/users/{id}` | DELETE | Remove user from tenant | ✅ COMPLETE |
| `/api/v1/accounts/users/invite` | POST | Invite user to tenant | ✅ COMPLETE |
| `/api/v1/accounts/invitations` | GET | List pending invitations | ✅ COMPLETE |
| `/api/v1/accounts/invitations/{id}/accept` | POST | Accept invitation (public) | ✅ COMPLETE |
| `/api/v1/accounts/profile` | GET | Current user profile | ✅ COMPLETE |
| `/api/v1/accounts/profile` | PUT | Update profile & preferences | ✅ COMPLETE |
| `/api/v1/accounts/billing` | GET | Billing summary | ✅ COMPLETE |
| `/api/v1/accounts/billing/invoices` | GET | Invoice history | ✅ COMPLETE |
| `/api/v1/accounts/support` | GET | Support contact info | ✅ COMPLETE |
| `/api/v1/accounts/support/tickets` | GET | List support tickets | ✅ COMPLETE |
| `/api/v1/accounts/support/tickets` | POST | Create support ticket | ✅ COMPLETE |

### Related Endpoints (tenants.py)

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/v1/api-keys` | GET | List API keys | ✅ COMPLETE |
| `/api/v1/api-keys` | POST | Create API key | ✅ COMPLETE |
| `/api/v1/api-keys/{id}` | DELETE | Revoke API key | ✅ COMPLETE |

---

## 3. Response Models

### GET /api/v1/accounts/projects

```json
{
  "items": [
    {
      "project_id": "string",
      "name": "string",
      "description": "string",
      "status": "active|suspended",
      "plan": "string"
    }
  ],
  "total": 0,
  "has_more": false,
  "filters_applied": {}
}
```

### GET /api/v1/accounts/projects/{id}

```json
{
  "project_id": "string",
  "name": "string",
  "quotas": {
    "max_workers": 0,
    "max_runs_per_day": 0,
    "max_concurrent_runs": 0,
    "max_tokens_per_month": 0,
    "max_api_keys": 0
  },
  "usage": {
    "runs_today": 0,
    "runs_this_month": 0,
    "tokens_this_month": 0
  },
  "onboarding_state": "string",
  "onboarding_complete": false
}
```

### PUT /api/v1/accounts/profile

```json
// Request
{
  "display_name": "string",
  "timezone": "string",
  "preferences": { "key": "value" }
}

// Response
{
  "user_id": "string",
  "email": "string",
  "display_name": "string",
  "timezone": "string",
  "preferences": {},
  "updated_at": "datetime"
}
```

### GET /api/v1/accounts/users/{id}

```json
{
  "user_id": "string",
  "email": "string",
  "name": "string",
  "role": "owner|admin|member|viewer",
  "status": "active|suspended",
  "permissions": {
    "can_manage_keys": false,
    "can_run_workers": false,
    "can_view_runs": false
  },
  "membership": {
    "membership_created_at": "datetime",
    "invited_by": "string|null"
  }
}
```

### POST /api/v1/accounts/users/invite

```json
// Request
{
  "email": "user@example.com",
  "role": "member"
}

// Response
{
  "id": "string",
  "email": "string",
  "role": "string",
  "status": "pending",
  "created_at": "datetime",
  "expires_at": "datetime",
  "invited_by": "string"
}
```

### POST /api/v1/accounts/invitations/{id}/accept

```json
// Request
{
  "token": "invitation-token-from-email"
}

// Response
{
  "message": "Invitation accepted",
  "tenant_id": "string",
  "role": "string"
}
```

### GET /api/v1/accounts/billing

```json
{
  "plan": "string",
  "status": "active|trialing|past_due|canceled",
  "billing_period": "monthly|yearly|unlimited",
  "current_period_start": "datetime",
  "current_period_end": "datetime",
  "usage_this_period": {
    "runs": 0,
    "tokens": 0
  },
  "next_invoice_date": "datetime",
  "quota_context": {
    "max_runs_per_day": 0,
    "max_tokens_per_month": 0
  }
}
```

### GET /api/v1/accounts/billing/invoices

```json
{
  "invoices": [],
  "total": 0,
  "message": "Free tier - unlimited usage, no invoices"
}
```

### POST /api/v1/accounts/support/tickets

```json
// Request
{
  "subject": "Issue title",
  "description": "Detailed description",
  "category": "general|billing|technical|feature",
  "priority": "low|medium|high|urgent"
}

// Response
{
  "id": "string",
  "subject": "string",
  "description": "string",
  "category": "string",
  "priority": "string",
  "status": "open",
  "created_at": "datetime",
  "updated_at": "datetime",
  "resolution": null,
  "resolved_at": null
}
```

---

## 4. Models

### Core Account Models

| Model | Table | Purpose |
|-------|-------|---------|
| `Tenant` | `tenants` | Project container with quotas and usage |
| `User` | `users` | User identity with preferences |
| `TenantMembership` | `tenant_memberships` | User-to-project role assignment |
| `Invitation` | `invitations` | Token-based user invitations |
| `SupportTicket` | `support_tickets` | Customer support tickets → CRM |
| `APIKey` | `api_keys` | API key with permissions and rate limits |
| `Subscription` | `subscriptions` | Billing plan and status |

### Model Details

**Tenant:**
- id, name, slug, clerk_org_id
- plan, billing_email, stripe_customer_id
- Quotas: max_workers, max_runs_per_day, max_concurrent_runs, max_tokens_per_month, max_api_keys
- Usage: runs_today, runs_this_month, tokens_this_month
- status, suspended_reason, onboarding_state

**User:**
- id, email, name, clerk_id
- preferences_json (JSON string with get/set helpers)
- created_at, updated_at

**TenantMembership Roles:**
- `owner` - Full access, can delete project, change roles
- `admin` - Can manage users and keys, invite users
- `member` - Can run workers and view runs
- `viewer` - Read-only access

**Invitation:**
- id, tenant_id, email, role, status
- token_hash (SHA-256, never stores plaintext)
- invited_by, created_at, expires_at (7 days), accepted_at

**SupportTicket:**
- id, tenant_id, user_id
- subject, description, category, priority
- status (open, in_progress, resolved, closed)
- resolution, issue_event_id (CRM reference)
- created_at, updated_at, resolved_at

**APIKey Security:**
- Prefix-based storage (aos_xxxxxxxx)
- SHA-256 hashing (never stores plaintext)
- Expiration, rate limiting, concurrent run limits
- Revocation with reason tracking

---

## 5. Boundary Violation Check

### Constitutional Compliance

| Check | Result | Evidence |
|-------|--------|----------|
| References executions? | ✅ NO | No Run/Execution model imports |
| References incidents? | ✅ NO | No Incident model imports |
| References policies? | ✅ NO | No Policy/PolicyRule imports |
| References logs? | ✅ NO | No Logs/Traces imports |
| Joins to domain tables? | ✅ NO | Only tenant/user/subscription joins |

**Result:** ✅ **ZERO BOUNDARY VIOLATIONS**

The Account API is correctly scoped to secondary navigation concerns only.

---

## 6. Coverage Summary

```
Sections COMPLETE:        6/6 (100%)
Sections PARTIAL:         0/6 (0%)
Sections MISSING:         0/6 (0%)

Endpoints COMPLETE:       19/19 (100%)
Endpoints MISSING:        0/19 (0%)

Boundary Violations:      0 (COMPLIANT)
```

---

## 7. RBAC Permission Matrix

| Role | manage_keys | run_workers | view_runs | manage_users | change_roles |
|------|-------------|-------------|-----------|--------------|--------------|
| owner | ✅ | ✅ | ✅ | ✅ | ✅ |
| admin | ✅ | ✅ | ✅ | ✅ | ❌ |
| member | ❌ | ✅ | ✅ | ❌ | ❌ |
| viewer | ❌ | ❌ | ✅ | ❌ | ❌ |

### Permission Enforcement

```python
# TenantMembership helper methods
def can_manage_users(self) -> bool:
    """Check if this member can invite/manage other users."""
    return self.role in ("owner", "admin")

def can_change_roles(self) -> bool:
    """Check if this member can change other users' roles."""
    return self.role == "owner"
```

---

## 8. CRM Workflow Integration

Support tickets feed into the Part-2 CRM Workflow (10-step process):

```
Step 1:  CRM Ticket Created ← POST /support/tickets
Step 2:  Auto-Classification (category, priority)
Step 3:  Impact Assessment
Step 4:  Pattern Matching
Step 5:  FOUNDER REVIEW (Human-in-the-loop) ← DECISION GATE
Step 6:  Resolution Planning
Step 7:  Implementation
Step 8:  Verification
Step 9:  Documentation
Step 10: Closure
```

**Key Design Decision:** No automatic agent assignment. Human review at Step 5.

**Reference:** `docs/governance/part2/PART2_CRM_WORKFLOW_CHARTER.md`

---

## 9. Database Migration

**Migration:** `ce967f70c95d_invitations_and_support_tickets.py`

**Changes:**
1. `users.preferences_json` - New column for user preferences
2. `invitations` table - Token-based user invitations
3. `support_tickets` table - Customer support tickets

**Apply:**
```bash
export DB_AUTHORITY=neon
export DATABASE_URL=<neon-connection-string>
alembic upgrade head
```

---

## 10. Related Files

| File | Purpose | Lines |
|------|---------|-------|
| `backend/app/api/accounts.py` | Accounts facade (L2) | ~1600 |
| `backend/app/api/tenants.py` | API keys, workers (L2) | 625 |
| `backend/app/models/tenant.py` | Account models (L6) | ~700 |
| `backend/alembic/versions/ce967f70c95d_*.py` | Migration | 98 |

---

## 11. Architecture Notes

### Account vs Domain

| Aspect | Domains | Account |
|--------|---------|---------|
| Navigation | Sidebar (primary) | Top-right/footer (secondary) |
| Data | What happened (events) | Who/what/billing (config) |
| Capabilities | SDSR-observed | None (static config) |
| Intent Files | AURORA_L2_INTENT_* | None |
| Tables | Domain-specific | tenants, users, subscriptions |

### API Key Security Model

```
Generation: aos_ + 32 random bytes (hex)
Storage: Prefix (aos_xxxxxxxx) + SHA-256 hash
Validation: Hash comparison (constant-time)
Revocation: Soft delete with reason + timestamp
Rate Limiting: Per-key RPM limit
Expiration: Optional expiry date
```

### Invitation Security Model

```
Generation: 32 bytes via secrets.token_urlsafe()
Storage: SHA-256 hash only (never plaintext)
Expiration: 7 days from creation
Validation: Constant-time hash comparison
Single-use: Invalidated on accept
```

---

## 12. Implementation Status

**Date:** 2026-01-18

**Overall Grade: A+**

The Accounts section is fully implemented, properly isolated, and constitutionally compliant.

### Summary Table

| Component | Status | Notes |
|-----------|--------|-------|
| Projects CRUD | ✅ COMPLETE | List, detail, quotas, usage |
| Users CRUD | ✅ COMPLETE | List, detail, permissions |
| User Invitations | ✅ COMPLETE | Invite, list, accept with token |
| User Role Management | ✅ COMPLETE | Update role, remove user |
| Profile View | ✅ COMPLETE | User + tenant context |
| Profile Update | ✅ COMPLETE | Name, timezone, preferences |
| Billing Summary | ✅ COMPLETE | Plan, status, usage |
| Invoice History | ✅ COMPLETE | Free tier = unlimited |
| Support Contact | ✅ COMPLETE | Contact info endpoint |
| Support Tickets | ✅ COMPLETE | Create, list → CRM workflow |
| API Key Management | ✅ COMPLETE | Full CRUD with security |
| Tenant Isolation | ✅ ENFORCED | All endpoints scoped |
| RBAC | ✅ INTEGRATED | Role-based permissions |
| Constitution Compliance | ✅ ZERO VIOLATIONS | No domain data exposed |

---

## 13. Change Log

| Date | Change |
|------|--------|
| 2026-01-18 | COMPLETE: Added invitations, support tickets, profile preferences, user management |
| 2026-01-16 | Initial audit (A- grade, 67% sections, 82% endpoints) |
