# hoc_cus_logs_L5_engines_logs_facade

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L5_engines/logs_facade.py` |
| Layer | L5 — Domain Engine |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Logs domain facade - unified entry point for all logs operations

## Intent

**Role:** Logs domain facade - unified entry point for all logs operations
**Reference:** PIN-470, HOC_LAYER_TOPOLOGY_V1.md, LOGS_PHASE2.5_IMPLEMENTATION_PLAN.md
**Callers:** L2 logs API, L3 adapters

## Purpose

Logs Domain Facade (L5)

---

## Functions

### `get_logs_facade() -> LogsFacade`
- **Async:** No
- **Docstring:** Get the singleton LogsFacade instance.
- **Calls:** LogsFacade

## Classes

### `SourceDomain(str, Enum)`
- **Docstring:** Source domain for evidence metadata.

### `Origin(str, Enum)`
- **Docstring:** Origin of the record.

### `EvidenceMetadataResult`
- **Docstring:** Global metadata contract for all Logs responses.
- **Class Variables:** tenant_id: str, run_id: Optional[str], human_actor_id: Optional[str], agent_id: Optional[str], system_id: Optional[str], occurred_at: datetime, recorded_at: datetime, timezone_str: str, trace_id: Optional[str], policy_ids: list[str], incident_ids: list[str], export_id: Optional[str], correlation_id: Optional[str], source_domain: str, source_component: str, origin: str, checksum: Optional[str], immutable: bool

### `LLMRunRecordResult`
- **Docstring:** Single LLM run record.
- **Class Variables:** id: str, run_id: str, trace_id: Optional[str], provider: str, model: str, input_tokens: int, output_tokens: int, cost_cents: int, execution_status: str, started_at: datetime, completed_at: Optional[datetime], source: str, is_synthetic: bool, created_at: datetime

### `LLMRunRecordsResult`
- **Docstring:** Response envelope for LLM run records.
- **Class Variables:** items: list[LLMRunRecordResult], total: int, has_more: bool, filters_applied: dict[str, Any]

### `TraceStepResult`
- **Docstring:** Individual trace step.
- **Class Variables:** step_index: int, timestamp: datetime, skill_name: str, status: str, outcome_category: str, cost_cents: int, duration_ms: int

### `LLMRunEnvelopeResult`
- **Docstring:** O1: Canonical immutable run record.
- **Class Variables:** id: str, run_id: str, trace_id: Optional[str], provider: str, model: str, input_tokens: int, output_tokens: int, cost_cents: int, execution_status: str, started_at: datetime, completed_at: Optional[datetime], source: str, is_synthetic: bool, created_at: datetime, metadata: EvidenceMetadataResult

### `LLMRunTraceResult`
- **Docstring:** O2: Step-by-step trace.
- **Class Variables:** run_id: str, trace_id: str, steps: list[TraceStepResult], total_steps: int, metadata: EvidenceMetadataResult

### `GovernanceEventResult`
- **Docstring:** Policy interaction event.
- **Class Variables:** timestamp: datetime, event_type: str, policy_id: Optional[str], rule_id: Optional[str], decision: str, entity_type: str, entity_id: str

### `LLMRunGovernanceResult`
- **Docstring:** O3: Policy interaction trace.
- **Class Variables:** run_id: str, events: list[GovernanceEventResult], total_events: int, metadata: EvidenceMetadataResult

### `ReplayEventResult`
- **Docstring:** Replay window event.
- **Class Variables:** source: str, timestamp: datetime, step_index: Optional[int], action: str, outcome: str

### `LLMRunReplayResult`
- **Docstring:** O4: 60-second replay window.
- **Class Variables:** run_id: str, inflection_timestamp: Optional[datetime], window_start: datetime, window_end: datetime, events: list[ReplayEventResult], metadata: EvidenceMetadataResult

### `LLMRunExportResult`
- **Docstring:** O5: Export metadata.
- **Class Variables:** run_id: str, available_formats: list[str], checksum: Optional[str], compliance_tags: list[str], metadata: EvidenceMetadataResult

### `SystemRecordResult`
- **Docstring:** Single system record entry.
- **Class Variables:** id: str, tenant_id: Optional[str], component: str, event_type: str, severity: str, summary: str, caused_by: Optional[str], correlation_id: Optional[str], created_at: datetime

### `SystemRecordsResult`
- **Docstring:** Response envelope for system records.
- **Class Variables:** items: list[SystemRecordResult], total: int, has_more: bool, filters_applied: dict[str, Any]

### `SystemSnapshotResult`
- **Docstring:** O1: Environment snapshot.
- **Class Variables:** run_id: str, component: str, event_type: str, severity: str, summary: str, details: Optional[dict[str, Any]], created_at: datetime, metadata: EvidenceMetadataResult

### `TelemetryStubResult`
- **Docstring:** O2: Telemetry stub response.
- **Class Variables:** status: str, reason: str, run_id: str, available_data: list[str], future_milestone: str

### `SystemEventResult`
- **Docstring:** System event record.
- **Class Variables:** id: str, component: str, event_type: str, severity: str, summary: str, caused_by: Optional[str], correlation_id: Optional[str], created_at: datetime

### `SystemEventsResult`
- **Docstring:** O3: Infra events affecting run.
- **Class Variables:** run_id: str, events: list[SystemEventResult], total_events: int, metadata: EvidenceMetadataResult

### `SystemReplayResult`
- **Docstring:** O4: Infra replay window.
- **Class Variables:** run_id: str, window_start: datetime, window_end: datetime, events: list[ReplayEventResult], metadata: EvidenceMetadataResult

### `SystemAuditResult`
- **Docstring:** O5: Infra attribution record.
- **Class Variables:** items: list[SystemEventResult], total: int, metadata: EvidenceMetadataResult

### `AuditLedgerItemResult`
- **Docstring:** Single audit ledger entry.
- **Class Variables:** id: str, event_type: str, entity_type: str, entity_id: str, actor_type: str, actor_id: Optional[str], action_reason: Optional[str], created_at: datetime

### `AuditLedgerDetailResult`
- **Docstring:** Audit ledger entry with state snapshots.
- **Class Variables:** id: str, event_type: str, entity_type: str, entity_id: str, actor_type: str, actor_id: Optional[str], action_reason: Optional[str], created_at: datetime, before_state: Optional[dict[str, Any]], after_state: Optional[dict[str, Any]], correlation_id: Optional[str]

### `AuditLedgerListResult`
- **Docstring:** Response envelope for audit ledger.
- **Class Variables:** items: list[AuditLedgerItemResult], total: int, has_more: bool, filters_applied: dict[str, Any]

### `IdentityEventResult`
- **Docstring:** Identity lifecycle event.
- **Class Variables:** id: str, event_type: str, actor_type: str, actor_id: Optional[str], created_at: datetime

### `AuditIdentityResult`
- **Docstring:** O1: Identity lifecycle.
- **Class Variables:** events: list[IdentityEventResult], total: int, metadata: EvidenceMetadataResult

### `AuthorizationDecisionResult`
- **Docstring:** Authorization decision record.
- **Class Variables:** id: str, event_type: str, entity_type: str, entity_id: str, actor_type: str, decision: str, created_at: datetime

### `AuditAuthorizationResult`
- **Docstring:** O2: Access decisions.
- **Class Variables:** decisions: list[AuthorizationDecisionResult], total: int, metadata: EvidenceMetadataResult

### `AccessEventResult`
- **Docstring:** Log access event.
- **Class Variables:** id: str, event_type: str, actor_type: str, actor_id: Optional[str], entity_type: str, entity_id: str, created_at: datetime

### `AuditAccessResult`
- **Docstring:** O3: Log access audit.
- **Class Variables:** events: list[AccessEventResult], total: int, metadata: EvidenceMetadataResult

### `IntegrityCheckResult`
- **Docstring:** Integrity verification record.
- **Class Variables:** status: str, last_verified: datetime, anomalies_detected: int, hash_chain_valid: bool

### `AuditIntegrityResult`
- **Docstring:** O4: Tamper detection.
- **Class Variables:** integrity: IntegrityCheckResult, metadata: EvidenceMetadataResult

### `ExportRecordResult`
- **Docstring:** Export record.
- **Class Variables:** id: str, scope: str, format: str, requested_by: str, status: str, checksum: Optional[str], created_at: datetime, delivered_at: Optional[datetime]

### `AuditExportsResult`
- **Docstring:** O5: Compliance exports.
- **Class Variables:** exports: list[ExportRecordResult], total: int, metadata: EvidenceMetadataResult

### `LogsFacade`
- **Docstring:** Unified facade for all Logs domain operations.
- **Methods:** __init__, list_llm_run_records, get_llm_run_envelope, get_llm_run_trace, get_llm_run_governance, get_llm_run_replay, get_llm_run_export, list_system_records, get_system_snapshot, get_system_telemetry, get_system_events, get_system_replay, get_system_audit, list_audit_entries, get_audit_entry, get_audit_identity, get_audit_authorization, get_audit_access, get_audit_integrity, get_audit_exports, _snapshot_to_record_result

## Attributes

- `_facade_instance: LogsFacade | None` (line 1353)
- `__all__` (line 1364)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.logs.L6_drivers.logs_domain_store` |

