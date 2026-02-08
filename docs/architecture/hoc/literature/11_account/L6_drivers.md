# Account — L6 Drivers (3 files)

**Domain:** account  
**Layer:** L6_drivers  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

---

## accounts_facade_driver.py
**Path:** `backend/app/hoc/cus/account/L6_drivers/accounts_facade_driver.py`  
**Layer:** L6_drivers | **Domain:** account | **Lines:** 954

**Docstring:** Accounts Facade Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `TenantSnapshot` |  | Tenant data from DB for list view. |
| `TenantDetailSnapshot` |  | Detailed tenant data from DB. |
| `UserSnapshot` |  | User data from DB for list view. |
| `UserDetailSnapshot` |  | Detailed user data from DB. |
| `MembershipSnapshot` |  | Tenant membership data from DB. |
| `ProfileSnapshot` |  | User profile data from DB. |
| `SubscriptionSnapshot` |  | Subscription data from DB. |
| `InvitationSnapshot` |  | Invitation data from DB. |
| `TicketSnapshot` |  | Support ticket data from DB. |
| `AccountsFacadeDriver` | fetch_tenant, fetch_tenants, count_tenants, fetch_tenant_detail, fetch_users, count_users, fetch_user_detail, fetch_tenant_memberships (+19 more) | L6 Driver for accounts domain data access. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_accounts_facade_driver` | `() -> AccountsFacadeDriver` | no | Get the singleton AccountsFacadeDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timedelta | no |
| `typing` | TYPE_CHECKING, Any, Optional | no |
| `sqlalchemy` | func, select | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.models.tenant` | Invitation, Subscription, SupportTicket, Tenant, TenantMembership (+3) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`AccountsFacadeDriver`, `get_accounts_facade_driver`, `TenantSnapshot`, `TenantDetailSnapshot`, `UserSnapshot`, `UserDetailSnapshot`, `MembershipSnapshot`, `ProfileSnapshot`, `SubscriptionSnapshot`, `InvitationSnapshot`, `TicketSnapshot`

---

## tenant_driver.py
**Path:** `backend/app/hoc/cus/account/L6_drivers/tenant_driver.py`  
**Layer:** L6_drivers | **Domain:** account | **Lines:** 573

**Docstring:** Tenant Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `TenantCoreSnapshot` |  | Core tenant data for engine operations. |
| `RunCountSnapshot` |  | Running count for quota checks. |
| `APIKeySnapshot` |  | API key data snapshot. |
| `UsageRecordSnapshot` |  | Usage record data. |
| `RunSnapshot` |  | Worker run snapshot. |
| `TenantDriver` | __init__, fetch_tenant_by_id, fetch_tenant_by_slug, fetch_tenant_snapshot, insert_tenant, update_tenant_plan, update_tenant_status, update_tenant_usage (+15 more) | L6 Driver for tenant data access. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_tenant_driver` | `(session: Session) -> TenantDriver` | no | Get a TenantDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `json` | json | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timedelta, timezone | no |
| `typing` | Any, List, Optional, cast | no |
| `sqlmodel` | Session, func, select | no |
| `app.models.tenant` | APIKey, AuditLog, Tenant, TenantMembership, UsageRecord (+2) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`TenantDriver`, `get_tenant_driver`, `TenantCoreSnapshot`, `RunCountSnapshot`, `APIKeySnapshot`, `UsageRecordSnapshot`, `RunSnapshot`

---

## user_write_driver.py
**Path:** `backend/app/hoc/cus/account/L6_drivers/user_write_driver.py`  
**Layer:** L6_drivers | **Domain:** account | **Lines:** 137

**Docstring:** User Write Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `UserWriteDriver` | __init__, create_user, update_user_login, user_to_dict | L6 driver for user write operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_user_write_driver` | `(session: Session) -> UserWriteDriver` | no | Factory function to get UserWriteDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timezone | no |
| `typing` | Dict, Optional | no |
| `sqlmodel` | Session | no |
| `app.models.tenant` | User | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`UserWriteDriver`, `get_user_write_driver`

---
