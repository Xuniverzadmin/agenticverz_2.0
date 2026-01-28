# General — L6 Drivers (13 files)

**Domain:** general  
**Layer:** L6_drivers  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

---

## alert_driver.py
**Path:** `backend/app/hoc/cus/general/L6_drivers/alert_driver.py`  
**Layer:** L6_drivers | **Domain:** general | **Lines:** 342

**Docstring:** Alert Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AlertDriver` | __init__, fetch_pending_alerts, fetch_queue_stats, update_alert_sent, update_alert_retry, update_alert_failed, mark_incident_alert_sent, insert_alert (+2 more) | L6 driver for alert queue data access. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_alert_driver` | `(session: AsyncSession) -> AlertDriver` | no | Factory function to get AlertDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timezone | no |
| `typing` | Any, Dict, List, Optional | no |
| `sqlalchemy` | and_, delete, func, select, update | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.models.costsim_cb` | CostSimAlertQueueModel, CostSimCBIncidentModel | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`AlertDriver`, `get_alert_driver`

---

## alert_emitter.py
**Path:** `backend/app/hoc/cus/general/L6_drivers/alert_emitter.py`  
**Layer:** L6_drivers | **Domain:** general | **Lines:** 422

**Docstring:** Alert Emitter Service

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AlertEmitter` | __init__, emit_near_threshold, emit_breach, _send_via_channel, _send_ui_notification, _send_webhook, _send_slack, _send_email (+2 more) | Emits alerts for threshold events. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_alert_emitter` | `() -> AlertEmitter` | no | Get or create AlertEmitter singleton. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `json` | json | no |
| `logging` | logging | no |
| `datetime` | datetime, timezone | no |
| `typing` | Optional | no |
| `httpx` | httpx | no |
| `sqlmodel` | Session, select | no |
| `app.db` | engine | no |
| `app.models.alert_config` | AlertChannel, AlertConfig | no |
| `app.models.threshold_signal` | SignalType, ThresholdSignal | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

---

## budget_tracker.py
**Path:** `backend/app/hoc/cus/general/L6_drivers/budget_tracker.py`  
**Layer:** L6_drivers | **Domain:** general | **Lines:** 531

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `BudgetStatus` |  | Current budget status for an agent. |
| `BudgetCheckResult` |  | Result of a budget enforcement check. |
| `BudgetTracker` | __init__, get_status, _get_today_spent, check_budget, enforce_budget, _pause_agent, deduct, record_cost | Tracks and enforces LLM cost budgets. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_budget_tracker` | `() -> BudgetTracker` | no | Get the singleton budget tracker. |
| `check_budget` | `(agent_id: str, estimated_cost_cents: int) -> tuple[bool, Optional[str]]` | no | Convenience function to check budget. |
| `deduct_budget` | `(agent_id: str, cost_cents: int, tenant_id: Optional[str] = None) -> bool` | no | Convenience function to deduct budget. |
| `record_cost` | `(run_id: str, agent_id: str, provider: str, model: str, input_tokens: int, outpu` | no | Convenience function to record cost. |
| `enforce_budget` | `(agent_id: str, estimated_cost_cents: int, model: Optional[str] = None, run_id: ` | no | Full budget enforcement with all protection layers. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `uuid` | uuid | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `typing` | Dict, Optional | no |
| `sqlmodel` | Session, text | no |
| `db` | Agent, engine | yes |
| `app.contracts.decisions` | emit_budget_decision | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### Constants
`BUDGET_ALERT_THRESHOLD`, `PER_RUN_MAX_CENTS`, `PER_DAY_MAX_CENTS`, `AUTO_PAUSE_ON_BREACH`

---

## cross_domain.py
**Path:** `backend/app/hoc/cus/general/L6_drivers/cross_domain.py`  
**Layer:** L6_drivers | **Domain:** general | **Lines:** 506

