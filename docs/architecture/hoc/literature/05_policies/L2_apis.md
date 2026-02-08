# Policies — L2 Apis (37 files)

**Domain:** policies  
**Layer:** L2_apis  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

---

## M25_integrations.py
**Path:** `backend/app/hoc/api/cus/policies/M25_integrations.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 1384

**Docstring:** M25 Integration API

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `LoopStatusResponse` |  | Response for loop status endpoint. |
| `StageDetail` |  | Detail for a single stage. |
| `CheckpointResponse` |  | Response for human checkpoint. |
| `ResolveCheckpointRequest` |  | Request to resolve a checkpoint. |
| `IntegrationStatsResponse` |  | Statistics for integration loop. |
| `RetryStageRequest` |  | Request to retry a failed stage. |
| `RevertLoopRequest` |  | Request to revert a loop. |
| `GateEvidenceResponse` |  | Evidence for a graduation gate. |
| `CapabilityStatus` |  | Status of a capability gate. |
| `SimulationStatus` |  | Simulation mode status - separate from real graduation. |
| `HardenedGraduationResponse` |  | Hardened graduation status response. |
| `SimulatePreventionRequest` |  | Request to simulate a prevention event for demo/testing. |
| `SimulateRegretRequest` |  | Request to simulate a regret event for demo/testing. |
| `TimelineEventResponse` |  | A single event in the prevention timeline. |
| `PreventionTimelineResponse` |  | Response for prevention timeline endpoint. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_tenant_id_from_token` | `(token: FounderToken = Depends(verify_fops_token)) -> str` | no | Get tenant ID from founder token - PIN-318 secure implementation. |
| `get_current_user_from_token` | `(token: FounderToken = Depends(verify_fops_token)) -> dict` | no | Get current user from founder token - PIN-318 secure implementation. |
| `get_tenant_id` | `(tenant_id: str = Query(..., description='Tenant ID')) -> str` | no | DEPRECATED: Get tenant ID from query parameter. Use get_tenant_id_from_token ins |
| `get_current_user` | `(user_id: Optional[str] = Query(None, description='User ID')) -> Optional[dict]` | no | DEPRECATED: Get current user from query parameter. Use get_current_user_from_tok |
| `get_loop_status` | `(incident_id: str, tenant_id: str = Depends(get_tenant_id)) -> LoopStatusRespons` | yes | Get current loop status for an incident. |
| `get_loop_stages` | `(incident_id: str, tenant_id: str = Depends(get_tenant_id)) -> list[StageDetail]` | yes | Get detailed stage information for a loop. |
| `stream_loop_status` | `(incident_id: str, tenant_id: str = Depends(get_tenant_id))` | yes | SSE endpoint for live loop status updates. |
| `retry_loop_stage` | `(incident_id: str, request: RetryStageRequest, tenant_id: str = Depends(get_tena` | yes | Retry a failed loop stage. |
| `revert_loop` | `(incident_id: str, request: RevertLoopRequest, tenant_id: str = Depends(get_tena` | yes | Revert all changes made by a loop. |
| `list_pending_checkpoints` | `(tenant_id: str = Depends(get_tenant_id)) -> list[CheckpointResponse]` | yes | List all pending human checkpoints for the tenant. |
| `get_checkpoint` | `(checkpoint_id: str, tenant_id: str = Depends(get_tenant_id)) -> CheckpointRespo` | yes | Get details of a specific checkpoint. |
| `resolve_checkpoint` | `(checkpoint_id: str, request: ResolveCheckpointRequest, tenant_id: str = Depends` | yes | Resolve a pending checkpoint. |
| `get_integration_stats` | `(tenant_id: str = Depends(get_tenant_id), hours: int = Query(24, ge=1, le=720, d` | yes | Get integration loop statistics for the specified period. |
| `get_loop_narrative` | `(incident_id: str, tenant_id: str = Depends(get_tenant_id)) -> dict` | yes | Get narrative artifacts for an incident loop. |
| `get_graduation_status` | `(tenant_id: str = Depends(get_tenant_id)) -> HardenedGraduationResponse` | yes | Get M25 graduation status (HARDENED). |
| `simulate_prevention` | `(request: SimulatePreventionRequest, tenant_id: str = Depends(get_tenant_id)) ->` | yes | Simulate a prevention event for demo/testing purposes. |
| `simulate_regret` | `(request: SimulateRegretRequest, tenant_id: str = Depends(get_tenant_id)) -> dic` | yes | Simulate a regret event for demo/testing purposes. |
| `simulate_timeline_view` | `(incident_id: str = Query(..., description='Incident ID to mark as viewed in tim` | yes | Simulate viewing a prevention timeline for Gate 3. |
| `record_timeline_view` | `(incident_id: str = Query(..., description='Incident ID viewed in timeline'), ha` | yes | Record a REAL timeline view for Gate 3 graduation. |
| `trigger_graduation_re_evaluation` | `(tenant_id: str = Depends(get_tenant_id)) -> dict` | yes | Trigger a re-evaluation of graduation status. |
| `get_prevention_timeline` | `(incident_id: str, tenant_id: str = Depends(get_tenant_id)) -> PreventionTimelin` | yes | Get the prevention timeline for an incident. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `uuid` | uuid | no |
| `datetime` | datetime, timedelta, timezone | no |
| `typing` | Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query | no |
| `fastapi.responses` | StreamingResponse | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.console_auth` | FounderToken, verify_fops_token | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | get_async_session_context, get_operation_registry, OperationContext | no |
| `app.schemas.response` | wrap_dict | no |
| `app.integrations.events` | LoopStage | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## alerts.py
**Path:** `backend/app/hoc/api/cus/policies/alerts.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 446

**Docstring:** Alerts API (L2)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CreateRuleRequest` |  | Request to create alert rule. |
| `UpdateRuleRequest` |  | Request to update alert rule. |
| `CreateRouteRequest` |  | Request to create alert route. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_facade` | `() -> AlertsFacade` | no | Get the alerts facade. |
| `create_rule` | `(request: CreateRuleRequest, ctx: TenantContext = Depends(get_tenant_context), f` | yes | Create an alert rule (GAP-110). |
| `list_rules` | `(severity: Optional[str] = Query(None, description='Filter by severity'), enable` | yes | List alert rules. |
| `get_rule` | `(rule_id: str, ctx: TenantContext = Depends(get_tenant_context), facade: AlertsF` | yes | Get a specific alert rule. |
| `update_rule` | `(rule_id: str, request: UpdateRuleRequest, ctx: TenantContext = Depends(get_tena` | yes | Update an alert rule. |
| `delete_rule` | `(rule_id: str, ctx: TenantContext = Depends(get_tenant_context), facade: AlertsF` | yes | Delete an alert rule. |
| `list_history` | `(rule_id: Optional[str] = Query(None, description='Filter by rule'), severity: O` | yes | List alert history (GAP-111). |
| `get_event` | `(event_id: str, ctx: TenantContext = Depends(get_tenant_context), facade: Alerts` | yes | Get a specific alert event. |
| `acknowledge_event` | `(event_id: str, ctx: TenantContext = Depends(get_tenant_context), facade: Alerts` | yes | Acknowledge an alert event. |
| `resolve_event` | `(event_id: str, ctx: TenantContext = Depends(get_tenant_context), facade: Alerts` | yes | Resolve an alert event. |
| `create_route` | `(request: CreateRouteRequest, ctx: TenantContext = Depends(get_tenant_context), ` | yes | Create an alert route (GAP-124). |
| `list_routes` | `(enabled_only: bool = Query(False, description='Only enabled routes'), limit: in` | yes | List alert routes. |
| `get_route` | `(route_id: str, ctx: TenantContext = Depends(get_tenant_context), facade: Alerts` | yes | Get a specific alert route. |
| `delete_route` | `(route_id: str, ctx: TenantContext = Depends(get_tenant_context), facade: Alerts` | yes | Delete an alert route. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, Dict, List, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.tenant_auth` | TenantContext, get_tenant_context | no |
| `app.auth.tier_gating` | requires_feature | no |
| `app.schemas.response` | wrap_dict | no |
| `app.hoc.cus.hoc_spine.services.alerts_facade` | AlertsFacade, get_alerts_facade | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## analytics.py
**Path:** `backend/app/hoc/api/cus/policies/analytics.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 1128

**Docstring:** Unified Analytics API (L2)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ResolutionType` |  | Time resolution for usage data. |
| `ScopeType` |  | Scope of usage aggregation. |
| `TimeWindow` |  | Generic time window specification (shared across topics). |
| `UsageWindow` |  | Time window specification. |
| `UsageTotals` |  | Aggregate usage totals. |
| `UsageDataPoint` |  | Single data point in usage time series. |
| `UsageSignals` |  | Signal source metadata for provenance. |
| `UsageStatisticsResponse` |  | GET /analytics/statistics/usage response (contracted). |
| `CostTotals` |  | Aggregate cost totals. |
| `CostDataPoint` |  | Single data point in cost time series. |
| `CostByModel` |  | Cost breakdown by model. |
| `CostByFeature` |  | Cost breakdown by feature tag. |
| `CostSignals` |  | Signal source metadata for cost provenance. |
| `CostStatisticsResponse` |  | GET /analytics/statistics/cost response (contracted). |
| `TopicStatus` |  | Status of a topic within a subdomain. |
| `AnalyticsStatusResponse` |  | GET /analytics/_status response. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_usage_statistics` | `(request: Request, from_ts: Annotated[datetime, Query(alias='from', description=` | yes | Get usage statistics for the specified time window. |
| `get_analytics_status` | `() -> AnalyticsStatusResponse` | yes | Analytics capability probe. |
| `get_cost_statistics` | `(request: Request, from_ts: Annotated[datetime, Query(alias='from', description=` | yes | Get cost statistics for the specified time window. |
| `analytics_health` | `()` | yes | Internal health check for analytics facade. |
| `_get_usage_data` | `(request: Request, from_ts: datetime, to_ts: datetime, resolution: ResolutionTyp` | yes | Internal helper to get usage data (shared by read and export endpoints). |
| `export_usage_csv` | `(request: Request, from_ts: Annotated[datetime, Query(alias='from', description=` | yes | Export usage statistics as CSV. |
| `export_usage_json` | `(request: Request, from_ts: Annotated[datetime, Query(alias='from', description=` | yes | Export usage statistics as JSON. |
| `_get_cost_data` | `(request: Request, from_ts: datetime, to_ts: datetime, resolution: ResolutionTyp` | yes | Internal helper to get cost data (shared by read and export endpoints). |
| `export_cost_csv` | `(request: Request, from_ts: Annotated[datetime, Query(alias='from', description=` | yes | Export cost statistics as CSV. |
| `export_cost_json` | `(request: Request, from_ts: Annotated[datetime, Query(alias='from', description=` | yes | Export cost statistics as JSON. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `csv` | csv | no |
| `io` | io | no |
| `logging` | logging | no |
| `datetime` | datetime, timedelta | no |
| `enum` | Enum | no |
| `typing` | Annotated, Dict, List | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query, Request | no |
| `fastapi.responses` | Response | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.gateway_middleware` | get_auth_context | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_operation_registry, get_session_dep | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## aos_accounts.py
**Path:** `backend/app/hoc/api/cus/policies/aos_accounts.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 1485

