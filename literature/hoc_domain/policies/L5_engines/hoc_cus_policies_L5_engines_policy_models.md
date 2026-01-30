# hoc_cus_policies_L5_engines_policy_models

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/policy_models.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy domain models and types

## Intent

**Role:** Policy domain models and types
**Reference:** PIN-470, Policy System
**Callers:** policy/*

## Purpose

_No module docstring._

---

## Classes

### `PolicyCategory(str, Enum)`
- **Docstring:** Categories of policies in the M19 Policy Layer.

### `PolicyDecision(str, Enum)`
- **Docstring:** Possible decisions from policy evaluation.

### `ActionType(str, Enum)`
- **Docstring:** Types of actions that require policy evaluation.

### `ViolationType(str, Enum)`
- **Docstring:** Types of policy violations.

### `ViolationSeverity(str, Enum)`
- **Docstring:** Enhanced violation severity classifications (GAP 5).

### `RecoverabilityType(str, Enum)`
- **Docstring:** Whether a violation is recoverable.

### `SafetyRuleType(str, Enum)`
- **Docstring:** Types of safety rules.

### `EthicalConstraintType(str, Enum)`
- **Docstring:** Types of ethical constraints.

### `BusinessRuleType(str, Enum)`
- **Docstring:** Types of business rules.

### `PolicyEvaluationRequest(BaseModel)`
- **Docstring:** Request for policy evaluation.
- **Class Variables:** action_type: ActionType, agent_id: Optional[str], tenant_id: Optional[str], context: Dict[str, Any], proposed_action: Optional[str], target_resource: Optional[str], estimated_cost: Optional[float], data_categories: Optional[List[str]], external_endpoints: Optional[List[str]], current_sba: Optional[Dict[str, Any]], proposed_modification: Optional[Dict[str, Any]], request_id: str, timestamp: datetime

### `PolicyModification(BaseModel)`
- **Docstring:** Modification applied to an action by policy engine.
- **Class Variables:** parameter: str, original_value: Any, modified_value: Any, reason: str

### `PolicyEvaluationResult(BaseModel)`
- **Docstring:** Result of policy evaluation.
- **Class Variables:** request_id: str, decision: PolicyDecision, decision_reason: Optional[str], policies_evaluated: int, rules_matched: List[str], evaluation_ms: float, modifications: List[PolicyModification], violations: List['PolicyViolation'], evaluated_at: datetime, policy_version: Optional[str]

### `PolicyViolation(BaseModel)`
- **Docstring:** A policy violation record.
- **Class Variables:** id: str, violation_type: ViolationType, policy_name: str, severity: float, description: str, evidence: Dict[str, Any], agent_id: Optional[str], tenant_id: Optional[str], action_attempted: Optional[str], routed_to_governor: bool, governor_action: Optional[str], detected_at: datetime

### `PolicyRule(BaseModel)`
- **Docstring:** A single rule within a policy.
- **Class Variables:** name: str, condition: Dict[str, Any], action: PolicyDecision, modification: Optional[Dict[str, Any]], priority: int

### `Policy(BaseModel)`
- **Docstring:** A policy definition.
- **Class Variables:** id: str, name: str, category: PolicyCategory, description: Optional[str], rules: List[PolicyRule], version: int, is_active: bool, supersedes_id: Optional[str], applies_to: Optional[List[str]], tenant_id: Optional[str], priority: int, created_at: datetime, effective_from: Optional[datetime], effective_until: Optional[datetime]

### `RiskCeiling(BaseModel)`
- **Docstring:** A risk ceiling definition.
- **Class Variables:** id: str, name: str, description: Optional[str], metric: str, max_value: float, current_value: float, window_seconds: int, applies_to: Optional[List[str]], tenant_id: Optional[str], breach_action: str, breach_count: int, last_breach_at: Optional[datetime], is_active: bool

### `SafetyRule(BaseModel)`
- **Docstring:** A safety rule definition.
- **Class Variables:** id: str, name: str, description: Optional[str], rule_type: SafetyRuleType, condition: Dict[str, Any], action: str, cooldown_seconds: Optional[int], applies_to: Optional[List[str]], tenant_id: Optional[str], priority: int, is_active: bool, triggered_count: int, last_triggered_at: Optional[datetime]

### `EthicalConstraint(BaseModel)`
- **Docstring:** An ethical constraint definition.
- **Class Variables:** id: str, name: str, description: str, constraint_type: EthicalConstraintType, forbidden_patterns: Optional[List[str]], required_disclosures: Optional[List[str]], transparency_threshold: Optional[float], enforcement_level: str, violation_action: str, is_active: bool, violated_count: int, last_violated_at: Optional[datetime]

### `BusinessRule(BaseModel)`
- **Docstring:** A business rule definition.
- **Class Variables:** id: str, name: str, description: Optional[str], rule_type: BusinessRuleType, condition: Dict[str, Any], constraint: Dict[str, Any], tenant_id: Optional[str], customer_tier: Optional[str], priority: int, is_active: bool

### `PolicyState(BaseModel)`
- **Docstring:** Current state of the policy layer.
- **Class Variables:** total_policies: int, active_policies: int, total_evaluations_today: int, total_violations_today: int, block_rate: float, compliance_violations: int, ethical_violations: int, risk_breaches: int, safety_triggers: int, business_violations: int, risk_ceilings_active: int, risk_ceilings_breached: int, evaluated_at: datetime

### `PolicyLoadResult(BaseModel)`
- **Docstring:** Result of loading policies from database.
- **Class Variables:** policies_loaded: int, risk_ceilings_loaded: int, safety_rules_loaded: int, ethical_constraints_loaded: int, business_rules_loaded: int, temporal_policies_loaded: int, errors: List[str], loaded_at: datetime

### `PolicyVersion(BaseModel)`
- **Docstring:** A versioned snapshot of a policy set (GAP 1).
- **Class Variables:** id: str, version: str, policy_hash: str, signature: Optional[str], created_by: str, created_at: datetime, description: Optional[str], policies_snapshot: Dict[str, Any], risk_ceilings_snapshot: Dict[str, Any], safety_rules_snapshot: Dict[str, Any], ethical_constraints_snapshot: Dict[str, Any], business_rules_snapshot: Dict[str, Any], temporal_policies_snapshot: Dict[str, Any], parent_version: Optional[str], is_active: bool, rolled_back_at: Optional[datetime], rolled_back_by: Optional[str]

### `PolicyProvenance(BaseModel)`
- **Docstring:** Audit trail for policy changes (GAP 1).
- **Class Variables:** id: str, policy_id: str, policy_type: str, action: str, changed_by: str, changed_at: datetime, previous_value: Optional[Dict[str, Any]], new_value: Optional[Dict[str, Any]], policy_version: str, reason: Optional[str]

### `PolicyDependency(BaseModel)`
- **Docstring:** Dependency relationship between policies (GAP 2).
- **Class Variables:** id: str, source_policy: str, target_policy: str, dependency_type: str, resolution_strategy: str, priority: int, description: Optional[str], is_active: bool

### `PolicyConflict(BaseModel)`
- **Docstring:** A detected conflict between policies (GAP 2).
- **Class Variables:** id: str, policy_a: str, policy_b: str, conflict_type: str, severity: float, description: str, affected_action_types: List[ActionType], resolved: bool, resolution: Optional[str], resolved_by: Optional[str], resolved_at: Optional[datetime], detected_at: datetime

### `DependencyGraph(BaseModel)`
- **Docstring:** The complete policy dependency graph (GAP 2).
- **Class Variables:** nodes: Dict[str, Dict[str, Any]], edges: List[PolicyDependency], conflicts: List[PolicyConflict], computed_at: datetime

### `TemporalPolicyType(str, Enum)`
- **Docstring:** Types of temporal policies.

### `TemporalPolicy(BaseModel)`
- **Docstring:** A temporal/sliding window policy (GAP 3).
- **Class Variables:** id: str, name: str, description: Optional[str], temporal_type: TemporalPolicyType, metric: str, max_value: float, window_seconds: int, applies_to: Optional[List[str]], tenant_id: Optional[str], agent_id: Optional[str], breach_action: str, cooldown_on_breach: int, is_active: bool, breach_count: int, last_breach_at: Optional[datetime], created_at: datetime

### `TemporalMetricWindow(BaseModel)`
- **Docstring:** A sliding window of metric values (GAP 3).
- **Class Variables:** policy_id: str, agent_id: Optional[str], tenant_id: Optional[str], values: List[Dict[str, Any]], window_start: datetime, window_seconds: int, current_sum: float, current_count: int, current_max: float

### `PolicyContext(BaseModel)`
- **Docstring:** Complete policy context passed through the decision cycle (GAP 4).
- **Class Variables:** agent_id: Optional[str], agent_type: Optional[str], agent_capabilities: List[str], tenant_id: Optional[str], customer_tier: Optional[str], risk_state: Dict[str, float], risk_utilization: Dict[str, float], historical_violation_count: int, violation_types_24h: Dict[str, int], last_violation_at: Optional[datetime], is_quarantined: bool, quarantine_until: Optional[datetime], action_chain_depth: int, action_chain_ids: List[str], origin_trigger: Optional[str], root_agent_id: Optional[str], cumulative_cost_1h: float, cumulative_cost_24h: float, daily_budget_remaining: Optional[float], temporal_metrics: Dict[str, float], temporal_utilization: Dict[str, float], governing_policy_version: Optional[str], policy_hash: Optional[str], request_id: str, timestamp: datetime, prior_decisions: List[Dict[str, Any]]

### `EnhancedPolicyEvaluationRequest(BaseModel)`
- **Docstring:** Enhanced evaluation request with full context (GAP 4).
- **Class Variables:** action_type: ActionType, policy_context: PolicyContext, proposed_action: Optional[str], target_resource: Optional[str], estimated_cost: Optional[float], data_categories: Optional[List[str]], external_endpoints: Optional[List[str]], current_sba: Optional[Dict[str, Any]], proposed_modification: Optional[Dict[str, Any]], context: Dict[str, Any], request_id: str, timestamp: datetime

### `EnhancedPolicyViolation(BaseModel)`
- **Docstring:** Enhanced violation with severity classification (GAP 5).
- **Class Variables:** id: str, violation_type: ViolationType, policy_name: str, description: str, evidence: Dict[str, Any], severity: float, severity_class: ViolationSeverity, recoverability: RecoverabilityType, agent_id: Optional[str], tenant_id: Optional[str], action_attempted: Optional[str], action_chain_depth: int, routed_to_governor: bool, governor_action: Optional[str], recommended_action: Optional[str], is_temporal_violation: bool, temporal_window_seconds: Optional[int], temporal_metric_value: Optional[float], policy_version: Optional[str], detected_at: datetime

### `EnhancedPolicyEvaluationResult(BaseModel)`
- **Docstring:** Enhanced evaluation result with full context (GAPs 1-5).
- **Class Variables:** request_id: str, decision: PolicyDecision, decision_reason: Optional[str], policies_evaluated: int, temporal_policies_evaluated: int, dependencies_checked: int, rules_matched: List[str], evaluation_ms: float, modifications: List[PolicyModification], violations: List[EnhancedPolicyViolation], conflicts_detected: List[PolicyConflict], conflict_resolution_applied: Optional[str], temporal_utilization: Dict[str, float], temporal_warnings: List[str], policy_version: Optional[str], policy_hash: Optional[str], updated_context: Optional[PolicyContext], evaluated_at: datetime

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `pydantic` |

## Callers

policy/*

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: PolicyCategory
      methods: []
    - name: PolicyDecision
      methods: []
    - name: ActionType
      methods: []
    - name: ViolationType
      methods: []
    - name: ViolationSeverity
      methods: []
    - name: RecoverabilityType
      methods: []
    - name: SafetyRuleType
      methods: []
    - name: EthicalConstraintType
      methods: []
    - name: BusinessRuleType
      methods: []
    - name: PolicyEvaluationRequest
      methods: []
    - name: PolicyModification
      methods: []
    - name: PolicyEvaluationResult
      methods: []
    - name: PolicyViolation
      methods: []
    - name: PolicyRule
      methods: []
    - name: Policy
      methods: []
    - name: RiskCeiling
      methods: []
    - name: SafetyRule
      methods: []
    - name: EthicalConstraint
      methods: []
    - name: BusinessRule
      methods: []
    - name: PolicyState
      methods: []
    - name: PolicyLoadResult
      methods: []
    - name: PolicyVersion
      methods: []
    - name: PolicyProvenance
      methods: []
    - name: PolicyDependency
      methods: []
    - name: PolicyConflict
      methods: []
    - name: DependencyGraph
      methods: []
    - name: TemporalPolicyType
      methods: []
    - name: TemporalPolicy
      methods: []
    - name: TemporalMetricWindow
      methods: []
    - name: PolicyContext
      methods: []
    - name: EnhancedPolicyEvaluationRequest
      methods: []
    - name: EnhancedPolicyViolation
      methods: []
    - name: EnhancedPolicyEvaluationResult
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
