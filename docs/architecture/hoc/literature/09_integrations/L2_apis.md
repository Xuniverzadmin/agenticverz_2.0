# Integrations — L2 Apis (5 files)

**Domain:** integrations  
**Layer:** L2_apis  
**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

---

## cus_telemetry.py
**Path:** `backend/app/hoc/api/cus/integrations/cus_telemetry.py`  
**Layer:** L2_api | **Domain:** integrations | **Lines:** 391

**Docstring:** Customer LLM Telemetry Ingestion API

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_integration_context` | `(request: Request, x_cus_integration_key: Optional[str] = Header(None, alias='X-` | yes | Extract and validate integration context from request. |
| `ingest_llm_usage` | `(payload: CusLLMUsageIngest, ctx: dict = Depends(get_integration_context))` | yes | Ingest a single LLM usage telemetry record. |
| `ingest_llm_usage_batch` | `(payload: CusLLMUsageBatchIngest, ctx: dict = Depends(get_integration_context))` | yes | Ingest a batch of LLM usage telemetry records. |
| `get_usage_summary` | `(request: Request, integration_id: Optional[str] = Query(None, description='Filt` | yes | Get aggregated usage summary for dashboard. |
| `get_usage_history` | `(request: Request, integration_id: Optional[str] = Query(None, description='Filt` | yes | Get detailed usage history records. |
| `get_daily_aggregates` | `(request: Request, integration_id: Optional[str] = Query(None, description='Filt` | yes | Get daily aggregated usage for charts. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | date, timedelta | no |
| `typing` | Optional | no |
| `fastapi` | APIRouter, Depends, Header, HTTPException, Query (+1) | no |
| `app.schemas.cus_schemas` | CusLLMUsageBatchIngest, CusLLMUsageIngest, CusLLMUsageResponse, CusUsageSummary | no |
| `app.schemas.response` | wrap_dict, wrap_error, wrap_list | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_operation_registry | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L4 spine

**SHOULD call:** L4_spine
**MUST NOT call:** L6_drivers, L7_models
**Called by:** L2.1_facade

---

## mcp_servers.py
**Path:** `backend/app/hoc/api/cus/integrations/mcp_servers.py`  
**Layer:** L2_api | **Domain:** integrations | **Lines:** 748

**Docstring:** MCP Servers API (L2)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `McpServerRegisterRequest` |  | Request body for registering a new MCP server. |
| `McpServerResponse` |  | Response for a single MCP server. |
| `McpServerSummary` |  | Summary view of an MCP server for list endpoint. |
| `McpServerListResponse` |  | Response for listing MCP servers. |
| `McpRegistrationResponse` |  | Response for server registration. |
| `McpDiscoveryResponse` |  | Response for tool discovery. |
| `McpHealthResponse` |  | Response for health check. |
| `McpDeleteResponse` |  | Response for server deletion. |
| `McpToolResponse` |  | Response for a single tool. |
| `McpToolListResponse` |  | Response for listing tools. |
| `McpInvocationSummary` |  | Summary of a tool invocation. |
| `McpInvocationListResponse` |  | Response for listing invocations. |
| `McpInvokeRequest` |  | Request body for invoking an MCP tool. |
| `McpInvokeResponse` |  | Response for tool invocation. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_tenant_id_from_auth` | `(request: Request) -> str` | no | Extract tenant_id from auth_context. Raises 401/403 if missing. |
| `register_mcp_server` | `(request: Request, body: McpServerRegisterRequest, session = Depends(get_session` | yes | Register a new MCP server. Tenant-scoped. |
| `list_mcp_servers` | `(request: Request, include_disabled: Annotated[bool, Query(description='Include ` | yes | List MCP servers. Tenant-scoped. |
| `get_mcp_server` | `(request: Request, server_id: str, session = Depends(get_session_dep)) -> McpSer` | yes | Get MCP server details. Tenant-scoped. |
| `discover_mcp_tools` | `(request: Request, server_id: str, session = Depends(get_session_dep)) -> McpDis` | yes | Discover tools from MCP server. Tenant-scoped. |
| `check_mcp_health` | `(request: Request, server_id: str, session = Depends(get_session_dep)) -> McpHea` | yes | Health check MCP server. Tenant-scoped. |
| `delete_mcp_server` | `(request: Request, server_id: str, session = Depends(get_session_dep)) -> McpDel` | yes | Delete MCP server. Tenant-scoped. |
| `list_mcp_tools` | `(request: Request, server_id: str, session = Depends(get_session_dep)) -> McpToo` | yes | List tools for MCP server. Tenant-scoped. |
| `list_mcp_invocations` | `(request: Request, server_id: str, limit: Annotated[int, Query(ge=1, le=100, des` | yes | List invocations for MCP server. Tenant-scoped. |
| `invoke_mcp_tool` | `(request: Request, server_id: str, tool_id: str, body: McpInvokeRequest, session` | yes | Invoke an MCP tool with governance. Tenant-scoped. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Annotated, Any, Dict, List, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query, Request | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.gateway_middleware` | get_auth_context | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_operation_registry, get_session_dep | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L4 spine

**SHOULD call:** L4_spine
**MUST NOT call:** L6_drivers, L7_models
**Called by:** L2.1_facade

---

## protection_dependencies.py
**Path:** `backend/app/hoc/api/cus/integrations/protection_dependencies.py`  
**Layer:** L2_api | **Domain:** integrations | **Lines:** 243

**Docstring:** Phase-7 Protection Dependencies — FastAPI Integration

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ProtectionContext` |  | Protection context for a request. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `is_exempt_endpoint` | `(path: str) -> bool` | no | Check if an endpoint is exempt from protection. |
| `check_protection` | `(request: Request) -> ProtectionContext` | no | FastAPI dependency: Run protection checks for current request. |
| `require_protection_allow` | `(request: Request) -> ProtectionContext` | no | FastAPI dependency: Require protection checks to pass. |
| `emit_protection_event` | `(context: ProtectionContext) -> dict` | no | Emit a structured protection event for observability. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `typing` | Optional | no |
| `fastapi` | Request, HTTPException | no |
| `logging` | logging | no |
| `app.protection.decisions` | Decision, ProtectionResult, AnomalySignal, allow | no |
| `app.protection.provider` | get_protection_provider | no |
| `app.hoc.cus.account.L5_schemas.onboarding_state` | OnboardingState | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L4 spine

**SHOULD call:** L4_spine
**MUST NOT call:** L6_drivers, L7_models
**Called by:** L2.1_facade

### Constants
`EXEMPT_PREFIXES`

### __all__ Exports
`ProtectionContext`, `check_protection`, `require_protection_allow`, `emit_protection_event`, `is_exempt_endpoint`, `EXEMPT_PREFIXES`

---

## session_context.py
**Path:** `backend/app/hoc/api/cus/integrations/session_context.py`  
**Layer:** L2_api | **Domain:** integrations | **Lines:** 155

**Docstring:** Session Context API

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_session_context` | `(request: Request) -> Dict[str, Any]` | yes | Get verified session context for the current authenticated user. |
| `_fetch_lifecycle_state_name` | `(tenant_id: str) -> str` | yes | Fetch lifecycle state name from DB (Tenant.status). |
| `_get_onboarding_state` | `(tenant_id: str) -> str` | yes | Fetch onboarding state name from DB (Tenant.onboarding_state). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, Dict, List, Optional | no |
| `fastapi` | APIRouter, Request, HTTPException | no |
| `app.auth.contexts` | FounderAuthContext, HumanAuthContext, MachineCapabilityContext | no |
| `app.auth.gateway_middleware` | get_auth_context | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | get_async_session_context, sql_text | no |
| `app.hoc.cus.account.L5_schemas.tenant_lifecycle_enums` | normalize_status | no |
| `app.schemas.response` | wrap_dict | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L4 spine

**SHOULD call:** L4_spine
**MUST NOT call:** L6_drivers, L7_models
**Called by:** L2.1_facade

---

## v1_proxy.py
**Path:** `backend/app/hoc/api/cus/integrations/v1_proxy.py`  
**Layer:** L2_api | **Domain:** integrations | **Lines:** 1256

**Docstring:** M22 KillSwitch MVP - OpenAI-Compatible Proxy API

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ChatMessage` |  |  |
| `ChatCompletionRequest` |  |  |
| `ChatCompletionChoice` |  |  |
| `Usage` |  |  |
| `ChatCompletionResponse` |  |  |
| `EmbeddingRequest` |  |  |
| `EmbeddingData` |  |  |
| `EmbeddingResponse` |  |  |
| `ErrorResponse` |  |  |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_auth_context` | `(authorization: Optional[str] = Header(None), x_api_key: Optional[str] = Header(` | yes | Authenticate request and return tenant/key context. |
| `record_usage_after_killswitch` | `(auth: Dict[str, Any], session) -> None` | yes | Record API key usage ONLY after kill switch passes. |
| `check_killswitch` | `(tenant_id: str, api_key_id: str, session) -> Optional[Dict[str, Any]]` | yes | Check if tenant or API key is frozen. |
| `evaluate_guardrails` | `(request_body: Dict[str, Any], session) -> tuple[bool, List[Dict[str, Any]]]` | yes | Evaluate default guardrails against request. |
| `_evaluate_guardrail` | `(guardrail, context: Dict[str, Any]) -> tuple[bool, Optional[str]]` | no | Evaluate a guardrail dict against context. |
| `calculate_cost` | `(model: str, input_tokens: int, output_tokens: int) -> Decimal` | no | Calculate cost in cents. |
| `estimate_tokens` | `(text: str) -> int` | no | Estimate token count. |
| `get_openai_client` | `()` | no | Get OpenAI client (lazy loaded). |
| `log_proxy_call` | `(session, tenant_id: str, api_key_id: str, endpoint: str, request_body: Dict[str` | yes | Log a proxy call for replay and analysis via L4 registry dispatch. |
| `chat_completions` | `(request: ChatCompletionRequest, auth: Dict[str, Any] = Depends(get_auth_context` | yes | OpenAI-compatible chat completions endpoint. |
| `stream_chat_completion` | `(client, openai_request: Dict[str, Any], request_body: Dict[str, Any], auth: Dic` | yes | Handle streaming chat completion. |
| `embeddings` | `(request: EmbeddingRequest, auth: Dict[str, Any] = Depends(get_auth_context), se` | yes | OpenAI-compatible embeddings endpoint. |
| `proxy_status` | `(authorization: Optional[str] = Header(None), x_api_key: Optional[str] = Header(` | yes | Protection status endpoint - the pulse of your safety net. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `json` | json | no |
| `logging` | logging | no |
| `os` | os | no |
| `time` | time | no |
| `uuid` | uuid | no |
| `datetime` | datetime, timedelta, timezone | no |
| `decimal` | Decimal | no |
| `typing` | Any, AsyncGenerator, Dict, List, Optional | no |
| `fastapi` | APIRouter, Depends, Header, HTTPException | no |
| `fastapi.responses` | StreamingResponse | no |
| `pydantic` | BaseModel | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | get_sync_session_dep, get_operation_registry, OperationContext | no |
| `app.schemas.response` | wrap_dict | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L4 spine

**SHOULD call:** L4_spine
**MUST NOT call:** L6_drivers, L7_models
**Called by:** L2.1_facade

### Constants
`COST_MODELS`, `DEFAULT_MODEL`

---
