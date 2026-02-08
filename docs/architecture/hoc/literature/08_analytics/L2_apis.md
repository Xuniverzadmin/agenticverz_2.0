# Analytics — L2 Apis (4 files)

**Domain:** analytics  
**Layer:** L2_apis  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

---

## costsim.py
**Path:** `backend/app/hoc/api/cus/analytics/costsim.py`  
**Layer:** L2_api | **Domain:** analytics | **Lines:** 1010

**Docstring:** API endpoints for CostSim V2 sandbox.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SimulationStep` |  | A single step in a simulation plan. |
| `SimulateRequest` |  | Request for V2 simulation. |
| `SimulationStepResult` |  | Result for a single step. |
| `V2SimulationResponse` |  | Response from V2 simulation. |
| `ComparisonResponse` |  | Comparison between V1 and V2. |
| `SideEffectDisclosure` |  | PIN-254 Phase C Fix (C5 Implicit Side-Effect): Explicit disclosure of side effects. |
| `SandboxSimulateResponse` |  | Response from sandbox simulation. |
| `SandboxStatusResponse` |  | Status of V2 sandbox. |
| `DivergenceReportResponse` |  | Divergence report response. |
| `CanaryRunResponse` |  | Canary run response. |
| `DatasetInfo` |  | Dataset information. |
| `ValidationResultResponse` |  | Validation result response. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_memory_context` | `(tenant_id: str, workflow_id: Optional[str] = None, agent_id: Optional[str] = No` | yes | Retrieve memory context for simulation. |
| `apply_post_execution_updates` | `(tenant_id: str, workflow_id: Optional[str], agent_id: Optional[str], simulation` | yes | Apply deterministic post-execution memory updates. |
| `detect_simulation_drift` | `(baseline_result: Dict[str, Any], memory_result: Dict[str, Any], workflow_id: Op` | yes | Detect drift between baseline and memory-enabled simulation. |
| `get_sandbox_status` | `(session = Depends(get_session_dep))` | yes | Get current V2 sandbox status. |
| `simulate_v2` | `(request: SimulateRequest, session = Depends(get_session_dep))` | yes | Run simulation through V2 sandbox. |
| `reset_circuit_breaker` | `(reason: Optional[str] = Query(None, description='Reason for reset'), session = ` | yes | Reset the V2 circuit breaker. |
| `get_incidents` | `(include_resolved: bool = Query(False, description='Include resolved incidents')` | yes | Get circuit breaker incidents. |
| `get_divergence_report` | `(start_date: Optional[datetime] = Query(None, description='Start of analysis per` | yes | Get cost divergence report between V1 and V2. |
| `trigger_canary_run` | `(sample_count: int = Query(100, ge=10, le=1000, description='Number of samples')` | yes | Trigger a canary run on-demand. |
| `get_canary_reports` | `(limit: int = Query(10, ge=1, le=100, description='Max reports to return'), stat` | yes | Get recent canary run reports. |
| `list_datasets` | `(session = Depends(get_session_dep))` | yes | List all available reference datasets. |
| `get_dataset_info` | `(dataset_id: str, session = Depends(get_session_dep))` | yes | Get information about a specific dataset. |
| `validate_against_dataset` | `(dataset_id: str, session = Depends(get_session_dep))` | yes | Validate V2 against a specific reference dataset. |
| `validate_all` | `(session = Depends(get_session_dep))` | yes | Validate V2 against ALL reference datasets. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `os` | os | no |
| `datetime` | datetime, timedelta, timezone | no |
| `typing` | Any, Dict, List, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query | no |
| `pydantic` | BaseModel, Field | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | OperationContext, get_operation_registry, get_session_dep | no |
| `app.schemas.response` | wrap_dict | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

### Constants
`MEMORY_CONTEXT_INJECTION`, `MEMORY_POST_UPDATE`, `DRIFT_DETECTION_ENABLED`, `MEMORY_FAIL_OPEN_OVERRIDE`, `MEMORY_POST_UPDATE_SYNC`

---

## feedback.py
**Path:** `backend/app/hoc/api/cus/analytics/feedback.py`  
**Layer:** L2_api | **Domain:** analytics | **Lines:** 221