**Docstring:** Cross-Domain Governance Functions (Mandatory)

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `utc_now` | `() -> datetime` | no | Return timezone-aware UTC datetime. |
| `generate_uuid` | `() -> str` | no | Generate a UUID string. |
| `create_incident_from_cost_anomaly` | `(session: AsyncSession, tenant_id: str, anomaly_id: str, anomaly_type: str, seve` | yes | Create an incident from a cost anomaly. MANDATORY. |
| `record_limit_breach` | `(session: AsyncSession, tenant_id: str, limit_id: str, breach_type: str, value_a` | yes | Record a limit breach. MANDATORY. |
| `table_exists` | `(session: AsyncSession, table_name: str) -> bool` | yes | Check if a table exists in the database. |
| `create_incident_from_cost_anomaly_sync` | `(session: Session, tenant_id: str, anomaly_id: str, anomaly_type: str, severity:` | no | Create an incident from a cost anomaly (SYNC version). MANDATORY. |
| `record_limit_breach_sync` | `(session: Session, tenant_id: str, limit_id: str, breach_type: str, value_at_bre` | no | Record a limit breach (SYNC version). MANDATORY. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `uuid` | uuid | no |
| `datetime` | datetime, timezone | no |
| `decimal` | Decimal | no |
| `typing` | Optional, Union | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `sqlmodel` | Session | no |
| `app.errors.governance` | GovernanceError | no |
| `app.metrics` | governance_incidents_created_total, governance_limit_breaches_recorded_total | no |
| `app.models.killswitch` | Incident | no |
| `app.models.policy_control_plane` | LimitBreach | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### Constants
`ANOMALY_SEVERITY_MAP`, `ANOMALY_TRIGGER_TYPE_MAP`

---

## cus_health_driver.py
**Path:** `backend/app/hoc/cus/general/L6_drivers/cus_health_driver.py`  
**Layer:** L6_drivers | **Domain:** general | **Lines:** 542

**Docstring:** Customer Health Driver

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CusHealthDriver` | __init__, check_health, _perform_health_check, check_all_integrations, get_health_summary, _calculate_overall_health | Driver for health checking customer LLM integrations. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `asyncio` | asyncio | no |
| `logging` | logging | no |
| `datetime` | datetime, timedelta, timezone | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | UUID | no |
| `httpx` | httpx | no |
| `sqlmodel` | Session, select | no |
| `app.db` | get_engine | no |
| `app.models.cus_models` | CusHealthState, CusIntegration | no |
| `app.hoc.cus.general.L5_engines.cus_credential_service` | CusCredentialService | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

---

## dag_executor.py
**Path:** `backend/app/hoc/cus/general/L6_drivers/dag_executor.py`  
**Layer:** L6_drivers | **Domain:** general | **Lines:** 325

**Docstring:** DAG-based executor for PLang v2.0.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `StageResult` | success, was_blocked | Result of executing a single stage. |
| `ExecutionTrace` | to_dict | Full execution trace across all stages. |
| `DAGExecutor` | __init__, execute, _execute_stage, _execute_policy, _is_more_restrictive, get_execution_plan, visualize_plan | Executes policies in DAG order. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `asyncio` | asyncio | no |
| `dataclasses` | dataclass, field | no |
| `typing` | Any, Dict, List, Optional | no |
| `app.policy.compiler.grammar` | ActionType | no |
| `app.policy.ir.ir_nodes` | IRModule | no |
| `app.policy.optimizer.dag_sorter` | DAGSorter, ExecutionPlan | no |
| `app.policy.runtime.deterministic_engine` | DeterministicEngine, ExecutionContext, ExecutionResult | no |
| `app.policy.runtime.intent` | Intent | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

---

## decisions.py
**Path:** `backend/app/hoc/cus/general/L6_drivers/decisions.py`  
**Layer:** L6_drivers | **Domain:** general | **Lines:** 1361

**Docstring:** Phase 4B: Decision Record Models and Service

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `DecisionType` |  | Types of decisions that must be recorded. |
| `DecisionSource` |  | Who originated the decision authority. |
| `DecisionTrigger` |  | Why the decision occurred. |
| `DecisionOutcome` |  | Result of the decision. |
| `CausalRole` |  | When in the lifecycle this decision occurred. |
| `DecisionRecord` | to_dict | Contract-aligned decision record. |
| `DecisionRecordService` | __init__, _bridge_to_taxonomy, emit, emit_sync, _emit_sync_impl | Append-only sink for decision records. |
| `CARESignalAccessError` |  | Raised when attempting to access a forbidden CARE signal. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_decision_service` | `() -> DecisionRecordService` | no | Get singleton decision record service. |
| `emit_routing_decision` | `(run_id: Optional[str], routed: bool, selected_agent: Optional[str], eligible_ag` | no | Emit a routing decision record. |
| `emit_recovery_decision` | `(run_id: Optional[str], evaluated: bool, triggered: bool, action: Optional[str] ` | no | Emit a recovery decision record. |
| `emit_memory_decision` | `(run_id: Optional[str], queried: bool, matched: bool, injected: bool, sources: O` | no | Emit a memory injection decision record. |
| `emit_policy_decision` | `(run_id: Optional[str], policy_id: str, evaluated: bool, violated: bool, severit` | no | Emit a policy enforcement decision record. |
| `emit_budget_decision` | `(run_id: Optional[str], budget_requested: int, budget_available: int, enforcemen` | no | Emit a budget handling decision record. |
| `_check_budget_enforcement_exists` | `(run_id: str) -> bool` | no | Check if a budget_enforcement decision already exists for this run. |
| `emit_budget_enforcement_decision` | `(run_id: str, budget_limit_cents: int, budget_consumed_cents: int, step_cost_cen` | no | Emit a budget enforcement decision record when hard limit halts execution. |
| `_check_policy_precheck_exists` | `(request_id: str, outcome: str) -> bool` | no | Check if a policy_pre_check decision already exists for this request+outcome. |
| `emit_policy_precheck_decision` | `(request_id: str, posture: str, passed: bool, service_available: bool, violation` | no | Emit a policy pre-check decision record. |
| `_check_recovery_evaluation_exists` | `(run_id: str, failure_type: str) -> bool` | no | Check if a recovery_evaluation decision already exists for this run+failure. |
| `emit_recovery_evaluation_decision` | `(run_id: str, request_id: str, recovery_class: str, recovery_action: Optional[st` | no | Emit a recovery evaluation decision record. |
| `backfill_run_id_for_request` | `(request_id: str, run_id: str) -> int` | no | Backfill run_id for all decisions with matching request_id. |
| `check_signal_access` | `(signal_name: str) -> bool` | no | Check if a signal is allowed for CARE optimization. |
| `activate_care_kill_switch` | `() -> bool` | no | Activate the CARE optimization kill-switch. |
| `deactivate_care_kill_switch` | `() -> bool` | no | Deactivate the CARE optimization kill-switch. |
| `is_care_kill_switch_active` | `() -> bool` | no | Check if CARE kill-switch is currently active. |
| `_check_care_optimization_exists` | `(request_id: str) -> bool` | no | Check if a care_routing_optimized decision already exists for this request. |
| `emit_care_optimization_decision` | `(request_id: str, baseline_agent: str, optimized_agent: str, confidence_score: f` | no | Emit a CARE routing optimization decision record. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `json` | json | no |
| `logging` | logging | no |
| `os` | os | no |
| `uuid` | uuid | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, Optional | no |
| `pydantic` | BaseModel, Field | no |
| `sqlalchemy` | create_engine, text | no |
| `sqlalchemy.exc` | SQLAlchemyError | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### Constants
`CARE_ALLOWED_SIGNALS`, `CARE_FORBIDDEN_SIGNALS`, `CARE_CONFIDENCE_THRESHOLD`

