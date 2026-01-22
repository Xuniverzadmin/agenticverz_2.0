# HOC Account Domain Analysis v1.0

**Domain:** customer/account
**Date:** 2026-01-22
**Status:** CLEANUP COMPLETE (v1.1)

---

## 1. FILE INVENTORY

**Total Files:** 17 Python files

```
account/
├── __init__.py                      # Domain root (12 LOC)
├── facades/
│   ├── __init__.py                  # Facade exports (11 LOC)
│   ├── accounts_facade.py           # Main unified facade (1308 LOC)
│   └── notifications_facade.py      # Notifications facade (471 LOC)
├── engines/
│   ├── __init__.py                  # Engine exports (11 LOC)
│   ├── iam_service.py               # IAM service - VIOLATION! (433 LOC)
│   ├── identity_resolver.py         # Identity resolvers (198 LOC)
│   ├── tenant_service.py            # Tenant CRUD/quotas (634 LOC)
│   ├── profile.py                   # Governance profile config (452 LOC)
│   ├── user_write_service.py        # User write operations (112 LOC)
│   └── email_verification.py        # OTP email verification (286 LOC)
├── drivers/
│   └── __init__.py                  # Reserved for L3 adapters (empty)
├── schemas/
│   └── __init__.py                  # Reserved for DTOs (empty)
├── notifications/
│   └── engines/
│       └── channel_service.py       # Multi-channel notifications (1098 LOC)
└── support/
    └── CRM/
        └── engines/
            ├── validator_service.py # CRM issue validator (731 LOC)
            ├── audit_service.py     # Governance audit (886 LOC)
            └── job_executor.py      # CRM job executor (521 LOC)
```

---

## 2. VIOLATIONS DETECTED

### 2.1 AUDIENCE Violation: iam_service.py

| Attribute | Value |
|-----------|-------|
| File | `engines/iam_service.py` |
| Header | `# AUDIENCE: INTERNAL` |
| Current Path | `customer/account/engines/iam_service.py` |
| Required Path | `internal/platform/iam/engines/iam_service.py` |
| Violation Type | BL-AUD-001 (Audience boundary) |

**File Header (lines 1-12):**
```python
# Layer: L4 — Domain Engines
# AUDIENCE: INTERNAL          <-- VIOLATION!
# PHASE: W2
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: IAM service for identity and access management
# Callers: Auth middleware, API routes
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: GAP-173 (IAM Integration)
```

**Reason for Move:**
- IAM is internal infrastructure used by auth middleware
- CUSTOMER code should not directly import IAM internals
- CUSTOMER facades should use high-level auth abstractions

---

## 3. FACADES ANALYSIS

### 3.1 accounts_facade.py (1308 LOC)

**Purpose:** Unified facade for all account domain operations

**Header:**
- Layer: L4 — Domain Engine
- AUDIENCE: CUSTOMER
- Product: ai-console

**Key Exports:**
- `AccountsFacade` - Main class
- `get_accounts_facade()` - Singleton accessor

**Operations:**
- **Projects:** list_projects, get_project_detail
- **Users:** list_users, get_user_detail, list_tenant_users, update_user_role, remove_user
- **Profile:** get_profile, update_profile
- **Billing:** get_billing_summary, get_billing_invoices
- **Support:** get_support_contact, create_support_ticket, list_support_tickets
- **Invitations:** invite_user, list_invitations, accept_invitation

**Result Types (28):**
```python
# Projects
ProjectSummaryResult, ProjectsListResult, ProjectDetailResult

# Users
UserSummaryResult, UsersListResult, UserDetailResult
TenantUserResult, TenantUsersListResult

# Profile
ProfileResult, ProfileUpdateResult

# Billing
BillingSummaryResult, InvoiceSummaryResult, InvoiceListResult

# Support
SupportContactResult, SupportTicketResult, SupportTicketListResult

# Invitations
InvitationResult, InvitationListResult, AcceptInvitationResult

# Error
AccountsErrorResult
```

### 3.2 notifications_facade.py (471 LOC)

**Purpose:** Centralized notification operations

**Header:**
- Layer: L4 — Domain Engine
- Product: system-wide

**Key Exports:**
- `NotificationsFacade` - Main class
- `get_notifications_facade()` - Singleton accessor

**Operations:**
- send_notification, list_notifications, get_notification, mark_as_read
- list_channels, get_channel
- get_preferences, update_preferences

