# Activity — L2 Apis (1 files)

**Domain:** activity  
**Layer:** L2_apis  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

---

## activity.py
**Path:** `backend/app/hoc/api/cus/activity/activity.py`  
**Layer:** L2_api | **Domain:** activity | **Lines:** 2293

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `RunState` |  | Run lifecycle state. |
| `RunStatus` |  | Run execution status. |
| `RiskLevel` |  | Risk classification. |
| `LatencyBucket` |  | Latency classification. |
| `EvidenceHealth` |  | Evidence capture health. |
| `IntegrityStatus` |  | Integrity verification status. |
| `RunSource` |  | Run initiator type. |
| `ProviderType` |  | LLM provider. |
| `SortField` |  | Allowed sort fields. |
| `SortOrder` |  | Sort direction. |
| `EvaluationOutcome` |  | Policy evaluation outcome. |
| `PolicyScope` |  | Policy/limit scope. |
| `RiskType` |  | Risk type classification for panels. |
| `PolicyContext` |  | Policy context for a run (V2). |
| `RunSummaryV2` |  | Run summary with policy context (V2). |
| `Pagination` |  | Pagination metadata. |
| `LiveRunsResponse` |  | GET /activity/live response (V2). |
| `CompletedRunsResponse` |  | GET /activity/completed response (V2). |
| `SignalFeedbackModel` |  | Feedback state for a signal. |
| `SignalProjection` |  | A signal projection (V2). |
| `SignalsResponse` |  | GET /activity/signals response (V2). |
| `MetricsResponse` |  | GET /activity/metrics response (V2). |
| `ThresholdSignal` |  | A threshold proximity signal (V2). |
| `ThresholdSignalsResponse` |  | GET /activity/threshold-signals response (V2). |
| `SignalAckRequest` |  | POST /activity/signals/{signal_fingerprint}/ack request. |
| `SignalAckResponse` |  | POST /activity/signals/{signal_fingerprint}/ack response. |
| `SignalSuppressRequest` |  | POST /activity/signals/{signal_fingerprint}/suppress request. |
| `SignalSuppressResponse` |  | POST /activity/signals/{signal_fingerprint}/suppress response. |
| `RunSummary` |  | Run summary for list view (O2). |
| `RunListResponse` |  | GET /runs response. |
| `RunDetailResponse` |  | GET /runs/{run_id} response (O3). |
| `StatusBucket` |  | A bucket in status summary. |
| `StatusSummaryResponse` |  | GET /summary/by-status response (COMP-O3). |
| `DimensionValue` |  | Allowed dimension values for grouping. |
| `DimensionGroup` |  | A group in dimension breakdown. |
| `DimensionBreakdownResponse` |  | GET /runs/by-dimension response (LIVE-O5). |
| `PatternMatchResponse` |  | A detected pattern. |
| `PatternDetectionResponse` |  | GET /patterns response (SIG-O3). |
| `AgentCostResponse` |  | Cost analysis for a single agent. |
| `CostAnalysisResponse` |  | GET /cost-analysis response (SIG-O4). |
| `AttentionItemResponse` |  | An item in the attention queue. |
| `AttentionQueueResponse` |  | GET /attention-queue response (SIG-O5). |
| `RiskSignalsResponse` |  | GET /risk-signals response. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `require_preflight` | `() -> None` | no | Guard for preflight-only endpoints (O4, O5). |
| `get_tenant_id_from_auth` | `(request: Request) -> str` | no | Extract tenant_id from auth_context. Raises 401/403 if missing. |
| `list_runs` | `(request: Request, project_id: Annotated[str | None, Query(description='Project ` | yes | List runs with unified query filters. READ-ONLY from v_runs_o2 view. |
| `get_run_detail` | `(request: Request, run_id: str, session = Depends(get_session_dep)) -> RunDetail` | yes | Get run detail (O3). Tenant isolation enforced. |
| `get_run_evidence` | `(request: Request, run_id: str) -> dict[str, Any]` | yes | Get run evidence (O4). Preflight console only. |
| `get_run_proof` | `(request: Request, run_id: str, include_payloads: bool = False) -> dict[str, Any` | yes | Get run proof (O5). Preflight console only. |
| `get_summary_by_status` | `(request: Request, state: Annotated[RunState | None, Query(description='Filter b` | yes | Get run summary by status (COMP-O3). READ-ONLY from v_runs_o2. |
| `_get_runs_by_dimension_internal` | `(session, tenant_id: str, dim: DimensionValue, state: RunState, limit: int = 20)` | yes | Internal helper for dimension breakdown with HARDCODED state binding. |
| `get_live_runs_by_dimension` | `(request: Request, dim: Annotated[DimensionValue, Query(description='Dimension t` | yes | Get LIVE runs grouped by dimension. State=LIVE is hardcoded. |
| `get_completed_runs_by_dimension` | `(request: Request, dim: Annotated[DimensionValue, Query(description='Dimension t` | yes | Get COMPLETED runs grouped by dimension. State=COMPLETED is hardcoded. |
| `get_runs_by_dimension` | `(request: Request, dim: Annotated[DimensionValue, Query(description='Dimension t` | yes | [INTERNAL] Get runs grouped by dimension with optional state. NOT FOR PANELS. |
| `get_patterns` | `(request: Request, window_hours: Annotated[int, Query(ge=1, le=168, description=` | yes | Detect instability patterns (SIG-O3). READ-ONLY from aos_traces/aos_trace_steps. |
| `get_cost_analysis` | `(request: Request, baseline_days: Annotated[int, Query(ge=1, le=30, description=` | yes | Analyze cost anomalies (SIG-O4). READ-ONLY from runs table. |
| `get_attention_queue` | `(request: Request, limit: Annotated[int, Query(ge=1, le=100, description='Max it` | yes | Get attention queue (SIG-O5). READ-ONLY from v_runs_o2. |
| `get_risk_signals` | `(request: Request, session = Depends(get_session_dep)) -> RiskSignalsResponse` | yes | Returns aggregated risk signal counts. |
| `_extract_policy_context` | `(row: dict) -> PolicyContext` | no | Extract PolicyContext from a v_runs_o2 row (V2 schema). |
| `_policy_context_from_l5` | `(pc: Any) -> PolicyContext` | no | Convert L5 PolicyContextResult dataclass to L2 PolicyContext Pydantic model. |
| `_run_summary_v2_from_l5` | `(item: Any) -> RunSummaryV2` | no | Convert L5 RunSummaryV2Result dataclass to L2 RunSummaryV2 Pydantic model. |
| `_row_to_run_summary_v2` | `(row: dict) -> RunSummaryV2` | no | Convert a v_runs_o2 row to RunSummaryV2. |
| `list_live_runs` | `(request: Request, project_id: Annotated[str | None, Query(description='Project ` | yes | List LIVE runs with policy context. |
| `list_completed_runs` | `(request: Request, project_id: Annotated[str | None, Query(description='Project ` | yes | List COMPLETED runs with policy context. |
| `list_signals` | `(request: Request, project_id: Annotated[str | None, Query(description='Project ` | yes | List activity signals (V2 projection). |
| `get_activity_metrics` | `(request: Request, session = Depends(get_session_dep)) -> MetricsResponse` | yes | Get aggregated activity metrics (V2). |
| `get_threshold_signals` | `(request: Request, risk_type: Annotated[RiskType | None, Query(description='Filt` | yes | Get threshold proximity signals (V2). |
| `acknowledge_signal` | `(request: Request, signal_fingerprint: Annotated[str, Path(description='Canonica` | yes | Acknowledge a signal. |
| `suppress_signal` | `(request: Request, signal_fingerprint: Annotated[str, Path(description='Canonica` | yes | Suppress a signal temporarily. |
| `get_actor_id_from_auth` | `(request: Request) -> str` | no | Extract actor ID from request auth context. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `os` | os | no |
| `datetime` | datetime, timedelta | no |
| `enum` | Enum | no |
| `typing` | Annotated, Any | no |
| `fastapi` | APIRouter, Depends, HTTPException, Path, Query (+1) | no |
| `pydantic` | BaseModel | no |
| `app.auth.gateway_middleware` | get_auth_context | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_operation_registry, get_session_dep | no |
| `app.schemas.response` | wrap_dict | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

### Constants
`_CURRENT_ENVIRONMENT`

---
