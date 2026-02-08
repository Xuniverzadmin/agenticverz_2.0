# Account — L5 Engines (7 files)

**Domain:** account  
**Layer:** L5_engines  
**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

**Layer Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

---

## accounts_facade.py
**Path:** `backend/app/hoc/cus/account/L5_engines/accounts_facade.py`  
**Layer:** L5_engines | **Domain:** account | **Lines:** 1135

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
| `app.hoc.cus.account.L5_schemas.result_types` | AccountsErrorResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### __all__ Exports
`AccountsFacade`, `get_accounts_facade`, `ProjectSummaryResult`, `ProjectsListResult`, `ProjectDetailResult`, `UserSummaryResult`, `UsersListResult`, `UserDetailResult`, `TenantUserResult`, `TenantUsersListResult`, `ProfileResult`, `ProfileUpdateResult`, `BillingSummaryResult`, `InvoiceSummaryResult`, `InvoiceListResult`, `SupportContactResult`, `SupportTicketResult`, `SupportTicketListResult`, `InvitationResult`, `InvitationListResult`, `AcceptInvitationResult`, `AccountsErrorResult`

---

## billing_provider_engine.py
**Path:** `backend/app/hoc/cus/account/L5_engines/billing_provider_engine.py`  
**Layer:** L5_engines | **Domain:** account | **Lines:** 252

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### __all__ Exports
`BillingProvider`, `MockBillingProvider`, `get_billing_provider`, `set_billing_provider`

---

## memory_pins_engine.py
**Path:** `backend/app/hoc/cus/account/L5_engines/memory_pins_engine.py`  
**Layer:** L5_engines | **Domain:** account | **Lines:** 321

**Docstring:** Memory Pins Engine (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `MemoryPinsDisabledError` |  | Raised when memory pins feature is disabled. |
| `MemoryPinResult` |  | Result of a memory pin operation. |
| `MemoryPinsDriverPort` | upsert_pin, get_pin, list_pins, delete_pin, cleanup_expired, write_audit | Port for L6 driver methods used by MemoryPinsEngine. |
| `MemoryPinsEngine` | _check_enabled, upsert_pin, get_pin, list_pins, delete_pin, cleanup_expired | Business logic for memory pin operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_memory_pins_engine` | `() -> MemoryPinsEngine` | no | Get or create the singleton MemoryPinsEngine. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `hashlib` | hashlib | no |
| `logging` | logging | no |
| `os` | os | no |
| `time` | time | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any, Dict, List, Optional, Protocol | no |
| `app.hoc.cus.account.L6_drivers.memory_pins_driver` | MemoryPinRow | no |
| `app.utils.metrics_helpers` | get_or_create_counter, get_or_create_histogram | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### Constants
`MEMORY_PINS_ENABLED`, `MEMORY_PINS_OPERATIONS`, `MEMORY_PINS_LATENCY`

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

---

## onboarding_engine.py
**Path:** `backend/app/hoc/cus/account/L5_engines/onboarding_engine.py`  
**Layer:** L5_engines | **Domain:** account | **Lines:** 144

**Docstring:** Onboarding Engine (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `OnboardingEngine` | __init__, get_state, advance | L5 Engine for onboarding state transitions. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_onboarding_engine` | `(driver) -> OnboardingEngine` | no | Get an OnboardingEngine instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `typing` | Optional | no |
| `app.hoc.cus.account.L5_schemas.onboarding_state` | ONBOARDING_STATUS_NAMES, is_complete | no |
| `app.hoc.cus.account.L5_schemas.onboarding_dtos` | OnboardingStateSnapshot, OnboardingTransitionResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### __all__ Exports
`OnboardingEngine`, `get_onboarding_engine`

---

## tenant_engine.py
**Path:** `backend/app/hoc/cus/account/L5_engines/tenant_engine.py`  
**Layer:** L5_engines | **Domain:** account | **Lines:** 583

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
| `app.hoc.cus.hoc_spine.services.time` | utc_now | no |
| `app.hoc.cus.account.L6_drivers.tenant_driver` | TenantDriver, get_tenant_driver | no |
| `app.hoc.cus.account.L5_schemas.plan_quotas` | PLAN_QUOTAS | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### __all__ Exports
`TenantEngine`, `TenantEngineError`, `QuotaExceededError`, `get_tenant_engine`

---

## tenant_lifecycle_engine.py
**Path:** `backend/app/hoc/cus/account/L5_engines/tenant_lifecycle_engine.py`  
**Layer:** L5_engines | **Domain:** account | **Lines:** 195

**Docstring:** Tenant Lifecycle Engine (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `TenantLifecycleEngine` | __init__, get_state, transition, suspend, resume, terminate, archive | L5 Engine for tenant lifecycle business logic. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_action_name` | `(to_status: TenantLifecycleStatus) -> str` | no | Map target status to action name. |
| `get_tenant_lifecycle_engine` | `(driver) -> TenantLifecycleEngine` | no | Get a TenantLifecycleEngine instance with injected driver. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `typing` | Optional | no |
| `app.hoc.cus.account.L5_schemas.tenant_lifecycle_enums` | TenantLifecycleStatus, VALID_TRANSITIONS, normalize_status, is_valid_transition, allows_sdk_execution (+5) | no |
| `app.hoc.cus.account.L5_schemas.lifecycle_dtos` | LifecycleActorContext, LifecycleTransitionResult, LifecycleStateSnapshot | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### __all__ Exports
`TenantLifecycleEngine`, `get_tenant_lifecycle_engine`

---