---

## 4. ENGINES ANALYSIS

### 4.1 iam_service.py (433 LOC) - VIOLATION

**Purpose:** Identity and access management (RBAC)

**Header:**
- Layer: L4 — Domain Engines
- **AUDIENCE: INTERNAL** ← In wrong location!

**Key Classes:**
- `Identity` - Resolved identity from any provider
- `AccessDecision` - Result of access control check
- `IAMService` - Main IAM service

**Key Methods:**
- `resolve_identity()` - Resolve identity from token/key
- `check_access()` - Check permission for resource/action
- `grant_role()`, `revoke_role()` - Role management
- `define_role()`, `define_resource_permissions()` - Configuration

### 4.2 identity_resolver.py (198 LOC)

**Purpose:** Identity resolution from various providers

**Header:**
- Layer: L4 — Domain Engines
- Product: system-wide

**Key Classes:**
- `IdentityResolver` (ABC) - Abstract resolver
- `ClerkIdentityResolver` - Clerk JWT resolver
- `APIKeyIdentityResolver` - API key resolver
- `SystemIdentityResolver` - System identity resolver
- `IdentityChain` - Chain of resolvers

### 4.3 tenant_service.py (634 LOC)

**Purpose:** Tenant CRUD, API keys, quotas

**Header:**
- Layer: L6 — Platform Substrate
- Product: system-wide

**Key Classes:**
- `TenantService` - Main service
- `TenantServiceError`, `QuotaExceededError` - Exceptions

**Key Methods:**
- Tenant: create, get, update_plan, suspend, create_membership
- API Keys: create, list, revoke
- Quotas: check_run_quota, check_token_quota, increment_usage
- Runs: create_run, complete_run, list_runs
- Usage: record_usage, get_usage_summary

### 4.4 profile.py (452 LOC)

**Purpose:** Governance profile configuration (NOT user profile)

**Header:**
- Layer: L4 — Domain Engine
- Product: system-wide

**Key Classes:**
- `GovernanceProfile` - Enum (STRICT, STANDARD, OBSERVE_ONLY)
- `GovernanceConfig` - Configuration dataclass

**Key Functions:**
- `get_governance_profile()` - Get from environment
- `load_governance_config()` - Load with overrides
- `validate_governance_config()` - Validate combinations
- `validate_governance_at_startup()` - Startup hook

### 4.5 user_write_service.py (112 LOC)

**Purpose:** DB write operations for User management

**Header:**
- Layer: L4 — Domain Engine
- Product: system-wide

**Key Class:**
- `UserWriteService` - Write-only service

**Methods:**
- `create_user()` - Create new user
- `update_user_login()` - Update last_login_at
- `user_to_dict()` - Convert to dict

### 4.6 email_verification.py (286 LOC)

**Purpose:** OTP-based email verification

**Header:**
- Layer: L3 — Boundary Adapter
- Product: AI Console

**Key Classes:**
- `EmailVerificationService` - Main service
- `VerificationResult` - Result dataclass

**Key Methods:**
- `send_otp()` - Generate and send OTP
- `verify_otp()` - Verify OTP code

---

## 5. NOTIFICATIONS SUBDOMAIN

### 5.1 channel_service.py (1098 LOC)

**Purpose:** Multi-channel notification management

**Header:**
- Layer: L4 — Domain Engines
- Product: system-wide
- Reference: GAP-017 (Notify Channels)

**Key Enums:**
- `NotifyChannel` - UI, WEBHOOK, EMAIL, SLACK, PAGERDUTY, TEAMS
- `NotifyEventType` - ALERT_*, INCIDENT_*, POLICY_*, RUN_*, SYSTEM_*
- `NotifyChannelStatus` - ENABLED, DISABLED, FAILED, UNCONFIGURED

**Key Classes:**
- `NotifyChannelConfig` - Channel configuration
- `NotifyDeliveryResult` - Delivery result
- `NotifyChannelService` - Main service

**Key Methods:**
- configure_channel, get_channel_config, get_all_configs
- enable_channel, disable_channel, set_event_filter
- send (to all enabled channels)
- check_health, get_delivery_history

---

## 6. SUPPORT/CRM SUBDOMAIN

### 6.1 validator_service.py (731 LOC)

**Purpose:** CRM issue validation (advisory verdicts)

