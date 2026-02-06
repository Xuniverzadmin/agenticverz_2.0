# policies_handler.py

**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/policies_handler.py`
**Layer:** L4 — HOC Spine (Handler)
**Component:** Orchestrator / Handler
**Created:** 2026-02-03
**Reference:** PIN-491 (L2-L4-L5 Construction Plan), PIN-520 (L4 Uniformity Initiative)

---

## Placement Card

```
File:            policies_handler.py
Lives in:        orchestrator/handlers/
Role:            Policies domain handler — routes policies operations to L5 engines via L4 registry
Inbound:         OperationRegistry (L4)
Outbound:        policies/L5_engines/* (lazy imports)
Transaction:     none (dispatch only)
Cross-domain:    no (single domain)
Purpose:         Route policies domain operations to L5 engines
Violations:      none
```

## Purpose

Domain handler for policies operations. Routes L2 HTTP requests to L5 engines
via the L4 operation registry. Implements the Dispatch Pattern (Law 5 - PIN-507):

- Explicit dispatch maps (no getattr reflection)
- Lazy imports inside execute()
- Session binding at handler level
- Error semantics preserved per facade

## Registered Operations

| Operation | Handler Class | L5 Target | Methods |
|-----------|---------------|-----------|---------|
| `policies.query` | PoliciesQueryHandler | PoliciesFacade | 13 async methods |
| `policies.enforcement` | PoliciesEnforcementHandler | CusEnforcementEngine | 3 async methods |
| `policies.governance` | PoliciesGovernanceHandler | GovernanceFacade | 7 sync methods |
| `policies.lessons` | PoliciesLessonsHandler | LessonsLearnedEngine | 14 methods |
| `policies.policy_facade` | PoliciesPolicyFacadeHandler | PolicyDriver | 37+ methods |
| `policies.limits` | PoliciesLimitsHandler | PolicyLimitsService | 4 async methods |
| `policies.rules` | PoliciesRulesHandler | PolicyRulesService | 3 async methods |
| `policies.rate_limits` | PoliciesRateLimitsHandler | LimitsFacade | 6 async methods |
| `policies.simulate` | PoliciesSimulateHandler | LimitsSimulationEngine | 1 async method |
| `policies.limits_query` | PoliciesLimitsQueryHandler | LimitsQueryEngine | dynamic |
| `policies.proposals_query` | PoliciesProposalsQueryHandler | ProposalsQueryEngine | dynamic |
| `policies.rules_query` | PoliciesRulesQueryHandler | PolicyRulesQueryEngine | dynamic |
| `policies.health` | PoliciesHealthHandler | — | 1 async method (PIN-520) |

## Handler Details

### PoliciesQueryHandler

Dispatches to PoliciesFacade (13 async endpoints):
- `list_policy_rules`, `get_policy_rule_detail`, `list_limits`, `get_limit_detail`
- `get_policy_state`, `get_policy_metrics`, `list_conflicts`, `get_dependency_graph`
- `list_violations`, `list_budgets`, `list_requests`, `list_lessons`, `get_lesson_stats`

### PoliciesEnforcementHandler

Dispatches to CusEnforcementEngine (3 async endpoints):
- `evaluate`, `get_enforcement_status`, `evaluate_batch`

### PoliciesGovernanceHandler

Dispatches to GovernanceFacade (7 sync endpoints):
- `enable_kill_switch`, `disable_kill_switch`, `set_mode`
- `get_governance_state`, `resolve_conflict`, `list_conflicts`, `get_boot_status`

### PoliciesLessonsHandler

Dispatches to LessonsLearnedEngine (14 endpoints):
- `detect_lesson_from_failure`, `detect_lesson_from_near_threshold`
- `detect_lesson_from_critical_success`, `emit_near_threshold`, `emit_critical_success`
- `list_lessons`, `get_lesson`, `convert_lesson_to_draft`
- `defer_lesson`, `dismiss_lesson`, `get_lesson_stats`
- `reactivate_deferred_lesson`, `get_expired_deferred_lessons`, `reactivate_expired_deferred_lessons`

Injects capability via DomainBridge (PIN-508 Phase 2A).

### PoliciesPolicyFacadeHandler

Dispatches to PolicyDriver (37+ endpoints):
- Evaluation: `evaluate`, `pre_check`, `get_state`, `evaluate_with_context`
- Reload: `reload_policies`
- Violations: `get_violations`, `get_violation`, `acknowledge_violation`
- Risk: `get_risk_ceilings`, `get_risk_ceiling`, `update_risk_ceiling`, `reset_risk_ceiling`
- Safety: `get_safety_rules`, `update_safety_rule`
- Ethics: `get_ethical_constraints`
- Cooldowns: `get_active_cooldowns`, `clear_cooldowns`
- Metrics: `get_metrics`
- Versioning: `get_policy_versions`, `get_current_version`, `create_policy_version`, `rollback_to_version`, `get_version_provenance`, `activate_policy_version`
- Dependencies: `get_dependency_graph`, `get_policy_conflicts`, `resolve_conflict`, `validate_dependency_dag`, `add_dependency_with_dag_check`, `get_topological_evaluation_order` (sync)
- Temporal: `get_temporal_policies`, `create_temporal_policy`, `get_temporal_utilization`, `prune_temporal_metrics`, `get_temporal_storage_stats`

### PoliciesLimitsHandler

Dispatches to PolicyLimitsService (4 async endpoints):
- `create`, `update`, `delete`, `get`

Injects audit service and capability via DomainBridge (PIN-508 Phase 2C).

Error translation: `LimitNotFoundError`, `ImmutableFieldError`, `LimitValidationError`, `PolicyLimitsServiceError`.

### PoliciesRulesHandler

Dispatches to PolicyRulesService (3 async endpoints):
- `create`, `update`, `get`

Injects audit service (PIN-504).

Error translation: `RuleNotFoundError`, `RuleValidationError`, `PolicyRulesServiceError`.

### PoliciesRateLimitsHandler

Dispatches to LimitsFacade (6 async endpoints):
- `list_limits`, `get_limit`, `update_limit`, `check_limit`, `get_usage`, `reset_limit`

### PoliciesSimulateHandler

Dispatches to LimitsSimulationEngine (1 async endpoint):
- `simulate`

Error translation: `TenantNotFoundError`, `LimitsSimulationServiceError`.

### PoliciesLimitsQueryHandler (PIN-513 Batch 2B)

Dispatches to LimitsQueryEngine (dynamic dispatch via getattr).

### PoliciesProposalsQueryHandler (PIN-513 Batch 2B)

Dispatches to ProposalsQueryEngine (dynamic dispatch via getattr).

### PoliciesRulesQueryHandler (PIN-513 Batch 2B)

Dispatches to PolicyRulesQueryEngine (dynamic dispatch via getattr).

### PoliciesHealthHandler (PIN-520 Phase 1)

Reports availability of policy-related L5 engines. Used by workers.py health endpoint
to check moat status.

**Purpose:**

This handler absorbs the L5 import checks that were previously done directly in workers.py,
routing them through L4. It checks availability of:

- **M20 Policy** (DAGExecutor): Policy DAG execution capability
- **M9 Failure Catalog** (RecoveryEvaluationEngine): Failure catalog for recovery decisions
- **M10 Recovery** (RecoveryEvaluationEngine): Recovery evaluation capability

**Response:**

```python
{
    "m20_policy": "available" | "unavailable",
    "m9_failure_catalog": "available" | "unavailable",
    "m10_recovery": "available" | "unavailable"
}
```

**Usage:**

```python
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import get_operation_registry

registry = get_operation_registry()
result = await registry.execute(
    "policies.health",
    tenant_id="t-123",
    session=session,
    params={}
)
# result.data = {"m20_policy": "available", "m9_failure_catalog": "available", "m10_recovery": "available"}
```

## PIN-520 Phase 1

The PoliciesHealthHandler was added as part of PIN-520 Phase 1 (workers.py migration).
It absorbs the moat availability checks that were previously done directly in workers.py,
routing them through the L4 operation registry for proper layer compliance.

This enables:
1. Moat availability checks via L4 (no direct L5 imports in L2)
2. Consistent health check patterns across domains
3. Workers.py layer compliance (L2 -> L4 -> L5)

---

*Generated: 2026-02-03*
