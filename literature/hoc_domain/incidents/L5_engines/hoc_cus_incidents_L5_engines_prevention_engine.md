# hoc_cus_incidents_L5_engines_prevention_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/incidents/L5_engines/prevention_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | incidents |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Prevention-based policy validation

## Intent

**Role:** Prevention-based policy validation
**Reference:** PIN-470, Policy System
**Callers:** policy/engine, workers

## Purpose

_No module docstring._

---

## Functions

### `get_prevention_engine() -> PreventionEngine`
- **Async:** No
- **Docstring:** Get global prevention engine instance.
- **Calls:** PreventionEngine

### `evaluate_prevention(tenant_id: str, call_id: str, user_query: str, llm_output: str, context_data: Dict[str, Any], model: str, user_id: Optional[str]) -> PreventionResult`
- **Async:** No
- **Docstring:** Convenience function to evaluate prevention.  Usage:
- **Calls:** PreventionContext, evaluate, get_prevention_engine

### `async create_incident_from_violation(ctx: PreventionContext, result: PreventionResult, session: Optional[Any]) -> Optional[str]`
- **Async:** Yes
- **Docstring:** Create an incident from prevention violation.  S3 Truth Model (PIN-195):
- **Calls:** AsyncSessionLocal, _create_incident_with_service, getLogger, isoformat, items, list, str, warning

### `async _create_incident_with_service(session: Any, ctx: PreventionContext, primary: PolicyViolation, evidence: dict) -> Optional[str]`
- **Async:** Yes
- **Docstring:** Helper to create incident using PolicyViolationService.
- **Calls:** PolicyViolationService, ViolationFact, persist_violation_and_create_incident

## Classes

### `PolicyType(str, Enum)`
- **Docstring:** Types of policies that can be evaluated.

### `Severity(str, Enum)`
- **Docstring:** Severity levels for policy violations.

### `PreventionAction(str, Enum)`
- **Docstring:** Action to take when prevention triggers.

### `PolicyViolation`
- **Docstring:** A single policy violation detected.
- **Methods:** to_dict
- **Class Variables:** policy: PolicyType, severity: Severity, rule_id: str, reason: str, evidence: Dict[str, Any], field_name: Optional[str], expected_behavior: Optional[str], actual_behavior: Optional[str], confidence: float

### `PreventionContext`
- **Docstring:** Context for prevention evaluation.
- **Methods:** hash_output
- **Class Variables:** tenant_id: str, call_id: str, user_query: str, llm_output: str, context_data: Dict[str, Any], model: str, user_id: Optional[str], system_prompt: Optional[str], output_tokens: int, input_tokens: int, cost_usd: float, timestamp: datetime

### `PreventionResult`
- **Docstring:** Result of prevention engine evaluation.
- **Methods:** highest_severity, primary_violation, to_dict
- **Class Variables:** action: PreventionAction, violations: List[PolicyViolation], passed_policies: List[PolicyType], modified_output: Optional[str], safe_output: Optional[str], would_prevent: bool, evaluation_id: str, evaluation_ms: int, timestamp: datetime

### `BaseValidator`
- **Docstring:** Base class for policy validators.
- **Methods:** validate
- **Class Variables:** policy_type: PolicyType, default_severity: Severity

### `ContentAccuracyValidatorV2(BaseValidator)`
- **Docstring:** Enhanced content accuracy validator.
- **Methods:** __init__, validate, _get_value, _extract_claim

### `PIIValidator(BaseValidator)`
- **Docstring:** Detects PII in LLM output that shouldn't be exposed.
- **Methods:** __init__, validate, _redact

### `SafetyValidator(BaseValidator)`
- **Docstring:** Detects harmful, dangerous, or inappropriate content.
- **Methods:** __init__, validate

### `HallucinationValidator(BaseValidator)`
- **Docstring:** Detects potential hallucinations by checking for unsupported claims.
- **Methods:** __init__, validate, _claim_in_context

### `BudgetValidator(BaseValidator)`
- **Docstring:** Validates that response doesn't exceed budget limits.
- **Methods:** __init__, validate

### `PreventionEngine`
- **Docstring:** Multi-policy prevention engine with severity levels and async incident creation.
- **Methods:** __init__, evaluate, _generate_safe_response, _emit_metrics

## Attributes

- `_engine: Optional[PreventionEngine]` (line 731)
- `__all__` (line 873)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L5 Engine | `app.hoc.cus.incidents.L5_engines.policy_violation_service` |
| External | `app.db_async`, `prometheus_client` |

## Callers

policy/engine, workers

## Export Contract

```yaml
exports:
  functions:
    - name: get_prevention_engine
      signature: "get_prevention_engine() -> PreventionEngine"
    - name: evaluate_prevention
      signature: "evaluate_prevention(tenant_id: str, call_id: str, user_query: str, llm_output: str, context_data: Dict[str, Any], model: str, user_id: Optional[str]) -> PreventionResult"
    - name: create_incident_from_violation
      signature: "async create_incident_from_violation(ctx: PreventionContext, result: PreventionResult, session: Optional[Any]) -> Optional[str]"
  classes:
    - name: PolicyType
      methods: []
    - name: Severity
      methods: []
    - name: PreventionAction
      methods: []
    - name: PolicyViolation
      methods: [to_dict]
    - name: PreventionContext
      methods: [hash_output]
    - name: PreventionResult
      methods: [highest_severity, primary_violation, to_dict]
    - name: BaseValidator
      methods: [validate]
    - name: ContentAccuracyValidatorV2
      methods: [validate]
    - name: PIIValidator
      methods: [validate]
    - name: SafetyValidator
      methods: [validate]
    - name: HallucinationValidator
      methods: [validate]
    - name: BudgetValidator
      methods: [validate]
    - name: PreventionEngine
      methods: [evaluate]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
