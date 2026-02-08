# Incidents — L6 Drivers (11 files)

**Domain:** incidents  
**Layer:** L6_drivers  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

---

## export_bundle_driver.py
**Path:** `backend/app/hoc/cus/incidents/L6_drivers/export_bundle_driver.py`  
**Layer:** L6_drivers | **Domain:** incidents | **Lines:** 434

**Docstring:** Export Bundle Service

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `TraceStorePort` | get_trace_summary, get_trace_steps |  |
| `ExportBundleDriver` | __init__, trace_store, create_evidence_bundle, create_soc2_bundle, create_executive_debrief, _compute_bundle_hash, _generate_attestation, _assess_risk_level (+3 more) | Generate structured export bundles from incidents/traces. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_export_bundle_driver` | `() -> ExportBundleDriver` | no | Get or create ExportBundleDriver singleton. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `json` | json | no |
| `logging` | logging | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any, Optional, Protocol, runtime_checkable | no |
| `sqlmodel` | Session, select | no |
| `app.db` | Run, engine | no |
| `app.models.killswitch` | Incident | no |
| `app.models.export_bundles` | DEFAULT_SOC2_CONTROLS, EvidenceBundle, ExecutiveDebriefBundle, PolicyContext, SOC2Bundle (+1) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

---

## incident_aggregator.py
**Path:** `backend/app/hoc/cus/incidents/L6_drivers/incident_aggregator.py`  
**Layer:** L6_drivers | **Domain:** incidents | **Lines:** 614

**Docstring:** Incident Aggregation Driver - Prevents Incident Explosion Under Load

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IncidentAggregatorConfig` |  | Configuration for incident aggregation behavior (L6 persistence config only). |
| `IncidentKey` | __hash__, __eq__, from_event | Grouping key for incident aggregation. |
| `IncidentAggregator` | __init__, get_or_create_incident, _find_open_incident, _can_create_incident, _get_rate_limit_incident, _create_incident, _add_call_to_incident, _add_incident_event (+2 more) | L6 Driver for intelligent incident aggregation. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `create_incident_aggregator` | `(config: Optional[IncidentAggregatorConfig] = None) -> IncidentAggregator` | no | Create an IncidentAggregator with canonical dependencies. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timedelta, timezone | no |
| `decimal` | Decimal | no |
| `typing` | Any, Callable, Dict, Optional, Tuple (+1) | no |
| `sqlmodel` | Session, and_, select | no |
| `app.hoc.cus.incidents.L5_schemas.severity_policy` | IncidentSeverityEngine, SeverityConfig, generate_incident_title | no |
| `app.models.killswitch` | Incident, IncidentEvent, IncidentSeverity, IncidentStatus | no |
| `app.utils.runtime` | generate_uuid, utc_now | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

---

## incident_pattern_driver.py
**Path:** `backend/app/hoc/cus/incidents/L6_drivers/incident_pattern_driver.py`  
**Layer:** L6_drivers | **Domain:** incidents | **Lines:** 255

**Docstring:** Incident Pattern Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IncidentPatternDriver` | __init__, fetch_incidents_count, fetch_category_clusters, fetch_severity_spikes, fetch_cascade_failures | L6 driver for incident pattern detection operations (async). |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_incident_pattern_driver` | `(session: AsyncSession) -> IncidentPatternDriver` | no | Factory function to get IncidentPatternDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `datetime` | datetime | no |
| `typing` | Any, Dict, List | no |
| `sqlalchemy` | text | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`IncidentPatternDriver`, `get_incident_pattern_driver`

---

## incident_read_driver.py
**Path:** `backend/app/hoc/cus/incidents/L6_drivers/incident_read_driver.py`  
**Layer:** L6_drivers | **Domain:** incidents | **Lines:** 212

**Docstring:** Incident Read Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IncidentReadDriver` | __init__, list_incidents, get_incident, get_incident_events, count_incidents_since, get_last_incident | L6 driver for incident read operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_incident_read_driver` | `(session: Session) -> IncidentReadDriver` | no | Factory function to get IncidentReadDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime | no |
| `typing` | List, Optional, Tuple | no |
| `sqlalchemy` | and_, desc, func, select | no |
| `sqlmodel` | Session | no |
| `app.models.killswitch` | Incident, IncidentEvent | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`IncidentReadDriver`, `get_incident_read_driver`

---

## incident_write_driver.py
**Path:** `backend/app/hoc/cus/incidents/L6_drivers/incident_write_driver.py`  
**Layer:** L6_drivers | **Domain:** incidents | **Lines:** 611

**Docstring:** Incident Write Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IncidentWriteDriver` | __init__, update_incident_acknowledged, update_incident_resolved, create_incident_event, refresh_incident, insert_incident, update_run_incident_count, update_trace_incident_id (+5 more) | L6 driver for incident write operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_incident_write_driver` | `(session: Session) -> IncidentWriteDriver` | no | Factory function to get IncidentWriteDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `json` | json | no |
| `datetime` | datetime | no |
| `typing` | Any, Dict, List, Optional | no |
| `sqlalchemy` | text | no |
| `sqlmodel` | Session | no |
| `app.models.killswitch` | Incident, IncidentEvent, IncidentStatus | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`IncidentWriteDriver`, `get_incident_write_driver`

---

## incidents_facade_driver.py
**Path:** `backend/app/hoc/cus/incidents/L6_drivers/incidents_facade_driver.py`  
**Layer:** L6_drivers | **Domain:** incidents | **Lines:** 807

