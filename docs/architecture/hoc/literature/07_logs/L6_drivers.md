# Logs — L6 Drivers (4 files)

**Domain:** logs  
**Layer:** L6_drivers  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`ExportBundleStore`, `get_export_bundle_store`, `IncidentSnapshot`, `RunSnapshot`, `TraceSummarySnapshot`, `TraceStepSnapshot`

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`LogsDomainStore`, `get_logs_domain_store`, `LLMRunSnapshot`, `SystemRecordSnapshot`, `AuditLedgerSnapshot`, `LogExportSnapshot`, `TraceStepSnapshot`, `QueryResult`

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

---
