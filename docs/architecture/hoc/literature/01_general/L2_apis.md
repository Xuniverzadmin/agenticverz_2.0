# General — L2 Apis (4 files)

**Domain:** general  
**Layer:** L2_apis  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

---

## agents.py
**Path:** `backend/app/hoc/api/cus/general/agents.py`  
**Layer:** L2_api | **Domain:** general | **Lines:** 2762

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CreateJobRequest` |  | Request to create a parallel job. |
| `JobResponse` |  | Job status response. |
| `ClaimItemResponse` |  | Response when claiming an item. |
| `CompleteItemRequest` |  | Request to complete an item. |
| `FailItemRequest` |  | Request to fail an item. |
| `BlackboardWriteRequest` |  | Request to write to blackboard. |
| `BlackboardIncrementRequest` |  | Request to increment counter. |
| `LockRequest` |  | Request for lock operation. |
| `RegisterAgentRequest` |  | Request to register an agent. |
| `SendMessageRequest` |  | Request to send a message. |
| `InvokeResponseRequest` |  | Request to respond to an invocation. |
| `SimulateJobRequest` |  | Request to simulate job execution before committing. |
| `SimulateJobResponse` |  | Response from job simulation. |
| `SBAValidateRequest` |  | Request to validate SBA schema. |
| `SBARegisterRequest` |  | Request to register agent with SBA. |
| `SBAGenerateRequest` |  | Request to auto-generate SBA for an agent. |
| `WorkerCostMetrics` |  | Worker cost and risk metrics. |
| `ActivityCostsResponse` |  | Response for activity costs endpoint. |
| `SpendingDataResponse` |  | Response for spending tracker endpoint. |
| `RetryEntryResponse` |  | Single retry entry. |
| `ActivityRetriesResponse` |  | Response for retries endpoint. |
| `BlockerEntry` |  | Single blocker entry. |
| `ActivityBlockersResponse` |  | Response for blockers endpoint. |
| `HealthCheckItem` |  | Single health check result. |
| `HealthCheckResponse` |  | Response for health check endpoint. |
| `CascadeEvaluateRequest` |  | Request for cascade evaluation. |
| `RoutingDispatchRequest` |  | Request for routing dispatch. |
| `RoutingConfigUpdate` |  | Request to update agent routing config. |
| `ExplainRoutingResponse` |  | Response explaining a routing decision. |
| `EvolutionReportResponse` |  | Response with agent evolution history. |
| `SystemStabilityResponse` |  | Response with system-wide stability metrics. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `simulate_job` | `(request: SimulateJobRequest, x_tenant_id: str = Header(default='default', alias` | yes | Simulate job execution before committing resources. |
| `create_job` | `(request: CreateJobRequest, x_tenant_id: str = Header(default='default', alias='` | yes | Create a new parallel job. |
| `get_job` | `(job_id: str)` | yes | Get job status by ID. |
| `cancel_job` | `(job_id: str)` | yes | Cancel a running job. |
| `claim_item` | `(job_id: str, worker_instance_id: str = Query(..., description='Worker instance ` | yes | Worker claims next available item. |
| `complete_item` | `(job_id: str, item_id: str, request: CompleteItemRequest)` | yes | Mark item as completed with output. |
| `fail_item` | `(job_id: str, item_id: str, request: FailItemRequest)` | yes | Mark item as failed. |
| `get_blackboard` | `(key: str)` | yes | Read value from blackboard. |
| `put_blackboard` | `(key: str, request: BlackboardWriteRequest)` | yes | Write value to blackboard. |
| `increment_blackboard` | `(key: str, request: BlackboardIncrementRequest)` | yes | Atomically increment a counter. |
| `lock_blackboard` | `(key: str, request: LockRequest)` | yes | Lock operation on blackboard. |
| `register_agent` | `(request: RegisterAgentRequest)` | yes | Register an agent instance. |
| `agent_heartbeat` | `(instance_id: str)` | yes | Update agent heartbeat. |
| `deregister_agent` | `(instance_id: str)` | yes | Deregister an agent instance. |
| `get_agent` | `(instance_id: str)` | yes | Get agent instance details. |
| `list_agents` | `(agent_id: Optional[str] = Query(default=None), job_id: Optional[str] = Query(de` | yes | List agent instances. |
| `send_message` | `(instance_id: str, request: SendMessageRequest)` | yes | Send a message to an agent. |
| `get_messages` | `(instance_id: str, status: Optional[str] = Query(default=None), message_type: Op` | yes | Get messages for an agent. |
| `mark_message_read` | `(instance_id: str, message_id: str)` | yes | Mark message as read. |
| `respond_to_invocation` | `(request: InvokeResponseRequest)` | yes | Respond to an agent invocation. |
| `validate_sba_endpoint` | `(request: SBAValidateRequest)` | yes | Validate an SBA schema. |
| `register_agent_with_sba` | `(request: SBARegisterRequest, x_tenant_id: str = Header(default='default', alias` | yes | Register an agent with its SBA schema. |
| `generate_sba_for_agent` | `(request: SBAGenerateRequest)` | yes | Auto-generate SBA for an agent. |
| `get_sba_version_info` | `()` | yes | M15.1.1: Get SBA version negotiation info. |
| `negotiate_sba_version` | `(requested_version: str = Query(..., description='Requested SBA version'))` | yes | M15.1.1: Negotiate SBA version. |
| `get_sba_health` | `(x_tenant_id: str = Header(default='default', alias='X-Tenant-ID'))` | yes | M16: Get aggregated strategy health for Guard Console. |
| `get_agent_sba` | `(agent_id: str)` | yes | Get SBA schema for an agent. |
| `list_agents_sba` | `(agent_type: Optional[str] = Query(default=None), sba_validated: Optional[bool] ` | yes | List agents with their SBA status. |
| `check_spawn_allowed` | `(agent_id: str = Query(..., description='Agent ID to check'), orchestrator: Opti` | yes | Check if agent is allowed to spawn. |
| `get_fulfillment_aggregated` | `(group_by: str = Query(default='domain', description='Group by: domain, agent_ty` | yes | M15.1.1: Get aggregated fulfillment metrics for heatmap visualization. |
| `get_agent_activity_costs` | `(agent_id: str, x_tenant_id: str = Header(default='default', alias='X-Tenant-ID'` | yes | M16: Get worker cost and risk metrics for an agent. |
| `get_agent_activity_spending` | `(agent_id: str, period: str = Query(default='24h', description='Time period: 1h,` | yes | M16: Get spending data for budget burn chart. |
| `get_agent_activity_retries` | `(agent_id: str, limit: int = Query(default=50, le=200), x_tenant_id: str = Heade` | yes | M16: Get retry log for an agent. |
| `get_agent_activity_blockers` | `(agent_id: str, x_tenant_id: str = Header(default='default', alias='X-Tenant-ID'` | yes | M16: Get current blockers for an agent. |
| `check_agent_health` | `(agent_id: str, x_tenant_id: str = Header(default='default', alias='X-Tenant-ID'` | yes | M16: Run comprehensive health check for an agent. |
| `cascade_evaluate` | `(request: CascadeEvaluateRequest, x_tenant_id: str = Header(default='default', a` | yes | M17: Evaluate agents through CARE pipeline without routing. |
| `routing_dispatch` | `(request: RoutingDispatchRequest, x_tenant_id: str = Header(default='default', a` | yes | M17: Execute full CARE routing pipeline and select best agent. |
| `get_agent_strategy` | `(agent_id: str)` | yes | M17: Get agent's Strategy Cascade. |
| `update_agent_strategy` | `(agent_id: str, update: RoutingConfigUpdate)` | yes | M17: Hot-swap agent's routing configuration. |
| `get_routing_stats` | `(x_tenant_id: str = Header(default='default', alias='X-Tenant-ID'))` | yes | M17: Get routing statistics. |
| `explain_routing_decision` | `(request_id: str, x_tenant_id: str = Header(default='default', alias='X-Tenant-I` | yes | M18: Explain why a routing decision was made. |
| `get_agent_evolution` | `(agent_id: str, include_acknowledged: bool = Query(default=False, description='I` | yes | M18: Get agent evolution history and current state. |
| `get_system_stability` | `()` | yes | M18: Get system-wide stability metrics. |
| `freeze_system` | `(duration_seconds: int = Query(default=900, ge=60, le=3600, description='Freeze ` | yes | M18: Manually freeze the learning system. |
| `unfreeze_system` | `()` | yes | M18: Manually unfreeze the learning system. |
| `trigger_batch_learning` | `(window_hours: int = Query(default=1, ge=1, le=24, description='Hours of data to` | yes | M18: Trigger batch learning process. |
| `get_agent_reputation` | `(agent_id: str)` | yes | M18: Get agent reputation details. |
| `get_agent_sla` | `(agent_id: str)` | yes | M18: Get agent SLA score details. |
| `get_agent_successors` | `(agent_id: str)` | yes | M18: Get successor mapping for agent failover. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | UUID | no |
| `fastapi` | APIRouter, Header, HTTPException, Query | no |
| `pydantic` | BaseModel, Field | no |
| `agents.services.blackboard_service` | get_blackboard_service | yes |
| `schemas.response` | wrap_dict | yes |
| `agents.services.credit_service` | CREDIT_COSTS, get_credit_service | yes |
| `agents.services.job_service` | JobConfig, get_job_service | yes |
| `agents.services.message_service` | get_message_service | yes |
| `agents.services.registry_service` | get_registry_service | yes |
| `agents.services.worker_service` | get_worker_service | yes |
| `agents.skills.agent_invoke` | AgentInvokeSkill | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## debug_auth.py
**Path:** `backend/app/hoc/api/cus/general/debug_auth.py`  
**Layer:** L2_api | **Domain:** general | **Lines:** 278

**Docstring:** Debug Auth Context Endpoint

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AuthContextDebugResponse` |  | Debug response showing current auth context state. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_mask_value` | `(value: str, visible_chars: int = 8) -> str` | no | Mask a sensitive value, showing only first N chars. |
| `_get_tenant_state` | `(tenant_id: Optional[str]) -> tuple[Optional[str], Optional[int]]` | yes | Get the DERIVED tenant state (not cached). |
| `get_auth_context` | `(request: Request)` | yes | Debug endpoint: Show current auth context. |
| `get_auth_planes` | `()` | yes | Debug endpoint: Show available auth planes and their characteristics. |
| `get_tenant_states` | `()` | yes | Debug endpoint: Show tenant state definitions. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timezone | no |
| `typing` | Any, Dict, Optional | no |
| `fastapi` | APIRouter, Request | no |
| `pydantic` | BaseModel | no |
| `app.schemas.response` | wrap_dict | no |
| `app.auth.contexts` | AuthPlane, FounderAuthContext, HumanAuthContext, MachineCapabilityContext | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## health.py
**Path:** `backend/app/hoc/api/cus/general/health.py`  
**Layer:** L2_api | **Domain:** general | **Lines:** 171

**Docstring:** Health and Determinism Status Endpoints

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `update_replay_hash` | `(workflow_name: str, output_hash: str)` | no | Update the determinism state after a replay test. |
| `report_drift` | `(workflow_name: str, expected: str, actual: str)` | no | Report a determinism drift. |
| `health_check` | `() -> Dict[str, Any]` | yes | Basic health check endpoint. |
| `readiness_check` | `() -> Dict[str, Any]` | yes | Kubernetes readiness probe. |
| `determinism_status` | `() -> Dict[str, Any]` | yes | Determinism status endpoint. |
| `adapter_status` | `() -> Dict[str, Any]` | yes | LLM adapter availability status. |
| `skills_status` | `() -> Dict[str, Any]` | yes | Skill registry status. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timezone | no |
| `typing` | Any, Dict | no |
| `fastapi` | APIRouter | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## sdk.py
**Path:** `backend/app/hoc/api/cus/general/sdk.py`  
**Layer:** L2_api | **Domain:** general | **Lines:** 226

**Docstring:** SDK Endpoints

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `HandshakeRequest` |  | SDK handshake request. |
| `HandshakeResponse` |  | SDK handshake response. |
| `InstructionsResponse` |  | SDK setup instructions response. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_maybe_advance_to_sdk_connected` | `(tenant_id: str) -> Optional[str]` | yes | PIN-399: Trigger onboarding state transition on first SDK handshake. |
| `sdk_handshake` | `(request: Request, body: HandshakeRequest)` | yes | SDK handshake endpoint. |
| `get_sdk_instructions` | `(request: Request)` | yes | Get SDK setup instructions. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `datetime` | datetime, timezone | no |
| `typing` | Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Request, status | no |
| `pydantic` | BaseModel, Field | no |
| `auth.gateway_middleware` | get_auth_context | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---
