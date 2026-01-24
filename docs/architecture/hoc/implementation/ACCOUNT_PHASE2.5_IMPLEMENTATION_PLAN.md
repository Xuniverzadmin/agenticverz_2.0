# Account Domain — Phase 2.5B Implementation Plan
# Status: COMPLETE → LOCKED
# Date: 2026-01-24
# Reference: HOC_LAYER_TOPOLOGY_V1.md, ACCOUNT_DOMAIN_ANALYSIS_REPORT.md
# Lock Document: ACCOUNT_DOMAIN_LOCK_FINAL.md

---

## Core Axiom (LOCKED)

> **Account is a MANAGEMENT domain, not an operations domain.**
> It manages who, what, and billing — not what happened.

Consequences:
1. Account pages MUST NOT display executions, incidents, policies, or logs
2. L4 may decide **user roles, membership, profile updates, billing status**
3. L4 must NEVER decide **run quotas, token limits, tenant suspension** (platform concerns)
4. L6 may only **persist, query, or aggregate account data**
5. Call flow: **Facade → Engine → Driver** (mandatory)

---

## Violation Summary

| # | File | Violation | Severity | Phase |
|---|------|-----------|----------|-------|
| 1 | `facades/accounts_facade.py` | L4 with sqlalchemy runtime imports | CRITICAL | I |
| 2 | `facades/accounts_facade.py` | L4→L7 model imports | CRITICAL | I |
| 3 | `drivers/tenant_service.py` | L6 contains business logic | CRITICAL | I |
| 4 | `drivers/tenant_service.py` | BANNED_NAMING (`*_service.py`) | MEDIUM | I |
| 5 | `engines/email_verification.py` | Layer/location mismatch (L3 in engines/) | CRITICAL | II |
| 6 | `engines/user_write_service.py` | BANNED_NAMING (`*_service.py`) | MEDIUM | II |
| 7 | `drivers/worker_registry_service.py` | BANNED_NAMING (`*_service.py`) | MEDIUM | II |
| 8 | `notifications/engines/channel_service.py` | BANNED_NAMING (`*_service.py`) | MEDIUM | II |
| 9 | `support/CRM/engines/validator_service.py` | BANNED_NAMING (`*_service.py`) | MEDIUM | II |

---

## Phase I — Hard Violations (Boundary Repair)

### I.1 — accounts_facade.py Extraction

**Current State:**
- File declares L4
- Contains sqlalchemy imports at runtime (lines 34-35)
- Contains L7 model imports (lines 37-46)
- 1300+ lines with direct DB queries in every async method

**Target State:**
- Facade becomes orchestration-only
- All DB access moves to driver
- Call flow: Facade → Driver

**Extraction Plan:**

```
BEFORE:
  accounts_facade.py (L4) — contains DB queries

AFTER:
  accounts_facade.py (L4) — orchestration only
      ↓ delegates to
  accounts_facade_driver.py (L6) — pure DB access
```

**Files to Create:**
1. `drivers/accounts_facade_driver.py` — L6 pure data access

**Functions to Extract:**

| Facade Method | Driver Method | Returns |
|---------------|---------------|---------|
| `list_projects()` | `fetch_tenants()` | `list[TenantSnapshot]` |
| `get_project_detail()` | `fetch_tenant_by_id()` | `Optional[TenantDetailSnapshot]` |
| `list_users()` | `fetch_users_by_tenant()` | `list[UserSnapshot]` |
| `get_user_detail()` | `fetch_user_by_id()` | `Optional[UserDetailSnapshot]` |
| `list_tenant_users()` | `fetch_tenant_memberships()` | `list[MembershipSnapshot]` |
| `update_user_role()` | `update_membership_role()` | `MembershipSnapshot` |
| `remove_user()` | `delete_membership()` | `bool` |
| `get_profile()` | `fetch_user_profile()` | `Optional[ProfileSnapshot]` |
| `update_profile()` | `update_user_profile()` | `ProfileSnapshot` |
| `get_billing_summary()` | `fetch_subscription()` | `Optional[SubscriptionSnapshot]` |
| `get_billing_invoices()` | `fetch_invoices()` | `list[InvoiceSnapshot]` |
| `create_support_ticket()` | `insert_support_ticket()` | `TicketSnapshot` |
| `list_support_tickets()` | `fetch_support_tickets()` | `list[TicketSnapshot]` |
| `invite_user()` | `insert_invitation()` | `InvitationSnapshot` |
| `list_invitations()` | `fetch_invitations()` | `list[InvitationSnapshot]` |
| `accept_invitation()` | `update_invitation_accepted()` | `InvitationSnapshot` |

