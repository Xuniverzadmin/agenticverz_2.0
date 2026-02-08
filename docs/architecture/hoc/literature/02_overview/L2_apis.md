# Overview — L2 Apis (1 files)

**Domain:** overview  
**Layer:** L2_apis  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

---

## overview.py
**Path:** `backend/app/hoc/api/cus/overview/overview.py`  
**Layer:** L2_api | **Domain:** overview | **Lines:** 561

**Docstring:** Unified Overview API (L2)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `DomainCount` |  | Count for a specific domain. |
| `SystemPulse` |  | System health pulse summary. |
| `HighlightsResponse` |  | GET /highlights response (O1). |
| `DecisionItem` |  | A pending decision requiring human action. |
| `Pagination` |  | Pagination metadata. |
| `DecisionsResponse` |  | GET /decisions response (O2). |
| `CostPeriod` |  | Time period for cost calculation. |
| `CostActuals` |  | Actual costs incurred. |
| `LimitCostItem` |  | Single limit with cost status. |
| `CostViolations` |  | Cost violation summary. |
| `CostsResponse` |  | GET /costs response (O2). |
| `DecisionsCountResponse` |  | GET /decisions/count response. |
| `RecoveryStatsResponse` |  | GET /recovery-stats response. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `require_preflight` | `() -> None` | no | Guard for preflight-only endpoints (O4, O5). |
| `get_tenant_id_from_auth` | `(request: Request) -> str` | no | Extract tenant_id from auth_context. Raises 401/403 if missing. |
| `get_highlights` | `(request: Request, session = Depends(get_session_dep)) -> HighlightsResponse` | yes | System pulse and domain counts. Tenant-scoped. |
| `get_decisions` | `(request: Request, source_domain: Annotated[str | None, Query(description='Filte` | yes | Pending decisions from incidents and policy proposals. Tenant-scoped. |
| `get_costs` | `(request: Request, period_days: Annotated[int, Query(ge=1, le=365, description='` | yes | Cost intelligence summary. Tenant-scoped. |
| `get_decisions_count` | `(request: Request, session = Depends(get_session_dep)) -> DecisionsCountResponse` | yes | Decisions count by domain and priority. Tenant-scoped. |
| `get_recovery_stats` | `(request: Request, period_days: Annotated[int, Query(ge=1, le=365, description='` | yes | Recovery statistics from incidents. Tenant-scoped. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `datetime` | datetime | no |
| `typing` | Annotated, Any, List, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query, Request | no |
| `pydantic` | BaseModel | no |
| `app.auth.gateway_middleware` | get_auth_context | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_operation_registry, get_session_dep | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

### Constants
`_CURRENT_ENVIRONMENT`

---
