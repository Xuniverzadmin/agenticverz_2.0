# Logs — L5 Engines (16 files)

**Domain:** logs  
**Layer:** L5_engines  
**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

**Layer Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

---

## audit_evidence.py
**Path:** `backend/app/hoc/cus/logs/L5_engines/audit_evidence.py`  
**Layer:** L5_engines | **Domain:** logs | **Lines:** 671

**Docstring:** Module: audit_evidence

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `MCPAuditEventType` |  | Types of MCP audit events. |
| `MCPAuditEvent` | __post_init__, _compute_integrity_hash, to_dict, verify_integrity | Compliance-grade audit event for MCP operations. |
| `MCPAuditEmitter` | __init__, _generate_event_id, emit_tool_requested, emit_tool_allowed, emit_tool_denied, emit_tool_started, emit_tool_completed, emit_tool_failed (+4 more) | Emitter for compliance-grade MCP audit events. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_hash_value` | `(value: Any) -> str` | no | Hash a value for audit purposes. |
| `_contains_sensitive` | `(key: str) -> bool` | no | Check if key name suggests sensitive data. |
| `_redact_sensitive` | `(data: Dict[str, Any]) -> Dict[str, Any]` | no | Redact sensitive fields from data for logging. |
| `get_mcp_audit_emitter` | `() -> MCPAuditEmitter` | no | Get or create the singleton MCPAuditEmitter. |
| `configure_mcp_audit_emitter` | `(publisher: Optional[Any] = None) -> MCPAuditEmitter` | no | Configure the singleton MCPAuditEmitter. |
| `reset_mcp_audit_emitter` | `() -> None` | no | Reset the singleton (for testing). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### Constants
`SENSITIVE_PATTERNS`

---

## audit_ledger_engine.py
**Path:** `backend/app/hoc/cus/logs/L5_engines/audit_ledger_engine.py`  
**Layer:** L5_engines | **Domain:** logs | **Lines:** 226

**Docstring:** Audit Ledger Service (Sync)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AuditLedgerService` | __init__, _emit, incident_acknowledged, incident_resolved, incident_manually_closed | Sync service for writing to the audit ledger. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_audit_ledger_service` | `(session: 'Session') -> AuditLedgerService` | no | Get an AuditLedgerService instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `typing` | Any, Dict, Optional, TYPE_CHECKING | no |
| `app.hoc.cus.hoc_spine.schemas.domain_enums` | ActorType, AuditEntityType, AuditEventType | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### __all__ Exports
`AuditLedgerService`, `get_audit_ledger_service`

---

## audit_reconciler.py
**Path:** `backend/app/hoc/cus/logs/L5_engines/audit_reconciler.py`  
**Layer:** L5_engines | **Domain:** logs | **Lines:** 322

**Docstring:** Audit Reconciler

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AuditReconciler` | __init__, reconcile, check_deadline_violations, get_run_audit_summary, _record_metrics | Reconciles expectations with acknowledgments. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_audit_reconciler` | `(store: Optional[AuditStore] = None) -> AuditReconciler` | no | Get the audit reconciler singleton. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `datetime` | datetime, timezone | no |
| `typing` | List, Optional, Set, Tuple | no |
| `uuid` | UUID | no |
| `prometheus_client` | Counter, Histogram | no |
| `app.hoc.cus.hoc_spine.schemas.rac_models` | AuditAction, AuditDomain, AuditExpectation, AuditStatus, DomainAck (+1) | no |
| `app.hoc.cus.hoc_spine.services.audit_store` | AuditStore, get_audit_store | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### Constants
`RECONCILIATION_TOTAL`, `MISSING_ACTIONS_TOTAL`, `DRIFT_ACTIONS_TOTAL`, `STALE_RUNS_TOTAL`, `RECONCILIATION_DURATION`

---

## certificate.py
**Path:** `backend/app/hoc/cus/logs/L5_engines/certificate.py`  
**Layer:** L5_engines | **Domain:** logs | **Lines:** 386

**Docstring:** M23 Certificate Service - Cryptographic Evidence of Deterministic Replay

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CertificateType` |  | Types of certificates that can be issued. |
| `CertificatePayload` | to_dict, canonical_json | The signed payload of a certificate. |
| `Certificate` | to_dict, to_json, from_dict | A signed certificate proving deterministic replay or policy evaluation. |
| `CertificateService` | __init__, _sign, _verify_signature, create_replay_certificate, create_policy_audit_certificate, verify_certificate, export_certificate | Service for creating and verifying cryptographic certificates. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `hmac` | hmac | no |
| `json` | json | no |
| `os` | os | no |
| `uuid` | uuid | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timedelta, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |
| `app.hoc.cus.logs.L5_engines.replay_determinism` | DeterminismLevel, ReplayResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### __all__ Exports
`CertificateService`, `Certificate`, `CertificatePayload`, `CertificateType`