**Facade Transformation:**
- Remove sqlalchemy imports
- Add TYPE_CHECKING block for type hints
- Inject driver as dependency
- Delegate all DB operations to driver
- Keep business logic (role validation, permission checks) in facade

---

### I.2 — tenant_service.py Split (Engine + Driver)

**Current State:**
- File declares L6 (drivers/)
- Contains sqlalchemy/sqlmodel imports (line 23)
- Contains L7 model imports (lines 26-35)
- Contains both READ and WRITE operations
- Contains BUSINESS LOGIC (quota enforcement, plan management)
- BANNED naming (`*_service.py`)

**Target State:**
- Engine (L4): quota decisions, plan logic, status validation
- Driver (L6): all SQL/ORM operations, snapshot DTOs

**Split Plan:**

```
BEFORE:
  tenant_service.py (L6) — mixed: DB queries + business logic

AFTER:
  tenant_engine.py (L4) — quota decisions, plan logic
      ↓ delegates to
  tenant_driver.py (L6) — pure DB access
```

**Files to Create:**
1. `drivers/tenant_driver.py` — L6 pure data access
2. `engines/tenant_engine.py` — L4 business logic

**Files to Delete:**
1. `drivers/tenant_service.py` — removed after split

**Extraction Plan:**

| Service Method | Layer | Destination |
|----------------|-------|-------------|
| `create_tenant()` | L6 | Driver: `insert_tenant()` |
| `get_tenant()` | L6 | Driver: `fetch_tenant_by_id()` |
| `get_tenant_by_slug()` | L6 | Driver: `fetch_tenant_by_slug()` |
| `update_tenant_plan()` | L4+L6 | Engine: `update_plan()` → Driver: `update_tenant()` |
| `suspend_tenant()` | L4+L6 | Engine: `suspend()` → Driver: `update_tenant_status()` |
| `create_membership_with_default()` | L6 | Driver: `insert_membership()` |
| `create_api_key()` | L4+L6 | Engine: `create_key()` → Driver: `insert_api_key()` |
| `list_api_keys()` | L6 | Driver: `fetch_api_keys()` |
| `revoke_api_key()` | L4+L6 | Engine: `revoke_key()` → Driver: `update_api_key_revoked()` |
| `check_run_quota()` | **L4** | Engine: `check_run_quota()` |
| `check_token_quota()` | **L4** | Engine: `check_token_quota()` |
| `increment_usage()` | L4+L6 | Engine: `increment_usage()` → Driver: `update_usage()` |
| `_maybe_reset_daily_counter()` | **L4** | Engine: `maybe_reset_daily_counter()` |
| `record_usage()` | L6 | Driver: `insert_usage_record()` |
| `get_usage_summary()` | L6 | Driver: `fetch_usage_summary()` |
| `create_run()` | L4+L6 | Engine: `create_run()` → Driver: `insert_run()` |
| `complete_run()` | L4+L6 | Engine: `complete_run()` → Driver: `update_run()` |
| `list_runs()` | L6 | Driver: `fetch_runs()` |
| `_audit()` | L6 | Driver: `insert_audit_log()` |

**Business Logic in Engine (L4):**
- `check_run_quota()`: Validate tenant status, check daily/concurrent limits
- `check_token_quota()`: Validate token budget
- `maybe_reset_daily_counter()`: Temporal logic for daily reset
- `update_plan()`: Apply PLAN_QUOTAS based on plan type
- `create_run()`: Quota check + delegate to driver
- `complete_run()`: Token tracking + delegate to driver

---

## Phase II — Intent Resolution

### II.1 — email_verification.py Reclassification

**Current State:**
- Declares L3 (Boundary Adapter)
- Located in `engines/`
- Redis-only (no PostgreSQL)

**Analysis:**
- Contains domain-local verification logic
- OTP generation, cooldown, rate limiting = business logic
- NOT protocol adaptation (not L3)

**Decision:** Reclassify as L4

**After:**
```python
# Layer: L4 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Temporal:
#   Trigger: api
#   Execution: async (Redis operations)
# Role: Email OTP verification engine for customer onboarding
#
# RECLASSIFICATION NOTE (2026-01-24):
# This file was previously declared as L3 (Boundary Adapter).
# Reclassified to L4 because it contains domain-specific verification
# logic (OTP generation, cooldown, rate limiting). Redis-only state.
```

