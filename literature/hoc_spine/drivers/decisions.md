# decisions.py

**Path:** `backend/app/hoc/hoc_spine/drivers/decisions.py`  
**Layer:** L4 — HOC Spine (Driver)  
**Component:** Drivers

---

## Placement Card

```
File:            decisions.py
Lives in:        drivers/
Role:            Drivers
Inbound:         API routes, workers
Outbound:        none
Transaction:     OWNS COMMIT
Cross-domain:    none
Purpose:         Phase 4B: Decision Record Models and Service
Violations:      Driver calls commit (only transaction_coordinator allowed)
```

## Purpose

Phase 4B: Decision Record Models and Service

Implements DECISION_RECORD_CONTRACT v0.2.

Contract-mandated fields:
- decision_source: human | system | hybrid
- decision_trigger: explicit | autonomous | reactive

Rule: Emit records where decisions already happen. No logic changes.

## Import Analysis

**External:**
- `pydantic`
- `sqlalchemy`
- `sqlalchemy.exc`

## Transaction Boundary

- **Commits:** YES
- **Flushes:** no
- **Rollbacks:** no

## Governance Violations

- Driver calls commit (only transaction_coordinator allowed)

## Functions

### `get_decision_service() -> DecisionRecordService`

Get singleton decision record service.

### `emit_routing_decision(run_id: Optional[str], routed: bool, selected_agent: Optional[str], eligible_agents: list, rejection_reason: Optional[str], tenant_id: str, details: Optional[Dict[str, Any]], request_id: Optional[str], causal_role: CausalRole) -> DecisionRecord`

Emit a routing decision record.

Called from CARE engine after every route() call.
Note: Routing typically happens BEFORE run exists, so causal_role=PRE_RUN.

### `emit_recovery_decision(run_id: Optional[str], evaluated: bool, triggered: bool, action: Optional[str], candidates_count: int, reason: Optional[str], tenant_id: str, request_id: Optional[str], causal_role: CausalRole) -> DecisionRecord`

Emit a recovery decision record.

Called from recovery engine after every evaluation.
Note: Recovery happens DURING run execution, so causal_role=IN_RUN.

### `emit_memory_decision(run_id: Optional[str], queried: bool, matched: bool, injected: bool, sources: Optional[list], reason: Optional[str], tenant_id: str, request_id: Optional[str], causal_role: CausalRole) -> DecisionRecord`

Emit a memory injection decision record.

Called after every memory query attempt.
Note: Memory injection can happen pre-run or in-run. Default is IN_RUN.

### `emit_policy_decision(run_id: Optional[str], policy_id: str, evaluated: bool, violated: bool, severity: str, reason: Optional[str], tenant_id: str, request_id: Optional[str], causal_role: CausalRole) -> DecisionRecord`

Emit a policy enforcement decision record.

Called after every policy check.
Note: Policy checks can happen pre-run or in-run. Default is IN_RUN.

### `emit_budget_decision(run_id: Optional[str], budget_requested: int, budget_available: int, enforcement: str, simulation_feasible: Optional[bool], proceeded: bool, reason: Optional[str], tenant_id: str, request_id: Optional[str], causal_role: CausalRole) -> DecisionRecord`

Emit a budget handling decision record.

Called after every budget check.
Note: Budget checks typically happen pre-run to verify resource availability.

### `_check_budget_enforcement_exists(run_id: str) -> bool`

Check if a budget_enforcement decision already exists for this run.

Idempotency guard: prevents double emission on retry/restart.

### `emit_budget_enforcement_decision(run_id: str, budget_limit_cents: int, budget_consumed_cents: int, step_cost_cents: int, completed_steps: int, total_steps: int, tenant_id: str) -> Optional[DecisionRecord]`

Emit a budget enforcement decision record when hard limit halts execution.

Phase 5A: This is the ONLY decision type for hard budget halts.
Called immediately when execution is halted due to hard budget limit.

IDEMPOTENT: If already emitted for this run_id, returns None.

Contract alignment:
- decision_type: budget_enforcement
- decision_source: system
- decision_trigger: reactive
- decision_outcome: execution_halted

### `_check_policy_precheck_exists(request_id: str, outcome: str) -> bool`

Check if a policy_pre_check decision already exists for this request+outcome.

Idempotency guard: prevents double emission on retry/restart.

### `emit_policy_precheck_decision(request_id: str, posture: str, passed: bool, service_available: bool, violations: Optional[list], tenant_id: str) -> Optional[DecisionRecord]`

Emit a policy pre-check decision record.

Phase 5B: Pre-execution policy check.

EMISSION RULE (FROZEN):
  - EMIT IFF (posture == strict AND (failed OR unavailable))
  - DO NOT EMIT if passed or posture == advisory

