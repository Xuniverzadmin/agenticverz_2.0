# Controls — L5 Engines (9 files)

**Domain:** controls  
**Layer:** L5_engines  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

---

## alert_fatigue.py
**Path:** `backend/app/hoc/cus/controls/L5_engines/alert_fatigue.py`  
**Layer:** L5_engines | **Domain:** controls | **Lines:** 535

**Docstring:** Alert Fatigue Controller

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AlertSuppressReason` |  | Reason why an alert was suppressed. |
| `AlertRecord` | __post_init__, age | Record of a sent alert for deduplication tracking. |
| `TenantFatigueSettings` | get_domain_cooldown | Per-tenant fatigue settings. |
| `AlertCheckResult` | to_dict | Result of checking whether an alert should be sent. |
| `AlertFatigueController` | __init__, check_alert, should_send_alert, record_alert_sent, set_tenant_settings, get_tenant_stats, _get_tenant_settings, _check_deduplication (+3 more) | Controls alert deduplication and fatigue. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_alert_fatigue_controller` | `(redis_client = None) -> AlertFatigueController` | no | Get or create AlertFatigueController singleton. |
| `reset_alert_fatigue_controller` | `() -> None` | no | Reset the singleton (for testing). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `logging` | logging | no |
| `os` | os | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timedelta, timezone | no |
| `enum` | Enum | no |
| `threading` | Lock | no |
| `typing` | Any, Dict, FrozenSet, List, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`ALERT_FATIGUE_ENABLED`, `DEFAULT_DOMAIN_COOLDOWNS`, `DEDUP_WINDOW_SECONDS`, `MAX_ALERTS_PER_TENANT_PER_HOUR`, `REDIS_KEY_PREFIX`, `REDIS_TTL_SECONDS`

---

## budget_enforcement_engine.py
**Path:** `backend/app/hoc/cus/controls/L5_engines/budget_enforcement_engine.py`  
**Layer:** L5_engines | **Domain:** controls | **Lines:** 341

**Docstring:** Domain engine for budget enforcement decisions.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `BudgetEnforcementEngine` | __init__, emit_decision_for_halt, process_pending_halts, _parse_budget_from_error | L4 Domain Engine for budget enforcement decisions. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `emit_budget_halt_decision` | `(run_id: str, budget_limit_cents: int, budget_consumed_cents: int, step_cost_cen` | no | Convenience function to emit a budget enforcement decision. |
| `process_pending_budget_decisions` | `() -> int` | yes | Process all pending budget halt decisions. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `typing` | Optional | no |
| `app.contracts.decisions` | emit_budget_enforcement_decision | no |
| `app.hoc.cus.controls.L6_drivers.budget_enforcement_driver` | BudgetEnforcementDriver, get_budget_enforcement_driver | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### __all__ Exports
`BudgetEnforcementEngine`, `emit_budget_halt_decision`, `process_pending_budget_decisions`

---

## cb_sync_wrapper.py
**Path:** `backend/app/hoc/cus/controls/L5_engines/cb_sync_wrapper.py`  
**Layer:** L5_engines | **Domain:** controls | **Lines:** 169

