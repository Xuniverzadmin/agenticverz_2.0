# Account — L5 Engines (3 files)

**Domain:** account  
**Layer:** L5_engines  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### __all__ Exports
`AccountsFacade`, `get_accounts_facade`, `ProjectSummaryResult`, `ProjectsListResult`, `ProjectDetailResult`, `UserSummaryResult`, `UsersListResult`, `UserDetailResult`, `TenantUserResult`, `TenantUsersListResult`, `ProfileResult`, `ProfileUpdateResult`, `BillingSummaryResult`, `InvoiceSummaryResult`, `InvoiceListResult`, `SupportContactResult`, `SupportTicketResult`, `SupportTicketListResult`, `InvitationResult`, `InvitationListResult`, `AcceptInvitationResult`, `AccountsErrorResult`

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### __all__ Exports
`TenantEngine`, `TenantEngineError`, `QuotaExceededError`, `get_tenant_engine`

---