Contract alignment:
- decision_type: policy_pre_check
- decision_source: system
- decision_trigger: explicit (pre-check is proactive)
- causal_role: pre_run (always - run doesn't exist yet)
- run_id: None (run not created on block)

IDEMPOTENT: If already emitted for this request_id+outcome, returns None.

### `_check_recovery_evaluation_exists(run_id: str, failure_type: str) -> bool`

Check if a recovery_evaluation decision already exists for this run+failure.

Idempotency guard: prevents double emission on retry/restart.

### `emit_recovery_evaluation_decision(run_id: str, request_id: str, recovery_class: str, recovery_action: Optional[str], failure_type: str, failure_context: Optional[Dict[str, Any]], tenant_id: str) -> Optional[DecisionRecord]`

Emit a recovery evaluation decision record.

Phase 5C: Post-failure recovery evaluation.

EMISSION RULE (FROZEN per PIN-174):
  - ALWAYS emit exactly one RECOVERY_EVALUATION decision after any:
    - execution_halted
    - execution_failed

  Outcome mapping:
    - R1 and applied → recovery_applied
    - R2 and suggested → recovery_suggested
    - R3 or no applicable recovery → recovery_skipped

Contract alignment:
- decision_type: recovery_evaluation
- decision_source: system
- decision_trigger: reactive (recovery is always reactive to failure)
- causal_role: post_run (always - recovery evaluates after failure)

IDEMPOTENT: If already emitted for this run_id+failure_type, returns None.

### `backfill_run_id_for_request(request_id: str, run_id: str) -> int`

Backfill run_id for all decisions with matching request_id.

Called from run creation to bind pre-run decisions (routing, policy, budget)
to the newly created run. This is context enrichment, not mutation.

Returns the number of records updated.

### `check_signal_access(signal_name: str) -> bool`

Check if a signal is allowed for CARE optimization.

Phase 5D: Hard guard on signal access.

Raises:
    CARESignalAccessError: If signal is forbidden

Returns:
    True if signal is allowed

### `activate_care_kill_switch() -> bool`

Activate the CARE optimization kill-switch.

When activated:
- Forces baseline selection
- Prevents decision emission
- Takes effect within 1 request cycle

Returns:
    True on successful activation

### `deactivate_care_kill_switch() -> bool`

Deactivate the CARE optimization kill-switch.

Returns:
    True on successful deactivation

### `is_care_kill_switch_active() -> bool`

Check if CARE kill-switch is currently active.

### `_check_care_optimization_exists(request_id: str) -> bool`

Check if a care_routing_optimized decision already exists for this request.

Idempotency guard: prevents double emission.

### `emit_care_optimization_decision(request_id: str, baseline_agent: str, optimized_agent: str, confidence_score: float, signals_used: list, optimization_enabled: bool, shadow_mode: bool, tenant_id: str) -> Optional[DecisionRecord]`

Emit a CARE routing optimization decision record.

Phase 5D: Optimization-driven routing decision.

EMISSION RULE (FROZEN per PIN-176):
  - EMIT CARE_ROUTING_OPTIMIZED decision IF AND ONLY IF:
    - optimization_enabled = true
    - AND NOT shadow_mode
    - AND optimized_agent != baseline_agent

  - DO NOT EMIT if:
    - optimization_disabled
    - shadow_mode (log only, no decision record)
    - baseline == optimized (silence allowed)
    - kill_switch active

Contract alignment:
- decision_type: care_routing_optimized
- decision_source: system
- decision_trigger: autonomous (learning-driven)
- causal_role: pre_run (always - before run exists)

IDEMPOTENT: If already emitted for this request_id, returns None.

## Classes

### `DecisionType(str, Enum)`

Types of decisions that must be recorded.

### `DecisionSource(str, Enum)`

Who originated the decision authority.

### `DecisionTrigger(str, Enum)`

Why the decision occurred.

### `DecisionOutcome(str, Enum)`

Result of the decision.

### `CausalRole(str, Enum)`

When in the lifecycle this decision occurred.

### `DecisionRecord(BaseModel)`

Contract-aligned decision record.

Every decision (routing, recovery, memory, policy, budget) emits one of these.
Append-only. No business logic.

#### Methods

- `to_dict() -> Dict[str, Any]` — Convert to dictionary for JSON/logging.

### `DecisionRecordService`

Append-only sink for decision records.

Emits to contracts.decision_records table.
Non-blocking - failures are logged but don't affect callers.

Evidence Architecture v1.0: Also bridges to governance.policy_decisions for taxonomy evidence.

#### Methods

- `__init__(db_url: Optional[str])` — _No docstring._
- `_bridge_to_taxonomy(record: DecisionRecord) -> None` — Evidence Architecture v1.0: Bridge decision to governance taxonomy.
- `async emit(record: DecisionRecord) -> bool` — Emit a decision record to the sink.
- `emit_sync(record: DecisionRecord) -> bool` — Synchronous version of emit for non-async contexts.
- `_emit_sync_impl(record: DecisionRecord) -> bool` — Synchronous implementation of emit.

### `CARESignalAccessError(Exception)`

Raised when attempting to access a forbidden CARE signal.

## Domain Usage

**Callers:** API routes, workers

## Export Contract

```yaml
exports:
  functions:
    - name: get_decision_service
      signature: "get_decision_service() -> DecisionRecordService"
      consumers: ["orchestrator"]
    - name: emit_routing_decision
      signature: "emit_routing_decision(run_id: Optional[str], routed: bool, selected_agent: Optional[str], eligible_agents: list, rejection_reason: Optional[str], tenant_id: str, details: Optional[Dict[str, Any]], request_id: Optional[str], causal_role: CausalRole) -> DecisionRecord"
      consumers: ["orchestrator"]
    - name: emit_recovery_decision
      signature: "emit_recovery_decision(run_id: Optional[str], evaluated: bool, triggered: bool, action: Optional[str], candidates_count: int, reason: Optional[str], tenant_id: str, request_id: Optional[str], causal_role: CausalRole) -> DecisionRecord"
      consumers: ["orchestrator"]
    - name: emit_memory_decision
      signature: "emit_memory_decision(run_id: Optional[str], queried: bool, matched: bool, injected: bool, sources: Optional[list], reason: Optional[str], tenant_id: str, request_id: Optional[str], causal_role: CausalRole) -> DecisionRecord"
      consumers: ["orchestrator"]
    - name: emit_policy_decision
      signature: "emit_policy_decision(run_id: Optional[str], policy_id: str, evaluated: bool, violated: bool, severity: str, reason: Optional[str], tenant_id: str, request_id: Optional[str], causal_role: CausalRole) -> DecisionRecord"
      consumers: ["orchestrator"]
    - name: emit_budget_decision
      signature: "emit_budget_decision(run_id: Optional[str], budget_requested: int, budget_available: int, enforcement: str, simulation_feasible: Optional[bool], proceeded: bool, reason: Optional[str], tenant_id: str, request_id: Optional[str], causal_role: CausalRole) -> DecisionRecord"
      consumers: ["orchestrator"]
    - name: _check_budget_enforcement_exists
      signature: "_check_budget_enforcement_exists(run_id: str) -> bool"
      consumers: ["orchestrator"]
    - name: emit_budget_enforcement_decision
      signature: "emit_budget_enforcement_decision(run_id: str, budget_limit_cents: int, budget_consumed_cents: int, step_cost_cents: int, completed_steps: int, total_steps: int, tenant_id: str) -> Optional[DecisionRecord]"
      consumers: ["orchestrator"]
    - name: _check_policy_precheck_exists
      signature: "_check_policy_precheck_exists(request_id: str, outcome: str) -> bool"
      consumers: ["orchestrator"]
    - name: emit_policy_precheck_decision
      signature: "emit_policy_precheck_decision(request_id: str, posture: str, passed: bool, service_available: bool, violations: Optional[list], tenant_id: str) -> Optional[DecisionRecord]"
      consumers: ["orchestrator"]
    - name: _check_recovery_evaluation_exists
      signature: "_check_recovery_evaluation_exists(run_id: str, failure_type: str) -> bool"
      consumers: ["orchestrator"]
    - name: emit_recovery_evaluation_decision
      signature: "emit_recovery_evaluation_decision(run_id: str, request_id: str, recovery_class: str, recovery_action: Optional[str], failure_type: str, failure_context: Optional[Dict[str, Any]], tenant_id: str) -> Optional[DecisionRecord]"
      consumers: ["orchestrator"]
    - name: backfill_run_id_for_request
      signature: "backfill_run_id_for_request(request_id: str, run_id: str) -> int"
      consumers: ["orchestrator"]
    - name: check_signal_access
      signature: "check_signal_access(signal_name: str) -> bool"
      consumers: ["orchestrator"]
    - name: activate_care_kill_switch
      signature: "activate_care_kill_switch() -> bool"
      consumers: ["orchestrator"]
    - name: deactivate_care_kill_switch
      signature: "deactivate_care_kill_switch() -> bool"
      consumers: ["orchestrator"]
    - name: is_care_kill_switch_active
      signature: "is_care_kill_switch_active() -> bool"
      consumers: ["orchestrator"]
    - name: _check_care_optimization_exists
      signature: "_check_care_optimization_exists(request_id: str) -> bool"
      consumers: ["orchestrator"]
    - name: emit_care_optimization_decision
      signature: "emit_care_optimization_decision(request_id: str, baseline_agent: str, optimized_agent: str, confidence_score: float, signals_used: list, optimization_enabled: bool, shadow_mode: bool, tenant_id: str) -> Optional[DecisionRecord]"
      consumers: ["orchestrator"]
  classes:
    - name: DecisionType
      methods: []
      consumers: ["orchestrator"]
    - name: DecisionSource
      methods: []
      consumers: ["orchestrator"]
    - name: DecisionTrigger
      methods: []
      consumers: ["orchestrator"]
    - name: DecisionOutcome
      methods: []
      consumers: ["orchestrator"]
    - name: CausalRole
      methods: []
      consumers: ["orchestrator"]
    - name: DecisionRecord
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: DecisionRecordService
      methods:
        - emit
        - emit_sync
      consumers: ["orchestrator"]
    - name: CARESignalAccessError
      methods: []
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
    - "hoc_spine.services.*"
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
  actual_imports:
    spine_internal: []
    l7_model: []
    external: ['pydantic', 'sqlalchemy', 'sqlalchemy.exc']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

