# Controls — L6 Drivers (5 files)

**Domain:** controls  
**Layer:** L6_drivers  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

---

## budget_enforcement_driver.py
**Path:** `backend/app/hoc/cus/controls/L6_drivers/budget_enforcement_driver.py`  
**Layer:** L6_drivers | **Domain:** controls | **Lines:** 124

**Docstring:** Budget Enforcement Driver (L6 Data Access)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `BudgetEnforcementDriver` | __init__, _get_engine, fetch_pending_budget_halts, dispose | L6 Driver for budget enforcement data operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_budget_enforcement_driver` | `(db_url: Optional[str] = None) -> BudgetEnforcementDriver` | no | Get a BudgetEnforcementDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `typing` | Any, Optional | no |
| `sqlalchemy` | create_engine, text | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

---

## limits_read_driver.py
**Path:** `backend/app/hoc/cus/controls/L6_drivers/limits_read_driver.py`  
**Layer:** L6_drivers | **Domain:** controls | **Lines:** 322

**Docstring:** Limits Read Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `LimitsReadDriver` | __init__, fetch_limits, fetch_limit_by_id, fetch_budget_limits, fetch_limit_breaches_for_run | Read operations for limits. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_limits_read_driver` | `(session: AsyncSession) -> LimitsReadDriver` | no | Factory function for LimitsReadDriver. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timedelta, timezone | no |
| `typing` | Any, Optional | no |
| `sqlalchemy` | and_, func, select | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.models.policy_control_plane` | Limit, LimitBreach, LimitIntegrity | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`LimitsReadDriver`, `get_limits_read_driver`

---

## override_driver.py
**Path:** `backend/app/hoc/cus/controls/L6_drivers/override_driver.py`  
**Layer:** L6_drivers | **Domain:** controls | **Lines:** 295

**Docstring:** Limit Override Driver (PIN-LIM-05)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `LimitOverrideService` | __init__, request_override, get_override, list_overrides, cancel_override, _get_limit, _to_response | Driver for limit override lifecycle. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `uuid` | uuid | no |
| `datetime` | datetime, timedelta, timezone | no |
| `decimal` | Decimal | no |
| `typing` | Optional | no |
| `sqlalchemy` | and_, func, select | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.models.policy_control_plane` | Limit, LimitOverride | no |
| `app.hoc.cus.controls.L5_schemas.overrides` | LimitOverrideRequest, LimitOverrideResponse, OverrideStatus | no |
| `app.hoc.cus.controls.L5_schemas.override_types` | LimitOverrideServiceError, LimitNotFoundError, OverrideNotFoundError, OverrideValidationError, StackingAbuseError | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

---

## policy_limits_driver.py
**Path:** `backend/app/hoc/cus/controls/L6_drivers/policy_limits_driver.py`  
**Layer:** L6_drivers | **Domain:** controls | **Lines:** 131

**Docstring:** Policy Limits Driver

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyLimitsDriver` | __init__, fetch_limit_by_id, add_limit, add_integrity, create_limit, create_integrity, flush | Data access driver for policy limits. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_policy_limits_driver` | `(session: AsyncSession) -> PolicyLimitsDriver` | no | Factory function for PolicyLimitsDriver. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | TYPE_CHECKING, Optional | no |
| `sqlalchemy` | select | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

---

## threshold_driver.py
**Path:** `backend/app/hoc/cus/controls/L6_drivers/threshold_driver.py`  
**Layer:** L6_drivers | **Domain:** controls | **Lines:** 332

**Docstring:** Threshold Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `LimitSnapshot` |  | Immutable snapshot of a Limit record returned to engines. |
| `ThresholdDriver` | __init__, get_active_threshold_limits, get_threshold_limit_by_scope | Async database driver for threshold limit operations. |
| `ThresholdDriverSync` | __init__, get_active_threshold_limits | Sync database driver for threshold limit operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `emit_threshold_signal_sync` | `(session: Any, tenant_id: str, run_id: str, state: str, signal: Any, params_used` | no | Emit a threshold signal to ops_events table (sync). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `uuid` | uuid_module | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime | no |
| `typing` | Any, Optional | no |
| `sqlalchemy` | text | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `sqlmodel` | select | no |
| `app.models.policy_control_plane` | Limit, LimitCategory, LimitStatus | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

---
