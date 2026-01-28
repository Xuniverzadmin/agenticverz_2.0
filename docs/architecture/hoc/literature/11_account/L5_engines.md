# Account — L5 Engines (8 files)

**Domain:** account  
**Layer:** L5_engines  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

---

## accounts_facade.py
**Path:** `backend/app/hoc/cus/account/L5_engines/accounts_facade.py`  
**Layer:** L5_engines | **Domain:** account | **Lines:** 1140

**Docstring:** Accounts Domain Facade (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ProjectSummaryResult` |  | Project summary for list view. |
| `ProjectsListResult` |  | Projects list response. |
| `ProjectDetailResult` |  | Project detail response. |
| `UserSummaryResult` |  | User summary for list view. |
| `UsersListResult` |  | Users list response. |
| `UserDetailResult` |  | User detail response. |
| `TenantUserResult` |  | User in tenant. |
| `TenantUsersListResult` |  | List of tenant users. |
| `ProfileResult` |  | User profile response. |
| `ProfileUpdateResult` |  | Profile update response. |
| `BillingSummaryResult` |  | Billing summary response. |
| `InvoiceSummaryResult` |  | Invoice summary. |
| `InvoiceListResult` |  | Invoice list response. |
| `SupportContactResult` |  | Support contact info. |
| `SupportTicketResult` |  | Support ticket response. |
| `SupportTicketListResult` |  | Support ticket list response. |
| `InvitationResult` |  | Invitation response. |
| `InvitationListResult` |  | Invitation list response. |
| `AcceptInvitationResult` |  | Invitation acceptance result. |
| `AccountsErrorResult` |  | Error result for accounts operations. |
| `AccountsFacade` | __init__, list_projects, get_project_detail, list_users, get_user_detail, list_tenant_users, update_user_role, remove_user (+10 more) | Unified facade for all Accounts domain operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_accounts_facade` | `() -> AccountsFacade` | no | Get the singleton AccountsFacade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `hashlib` | hashlib | no |
| `secrets` | secrets | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timedelta, timezone | no |
| `typing` | TYPE_CHECKING, Any, Optional | no |
| `app.hoc.cus.account.L6_drivers.accounts_facade_driver` | AccountsFacadeDriver, get_accounts_facade_driver | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### __all__ Exports
`AccountsFacade`, `get_accounts_facade`, `ProjectSummaryResult`, `ProjectsListResult`, `ProjectDetailResult`, `UserSummaryResult`, `UsersListResult`, `UserDetailResult`, `TenantUserResult`, `TenantUsersListResult`, `ProfileResult`, `ProfileUpdateResult`, `BillingSummaryResult`, `InvoiceSummaryResult`, `InvoiceListResult`, `SupportContactResult`, `SupportTicketResult`, `SupportTicketListResult`, `InvitationResult`, `InvitationListResult`, `AcceptInvitationResult`, `AccountsErrorResult`

---

## billing_provider.py
**Path:** `backend/app/hoc/cus/account/L5_engines/billing_provider.py`  
**Layer:** L5_engines | **Domain:** account | **Lines:** 251

**Docstring:** Phase-6 Billing Provider — Interface and Mock Implementation

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `BillingProvider` | get_billing_state, get_plan, get_limits, is_limit_exceeded | Phase-6 Billing Provider Protocol. |
| `MockBillingProvider` | __init__, get_billing_state, get_plan, get_limits, is_limit_exceeded, set_billing_state, set_plan, reset | Phase-6 Mock Billing Provider. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_billing_provider` | `() -> BillingProvider` | no | Get the billing provider instance. |
| `set_billing_provider` | `(provider: BillingProvider) -> None` | no | Set the billing provider instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Protocol, Optional | no |
| `logging` | logging | no |
| `app.billing.state` | BillingState | no |
| `app.billing.plan` | Plan, DEFAULT_PLAN, PLAN_FREE, PLAN_PRO, PLAN_ENTERPRISE | no |
| `app.billing.limits` | Limits, derive_limits | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### __all__ Exports
`BillingProvider`, `MockBillingProvider`, `get_billing_provider`, `set_billing_provider`

---

## email_verification.py
**Path:** `backend/app/hoc/cus/account/L5_engines/email_verification.py`  
**Layer:** L5_engines | **Domain:** account | **Lines:** 302

**Docstring:** Email Verification Service

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `VerificationResult` |  | Result of OTP verification. |
| `EmailVerificationError` | __init__ | Email verification error. |
| `EmailVerificationService` | __init__, _otp_key, _attempts_key, _cooldown_key, _generate_otp, send_otp, _send_otp_email, verify_otp | Handles OTP generation, sending, and verification for email signup. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_email_verification_service` | `() -> EmailVerificationService` | no | Get email verification service singleton. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `logging` | logging | no |
| `os` | os | no |
| `secrets` | secrets | no |
| `dataclasses` | dataclass | no |
| `typing` | Optional | no |
| `httpx` | httpx | no |
| `redis` | Redis | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`RESEND_API_KEY`, `EMAIL_FROM`, `EMAIL_VERIFICATION_TTL`, `REDIS_URL`, `OTP_LENGTH`, `MAX_OTP_ATTEMPTS`, `OTP_COOLDOWN_SECONDS`

---

## identity_resolver.py
**Path:** `backend/app/hoc/cus/account/L5_engines/identity_resolver.py`  
**Layer:** L5_engines | **Domain:** account | **Lines:** 207

**Docstring:** Identity Resolver (GAP-173)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IdentityResolver` | resolve, provider | Abstract identity resolver. |
| `ClerkIdentityResolver` | __init__, provider, resolve | Resolver for Clerk JWT tokens. |
| `APIKeyIdentityResolver` | provider, resolve | Resolver for API keys. |
| `SystemIdentityResolver` | provider, resolve | Resolver for internal system identities. |
| `IdentityChain` | resolve | Chain of identity resolvers. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `create_default_identity_chain` | `() -> IdentityChain` | no | Create the default identity resolver chain. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `abc` | ABC, abstractmethod | no |
| `dataclasses` | dataclass | no |
| `typing` | Optional | no |
| `app.hoc.int.platform.iam.engines.iam_service` | ActorType, Identity, IdentityProvider | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## notifications_facade.py
**Path:** `backend/app/hoc/cus/account/L5_engines/notifications_facade.py`  
**Layer:** L5_engines | **Domain:** account | **Lines:** 480

**Docstring:** Notifications Facade (L5 Domain Engine)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `NotificationChannel` |  | Notification channels. |
| `NotificationPriority` |  | Notification priorities. |
| `NotificationStatus` |  | Notification delivery status. |
| `NotificationInfo` | to_dict | Notification information. |
| `ChannelInfo` | to_dict | Notification channel information. |
| `NotificationPreferences` | to_dict | User notification preferences. |
| `NotificationsFacade` | __init__, send_notification, list_notifications, get_notification, mark_as_read, list_channels, get_channel, get_preferences (+1 more) | Facade for notification operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_notifications_facade` | `() -> NotificationsFacade` | no | Get the notifications facade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | uuid | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## profile.py
**Path:** `backend/app/hoc/cus/account/L5_engines/profile.py`  
**Layer:** L5_engines | **Domain:** account | **Lines:** 459

**Docstring:** Governance Profile Configuration

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `GovernanceProfile` |  | Pre-defined governance profiles. |
| `GovernanceConfig` | to_dict | Complete governance configuration derived from profile + overrides. |
| `GovernanceConfigError` | __init__ | Raised when governance configuration is invalid. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_get_bool_env` | `(name: str, default: bool) -> bool` | no | Get boolean from environment variable. |
| `get_governance_profile` | `() -> GovernanceProfile` | no | Get the current governance profile from environment. |
| `load_governance_config` | `() -> GovernanceConfig` | no | Load complete governance configuration. |
| `validate_governance_config` | `(config: Optional[GovernanceConfig] = None) -> List[str]` | no | Validate governance configuration for invalid combinations. |
| `get_governance_config` | `() -> GovernanceConfig` | no | Get the validated governance configuration singleton. |
| `reset_governance_config` | `() -> None` | no | Reset the singleton (for testing). |
| `validate_governance_at_startup` | `() -> None` | no | Validate governance configuration at application startup. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `dataclasses` | dataclass | no |
| `enum` | Enum | no |
| `typing` | Dict, FrozenSet, List, Optional, Tuple | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## tenant_engine.py
**Path:** `backend/app/hoc/cus/account/L5_engines/tenant_engine.py`  
**Layer:** L5_engines | **Domain:** account | **Lines:** 582

**Docstring:** Tenant Engine (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `TenantEngineError` |  | Base exception for tenant engine errors. |
| `QuotaExceededError` | __init__ | Raised when a quota limit is exceeded. |
| `TenantEngine` | __init__, create_tenant, get_tenant, get_tenant_by_slug, update_plan, suspend, create_membership_with_default, create_api_key (+11 more) | L4 Engine for tenant business logic. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_tenant_engine` | `(session: Session) -> TenantEngine` | no | Get a TenantEngine instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `datetime` | timedelta | no |
| `typing` | TYPE_CHECKING, Any, List, Optional, Tuple | no |
| `app.hoc.cus.general.L5_utils.time` | utc_now | no |
| `app.hoc.cus.account.L6_drivers.tenant_driver` | TenantDriver, get_tenant_driver | no |
| `app.models.tenant` | PLAN_QUOTAS, APIKey, Tenant, TenantMembership, WorkerRun | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Violations
| Import | Rule Broken | Required Fix | Line |
|--------|-------------|-------------|------|
| `from app.models.tenant import PLAN_QUOTAS, APIKey, Tenant, TenantMembership, WorkerRun` | L5 MUST NOT import L7 models directly | Route through L6 driver | 52 |

### __all__ Exports
`TenantEngine`, `TenantEngineError`, `QuotaExceededError`, `get_tenant_engine`

---

## user_write_engine.py
**Path:** `backend/app/hoc/cus/account/L5_engines/user_write_engine.py`  
**Layer:** L5_engines | **Domain:** account | **Lines:** 91

**Docstring:** User Write Engine (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `UserWriteService` | __init__, create_user, update_user_login, user_to_dict | DB write operations for User management. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | TYPE_CHECKING, Dict, Optional | no |
| `app.hoc.cus.account.L6_drivers.user_write_driver` | UserWriteDriver, get_user_write_driver | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---
