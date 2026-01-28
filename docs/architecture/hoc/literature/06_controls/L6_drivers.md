# Controls — L6 Drivers (8 files)

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

## circuit_breaker.py
**Path:** `backend/app/hoc/cus/controls/L6_drivers/circuit_breaker.py`  
**Layer:** L6_drivers | **Domain:** controls | **Lines:** 983

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CircuitBreakerState` | to_dict | Current state of the circuit breaker (in-memory representation). |
| `Incident` | to_dict | Incident record for circuit breaker trip. |
| `CircuitBreaker` | __init__, _get_or_create_state, is_disabled, _auto_recover, is_open, is_closed, get_state, report_drift (+11 more) | DB-backed circuit breaker for CostSim V2 auto-disable. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `create_circuit_breaker` | `(session: Session, failure_threshold: Optional[int] = None, drift_threshold: Opt` | no | Create CircuitBreaker with required session. |
| `is_v2_disabled` | `(session: Session) -> bool` | yes | Check if CostSim V2 is disabled. |
| `disable_v2` | `(session: Session, reason: str, disabled_by: str, disabled_until: Optional[datet` | yes | Disable CostSim V2. |
| `enable_v2` | `(session: Session, enabled_by: str, reason: Optional[str] = None) -> bool` | yes | Enable CostSim V2. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `app.infra` | FeatureIntent, RetryPolicy | no |
| `asyncio` | asyncio | no |
| `json` | json | no |
| `logging` | logging | no |
| `uuid` | uuid | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timedelta, timezone | no |
| `pathlib` | Path | no |
| `typing` | Any, Dict, List, Optional, Tuple (+1) | no |
| `httpx` | httpx | no |
| `sqlmodel` | Session, select | no |
| `app.costsim.config` | get_config | no |
| `app.db` | CostSimCBIncident, CostSimCBState, log_status_change | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### Constants
`FEATURE_INTENT`, `RETRY_POLICY`, `CB_NAME`

---

## circuit_breaker_async.py
**Path:** `backend/app/hoc/cus/controls/L6_drivers/circuit_breaker_async.py`  
**Layer:** L6_drivers | **Domain:** controls | **Lines:** 999

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CircuitBreakerState` | to_dict | Current state of the circuit breaker. |
| `Incident` | to_dict | Incident record for circuit breaker trip. |
| `AsyncCircuitBreaker` | __init__, is_disabled, is_open, is_closed, get_state, report_drift, report_schema_error, disable_v2 (+4 more) | Async circuit breaker class for compatibility with existing code. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_get_or_create_state` | `(session: AsyncSession, lock: bool = False) -> CostSimCBStateModel` | yes | Get or create circuit breaker state row. |
| `is_v2_disabled` | `(session: Optional[AsyncSession] = None) -> bool` | yes | Check if V2 is disabled. |
| `_try_auto_recover` | `(state_id: int) -> bool` | yes | Attempt auto-recovery with proper locking to avoid TOCTOU race. |
| `_auto_recover` | `(session: AsyncSession, state: CostSimCBStateModel) -> None` | yes | Legacy auto-recover function (deprecated). |
| `get_state` | `() -> CircuitBreakerState` | yes | Get current circuit breaker state. |
| `report_drift` | `(drift_score: float, sample_count: int = 1, details: Optional[Dict[str, Any]] = ` | yes | Report drift observation. |
| `report_schema_error` | `(error_count: int = 1, details: Optional[Dict[str, Any]] = None) -> Optional[Inc` | yes | Report schema validation errors. |
| `disable_v2` | `(reason: str, disabled_by: str, disabled_until: Optional[datetime] = None) -> Tu` | yes | Manually disable CostSim V2. |
| `enable_v2` | `(enabled_by: str, reason: Optional[str] = None) -> bool` | yes | Manually enable CostSim V2. |
| `_trip` | `(session: AsyncSession, state: CostSimCBStateModel, reason: str, drift_score: fl` | yes | Trip the circuit breaker. |
| `_resolve_incident` | `(session: AsyncSession, incident_id: str, resolved_by: str, resolution_notes: st` | yes | Resolve an incident. |
| `get_incidents` | `(include_resolved: bool = False, limit: int = 10) -> List[Incident]` | yes | Get recent incidents. |
| `_enqueue_alert` | `(session: AsyncSession, alert_type: str, payload: List[Dict[str, Any]], incident` | yes | Enqueue alert for reliable delivery. |
| `_build_disable_alert_payload` | `(incident: Incident, disabled_until: Optional[datetime]) -> List[Dict[str, Any]]` | no | Build Alertmanager payload for disable alert. |
| `_build_enable_alert_payload` | `(enabled_by: str, reason: Optional[str] = None) -> List[Dict[str, Any]]` | no | Build Alertmanager payload for enable/resolved alert. |
| `get_async_circuit_breaker` | `() -> AsyncCircuitBreaker` | no | Get the global async circuit breaker instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `app.infra` | FeatureIntent, RetryPolicy | no |
| `json` | json | no |
| `logging` | logging | no |
| `uuid` | uuid | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timedelta, timezone | no |
| `typing` | Any, Dict, List, Optional, Tuple | no |
| `sqlalchemy` | select | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.costsim.config` | get_config | no |
| `app.costsim.metrics` | get_metrics | no |
| `app.db_async` | AsyncSessionLocal, async_session_context | no |
| `app.models.costsim_cb` | CostSimAlertQueueModel, CostSimCBIncidentModel, CostSimCBStateModel | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### Constants
`FEATURE_INTENT`, `RETRY_POLICY`, `CB_NAME`

---

## limits_read_driver.py
**Path:** `backend/app/hoc/cus/controls/L6_drivers/limits_read_driver.py`  
**Layer:** L6_drivers | **Domain:** controls | **Lines:** 281

**Docstring:** Limits Read Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `LimitsReadDriver` | __init__, fetch_limits, fetch_limit_by_id, fetch_budget_limits | Read operations for limits. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_limits_read_driver` | `(session: AsyncSession) -> LimitsReadDriver` | no | Factory function for LimitsReadDriver. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timedelta | no |
| `typing` | Any, Optional | no |
| `sqlalchemy` | and_, func, select | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.hoc.cus.general.L5_utils.time` | utc_now | no |
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
**Layer:** L6_drivers | **Domain:** controls | **Lines:** 266

**Docstring:** Limit Override Service (PIN-LIM-05)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `LimitOverrideServiceError` |  | Base exception for override service. |
| `LimitNotFoundError` |  | Raised when limit is not found. |
| `OverrideNotFoundError` |  | Raised when override is not found. |
| `OverrideValidationError` |  | Raised when override validation fails. |
| `StackingAbuseError` |  | Raised when too many overrides are active. |
| `LimitOverrideService` | __init__, request_override, get_override, list_overrides, cancel_override, _get_limit, _to_response | Service for limit override lifecycle. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `uuid` | uuid | no |
| `datetime` | datetime, timedelta, timezone | no |
| `decimal` | Decimal | no |
| `typing` | Optional | no |
| `sqlalchemy` | and_, select | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.models.policy_control_plane` | Limit | no |
| `app.hoc.cus.general.L5_utils.time` | utc_now | no |
| `app.hoc.cus.general.L6_drivers.cross_domain` | generate_uuid | no |
| `app.hoc.cus.controls.L5_schemas.overrides` | LimitOverrideRequest, LimitOverrideResponse, OverrideStatus | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

---

## policy_limits_driver.py
**Path:** `backend/app/hoc/cus/controls/L6_drivers/policy_limits_driver.py`  
**Layer:** L6_drivers | **Domain:** controls | **Lines:** 117

**Docstring:** Policy Limits Driver

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyLimitsDriver` | __init__, fetch_limit_by_id, add_limit, add_integrity, flush | Data access driver for policy limits. |

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

## scoped_execution.py
**Path:** `backend/app/hoc/cus/controls/L6_drivers/scoped_execution.py`  
**Layer:** L6_drivers | **Domain:** controls | **Lines:** 696

**Docstring:** M6: Scoped Execution Context Service (P2FC-4)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `RiskClass` |  | Risk classification for recovery actions. |
| `ExecutionScope` |  | Type of scoped execution. |
| `ScopedExecutionResult` |  | Result of a scoped execution test. |
| `RecoveryAction` |  | A recovery action to be tested in scoped execution. |
| `ScopedExecutionContext` | __init__, execute, _dry_run_validate, _execute_scoped, _estimate_cost, _elapsed_ms, _compute_hash | M6 Scoped Execution primitive. |
| `ScopedExecutionRequired` |  | Raised when a MEDIUM+ risk action is attempted without scoped pre-execution. |
| `ScopeNotFound` |  | Raised when a scope ID does not exist. |
| `ScopeExhausted` |  | Raised when a scope has been fully consumed. |
| `ScopeExpired` |  | Raised when a scope has expired. |
| `ScopeActionMismatch` |  | Raised when action does not match scope's allowed actions. |
| `ScopeIncidentMismatch` |  | Raised when execution targets a different incident than scope. |
| `BoundExecutionScope` | is_valid, can_execute, consume, to_dict | A bound execution scope that gates recovery actions. |
| `ScopeStore` | __new__, create_scope, get_scope, get_scopes_for_incident, revoke_scope, cleanup_expired | Thread-safe in-memory store for execution scopes. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_scope_store` | `() -> ScopeStore` | no | Get the global scope store. |
| `create_recovery_scope` | `(incident_id: str, action: str, intent: str = '', max_cost_usd: float = 0.5, max` | yes | Create a bound execution scope for recovery action. |
| `execute_with_scope` | `(scope_id: str, action: str, incident_id: str, parameters: Optional[Dict[str, An` | yes | Execute a recovery action within a valid scope. |
| `validate_scope_required` | `(incident_id: str, action: str) -> None` | yes | Validate that execution without scope should fail. |
| `requires_scoped_execution` | `(risk_threshold: RiskClass = RiskClass.MEDIUM)` | no | Decorator to enforce scoped pre-execution for risky recovery actions. |
| `test_recovery_scope` | `(action_id: str, action_name: str, action_type: str, risk_class: str, parameters` | yes | Test a recovery action in scoped execution. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `hashlib` | hashlib | no |
| `logging` | logging | no |
| `secrets` | secrets | no |
| `threading` | threading | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timedelta, timezone | no |
| `enum` | Enum | no |
| `functools` | wraps | no |
| `typing` | Any, Dict, List, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

---

## threshold_driver.py
**Path:** `backend/app/hoc/cus/controls/L6_drivers/threshold_driver.py`  
**Layer:** L6_drivers | **Domain:** controls | **Lines:** 380

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
| `emit_and_persist_threshold_signal` | `(session: Any, tenant_id: str, run_id: str, state: str, signals: list, params_us` | no | Emit threshold signals to both Founder and Customer consoles. |

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
