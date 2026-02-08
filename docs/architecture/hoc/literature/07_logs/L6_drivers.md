# Logs — L6 Drivers (16 files)

**Domain:** logs  
**Layer:** L6_drivers  
**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

**Layer Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

---

## audit_ledger_driver.py
**Path:** `backend/app/hoc/cus/logs/L6_drivers/audit_ledger_driver.py`  
**Layer:** L6_drivers | **Domain:** logs | **Lines:** 397

**Docstring:** Audit Ledger Service (Async)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AuditLedgerServiceAsync` | __init__, _emit, limit_created, limit_updated, limit_breached, policy_rule_created, policy_rule_modified, policy_rule_retired (+5 more) | Async service for writing to the audit ledger. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_audit_ledger_service_async` | `(session: AsyncSession) -> AuditLedgerServiceAsync` | no | Get an AuditLedgerServiceAsync instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Any, Dict, Optional | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.models.audit_ledger` | ActorType, AuditEntityType, AuditEventType, AuditLedger | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

### __all__ Exports
`AuditLedgerServiceAsync`, `get_audit_ledger_service_async`

---

## audit_ledger_read_driver.py
**Path:** `backend/app/hoc/cus/logs/L6_drivers/audit_ledger_read_driver.py`  
**Layer:** L6_drivers | **Domain:** logs | **Lines:** 243

**Docstring:** Audit Ledger Read Driver (PIN-519)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AuditLedgerReadDriver` | __init__, get_signal_feedback, get_audit_entries_for_entity, get_signal_events_for_run | Async driver for reading from the audit ledger. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_audit_ledger_read_driver` | `(session: AsyncSession) -> AuditLedgerReadDriver` | no | Get an AuditLedgerReadDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `datetime` | datetime | no |
| `typing` | Optional | no |
| `sqlalchemy` | and_, desc, select | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.models.audit_ledger` | AuditEntityType, AuditEventType, AuditLedger | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

### __all__ Exports
`AuditLedgerReadDriver`, `get_audit_ledger_read_driver`

---

## audit_ledger_write_driver_sync.py
**Path:** `backend/app/hoc/cus/logs/L6_drivers/audit_ledger_write_driver_sync.py`  
**Layer:** L6_drivers | **Domain:** logs | **Lines:** 95

**Docstring:** Audit Ledger Sync Write Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AuditLedgerWriteDriverSync` | __init__, emit_entry | L6 sync driver for constructing and persisting AuditLedger ORM rows. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_audit_ledger_write_driver_sync` | `(session: Session) -> AuditLedgerWriteDriverSync` | no | Factory for AuditLedgerWriteDriverSync. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Any, Dict, Optional | no |
| `sqlmodel` | Session | no |
| `app.models.audit_ledger` | AuditLedger | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

---

## bridges_driver.py
**Path:** `backend/app/hoc/cus/logs/L6_drivers/bridges_driver.py`  
**Layer:** L6_drivers | **Domain:** logs | **Lines:** 123

**Docstring:** M25 Bridges Driver

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `record_policy_activation` | `(session: AsyncSession, policy_id: str, source_pattern_id: str, source_recovery_` | yes | Record policy activation for audit trail. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `datetime` | datetime, timezone | no |
| `sqlalchemy` | text | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `schemas.audit_schemas` | PolicyActivationAudit | yes |
| `schemas.loop_events` | ConfidenceCalculator | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

---

## capture_driver.py
**Path:** `backend/app/hoc/cus/logs/L6_drivers/capture_driver.py`  
**Layer:** L6_drivers | **Domain:** logs | **Lines:** 870