**Docstring:** Incidents Facade Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IncidentSnapshot` |  | Raw incident data snapshot from database. |
| `IncidentListSnapshot` |  | Paginated list of incident snapshots. |
| `MetricsSnapshot` |  | Raw metrics aggregates from database. |
| `CostImpactRowSnapshot` |  | Single row from cost impact query. |
| `HistoricalTrendRowSnapshot` |  | Single row from historical trend query. |
| `HistoricalDistributionRowSnapshot` |  | Single row from distribution query. |
| `CostTrendRowSnapshot` |  | Single row from cost trend query. |
| `IncidentsFacadeDriver` | __init__, fetch_active_incidents, fetch_resolved_incidents, fetch_historical_incidents, fetch_incident_by_id, fetch_incidents_by_run, fetch_metrics_aggregates, fetch_cost_impact_data (+5 more) | L6 Database driver for incidents facade. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timedelta, timezone | no |
| `typing` | Any, Optional | no |
| `sqlalchemy` | func, select, text | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.models.killswitch` | Incident | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`IncidentsFacadeDriver`, `IncidentSnapshot`, `IncidentListSnapshot`, `MetricsSnapshot`, `CostImpactRowSnapshot`, `HistoricalTrendRowSnapshot`, `HistoricalDistributionRowSnapshot`, `CostTrendRowSnapshot`

---

## lessons_driver.py
**Path:** `backend/app/hoc/cus/incidents/L6_drivers/lessons_driver.py`  
**Layer:** L6_drivers | **Domain:** incidents | **Lines:** 649

**Docstring:** Lessons Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `LessonsDriver` | __init__, insert_lesson, fetch_lesson_by_id, fetch_lessons_list, fetch_lesson_stats, update_lesson_deferred, update_lesson_dismissed, update_lesson_converted (+4 more) | L6 driver for lessons_learned operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_lessons_driver` | `(session: Session) -> LessonsDriver` | no | Factory function to get LessonsDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `json` | json | no |
| `datetime` | datetime | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | UUID | no |
| `sqlalchemy` | text | no |
| `sqlmodel` | Session | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`LessonsDriver`, `get_lessons_driver`

---

## llm_failure_driver.py
**Path:** `backend/app/hoc/cus/incidents/L6_drivers/llm_failure_driver.py`  
**Layer:** L6_drivers | **Domain:** incidents | **Lines:** 331

**Docstring:** LLM Failure Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `LLMFailureDriver` | __init__, insert_failure, insert_evidence, update_run_failed, fetch_failure_by_run_id, fetch_contamination_check | L6 driver for LLM failure operations (async). |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_llm_failure_driver` | `(session: AsyncSession) -> LLMFailureDriver` | no | Factory function to get LLMFailureDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `json` | json | no |
| `logging` | logging | no |
| `datetime` | datetime | no |
| `typing` | Any, Dict, Optional, Tuple | no |
| `sqlalchemy` | text | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`LLMFailureDriver`, `get_llm_failure_driver`

---

## policy_violation_driver.py
**Path:** `backend/app/hoc/cus/incidents/L6_drivers/policy_violation_driver.py`  
**Layer:** L6_drivers | **Domain:** incidents | **Lines:** 481

**Docstring:** Policy Violation Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyViolationDriver` | __init__, insert_violation_record, fetch_violation_exists, fetch_policy_enabled, insert_evidence_event, fetch_incident_by_violation, fetch_violation_truth_check, insert_policy_evaluation | L6 driver for policy violation operations (async). |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `insert_policy_evaluation_sync_with_cursor` | `(cursor, evaluation_id: str, run_id: str, tenant_id: str, outcome: str, policies` | no | Insert policy evaluation record using provided cursor. |
| `get_policy_violation_driver` | `(session: AsyncSession) -> PolicyViolationDriver` | no | Factory function to get PolicyViolationDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `json` | json | no |
| `logging` | logging | no |
| `datetime` | datetime | no |
| `typing` | Any, Dict, Optional | no |
| `sqlalchemy` | text | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`PolicyViolationDriver`, `get_policy_violation_driver`, `insert_policy_evaluation_sync_with_cursor`

---

## postmortem_driver.py
**Path:** `backend/app/hoc/cus/incidents/L6_drivers/postmortem_driver.py`  
**Layer:** L6_drivers | **Domain:** incidents | **Lines:** 316

**Docstring:** Post-Mortem Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PostMortemDriver` | __init__, fetch_category_stats, fetch_resolution_methods, fetch_recurrence_data, fetch_resolution_summary, fetch_similar_incidents | L6 driver for post-mortem analytics operations (async). |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_postmortem_driver` | `(session: AsyncSession) -> PostMortemDriver` | no | Factory function to get PostMortemDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Any, Dict, List, Optional | no |
| `sqlalchemy` | text | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`PostMortemDriver`, `get_postmortem_driver`

---

## recurrence_analysis_driver.py
**Path:** `backend/app/hoc/cus/incidents/L6_drivers/recurrence_analysis_driver.py`  
**Layer:** L6_drivers | **Domain:** incidents | **Lines:** 213

**Docstring:** Recurrence Analysis Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `RecurrenceGroupSnapshot` |  | Raw recurrence group data from database. |
| `RecurrenceAnalysisDriver` | __init__, fetch_recurrence_groups, fetch_recurrence_for_category | L6 Database driver for recurrence analysis. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime | no |
| `typing` | Optional | no |
| `sqlalchemy` | text | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`RecurrenceAnalysisDriver`, `RecurrenceGroupSnapshot`

---
