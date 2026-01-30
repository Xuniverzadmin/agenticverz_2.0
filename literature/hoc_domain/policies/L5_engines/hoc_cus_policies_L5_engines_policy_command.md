# hoc_cus_policies_L5_engines_policy_command

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/policy_command.py` |
| Layer | L4 — Domain Engine (Command Facade) |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy evaluation and decision authority

## Intent

**Role:** Policy evaluation and decision authority
**Reference:** PIN-258 Phase F-3 Policy Cluster
**Callers:** policy_adapter.py (L3)

## Purpose

Policy Command (L4)

---

## Functions

### `async simulate_cost(skill_id: str, tenant_id: str, payload: Dict[str, Any]) -> Optional[int]`
- **Async:** Yes
- **Docstring:** Simulate cost for a skill execution.  This L4 command delegates to L5 CostSimulator.
- **Calls:** CostSimulator, debug, int, simulate, warning

### `async check_policy_violations(skill_id: str, tenant_id: str, agent_id: Optional[str], payload: Dict[str, Any], simulated_cost: Optional[int]) -> List[PolicyViolation]`
- **Async:** Yes
- **Docstring:** Check for policy violations.  This L4 command delegates to L5 PolicyEnforcer.
- **Calls:** MinimalContext, MinimalStep, PolicyEnforcer, PolicyViolation, _record_budget_rejection, _record_capability_violation, append, check_can_execute, debug, str, type

### `async evaluate_policy(skill_id: str, tenant_id: str, agent_id: Optional[str], payload: Dict[str, Any], auto_approve_max_cost_cents: int, approval_level: int) -> PolicyEvaluationResult`
- **Async:** Yes
- **Docstring:** Evaluate policy for a skill execution.  This L4 command orchestrates:
- **Calls:** PolicyEvaluationResult, _record_policy_decision, all, append, check_policy_violations, simulate_cost

### `_record_policy_decision(decision: str, policy_type: str) -> None`
- **Async:** No
- **Docstring:** Record policy decision metric.  L4 → L5 is allowed. This is an effect, not a decision.
- **Calls:** debug, record_policy_decision

### `_record_capability_violation(violation_type: str, skill_id: str, tenant_id: Optional[str]) -> None`
- **Async:** No
- **Docstring:** Record capability violation metric.  L4 → L5 is allowed. This is an effect, not a decision.
- **Calls:** debug, record_capability_violation

### `_record_budget_rejection(resource_type: str, skill_id: str) -> None`
- **Async:** No
- **Docstring:** Record budget rejection metric.  L4 → L5 is allowed. This is an effect, not a decision.
- **Calls:** debug, record_budget_rejection

### `_record_approval_request_created(policy_type: str) -> None`
- **Async:** No
- **Docstring:** Record approval request creation metric.  L4 → L5 is allowed. This is an effect, not a decision.
- **Calls:** debug, record_approval_request_created

### `_record_approval_action(result: str) -> None`
- **Async:** No
- **Docstring:** Record approval action metric.  L4 → L5 is allowed. This is an effect, not a decision.
- **Calls:** debug, record_approval_action

### `_record_approval_escalation() -> None`
- **Async:** No
- **Docstring:** Record approval escalation metric.  L4 → L5 is allowed. This is an effect, not a decision.
- **Calls:** debug, record_approval_escalation

### `_record_webhook_fallback() -> None`
- **Async:** No
- **Docstring:** Record webhook fallback metric.  L4 → L5 is allowed. This is an effect, not a decision.
- **Calls:** debug, record_webhook_fallback

### `record_approval_created(policy_type: str) -> None`
- **Async:** No
- **Docstring:** Record that an approval request was created.  This is a public L4 command for L3 to call.
- **Calls:** _record_approval_request_created

### `record_approval_outcome(result: str) -> None`
- **Async:** No
- **Docstring:** Record approval outcome (approved/rejected/expired).  This is a public L4 command for L3 to call.
- **Calls:** _record_approval_action

### `record_escalation() -> None`
- **Async:** No
- **Docstring:** Record that an escalation occurred.  This is a public L4 command for L3 to call.
- **Calls:** _record_approval_escalation

### `record_webhook_used() -> None`
- **Async:** No
- **Docstring:** Record that webhook fallback was used.  This is a public L4 command for L3 to call.
- **Calls:** _record_webhook_fallback

## Classes

### `PolicyViolation`
- **Docstring:** A policy violation detected during evaluation.
- **Class Variables:** type: str, message: str, policy: str, details: Dict[str, Any]

### `PolicyEvaluationResult`
- **Docstring:** Result from policy evaluation command.
- **Class Variables:** decision: str, reasons: List[str], simulated_cost_cents: Optional[int], violations: List[PolicyViolation], approval_level_required: Optional[int], auto_approve_threshold_cents: Optional[int]

### `ApprovalConfig`
- **Docstring:** Approval level configuration.
- **Class Variables:** approval_level: int, auto_approve_max_cost_cents: int, require_human_approval: bool, webhook_url: Optional[str], escalate_to: Optional[str], escalation_timeout_seconds: int

## Attributes

- `logger` (line 41)
- `__all__` (line 462)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.workflow.cost_sim`, `app.workflow.metrics`, `app.workflow.policies` |

## Callers

policy_adapter.py (L3)

## Export Contract

```yaml
exports:
  functions:
    - name: simulate_cost
      signature: "async simulate_cost(skill_id: str, tenant_id: str, payload: Dict[str, Any]) -> Optional[int]"
    - name: check_policy_violations
      signature: "async check_policy_violations(skill_id: str, tenant_id: str, agent_id: Optional[str], payload: Dict[str, Any], simulated_cost: Optional[int]) -> List[PolicyViolation]"
    - name: evaluate_policy
      signature: "async evaluate_policy(skill_id: str, tenant_id: str, agent_id: Optional[str], payload: Dict[str, Any], auto_approve_max_cost_cents: int, approval_level: int) -> PolicyEvaluationResult"
    - name: record_approval_created
      signature: "record_approval_created(policy_type: str) -> None"
    - name: record_approval_outcome
      signature: "record_approval_outcome(result: str) -> None"
    - name: record_escalation
      signature: "record_escalation() -> None"
    - name: record_webhook_used
      signature: "record_webhook_used() -> None"
  classes:
    - name: PolicyViolation
      methods: []
    - name: PolicyEvaluationResult
      methods: []
    - name: ApprovalConfig
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