**Docstring:** Taxonomy Evidence Capture Service (v1.1)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `EvidenceContextError` | __init__ | Hard failure when evidence capture is attempted without ExecutionContext. |
| `CaptureFailureReason` |  | Standard failure reasons for integrity evidence. |
| `FailureResolution` |  | Resolution semantics for capture failures. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_assert_context_exists` | `(ctx: ExecutionContext, evidence_type: str) -> None` | no | Hard guard: Fail fast if context is None. |
| `_record_capture_failure` | `(session: Session, run_id: str, evidence_type: str, failure_reason: str, error_m` | no | Record an evidence capture failure for later integrity reporting. |
| `_hash_content` | `(content: str) -> str` | no | Generate SHA256 fingerprint of content. |
| `capture_environment_evidence` | `(session: Session, ctx: ExecutionContext) -> Optional[str]` | no | Capture environment evidence (Class H) at run creation. |
| `capture_activity_evidence` | `(session: Session, ctx: ExecutionContext) -> Optional[str]` | no | Capture activity evidence (Class B) before/after LLM calls. |
| `capture_provider_evidence` | `(session: Session, ctx: ExecutionContext) -> Optional[str]` | no | Capture provider evidence (Class G) after LLM provider response. |
| `capture_policy_decision_evidence` | `(session: Session, ctx: ExecutionContext) -> Optional[str]` | no | Capture policy decision evidence (Class D) during policy evaluation. |
| `compute_integrity` | `(run_id: str) -> Dict[str, Any]` | no | Compute integrity payload by examining evidence tables. |
| `capture_integrity_evidence` | `(session: Session, run_id: str) -> Optional[str]` | no | Capture integrity evidence (Class J) at terminal state. |
| `hash_prompt` | `(prompt: str) -> str` | no | Generate SHA256 fingerprint of prompt content. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `hashlib` | hashlib | no |
| `json` | json | no |
| `logging` | logging | no |
| `os` | os | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | uuid4 | no |
| `sqlalchemy` | text | no |
| `sqlalchemy.exc` | SQLAlchemyError | no |
| `sqlmodel` | Session | no |
| `app.core.execution_context` | ExecutionContext | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

### Constants
`_FAILURE_RESOLUTION_MAP`

---

## cost_intelligence_driver.py
**Path:** `backend/app/hoc/cus/logs/L6_drivers/cost_intelligence_driver.py`  
**Layer:** L6_drivers | **Domain:** logs | **Lines:** 545

**Docstring:** Cost Intelligence Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CostIntelligenceDriver` | __init__, fetch_cost_summary, fetch_tenant_budget, fetch_total_cost, fetch_costs_by_feature, fetch_costs_by_user, fetch_costs_by_model, fetch_recent_anomalies (+8 more) | L6 driver for cost intelligence read operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_cost_intelligence_driver` | `(session: AsyncSession) -> CostIntelligenceDriver` | no | Get cost intelligence driver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime | no |
| `typing` | Any, Optional | no |
| `sqlalchemy` | text | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

---

## cost_intelligence_sync_driver.py
**Path:** `backend/app/hoc/cus/logs/L6_drivers/cost_intelligence_sync_driver.py`  
**Layer:** L6_drivers | **Domain:** logs | **Lines:** 673

**Docstring:** Cost Intelligence Sync Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CostIntelligenceSyncDriver` | __init__, check_feature_tag_exists, fetch_feature_tags, fetch_feature_tag_by_tag, fetch_active_feature_tag, update_feature_tag, fetch_cost_summary, fetch_tenant_budget (+12 more) | L6 sync driver for cost intelligence read operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_cost_intelligence_sync_driver` | `(session: Session) -> CostIntelligenceSyncDriver` | no | Get cost intelligence sync driver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime | no |
| `typing` | Any, Optional | no |
| `sqlalchemy` | text | no |
| `sqlmodel` | Session | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

### __all__ Exports
`CostIntelligenceSyncDriver`, `get_cost_intelligence_sync_driver`

---

## export_bundle_store.py
**Path:** `backend/app/hoc/cus/logs/L6_drivers/export_bundle_store.py`  
**Layer:** L6_drivers | **Domain:** logs | **Lines:** 245

**Docstring:** Export Bundle Store (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IncidentSnapshot` |  | Immutable snapshot of incident. |
| `RunSnapshot` |  | Immutable snapshot of run. |
| `TraceSummarySnapshot` |  | Immutable snapshot of trace summary. |
| `TraceStepSnapshot` |  | Immutable snapshot of trace step. |
| `ExportBundleStore` | __init__, trace_store, get_incident, get_run_by_run_id, get_trace_summary, get_trace_steps | L6 Database Driver for export bundle data. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_export_bundle_store` | `() -> ExportBundleStore` | no | Get the singleton ExportBundleStore instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime | no |
| `typing` | Optional | no |
| `sqlmodel` | Session, select | no |
| `app.db` | Run, engine | no |
| `app.models.killswitch` | Incident | no |
| `app.traces.store` | TraceStore | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

### __all__ Exports
`ExportBundleStore`, `get_export_bundle_store`, `IncidentSnapshot`, `RunSnapshot`, `TraceSummarySnapshot`, `TraceStepSnapshot`

---

## idempotency_driver.py
**Path:** `backend/app/hoc/cus/logs/L6_drivers/idempotency_driver.py`  
**Layer:** L6_drivers | **Domain:** logs | **Lines:** 399

**Docstring:** Redis Idempotency Store for AOS Traces

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IdempotencyResult` |  | Result of idempotency check. |
| `IdempotencyResponse` | is_new, is_duplicate, is_conflict | Response from idempotency check. |
| `RedisIdempotencyStore` | __init__, _make_key, _ensure_script_loaded, check, mark_completed, mark_failed, delete, get_status | Redis-backed idempotency store with Lua script for atomicity. |
| `InMemoryIdempotencyStore` | __init__, _make_key, check, mark_completed, mark_failed, delete, get_status | In-memory idempotency store for testing and development. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_load_lua_script` | `() -> str` | no | Load Lua script from file. |
| `canonical_json` | `(obj: Any) -> str` | no | Produce canonical JSON (sorted keys, compact format). |
| `hash_request` | `(data: Dict[str, Any]) -> str` | no | Hash request data for idempotency comparison. |
| `get_idempotency_store` | `() -> Any` | yes | Get or create idempotency store based on environment. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `json` | json | no |
| `logging` | logging | no |
| `os` | os | no |
| `dataclasses` | dataclass | no |
| `enum` | Enum | no |
| `pathlib` | Path | no |
| `typing` | Any, Dict, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

### Constants
`_LUA_SCRIPT_PATH`

---

## integrity_driver.py
**Path:** `backend/app/hoc/cus/logs/L6_drivers/integrity_driver.py`  
**Layer:** L6_drivers | **Domain:** logs | **Lines:** 524

**Docstring:** Integrity Computation Module (v1.1)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IntegrityState` |  | Evidence completeness state. |
| `IntegrityGrade` |  | Quality judgment on the evidence. |
| `EvidenceClass` |  | Taxonomy of evidence classes. |
| `FailureResolution` |  | Resolution semantics for capture failures. |
| `CaptureFailure` | to_dict | Structured representation of an evidence capture failure. |
| `IntegrityFacts` | has_required_evidence, has_capture_failures, unresolved_failures | Raw facts gathered from evidence tables. |
| `IntegrityAssembler` | __init__, gather, _count_evidence, _gather_failures, _resolve_superseded, _table_to_class, _string_to_class | Gathers facts from evidence tables. |
| `IntegrityEvaluation` | integrity_status | Result of integrity policy evaluation. |
| `IntegrityEvaluator` | evaluate, _find_failure, _compute_grade, _build_explanation | Applies policy to integrity facts. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `compute_integrity_v2` | `(run_id: str) -> Dict[str, Any]` | no | Compute integrity using the new split architecture. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `json` | json | no |
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |
| `sqlalchemy` | create_engine, text | no |
| `sqlalchemy.exc` | SQLAlchemyError | no |
| `os` | os | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

### Constants
`DATABASE_URL`, `REQUIRED_EVIDENCE`, `EXPECTED_EVIDENCE`

---

## job_execution_driver.py
**Path:** `backend/app/hoc/cus/logs/L6_drivers/job_execution_driver.py`  
**Layer:** L6_drivers | **Domain:** logs | **Lines:** 881

**Docstring:** Module: job_execution

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `RetryStrategy` |  | Retry strategy types. |
| `RetryConfig` |  | Configuration for job retry. |
| `RetryAttempt` |  | Record of a retry attempt. |
| `JobRetryManager` | __init__, should_retry, calculate_delay, record_retry, get_retry_history, clear_history | Manages job retry logic with configurable strategies. |
| `ProgressStage` |  | Standard progress stages. |
| `ProgressUpdate` | to_dict | A progress update for a job. |
| `JobProgressTracker` | __init__, start, update, complete, fail, get_progress, register_callback, _calculate_eta (+2 more) | Tracks and reports job progress. |
| `JobAuditEventType` |  | Types of job audit events. |
| `JobAuditEvent` | __post_init__, _compute_integrity_hash, to_dict, verify_integrity | Audit event for job execution. |
| `JobAuditEmitter` | __init__, _generate_event_id, emit_created, emit_started, emit_completed, emit_failed, emit_retried, _emit (+1 more) | Emits audit events for job execution. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_hash_value` | `(value: Any) -> str` | no | Hash a value for audit purposes. |
| `get_job_retry_manager` | `() -> JobRetryManager` | no | Get the singleton JobRetryManager. |
| `get_job_progress_tracker` | `() -> JobProgressTracker` | no | Get the singleton JobProgressTracker. |
| `get_job_audit_emitter` | `() -> JobAuditEmitter` | no | Get the singleton JobAuditEmitter. |
| `reset_job_execution_services` | `() -> None` | no | Reset all singletons (for testing). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `logging` | logging | no |
| `random` | random | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timedelta, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Callable, Dict, List, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

---

## logs_domain_store.py
**Path:** `backend/app/hoc/cus/logs/L6_drivers/logs_domain_store.py`  
**Layer:** L6_drivers | **Domain:** logs | **Lines:** 673

**Docstring:** Logs Domain Store (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `LLMRunSnapshot` |  | Immutable snapshot of LLM run record. |
| `SystemRecordSnapshot` |  | Immutable snapshot of system record. |
| `AuditLedgerSnapshot` |  | Immutable snapshot of audit ledger entry. |
| `LogExportSnapshot` |  | Immutable snapshot of log export record. |
| `TraceStepSnapshot` |  | Immutable snapshot of trace step. |
| `QueryResult` |  | Generic query result with pagination info. |
| `LogsDomainStore` | list_llm_runs, get_llm_run, _to_llm_run_snapshot, get_trace_id_for_run, get_trace_steps, get_replay_window_events, list_system_records, get_system_record_by_correlation (+8 more) | L6 Database Driver for Logs domain. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_logs_domain_store` | `() -> LogsDomainStore` | no | Get the singleton LogsDomainStore instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timedelta, timezone | no |
| `typing` | Any, Optional | no |
| `sqlalchemy` | func, select, text | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.models.audit_ledger` | AuditLedger | no |
| `app.models.log_exports` | LogExport | no |
| `app.models.logs_records` | LLMRunRecord, SystemRecord | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

### __all__ Exports
`LogsDomainStore`, `get_logs_domain_store`, `LLMRunSnapshot`, `SystemRecordSnapshot`, `AuditLedgerSnapshot`, `LogExportSnapshot`, `TraceStepSnapshot`, `QueryResult`

---

## panel_consistency_driver.py
**Path:** `backend/app/hoc/cus/logs/L6_drivers/panel_consistency_driver.py`  
**Layer:** L6_drivers | **Domain:** logs | **Lines:** 251

**Docstring:** Panel Consistency Checker — Cross-slot consistency rules

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ConsistencyViolation` |  | A consistency violation between slots. |
| `ConsistencyCheckResult` |  | Result of consistency checking. |
| `PanelConsistencyChecker` | __init__, _default_rules, check, _check_rule, _evaluate_condition, _eval_expr | Checks cross-slot consistency within a panel. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `create_consistency_checker` | `(rules: Optional[List[Dict[str, Any]]] = None) -> PanelConsistencyChecker` | no | Create consistency checker with optional custom rules. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `typing` | Any, Dict, List, Optional | no |
| `panel_types` | PanelSlotResult | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

---

## pg_store.py
**Path:** `backend/app/hoc/cus/logs/L6_drivers/pg_store.py`  
**Layer:** L6_drivers | **Domain:** logs | **Lines:** 769

**Docstring:** PostgreSQL Trace Store for AOS

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PostgresTraceStore` | __init__, _get_pool, close, start_trace, record_step, complete_trace, mark_trace_aborted, store_trace (+8 more) | PostgreSQL-based trace storage for production. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_status_to_level` | `(status: str) -> str` | no | Derive log level from step status. |
| `get_postgres_trace_store` | `() -> PostgresTraceStore` | no | Get singleton PostgreSQL trace store. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `json` | json | no |
| `os` | os | no |
| `uuid` | uuid | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any | no |
| `models` | TraceRecord, TraceStatus, TraceStep, TraceSummary | yes |
| `redact` | redact_trace_data | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

---

## replay_driver.py
**Path:** `backend/app/hoc/cus/logs/L6_drivers/replay_driver.py`  
**Layer:** L6_drivers | **Domain:** logs | **Lines:** 330

**Docstring:** Server-Side Replay Enforcement

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ReplayBehavior` |  | Replay behavior options. |
| `ReplayMismatchError` | __init__ | Raised when replay output doesn't match original. |
| `IdempotencyViolationError` | __init__ | Raised when idempotency key is violated. |
| `ReplayResult` |  | Result of a replay operation. |
| `ReplayEnforcer` | __init__, enforce_step, enforce_trace | Server-side replay behavior enforcer. |
| `IdempotencyStore` | get, set, delete | Abstract base for idempotency storage. |
| `InMemoryIdempotencyStore` | __init__, _make_key, get, set, delete, clear | In-memory idempotency store for testing. |
| `RedisIdempotencyStore` | __init__, _get_client, _make_key, get, set, delete | Redis-based idempotency store for production. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `hash_output` | `(data: Any) -> str` | no | Compute hash of output data for comparison. |
| `get_replay_enforcer` | `(use_redis: bool = False) -> ReplayEnforcer` | no | Get singleton replay enforcer. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `json` | json | no |
| `dataclasses` | dataclass | no |
| `enum` | Enum | no |
| `typing` | Any, Awaitable, Callable, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

---

## trace_mismatch_driver.py
**Path:** `backend/app/hoc/cus/logs/L6_drivers/trace_mismatch_driver.py`  
**Layer:** L6_drivers | **Domain:** logs | **Lines:** 316

**Docstring:** Trace Mismatch Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `TraceMismatchDriver` | __init__, fetch_trace_tenant, insert_mismatch, update_mismatch_issue_url, update_mismatch_notification, resolve_mismatch, fetch_mismatches_for_trace, fetch_all_mismatches (+2 more) | L6 driver for trace mismatch data access. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_trace_mismatch_driver` | `(session: AsyncSession) -> TraceMismatchDriver` | no | Get trace mismatch driver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, Optional | no |
| `sqlalchemy` | text | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

---