## Callers

L2 logs API, L3 adapters

## Export Contract

```yaml
exports:
  functions:
    - name: get_logs_facade
      signature: "get_logs_facade() -> LogsFacade"
  classes:
    - name: SourceDomain
      methods: []
    - name: Origin
      methods: []
    - name: EvidenceMetadataResult
      methods: []
    - name: LLMRunRecordResult
      methods: []
    - name: LLMRunRecordsResult
      methods: []
    - name: TraceStepResult
      methods: []
    - name: LLMRunEnvelopeResult
      methods: []
    - name: LLMRunTraceResult
      methods: []
    - name: GovernanceEventResult
      methods: []
    - name: LLMRunGovernanceResult
      methods: []
    - name: ReplayEventResult
      methods: []
    - name: LLMRunReplayResult
      methods: []
    - name: LLMRunExportResult
      methods: []
    - name: SystemRecordResult
      methods: []
    - name: SystemRecordsResult
      methods: []
    - name: SystemSnapshotResult
      methods: []
    - name: TelemetryStubResult
      methods: []
    - name: SystemEventResult
      methods: []
    - name: SystemEventsResult
      methods: []
    - name: SystemReplayResult
      methods: []
    - name: SystemAuditResult
      methods: []
    - name: AuditLedgerItemResult
      methods: []
    - name: AuditLedgerDetailResult
      methods: []
    - name: AuditLedgerListResult
      methods: []
    - name: IdentityEventResult
      methods: []
    - name: AuditIdentityResult
      methods: []
    - name: AuthorizationDecisionResult
      methods: []
    - name: AuditAuthorizationResult
      methods: []
    - name: AccessEventResult
      methods: []
    - name: AuditAccessResult
      methods: []
    - name: IntegrityCheckResult
      methods: []
    - name: AuditIntegrityResult
      methods: []
    - name: ExportRecordResult
      methods: []
    - name: AuditExportsResult
      methods: []
    - name: LogsFacade
      methods: [list_llm_run_records, get_llm_run_envelope, get_llm_run_trace, get_llm_run_governance, get_llm_run_replay, get_llm_run_export, list_system_records, get_system_snapshot, get_system_telemetry, get_system_events, get_system_replay, get_system_audit, list_audit_entries, get_audit_entry, get_audit_identity, get_audit_authorization, get_audit_access, get_audit_integrity, get_audit_exports]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