**Docstring:** Unified Accounts API (L2)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ProjectSummary` |  | O2 Result Shape for projects. |
| `ProjectsListResponse` |  | GET /projects response (O2). |
| `ProjectDetailResponse` |  | GET /projects/{id} response (O3). |
| `UserSummary` |  | O2 Result Shape for users. |
| `UsersListResponse` |  | GET /users response (O2). |
| `UserDetailResponse` |  | GET /users/{id} response (O3). |
| `ProfileResponse` |  | GET /profile response. |
| `BillingSummaryResponse` |  | GET /billing response. |
| `ProfileUpdateRequest` |  | Request to update user profile preferences. |
| `ProfileUpdateResponse` |  | Profile update response. |
| `InvoiceSummary` |  | Invoice summary for billing history. |
| `InvoiceListResponse` |  | List of invoices response. |
| `SupportTicketCreate` |  | Create a support ticket. |
| `SupportTicketResponse` |  | Support ticket response. |
| `SupportTicketListResponse` |  | List of support tickets. |
| `SupportContactResponse` |  | Support contact information. |
| `InviteUserRequest` |  | Request to invite a user to the tenant. |
| `InvitationResponse` |  | Invitation response. |
| `InvitationListResponse` |  | List of invitations. |
| `AcceptInvitationRequest` |  | Request to accept an invitation. |
| `UpdateUserRoleRequest` |  | Request to update a user's role. |
| `TenantUserResponse` |  | User in tenant response. |
| `TenantUserListResponse` |  | List of users in tenant. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_tenant_id_from_auth` | `(request: Request) -> str` | no | Extract tenant_id from auth_context. Raises 401/403 if missing. |
| `get_user_id_from_auth` | `(request: Request) -> str | None` | no | Extract user_id from auth_context. Returns None if not available. |
| `list_projects` | `(request: Request, status: Annotated[Optional[str], Query(description='Filter by` | yes | READ-ONLY customer facade - delegates to L4 AccountsFacade. |
| `get_project_detail` | `(request: Request, project_id: str, session = Depends(get_session_dep)) -> Proje` | yes | READ-ONLY customer facade - delegates to L4 AccountsFacade. |
| `list_users` | `(request: Request, role: Annotated[Optional[str], Query(description='Filter by r` | yes | READ-ONLY customer facade - delegates to L4 AccountsFacade. |
| `get_user_detail` | `(request: Request, user_id: str, session = Depends(get_session_dep)) -> UserDeta` | yes | READ-ONLY customer facade - delegates to L4 AccountsFacade. |
| `get_profile` | `(request: Request, session = Depends(get_session_dep)) -> ProfileResponse` | yes | READ-ONLY customer facade - delegates to L4 AccountsFacade. |
| `get_billing_summary` | `(request: Request, session = Depends(get_session_dep)) -> BillingSummaryResponse` | yes | READ-ONLY customer facade - delegates to L4 AccountsFacade. |
| `update_profile` | `(request: Request, update: ProfileUpdateRequest, session = Depends(get_session_d` | yes | WRITE customer facade - delegates to L4 AccountsFacade. |
| `get_billing_invoices` | `(request: Request, session = Depends(get_session_dep)) -> InvoiceListResponse` | yes | READ-ONLY customer facade - delegates to L4 AccountsFacade. |
| `get_support_contact` | `() -> SupportContactResponse` | no | READ-ONLY customer facade - delegates to L4 AccountsFacade. |
| `create_support_ticket` | `(request: Request, ticket: SupportTicketCreate, session = Depends(get_session_de` | yes | WRITE customer facade - delegates to L4 AccountsFacade. |
| `list_support_tickets` | `(request: Request, status: Optional[str] = Query(None, description='Filter by st` | yes | READ-ONLY customer facade - delegates to L4 AccountsFacade. |
| `invite_user` | `(request: Request, invite: InviteUserRequest, session = Depends(get_session_dep)` | yes | WRITE customer facade - delegates to L4 AccountsFacade. |
| `list_invitations` | `(request: Request, status: Optional[str] = Query(None, description='Filter by st` | yes | READ-ONLY customer facade - delegates to L4 AccountsFacade. |
| `accept_invitation` | `(invitation_id: str, accept: AcceptInvitationRequest, session = Depends(get_sess` | yes | Accept an invitation to join a tenant. |
| `list_tenant_users` | `(request: Request, session = Depends(get_session_dep)) -> TenantUserListResponse` | yes | List users in the current tenant. |
| `update_user_role` | `(request: Request, user_id: str, update: UpdateUserRoleRequest, session = Depend` | yes | Update a user's role in the tenant. |
| `remove_user` | `(request: Request, user_id: str, session = Depends(get_session_dep)) -> dict` | yes | Remove a user from the tenant. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timedelta | no |
| `typing` | Annotated, Any, List, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query, Request | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.gateway_middleware` | get_auth_context | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_operation_registry, get_session_dep | no |
| `app.models.tenant` | Invitation, Subscription, SupportTicket, Tenant, TenantMembership (+3) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

### Violations
| Import | Rule Broken | Required Fix | Line |
|--------|-------------|-------------|------|
| `from app.models.tenant import Invitation, Subscription, SupportTicket, Tenant, TenantMembership, User, generate_uuid, utc_now` | L2 MUST NOT import L7 models | Use L5 schemas or response models | 65 |

---

## aos_api_key.py
**Path:** `backend/app/hoc/api/cus/policies/aos_api_key.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 297