---

## completeness_checker.py
**Path:** `backend/app/hoc/cus/logs/L5_engines/completeness_checker.py`  
**Layer:** L5_engines | **Domain:** logs | **Lines:** 518

**Docstring:** Module: completeness_checker

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CompletenessCheckResult` |  | Result of a completeness check. |
| `EvidenceCompletenessError` | __init__, to_dict | Raised when evidence bundle is incomplete for PDF generation. |
| `CompletenessCheckResponse` | to_dict | Response from a completeness check. |
| `EvidenceCompletenessChecker` | __init__, from_governance_config, validation_enabled, strict_mode, get_required_fields, get_field_value, is_field_present, check (+3 more) | Checks evidence bundle completeness before PDF generation. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `check_evidence_completeness` | `(bundle: Any, export_type: str = 'evidence', validation_enabled: bool = True, st` | no | Quick helper to check evidence completeness. |
| `ensure_evidence_completeness` | `(bundle: Any, export_type: str = 'evidence', validation_enabled: bool = True, st` | no | Quick helper to ensure evidence completeness or raise error. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass, field | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, FrozenSet, List, Optional (+1) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

---

## cost_intelligence_engine.py
**Path:** `backend/app/hoc/cus/logs/L5_engines/cost_intelligence_engine.py`  
**Layer:** L5_engines | **Domain:** logs | **Lines:** 438

**Docstring:** Cost Intelligence Engine (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CostIntelligenceEngine` | __init__, check_feature_tag_exists, list_feature_tags, get_feature_tag, get_active_feature_tag, update_feature_tag, get_cost_summary, get_total_cost (+10 more) | L5 engine for cost intelligence operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_cost_intelligence_engine` | `(driver: CostIntelligenceSyncDriver) -> CostIntelligenceEngine` | no | Get cost intelligence engine instance for the given (session-bound) driver. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timedelta | no |
| `typing` | Any, List, Optional | no |
| `app.hoc.cus.logs.L6_drivers.cost_intelligence_sync_driver` | CostIntelligenceSyncDriver | no |
| `app.hoc.cus.hoc_spine.services.time` | utc_now | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### __all__ Exports
`CostIntelligenceEngine`, `get_cost_intelligence_engine`

---

## evidence_facade.py
**Path:** `backend/app/hoc/cus/logs/L5_engines/evidence_facade.py`  
**Layer:** L5_engines | **Domain:** logs | **Lines:** 570

**Docstring:** Evidence Facade (L5 Domain Engine)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `EvidenceType` |  | Evidence types. |
| `ExportFormat` |  | Export formats. |
| `ExportStatus` |  | Export status. |
| `EvidenceLink` | to_dict | A link in an evidence chain. |
| `EvidenceChain` | to_dict | An evidence chain. |
| `VerificationResult` | to_dict | Result of chain verification. |
| `EvidenceExport` | to_dict | Evidence export request. |
| `EvidenceFacade` | __init__, list_chains, get_chain, create_chain, add_evidence, verify_chain, _create_link, _hash_data (+3 more) | Facade for evidence chain and export operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_evidence_facade` | `() -> EvidenceFacade` | no | Get the evidence facade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | uuid | no |
| `hashlib` | hashlib | no |
| `json` | json | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

---

## evidence_report.py
**Path:** `backend/app/hoc/cus/logs/L5_engines/evidence_report.py`  
**Layer:** L5_engines | **Domain:** logs | **Lines:** 1164

**Docstring:** Evidence Report Generator - Legal-Grade PDF Export

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CertificateEvidence` |  | M23: Certificate data for cryptographic proof. |
| `IncidentEvidence` |  | Evidence data for an incident. |
| `EvidenceReportGenerator` | __init__, _setup_custom_styles, generate, _add_footer, _build_incident_snapshot, _build_cover_page, _build_executive_summary, _build_factual_reconstruction (+9 more) | Generates legal-grade PDF evidence reports. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `generate_evidence_report` | `(incident_id: str, tenant_id: str, tenant_name: str, user_id: str, product_name:` | no | Convenience function to generate an evidence report. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `io` | io | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime | no |
| `typing` | Any, Dict, List, Optional | no |
| `reportlab.lib` | colors | no |
| `reportlab.lib.enums` | TA_CENTER | no |
| `reportlab.lib.pagesizes` | letter | no |
| `reportlab.lib.styles` | ParagraphStyle, getSampleStyleSheet | no |
| `reportlab.lib.units` | inch | no |
| `reportlab.platypus` | HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer (+2) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

---

## logs_facade.py
**Path:** `backend/app/hoc/cus/logs/L5_engines/logs_facade.py`  
**Layer:** L5_engines | **Domain:** logs | **Lines:** 1407

**Docstring:** Logs Domain Facade (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SourceDomain` |  | Source domain for evidence metadata. |
| `Origin` |  | Origin of the record. |
| `EvidenceMetadataResult` |  | Global metadata contract for all Logs responses. |
| `LLMRunRecordResult` |  | Single LLM run record. |
| `LLMRunRecordsResult` |  | Response envelope for LLM run records. |
| `TraceStepResult` |  | Individual trace step. |
| `LLMRunEnvelopeResult` |  | O1: Canonical immutable run record. |
| `LLMRunTraceResult` |  | O2: Step-by-step trace. |
| `GovernanceEventResult` |  | Policy interaction event. |
| `LLMRunGovernanceResult` |  | O3: Policy interaction trace. |
| `ReplayEventResult` |  | Replay window event. |
| `LLMRunReplayResult` |  | O4: 60-second replay window. |
| `LLMRunExportResult` |  | O5: Export metadata. |
| `SystemRecordResult` |  | Single system record entry. |
| `SystemRecordsResult` |  | Response envelope for system records. |
| `SystemSnapshotResult` |  | O1: Environment snapshot. |
| `TelemetryStubResult` |  | O2: Telemetry stub response. |
| `SystemEventResult` |  | System event record. |
| `SystemEventsResult` |  | O3: Infra events affecting run. |
| `SystemReplayResult` |  | O4: Infra replay window. |
| `SystemAuditResult` |  | O5: Infra attribution record. |
| `AuditLedgerItemResult` |  | Single audit ledger entry. |
| `AuditLedgerDetailResult` |  | Audit ledger entry with state snapshots. |
| `AuditLedgerListResult` |  | Response envelope for audit ledger. |
| `IdentityEventResult` |  | Identity lifecycle event. |
| `AuditIdentityResult` |  | O1: Identity lifecycle. |
| `AuthorizationDecisionResult` |  | Authorization decision record. |
| `AuditAuthorizationResult` |  | O2: Access decisions. |
| `AccessEventResult` |  | Log access event. |
| `AuditAccessResult` |  | O3: Log access audit. |
| `IntegrityCheckResult` |  | Integrity verification record. |
| `AuditIntegrityResult` |  | O4: Tamper detection. |
| `ExportRecordResult` |  | Export record. |
| `AuditExportsResult` |  | O5: Compliance exports. |
| `LogsFacade` | __init__, list_llm_run_records, get_llm_run_envelope, get_llm_run_trace, get_llm_run_governance, get_llm_run_replay, get_llm_run_export, list_system_records (+13 more) | Unified facade for all Logs domain operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_logs_facade` | `() -> LogsFacade` | no | Get the singleton LogsFacade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timedelta, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Optional | no |
| `app.hoc.cus.logs.L6_drivers.logs_domain_store` | AuditLedgerSnapshot, LLMRunSnapshot, LogsDomainStore, LogExportSnapshot, QueryResult (+3) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### __all__ Exports
`LogsFacade`, `get_logs_facade`, `SourceDomain`, `Origin`, `EvidenceMetadataResult`, `LLMRunRecordResult`, `LLMRunRecordsResult`, `TraceStepResult`, `LLMRunEnvelopeResult`, `LLMRunTraceResult`, `GovernanceEventResult`, `LLMRunGovernanceResult`, `ReplayEventResult`, `LLMRunReplayResult`, `LLMRunExportResult`, `SystemRecordResult`, `SystemRecordsResult`, `SystemSnapshotResult`, `TelemetryStubResult`, `SystemEventResult`, `SystemEventsResult`, `SystemReplayResult`, `SystemAuditResult`, `AuditLedgerItemResult`, `AuditLedgerDetailResult`, `AuditLedgerListResult`, `IdentityEventResult`, `AuditIdentityResult`, `AuthorizationDecisionResult`, `AuditAuthorizationResult`, `AccessEventResult`, `AuditAccessResult`, `IntegrityCheckResult`, `AuditIntegrityResult`, `ExportRecordResult`, `AuditExportsResult`

---

## logs_read_engine.py
**Path:** `backend/app/hoc/cus/logs/L5_engines/logs_read_engine.py`  
**Layer:** L5_engines | **Domain:** logs | **Lines:** 215

**Docstring:** Logs Read Engine (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `LogsReadService` | __init__, _get_store, search_traces, get_trace, get_trace_count, get_trace_by_root_hash, list_traces | L4 service for logs/trace read operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_logs_read_service` | `() -> LogsReadService` | no | Factory function to get LogsReadService instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | List, Optional | no |
| `app.hoc.cus.logs.L5_engines.traces_models` | TraceRecord, TraceSummary | no |
| `app.hoc.cus.logs.L6_drivers.pg_store` | PostgresTraceStore, get_postgres_trace_store | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### __all__ Exports
`LogsReadService`, `get_logs_read_service`

---

## mapper.py
**Path:** `backend/app/hoc/cus/logs/L5_engines/mapper.py`  
**Layer:** L5_engines | **Domain:** logs | **Lines:** 273

**Docstring:** Module: mapper

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SOC2ControlMapper` | __init__, map_incident_to_controls, _create_mapping, _determine_compliance_status, get_all_applicable_controls | Maps incidents to relevant SOC2 controls. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_control_mappings_for_incident` | `(incident_category: str, incident_data: dict[str, Any]) -> list[dict[str, Any]]` | no | Get SOC2 control mappings for an incident (GAP-025 main entry point). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timezone | no |
| `typing` | Any, Optional | no |
| `app.hoc.cus.hoc_spine.services.time` | utc_now | no |
| `app.hoc.cus.hoc_spine.services.control_registry` | SOC2ComplianceStatus, SOC2Control, SOC2ControlMapping, SOC2ControlRegistry, get_control_registry | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

---

## pdf_renderer.py
**Path:** `backend/app/hoc/cus/logs/L5_engines/pdf_renderer.py`  
**Layer:** L5_engines | **Domain:** logs | **Lines:** 683

**Docstring:** PDF Renderer Engine

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PDFRenderer` | __init__, _setup_styles, render_evidence_pdf, render_soc2_pdf, render_executive_debrief_pdf, _build_evidence_cover, _build_evidence_summary, _build_trace_timeline (+9 more) | Render export bundles to PDF format. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_pdf_renderer` | `() -> PDFRenderer` | no | Get or create PDFRenderer singleton. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `io` | io | no |
| `logging` | logging | no |
| `datetime` | datetime | no |
| `typing` | TYPE_CHECKING, Optional | no |
| `reportlab.lib` | colors | no |
| `reportlab.lib.enums` | TA_CENTER, TA_LEFT | no |
| `reportlab.lib.pagesizes` | letter | no |
| `reportlab.lib.styles` | ParagraphStyle, getSampleStyleSheet | no |
| `reportlab.lib.units` | inch | no |
| `reportlab.platypus` | HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer (+2) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

---

## redact.py
**Path:** `backend/app/hoc/cus/logs/L5_engines/redact.py`  
**Layer:** L5_engines | **Domain:** logs | **Lines:** 267

**Docstring:** PII Redaction Utility for Trace Storage

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `redact_json_string` | `(json_str: str) -> str` | no | Apply PII redaction patterns to a JSON string. |
| `redact_dict` | `(data: dict[str, Any], depth: int = 0, max_depth: int = 20) -> dict[str, Any]` | no | Recursively redact sensitive fields in a dictionary. |
| `redact_list` | `(data: list[Any], depth: int = 0, max_depth: int = 20) -> list[Any]` | no | Recursively redact sensitive fields in a list. |
| `redact_string_value` | `(value: str) -> str` | no | Redact sensitive patterns in a string value. |
| `redact_trace_data` | `(trace: dict[str, Any]) -> dict[str, Any]` | no | Redact PII from a complete trace object. |
| `is_sensitive_field` | `(field_name: str) -> bool` | no | Check if a field name indicates sensitive data. |
| `add_sensitive_field` | `(field_name: str) -> None` | no | Add a custom field name to the sensitive fields set. |
| `add_redaction_pattern` | `(pattern: str, replacement: str) -> None` | no | Add a custom redaction pattern. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `copy` | copy | no |
| `re` | re | no |
| `typing` | Any | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### Constants
`PII_PATTERNS`, `SENSITIVE_FIELD_NAMES`

---

## replay_determinism.py
**Path:** `backend/app/hoc/cus/logs/L5_engines/replay_determinism.py`  
**Layer:** L5_engines | **Domain:** logs | **Lines:** 498

**Docstring:** Replay Determinism Service - Defines and Enforces Determinism Semantics

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ModelVersion` | to_dict, from_dict | Track the model version used for a call. |
| `PolicyDecision` | to_dict | Record of a policy enforcement decision. |
| `ReplayMatch` |  | Result of replay comparison. |
| `ReplayResult` | to_dict | Result of replay validation. |
| `CallRecord` | to_dict | Record of a call for replay validation. |
| `ReplayValidator` | __init__, validate_replay, _detect_model_drift, _compare_policies, _semantic_equivalent, _level_meets_requirement, hash_content | Validates replay determinism at configurable levels. |
| `ReplayContextBuilder` | __init__, build_call_record | Builds replay context from API calls. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `json` | json | no |
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |
| `app.hoc.cus.logs.L5_schemas.determinism_types` | DeterminismLevel | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### __all__ Exports
`DeterminismLevel`, `ModelVersion`, `PolicyDecision`, `ReplayMatch`, `ReplayResult`, `CallRecord`, `ReplayValidator`, `ReplayContextBuilder`

---

## trace_mismatch_engine.py
**Path:** `backend/app/hoc/cus/logs/L5_engines/trace_mismatch_engine.py`  
**Layer:** L5_engines | **Domain:** logs | **Lines:** 583

**Docstring:** Trace Mismatch Engine (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `MismatchReportInput` |  | Input for reporting a mismatch. |
| `NotificationResult` |  | Result of notification attempt. |
| `TraceMismatchEngine` | __init__, list_all_mismatches, list_trace_mismatches, report_mismatch, resolve_mismatch, bulk_report_mismatches, _send_notification, _create_bulk_github_issue (+1 more) | L5 engine for trace mismatch business logic. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_trace_mismatch_engine` | `(driver: TraceMismatchDriver) -> TraceMismatchEngine` | no | Get trace mismatch engine instance for the given (session-bound) driver. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `uuid` | uuid | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timedelta, timezone | no |
| `typing` | Any, Optional | no |
| `app.hoc.cus.logs.L6_drivers.trace_mismatch_driver` | TraceMismatchDriver | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

---

## traces_models.py
**Path:** `backend/app/hoc/cus/logs/L5_engines/traces_models.py`  
**Layer:** L5_engines | **Domain:** logs | **Lines:** 51

**Docstring:** Trace Models for AOS - BACKWARD COMPATIBILITY RE-EXPORTS

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.hoc.cus.logs.L5_schemas.traces_models` | ParityResult, TraceRecord, TraceStatus, TraceStep, TraceSummary (+2) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L7_models
**Called by:** L4_spine

### __all__ Exports
`TraceStatus`, `TraceStep`, `TraceSummary`, `TraceRecord`, `ParityResult`, `compare_traces`, `_normalize_for_determinism`

---
