# Accounts Architecture

**Status:** IMPLEMENTED
**Last Updated:** 2026-01-22
**Reference:** CUSTOMER_CONSOLE_V1_CONSTITUTION.md, PART2_CRM_WORKFLOW_CHARTER.md, PIN-463 (L4 Facade Pattern)

---

## 1. Overview

### 1.1 Governing Principle

> **Account is NOT a domain.**
> It manages *who*, *what*, and *billing* — not *what happened*.

The Accounts section is **secondary navigation** (top-right or footer), not sidebar. It is the customer's control plane for identity, access, and billing — completely isolated from operational data (executions, incidents, policies, logs).

### 1.2 Scope

| Concern | Account Handles | Account Does NOT Handle |
|---------|-----------------|-------------------------|
| Identity | Users, profiles, preferences | N/A |
| Access | Invitations, roles, API keys | Execution permissions |
| Organization | Projects (tenants) | Workflow configuration |
| Billing | Plans, invoices, usage | Cost attribution per-run |
| Support | Tickets, contact info | Incident response |

### 1.3 Design Principles

1. **ONE Facade Architecture** - All account APIs route through `/api/v1/accounts/*`
2. **Tenant Isolation** - Every request is scoped to `auth_context.tenant_id`
3. **RBAC Enforcement** - Role-based access control on all mutations
4. **Zero Domain Coupling** - No imports from domain models (runs, incidents, policies)
5. **CRM Integration** - Support tickets feed into Part-2 workflow (no auto-assignment)

