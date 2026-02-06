# hoc_cus_logs_L5_support_audit_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L5_support/CRM/engines/audit_engine.py` |
| Layer | L8 — Catalyst / Verification |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Audit Engine - verifies job execution against contract intent

## Intent

**Role:** Audit Engine - verifies job execution against contract intent
**Reference:** GOVERNANCE_AUDIT_MODEL.md, part2-design-v1
**Callers:** GovernanceOrchestrator (via AuditTrigger)

## Purpose

Part-2 Governance Audit Service (L8)

---

## Functions

### `audit_result_to_record(result: AuditResult) -> dict[str, Any]`
- **Async:** No
- **Docstring:** Convert AuditResult to database record format.  This is what gets persisted.
- **Calls:** isoformat, str

### `create_audit_input_from_evidence(job_id: UUID, contract_id: UUID, job_status: str, contract_scope: list[str], proposed_changes: dict[str, Any], execution_result: dict[str, Any], activation_window_start: Optional[datetime], activation_window_end: Optional[datetime]) -> AuditInput`
- **Async:** No
- **Docstring:** Create AuditInput from job execution evidence.  Helper to transform evidence into audit-ready format.
- **Calls:** AuditInput, fromisoformat, get, now, replace

## Classes

### `CheckResult(str, Enum)`
- **Docstring:** Result of an individual audit check.

### `AuditCheck`
- **Docstring:** Result of a single audit check.
- **Class Variables:** check_id: str, name: str, question: str, result: CheckResult, reason: str, evidence: dict[str, Any]

### `AuditInput`
- **Docstring:** Input to the audit process.
- **Class Variables:** job_id: UUID, contract_id: UUID, job_status: str, contract_scope: list[str], proposed_changes: dict[str, Any], steps_executed: list[dict[str, Any]], step_results: list[dict[str, Any]], health_before: Optional[dict[str, Any]], health_after: Optional[dict[str, Any]], activation_window_start: Optional[datetime], activation_window_end: Optional[datetime], job_started_at: datetime, job_completed_at: datetime, execution_duration_seconds: float

### `AuditResult`
- **Docstring:** Complete audit result with all checks and final verdict.
- **Class Variables:** audit_id: UUID, job_id: UUID, contract_id: UUID, verdict: AuditVerdict, verdict_reason: str, checks: tuple[AuditCheck, ...], checks_passed: int, checks_failed: int, checks_inconclusive: int, evidence_summary: dict[str, Any], health_snapshot_before: Optional[dict[str, Any]], health_snapshot_after: Optional[dict[str, Any]], audited_at: datetime, duration_ms: int, auditor_version: str

### `AuditChecks`
- **Docstring:** Individual audit check implementations.
- **Methods:** check_scope_compliance, check_health_preservation, _is_health_degraded, check_execution_fidelity, check_timing_compliance, check_rollback_availability, check_signal_consistency, check_no_unauthorized_mutations

### `AuditService`
- **Docstring:** Part-2 Governance Audit Service (L8)
- **Methods:** __init__, version, audit, _run_all_checks, _determine_verdict

### `RolloutGate`
- **Docstring:** Gate that determines if rollout is authorized.
- **Methods:** is_rollout_authorized, get_rollout_status

## Attributes

- `AUDIT_SERVICE_VERSION` (line 67)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.contract` |

## Callers

GovernanceOrchestrator (via AuditTrigger)

## Export Contract

```yaml
exports:
  functions:
    - name: audit_result_to_record
      signature: "audit_result_to_record(result: AuditResult) -> dict[str, Any]"
    - name: create_audit_input_from_evidence
      signature: "create_audit_input_from_evidence(job_id: UUID, contract_id: UUID, job_status: str, contract_scope: list[str], proposed_changes: dict[str, Any], execution_result: dict[str, Any], activation_window_start: Optional[datetime], activation_window_end: Optional[datetime]) -> AuditInput"
  classes:
    - name: CheckResult
      methods: []
    - name: AuditCheck
      methods: []
    - name: AuditInput
      methods: []
    - name: AuditResult
      methods: []
    - name: AuditChecks
      methods: [check_scope_compliance, check_health_preservation, check_execution_fidelity, check_timing_compliance, check_rollback_availability, check_signal_consistency, check_no_unauthorized_mutations]
    - name: AuditService
      methods: [version, audit]
    - name: RolloutGate
      methods: [is_rollout_authorized, get_rollout_status]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
