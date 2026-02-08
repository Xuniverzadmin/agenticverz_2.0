# Logs — L2 Apis (4 files)

**Domain:** logs  
**Layer:** L2_apis  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

---

## cost_intelligence.py
**Path:** `backend/app/hoc/api/cus/logs/cost_intelligence.py`  
**Layer:** L2_api | **Domain:** logs | **Lines:** 903

**Docstring:** M26 Cost Intelligence API

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `FeatureTagCreate` |  | Create a new feature tag. |
| `FeatureTagResponse` |  | Feature tag response. |
| `FeatureTagUpdate` |  | Update a feature tag. |
| `CostRecordCreate` |  | Record a cost entry. |
| `CostProvenance` |  | Provenance metadata for cost interpretation panels. |
| `CostSummary` |  | Cost summary for a period. |
| `CostByFeature` |  | Cost breakdown by feature. |
| `CostByUser` |  | Cost breakdown by user. |
| `CostByModel` |  | Cost breakdown by model. |
| `CostProjection` |  | Cost projection for upcoming period. |
| `CostAnomalyResponse` |  | Cost anomaly response. |
| `AnalyticsProvenance` |  | Provenance envelope for analytics interpretation panels. |
| `CostByUserEnvelope` |  | Envelope response for cost by user with provenance. |
| `CostByModelEnvelope` |  | Envelope response for cost by model with provenance. |
| `CostByFeatureEnvelope` |  | Envelope response for cost by feature with provenance. |
| `CostAnomaliesEnvelope` |  | Envelope response for cost anomalies with provenance. |
| `CostDashboard` |  | Complete cost dashboard data. |
| `BudgetCreate` |  | Create or update a budget. |
| `BudgetResponse` |  | Budget response. |
| `AnomalyDetectionRequest` |  | Request to trigger anomaly detection. |
| `AnomalyDetectionResponse` |  | Response from anomaly detection. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_get_cost_write_service` | `(session)` | no | Get cost write service via L4 analytics bridge (PIN-520 compliance). |
| `_get_cost_intelligence_engine` | `(session)` | no | Get cost intelligence engine via L4 logs bridge (L2 purity migration). |
| `get_tenant_id` | `(tenant_id: str = Query(..., description='Tenant ID')) -> str` | no | Extract tenant_id from query parameter. |
| `create_feature_tag` | `(data: FeatureTagCreate, tenant_id: str = Depends(get_tenant_id), session = Depe` | yes | Register a new feature tag. |
| `list_feature_tags` | `(include_inactive: bool = False, tenant_id: str = Depends(get_tenant_id), sessio` | yes | List all feature tags for the tenant. |
| `update_feature_tag` | `(tag: str, data: FeatureTagUpdate, tenant_id: str = Depends(get_tenant_id), sess` | yes | Update a feature tag. |
| `record_cost` | `(data: CostRecordCreate, tenant_id: str = Depends(get_tenant_id), session = Depe` | yes | Record a cost entry. |
| `get_cost_dashboard` | `(period: str = Query('24h', regex='^(24h|7d|30d)$'), tenant_id: str = Depends(ge` | yes | Get complete cost dashboard. |
| `get_cost_summary` | `(period: str = Query('24h', regex='^(24h|7d|30d)$'), tenant_id: str = Depends(ge` | yes | Get cost summary for the period. |
| `get_costs_by_feature` | `(period: str = Query('24h', regex='^(24h|7d|30d)$'), tenant_id: str = Depends(ge` | yes | Get cost breakdown by feature tag. |
| `get_costs_by_user` | `(period: str = Query('24h', regex='^(24h|7d|30d)$'), tenant_id: str = Depends(ge` | yes | Get cost breakdown by user with anomaly detection. |
| `get_costs_by_model` | `(period: str = Query('24h', regex='^(24h|7d|30d)$'), tenant_id: str = Depends(ge` | yes | Get cost breakdown by model. |
| `get_anomalies` | `(days: int = Query(7, ge=1, le=90), include_resolved: bool = False, tenant_id: s` | yes | Get detected cost anomalies. |
| `get_projection` | `(lookback_days: int = Query(7, ge=1, le=30), forecast_days: int = Query(7, ge=1,` | yes | Get cost projection based on historical data. |
| `create_or_update_budget` | `(data: BudgetCreate, tenant_id: str = Depends(get_tenant_id), session = Depends(` | yes | Create or update a budget. |
| `list_budgets` | `(tenant_id: str = Depends(get_tenant_id), session = Depends(get_sync_session_dep` | yes | List all budgets for the tenant. |
| `trigger_anomaly_detection` | `(request: AnomalyDetectionRequest = AnomalyDetectionRequest(), tenant_id: str = ` | yes | Trigger anomaly detection for this tenant. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `datetime` | datetime, timedelta | no |
| `typing` | List, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query | no |
| `pydantic` | BaseModel, Field | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | get_sync_session_dep | no |
| `app.hoc.cus.hoc_spine.services.time` | utc_now | no |
| `app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.analytics_bridge` | get_analytics_bridge | no |
| `app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.logs_bridge` | get_logs_bridge | no |
| `app.schemas.response` | wrap_dict | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## guard_logs.py
**Path:** `backend/app/hoc/api/cus/logs/guard_logs.py`  
**Layer:** L2_api | **Domain:** logs | **Lines:** 215

**Docstring:** Guard Logs API - Customer Console Logs Endpoint

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `list_logs` | `(tenant_id: str = Query(..., description='Tenant ID (required)'), agent_id: Opti` | yes | List execution logs for customer. |
| `export_logs` | `(tenant_id: str = Query(..., description='Tenant ID (required)'), format: str = ` | yes | Export logs for customer. |
| `get_log` | `(log_id: str, tenant_id: str = Query(..., description='Tenant ID (required)'))` | yes | Get log detail with execution steps. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query | no |
| `fastapi.responses` | StreamingResponse | no |
| `app.adapters.customer_logs_adapter` | CustomerLogDetail, CustomerLogListResponse, get_customer_logs_adapter | no |
| `app.auth.console_auth` | verify_console_token | no |
| `app.schemas.response` | wrap_dict | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## tenants.py
**Path:** `backend/app/hoc/api/cus/logs/tenants.py`  
**Layer:** L2_api | **Domain:** logs | **Lines:** 677

**Docstring:** Tenant & API Key Management API (M21)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `TenantResponse` |  | Tenant information response. |
| `APIKeyCreateRequest` |  | Request to create an API key. |
| `APIKeyResponse` |  | API key information (without the actual key). |
| `APIKeyCreatedResponse` |  | Response when creating an API key (includes the key once). |
| `AnalyticsProvenance` |  | Provenance envelope for analytics interpretation panels. |
| `UsageSummaryResponse` |  | Usage summary for a tenant with provenance for SDSR ANALYTICS domain. |
| `WorkerSummaryResponse` |  | Worker summary information. |
| `WorkerDetailResponse` |  | Detailed worker information. |
| `WorkerConfigRequest` |  | Request to configure a worker for a tenant. |
| `WorkerConfigResponse` |  | Worker configuration response. |
| `RunHistoryItem` |  | Run history item. |
| `QuotaCheckResponse` |  | Quota check response. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_services` | `(session = Depends(get_sync_session_dep))` | no | Get worker registry and session for route handlers. |
| `_tenant_op` | `(session, tenant_id: str, method: str, **kwargs)` | yes | Execute a tenant operation via L4 registry (account.tenant). |
| `_api_keys_op` | `(session, tenant_id: str, method: str, **kwargs)` | yes | Execute an API keys operation via L4 registry (api_keys.write). |
| `_maybe_advance_to_api_key_created` | `(tenant_id: str) -> None` | yes | PIN-399: Trigger onboarding state transition on first API key creation. |
| `get_current_tenant` | `(ctx: TenantContext = Depends(get_tenant_context), services: dict = Depends(get_` | yes | Get information about the current tenant (from API key). |
| `get_tenant_usage` | `(period: str = Query('24h', regex='^(24h|7d|30d)$'), ctx: TenantContext = Depend` | yes | Get usage summary for the current tenant. |
| `check_run_quota` | `(ctx: TenantContext = Depends(get_tenant_context), services: dict = Depends(get_` | yes | Check if the tenant can create a new run. |
| `check_token_quota` | `(tokens_needed: int = Query(default=10000, ge=1), ctx: TenantContext = Depends(g` | yes | Check if the tenant has token budget for an operation. |
| `list_api_keys` | `(include_revoked: bool = False, ctx: TenantContext = Depends(get_tenant_context)` | yes | List all API keys for the current tenant. |
| `create_api_key` | `(request: APIKeyCreateRequest, ctx: TenantContext = Depends(get_tenant_context),` | yes | Create a new API key for the current tenant. |
| `revoke_api_key` | `(key_id: str, reason: str = Query(default='Manual revocation'), ctx: TenantConte` | yes | Revoke an API key. |
| `list_workers` | `(status: Optional[str] = None, ctx: TenantContext = Depends(get_tenant_context),` | yes | List all available workers. |
| `list_available_workers_for_tenant` | `(include_disabled: bool = False, ctx: TenantContext = Depends(get_tenant_context` | yes | List workers available to the current tenant with their configurations. |
| `get_worker_details` | `(worker_id: str, ctx: TenantContext = Depends(get_tenant_context), services: dic` | yes | Get detailed information about a specific worker. |
| `get_worker_config` | `(worker_id: str, ctx: TenantContext = Depends(get_tenant_context), services: dic` | yes | Get the effective configuration for a worker (tenant overrides merged with defau |
| `set_worker_config` | `(worker_id: str, request: WorkerConfigRequest, ctx: TenantContext = Depends(get_` | yes | Set tenant-specific configuration for a worker. |
| `list_runs` | `(limit: int = Query(default=20, ge=1, le=100), offset: int = Query(default=0, ge` | yes | List runs for the current tenant. |
| `tenant_health` | `()` | yes | Health check for tenant system. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `datetime` | datetime, timezone | no |
| `typing` | List, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query, status | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.tenant_auth` | TenantContext, get_tenant_context | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_operation_registry, get_sync_session_dep | no |
| `app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges` | get_integrations_driver_bridge | no |
| `app.schemas.response` | wrap_dict, wrap_list | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## traces.py
**Path:** `backend/app/hoc/api/cus/logs/traces.py`  
**Layer:** L2_api | **Domain:** logs | **Lines:** 910

**Docstring:** Trace Query API

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `User` | __init__, has_role, from_token | User model for RBAC - wraps JWT TokenPayload for backwards compatibility. |
| `TraceSummaryResponse` |  | Trace summary for list views. |
| `TraceStepResponse` |  | Individual trace step. |
| `TraceDetailResponse` |  | Full trace with all steps. |
| `TraceListResponse` |  | Paginated trace list. |
| `TraceCompareResponse` |  | Result of comparing two traces. |
| `StoreTraceRequest` |  | Request to store a client-provided trace. |
| `MismatchReport` |  | Report a replay mismatch for operator review. |
| `MismatchResponse` |  | Response after reporting a mismatch. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_current_user` | `(request: Request, token: TokenPayload = Depends(_jwt_auth)) -> User` | yes | Get current authenticated user from JWT token. |
| `require_role` | `(user: User, role: str) -> bool` | no | Check if user has required role. |
| `get_trace_store` | `() -> TraceStoreType` | no | Get the trace store instance. |
| `list_traces` | `(tenant_id: Optional[str] = Query(None, description='Filter by tenant ID'), agen` | yes | List and search traces with optional filters. |
| `store_trace` | `(request: StoreTraceRequest, store: TraceStoreType = Depends(get_trace_store), u` | yes | Store a client-provided trace. |
| `list_all_mismatches` | `(window: Optional[str] = Query(None, description='Time window (e.g., 24h, 7d)'),` | yes | List all trace mismatches across the system. |
| `get_trace` | `(run_id: str, store: TraceStoreType = Depends(get_trace_store), user: User = Dep` | yes | Get a complete trace by run ID. |
| `get_trace_by_hash` | `(root_hash: str, store: TraceStoreType = Depends(get_trace_store), user: User = ` | yes | Get a trace by its deterministic root hash. |
| `compare_traces` | `(run_id1: str, run_id2: str, store: TraceStoreType = Depends(get_trace_store), u` | yes | Compare two traces for deterministic equality. |
| `delete_trace` | `(run_id: str, store: TraceStoreType = Depends(get_trace_store), user: User = Dep` | yes | Delete a trace by run ID. |
| `cleanup_old_traces` | `(days: int = Query(30, ge=1, le=365, description='Delete traces older than N day` | yes | Delete traces older than specified number of days. |
| `check_idempotency` | `(idempotency_key: str, store: TraceStoreType = Depends(get_trace_store), user: U` | yes | Check if an idempotency key has been executed. |
| `bulk_report_mismatches` | `(mismatch_ids: List[str] = Query(..., description='List of mismatch IDs to link'` | yes | Create a single GitHub issue for multiple mismatches. |
| `report_mismatch` | `(trace_id: str, payload: MismatchReport, store: TraceStoreType = Depends(get_tra` | yes | Report a replay mismatch for operator review. |
| `list_trace_mismatches` | `(trace_id: str, user: User = Depends(get_current_user))` | yes | List all mismatches reported for a trace. |
| `resolve_mismatch` | `(trace_id: str, mismatch_id: str, resolution_note: Optional[str] = Query(None, d` | yes | Mark a mismatch as resolved. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `typing` | List, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query, Request (+2) | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.jwt_auth` | JWTAuthDependency, JWTConfig, TokenPayload | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_async_session_context, get_operation_registry, get_session_dep | no |
| `app.schemas.response` | wrap_dict | no |
| `app.traces.redact` | redact_trace_data | no |
| `app.hoc.cus.hoc_spine.orchestrator.handlers.traces_handler` | register_traces_handlers | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

### Constants
`USE_POSTGRES`

---