**Header:**
- Layer: L4 — Domain Engine
- Product: system-wide

**Governance Rule:** VALIDATOR-IS-ADVISORY (Non-Negotiable)

**Key Enums:**
- `IssueType` - CAPABILITY_REQUEST, BUG_REPORT, CONFIGURATION_CHANGE, ESCALATION, UNKNOWN
- `Severity` - CRITICAL, HIGH, MEDIUM, LOW
- `RecommendedAction` - CREATE_CONTRACT, DEFER, REJECT, ESCALATE

**Key Classes:**
- `ValidatorInput` - Input to validator
- `ValidatorVerdict` - Output verdict
- `ValidatorService` - Main service

**Invariants:**
- VAL-001: Validator is stateless (no writes)
- VAL-002: Verdicts include version
- VAL-003: Confidence in [0,1]
- VAL-004: Unknown type defers
- VAL-005: Escalation always escalates

### 6.2 audit_service.py (886 LOC)

**Purpose:** Governance audit (post-execution verification)

**Header:**
- Layer: L8 — Catalyst / Verification
- Product: system-wide

**Governance Rule:** AUDIT-AUTHORITY (Non-Negotiable)

**Key Classes:**
- `AuditCheck` - Individual check result
- `AuditInput` - Frozen evidence input
- `AuditResult` - Complete audit result
- `AuditService` - Main service
- `RolloutGate` - Rollout authorization

**Audit Checks (A-001 to A-007):**
- A-001: Scope Compliance
- A-002: Health Preservation
- A-003: Execution Fidelity
- A-004: Timing Compliance
- A-005: Rollback Availability
- A-006: Signal Consistency
- A-007: No Unauthorized Mutations

**Invariants:**
- AUDIT-001: All completed jobs require audit
- AUDIT-002: PASS required for COMPLETED
- AUDIT-003: FAIL triggers rollback
- AUDIT-004: Verdicts are immutable
- AUDIT-005: Evidence is preserved
- AUDIT-006: Health snapshots required

### 6.3 job_executor.py (521 LOC)

**Purpose:** Execute governance job steps

**Header:**
- Layer: L5 — Execution & Workers
- Product: system-wide

**Governance Rule:** EXECUTOR-AUTHORITY (Non-Negotiable)

**Key Classes:**
- `ExecutionContext` - Execution context
- `ExecutionResult` - Execution result
- `StepOutput` - Step handler output
- `JobExecutor` - Main executor

**Invariants:**
- EXEC-001: Execute steps in declared order
- EXEC-002: Emit evidence per step
- EXEC-003: Stop on first failure
- EXEC-004: Health is observed, never modified
- EXEC-005: No eligibility or contract mutation
- EXEC-006: No retry logic

---

## 7. CLEANUP ACTIONS

### 7.1 COMPLETE: Move iam_service.py ✅

**Action:** Moved `iam_service.py` from `customer/` to `internal/`

**From:** `app/houseofcards/customer/account/engines/iam_service.py`
**To:** `app/houseofcards/internal/platform/iam/engines/iam_service.py`

**Completed Steps:**
1. ✅ Created `internal/platform/iam/` directory structure
2. ✅ Created `internal/platform/iam/__init__.py`
3. ✅ Created `internal/platform/iam/engines/__init__.py` with exports
4. ✅ Moved `iam_service.py`
5. ✅ Updated `customer/account/engines/__init__.py` to document removal
6. ⏳ Callers update pending (phase 5: wire imports)

**New Import Path:**
```python
from app.houseofcards.internal.platform.iam.engines import (
    IAMService,
    Identity,
    AccessDecision,
    IdentityProvider,
    ActorType,
)
```

### 7.2 DEFERRED: Consider Moving identity_resolver.py

**Note:** `identity_resolver.py` imports from `iam_service.py` and may also need to move. Evaluate during import wiring phase.

---

## 8. SUMMARY

| Category | Count | Status |
|----------|-------|--------|
| Total Files | 17 | Analyzed |
| Facades | 2 | CLEAN |
| Engines | 6 | 1 VIOLATION |
| Notifications | 1 | CLEAN |
| CRM/Support | 3 | CLEAN |
| Empty Dirs | 2 | Expected (drivers/, schemas/) |

**Violations:** 1 (iam_service.py AUDIENCE: INTERNAL)

**Recommendation:** Execute cleanup action 7.1 immediately.
