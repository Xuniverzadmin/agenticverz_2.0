# Incidents — L2 Apis (2 files)

**Domain:** incidents  
**Layer:** L2_apis  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

---

## cost_guard.py
**Path:** `backend/app/hoc/api/cus/incidents/cost_guard.py`  
**Layer:** L2_api | **Domain:** incidents | **Lines:** 556

**Docstring:** Guard Console Cost Visibility API - Customer Cost Transparency

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_map_trend` | `(deviation_pct: Optional[float]) -> tuple[Literal['normal', 'rising', 'spike'], ` | no | Map deviation to customer-friendly trend. |
| `_map_severity_to_status` | `(severity: str) -> Literal['protected', 'attention_needed', 'resolved']` | no | Map internal severity to calm vocabulary. |
| `_generate_summary` | `(by_feature: List[CostBreakdownItemDTO], by_model: List[CostBreakdownItemDTO], t` | no | Generate a one-sentence summary of cost drivers. |
| `get_cost_summary` | `(tenant_id: str = Query(..., description='Your tenant ID'), token: CustomerToken` | yes | GET /guard/costs/summary |
| `get_cost_explained` | `(tenant_id: str = Query(..., description='Your tenant ID'), period: Literal['tod` | yes | GET /guard/costs/explained |
| `get_cost_incidents` | `(tenant_id: str = Query(..., description='Your tenant ID'), include_resolved: bo` | yes | GET /guard/costs/incidents |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `datetime` | datetime, timedelta, timezone | no |
| `typing` | List, Literal, Optional | no |
| `fastapi` | APIRouter, Depends, Query | no |
| `sqlalchemy` | text | no |
| `sqlmodel` | Session | no |
| `app.auth.console_auth` | CustomerToken, verify_console_token | no |
| `app.contracts.guard` | CostBreakdownItemDTO, CustomerCostExplainedDTO, CustomerCostIncidentDTO, CustomerCostIncidentListDTO, CustomerCostSummaryDTO | no |
| `app.db` | get_session | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## incidents.py
**Path:** `backend/app/hoc/api/cus/incidents/incidents.py`  
**Layer:** L2_api | **Domain:** incidents | **Lines:** 2023

**Docstring:** Unified Incidents API (L2)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `LifecycleState` |  | Incident lifecycle state. |
| `Severity` |  | Incident severity. |
| `CauseType` |  | Incident cause type. |
| `Topic` |  | UX topic for filtering. |
| `SortField` |  | Allowed sort fields. |
| `SortOrder` |  | Sort direction. |
| `IncidentSummary` |  | Incident summary for list view (O2). |
| `Pagination` |  | Pagination metadata. |
| `IncidentListResponse` |  | GET /incidents response. |
| `IncidentDetailResponse` |  | GET /incidents/{incident_id} response (O3). |
| `IncidentsByRunResponse` |  | GET /incidents/by-run/{run_id} response. |
| `PatternMatchResponse` |  | A detected incident pattern. |
| `PatternDetectionResponse` |  | GET /incidents/patterns response (ACT-O5). |
| `RecurrenceGroupResponse` |  | A group of recurring incidents. |
| `RecurrenceAnalysisResponse` |  | GET /incidents/recurring response (HIST-O3). |
| `CostImpactSummary` |  | Cost impact summary for an incident category. |
| `CostImpactResponse` |  | GET /incidents/cost-impact response (RES-O3). |
| `IncidentMetricsResponse` |  | GET /incidents/metrics response - Dedicated metrics capability. |
| `HistoricalTrendDataPoint` |  | A single data point in a historical trend. |
| `HistoricalTrendResponse` |  | GET /incidents/historical/trend response. |
| `HistoricalDistributionEntry` |  | A single entry in the distribution. |
| `HistoricalDistributionResponse` |  | GET /incidents/historical/distribution response. |
| `CostTrendDataPoint` |  | A single data point in the cost trend. |
| `CostTrendResponse` |  | GET /incidents/historical/cost-trend response. |
| `LearningInsightResponse` |  | A learning insight from incident analysis. |
| `ResolutionSummaryResponse` |  | Summary of incident resolution. |
| `LearningsResponse` |  | GET /incidents/{id}/learnings response (RES-O4). |
| `ExportFormat` |  | Export format options. |
| `ExportRequest` |  | Request for export with optional parameters. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `require_preflight` | `() -> None` | no | Guard for preflight-only endpoints (O4, O5). |
| `get_tenant_id_from_auth` | `(request: Request) -> str` | no | Extract tenant_id from auth_context. Raises 401/403 if missing. |
| `list_incidents` | `(request: Request, topic: Annotated[Topic | None, Query(description='UX Topic: A` | yes | List incidents with unified query filters. Tenant-scoped. |
| `get_incidents_for_run` | `(request: Request, run_id: str, session: AsyncSession = Depends(get_async_sessio` | yes | Get all incidents linked to a specific run. Tenant-scoped. |
| `detect_patterns` | `(request: Request, window_hours: Annotated[int, Query(ge=1, le=168, description=` | yes | Detect incident patterns. Tenant-scoped. |
| `analyze_recurrence` | `(request: Request, baseline_days: Annotated[int, Query(ge=1, le=90, description=` | yes | Analyze recurring incident patterns. Tenant-scoped. |
| `analyze_cost_impact` | `(request: Request, baseline_days: Annotated[int, Query(ge=1, le=90, description=` | yes | Analyze cost impact across incidents. Tenant-scoped. |
| `list_active_incidents` | `(request: Request, severity: Annotated[Severity | None, Query(description='Filte` | yes | List ACTIVE incidents. Topic enforced at endpoint boundary. |
| `list_resolved_incidents` | `(request: Request, severity: Annotated[Severity | None, Query(description='Filte` | yes | List RESOLVED incidents. Topic enforced at endpoint boundary. |
| `list_historical_incidents` | `(request: Request, retention_days: Annotated[int, Query(ge=7, le=365, descriptio` | yes | List HISTORICAL incidents (resolved beyond retention). Topic enforced. |
| `get_incident_metrics` | `(request: Request, window_days: Annotated[int, Query(ge=1, le=90, description='W` | yes | Get incident metrics. Backend-computed, deterministic. |
| `get_historical_trend` | `(request: Request, window_days: Annotated[int, Query(ge=7, le=365, description='` | yes | Get historical trend. Backend-computed, deterministic. |
| `get_historical_distribution` | `(request: Request, window_days: Annotated[int, Query(ge=7, le=365, description='` | yes | Get historical distribution. Backend-computed, deterministic. |
| `get_historical_cost_trend` | `(request: Request, window_days: Annotated[int, Query(ge=7, le=365, description='` | yes | Get historical cost trend. Backend-computed, deterministic. |
| `get_incident_detail` | `(request: Request, incident_id: str, session: AsyncSession = Depends(get_async_s` | yes | Get incident detail (O3). Tenant isolation enforced. |
| `get_incident_evidence` | `(request: Request, incident_id: str) -> dict[str, Any]` | yes | Get incident evidence (O4). Preflight console only. |
| `get_incident_proof` | `(request: Request, incident_id: str) -> dict[str, Any]` | yes | Get incident proof (O5). Preflight console only. |
| `get_incident_learnings` | `(request: Request, incident_id: str, session: AsyncSession = Depends(get_async_s` | yes | Get post-mortem learnings for an incident. Tenant-scoped. |
| `export_evidence` | `(request: Request, incident_id: str, export_request: ExportRequest) -> Any` | yes | Export incident evidence bundle. |
| `export_soc2` | `(request: Request, incident_id: str, export_request: ExportRequest) -> Any` | yes | Export SOC2-compliant bundle as PDF. |
| `export_executive_debrief` | `(request: Request, incident_id: str, export_request: ExportRequest) -> Any` | yes | Export executive debrief as PDF. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `datetime` | datetime | no |
| `enum` | Enum | no |
| `typing` | Annotated, Any, List, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query, Request | no |
| `pydantic` | BaseModel | no |
| `sqlalchemy` | func, select | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.auth.gateway_middleware` | get_auth_context | no |
| `app.db` | get_async_session_dep | no |
| `app.models.killswitch` | Incident | no |
| `app.schemas.response` | wrap_dict | no |
| `app.hoc.cus.incidents.L5_engines.incidents_facade` | get_incidents_facade | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

### Violations
| Import | Rule Broken | Required Fix | Line |
|--------|-------------|-------------|------|
| `from app.models.killswitch import Incident` | L2 MUST NOT import L7 models | Use L5 schemas or response models | 54 |
| `from app.hoc.cus.incidents.L5_engines.incidents_facade import get_incidents_facade` | L2 MUST NOT import L5 directly | Route through L3 adapter | 57 |

### Constants
`_CURRENT_ENVIRONMENT`

---