---

## governance_signal_driver.py
**Path:** `backend/app/hoc/cus/general/L6_drivers/governance_signal_driver.py`  
**Layer:** L6_drivers | **Domain:** general | **Lines:** 293

**Docstring:** Governance Signal Service (Phase E FIX-03)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `GovernanceSignalService` | __init__, record_signal, _supersede_existing_signals, check_governance, is_blocked, get_active_signals, clear_signal | Service for governance signal operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `check_governance_status` | `(session: Session, scope: str, signal_type: Optional[str] = None) -> GovernanceC` | no | Check governance status for a scope. |
| `is_governance_blocked` | `(session: Session, scope: str, signal_type: Optional[str] = None) -> bool` | no | Quick check if scope is blocked. |
| `record_governance_signal` | `(session: Session, signal_type: str, scope: str, decision: str, recorded_by: str` | no | Record a governance signal. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timezone | no |
| `typing` | Optional | no |
| `sqlalchemy` | and_, or_, select, update | no |
| `sqlalchemy.orm` | Session | no |
| `app.models.governance` | GovernanceCheckResult, GovernanceSignal, GovernanceSignalResponse | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

---

## guard_cache.py
**Path:** `backend/app/hoc/cus/general/L6_drivers/guard_cache.py`  
**Layer:** L6_drivers | **Domain:** general | **Lines:** 252