---

### II.2 — File Renames (BANNED naming)

| Current Name | New Name | Layer |
|--------------|----------|-------|
| `engines/user_write_service.py` | `engines/user_write_engine.py` | L4 |
| `drivers/worker_registry_service.py` | `drivers/worker_registry_driver.py` | L6 |
| `notifications/engines/channel_service.py` | `notifications/engines/channel_engine.py` | L4 |
| `support/CRM/engines/validator_service.py` | `support/CRM/engines/validator_engine.py` | L4 |

---

## Snapshot Dataclasses

### accounts_facade_driver.py

```python
@dataclass
class TenantSnapshot:
    """Tenant data from DB for list view."""
    id: str
    name: str
    slug: str
    status: str
    plan: str
    created_at: datetime
    updated_at: Optional[datetime]

@dataclass
class TenantDetailSnapshot:
    """Detailed tenant data from DB."""
    id: str
    name: str
    slug: str
    status: str
    plan: str
    max_workers: int
    max_runs_per_day: int
    max_concurrent_runs: int
    max_tokens_per_month: int
    max_api_keys: int
    runs_today: int
    runs_this_month: int
    tokens_this_month: int
    onboarding_state: int
    created_at: datetime
    updated_at: Optional[datetime]

@dataclass
class UserSnapshot:
    """User data from DB for list view."""
    id: str
    email: str
    name: Optional[str]
    status: str
    role: str
    created_at: datetime
    last_login_at: Optional[datetime]

@dataclass
class UserDetailSnapshot:
    """Detailed user data from DB."""
    id: str
    email: str
    name: Optional[str]
    avatar_url: Optional[str]
    status: str
    email_verified: bool
    oauth_provider: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    last_login_at: Optional[datetime]

@dataclass
class MembershipSnapshot:
    """Tenant membership data from DB."""
    id: str
    tenant_id: str
    user_id: str
    role: str
    invited_by: Optional[str]
    created_at: datetime

@dataclass
class ProfileSnapshot:
    """User profile data from DB."""
    user_id: str
    email: str
    name: Optional[str]
    avatar_url: Optional[str]
    preferences_json: Optional[str]
    created_at: datetime

@dataclass
class SubscriptionSnapshot:
    """Subscription data from DB."""
    id: str
    tenant_id: str
    plan: str
    status: str
    billing_period: str
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]

@dataclass
class InvitationSnapshot:
    """Invitation data from DB."""
    id: str
    tenant_id: str
    email: str
    role: str
    status: str
    token_hash: str
    invited_by: str
    created_at: datetime
    expires_at: datetime
    accepted_at: Optional[datetime]

@dataclass
class TicketSnapshot:
    """Support ticket data from DB."""
    id: str
    tenant_id: str
    user_id: str
    subject: str
    description: str
    category: str
    priority: str
    status: str
    resolution: Optional[str]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
```

### tenant_driver.py

```python
@dataclass
class TenantCoreSnapshot:
    """Core tenant data for engine operations."""
    id: str
    name: str
    slug: str
    status: str
    plan: str
    max_workers: int
    max_runs_per_day: int
    max_concurrent_runs: int
    max_tokens_per_month: int
    max_api_keys: int
    runs_today: int
    tokens_this_month: int
    last_run_reset_at: Optional[datetime]
    created_at: datetime

@dataclass
class RunCountSnapshot:
    """Running count for quota checks."""
    count: int

@dataclass
class UsageRecordSnapshot:
    """Usage record data."""
    id: str
    tenant_id: str
    meter_name: str
    amount: int
    unit: str
    period_start: datetime
    period_end: datetime
```

---

## Execution Checklist

### Phase I Execution