**Docstring:** API Keys API (L2) - Connectivity Domain

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `APIKeySummary` |  | O2 Result Shape for API keys. |
| `APIKeysListResponse` |  | GET /api-keys response (O2). |
| `APIKeyDetailResponse` |  | GET /api-keys/{id} response (O3). |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_tenant_id_from_auth` | `(request: Request) -> str` | no | Extract tenant_id from auth_context. Raises 401/403 if missing. |
| `list_api_keys` | `(request: Request, status: Annotated[Optional[str], Query(description='Filter by` | yes | List API keys. READ-ONLY. Delegates to L4 operation registry. |
| `get_api_key_detail` | `(request: Request, key_id: str, session = Depends(get_session_dep)) -> APIKeyDet` | yes | Get API key detail (O3). Delegates to L4 operation registry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
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

---

## aos_cus_integrations.py
**Path:** `backend/app/hoc/api/cus/policies/aos_cus_integrations.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 673

**Docstring:** Customer LLM Integration Management API

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_user_id` | `(request: Request) -> Optional[str]` | no | Extract user_id from authenticated request. |
| `list_integrations` | `(request: Request, offset: int = Query(default=0, ge=0, description='Pagination ` | yes | List all integrations for the tenant. |
| `get_integration` | `(integration_id: UUID, request: Request)` | yes | Get full details for a specific integration. |
| `create_integration` | `(payload: CusIntegrationCreate, request: Request)` | yes | Create a new LLM integration. |
| `update_integration` | `(integration_id: UUID, payload: CusIntegrationUpdate, request: Request)` | yes | Update an existing integration. |
| `delete_integration` | `(integration_id: UUID, request: Request)` | yes | Delete an integration (soft delete). |
| `enable_integration` | `(integration_id: UUID, request: Request)` | yes | Enable an integration. |
| `disable_integration` | `(integration_id: UUID, request: Request)` | yes | Disable an integration. |
| `get_integration_health` | `(integration_id: UUID, request: Request)` | yes | Get current health status without running a new check. |
| `test_integration_credentials` | `(integration_id: UUID, request: Request)` | yes | Test integration credentials and update health status. |
| `get_integration_limits` | `(integration_id: UUID, request: Request)` | yes | Get current usage against configured limits. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Optional | no |
| `uuid` | UUID | no |
| `fastapi` | APIRouter, HTTPException, Query, Request | no |
| `app.auth.tenant_resolver` | resolve_tenant_id | no |
| `app.schemas.cus_schemas` | CusHealthCheckResponse, CusIntegrationCreate, CusIntegrationResponse, CusIntegrationSummary, CusIntegrationUpdate | no |
| `app.schemas.response` | wrap_dict, wrap_list | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_operation_registry | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## billing_dependencies.py
**Path:** `backend/app/hoc/api/cus/policies/billing_dependencies.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 203

**Docstring:** Phase-6 Billing Dependencies — FastAPI Integration

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `BillingContext` | allows_usage | Billing context for a request. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_get_billing_provider` | `()` | no | Get billing provider via L4 bridge (PIN-520 compliance). |
| `get_billing_context` | `(request: Request) -> BillingContext` | no | FastAPI dependency: Get billing context for current request. |
| `require_billing_active` | `(request: Request) -> BillingContext` | no | FastAPI dependency: Require billing state allows usage. |
| `check_limit` | `(context: BillingContext, limit_name: str, current_value: float) -> Optional[dic` | no | Check if a specific limit is exceeded. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `typing` | Optional | no |
| `fastapi` | Request, HTTPException | no |
| `app.billing.state` | BillingState | no |
| `app.billing.plan` | Plan, DEFAULT_PLAN | no |
| `app.billing.limits` | Limits, DEFAULT_LIMITS | no |
| `app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.account_bridge` | get_account_bridge | no |
| `app.auth.onboarding_state` | OnboardingState | no |
| `app.schemas.response` | wrap_dict | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

### __all__ Exports
`BillingContext`, `get_billing_context`, `require_billing_active`, `check_limit`

---

## compliance.py
**Path:** `backend/app/hoc/api/cus/policies/compliance.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 220

**Docstring:** Compliance API (L2)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `VerifyComplianceRequest` |  | Request to run compliance verification. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_facade` | `() -> ComplianceFacade` | no | Get the compliance facade. |
| `verify_compliance` | `(request: VerifyComplianceRequest, ctx: TenantContext = Depends(get_tenant_conte` | yes | Run compliance verification (GAP-103). |
| `list_reports` | `(scope: Optional[str] = Query(None, description='Filter by scope'), status: Opti` | yes | List compliance reports. |
| `get_report` | `(report_id: str, ctx: TenantContext = Depends(get_tenant_context), facade: Compl` | yes | Get a specific compliance report. |
| `list_rules` | `(scope: Optional[str] = Query(None, description='Filter by scope'), enabled_only` | yes | List compliance rules. |
| `get_rule` | `(rule_id: str, ctx: TenantContext = Depends(get_tenant_context), facade: Complia` | yes | Get a specific compliance rule. |
| `get_compliance_status` | `(ctx: TenantContext = Depends(get_tenant_context), facade: ComplianceFacade = De` | yes | Get overall compliance status. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, Dict, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.tenant_auth` | TenantContext, get_tenant_context | no |
| `app.auth.tier_gating` | requires_feature | no |
| `app.schemas.response` | wrap_dict | no |
| `app.hoc.cus.hoc_spine.services.compliance_facade` | ComplianceFacade, get_compliance_facade | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## connectors.py
**Path:** `backend/app/hoc/api/cus/policies/connectors.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 285

**Docstring:** Connectors API (L2)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `RegisterConnectorRequest` |  | Request to register a new connector. |
| `UpdateConnectorRequest` |  | Request to update a connector. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `list_connectors` | `(connector_type: Optional[str] = Query(None, description='Filter by type'), stat` | yes | List connectors for the tenant. |
| `register_connector` | `(request: RegisterConnectorRequest, ctx: TenantContext = Depends(get_tenant_cont` | yes | Register a new connector. |
| `get_connector` | `(connector_id: str, ctx: TenantContext = Depends(get_tenant_context), _tier: Non` | yes | Get a specific connector by ID. |
| `update_connector` | `(connector_id: str, request: UpdateConnectorRequest, ctx: TenantContext = Depend` | yes | Update a connector. |
| `delete_connector` | `(connector_id: str, ctx: TenantContext = Depends(get_tenant_context), _tier: Non` | yes | Delete a connector. |
| `test_connector` | `(connector_id: str, ctx: TenantContext = Depends(get_tenant_context), _tier: Non` | yes | Test a connector connection. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, Dict, List, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.tenant_auth` | TenantContext, get_tenant_context | no |
| `app.auth.tier_gating` | requires_feature | no |
| `app.schemas.response` | wrap_dict | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_operation_registry | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## cus_enforcement.py
**Path:** `backend/app/hoc/api/cus/policies/cus_enforcement.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 265

**Docstring:** Customer LLM Enforcement API

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `EnforcementCheckRequest` |  | Request for enforcement check. |
| `EnforcementBatchRequest` |  | Request for batch enforcement check. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_tenant_id` | `(request: Request) -> str` | no | Extract tenant_id from authenticated request. |
| `check_enforcement` | `(payload: EnforcementCheckRequest, request: Request)` | yes | Check enforcement policy before making an LLM call. |
| `get_enforcement_status` | `(request: Request, integration_id: str = Query(..., description='Integration ID'` | yes | Get current enforcement status for an integration. |
| `batch_enforcement_check` | `(payload: EnforcementBatchRequest, request: Request)` | yes | Check enforcement for multiple requests at once. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | List | no |
| `fastapi` | APIRouter, HTTPException, Query, Request | no |
| `pydantic` | BaseModel, Field | no |
| `app.schemas.response` | wrap_dict, wrap_list | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_operation_registry | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## customer_visibility.py
**Path:** `backend/app/hoc/api/cus/policies/customer_visibility.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 606

**Docstring:** Phase 4C-2: Customer Visibility Endpoints

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `StageDeclaration` |  | Single stage in the execution plan. |
| `CostDeclaration` |  | Cost expectations before execution. |
| `BudgetDeclaration` |  | Budget enforcement mode. |
| `PolicyDeclaration` |  | Policy posture declaration. |
| `MemoryDeclaration` |  | Memory mode declaration. |
| `EstimationMethodology` |  | PIN-254 Phase C Fix (C3 Partial Truth): Explicit disclosure of estimation basis. |
| `PreRunDeclaration` |  | Complete PRE-RUN declaration for customer visibility. |
| `AcknowledgementRequest` |  | Customer acknowledgement of PRE-RUN declaration. |
| `AcknowledgementResponse` |  | Response after acknowledgement. |
| `OutcomeItem` |  | Single outcome item. |
| `OutcomeReconciliation` |  | Complete outcome reconciliation for customer visibility. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_budget_mode` | `() -> BudgetDeclaration` | no | Determine budget enforcement mode from configuration. |
| `get_policy_posture` | `(strict_mode: bool = False) -> PolicyDeclaration` | no | Determine policy posture from configuration. |
| `get_memory_mode` | `() -> MemoryDeclaration` | no | Determine memory mode from configuration. |
| `estimate_stages` | `(agent_id: str, goal: str) -> List[StageDeclaration]` | no | Estimate execution stages based on agent capabilities. |
| `estimate_cost` | `(agent_id: str, goal: str, stages: List[StageDeclaration]) -> CostDeclaration` | no | Estimate cost based on stages and historical data. |
| `get_pre_run_declaration` | `(agent_id: str, goal: str, strict_mode: bool = False, _: str = Depends(verify_ap` | yes | Get PRE-RUN declaration before execution. |
| `acknowledge_declaration` | `(request: AcknowledgementRequest, _: str = Depends(verify_api_key)) -> Acknowled` | yes | Acknowledge PRE-RUN declaration. |
| `get_outcome_reconciliation` | `(run_id: str, request: Request, _: str = Depends(verify_api_key), session = Depe` | yes | Get outcome reconciliation after execution. |
| `get_declaration` | `(declaration_id: str, _: str = Depends(verify_api_key)) -> PreRunDeclaration` | yes | Retrieve a previously created PRE-RUN declaration. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any, Dict, List, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Request | no |
| `pydantic` | BaseModel, Field | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | get_operation_registry, get_session_dep, OperationContext | no |
| `app.auth` | verify_api_key | no |
| `app.middleware.tenancy` | get_tenant_id | no |
| `app.schemas.response` | wrap_dict | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## datasources.py
**Path:** `backend/app/hoc/api/cus/policies/datasources.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 387

**Docstring:** DataSources API (L2)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CreateSourceRequest` |  | Request to create a data source. |
| `UpdateSourceRequest` |  | Request to update a data source. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `create_source` | `(request: CreateSourceRequest, ctx: TenantContext = Depends(get_tenant_context),` | yes | Create a data source (GAP-113). |
| `list_sources` | `(source_type: Optional[str] = Query(None, description='Filter by type'), status:` | yes | List data sources. |
| `get_statistics` | `(ctx: TenantContext = Depends(get_tenant_context), _tier: None = Depends(require` | yes | Get data source statistics. |
| `get_source` | `(source_id: str, ctx: TenantContext = Depends(get_tenant_context), _tier: None =` | yes | Get a specific data source. |
| `update_source` | `(source_id: str, request: UpdateSourceRequest, ctx: TenantContext = Depends(get_` | yes | Update a data source. |
| `delete_source` | `(source_id: str, ctx: TenantContext = Depends(get_tenant_context), _tier: None =` | yes | Delete a data source. |
| `test_connection` | `(source_id: str, ctx: TenantContext = Depends(get_tenant_context), _tier: None =` | yes | Test a data source connection. |
| `activate_source` | `(source_id: str, ctx: TenantContext = Depends(get_tenant_context), _tier: None =` | yes | Activate a data source. |
| `deactivate_source` | `(source_id: str, ctx: TenantContext = Depends(get_tenant_context), _tier: None =` | yes | Deactivate a data source. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, Dict, List, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.tenant_auth` | TenantContext, get_tenant_context | no |
| `app.auth.tier_gating` | requires_feature | no |
| `app.schemas.response` | wrap_dict | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_operation_registry | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## detection.py
**Path:** `backend/app/hoc/api/cus/policies/detection.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 319

**Docstring:** Detection API (L2)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `RunDetectionRequest` |  | Request to run anomaly detection. |
| `ResolveAnomalyRequest` |  | Request to resolve an anomaly. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `run_detection` | `(request: RunDetectionRequest, ctx: TenantContext = Depends(get_tenant_context),` | yes | Run anomaly detection on demand (GAP-102). |
| `list_anomalies` | `(detection_type: Optional[str] = Query(None, description='Filter by type'), seve` | yes | List anomalies for the tenant. |
| `get_anomaly` | `(anomaly_id: str, ctx: TenantContext = Depends(get_tenant_context), _tier: None ` | yes | Get a specific anomaly by ID. |
| `resolve_anomaly` | `(anomaly_id: str, request: ResolveAnomalyRequest, ctx: TenantContext = Depends(g` | yes | Resolve an anomaly. |
| `acknowledge_anomaly` | `(anomaly_id: str, ctx: TenantContext = Depends(get_tenant_context), _tier: None ` | yes | Acknowledge an anomaly. |
| `get_detection_status` | `(ctx: TenantContext = Depends(get_tenant_context))` | yes | Get detection engine status. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, Dict, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.tenant_auth` | TenantContext, get_tenant_context | no |
| `app.auth.tier_gating` | requires_feature | no |
| `app.schemas.response` | wrap_dict | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_operation_registry | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## evidence.py
**Path:** `backend/app/hoc/api/cus/policies/evidence.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 376

**Docstring:** Evidence API (L2)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CreateChainRequest` |  | Request to create evidence chain. |
| `AddEvidenceRequest` |  | Request to add evidence to chain. |
| `CreateExportRequest` |  | Request to create evidence export. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `list_chains` | `(run_id: Optional[str] = Query(None, description='Filter by run'), limit: int = ` | yes | List evidence chains. |
| `create_chain` | `(request: CreateChainRequest, ctx: TenantContext = Depends(get_tenant_context), ` | yes | Create an evidence chain (GAP-104). |
| `get_chain` | `(chain_id: str, ctx: TenantContext = Depends(get_tenant_context), _tier: None = ` | yes | Get a specific evidence chain. |
| `add_evidence` | `(chain_id: str, request: AddEvidenceRequest, ctx: TenantContext = Depends(get_te` | yes | Add evidence to a chain. |
| `verify_chain` | `(chain_id: str, ctx: TenantContext = Depends(get_tenant_context), _tier: None = ` | yes | Verify chain integrity. |
| `create_export` | `(request: CreateExportRequest, ctx: TenantContext = Depends(get_tenant_context),` | yes | Create evidence export (GAP-105). |
| `list_exports` | `(chain_id: Optional[str] = Query(None, description='Filter by chain'), limit: in` | yes | List evidence exports. |
| `get_export` | `(export_id: str, ctx: TenantContext = Depends(get_tenant_context), _tier: None =` | yes | Get export status. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, Dict, List, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.tenant_auth` | TenantContext, get_tenant_context | no |
| `app.auth.tier_gating` | requires_feature | no |
| `app.schemas.response` | wrap_dict | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_operation_registry | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## governance.py
**Path:** `backend/app/hoc/api/cus/policies/governance.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 315

**Docstring:** Governance API (L2)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `KillSwitchRequest` |  | Request to toggle kill switch. |
| `ModeRequest` |  | Request to set governance mode. |
| `ConflictResolutionRequest` |  | Request to resolve a policy conflict. |
| `GovernanceStateResponse` |  | Governance state response. |
| `KillSwitchResponse` |  | Kill switch operation response. |
| `BootStatusResponse` |  | Boot status response. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_governance_state` | `(ctx: TenantContext = Depends(get_tenant_context))` | yes | Get current governance state. |
| `toggle_kill_switch` | `(request: KillSwitchRequest, ctx: TenantContext = Depends(get_tenant_context), _` | yes | Toggle the governance kill switch (GAP-090). |
| `set_governance_mode` | `(request: ModeRequest, ctx: TenantContext = Depends(get_tenant_context), _tier: ` | yes | Set governance mode (GAP-091). |
| `resolve_conflict` | `(request: ConflictResolutionRequest, ctx: TenantContext = Depends(get_tenant_con` | yes | Manually resolve a policy conflict (GAP-092). |
| `list_conflicts` | `(tenant_id: Optional[str] = Query(None, description='Filter by tenant'), status:` | yes | List policy conflicts. |
| `get_boot_status` | `(ctx: TenantContext = Depends(get_tenant_context))` | yes | Get SPINE component health status (GAP-095). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime | no |
| `typing` | Any, Dict, List, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.tenant_auth` | TenantContext, get_tenant_context | no |
| `app.auth.tier_gating` | requires_feature | no |
| `app.schemas.response` | wrap_dict | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_operation_registry | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## guard.py
**Path:** `backend/app/hoc/api/cus/policies/guard.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 2486

**Docstring:** Guard API - Customer Console Backend

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `GuardStatus` |  | Protection status response. |
| `TodaySnapshot` |  | Today's metrics snapshot. |
| `IncidentSummary` |  | Incident list item. |
| `IncidentEventResponse` |  | Timeline event. |
| `IncidentDetailResponse` |  | Full incident detail with timeline. |
| `ApiKeyResponse` |  | API key for customer console. |
| `PaginatedResponse` |  | Generic paginated response. |
| `GuardrailConfig` |  | Guardrail configuration for settings page. |
| `TenantSettings` |  | Read-only tenant settings. |
| `PolicyDecision` |  | Policy decision for replay. |
| `ReplayCallSnapshot` |  | Call snapshot for replay comparison. |
| `ReplayCertificate` |  | M23: Cryptographic certificate proving deterministic replay. |
| `ReplayResult` |  | Replay result response. |
| `IncidentSearchRequest` |  | Search incidents with filters. |
| `IncidentSearchResult` |  | Search result item matching component map spec. |
| `IncidentSearchResponse` |  | Search response. |
| `TimelineEvent` |  | Decision timeline event - step by step policy evaluation. |
| `PolicyEvaluation` |  | Individual policy evaluation result. |
| `CARERoutingInfo` |  | M17 CARE routing information for decision timeline. |
| `FailureCatalogMatch` |  | M9 Failure Catalog match information. |
| `DecisionTimelineResponse` |  | Full decision timeline for an incident/call. |
| `EvidenceExportRequest` |  | Request for evidence report export. |
| `OnboardingVerifyRequest` |  | Request for onboarding safety verification. |
| `OnboardingVerifyResponse` |  | Response from onboarding verification. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `utc_now` | `() -> datetime` | no |  |
| `get_tenant_from_auth` | `(session, tenant_id: str) -> dict` | yes | Get tenant or raise 404. Uses L4 registry dispatch for L2 first-principles purit |
| `get_guard_status` | `(tenant_id: str = Query(..., description='Tenant ID'), session = Depends(get_syn` | yes | Get protection status - "Am I safe right now?" |
| `get_today_snapshot` | `(tenant_id: str = Query(..., description='Tenant ID'), session = Depends(get_syn` | yes | Get today's metrics - "What did it cost/save me?" |
| `activate_killswitch` | `(tenant_id: str = Query(..., description='Tenant ID'), session = Depends(get_syn` | yes | Stop all traffic - Emergency kill switch. |
| `deactivate_killswitch` | `(tenant_id: str = Query(..., description='Tenant ID'), session = Depends(get_syn` | yes | Resume traffic - Deactivate kill switch. |
| `list_incidents` | `(tenant_id: str = Query(..., description='Tenant ID'), limit: int = Query(defaul` | yes | List incidents - "What did you stop for me?" |
| `get_incident_detail` | `(incident_id: str, tenant_id: str = Query(..., description='Tenant ID'), session` | yes | Get incident detail with timeline. |
| `acknowledge_incident` | `(incident_id: str, tenant_id: str = Query(..., description='Tenant ID'), session` | yes | Acknowledge an incident. |
| `resolve_incident` | `(incident_id: str, tenant_id: str = Query(..., description='Tenant ID'), session` | yes | Resolve an incident. |
| `get_customer_incident_narrative` | `(incident_id: str, token: CustomerToken = Depends(verify_console_token), session` | yes | GET /guard/incidents/{id}/narrative |
| `_generate_plain_title` | `(incident: dict) -> str` | no | Generate plain language title - no internal terminology. |
| `_generate_calm_summary` | `(incident: dict) -> str` | no | Generate calm, reassuring summary - no internal terms. |
| `_build_customer_impact` | `(incident: dict) -> CustomerIncidentImpactDTO` | no | Build impact assessment with calm vocabulary. |
| `_build_customer_resolution` | `(incident: dict) -> CustomerIncidentResolutionDTO` | no | Build resolution status with reassuring message. |
| `_build_customer_actions` | `(incident: dict) -> list` | no | Build customer actions - only if necessary. |
| `replay_call` | `(call_id: str, level: str = Query('logical', description='Determinism level: str` | yes | Replay a call - Trust builder. |
| `list_api_keys` | `(tenant_id: str = Query(..., description='Tenant ID'), session = Depends(get_syn` | yes | List API keys with status. |
| `freeze_api_key` | `(key_id: str, tenant_id: str = Query(..., description='Tenant ID'), session = De` | yes | Freeze an API key. |
| `unfreeze_api_key` | `(key_id: str, tenant_id: str = Query(..., description='Tenant ID'), session = De` | yes | Unfreeze an API key. |
| `get_settings` | `(tenant_id: str = Query(..., description='Tenant ID'), session = Depends(get_syn` | yes | Get read-only settings. |
| `search_incidents` | `(request: IncidentSearchRequest, tenant_id: str = Query(..., description='Tenant` | yes | Search incidents with filters - M23 component map spec. |
| `get_decision_timeline` | `(incident_id: str, session = Depends(get_sync_session_dep))` | yes | Get decision timeline - M23 component map spec. |
| `export_incident_evidence` | `(incident_id: str, tenant_id: str = Query(..., description='Tenant ID'), include` | yes | Export incident as a legal-grade PDF evidence report. |
| `onboarding_verify` | `(request: OnboardingVerifyRequest, tenant_id: str = Query(..., description='Tena` | yes | REAL safety verification for onboarding. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `uuid` | uuid | no |
| `datetime` | datetime, timedelta, timezone | no |
| `typing` | Any, Dict, List, Optional, cast | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query | no |
| `pydantic` | BaseModel | no |
| `app.adapters.customer_incidents_adapter` | get_customer_incidents_adapter | no |
| `app.adapters.customer_keys_adapter` | get_customer_keys_adapter | no |
| `app.adapters.customer_killswitch_adapter` | get_customer_killswitch_adapter | no |
| `app.auth.authority` | AuthorityResult, emit_authority_audit, require_replay_execute | no |
| `app.auth.console_auth` | CustomerToken, verify_console_token | no |
| `app.schemas.response` | wrap_dict | no |
| `app.contracts.guard` | CustomerIncidentActionDTO, CustomerIncidentImpactDTO, CustomerIncidentNarrativeDTO, CustomerIncidentResolutionDTO | no |
| `app.models.killswitch` | IncidentSeverity | no |
| `app.hoc.cus.hoc_spine.drivers.guard_write_driver` | GuardWriteDriver | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, OperationResult, get_operation_registry, get_sync_session_dep | no |
| `app.hoc.cus.logs.L5_schemas.determinism_types` | DeterminismLevel | no |
| `app.utils.guard_cache` | get_guard_cache | no |
| `json` | json | no |
| `decimal` | Decimal | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

### Violations
| Import | Rule Broken | Required Fix | Line |
|--------|-------------|-------------|------|
| `from app.models.killswitch import IncidentSeverity` | L2 MUST NOT import L7 models | Use L5 schemas or response models | 68 |

---

## guard_policies.py
**Path:** `backend/app/hoc/api/cus/policies/guard_policies.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 128

**Docstring:** Guard Policies API - Customer Console Policy Constraints Endpoint

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_policy_constraints` | `(tenant_id: str = Query(..., description='Tenant ID (required)'))` | yes | Get policy constraints for customer. |
| `get_guardrail_detail` | `(guardrail_id: str, tenant_id: str = Query(..., description='Tenant ID (required` | yes | Get guardrail detail. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query | no |
| `app.adapters.customer_policies_adapter` | CustomerGuardrail, CustomerPolicyConstraints, get_customer_policies_adapter | no |
| `app.auth.console_auth` | verify_console_token | no |
| `app.schemas.response` | wrap_dict | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## lifecycle.py
**Path:** `backend/app/hoc/api/cus/policies/lifecycle.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 401

**Docstring:** Lifecycle API (L2)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CreateAgentRequest` |  | Request to create an agent. |
| `CreateRunRequest` |  | Request to create a run. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_facade` | `() -> LifecycleFacade` | no | Get the lifecycle facade. |
| `create_agent` | `(request: CreateAgentRequest, ctx: TenantContext = Depends(get_tenant_context), ` | yes | Create a new agent (GAP-131). |
| `list_agents` | `(state: Optional[str] = Query(None, description='Filter by state'), limit: int =` | yes | List agents (GAP-131). |
| `get_agent` | `(agent_id: str, ctx: TenantContext = Depends(get_tenant_context), facade: Lifecy` | yes | Get a specific agent (GAP-131). |
| `start_agent` | `(agent_id: str, ctx: TenantContext = Depends(get_tenant_context), facade: Lifecy` | yes | Start an agent (GAP-132). |
| `stop_agent` | `(agent_id: str, ctx: TenantContext = Depends(get_tenant_context), facade: Lifecy` | yes | Stop an agent (GAP-132). |
| `terminate_agent` | `(agent_id: str, ctx: TenantContext = Depends(get_tenant_context), facade: Lifecy` | yes | Terminate an agent (GAP-132). |
| `create_run` | `(request: CreateRunRequest, ctx: TenantContext = Depends(get_tenant_context), fa` | yes | Create a new run (GAP-133). |
| `list_runs` | `(agent_id: Optional[str] = Query(None, description='Filter by agent'), state: Op` | yes | List runs (GAP-133). |
| `get_run` | `(run_id: str, ctx: TenantContext = Depends(get_tenant_context), facade: Lifecycl` | yes | Get a specific run (GAP-133). |
| `pause_run` | `(run_id: str, ctx: TenantContext = Depends(get_tenant_context), facade: Lifecycl` | yes | Pause a run (GAP-134). |
| `resume_run` | `(run_id: str, ctx: TenantContext = Depends(get_tenant_context), facade: Lifecycl` | yes | Resume a paused run (GAP-135). |
| `cancel_run` | `(run_id: str, ctx: TenantContext = Depends(get_tenant_context), facade: Lifecycl` | yes | Cancel a run (GAP-136). |
| `get_summary` | `(ctx: TenantContext = Depends(get_tenant_context), facade: LifecycleFacade = Dep` | yes | Get lifecycle summary. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, Dict, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.tenant_auth` | TenantContext, get_tenant_context | no |
| `app.auth.tier_gating` | requires_feature | no |
| `app.schemas.response` | wrap_dict | no |
| `app.hoc.cus.hoc_spine.services.lifecycle_facade` | LifecycleFacade, get_lifecycle_facade | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## logs.py
**Path:** `backend/app/hoc/api/cus/policies/logs.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 1639

**Docstring:** Unified Logs API (L2) - LOGS Domain V2

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `EvidenceMetadata` |  | Global metadata contract for all Logs responses. |
| `LLMRunEnvelope` |  | O1: Canonical immutable run record. |
| `TraceStep` |  | Individual trace step. |
| `LLMRunTrace` |  | O2: Step-by-step trace. |
| `GovernanceEvent` |  | Policy interaction event. |
| `LLMRunGovernance` |  | O3: Policy interaction trace. |
| `ReplayEvent` |  | Replay window event. |
| `LLMRunReplay` |  | O4: 60-second replay window. |
| `LLMRunExport` |  | O5: Export metadata. |
| `LLMRunRecordItem` |  | Single LLM run record entry (list view). |
| `LLMRunRecordsResponse` |  | Response envelope for LLM run records. |
| `SystemSnapshot` |  | O1: Environment snapshot. |
| `TelemetryStub` |  | O2: Telemetry stub response. |
| `SystemEvent` |  | System event record. |
| `SystemEvents` |  | O3: Infra events affecting run. |
| `SystemReplay` |  | O4: Infra replay window. |
| `SystemAudit` |  | O5: Infra attribution record. |
| `SystemRecordItem` |  | Single system record entry. |
| `SystemRecordsResponse` |  | Response envelope for system records. |
| `AuditLedgerItem` |  | Single audit ledger entry. |
| `AuditLedgerDetailItem` |  | Audit ledger entry with state snapshots. |
| `AuditLedgerResponse` |  | Response envelope for audit ledger. |
| `IdentityEvent` |  | Identity lifecycle event. |
| `AuditIdentity` |  | O1: Identity lifecycle. |
| `AuthorizationDecision` |  | Authorization decision record. |
| `AuditAuthorization` |  | O2: Access decisions. |
| `AccessEvent` |  | Log access event. |
| `AuditAccess` |  | O3: Log access audit. |
| `IntegrityCheck` |  | Integrity verification record. |
| `AuditIntegrity` |  | O4: Tamper detection. |
| `ExportRecord` |  | Export record. |
| `AuditExports` |  | O5: Compliance exports. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_tenant_id_from_auth` | `(request: Request) -> str` | no | Extract tenant_id from auth_context. Raises 401/403 if missing. |
| `list_llm_run_records` | `(request: Request, run_id: Annotated[Optional[str], Query(description='Filter by` | yes | List LLM run records. READ-ONLY customer facade. |
| `get_llm_run_envelope` | `(request: Request, run_id: str, session = Depends(get_session_dep)) -> LLMRunEnv` | yes | O1: Canonical immutable run record. READ-ONLY customer facade. |
| `get_llm_run_trace` | `(request: Request, run_id: str, session = Depends(get_session_dep)) -> LLMRunTra` | yes | O2: Step-by-step execution trace. READ-ONLY customer facade. |
| `get_llm_run_governance` | `(request: Request, run_id: str, session = Depends(get_session_dep)) -> LLMRunGov` | yes | O3: Policy interaction trace. READ-ONLY customer facade. |
| `get_llm_run_replay` | `(request: Request, run_id: str, session = Depends(get_session_dep)) -> LLMRunRep` | yes | O4: 60-second replay window. READ-ONLY customer facade. |
| `get_llm_run_export` | `(request: Request, run_id: str, session = Depends(get_session_dep)) -> LLMRunExp` | yes | O5: Export information. READ-ONLY customer facade. |
| `list_system_records` | `(request: Request, component: Annotated[Optional[str], Query(description='Filter` | yes | List system records. READ-ONLY customer facade. |
| `get_system_snapshot` | `(request: Request, run_id: str, session = Depends(get_session_dep)) -> SystemSna` | yes | O1: Environment baseline snapshot. READ-ONLY customer facade. |
| `get_system_telemetry` | `(request: Request, run_id: str) -> TelemetryStub` | yes | O2: Telemetry stub - producer not implemented. READ-ONLY customer facade. |
| `get_system_events` | `(request: Request, run_id: str, session = Depends(get_session_dep)) -> SystemEve` | yes | O3: Infra events affecting run. READ-ONLY customer facade. |
| `get_system_replay` | `(request: Request, run_id: str, session = Depends(get_session_dep)) -> SystemRep` | yes | O4: Infra replay window. READ-ONLY customer facade. |
| `get_system_audit` | `(request: Request, limit: Annotated[int, Query(ge=1, le=100)] = 50, offset: Anno` | yes | O5: Infra attribution. READ-ONLY customer facade. |
| `list_audit_entries` | `(request: Request, event_type: Annotated[Optional[str], Query(description='Filte` | yes | List audit entries. READ-ONLY customer facade. |
| `get_audit_entry` | `(request: Request, entry_id: str, session = Depends(get_session_dep)) -> AuditLe` | yes | Get audit entry detail. READ-ONLY customer facade. |
| `get_audit_identity` | `(request: Request, limit: Annotated[int, Query(ge=1, le=100)] = 50, session = De` | yes | O1: Identity lifecycle. READ-ONLY customer facade. |
| `get_audit_authorization` | `(request: Request, limit: Annotated[int, Query(ge=1, le=100)] = 50, session = De` | yes | O2: Authorization decisions. READ-ONLY customer facade. |
| `get_audit_access` | `(request: Request, limit: Annotated[int, Query(ge=1, le=100)] = 50, session = De` | yes | O3: Log access audit. READ-ONLY customer facade. |
| `get_audit_integrity` | `(request: Request) -> AuditIntegrity` | yes | O4: Tamper detection. READ-ONLY customer facade. |
| `get_audit_exports` | `(request: Request, limit: Annotated[int, Query(ge=1, le=100)] = 50, offset: Anno` | yes | O5: Compliance exports. READ-ONLY customer facade. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timedelta | no |
| `typing` | Annotated, Any, List, Literal, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query, Request | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.gateway_middleware` | get_auth_context | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_operation_registry, get_session_dep | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## monitors.py
**Path:** `backend/app/hoc/api/cus/policies/monitors.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 298

**Docstring:** Monitors API (L2)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CreateMonitorRequest` |  | Request to create a monitor. |
| `UpdateMonitorRequest` |  | Request to update a monitor. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_facade` | `() -> MonitorsFacade` | no | Get the monitors facade. |
| `create_monitor` | `(request: CreateMonitorRequest, ctx: TenantContext = Depends(get_tenant_context)` | yes | Create a monitor (GAP-121). |
| `list_monitors` | `(monitor_type: Optional[str] = Query(None, description='Filter by type'), status` | yes | List monitors. |
| `get_status` | `(ctx: TenantContext = Depends(get_tenant_context), facade: MonitorsFacade = Depe` | yes | Get overall monitoring status (GAP-120). |
| `get_monitor` | `(monitor_id: str, ctx: TenantContext = Depends(get_tenant_context), facade: Moni` | yes | Get a specific monitor. |
| `update_monitor` | `(monitor_id: str, request: UpdateMonitorRequest, ctx: TenantContext = Depends(ge` | yes | Update a monitor. |
| `delete_monitor` | `(monitor_id: str, ctx: TenantContext = Depends(get_tenant_context), facade: Moni` | yes | Delete a monitor. |
| `run_check` | `(monitor_id: str, ctx: TenantContext = Depends(get_tenant_context), facade: Moni` | yes | Run a health check (GAP-120). |
| `get_history` | `(monitor_id: str, limit: int = Query(100, le=1000, description='Maximum results'` | yes | Get health check history. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, Dict, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.tenant_auth` | TenantContext, get_tenant_context | no |
| `app.auth.tier_gating` | requires_feature | no |
| `app.schemas.response` | wrap_dict | no |
| `app.hoc.cus.hoc_spine.services.monitors_facade` | MonitorsFacade, get_monitors_facade | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## notifications.py
**Path:** `backend/app/hoc/api/cus/policies/notifications.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 304

**Docstring:** Notifications API (L2)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SendNotificationRequest` |  | Request to send notification. |
| `UpdatePreferencesRequest` |  | Request to update notification preferences. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `send_notification` | `(request: SendNotificationRequest, ctx: TenantContext = Depends(get_tenant_conte` | yes | Send a notification (GAP-109). |
| `list_notifications` | `(channel: Optional[str] = Query(None, description='Filter by channel'), status: ` | yes | List notifications for the tenant. |
| `list_channels` | `(ctx: TenantContext = Depends(get_tenant_context))` | yes | List available notification channels. |
| `get_preferences` | `(ctx: TenantContext = Depends(get_tenant_context), _tier: None = Depends(require` | yes | Get notification preferences for the current user. |
| `update_preferences` | `(request: UpdatePreferencesRequest, ctx: TenantContext = Depends(get_tenant_cont` | yes | Update notification preferences for the current user. |
| `get_notification` | `(notification_id: str, ctx: TenantContext = Depends(get_tenant_context), _tier: ` | yes | Get a specific notification. |
| `mark_as_read` | `(notification_id: str, ctx: TenantContext = Depends(get_tenant_context), _tier: ` | yes | Mark a notification as read. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, Dict, List, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.tenant_auth` | TenantContext, get_tenant_context | no |
| `app.auth.tier_gating` | requires_feature | no |
| `app.schemas.response` | wrap_dict | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_operation_registry | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## override.py
**Path:** `backend/app/hoc/api/cus/policies/override.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 353

**Docstring:** Limit Override API (PIN-LIM-05)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CreateOverrideRequest` |  | Request to create a limit override. |
| `OverrideListItem` |  | Override summary for list view. |
| `OverrideDetail` |  | Full override details. |
| `OverrideListResponse` |  | Response for override list. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `create_override` | `(request: Request, body: CreateOverrideRequest, session = Depends(get_session_de` | yes | Request a temporary limit override. |
| `list_overrides` | `(request: Request, status: Optional[str] = Query(default=None, description='Filt` | yes | List overrides for the tenant. |
| `get_override` | `(request: Request, override_id: str, session = Depends(get_session_dep)) -> Over` | yes | Get override by ID. |
| `cancel_override` | `(request: Request, override_id: str, session = Depends(get_session_dep)) -> Over` | yes | Cancel a pending or active override. |
| `_to_detail` | `(result: LimitOverrideResponse) -> OverrideDetail` | no | Convert service response to API response. |
| `_to_list_item` | `(result: LimitOverrideResponse) -> OverrideListItem` | no | Convert service response to list item. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime | no |
| `decimal` | Decimal | no |
| `typing` | Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query, Request | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.gateway_middleware` | get_auth_context | no |
| `app.schemas.limits.overrides` | LimitOverrideRequest, LimitOverrideResponse, OverrideStatus | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_operation_registry, get_session_dep | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## policies.py
**Path:** `backend/app/hoc/api/cus/policies/policies.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 1658

**Docstring:** Unified Policies API (L2)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyRuleSummary` |  | O2 Result Shape for policy rules. |
| `RulesListResponse` |  | GET /rules response (O2). |
| `PolicyRuleDetailResponse` |  | GET /rules/{rule_id} response (O3). |
| `LimitSummary` |  | O2 Result Shape for limits. |
| `LimitsListResponse` |  | GET /limits response (O2). |
| `LimitDetailResponse` |  | GET /limits/{limit_id} response (O3). |
| `LessonSummaryResponse` |  | O2 Result Shape for lessons. |
| `LessonsListResponse` |  | GET /lessons response (O2). |
| `LessonDetailResponse` |  | GET /lessons/{id} response (O3). |
| `LessonStatsResponse` |  | Lesson statistics response. |
| `PolicyStateResponse` |  | Policy layer state summary (ACT-O4). |
| `PolicyMetricsResponse` |  | Policy enforcement metrics (ACT-O5). |
| `PolicyConflictResponse` |  | Policy conflict summary (DFT-O4 spec). |
| `ConflictsListResponse` |  | GET /conflicts response (DFT-O4). |
| `PolicyDependencyRelation` |  | A dependency relationship detail. |
| `PolicyNodeResponse` |  | A node in the dependency graph (DFT-O5 spec). |
| `PolicyDependencyEdge` |  | A dependency edge in the graph. |
| `DependencyGraphResponse` |  | GET /dependencies response (DFT-O5). |
| `PolicyViolationSummary` |  | Policy violation summary (VIO-O1). |
| `ViolationsListResponse` |  | GET /violations response (VIO-O1). |
| `BudgetDefinitionSummary` |  | Budget definition summary (THR-O2). |
| `BudgetsListResponse` |  | GET /budgets response (THR-O2). |
| `PolicyRequestSummary` |  | Summary of a pending policy request (draft proposal). |
| `PolicyRequestsListResponse` |  | Response for policy requests list (ACT-O3). |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `require_preflight` | `() -> None` | no | Guard for preflight-only endpoints (O4, O5). |
| `get_tenant_id_from_auth` | `(request: Request) -> str` | no | Extract tenant_id from auth_context. Raises 401/403 if missing. |
| `list_policy_rules` | `(request: Request, status: Annotated[str, Query(description='Rule status: ACTIVE` | yes | List policy rules with unified query filters. READ-ONLY. |
| `get_policy_rule_detail` | `(request: Request, rule_id: str, session = Depends(get_session_dep)) -> PolicyRu` | yes | Get policy rule detail (O3). Tenant isolation enforced. |
| `list_limits` | `(request: Request, category: Annotated[str, Query(alias='type', description='Lim` | yes | List limits with unified query filters. READ-ONLY. |
| `get_limit_detail` | `(request: Request, limit_id: str, session = Depends(get_session_dep)) -> LimitDe` | yes | Get limit detail (O3). Tenant isolation enforced. |
| `get_rule_evidence` | `(request: Request, rule_id: str) -> dict[str, Any]` | yes | Get rule evidence (O4). Preflight console only. |
| `get_limit_evidence` | `(request: Request, limit_id: str) -> dict[str, Any]` | yes | Get limit evidence (O4). Preflight console only. |
| `list_lessons` | `(request: Request, lesson_type: Annotated[Optional[str], Query(description='Filt` | yes | List lessons learned (O2). READ-ONLY customer facade. |
| `get_lesson_stats` | `(request: Request, session = Depends(get_session_dep)) -> LessonStatsResponse` | yes | Get lesson statistics (O1). READ-ONLY customer facade. |
| `get_lesson_detail` | `(request: Request, lesson_id: str, session = Depends(get_session_dep)) -> Lesson` | yes | Get lesson detail (O3). READ-ONLY customer facade. |
| `get_policy_state` | `(request: Request, session = Depends(get_session_dep)) -> PolicyStateResponse` | yes | Get policy layer state (ACT-O4). Customer facade. |
| `get_policy_metrics` | `(request: Request, hours: Annotated[int, Query(ge=1, le=720, description='Time w` | yes | Get policy metrics (ACT-O5). Customer facade. |
| `list_policy_conflicts` | `(request: Request, policy_id: Annotated[Optional[str], Query(description='Filter` | yes | Detect policy conflicts (DFT-O4). Uses PolicyConflictEngine via facade. |
| `get_policy_dependencies` | `(request: Request, policy_id: Annotated[Optional[str], Query(description='Filter` | yes | Get policy dependency graph (DFT-O5). Uses PolicyDependencyEngine via facade. |
| `list_policy_violations` | `(request: Request, violation_type: Annotated[Optional[str], Query(description='F` | yes | List policy violations (VIO-O1). Unified customer facade. |
| `list_budget_definitions` | `(request: Request, scope: Annotated[Optional[str], Query(description='Filter by ` | yes | List budget definitions (THR-O2). Customer facade. |
| `list_policy_requests` | `(request: Request, status: Annotated[str, Query(description='Filter by status: d` | yes | List pending policy requests (ACT-O3). Customer facade. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `datetime` | datetime | no |
| `decimal` | Decimal | no |
| `typing` | Annotated, Any, List, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query, Request | no |
| `pydantic` | BaseModel | no |
| `app.auth.gateway_middleware` | get_auth_context | no |
| `app.schemas.response` | wrap_dict | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_operation_registry, get_session_dep | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

### Constants
`_CURRENT_ENVIRONMENT`

---

## policy.py
**Path:** `backend/app/hoc/api/cus/policies/policy.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 2268

**Docstring:** Policy API Endpoints (M5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyType` |  | Types of policies that can be evaluated. |
| `ApprovalStatus` |  | Status of an approval request. |
| `PolicyEvalRequest` |  | Request for policy sandbox evaluation. |
| `PolicyEvalResponse` |  | Response from policy sandbox evaluation. |
| `ApprovalRequestCreate` |  | Request to create an approval request. |
| `ApprovalRequestResponse` |  | Response when creating an approval request. |
| `ApprovalAction` |  | Action to approve or reject a request. |
| `ApprovalStatusResponse` |  | Full status of an approval request. |
| `PolicyMetadata` |  | Governance metadata for policy artifacts (aos_sdk-grade). |
| `PolicyContextSummary` |  | Summary of an active policy for cross-domain consumption. |
| `ActivePoliciesResponse` |  | GET /policy/active response — What governs execution now? |
| `PolicyLibrarySummary` |  | Summary of a policy rule in the library. |
| `PolicyLibraryResponse` |  | GET /policy/library response — What patterns are available? |
| `PolicyLessonSummary` |  | Summary of a lesson or draft for cross-domain consumption. |
| `LessonsResponse` |  | GET /policy/lessons response — What governance emerged? |
| `ThresholdSummary` |  | Summary of an enforced limit/threshold. |
| `ThresholdsResponse` |  | GET /policy/thresholds response — What limits are enforced? |
| `ViolationSummary` |  | Summary of a policy violation for cross-domain consumption. |
| `ViolationsResponse` |  | GET /policy/violations response — What enforcement occurred? |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_get_policy_adapter` | `()` | no | Get the L3 policy adapter. |
| `_record_policy_decision` | `(decision: str, policy_type: str) -> None` | no | Record policy decision metric via L3 adapter. |
| `_record_capability_violation` | `(violation_type: str, skill_id: str, tenant_id: Optional[str] = None) -> None` | no | Record capability violation metric via L3 adapter. |
| `_record_budget_rejection` | `(resource_type: str, skill_id: str) -> None` | no | Record budget rejection metric via L3 adapter. |
| `_record_approval_request_created` | `(policy_type: str) -> None` | no | Record approval request creation metric via L3 adapter. |
| `_record_approval_action` | `(result: str) -> None` | no | Record approval action metric via L3 adapter. |
| `_record_approval_escalation` | `() -> None` | no | Record approval escalation metric via L3 adapter. |
| `_record_webhook_fallback` | `() -> None` | no | Record webhook fallback metric via L3 adapter. |
| `_check_rate_limit` | `(tenant_id: str, endpoint: str = 'policy') -> None` | no | Check rate limit for tenant. Raises HTTPException if exceeded. |
| `_get_policy_version` | `() -> str` | no | Get current policy version. |
| `_hash_webhook_secret` | `(secret: str) -> str` | no | Hash webhook secret for storage. |
| `_get_approval_level_config` | `(session, policy_type: PolicyType, tenant_id: str, agent_id: Optional[str] = Non` | yes | Get approval level configuration from PolicyApprovalLevel table. |
| `_simulate_cost` | `(skill_id: str, tenant_id: str, payload: Dict[str, Any]) -> Optional[int]` | yes | Simulate cost for a skill execution via L3 adapter. |
| `_check_policy_violations` | `(skill_id: str, tenant_id: str, agent_id: Optional[str], payload: Dict[str, Any]` | yes | Check for policy violations via L3 adapter. |
| `_compute_webhook_signature` | `(payload: str, secret: str) -> str` | no | Compute HMAC-SHA256 signature for webhook. |
| `_send_webhook` | `(url: str, payload: Dict[str, Any], secret: Optional[str] = None, key_version: O` | yes | Send webhook callback with retry logic and key versioning. |
| `verify_webhook_signature` | `(body: str, signature: str, key_version: str, secrets: Dict[str, str]) -> bool` | no | Verify webhook signature with version support for rotation. |
| `evaluate_policy` | `(request: PolicyEvalRequest, session = Depends(get_session_dep), ctx: TenantCont` | yes | Sandbox evaluation of policy for a skill execution. |
| `create_approval_request` | `(request: ApprovalRequestCreate, background_tasks: BackgroundTasks, session = De` | yes | Create a new approval request (persisted to DB). |
| `get_approval_request` | `(request_id: str, session = Depends(get_session_dep)) -> ApprovalStatusResponse` | yes | Get the current status of an approval request. |
| `_check_approver_authorization` | `(approver_id: str, level: int, tenant_id: Optional[str] = None) -> None` | no | RBAC: Verify approver has permission to approve at the given level. |
| `approve_request` | `(request_id: str, action: ApprovalAction, background_tasks: BackgroundTasks, ses` | yes | Approve an approval request. |
| `reject_request` | `(request_id: str, action: ApprovalAction, background_tasks: BackgroundTasks, ses` | yes | Reject an approval request. |
| `list_approval_requests` | `(status: Optional[ApprovalStatus] = None, tenant_id: Optional[str] = None, limit` | yes | List approval requests with optional filtering. |
| `run_escalation_check` | `(session) -> int` | yes | Check for pending requests that need escalation. |
| `run_escalation_task` | `()` | no | Entry point for scheduled escalation check. |
| `_build_policy_metadata_from_rule` | `(rule) -> PolicyMetadata` | no | Build PolicyMetadata from a PolicyRule model instance. |
| `_build_policy_metadata_from_limit` | `(limit) -> PolicyMetadata` | no | Build PolicyMetadata from a Limit model instance. |
| `_build_policy_metadata_from_violation` | `(v) -> PolicyMetadata` | no | Build PolicyMetadata from a violation object (from policy engine). |
| `_build_policy_metadata_from_lesson` | `(lesson: dict) -> PolicyMetadata` | no | Build PolicyMetadata from a lesson dict (from lessons_learned_engine). |
| `get_active_policies` | `(scope: Optional[str] = None, enforcement_mode: Optional[str] = None, limit: int` | yes | V2 Facade: What governs execution now? |
| `get_active_policy_detail` | `(policy_id: str, session = Depends(get_session_dep), ctx: TenantContext = Depend` | yes | V2 Facade: Policy detail for cross-domain navigation. |
| `get_policy_library` | `(status: Optional[str] = None, rule_type: Optional[str] = None, limit: int = 50,` | yes | V2 Facade: What patterns are available? |
| `get_policy_lessons` | `(status: Optional[str] = None, lesson_type: Optional[str] = None, limit: int = 5` | yes | V2 Facade: What governance emerged? |
| `get_policy_lesson_detail` | `(lesson_id: str, ctx: TenantContext = Depends(get_tenant_context)) -> dict` | yes | V2 Facade: Lesson detail for cross-domain navigation. |
| `get_policy_thresholds` | `(limit_category: Optional[str] = None, scope: Optional[str] = None, status: str ` | yes | V2 Facade: What limits are enforced? |
| `get_policy_threshold_detail` | `(threshold_id: str, session = Depends(get_session_dep), ctx: TenantContext = Dep` | yes | V2 Facade: Threshold detail for cross-domain navigation. |
| `get_policy_violations_v2` | `(violation_type: Optional[str] = None, severity_min: Optional[float] = None, hou` | yes | V2 Facade: What enforcement occurred? |
| `get_policy_violation_detail` | `(violation_id: str, session = Depends(get_session_dep), ctx: TenantContext = Dep` | yes | V2 Facade: Violation detail for cross-domain navigation. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `asyncio` | asyncio | no |
| `hashlib` | hashlib | no |
| `hmac` | hmac | no |
| `json` | json | no |
| `logging` | logging | no |
| `os` | os | no |
| `datetime` | datetime, timedelta, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | uuid4 | no |
| `httpx` | httpx | no |
| `fastapi` | APIRouter, BackgroundTasks, Depends, HTTPException | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.tenant_auth` | TenantContext, get_tenant_context | no |
| `app.auth.tier_gating` | TenantTier, requires_feature, requires_tier | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_async_session_context, get_operation_registry, get_session_dep | no |
| `app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges` | get_policies_engine_bridge | no |
| `app.schemas.response` | wrap_dict | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

### Constants
`WEBHOOK_MAX_RETRIES`, `WEBHOOK_RETRY_DELAYS`, `WEBHOOK_CURRENT_KEY_VERSION`, `WEBHOOK_KEY_GRACE_VERSIONS`, `WEBHOOK_KEY_GRACE_VERSIONS`, `RATE_LIMIT_ENABLED`, `RATE_LIMIT_DEFAULT_RPM`, `RATE_LIMIT_BURST_RPM`

---

## policy_layer.py
**Path:** `backend/app/hoc/api/cus/policies/policy_layer.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 1876

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `EvaluateRequest` |  | Request to evaluate an action against policies. |
| `SimulateRequest` |  | Request to simulate policy evaluation (dry run). |
| `ViolationQuery` |  | Query parameters for violations. |
| `RiskCeilingUpdate` |  | Update for a risk ceiling. |
| `SafetyRuleUpdate` |  | Update for a safety rule. |
| `CooldownInfo` |  | Information about an active cooldown. |
| `PolicyMetrics` |  | Metrics from the policy engine. |
| `CreateVersionRequest` |  | Request to create a new policy version. |
| `RollbackRequest` |  | Request to rollback to a previous version. |
| `ResolveConflictRequest` |  | Request to resolve a policy conflict. |
| `TemporalPolicyCreate` |  | Request to create a temporal policy. |
| `ContextAwareEvaluateRequest` |  | Request for context-aware policy evaluation (GAP 4). |
| `AddDependencyRequest` |  | Request to add a policy dependency with DAG validation. |
| `PruneTemporalMetricsRequest` |  | Request to prune temporal metrics. |
| `ActivateVersionRequest` |  | Request to activate a policy version. |
| `LessonConvertRequest` |  | Request to convert a lesson to draft proposal. |
| `LessonDeferRequest` |  | Request to defer a lesson. |
| `LessonDismissRequest` |  | Request to dismiss a lesson. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `evaluate_action` | `(request: EvaluateRequest, db = Depends(get_session_dep)) -> PolicyEvaluationRes` | yes | Evaluate a proposed action against all applicable policies. |
| `simulate_evaluation` | `(request: SimulateRequest, db = Depends(get_session_dep)) -> PolicyEvaluationRes` | yes | Simulate policy evaluation without side effects. |
| `get_policy_state` | `(db = Depends(get_session_dep)) -> PolicyState` | yes | Get the current state of the policy layer. |
| `reload_policies` | `(db = Depends(get_session_dep)) -> Dict[str, Any]` | yes | Hot-reload policies from database. |
| `list_violations` | `(violation_type: Optional[ViolationType] = None, agent_id: Optional[str] = None,` | yes | List policy violations with filtering. |
| `get_violation` | `(violation_id: str, db = Depends(get_session_dep)) -> PolicyViolation` | yes | Get a specific violation by ID. |
| `acknowledge_violation` | `(violation_id: str, notes: Optional[str] = None, db = Depends(get_session_dep)) ` | yes | Acknowledge a violation (mark as reviewed). |
| `list_risk_ceilings` | `(tenant_id: Optional[str] = None, include_inactive: bool = False, db = Depends(g` | yes | List all risk ceilings with current values. |
| `get_risk_ceiling` | `(ceiling_id: str, db = Depends(get_session_dep)) -> Dict[str, Any]` | yes | Get a specific risk ceiling with current utilization. |
| `update_risk_ceiling` | `(ceiling_id: str, update: RiskCeilingUpdate, db = Depends(get_session_dep)) -> D` | yes | Update a risk ceiling configuration. |
| `reset_risk_ceiling` | `(ceiling_id: str, db = Depends(get_session_dep)) -> Dict[str, Any]` | yes | Reset a risk ceiling's current value to 0. |
| `list_safety_rules` | `(tenant_id: Optional[str] = None, include_inactive: bool = False, db = Depends(g` | yes | List all safety rules. |
| `update_safety_rule` | `(rule_id: str, update: SafetyRuleUpdate, db = Depends(get_session_dep)) -> Dict[` | yes | Update a safety rule configuration. |
| `list_ethical_constraints` | `(include_inactive: bool = False, db = Depends(get_session_dep)) -> List[Dict[str` | yes | List all ethical constraints. |
| `list_active_cooldowns` | `(agent_id: Optional[str] = None, db = Depends(get_session_dep)) -> List[Cooldown` | yes | List all active cooldowns. |
| `clear_cooldowns` | `(agent_id: str, rule_name: Optional[str] = None, db = Depends(get_session_dep)) ` | yes | Clear cooldowns for an agent. |
| `get_policy_metrics` | `(hours: int = Query(24, ge=1, le=720), db = Depends(get_session_dep)) -> PolicyM` | yes | Get policy engine metrics for the specified time window. |
| `evaluate_batch` | `(requests: List[EvaluateRequest], db = Depends(get_session_dep)) -> List[PolicyE` | yes | Evaluate multiple actions in a single call. |
| `list_policy_versions` | `(limit: int = Query(20, ge=1, le=100), include_inactive: bool = False, db = Depe` | yes | List all policy versions. |
| `get_current_version` | `(db = Depends(get_session_dep)) -> Dict[str, Any]` | yes | Get the currently active policy version. |
| `create_policy_version` | `(request: CreateVersionRequest, db = Depends(get_session_dep)) -> Dict[str, Any]` | yes | Create a new policy version snapshot. |
| `rollback_to_version` | `(request: RollbackRequest, db = Depends(get_session_dep)) -> Dict[str, Any]` | yes | Rollback to a previous policy version. |
| `get_version_provenance` | `(version_id: str, db = Depends(get_session_dep)) -> List[Dict[str, Any]]` | yes | Get the provenance (change history) for a policy version. |
| `get_dependency_graph` | `(db = Depends(get_session_dep)) -> Dict[str, Any]` | yes | Get the policy dependency graph. |
| `list_conflicts` | `(include_resolved: bool = False, db = Depends(get_session_dep)) -> List[Dict[str` | yes | List policy conflicts. |
| `resolve_conflict` | `(conflict_id: str, request: ResolveConflictRequest, db = Depends(get_session_dep` | yes | Resolve a policy conflict. |
| `list_temporal_policies` | `(metric: Optional[str] = None, include_inactive: bool = False, db = Depends(get_` | yes | List temporal (sliding window) policies. |
| `create_temporal_policy` | `(request: TemporalPolicyCreate, db = Depends(get_session_dep)) -> Dict[str, Any]` | yes | Create a new temporal policy. |
| `get_temporal_utilization` | `(policy_id: str, agent_id: Optional[str] = None, db = Depends(get_session_dep)) ` | yes | Get current utilization for a temporal policy. |
| `evaluate_with_context` | `(request: ContextAwareEvaluateRequest, db = Depends(get_session_dep)) -> Dict[st` | yes | Context-aware policy evaluation (GAP 4). |
| `validate_dependency_dag` | `(db = Depends(get_session_dep)) -> Dict[str, Any]` | yes | Validate that policy dependencies form a valid DAG. |
| `add_dependency_with_dag_check` | `(request: AddDependencyRequest, db = Depends(get_session_dep)) -> Dict[str, Any]` | yes | Add a policy dependency with DAG validation. |
| `get_evaluation_order` | `(db = Depends(get_session_dep)) -> Dict[str, Any]` | yes | Get the topological evaluation order for policies. |
| `prune_temporal_metrics` | `(request: PruneTemporalMetricsRequest, db = Depends(get_session_dep)) -> Dict[st` | yes | Prune and compact temporal metric events. |
| `get_temporal_storage_stats` | `(db = Depends(get_session_dep)) -> Dict[str, Any]` | yes | Get storage statistics for temporal metrics. |
| `activate_policy_version` | `(request: ActivateVersionRequest, db = Depends(get_session_dep)) -> Dict[str, An` | yes | Activate a policy version with pre-activation integrity checks. |
| `check_version_integrity` | `(version_id: str, db = Depends(get_session_dep)) -> Dict[str, Any]` | yes | Run integrity checks on a version without activating. |
| `list_lessons` | `(tenant_id: Optional[str] = None, lesson_type: Optional[str] = Query(None, descr` | yes | List lessons learned. |
| `get_lesson_stats` | `(tenant_id: str, db = Depends(get_session_dep)) -> Dict[str, Any]` | yes | Get lesson statistics for a tenant. |
| `get_lesson` | `(lesson_id: str, tenant_id: str, db = Depends(get_session_dep)) -> Dict[str, Any` | yes | Get a specific lesson by ID. |
| `convert_lesson_to_draft` | `(lesson_id: str, request: LessonConvertRequest, tenant_id: str = Query(..., desc` | yes | Convert a lesson to a draft policy proposal. |
| `defer_lesson` | `(lesson_id: str, request: LessonDeferRequest, tenant_id: str = Query(..., descri` | yes | Defer a lesson until a future date. |
| `dismiss_lesson` | `(lesson_id: str, request: LessonDismissRequest, tenant_id: str = Query(..., desc` | yes | Dismiss a lesson (mark as not actionable). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timedelta, timezone | no |
| `typing` | Any, Dict, List, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query | no |
| `pydantic` | BaseModel, Field | no |
| `app.schemas.response` | wrap_dict | no |
| `app.policy` | ActionType, PolicyEvaluationRequest, PolicyEvaluationResult, PolicyState, PolicyViolation (+1) | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_operation_registry, get_session_dep | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## policy_limits_crud.py
**Path:** `backend/app/hoc/api/cus/policies/policy_limits_crud.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 511

**Docstring:** Policy Limits CRUD API (PIN-LIM-01)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CreateLimitRequest` |  | API request to create a policy limit. |
| `UpdateLimitRequest` |  | API request to update a policy limit. |
| `ThresholdParamsRequest` |  | API request to set execution threshold parameters. |
| `ThresholdParamsResponse` |  | Response with effective threshold params. |
| `LimitDetail` |  | Full limit response. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `create_limit` | `(request: Request, body: CreateLimitRequest, session = Depends(get_session_dep))` | yes | Create a new policy limit. |
| `update_limit` | `(request: Request, limit_id: str, body: UpdateLimitRequest, session = Depends(ge` | yes | Update an existing policy limit. |
| `delete_limit` | `(request: Request, limit_id: str, session = Depends(get_session_dep)) -> None` | yes | Soft-delete a policy limit. |
| `get_threshold_params` | `(request: Request, limit_id: str, session = Depends(get_session_dep)) -> Thresho` | yes | Get threshold parameters for a limit. |
| `set_threshold_params` | `(request: Request, limit_id: str, body: ThresholdParamsRequest, session = Depend` | yes | Set threshold parameters for a limit. |
| `_to_detail` | `(result: PolicyLimitResponse) -> LimitDetail` | no | Convert service response to API response. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime | no |
| `decimal` | Decimal | no |
| `typing` | Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Request | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.gateway_middleware` | get_auth_context | no |
| `app.schemas.limits.policy_limits` | CreatePolicyLimitRequest, LimitCategoryEnum, LimitEnforcementEnum, LimitScopeEnum, PolicyLimitResponse (+2) | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_operation_registry, get_session_dep | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## policy_proposals.py
**Path:** `backend/app/hoc/api/cus/policies/policy_proposals.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 523

**Docstring:** PB-S4 Policy Proposals API

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ProposalSummaryResponse` |  | Summary of a policy proposal. |
| `ProposalListResponse` |  | Paginated list of policy proposals. |
| `ProposalDetailResponse` |  | Detailed policy proposal record. |
| `VersionResponse` |  | Policy version record. |
| `ApproveRejectRequest` |  | Request body for approve/reject actions. |
| `ApprovalResponse` |  | Response for approve/reject actions. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `list_proposals` | `(request: Request, tenant_id: Optional[str] = Query(None, description='Filter by` | yes | List policy proposals (PB-S4). |
| `get_proposal_stats` | `(request: Request, tenant_id: Optional[str] = Query(None, description='Filter by` | yes | Get policy proposal statistics (PB-S4). |
| `get_proposal` | `(request: Request, proposal_id: str)` | yes | Get detailed policy proposal by ID (PB-S4). |
| `list_proposal_versions` | `(request: Request, proposal_id: str)` | yes | List all versions of a policy proposal (PB-S4). |
| `approve_proposal` | `(http_request: Request, proposal_id: str, request: ApproveRejectRequest, role: T` | yes | Approve a policy proposal (PIN-373). |
| `reject_proposal` | `(http_request: Request, proposal_id: str, request: ApproveRejectRequest, role: T` | yes | Reject a policy proposal (PIN-373). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Optional | no |
| `uuid` | UUID | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query, Request | no |
| `pydantic` | BaseModel | no |
| `app.auth.role_guard` | require_role | no |
| `app.auth.tenant_roles` | TenantRole | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_async_session_context, get_operation_registry | no |
| `app.schemas.response` | wrap_dict | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## policy_rules_crud.py
**Path:** `backend/app/hoc/api/cus/policies/policy_rules_crud.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 264

**Docstring:** Policy Rules CRUD API (PIN-LIM-02)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CreateRuleRequest` |  | API request to create a policy rule. |
| `UpdateRuleRequest` |  | API request to update a policy rule. |
| `RuleDetail` |  | Full rule response. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `create_rule` | `(request: Request, body: CreateRuleRequest, session = Depends(get_session_dep)) ` | yes | Create a new policy rule. |
| `update_rule` | `(request: Request, rule_id: str, body: UpdateRuleRequest, session = Depends(get_` | yes | Update an existing policy rule. |
| `_to_detail` | `(result: PolicyRuleResponse) -> RuleDetail` | no | Convert service response to API response. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime | no |
| `typing` | Any, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Request | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.gateway_middleware` | get_auth_context | no |
| `app.schemas.limits.policy_rules` | CreatePolicyRuleRequest, PolicyRuleResponse, UpdatePolicyRuleRequest | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_operation_registry, get_session_dep | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## rate_limits.py
**Path:** `backend/app/hoc/api/cus/policies/rate_limits.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 278

**Docstring:** Rate Limits API (L2) - GAP-122

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `UpdateLimitRequest` |  | Request to update a limit. |
| `CheckLimitRequest` |  | Request to check a limit. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `list_limits` | `(limit_type: Optional[str] = Query(None, description='Filter by type'), limit: i` | yes | List limits (GAP-122). |
| `get_usage` | `(ctx: TenantContext = Depends(get_tenant_context), _tier: None = Depends(require` | yes | Get current usage summary. |
| `check_limit` | `(request: CheckLimitRequest, ctx: TenantContext = Depends(get_tenant_context), _` | yes | Check if a limit allows an operation. |
| `get_limit` | `(limit_id: str, ctx: TenantContext = Depends(get_tenant_context), _tier: None = ` | yes | Get a specific limit. |
| `update_limit` | `(limit_id: str, request: UpdateLimitRequest, ctx: TenantContext = Depends(get_te` | yes | Update a limit configuration. |
| `reset_limit` | `(limit_id: str, ctx: TenantContext = Depends(get_tenant_context), _tier: None = ` | yes | Reset a limit's usage counter. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, Dict, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.tenant_auth` | TenantContext, get_tenant_context | no |
| `app.auth.tier_gating` | requires_feature | no |
| `app.schemas.response` | wrap_dict | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_operation_registry | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## rbac_api.py
**Path:** `backend/app/hoc/api/cus/policies/rbac_api.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 344

**Docstring:** RBAC Management API

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyInfoResponse` |  | Current policy information. |
| `ReloadResponse` |  | Policy reload response. |
| `AuditEntry` |  | Single audit log entry. |
| `AuditResponse` |  | Audit log query response. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_get_rbac_engine` | `()` | no | Get rbac_engine via L4 bridge to maintain L2 purity. |
| `get_policy_info` | `(request: Request)` | yes | Get current RBAC policy information. |
| `reload_policies` | `(request: Request)` | yes | Hot-reload RBAC policies from file. |
| `get_permission_matrix` | `(request: Request) -> Dict[str, Any]` | yes | Get current permission matrix. |
| `query_audit_logs` | `(request: Request, resource: Optional[str] = Query(default=None, description='Fi` | yes | Query RBAC audit logs. |
| `cleanup_audit_logs` | `(request: Request, retention_days: int = Query(default=90, ge=1, le=365), db = D` | yes | Clean up old audit logs. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any, Dict, List, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query, Request | no |
| `pydantic` | BaseModel | no |
| `app.auth.authorization_choke` | check_permission_request | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | get_operation_registry, get_sync_session_dep, OperationContext | no |
| `app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges` | get_account_bridge | no |
| `app.schemas.response` | wrap_dict | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## replay.py
**Path:** `backend/app/hoc/api/cus/policies/replay.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 702

**Docstring:** Replay UX API (H1)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ReplayCategory` |  | Categories for replay data grouping. |
| `ReplayItem` |  | Single item in replay timeline. |
| `ReplaySliceResponse` |  | Paginated, grouped replay slice response. |
| `IncidentSummaryResponse` |  | Summary of incident for replay context. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_parse_json_field` | `(value) -> Any` | no | Safely parse a JSON string field, returning empty dict/list on failure. |
| `_get_policy_decisions` | `(row: dict) -> list` | no | Extract policy decisions from a proxy call row dict. |
| `_get_related_call_ids` | `(row: dict) -> list` | no | Extract related call IDs from incident metadata. |
| `_get_event_data` | `(row: dict) -> dict` | no | Extract data dict from incident event row. |
| `_categorize_proxy_call_row` | `(row: dict) -> ReplayCategory` | no | Categorize a proxy call row into replay category. |
| `_proxy_call_row_to_replay_item` | `(row: dict) -> ReplayItem` | no | Convert proxy call row dict to ReplayItem for visualization. |
| `_incident_event_row_to_replay_item` | `(row: dict) -> ReplayItem` | no | Convert IncidentEvent row dict to ReplayItem for visualization. |
| `_dispatch_replay` | `(session, method: str, **kwargs) -> Any` | yes | Dispatch a replay operation through the L4 registry. |
| `get_replay_slice` | `(request: Request, incident_id: str, window: int = Query(30, ge=5, le=300, descr` | yes | Get time-windowed replay slice of an incident. |
| `get_incident_summary` | `(request: Request, incident_id: str, auth: AuthorityResult = Depends(require_rep` | yes | Get incident summary for replay context. |
| `get_replay_timeline` | `(request: Request, incident_id: str, limit: int = Query(100, ge=10, le=500, desc` | yes | Get full timeline for an incident (unpaginated for scrubbing UI). |
| `explain_replay_item` | `(request: Request, incident_id: str, item_id: str, auth: AuthorityResult = Depen` | yes | Get detailed explanation for a single replay item. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `json` | json | no |
| `logging` | logging | no |
| `datetime` | datetime, timedelta | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query, Request | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.authority` | AuthorityResult, require_replay_read, verify_tenant_access | no |
| `app.schemas.response` | wrap_dict | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | get_operation_registry, get_sync_session_dep, OperationContext | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## retrieval.py
**Path:** `backend/app/hoc/api/cus/policies/retrieval.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 243

**Docstring:** Retrieval API (L2)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AccessDataRequest` |  | Request for mediated data access. |
| `RegisterPlaneRequest` |  | Request to register a knowledge plane. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_facade` | `() -> RetrievalFacade` | no | Get the retrieval facade. |
| `access_data` | `(request: AccessDataRequest, ctx: TenantContext = Depends(get_tenant_context), f` | yes | Mediated data access (GAP-094). |
| `list_planes` | `(connector_type: Optional[str] = Query(None, description='Filter by connector ty` | yes | List available knowledge planes. |
| `register_plane` | `(request: RegisterPlaneRequest, ctx: TenantContext = Depends(get_tenant_context)` | yes | Register a knowledge plane. |
| `get_plane` | `(plane_id: str, ctx: TenantContext = Depends(get_tenant_context), facade: Retrie` | yes | Get a specific knowledge plane. |
| `list_evidence` | `(run_id: Optional[str] = Query(None, description='Filter by run'), plane_id: Opt` | yes | List retrieval evidence records. |
| `get_evidence` | `(evidence_id: str, ctx: TenantContext = Depends(get_tenant_context), facade: Ret` | yes | Get a specific evidence record. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, Dict, List, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.tenant_auth` | TenantContext, get_tenant_context | no |
| `app.auth.tier_gating` | requires_feature | no |
| `app.schemas.response` | wrap_dict | no |
| `app.hoc.cus.hoc_spine.services.retrieval_facade` | RetrievalFacade, get_retrieval_facade | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## runtime.py
**Path:** `backend/app/hoc/api/cus/policies/runtime.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 716

**Docstring:** Machine-Native Runtime API Endpoints (M5.5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PlanStep` |  | A single step in a plan to simulate. |
| `SimulateRequest` |  | Request to simulate a plan before execution. |
| `SimulateResponse` |  | Response from plan simulation. |
| `QueryRequest` |  | Request to query runtime state. |
| `QueryResponse` |  | Response from runtime query. |
| `SkillDescriptorResponse` |  | Response describing a skill. |
| `SkillListResponse` |  | Response listing available skills. |
| `CapabilitiesResponse` |  | Response with agent capabilities. |
| `ReplayRequest` |  | Request to replay a stored run. |
| `ReplayResponse` |  | Response from replay operation. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_get_cost_simulator` | `()` | no | Get CostSimulator instance. |
| `_get_runtime_adapter` | `()` | no | Get RuntimeAdapter instance (L3). |
| `_get_skill_registry` | `()` | no | Get skill registry. |
| `simulate_plan` | `(request: SimulateRequest, _http_request: Request = None, _rate_limited: bool = ` | yes | Simulate a plan before execution. |
| `query_runtime` | `(request: QueryRequest, ctx: TenantContext = Depends(get_tenant_context), _tier:` | yes | Query runtime state. |
| `list_available_skills` | `(ctx: TenantContext = Depends(get_tenant_context))` | yes | List all available skills. |
| `describe_skill` | `(skill_id: str, ctx: TenantContext = Depends(get_tenant_context))` | yes | Get detailed descriptor for a skill. |
| `get_capabilities` | `(agent_id: Optional[str] = Query(default=None, description='Agent ID'), tenant_i` | yes | Get available capabilities for an agent/tenant. |
| `get_resource_contract` | `(resource_id: str)` | yes | Get resource contract for a specific resource. |
| `replay_run` | `(run_id: str, request: ReplayRequest = ReplayRequest(), _rate_limited: bool = De` | yes | Replay a stored plan and optionally verify determinism parity. |
| `list_traces` | `(tenant_id: Optional[str] = Query(None, description='Filter by tenant'), limit: ` | yes | List stored traces for a tenant. |
| `get_trace` | `(run_id: str)` | yes | Get a specific trace by run ID. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `typing` | Any, Dict, List, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query, Request | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.authority` | AuthorityResult, require_replay_execute | no |
| `app.auth.tenant_auth` | TenantContext, get_tenant_context | no |
| `app.auth.tier_gating` | requires_feature | no |
| `app.middleware.rate_limit` | rate_limit_dependency | no |
| `app.schemas.response` | wrap_dict | no |
| `app.commands.runtime_command` | DEFAULT_SKILL_METADATA | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

### Constants
`AOS_WORKSPACE_ROOT`

---

## scheduler.py
**Path:** `backend/app/hoc/api/cus/policies/scheduler.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 341

**Docstring:** Scheduler API (L2)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CreateJobRequest` |  | Request to create scheduled job. |
| `UpdateJobRequest` |  | Request to update scheduled job. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_facade` | `() -> SchedulerFacade` | no | Get the scheduler facade. |
| `create_job` | `(request: CreateJobRequest, ctx: TenantContext = Depends(get_tenant_context), fa` | yes | Create a scheduled job (GAP-112). |
| `list_jobs` | `(status: Optional[str] = Query(None, description='Filter by status'), limit: int` | yes | List scheduled jobs. |
| `get_job` | `(job_id: str, ctx: TenantContext = Depends(get_tenant_context), facade: Schedule` | yes | Get a specific scheduled job. |
| `update_job` | `(job_id: str, request: UpdateJobRequest, ctx: TenantContext = Depends(get_tenant` | yes | Update a scheduled job. |
| `delete_job` | `(job_id: str, ctx: TenantContext = Depends(get_tenant_context), facade: Schedule` | yes | Delete a scheduled job. |
| `trigger_job` | `(job_id: str, ctx: TenantContext = Depends(get_tenant_context), facade: Schedule` | yes | Trigger a job to run immediately. |
| `pause_job` | `(job_id: str, ctx: TenantContext = Depends(get_tenant_context), facade: Schedule` | yes | Pause a scheduled job. |
| `resume_job` | `(job_id: str, ctx: TenantContext = Depends(get_tenant_context), facade: Schedule` | yes | Resume a paused job. |
| `list_job_runs` | `(job_id: str, status: Optional[str] = Query(None, description='Filter by status'` | yes | List job run history. |
| `get_run` | `(run_id: str, ctx: TenantContext = Depends(get_tenant_context), facade: Schedule` | yes | Get a specific job run. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, Dict, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.tenant_auth` | TenantContext, get_tenant_context | no |
| `app.auth.tier_gating` | requires_feature | no |
| `app.schemas.response` | wrap_dict | no |
| `app.hoc.cus.hoc_spine.services.scheduler_facade` | SchedulerFacade, get_scheduler_facade | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## simulate.py
**Path:** `backend/app/hoc/api/cus/policies/simulate.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 163

**Docstring:** Limit Simulation API (PIN-LIM-04)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SimulateRequest` |  | Wrapper for simulation request. |
| `SimulateResponse` |  | Simulation response with decision and details. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `simulate_execution` | `(request: Request, body: SimulateRequest, session = Depends(get_session_dep)) ->` | yes | Simulate an execution against all limits. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `fastapi` | APIRouter, Depends, HTTPException, Request | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.gateway_middleware` | get_auth_context | no |
| `app.hoc.cus.controls.L5_schemas.simulation` | LimitSimulationRequest, LimitSimulationResponse, SimulationDecision | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_operation_registry, get_session_dep | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## status_history.py
**Path:** `backend/app/hoc/api/cus/policies/status_history.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 457

**Docstring:** API endpoints for immutable status history audit trail.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `StatusHistoryQuery` |  | Query parameters for status history. |
| `StatusHistoryResponse` |  | Single status history record. |
| `StatusHistoryListResponse` |  | Paginated list of status history records. |
| `ExportRequest` |  | Request for status history export. |
| `ExportResponse` |  | Response with signed URL for export download. |
| `StatsResponse` |  | Statistics for audit reporting. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `generate_signed_url` | `(export_id: str, format: str) -> tuple[str, datetime]` | no | Generate a signed URL for export download. |
| `verify_signed_url` | `(export_id: str, format: str, expires_ts: int, signature: str) -> bool` | no | Verify a signed URL signature. |
| `query_status_history` | `(entity_type: Optional[str] = Query(None, description='Filter by entity type'), ` | yes | Query status history with filters. |
| `get_entity_history` | `(entity_type: str, entity_id: str, limit: int = Query(100, ge=1, le=1000), sessi` | yes | Get complete status history for a specific entity. |
| `create_export` | `(request: ExportRequest, session = Depends(get_session_dep))` | yes | Create an export of status history records. |
| `download_export` | `(export_id: str, format: str = Query(..., description='Export format'), expires:` | yes | Download an exported file using signed URL. |
| `get_stats` | `(tenant_id: Optional[str] = Query(None, description='Filter by tenant'), session` | yes | Get statistics about status history records. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `csv` | csv | no |
| `hashlib` | hashlib | no |
| `hmac` | hmac | no |
| `json` | json | no |
| `os` | os | no |
| `time` | time | no |
| `uuid` | uuid | no |
| `datetime` | datetime, timedelta, timezone | no |
| `pathlib` | Path | no |
| `typing` | Any, Dict, List, Optional, cast | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query, Response | no |
| `pydantic` | BaseModel, Field | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_operation_registry, get_session_dep | no |
| `app.schemas.response` | wrap_dict | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

### Constants
`EXPORT_DIR`, `SIGNED_URL_SECRET`, `SIGNED_URL_TTL_SECONDS`

---

## workers.py
**Path:** `backend/app/hoc/api/cus/policies/workers.py`  
**Layer:** L2_api | **Domain:** policies | **Lines:** 1595

**Docstring:** API endpoints for Business Builder Worker.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ToneRuleRequest` |  | Tone rule for brand. |
| `ForbiddenClaimRequest` |  | Forbidden claim definition. |
| `VisualIdentityRequest` |  | Visual identity for brand. |
| `BrandRequest` |  | Brand schema for worker execution. |
| `WorkerRunRequest` |  | Request to run the Business Builder Worker. |
| `PolicyStatusModel` |  | Phase 5B: Policy pre-check status for PRE-RUN declaration. |
| `WorkerRunResponse` |  | Response from worker execution. |
| `ReplayRequest` |  | Request to replay a previous execution. |
| `BrandValidationResponse` |  | Response from brand validation. |
| `RunListItem` |  | Summary item for run listing. |
| `RunListResponse` |  | Response for listing runs. |
| `RunRetryResponse` |  | Response for run retry - Phase-2.5. |
| `WorkerEventBus` | __init__, subscribe, unsubscribe, emit, get_history, cleanup | Event bus for real-time worker execution streaming. |
| `EventType` |  | Constants for SSE event types. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_get_workers_adapter` | `()` | no | Get the L3 workers adapter. |
| `_calculate_cost_cents` | `(model: str, input_tokens: int, output_tokens: int) -> int` | no | Calculate LLM cost in cents via L3 adapter. |
| `_store_run` | `(run_id: str, data: Dict[str, Any], tenant_id: str = 'default') -> None` | yes | Persist a run to PostgreSQL. |
| `_insert_cost_record` | `(run_id: str, tenant_id: str, model: str, input_tokens: int, output_tokens: int,` | yes | Insert a cost record for a worker run. |
| `_check_and_emit_cost_advisory` | `(run_id: str, tenant_id: str, cost_cents: int) -> Dict[str, Any]` | yes | Check if cost threshold is crossed and emit advisory if needed. |
| `_verify_advisory_invariant` | `(run_id: str, tenant_id: str, advisory_result: Dict[str, Any]) -> None` | yes | Verify advisory emission invariant in VERIFICATION_MODE. |
| `_get_run` | `(run_id: str) -> Optional[Dict[str, Any]]` | yes | Get a run from PostgreSQL via L4 registry. |
| `_list_runs` | `(limit: int = 20, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]` | yes | List recent runs from PostgreSQL via L4 registry. |
| `get_event_bus` | `() -> WorkerEventBus` | no | Get the global event bus instance. |
| `_brand_request_to_schema` | `(brand_req: BrandRequest)` | no | Convert API request to BrandSchema via L3 adapter. |
| `_execute_worker_async` | `(run_id: str, request: WorkerRunRequest) -> None` | yes | Execute worker in background and update run store. |
| `run_worker` | `(request: WorkerRunRequest, background_tasks: BackgroundTasks, _: str = Depends(` | yes | Execute the Business Builder Worker. |
| `replay_execution_endpoint` | `(request: ReplayRequest, auth: AuthorityResult = Depends(require_replay_execute)` | yes | Replay a previous execution using Golden Replay (M4). |
| `get_run` | `(run_id: str, _: str = Depends(verify_api_key))` | yes | Get details of a worker run. |
| `list_runs` | `(limit: int = 20, tenant_id: Optional[str] = None, _: str = Depends(verify_api_k` | yes | List recent worker runs. |
| `retry_run` | `(run_id: str, _: str = Depends(verify_api_key))` | yes | Retry a completed or failed run - Phase-2.5. |
| `validate_brand` | `(request: BrandRequest, _: str = Depends(verify_api_key))` | yes | Validate a brand schema without executing the worker. |
| `worker_health` | `()` | yes | Health check for Business Builder Worker. |
| `delete_run` | `(run_id: str, _: str = Depends(verify_api_key))` | yes | Delete a run from storage. |
| `get_brand_schema` | `()` | yes | Get the JSON schema for BrandRequest. |
| `get_run_schema` | `()` | yes | Get the JSON schema for WorkerRunRequest. |
| `_sse_event_generator` | `(run_id: str, queue: asyncio.Queue) -> AsyncGenerator[str, None]` | yes | Generate SSE events from the queue. |
| `stream_run_events` | `(run_id: str, request: Request)` | yes | Stream real-time events for a worker run via Server-Sent Events (SSE). |
| `get_run_events` | `(run_id: str, _: str = Depends(verify_api_key))` | yes | Get all events for a run (non-streaming). |
| `_execute_worker_with_events` | `(run_id: str, request: WorkerRunRequest) -> None` | yes | Execute worker with REAL event emission from worker itself. |
| `run_worker_streaming` | `(request: WorkerRunRequest, background_tasks: BackgroundTasks, _: str = Depends(` | yes | Execute the Business Builder Worker with real-time event streaming. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `asyncio` | asyncio | no |
| `json` | json | no |
| `logging` | logging | no |
| `os` | os | no |
| `uuid` | uuid | no |
| `collections` | defaultdict | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any, AsyncGenerator, Dict, List, Optional | no |
| `fastapi` | APIRouter, BackgroundTasks, Depends, HTTPException, Request | no |
| `fastapi.responses` | StreamingResponse | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth` | verify_api_key | no |
| `app.auth.authority` | AuthorityResult, emit_authority_audit, require_replay_execute | no |
| `app.contracts.decisions` | emit_policy_precheck_decision | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_async_session_context, get_operation_registry | no |
| `app.schemas.response` | wrap_dict | no |
| `app.hoc.cus.hoc_spine.drivers.worker_write_driver_async` | WorkerWriteServiceAsync | no |
| `app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges` | get_policies_engine_bridge | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

### Constants
`VERIFICATION_MODE`, `COST_ENFORCEMENT_ENABLED`

---
