# hoc_cus_integrations_L5_engines_prevention_contract

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/prevention_contract.py` |
| Layer | L5 — Domain Engine |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Prevention contract enforcement (validation logic)

## Intent

**Role:** Prevention contract enforcement (validation logic)
**Reference:** PIN-470, HOC_LAYER_TOPOLOGY_V1.md, INTEGRATIONS_PHASE2.5_IMPLEMENTATION_PLAN.md
**Callers:** policy engine, workers

## Purpose

M25 Prevention Contract Enforcement

---

## Functions

### `validate_prevention_candidate(candidate: PreventionCandidate) -> None`
- **Async:** No
- **Docstring:** Validate that a prevention candidate satisfies the contract.  Raises PreventionContractViolation if any rule is violated.
- **Calls:** PreventionContractViolation, info

### `assert_prevention_immutable(record_id: str, existing_record: dict[str, Any]) -> None`
- **Async:** No
- **Docstring:** Assert that a prevention record has not been modified.  Prevention records are append-only and immutable.
- **Calls:** PreventionContractViolation

### `assert_no_deletion(record_id: str) -> None`
- **Async:** No
- **Docstring:** Assert that a prevention record cannot be deleted.  Prevention records are append-only and immutable.
- **Calls:** PreventionContractViolation

### `validate_prevention_for_graduation(prevention_record: dict[str, Any], policy_activated_at: datetime) -> bool`
- **Async:** No
- **Docstring:** Validate that a prevention record counts toward graduation.  For Gate 1 (Prevention) to pass:
- **Calls:** debug, get, info, isinstance, replace

## Classes

### `PreventionContractViolation(Exception)`
- **Docstring:** Raised when a prevention record would violate the contract.
- **Methods:** __init__

### `PreventionCandidate`
- **Docstring:** Candidate for prevention record creation.
- **Class Variables:** policy_id: str, pattern_id: str, tenant_id: str, blocked_incident_id: str, original_incident_id: str, signature_match_confidence: float, policy_mode: str, pattern_signature: dict[str, Any], request_signature: dict[str, Any], incident_created: bool, is_simulated: bool

## Attributes

- `logger` (line 48)
- `PREVENTION_CONTRACT_VERSION` (line 51)
- `PREVENTION_CONTRACT_FROZEN_AT` (line 52)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__` |

## Callers

policy engine, workers

## Export Contract

```yaml
exports:
  functions:
    - name: validate_prevention_candidate
      signature: "validate_prevention_candidate(candidate: PreventionCandidate) -> None"
    - name: assert_prevention_immutable
      signature: "assert_prevention_immutable(record_id: str, existing_record: dict[str, Any]) -> None"
    - name: assert_no_deletion
      signature: "assert_no_deletion(record_id: str) -> None"
    - name: validate_prevention_for_graduation
      signature: "validate_prevention_for_graduation(prevention_record: dict[str, Any], policy_activated_at: datetime) -> bool"
  classes:
    - name: PreventionContractViolation
      methods: []
    - name: PreventionCandidate
      methods: []
```

## PIN-520 Dead Code Rewiring Updates

- **Change Date:** 2026-02-03
- **Change Type:** Documentation — Dead Code Rewiring
- **Details:** Wired `existing_record` parameter during PIN-520 phase 3 dead code rewiring
- **Impact:** No code changes; enhanced documentation of existing parameter

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
