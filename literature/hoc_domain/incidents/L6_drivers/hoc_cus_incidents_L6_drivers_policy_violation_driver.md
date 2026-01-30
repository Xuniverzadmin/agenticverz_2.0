# hoc_cus_incidents_L6_drivers_policy_violation_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/incidents/L6_drivers/policy_violation_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | incidents |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Data access for policy violation operations (async + sync)

## Intent

**Role:** Data access for policy violation operations (async + sync)
**Reference:** PIN-470, PIN-468, PHASE2_EXTRACTION_PROTOCOL.md
**Callers:** PolicyViolationEngine (L5)

## Purpose

Policy Violation Driver (L6)

---

## Functions

### `insert_policy_evaluation_sync(database_url: str, evaluation_id: str, run_id: str, tenant_id: str, outcome: str, policies_checked: int, confidence: float, created_at: datetime, is_synthetic: bool, synthetic_scenario_id: Optional[str]) -> Optional[str]`
- **Async:** No
- **Docstring:** Insert policy evaluation record using sync psycopg2 connection.  This is used in worker contexts where async is not available.
- **Calls:** close, commit, connect, cursor, error, execute, fetchone

### `get_policy_violation_driver(session: AsyncSession) -> PolicyViolationDriver`
- **Async:** No
- **Docstring:** Factory function to get PolicyViolationDriver instance.
- **Calls:** PolicyViolationDriver

## Classes

### `PolicyViolationDriver`
- **Docstring:** L6 driver for policy violation operations (async).
- **Methods:** __init__, insert_violation_record, fetch_violation_exists, fetch_policy_enabled, insert_evidence_event, fetch_incident_by_violation, fetch_violation_truth_check, insert_policy_evaluation

## Attributes

- `logger` (line 79)
- `__all__` (line 486)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `psycopg2`, `sqlalchemy`, `sqlalchemy.ext.asyncio` |

## Callers

PolicyViolationEngine (L5)

## Export Contract

```yaml
exports:
  functions:
    - name: insert_policy_evaluation_sync
      signature: "insert_policy_evaluation_sync(database_url: str, evaluation_id: str, run_id: str, tenant_id: str, outcome: str, policies_checked: int, confidence: float, created_at: datetime, is_synthetic: bool, synthetic_scenario_id: Optional[str]) -> Optional[str]"
    - name: get_policy_violation_driver
      signature: "get_policy_violation_driver(session: AsyncSession) -> PolicyViolationDriver"
  classes:
    - name: PolicyViolationDriver
      methods: [insert_violation_record, fetch_violation_exists, fetch_policy_enabled, insert_evidence_event, fetch_incident_by_violation, fetch_violation_truth_check, insert_policy_evaluation]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
