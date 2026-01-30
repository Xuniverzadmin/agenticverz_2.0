# hoc_cus_incidents_L5_engines_policy_violation_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/incidents/L5_engines/policy_violation_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | incidents |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

S3 violation truth model, fact persistence, evidence linking

## Intent

**Role:** S3 violation truth model, fact persistence, evidence linking
**Reference:** PIN-470, PIN-242 (Baseline Freeze), PIN-468, PHASE2_EXTRACTION_PROTOCOL.md
**Callers:** L5 policy engine, L5 workers

## Purpose

Policy Violation Service - S3 Hardening for Phase A.5 Verification

---

## Functions

### `async create_policy_evaluation_record(session: 'AsyncSession', run_id: str, tenant_id: str, outcome: str, policies_checked: int, reason: str, draft_candidate: bool, is_synthetic: bool, synthetic_scenario_id: Optional[str]) -> str`
- **Async:** Yes
- **Docstring:** Create a policy evaluation record for ANY run (PIN-407).  Every run MUST produce exactly one policy evaluation record.
- **Calls:** generate_uuid, get_policy_violation_driver, info, insert_policy_evaluation, now

### `async handle_policy_evaluation_for_run(session: 'AsyncSession', run_id: str, tenant_id: str, run_status: str, policies_checked: int, is_synthetic: bool, synthetic_scenario_id: Optional[str]) -> str`
- **Async:** Yes
- **Docstring:** Create a policy evaluation record for ANY run (PIN-407).  This is the NEW primary entry point for run → policy evaluation propagation.
- **Calls:** create_policy_evaluation_record, lower

### `async handle_policy_violation(session: 'AsyncSession', run_id: str, tenant_id: str, policy_type: str, policy_id: str, violated_rule: str, reason: str, severity: str, evidence: Optional[Dict[str, Any]]) -> Optional[ViolationIncident]`
- **Async:** Yes
- **Docstring:** Handle a policy violation with S3 truth guarantees.  This is the main entry point for policy violation handling.
- **Calls:** PolicyViolationService, ViolationFact, persist_violation_and_create_incident

### `create_policy_evaluation_sync(run_id: str, tenant_id: str, run_status: str, policies_checked: int, is_synthetic: bool, synthetic_scenario_id: Optional[str]) -> Optional[str]`
- **Async:** No
- **Docstring:** Create a policy evaluation record for ANY run (PIN-407) - SYNC VERSION.  This is a synchronous wrapper for use in worker contexts where we don't
- **Calls:** debug, error, generate_uuid, getenv, info, insert_policy_evaluation_sync, lower, now

## Classes

### `ViolationFact`
- **Docstring:** Authoritative violation fact - must be persisted before incident creation.
- **Class Variables:** id: str, run_id: str, tenant_id: str, policy_id: str, policy_type: str, violated_rule: str, evaluated_value: str, threshold_condition: str, severity: str, reason: str, evidence: Dict[str, Any], timestamp: datetime, persisted: bool

### `ViolationIncident`
- **Docstring:** Result of creating an incident from a violation.
- **Class Variables:** incident_id: str, violation_id: str, evidence_id: Optional[str], persisted: bool

### `PolicyViolationService`
- **Docstring:** Service for handling policy violations with S3 truth guarantees.
- **Methods:** __init__, persist_violation_fact, check_violation_persisted, check_policy_enabled, persist_evidence, check_incident_exists, create_incident_from_violation, persist_violation_and_create_incident, verify_violation_truth

### `PolicyEvaluationResult`
- **Docstring:** Result of policy evaluation (PIN-407: Success as First-Class Data).
- **Class Variables:** id: str, run_id: str, tenant_id: str, outcome: str, policies_checked: int, reason: str, timestamp: datetime, draft_candidate: bool

## Attributes

- `logger` (line 78)
- `VERIFICATION_MODE` (line 81)
- `POLICY_OUTCOME_NO_VIOLATION` (line 443)
- `POLICY_OUTCOME_VIOLATION` (line 444)
- `POLICY_OUTCOME_ADVISORY` (line 445)
- `POLICY_OUTCOME_NOT_APPLICABLE` (line 446)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.incidents.L6_drivers.incident_aggregator`, `app.hoc.cus.incidents.L6_drivers.policy_violation_driver` |
| External | `app.db`, `app.utils.runtime`, `sqlalchemy.ext.asyncio`, `sqlmodel` |

## Callers

L5 policy engine, L5 workers

## Export Contract

```yaml
exports:
  functions:
    - name: create_policy_evaluation_record
      signature: "async create_policy_evaluation_record(session: 'AsyncSession', run_id: str, tenant_id: str, outcome: str, policies_checked: int, reason: str, draft_candidate: bool, is_synthetic: bool, synthetic_scenario_id: Optional[str]) -> str"
    - name: handle_policy_evaluation_for_run
      signature: "async handle_policy_evaluation_for_run(session: 'AsyncSession', run_id: str, tenant_id: str, run_status: str, policies_checked: int, is_synthetic: bool, synthetic_scenario_id: Optional[str]) -> str"
    - name: handle_policy_violation
      signature: "async handle_policy_violation(session: 'AsyncSession', run_id: str, tenant_id: str, policy_type: str, policy_id: str, violated_rule: str, reason: str, severity: str, evidence: Optional[Dict[str, Any]]) -> Optional[ViolationIncident]"
    - name: create_policy_evaluation_sync
      signature: "create_policy_evaluation_sync(run_id: str, tenant_id: str, run_status: str, policies_checked: int, is_synthetic: bool, synthetic_scenario_id: Optional[str]) -> Optional[str]"
  classes:
    - name: ViolationFact
      methods: []
    - name: ViolationIncident
      methods: []
    - name: PolicyViolationService
      methods: [persist_violation_fact, check_violation_persisted, check_policy_enabled, persist_evidence, check_incident_exists, create_incident_from_violation, persist_violation_and_create_incident, verify_violation_truth]
    - name: PolicyEvaluationResult
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