**Docstring:** Thread-safe sync wrapper for async circuit breaker functions.

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_get_executor` | `() -> concurrent.futures.ThreadPoolExecutor` | no | Get or create the shared thread pool executor. |
| `_run_async_in_thread` | `(coro, timeout: float = 5.0)` | no | Run an async coroutine in a separate thread with its own event loop. |
| `is_v2_disabled_sync` | `(timeout: float = 5.0) -> bool` | no | Sync wrapper for is_v2_disabled(). |
| `get_state_sync` | `(timeout: float = 5.0)` | no | Sync wrapper for get_state(). |
| `shutdown_executor` | `()` | no | Shutdown the thread pool executor gracefully. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `asyncio` | asyncio | no |
| `concurrent.futures` | concurrent.futures | no |
| `logging` | logging | no |
| `typing` | Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## controls_facade.py
**Path:** `backend/app/hoc/cus/controls/L5_engines/controls_facade.py`  
**Layer:** L5_engines | **Domain:** controls | **Lines:** 438

**Docstring:** Controls Facade (L4 Domain Logic)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ControlType` |  | Types of controls. |
| `ControlState` |  | Control state. |
| `ControlConfig` | to_dict | Control configuration. |
| `ControlStatusSummary` | to_dict | Overall control status summary. |
| `ControlsFacade` | __init__, _ensure_default_controls, list_controls, get_control, update_control, enable_control, disable_control, get_status | Facade for control operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_controls_facade` | `() -> ControlsFacade` | no | Get the controls facade instance. |

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

## cost_safety_rails.py
**Path:** `backend/app/hoc/cus/controls/L5_engines/cost_safety_rails.py`  
**Layer:** L5_engines | **Domain:** controls | **Lines:** 402

**Docstring:** M27 Cost Safety Rails

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SafetyConfig` | production, testing | M27 Safety Configuration. |
| `CostSafetyRails` | __init__, can_auto_apply_policy, can_auto_apply_recovery, can_auto_apply_routing, record_action, _get_action_count, get_status | Enforces M27 safety limits. |
| `SafeCostLoopOrchestrator` | __init__, process_anomaly_safe | Wraps CostLoopOrchestrator with safety rails. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_safety_rails` | `(config: SafetyConfig | None = None) -> CostSafetyRails` | no | Get or create default safety rails instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## decisions.py
**Path:** `backend/app/hoc/cus/controls/L5_engines/decisions.py`  
**Layer:** L5_engines | **Domain:** controls | **Lines:** 221

**Docstring:** Phase-7 Abuse Protection — Decision Types

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `Decision` | blocks_request, is_warning_only | Phase-7 Protection Decisions (Finite, Locked). |
| `ProtectionResult` | to_error_response | Result of a protection check. |
| `AnomalySignal` | to_signal_response | Anomaly detection signal (non-blocking per ABUSE-003). |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `allow` | `() -> ProtectionResult` | no | Create an ALLOW result. |
| `reject_rate_limit` | `(dimension: str, retry_after_ms: int, message: Optional[str] = None) -> Protecti` | no | Create a REJECT result for rate limiting. |
| `reject_cost_limit` | `(current_value: float, allowed_value: float, message: Optional[str] = None) -> P` | no | Create a REJECT result for cost limit. |
| `throttle` | `(dimension: str, retry_after_ms: int, message: Optional[str] = None) -> Protecti` | no | Create a THROTTLE result. |
| `warn` | `(dimension: str, message: Optional[str] = None) -> ProtectionResult` | no | Create a WARN result (non-blocking). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `enum` | Enum | no |
| `typing` | Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### __all__ Exports
`Decision`, `ProtectionResult`, `AnomalySignal`, `allow`, `reject_rate_limit`, `reject_cost_limit`, `throttle`, `warn`

---

## killswitch.py
**Path:** `backend/app/hoc/cus/controls/L5_engines/killswitch.py`  
**Layer:** L5_engines | **Domain:** controls | **Lines:** 262

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `KillSwitchState` |  | Global kill-switch state. Exactly two values. No partial states. |
| `KillSwitchTrigger` |  | What triggered the kill-switch. |
| `RollbackStatus` |  | Status of rollback operation. |
| `KillSwitchEvent` |  | Immutable audit record for kill-switch events. |
| `KillSwitch` | __init__, state, is_enabled, is_disabled, activate, mark_rollback_complete, rearm, on_activate (+2 more) | Global, authoritative kill-switch for C3 optimization. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_killswitch` | `() -> KillSwitch` | no | Get the global kill-switch instance. |
| `reset_killswitch_for_testing` | `() -> None` | no | Reset kill-switch state. FOR TESTING ONLY. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `threading` | threading | no |
| `uuid` | uuid | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Callable, List, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## s2_cost_smoothing.py
**Path:** `backend/app/hoc/cus/controls/L5_engines/s2_cost_smoothing.py`  
**Layer:** L5_engines | **Domain:** controls | **Lines:** 220

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `create_s2_envelope` | `(baseline_value: float = 10.0, reference_id: str = 'scheduler_v2') -> Envelope` | no | Create a fresh S2 envelope instance with specified baseline. |
| `validate_s2_envelope` | `(envelope: Envelope) -> None` | no | Validate S2-specific rules (additive to V1-V5). |
| `calculate_s2_bounded_value` | `(baseline: float, max_decrease_pct: float, prediction_confidence: float) -> floa` | no | Calculate the bounded value for S2 (decrease only). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.optimization.envelope` | BaselineSource, DeltaType, Envelope, EnvelopeBaseline, EnvelopeBounds (+6) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`S2_COST_SMOOTHING_ENVELOPE`, `S2_ABSOLUTE_FLOOR`

---

## threshold_engine.py
**Path:** `backend/app/hoc/cus/controls/L5_engines/threshold_engine.py`  
**Layer:** L5_engines | **Domain:** controls | **Lines:** 708

**Docstring:** Threshold Decision Engine (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ThresholdParams` | coerce_decimal_to_float | Validated threshold parameters for LLM run governance. |
| `ThresholdParamsUpdate` |  | Partial update for threshold params. |
| `ThresholdSignal` |  | Signals emitted when runs breach thresholds. |
| `ThresholdEvaluationResult` |  | Result of threshold evaluation. |
| `ThresholdDriverProtocol` | get_active_threshold_limits | Protocol defining the interface for threshold drivers. |
| `ThresholdDriverSyncProtocol` | get_active_threshold_limits | Protocol defining the interface for sync threshold drivers. |
| `LLMRunThresholdResolver` | __init__, resolve | Resolves effective threshold params for an LLM run |
| `LLMRunEvaluator` | __init__, evaluate_live_run, evaluate_completed_run | Evaluates LLM runs against threshold params. |
| `LLMRunThresholdResolverSync` | __init__, resolve | Sync version of LLMRunThresholdResolver for worker context. |
| `LLMRunEvaluatorSync` | __init__, evaluate_completed_run | Sync version of LLMRunEvaluator for worker context. |
| `ThresholdSignalRecord` |  | Record of a threshold signal for activity domain. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `create_threshold_signal_record` | `(tenant_id: str, run_id: str, state: str, signal: ThresholdSignal, params_used: ` | no | Create a threshold signal record for activity domain. |
| `collect_signals_from_evaluation` | `(evaluation: ThresholdEvaluationResult, tenant_id: str, state: str) -> list[Thre` | no | Collect all signals from an evaluation result into records. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `decimal` | Decimal | no |
| `enum` | Enum | no |
| `typing` | TYPE_CHECKING, Optional, Protocol | no |
| `pydantic` | BaseModel, Field, field_validator | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`DEFAULT_LLM_RUN_PARAMS`

---
