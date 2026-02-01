# run_governance_facade.py

**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/run_governance_facade.py`  
**Layer:** L4 — HOC Spine (Orchestrator)  
**Component:** Orchestrator

---

## Placement Card

```
File:            run_governance_facade.py
Lives in:        orchestrator/
Role:            Orchestrator
Inbound:         L5 runner (worker runtime)
Outbound:        app.hoc.cus.hoc_spine.schemas.rac_models, app.hoc.cus.hoc_spine.services.audit_store
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Run Governance Facade (L4 Domain Logic)
Violations:      none
```

## Purpose

Run Governance Facade (L4 Domain Logic)

This facade provides the external interface for governance operations
during run execution. The L5 runner MUST use this facade instead of
directly importing L4 engines.

Why This Facade Exists (PIN-454):
- Prevents L5→L4 layer violations (runner importing engines directly)
- Centralizes governance logic for run lifecycle
- Provides RAC (Runtime Audit Contract) acknowledgment emission
- Single point for audit expectation/acknowledgment emission

Wrapped Services:
- LessonsLearnedEngine: Learning from run outcomes
- PolicyViolationService: Policy evaluation for runs

RAC Integration (PIN-454):
- Emits acknowledgments after policy evaluation
- Domain: POLICIES
- Action: EVALUATE_POLICY

Usage:
    from app.hoc.cus.hoc_spine.orchestrator.run_governance_facade import get_run_governance_facade

    facade = get_run_governance_facade()

    # Policy evaluation (emits RAC ack automatically)
    policy_id = facade.create_policy_evaluation(
        run_id=run_id,
        tenant_id=tenant_id,
        run_status="succeeded",
    )

    # Lesson emission
    lesson_id = facade.emit_near_threshold_lesson(
        tenant_id=tenant_id,
        metric="budget",
        utilization=87.5,
        ...
    )

## Import Analysis

**Spine-internal:**
- `app.hoc.cus.hoc_spine.schemas.rac_models`
- `app.hoc.cus.hoc_spine.services.audit_store`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `get_run_governance_facade() -> RunGovernanceFacade`

Get the run governance facade instance.

This is the recommended way to access governance operations from
the L5 worker runtime.

Returns:
    RunGovernanceFacade instance

## Classes

### `RunGovernanceFacade`

Facade for run governance operations.

This is the ONLY entry point for L5 worker code to interact with
lessons learned and policy evaluation services.

Layer: L4 (Domain Logic)
Callers: RunRunner (L5)

#### Methods

- `__init__()` — Initialize facade with lazy-loaded engines.
- `_lessons()` — Lazy-load LessonsLearnedEngine.
- `create_policy_evaluation(run_id: str, tenant_id: str, run_status: str, policies_checked: int, is_synthetic: bool, synthetic_scenario_id: Optional[str]) -> Optional[str]` — Create a policy evaluation record for a run (PIN-407).
- `_emit_ack(run_id: str, result_id: Optional[str], error: Optional[str]) -> None` — Emit RAC acknowledgment for policy evaluation.
- `emit_near_threshold_lesson(tenant_id: str, metric: str, utilization: float, threshold_value: float, current_value: float, source_event_id: UUID, window: str, is_synthetic: bool, synthetic_scenario_id: Optional[str]) -> Optional[UUID]` — Emit a near-threshold lesson for proactive governance.
- `emit_critical_success_lesson(tenant_id: str, success_type: str, metrics: Dict[str, Any], source_event_id: UUID, is_synthetic: bool, synthetic_scenario_id: Optional[str]) -> Optional[UUID]` — Emit a critical success lesson for positive reinforcement.

## Domain Usage

**Callers:** L5 runner (worker runtime)

## Export Contract

```yaml
exports:
  functions:
    - name: get_run_governance_facade
      signature: "get_run_governance_facade() -> RunGovernanceFacade"
      consumers: ["orchestrator"]
  classes:
    - name: RunGovernanceFacade
      methods:
        - create_policy_evaluation
        - emit_near_threshold_lesson
        - emit_critical_success_lesson
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc.api.*"
    - "hoc_spine.adapters.*"
  forbidden_inbound:
  actual_imports:
    spine_internal: ['app.hoc.cus.hoc_spine.schemas.rac_models', 'app.hoc.cus.hoc_spine.services.audit_store']
    l7_model: []
    external: []
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