**Docstring:** PB-S3 Pattern Feedback API (READ-ONLY)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `FeedbackSummaryResponse` |  | Summary of a feedback record. |
| `FeedbackListResponse` |  | Paginated list of feedback records. |
| `FeedbackDetailResponse` |  | Detailed feedback record. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `list_feedback` | `(tenant_id: Optional[str] = Query(None, description='Filter by tenant'), pattern` | yes | List pattern feedback records (PB-S3). |
| `get_feedback` | `(feedback_id: str, _: str = Depends(verify_api_key))` | yes | Get detailed feedback record by ID (PB-S3). |
| `get_feedback_stats` | `(tenant_id: Optional[str] = Query(None, description='Filter by tenant'), _: str ` | yes | Get feedback statistics summary (PB-S3). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query | no |
| `pydantic` | BaseModel | no |
| `app.auth` | verify_api_key | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | get_async_session_context, get_operation_registry, OperationContext | no |
| `app.schemas.response` | wrap_dict | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## predictions.py
**Path:** `backend/app/hoc/api/cus/analytics/predictions.py`  
**Layer:** L2_api | **Domain:** analytics | **Lines:** 300

**Docstring:** PB-S5 Predictions API (READ-ONLY)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PredictionSummaryResponse` |  | Summary of a prediction event. |
| `PredictionListResponse` |  | Paginated list of predictions. |
| `PredictionDetailResponse` |  | Detailed prediction event record. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `list_predictions` | `(tenant_id: Optional[str] = Query(None, description='Filter by tenant'), predict` | yes | List prediction events (PB-S5). |
| `get_prediction` | `(prediction_id: str, session = Depends(get_session_dep), auth: AuthorityResult =` | yes | Get detailed prediction by ID (PB-S5). |
| `get_predictions_for_subject` | `(subject_type: str, subject_id: str, include_expired: bool = Query(False, descri` | yes | Get all predictions for a specific subject (PB-S5). |
| `get_prediction_stats` | `(tenant_id: Optional[str] = Query(None, description='Filter by tenant'), include` | yes | Get prediction statistics (PB-S5). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query | no |
| `pydantic` | BaseModel | no |
| `app.auth.authority` | AuthorityResult, emit_authority_audit, require_predictions_read | no |
| `app.hoc.cus.hoc_spine.orchestrator.operation_registry` | get_operation_registry, get_session_dep, OperationContext | no |
| `app.schemas.response` | wrap_dict | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---

## scenarios.py
**Path:** `backend/app/hoc/api/cus/analytics/scenarios.py`  
**Layer:** L2_api | **Domain:** analytics | **Lines:** 525

**Docstring:** Scenario-based Cost Simulation API (H2)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SimulationStepInput` |  | A single step in a simulation plan. |
| `ScenarioCreate` |  | Request to create a new scenario. |
| `ScenarioModel` |  | Stored scenario model. |
| `ScenarioResponse` |  | Response for scenario operations. |
| `StepEstimate` |  | Cost estimate for a single step. |
| `SimulationResult` |  | Result of a scenario simulation (advisory only). |
| `AdhocSimulationRequest` |  | Request for ad-hoc simulation without saving scenario. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_init_default_scenarios` | `()` | no | Initialize default template scenarios for quick access. |
| `_simulate_plan` | `(plan: List[SimulationStepInput], budget_cents: int) -> SimulationResult` | no | Run pure simulation on a plan. |
| `list_scenarios` | `(include_templates: bool = Query(True, description='Include template scenarios')` | yes | List all available scenarios. |
| `create_scenario` | `(request: ScenarioCreate)` | yes | Create a new scenario. |
| `get_scenario` | `(scenario_id: str)` | yes | Get a specific scenario by ID. |
| `delete_scenario` | `(scenario_id: str)` | yes | Delete a scenario. |
| `simulate_scenario` | `(scenario_id: str, budget_override: Optional[int] = Query(None, ge=0, le=1000000` | yes | Run simulation for a saved scenario. |
| `simulate_adhoc` | `(request: AdhocSimulationRequest)` | yes | Run ad-hoc simulation without saving scenario. |
| `get_immutability_info` | `()` | yes | Get information about the immutability guarantees. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `uuid` | uuid | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any, Dict, List, Optional | no |
| `fastapi` | APIRouter, Depends, HTTPException, Query | no |
| `pydantic` | BaseModel, Field | no |
| `app.auth.console_auth` | verify_fops_token | no |
| `app.schemas.response` | wrap_dict | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** HTTP translation — request validation, auth, response formatting, delegates to L3

**SHOULD call:** L3_adapters
**MUST NOT call:** L5_engines, L6_drivers, L7_models
**Called by:** L2.1_facade

---