---

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CUSTOMER CONSOLE                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  TOP-RIGHT / FOOTER (Secondary Navigation)                          │ │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │ │
│  │  │Projects │ │ Users   │ │ Profile │ │ Billing │ │ Support │       │ │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘       │ │
│  └───────┼──────────┼──────────┼──────────┼──────────┼─────────────────┘ │
└──────────┼──────────┼──────────┼──────────┼──────────┼───────────────────┘
           │          │          │          │          │
           ▼          ▼          ▼          ▼          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    /api/v1/accounts/* (ONE FACADE)                      │
│                                                                          │
│  L2 Product API Layer                                                   │
│  File: backend/app/api/aos_accounts.py                                      │
│                                                                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐             │
│  │ Projects       │  │ Users          │  │ Support        │             │
│  │ GET /projects  │  │ GET /users     │  │ POST /tickets  │             │
│  │ GET /{id}      │  │ PUT /{id}/role │  │ GET /tickets   │             │
│  └────────────────┘  │ DELETE /{id}   │  └────────────────┘             │
│                      │ POST /invite   │                                  │
│  ┌────────────────┐  └────────────────┘  ┌────────────────┐             │
│  │ Profile        │                      │ Billing        │             │
│  │ GET /profile   │  ┌────────────────┐  │ GET /billing   │             │
│  │ PUT /profile   │  │ Invitations    │  │ GET /invoices  │             │
│  └────────────────┘  │ GET /          │  └────────────────┘             │
│                      │ POST /{id}/    │                                  │
│                      │   accept       │                                  │
│                      └────────────────┘                                  │
└─────────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         L6 DATA LAYER                                    │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │   tenants    │  │    users     │  │ subscriptions│                   │
│  └──────────────┘  └──────────────┘  └──────────────┘                   │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │  tenant_     │  │ invitations  │  │  support_    │                   │
│  │ memberships  │  │              │  │  tickets     │                   │
│  └──────────────┘  └──────────────┘  └──────────────┘                   │
│                                                                          │
│  File: backend/app/models/tenant.py                                     │
└─────────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     CRM WORKFLOW (Part-2)                                │
│                                                                          │
│  Support Ticket → Issue Event → Auto-Classification → Founder Review    │
│                                                                          │
│  Reference: docs/governance/part2/PART2_CRM_WORKFLOW_CHARTER.md         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. L4 Domain Facade

**File:** `backend/app/services/accounts_facade.py`
**Getter:** `get_accounts_facade()` (singleton)

The Accounts Facade is the single entry point for all account management logic. L2 API routes
must call facade methods rather than implementing inline SQL queries.

### 3.1 Architecture Pattern

```
┌─────────────────────┐
│   L2: accounts.py   │  (Endpoint handlers)
│   - Auth extraction │
│   - Request params  │
│   - Response mapping│
└──────────┬──────────┘
           │ await facade.method()
           ▼
┌─────────────────────┐
│  L4: AccountsFacade │  (Domain logic)
│   - Query building  │
│   - Validation      │
│   - Result mapping  │
└──────────┬──────────┘
           │ session.execute()
           ▼
┌─────────────────────┐
│   L6: Database      │  (Data access)
└─────────────────────┘
```

### 3.2 Usage Pattern

```python
from app.services.accounts_facade import get_accounts_facade, AccountsErrorResult

facade = get_accounts_facade()
result = await facade.list_projects(session, tenant_id)

# For operations that can fail, check for error results
if isinstance(result, AccountsErrorResult):
    raise HTTPException(status_code=result.status_code, detail=result.message)
```

### 3.3 Operations Provided

| Method | Purpose | Returns |
|--------|---------|---------|
| `list_projects()` | Projects list | `ProjectsListResult` |
| `get_project_detail()` | Project detail | `ProjectDetailResult` |
| `list_users()` | Users list (O2) | `UsersListResult` |
| `get_user_detail()` | User detail (O3) | `UserDetailResult` |
| `list_tenant_users()` | Tenant users list | `TenantUsersListResult` |
| `invite_user()` | Send user invitation | `InvitationResult \| AccountsErrorResult` |
| `update_user_role()` | Change user role | `TenantUserResult \| AccountsErrorResult` |
| `remove_user()` | Remove user from tenant | `dict \| AccountsErrorResult` |
| `get_profile()` | Current user profile | `ProfileResult` |
| `update_profile()` | Update user profile | `ProfileUpdateResult` |
| `get_billing_summary()` | Billing summary | `BillingSummaryResult` |
| `get_billing_invoices()` | Invoice list | `InvoicesListResult` |
| `get_support_contact()` | Support contact info | `SupportContactResult` |
| `create_support_ticket()` | Create support ticket | `SupportTicketResult` |
| `list_support_tickets()` | List support tickets | `SupportTicketsListResult` |
| `list_invitations()` | Pending invitations | `InvitationsListResult` |
| `accept_invitation()` | Accept an invitation | `AcceptInvitationResult` |

### 3.4 L2-to-L4 Result Type Mapping

All L4 facade methods return dataclass result types that L2 maps to Pydantic response models:

| L4 Result Type | L2 Response Model | Purpose |
|----------------|-------------------|---------|
| `ProjectsListResult` | `ProjectsListResponse` | Projects list |
| `ProjectDetailResult` | `ProjectDetailResponse` | Project detail |
| `UsersListResult` | `UsersListResponse` | Users list |
| `UserDetailResult` | `UserDetailResponse` | User detail |
| `TenantUsersListResult` | `TenantUserListResponse` | Tenant users list |
| `TenantUserResult` | `TenantUserResponse` | Tenant user |
| `ProfileResult` | `ProfileResponse` | User profile |
| `ProfileUpdateResult` | `ProfileUpdateResponse` | Profile update |
| `BillingSummaryResult` | `BillingSummaryResponse` | Billing summary |
| `InvoicesListResult` | `InvoicesListResponse` | Invoice list |
| `SupportContactResult` | `SupportContactResponse` | Support contact |
| `SupportTicketResult` | `SupportTicketResponse` | Support ticket |
| `SupportTicketsListResult` | `SupportTicketsListResponse` | Tickets list |
| `InvitationsListResult` | `InvitationsListResponse` | Invitations list |
| `InvitationResult` | `InvitationResponse` | Invitation |
| `AcceptInvitationResult` | `dict` | Invitation accept |
| `AccountsErrorResult` | `HTTPException` | Error handling |

### 3.5 Facade Rules

- L2 routes call facade methods, never direct SQL
- Facade returns typed dataclass results
- Facade handles tenant isolation internally
- Error cases return `AccountsErrorResult` for union types
- Account does NOT display executions, incidents, policies, or logs

---

## 4. Data Models

### 3.1 Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────────┐       ┌─────────────┐
│   Tenant    │───────│TenantMembership │───────│    User     │
│             │  1:N  │                 │  N:1  │             │
│ id          │       │ id              │       │ id          │
│ name        │       │ tenant_id       │       │ email       │
│ plan        │       │ user_id         │       │ name        │
│ status      │       │ role            │       │ preferences │
│ quotas      │       │ created_at      │       │ created_at  │
└─────────────┘       └─────────────────┘       └─────────────┘
      │                                                │
      │ 1:N                                            │ 1:N
      ▼                                                ▼
┌─────────────┐       ┌─────────────────┐       ┌─────────────┐
│ Subscription│       │   Invitation    │       │SupportTicket│
│             │       │                 │       │             │
│ id          │       │ id              │       │ id          │
│ tenant_id   │       │ tenant_id       │       │ tenant_id   │
│ plan        │       │ email           │       │ user_id     │
│ status      │       │ role            │       │ subject     │
│ period      │       │ token_hash      │       │ description │
│ dates       │       │ invited_by      │       │ status      │
└─────────────┘       │ expires_at      │       │ priority    │
                      └─────────────────┘       └─────────────┘
```

### 3.2 Model Details

#### Tenant (Project)
```python
class Tenant(SQLModel, table=True):
    id: str                          # UUID primary key
    name: str                        # Display name
    slug: str                        # URL-safe identifier
    clerk_org_id: Optional[str]      # Clerk integration

    # Plan & Billing
    plan: str                        # free, starter, pro, enterprise
    billing_email: Optional[str]
    stripe_customer_id: Optional[str]

    # Quotas
    max_workers: int                 # Default: 3
    max_runs_per_day: int            # Default: 100
    max_concurrent_runs: int         # Default: 5
    max_tokens_per_month: int        # Default: 1,000,000
    max_api_keys: int                # Default: 10

    # Usage (reset daily/monthly)
    runs_today: int
    runs_this_month: int
    tokens_this_month: int

    # Status
    status: str                      # active, suspended
    suspended_reason: Optional[str]
    onboarding_state: str            # created, configured, verified, complete
```

#### User
```python
class User(SQLModel, table=True):
    id: str                          # UUID primary key
    email: str                       # Unique email
    name: Optional[str]              # Display name
    clerk_id: Optional[str]          # Clerk user ID
    preferences_json: Optional[str]  # JSON preferences (timezone, theme, etc.)

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Helper methods
    def get_preferences(self) -> dict
    def set_preferences(self, prefs: dict) -> None
```

#### TenantMembership
```python
class TenantMembership(SQLModel, table=True):
    id: str                          # UUID primary key
    tenant_id: str                   # FK → tenants
    user_id: str                     # FK → users
    role: str                        # owner, admin, member, viewer
    created_at: datetime

    # Permission helpers
    def can_manage_users(self) -> bool   # owner, admin
    def can_change_roles(self) -> bool   # owner only
```

#### Invitation
```python
class Invitation(SQLModel, table=True):
    id: str                          # UUID primary key
    tenant_id: str                   # FK → tenants
    email: str                       # Invitee email
    role: str                        # Assigned role on accept
    status: str                      # pending, accepted, expired, revoked
    token_hash: str                  # SHA-256 hash of invite token
    invited_by: str                  # FK → users
    created_at: datetime
    expires_at: datetime             # 7-day default
    accepted_at: Optional[datetime]
```

#### SupportTicket
```python
class SupportTicket(SQLModel, table=True):
    id: str                          # UUID primary key
    tenant_id: str                   # FK → tenants
    user_id: str                     # FK → users (creator)

    # Ticket content
    subject: str                     # Max 200 chars
    description: str                 # Max 4000 chars
    category: str                    # general, billing, technical, feature
    priority: str                    # low, medium, high, urgent

    # Status tracking
    status: str                      # open, in_progress, resolved, closed
    resolution: Optional[str]        # Resolution notes
    issue_event_id: Optional[str]    # CRM workflow reference

    # Timestamps
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
```

---

## 4. API Reference

### 4.1 Projects

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/accounts/projects` | GET | Any | List projects for current user |
| `/api/v1/accounts/projects/{id}` | GET | Any | Get project detail with quotas |

### 4.2 Users & Invitations

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/accounts/users` | GET | Any | List users in current tenant |
| `/api/v1/accounts/users/{id}` | GET | Any | Get user detail with permissions |
| `/api/v1/accounts/users/{id}/role` | PUT | Owner | Change user's role |
| `/api/v1/accounts/users/{id}` | DELETE | Admin+ | Remove user from tenant |
| `/api/v1/accounts/users/invite` | POST | Admin+ | Send invitation email |
| `/api/v1/accounts/invitations` | GET | Admin+ | List pending invitations |
| `/api/v1/accounts/invitations/{id}/accept` | POST | Public | Accept invitation (token-based) |

### 4.3 Profile

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/accounts/profile` | GET | Any | Get current user profile |
| `/api/v1/accounts/profile` | PUT | Any | Update profile and preferences |

### 4.4 Billing

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/accounts/billing` | GET | Any | Get billing summary |
| `/api/v1/accounts/billing/invoices` | GET | Any | Get invoice history |

**Note:** Free tier (demo-tenant) returns unlimited usage, no invoices.

### 4.5 Support

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/accounts/support` | GET | Any | Get support contact info |
| `/api/v1/accounts/support/tickets` | GET | Any | List user's support tickets |
| `/api/v1/accounts/support/tickets` | POST | Any | Create support ticket |

---

## 5. RBAC Permission Matrix

### 5.1 Role Hierarchy

```
owner > admin > member > viewer
```

### 5.2 Permission Matrix

| Permission | Owner | Admin | Member | Viewer |
|------------|-------|-------|--------|--------|
| View projects | ✅ | ✅ | ✅ | ✅ |
| View users | ✅ | ✅ | ✅ | ✅ |
| View billing | ✅ | ✅ | ✅ | ✅ |
| Update profile | ✅ | ✅ | ✅ | ✅ |
| Create tickets | ✅ | ✅ | ✅ | ✅ |
| Invite users | ✅ | ✅ | ❌ | ❌ |
| Remove users | ✅ | ✅ | ❌ | ❌ |
| Change roles | ✅ | ❌ | ❌ | ❌ |
| Remove owners | ✅ | ❌ | ❌ | ❌ |

### 5.3 Implementation

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

## 6. Invitation Flow

### 6.1 Flow Diagram

```
┌─────────────────┐
│  Admin/Owner    │
│  invites user   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ POST /users/    │────▶│ Create          │
│ invite          │     │ Invitation      │
└─────────────────┘     │ (7-day expiry)  │
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │ Generate token  │
                        │ Store hash      │
                        │ Send email*     │
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │ User clicks     │
                        │ invitation link │
                        └────────┬────────┘
                                 │
         ┌───────────────────────┴───────────────────────┐
         │                                               │
         ▼                                               ▼
┌─────────────────┐                             ┌─────────────────┐
│ User exists     │                             │ User does NOT   │
│ with email      │                             │ exist           │
└────────┬────────┘                             └────────┬────────┘
         │                                               │
         │                                               ▼
         │                                      ┌─────────────────┐
         │                                      │ Create User     │
         │                                      │ (from email)    │
         │                                      └────────┬────────┘
         │                                               │
         └───────────────────────┬───────────────────────┘
                                 │
                        ┌────────▼────────┐
                        │ Create          │
                        │ TenantMembership│
                        │ with role       │
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │ Mark invitation │
                        │ as accepted     │
                        └─────────────────┘
```

*Email sending is a TODO - currently returns token for manual testing.

### 6.2 Security

- **Token**: 32-byte random, URL-safe (secrets.token_urlsafe)
- **Storage**: SHA-256 hash only (never store plaintext)
- **Expiry**: 7 days from creation
- **Single-use**: Token invalidated on accept
- **Validation**: Constant-time hash comparison

---

## 7. Support Ticket → CRM Workflow

### 7.1 Integration Overview

Support tickets created via `/api/v1/accounts/support/tickets` feed into the Part-2 CRM Workflow. This provides structured customer feedback without automatic agent assignment.

### 7.2 CRM Workflow (10 Steps)

```
Step 1:  CRM Ticket Created (POST /support/tickets)
    │
Step 2:  Auto-Classification (category, priority)
    │
Step 3:  Impact Assessment (scope, affected systems)
    │
Step 4:  Pattern Matching (similar issues, known solutions)
    │
Step 5:  FOUNDER REVIEW (Human-in-the-loop) ◀── DECISION GATE
    │
Step 6:  Resolution Planning (if approved)
    │
Step 7:  Implementation
    │
Step 8:  Verification
    │
Step 9:  Documentation
    │
Step 10: Closure
```

### 7.3 Issue Sources

| Source | Description |
|--------|-------------|
| `crm_feedback` | Customer feedback via support ticket |
| `support_ticket` | Direct support request |
| `ops_alert` | Operational alert (system-generated) |
| `manual` | Manual entry by team |

### 7.4 Implementation

```python
@router.post("/support/tickets", response_model=SupportTicketResponse)
async def create_support_ticket(
    request: Request,
    ticket: SupportTicketCreate,
    session: AsyncSession = Depends(get_async_session_dep),
) -> SupportTicketResponse:
    """
    Create a support ticket.

    This feeds into the CRM workflow (Part-2) with human-in-the-loop
    at Step 5 (Founder Review). No automatic agent assignment.
    """
    # ... create ticket ...

    # TODO: Trigger CRM workflow via issue_event_id
    # Step 1: CRM Ticket Created
    # Step 2: Auto-Classification (from category, priority)
```

---

## 8. Database Schema

### 8.1 Migration: ce967f70c95d

**File:** `backend/alembic/versions/ce967f70c95d_invitations_and_support_tickets.py`

**Changes:**
1. Add `preferences_json` column to `users` table
2. Create `invitations` table with indexes
3. Create `support_tickets` table with indexes

### 8.2 Table: invitations

```sql
CREATE TABLE invitations (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    token_hash VARCHAR(128) NOT NULL,
    invited_by VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    accepted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX ix_invitations_tenant_id ON invitations(tenant_id);
CREATE INDEX ix_invitations_email ON invitations(email);
CREATE INDEX ix_invitations_token_hash ON invitations(token_hash);
```

### 8.3 Table: support_tickets

```sql
CREATE TABLE support_tickets (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject VARCHAR(200) NOT NULL,
    description VARCHAR(4000) NOT NULL,
    category VARCHAR(50) NOT NULL DEFAULT 'general',
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    status VARCHAR(50) NOT NULL DEFAULT 'open',
    resolution VARCHAR(4000),
    issue_event_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    resolved_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX ix_support_tickets_tenant_id ON support_tickets(tenant_id);
CREATE INDEX ix_support_tickets_user_id ON support_tickets(user_id);
CREATE INDEX ix_support_tickets_status ON support_tickets(status);
```

---

## 9. Constitutional Compliance

### 9.1 Boundary Checks

| Check | Result | Evidence |
|-------|--------|----------|
| References executions? | ✅ NO | No Run model imports |
| References incidents? | ✅ NO | No Incident model imports |
| References policies? | ✅ NO | No Policy imports |
| References logs/traces? | ✅ NO | No Trace imports |
| Joins to domain tables? | ✅ NO | Only tenant/user joins |

**Result:** ✅ **ZERO BOUNDARY VIOLATIONS**

### 9.2 Navigation Compliance

| Rule | Status |
|------|--------|
| Account is secondary navigation | ✅ COMPLIANT |
| No sidebar placement | ✅ COMPLIANT |
| No domain data display | ✅ COMPLIANT |
| Projects are containers, not domains | ✅ COMPLIANT |

---

## 10. Files

| File | Layer | Purpose | Lines |
|------|-------|---------|-------|
| `backend/app/api/aos_accounts.py` | L2 | API endpoints | ~1600 |
| `backend/app/models/tenant.py` | L6 | Data models | ~700 |
| `backend/alembic/versions/ce967f70c95d_*.py` | L6 | Migration | 98 |

---

## 11. Related Documents

| Document | Purpose |
|----------|---------|
| `ACCOUNTS_SECTION_AUDIT.md` | Implementation audit |
| `CUSTOMER_CONSOLE_V1_CONSTITUTION.md` | Navigation governance |
| `PART2_CRM_WORKFLOW_CHARTER.md` | CRM workflow spec |
| `RBAC_AUTHORITY_SEPARATION_DESIGN.md` | Permission model |

---

## 12. Change Log

| Date | Change |
|------|--------|
| 2026-01-22 | Updated L4 facade section with architecture pattern and result type mapping |
| 2026-01-18 | Added invitations, support_tickets, profile preferences |
| 2026-01-16 | Initial audit completed (A- grade) |