**Docstring:** Redis-based cache for Guard Console endpoints.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `GuardCache` | __init__, get_instance, _get_redis, _make_key, get, set, invalidate, get_status (+6 more) | Redis-based cache for Guard Console API. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_guard_cache` | `() -> GuardCache` | no | Get guard cache singleton. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `json` | json | no |
| `logging` | logging | no |
| `os` | os | no |
| `typing` | Dict, Optional | no |
| `metrics_helpers` | get_or_create_counter, get_or_create_histogram | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### Constants
`GUARD_CACHE_ENABLED`, `GUARD_STATUS_TTL`, `GUARD_SNAPSHOT_TTL`, `GUARD_INCIDENTS_TTL`, `GUARD_CACHE_PREFIX`, `GUARD_CACHE_HITS`, `GUARD_CACHE_MISSES`, `GUARD_CACHE_LATENCY`

### __all__ Exports
`GuardCache`, `get_guard_cache`, `GUARD_STATUS_TTL`, `GUARD_SNAPSHOT_TTL`, `GUARD_INCIDENTS_TTL`

---

## idempotency.py
**Path:** `backend/app/hoc/cus/general/L6_drivers/idempotency.py`  
**Layer:** L6_drivers | **Domain:** general | **Lines:** 160

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IdempotencyResult` |  | Result of idempotency check. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_existing_run` | `(idempotency_key: str, tenant_id: Optional[str] = None, agent_id: Optional[str] ` | no | Check if a run with this idempotency key already exists. |
| `check_idempotency` | `(idempotency_key: str, tenant_id: Optional[str] = None, agent_id: Optional[str] ` | no | Check idempotency and return result with status. |
| `should_return_cached` | `(result: IdempotencyResult) -> bool` | no | Determine if we should return cached result. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `typing` | Optional | no |
| `sqlmodel` | Session, select | no |
| `db` | Run, engine | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### Constants
`IDEMPOTENCY_TTL_SECONDS`

---

## ledger.py
**Path:** `backend/app/hoc/cus/general/L6_drivers/ledger.py`  
**Layer:** L6_drivers | **Domain:** general | **Lines:** 270

**Docstring:** Discovery Ledger - signal recording helpers.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `DiscoverySignal` |  | Discovery signal data model. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `emit_signal` | `(artifact: str, signal_type: str, evidence: dict[str, Any], detected_by: str, fi` | no | Record a discovery signal to the ledger. |
| `get_signals` | `(artifact: Optional[str] = None, signal_type: Optional[str] = None, status: Opti` | no | Query discovery signals from the ledger. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `decimal` | Decimal | no |
| `typing` | Any, Optional | no |
| `uuid` | UUID | no |
| `pydantic` | BaseModel, Field | no |
| `sqlalchemy` | text | no |
| `sqlalchemy.exc` | SQLAlchemyError | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

---

## schema_parity.py
**Path:** `backend/app/hoc/cus/general/L6_drivers/schema_parity.py`  
**Layer:** L6_drivers | **Domain:** general | **Lines:** 166

**Docstring:** M26 Prevention Mechanism #2: Startup Schema Parity Guard

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SchemaParityError` |  | Raised when model schema doesn't match database schema. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `check_schema_parity` | `(engine: Engine, models: Optional[List[type]] = None, hard_fail: bool = True) ->` | no | Check that SQLModel definitions match actual database schema. |
| `check_m26_cost_tables` | `(engine: Engine) -> Tuple[bool, List[str]]` | no | Specific check for M26 cost tables - the most critical. |
| `run_startup_parity_check` | `(engine: Engine) -> None` | no | Run full schema parity check on startup. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | List, Optional, Tuple | no |
| `sqlalchemy` | inspect | no |
| `sqlalchemy.engine` | Engine | no |
| `sqlmodel` | SQLModel | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

---

## worker_write_service_async.py
**Path:** `backend/app/hoc/cus/general/L6_drivers/worker_write_service_async.py`  
**Layer:** L6_drivers | **Domain:** general | **Lines:** 222

**Docstring:** Worker Write Service (Async) - DB write operations for Worker API.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `WorkerWriteServiceAsync` | __init__, upsert_worker_run, insert_cost_record, insert_cost_advisory, delete_worker_run, get_worker_run | Async DB write operations for Worker API. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `json` | json | no |
| `datetime` | datetime | no |
| `typing` | Any, Dict, Optional | no |
| `sqlalchemy` | select | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.db` | CostAnomaly, CostRecord | no |
| `app.models.tenant` | WorkerRun | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

---
