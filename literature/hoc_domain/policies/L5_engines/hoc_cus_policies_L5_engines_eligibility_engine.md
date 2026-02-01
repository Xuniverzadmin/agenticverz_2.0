# hoc_cus_policies_L5_engines_eligibility_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/eligibility_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Eligibility Engine - pure rules, deterministic gating

## Intent

**Role:** Eligibility Engine - pure rules, deterministic gating
**Reference:** ELIGIBILITY_RULES.md (frozen), part2-design-v1
**Callers:** L3 (adapters), L2 (governance APIs)

## Purpose

Part-2 Eligibility Engine (L4)

---

## Classes

### `EligibilityDecision(str, Enum)`
- **Docstring:** Binary eligibility decision.

### `SystemHealthStatus(str, Enum)`
- **Docstring:** System health status for E-104 rule.

### `EligibilityConfig`
- **Docstring:** Eligibility engine configuration.
- **Class Variables:** confidence_threshold: Decimal, minimum_confidence: Decimal, allowed_sources: tuple[str, ...], actionable_types: tuple[IssueType, ...], duplicate_window_hours: int, rules_version: str

### `CapabilityLookup(Protocol)`
- **Docstring:** Protocol for capability registry lookups.
- **Methods:** exists, is_frozen

### `GovernanceSignalLookup(Protocol)`
- **Docstring:** Protocol for governance signal lookups.
- **Methods:** has_blocking_signal

### `SystemHealthLookup(Protocol)`
- **Docstring:** Protocol for system health lookups.
- **Methods:** get_status

### `ContractLookup(Protocol)`
- **Docstring:** Protocol for contract lookups.
- **Methods:** has_similar_pending

### `PreApprovalLookup(Protocol)`
- **Docstring:** Protocol for pre-approval lookups.
- **Methods:** has_system_pre_approval

### `DefaultCapabilityLookup`
- **Docstring:** Default capability lookup using provided registry.
- **Methods:** __init__, exists, is_frozen

### `DefaultGovernanceSignalLookup`
- **Docstring:** Default governance signal lookup with no blocking signals.
- **Methods:** __init__, has_blocking_signal

### `DefaultSystemHealthLookup`
- **Docstring:** Default system health lookup returning HEALTHY.
- **Methods:** __init__, get_status

### `DefaultContractLookup`
- **Docstring:** Default contract lookup with no pending contracts.
- **Methods:** __init__, has_similar_pending

### `DefaultPreApprovalLookup`
- **Docstring:** Default pre-approval lookup with no pre-approvals.
- **Methods:** __init__, has_system_pre_approval

### `EligibilityInput`
- **Docstring:** Input to the eligibility engine.
- **Class Variables:** proposal_id: UUID, validator_verdict: ValidatorVerdict, source: str, affected_capabilities: tuple[str, ...], received_at: datetime, tenant_id: Optional[UUID]

### `RuleResult`
- **Docstring:** Result of evaluating a single rule.
- **Class Variables:** rule_id: str, rule_name: str, passed: bool, reason: str, evidence: dict[str, Any]

### `EligibilityVerdict`
- **Docstring:** Output from the eligibility engine.
- **Class Variables:** decision: EligibilityDecision, reason: str, rules_evaluated: int, first_failing_rule: Optional[str], blocking_signals: tuple[str, ...], missing_prerequisites: tuple[str, ...], evaluated_at: datetime, rules_version: str, rule_results: tuple[RuleResult, ...]

### `EligibilityEngine`
- **Docstring:** Part-2 Eligibility Engine (L4)
- **Methods:** __init__, evaluate, _evaluate_e104_health_degraded, _evaluate_e100_below_minimum_confidence, _evaluate_e101_critical_without_escalation, _evaluate_e102_frozen_capability, _evaluate_e103_system_scope_without_preapproval, _evaluate_e001_confidence_threshold, _evaluate_e002_known_capability, _evaluate_e003_no_blocking_signal, _evaluate_e004_actionable_type, _evaluate_e005_source_allowlist, _evaluate_e006_not_duplicate, _create_verdict

## Attributes

- `ELIGIBILITY_ENGINE_VERSION` (line 86)
- `DEFAULT_ELIGIBILITY_CONFIG` (line 149)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.hoc.cus.hoc_spine.orchestrator` |

## Callers

L3 (adapters), L2 (governance APIs)

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: EligibilityDecision
      methods: []
    - name: SystemHealthStatus
      methods: []
    - name: EligibilityConfig
      methods: []
    - name: CapabilityLookup
      methods: [exists, is_frozen]
    - name: GovernanceSignalLookup
      methods: [has_blocking_signal]
    - name: SystemHealthLookup
      methods: [get_status]
    - name: ContractLookup
      methods: [has_similar_pending]
    - name: PreApprovalLookup
      methods: [has_system_pre_approval]
    - name: DefaultCapabilityLookup
      methods: [exists, is_frozen]
    - name: DefaultGovernanceSignalLookup
      methods: [has_blocking_signal]
    - name: DefaultSystemHealthLookup
      methods: [get_status]
    - name: DefaultContractLookup
      methods: [has_similar_pending]
    - name: DefaultPreApprovalLookup
      methods: [has_system_pre_approval]
    - name: EligibilityInput
      methods: []
    - name: RuleResult
      methods: []
    - name: EligibilityVerdict
      methods: []
    - name: EligibilityEngine
      methods: [evaluate]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