- [x] **I.1.1** Create `drivers/accounts_facade_driver.py` with snapshot dataclasses ✅ (2026-01-24)
- [x] **I.1.2** Implement driver fetch methods (DB queries) ✅ (2026-01-24)
- [x] **I.1.3** Update facade to use TYPE_CHECKING pattern ✅ (2026-01-24)
- [x] **I.1.4** Update facade to delegate to driver ✅ (2026-01-24)
- [x] **I.1.5** Run BLCA verification — target: 0 violations for facade ✅ (2026-01-24)
- [x] **I.2.1** Create `drivers/tenant_driver.py` with snapshot dataclasses ✅ (2026-01-24)
- [x] **I.2.2** Implement driver fetch/update methods (DB queries + mutations) ✅ (2026-01-24)
- [x] **I.2.3** Create `engines/tenant_engine.py` with business logic ✅ (2026-01-24)
- [x] **I.2.4** Update engine to delegate to driver ✅ (2026-01-24)
- [x] **I.2.5** Update all callers of TenantService to use new engine/driver ✅ (2026-01-24) — No HOC callers found
- [x] **I.2.6** Delete `drivers/tenant_service.py` ✅ (2026-01-24)
- [x] **I.2.7** Run BLCA verification — target: 0 violations for tenant ✅ (2026-01-24)

### Phase II Execution

- [x] **II.1.1** Reclassify email_verification.py header to L4 ✅ (2026-01-24)
- [x] **II.1.2** Add reclassification note ✅ (2026-01-24)
- [x] **II.2.1** Rename `user_write_service.py` → `user_write_engine.py` ✅ (2026-01-24)
- [x] **II.2.2** Update imports in callers ✅ (2026-01-24) — No HOC callers found
- [x] **II.2.3** Rename `worker_registry_service.py` → `worker_registry_driver.py` ✅ (2026-01-24)
- [x] **II.2.4** Update imports in callers ✅ (2026-01-24) — No HOC callers found
- [x] **II.2.5** Rename `channel_service.py` → `channel_engine.py` ✅ (2026-01-24)
- [x] **II.2.6** Update imports in callers ✅ (2026-01-24) — No HOC callers found
- [x] **II.2.7** Rename `validator_service.py` → `validator_engine.py` ✅ (2026-01-24)
- [x] **II.2.8** Update imports in callers ✅ (2026-01-24) — No HOC callers found

### Post-Remediation

- [x] Run full BLCA scan — target: 0 violations for account domain ✅ (2026-01-24)
    - All 9 original violations resolved
    - Only unrelated issue: missing header in memory_pins.py (out of scope)
- [x] Update all __init__.py exports ✅ (2026-01-24)
- [x] Create ACCOUNT_DOMAIN_LOCK_FINAL.md ✅ (2026-01-24)
- [x] Update HOC INDEX.md ✅ (2026-01-24)

---

## Transitional Debt Policy

**Decision:** ❌ NO transitional debt approved

Rationale:
- Account domain handles user identity and billing — security-critical
- Any "temporary" shortcut becomes a security liability
- Prior domains (api_keys, overview, incidents) achieved zero debt
- Zero-debt is achievable here

---

## Governance Invariants

| ID | Rule | Enforcement |
|----|------|-------------|
| **INV-ACCT-001** | L4 cannot import sqlalchemy at runtime | BLOCKING |
| **INV-ACCT-002** | L4 cannot import from L7 models directly | BLOCKING |
| **INV-ACCT-003** | Facades delegate, never query directly | BLOCKING |
| **INV-ACCT-004** | Call flow: Facade → Engine → Driver | BLOCKING |
| **INV-ACCT-005** | Driver returns snapshots, not ORM models | BLOCKING |
| **INV-ACCT-006** | `*_service.py` naming banned | BLOCKING |
| **INV-ACCT-007** | L6 contains no business logic | BLOCKING |

---

## Risk Assessment

| Factor | Assessment | Mitigation |
|--------|------------|------------|
| File Size | HIGH (accounts_facade.py is 1300+ lines) | Extract incrementally by method group |
| Caller Count | MEDIUM (tenant_service.py has many callers) | Update callers in parallel |
| Test Coverage | UNKNOWN | Run existing tests after each change |
| API Compatibility | LOW (internal changes only) | Maintain same facade interface |

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-01-24 | 1.0.0 | Initial plan created |
| 2026-01-24 | 1.1.0 | Phase I complete: accounts_facade.py extracted, tenant_service.py split |
| 2026-01-24 | 1.2.0 | Phase II complete: All 4 files renamed, email_verification reclassified |
| 2026-01-24 | 1.3.0 | Post-remediation: __init__.py exports updated, BLCA verified 0 account violations |

---

**STATUS: COMPLETE → LOCKED**

See: `ACCOUNT_DOMAIN_LOCK_FINAL.md`

**END OF IMPLEMENTATION PLAN**
