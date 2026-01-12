# CostSim V2 API (M6 + M7 Memory Integration)
"""
API endpoints for CostSim V2 sandbox.

Endpoints:
- POST /costsim/v2/simulate - Run V2 simulation (sandbox mode)
- GET /costsim/v2/status - Get V2 sandbox status
- POST /costsim/v2/reset - Reset circuit breaker
- GET /costsim/divergence - Get divergence report
- POST /costsim/canary/run - Trigger canary run
- GET /costsim/canary/reports - Get canary reports

M7 Enhancements:
- Memory context injection for simulations
- Post-execution memory updates via rules engine
- Drift detection between baseline and memory-enabled runs
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.costsim import (
    get_circuit_breaker,
    is_v2_disabled_by_drift,
    is_v2_sandbox_enabled,
    run_canary,
    simulate_with_sandbox,
)
from app.costsim.config import get_config
from app.costsim.divergence import generate_divergence_report

logger = logging.getLogger("nova.api.costsim")

# M7: Memory integration feature flags
MEMORY_CONTEXT_INJECTION = os.getenv("MEMORY_CONTEXT_INJECTION", "false").lower() == "true"
MEMORY_POST_UPDATE = os.getenv("MEMORY_POST_UPDATE", "false").lower() == "true"
DRIFT_DETECTION_ENABLED = os.getenv("DRIFT_DETECTION_ENABLED", "false").lower() == "true"
# Emergency override: allows service to start without memory modules (NOT recommended)
MEMORY_FAIL_OPEN_OVERRIDE = os.getenv("MEMORY_FAIL_OPEN_OVERRIDE", "false").lower() == "true"
# Synchronous update mode for tests - blocks until memory updates are applied
MEMORY_POST_UPDATE_SYNC = os.getenv("MEMORY_POST_UPDATE_SYNC", "false").lower() == "true"

# M7: Import memory components - FAIL-FAST if feature flags are enabled
# Memory modules are required when any memory feature is enabled
_memory_features_enabled = MEMORY_CONTEXT_INJECTION or MEMORY_POST_UPDATE or DRIFT_DETECTION_ENABLED

if _memory_features_enabled:
    try:
        from app.memory.drift_detector import get_drift_detector
        from app.memory.memory_service import MemoryResult, get_memory_service
        from app.memory.update_rules import get_update_rules_engine
        from app.tasks.memory_update import apply_update_rules, apply_update_rules_sync

        logger.info("Memory integration modules loaded successfully")
    except ImportError as e:
        if MEMORY_FAIL_OPEN_OVERRIDE:
            logger.warning(f"Memory modules import failed but MEMORY_FAIL_OPEN_OVERRIDE=true: {e}")
            # Define stub functions to prevent NameError
            get_memory_service = lambda: None
            get_update_rules_engine = lambda: None
            get_drift_detector = lambda: None

            async def apply_update_rules(*args, **kwargs):
                return 0

            def apply_update_rules_sync(*args, **kwargs):
                return True
        else:
            raise RuntimeError(
                f"Memory integration required (MEMORY_CONTEXT_INJECTION={MEMORY_CONTEXT_INJECTION}, "
                f"MEMORY_POST_UPDATE={MEMORY_POST_UPDATE}, DRIFT_DETECTION_ENABLED={DRIFT_DETECTION_ENABLED}) "
                f"but memory modules failed to import: {e}. "
                f"Set MEMORY_FAIL_OPEN_OVERRIDE=true to bypass (NOT recommended)."
            ) from e
else:
    # Memory features disabled - no imports needed, define stubs
    def get_memory_service():
        return None

    def get_update_rules_engine():
        return None

    def get_drift_detector():
        return None

    async def apply_update_rules(*args, **kwargs):
        return 0

    def apply_update_rules_sync(*args, **kwargs):
        return True

    logger.debug("Memory features disabled, skipping memory module imports")

router = APIRouter(prefix="/costsim", tags=["costsim"])


# Request/Response Models
class SimulationStep(BaseModel):
    """A single step in a simulation plan."""

    skill: str = Field(..., description="Skill ID")
    params: Dict[str, Any] = Field(default_factory=dict, description="Skill parameters")
    iterations: int = Field(default=1, ge=1, le=100, description="Number of times to execute this step")


class SimulateRequest(BaseModel):
    """Request for V2 simulation."""

    plan: List[SimulationStep] = Field(..., description="Plan steps to simulate")
    budget_cents: int = Field(1000, ge=0, description="Available budget in cents")
    tenant_id: Optional[str] = Field(None, description="Tenant identifier")
    run_id: Optional[str] = Field(None, description="Run identifier")
    # M7: Memory integration fields
    workflow_id: Optional[str] = Field(None, description="Workflow identifier for memory context")
    agent_id: Optional[str] = Field(None, description="Agent identifier for memory context")
    inject_memory: Optional[bool] = Field(None, description="Override memory injection setting")


class SimulationStepResult(BaseModel):
    """Result for a single step."""

    step_index: int
    skill_id: str
    cost_cents: float
    latency_ms: float
    confidence: float


class V2SimulationResponse(BaseModel):
    """Response from V2 simulation."""

    feasible: bool
    status: str
    estimated_cost_cents: int
    estimated_duration_ms: int
    budget_remaining_cents: int
    confidence_score: float
    model_version: str
    step_estimates: List[SimulationStepResult]
    risks: List[Dict[str, Any]]
    warnings: List[str]
    runtime_ms: int


class ComparisonResponse(BaseModel):
    """Comparison between V1 and V2."""

    verdict: str
    v1_cost_cents: int
    v2_cost_cents: int
    cost_delta_cents: int
    cost_delta_pct: float
    drift_score: float
    feasibility_match: bool


class SideEffectDisclosure(BaseModel):
    """
    PIN-254 Phase C Fix (C5 Implicit Side-Effect): Explicit disclosure of side effects.

    The /simulate endpoint can trigger memory writes when MEMORY_POST_UPDATE=true.
    This violates the implicit contract that "simulation" is side-effect-free.

    This disclosure makes the side-effect conditions explicit in the response.
    """

    memory_write_occurred: bool = False  # Did this call write to memory?
    memory_write_feature_flag: str = "MEMORY_POST_UPDATE"  # Which flag controls it
    memory_write_enabled: bool = False  # Is the flag currently enabled?
    disclaimer: str = "Simulation may update memory when MEMORY_POST_UPDATE=true."


class SandboxSimulateResponse(BaseModel):
    """Response from sandbox simulation."""

    # V1 result (production)
    v1_feasible: bool
    v1_cost_cents: int
    v1_duration_ms: int

    # V2 result (if sandbox enabled)
    v2_result: Optional[V2SimulationResponse] = None
    comparison: Optional[ComparisonResponse] = None

    # Sandbox status
    sandbox_enabled: bool
    v2_error: Optional[str] = None

    # M7: Memory integration fields
    memory_context_keys: Optional[List[str]] = None
    memory_updates_applied: Optional[int] = None
    drift_detected: Optional[bool] = None
    drift_score: Optional[float] = None

    # PIN-254 Phase C Fix: Side-effect transparency
    side_effects: Optional[SideEffectDisclosure] = None


class SandboxStatusResponse(BaseModel):
    """Status of V2 sandbox."""

    sandbox_enabled: bool
    circuit_breaker_open: bool
    disabled_by_drift: bool
    model_version: str
    adapter_version: str
    drift_threshold: float


class DivergenceReportResponse(BaseModel):
    """Divergence report response."""

    start_date: datetime
    end_date: datetime
    version: str
    sample_count: int
    delta_p50: float
    delta_p90: float
    kl_divergence: float
    outlier_count: int
    fail_ratio: float
    matching_rate: float
    detailed_samples: List[Dict[str, Any]]


class CanaryRunResponse(BaseModel):
    """Canary run response."""

    run_id: str
    status: str
    passed: bool
    total_samples: int
    matching_samples: int
    kl_divergence: float
    failure_reasons: List[str]
    artifact_paths: List[str]


# =============================================================================
# M7: Memory Integration Helpers
# =============================================================================


async def get_memory_context(
    tenant_id: str, workflow_id: Optional[str] = None, agent_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieve memory context for simulation.

    Fetches relevant memory pins for the tenant, workflow, and agent.
    Returns empty dict if memory service unavailable (fail-open).
    """
    if not _memory_features_enabled or not MEMORY_CONTEXT_INJECTION:
        return {}

    memory_service = get_memory_service()
    if not memory_service:
        return {}

    context = {}

    try:
        # Get tenant-level config
        config_result = await memory_service.get(tenant_id, "config:simulation", agent_id)
        if config_result.success and config_result.entry:
            context["config"] = config_result.entry.value

        # Get agent preferences if agent_id provided
        if agent_id:
            prefs_result = await memory_service.get(tenant_id, f"agent:{agent_id}:preferences", agent_id)
            if prefs_result.success and prefs_result.entry:
                context["agent_preferences"] = prefs_result.entry.value

        # Get workflow state if workflow_id provided
        if workflow_id:
            workflow_result = await memory_service.get(tenant_id, f"workflow:{workflow_id}:state", agent_id)
            if workflow_result.success and workflow_result.entry:
                context["workflow_state"] = workflow_result.entry.value

        # Get cost history
        history_result = await memory_service.get(tenant_id, "costsim:history", agent_id)
        if history_result.success and history_result.entry:
            context["cost_history"] = history_result.entry.value

        logger.debug(f"Memory context retrieved: {list(context.keys())}")
        return context

    except Exception as e:
        logger.warning(f"Memory context retrieval error: {e}")
        # M7: Emit context injection failure metric
        try:
            from app.memory.memory_service import MEMORY_CONTEXT_INJECTION_FAILURES

            MEMORY_CONTEXT_INJECTION_FAILURES.labels(tenant_id=tenant_id, reason=type(e).__name__).inc()
        except ImportError:
            pass
        return {}


async def apply_post_execution_updates(
    tenant_id: str, workflow_id: Optional[str], agent_id: Optional[str], simulation_result: Dict[str, Any]
) -> int:
    """
    Apply deterministic post-execution memory updates.

    Uses the update rules engine to apply memory updates based on
    simulation results. Returns count of updates applied.
    """
    if not _memory_features_enabled or not MEMORY_POST_UPDATE:
        return 0

    memory_service = get_memory_service()
    if not memory_service:
        return 0

    updates_applied = 0

    try:
        # Update cost history
        history_update = {
            "last_simulation": datetime.now(timezone.utc).isoformat(),
            "last_cost_cents": simulation_result.get("estimated_cost_cents", 0),
            "last_feasible": simulation_result.get("feasible", False),
            "total_simulations": 1,  # Will be incremented by rule
        }

        result = await memory_service.set(
            tenant_id, "costsim:history", history_update, source="costsim_engine", agent_id=agent_id
        )
        if result.success:
            updates_applied += 1

        # Update workflow state if workflow_id provided
        if workflow_id:
            workflow_update = {
                "last_simulation_at": datetime.now(timezone.utc).isoformat(),
                "simulation_count": 1,  # Increment via rule
                "last_feasibility": simulation_result.get("feasible", False),
            }

            result = await memory_service.set(
                tenant_id, f"workflow:{workflow_id}:state", workflow_update, source="costsim_engine", agent_id=agent_id
            )
            if result.success:
                updates_applied += 1

        logger.debug(f"Applied {updates_applied} memory updates")
        return updates_applied

    except Exception as e:
        logger.warning(f"Post-execution memory update error: {e}")
        return 0


async def detect_simulation_drift(
    baseline_result: Dict[str, Any], memory_result: Dict[str, Any], workflow_id: Optional[str]
) -> tuple[bool, float]:
    """
    Detect drift between baseline and memory-enabled simulation.

    Compares results to identify if memory context significantly
    changed the simulation outcome.
    """
    if not _memory_features_enabled or not DRIFT_DETECTION_ENABLED:
        return False, 0.0

    try:
        drift_detector = get_drift_detector()
        if not drift_detector:
            return False, 0.0

        # Create trace-like structures for comparison
        baseline_trace = {
            "workflow_id": workflow_id or "baseline",
            "memory_enabled": False,
            "cost_cents": baseline_result.get("estimated_cost_cents", 0),
            "feasible": baseline_result.get("feasible", False),
            "step_count": len(baseline_result.get("step_estimates", [])),
        }

        memory_trace = {
            "workflow_id": workflow_id or "memory",
            "memory_enabled": True,
            "cost_cents": memory_result.get("estimated_cost_cents", 0),
            "feasible": memory_result.get("feasible", False),
            "step_count": len(memory_result.get("step_estimates", [])),
        }

        comparison = await drift_detector.compare_traces(baseline_trace, memory_trace)

        # M7: Emit drift detection metrics
        if comparison.drift_detected:
            try:
                from app.memory.memory_service import MEMORY_DRIFT_DETECTED, MEMORY_DRIFT_SCORE

                severity = (
                    "high" if comparison.drift_score > 0.3 else "medium" if comparison.drift_score > 0.15 else "low"
                )
                MEMORY_DRIFT_DETECTED.labels(tenant_id=workflow_id or "unknown", severity=severity).inc()
                MEMORY_DRIFT_SCORE.labels(workflow_id=workflow_id or "unknown").set(comparison.drift_score)
            except ImportError:
                pass

        return comparison.drift_detected, comparison.drift_score

    except Exception as e:
        logger.warning(f"Drift detection error: {e}")
        return False, 0.0


# API Endpoints
@router.get("/v2/status", response_model=SandboxStatusResponse)
async def get_sandbox_status():
    """
    Get current V2 sandbox status.

    Returns information about:
    - Whether sandbox is enabled (feature flag)
    - Whether circuit breaker is open (auto-disabled due to drift)
    - Current model version
    - Drift thresholds
    """
    config = get_config()
    circuit_breaker = get_circuit_breaker()

    # Use async method since we're in an async endpoint
    circuit_breaker_open = await circuit_breaker.is_disabled()

    return SandboxStatusResponse(
        sandbox_enabled=is_v2_sandbox_enabled(),
        circuit_breaker_open=circuit_breaker_open,
        disabled_by_drift=is_v2_disabled_by_drift(),
        model_version=config.model_version,
        adapter_version=config.adapter_version,
        drift_threshold=config.drift_threshold,
    )


@router.post("/v2/simulate", response_model=SandboxSimulateResponse)
async def simulate_v2(request: SimulateRequest):
    """
    Run simulation through V2 sandbox.

    This endpoint always runs V1 for production results.
    If sandbox is enabled, also runs V2 in shadow mode
    and returns comparison metrics.

    The V1 result is always the authoritative result.
    V2 is for validation only.

    M7 Enhancements:
    - Memory context injection for simulations
    - Post-execution memory updates via rules engine
    - Drift detection between baseline and memory-enabled runs
    """
    # Convert request to plan format (include iterations for cost calculation)
    plan = [{"skill": step.skill, "params": step.params, "iterations": step.iterations} for step in request.plan]

    # M7: Determine if memory should be injected
    use_memory = request.inject_memory if request.inject_memory is not None else MEMORY_CONTEXT_INJECTION
    # AUTH_DESIGN.md: AUTH-TENANT-005 - No fallback tenant. Missing tenant is hard failure.
    if not request.tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    tenant_id = request.tenant_id

    # M7: Get memory context if enabled
    memory_context = {}
    memory_context_keys = []
    if use_memory and _memory_features_enabled:
        memory_context = await get_memory_context(
            tenant_id=tenant_id, workflow_id=request.workflow_id, agent_id=request.agent_id
        )
        memory_context_keys = list(memory_context.keys())
        logger.debug(f"Injecting memory context: {memory_context_keys}")

    # Run through sandbox
    # Note: Memory context could be passed to simulate_with_sandbox if the
    # underlying engine supports it. For now, we track it in the response.
    result = await simulate_with_sandbox(
        plan=plan,
        budget_cents=request.budget_cents,
        tenant_id=request.tenant_id,
        run_id=request.run_id,
    )

    # Build response
    # PIN-254 Phase C Fix: Include side-effect disclosure
    side_effects = SideEffectDisclosure(
        memory_write_occurred=False,  # Will be updated below if writes occur
        memory_write_feature_flag="MEMORY_POST_UPDATE",
        memory_write_enabled=MEMORY_POST_UPDATE and _memory_features_enabled,
        disclaimer="Simulation may update memory when MEMORY_POST_UPDATE=true.",
    )

    response = SandboxSimulateResponse(
        v1_feasible=result.v1_result.feasible,
        v1_cost_cents=result.v1_result.estimated_cost_cents,
        v1_duration_ms=result.v1_result.estimated_duration_ms,
        sandbox_enabled=result.sandbox_enabled,
        v2_error=result.v2_error,
        # M7: Include memory context info
        memory_context_keys=memory_context_keys if memory_context_keys else None,
        # PIN-254 Phase C Fix: Side-effect transparency
        side_effects=side_effects,
    )

    # Add V2 result if available
    if result.v2_result:
        response.v2_result = V2SimulationResponse(
            feasible=result.v2_result.feasible,
            status=result.v2_result.status.value,
            estimated_cost_cents=result.v2_result.estimated_cost_cents,
            estimated_duration_ms=result.v2_result.estimated_duration_ms,
            budget_remaining_cents=result.v2_result.budget_remaining_cents,
            confidence_score=result.v2_result.confidence_score,
            model_version=result.v2_result.model_version,
            step_estimates=[
                SimulationStepResult(
                    step_index=e["step_index"],
                    skill_id=e["skill_id"],
                    cost_cents=e["cost_cents"],
                    latency_ms=e["latency_ms"],
                    confidence=e["confidence"],
                )
                for e in result.v2_result.step_estimates
            ],
            risks=result.v2_result.risks,
            warnings=result.v2_result.warnings,
            runtime_ms=result.v2_result.runtime_ms,
        )

        # M7: Apply post-execution memory updates
        if MEMORY_POST_UPDATE and _memory_features_enabled:
            simulation_result = {
                "estimated_cost_cents": result.v2_result.estimated_cost_cents,
                "feasible": result.v2_result.feasible,
                "step_estimates": result.v2_result.step_estimates,
                "status": result.v2_result.status.value
                if hasattr(result.v2_result.status, "value")
                else str(result.v2_result.status),
            }

            # Use sync mode for tests - blocks until updates are applied
            if MEMORY_POST_UPDATE_SYNC:
                # Synchronous apply - useful for integration tests
                success = apply_update_rules_sync(
                    tenant_id=tenant_id,
                    workflow_id=request.workflow_id,
                    request_id=request.run_id,
                    trace_input={"plan": plan, "budget_cents": request.budget_cents},
                    trace_output=simulation_result,
                )
                # Also run the existing async update for full coverage
                updates_applied = await apply_post_execution_updates(
                    tenant_id=tenant_id,
                    workflow_id=request.workflow_id,
                    agent_id=request.agent_id,
                    simulation_result=simulation_result,
                )
                response.memory_updates_applied = updates_applied
                # PIN-254 Phase C Fix: Track that memory write occurred
                if updates_applied > 0 and response.side_effects:
                    response.side_effects.memory_write_occurred = True
            else:
                # Async apply - non-blocking, default for production
                updates_applied = await apply_post_execution_updates(
                    tenant_id=tenant_id,
                    workflow_id=request.workflow_id,
                    agent_id=request.agent_id,
                    simulation_result=simulation_result,
                )
                response.memory_updates_applied = updates_applied
                # PIN-254 Phase C Fix: Track that memory write occurred
                if updates_applied > 0 and response.side_effects:
                    response.side_effects.memory_write_occurred = True

        # M7: Drift detection between baseline and memory-enabled runs
        if DRIFT_DETECTION_ENABLED and memory_context and _memory_features_enabled:
            # Compare V1 (baseline) vs V2 (potentially memory-enhanced)
            drift_detected, drift_score = await detect_simulation_drift(
                baseline_result={
                    "estimated_cost_cents": result.v1_result.estimated_cost_cents,
                    "feasible": result.v1_result.feasible,
                    "step_estimates": [],
                },
                memory_result={
                    "estimated_cost_cents": result.v2_result.estimated_cost_cents,
                    "feasible": result.v2_result.feasible,
                    "step_estimates": result.v2_result.step_estimates,
                },
                workflow_id=request.workflow_id,
            )
            response.drift_detected = drift_detected
            response.drift_score = drift_score

    # Add comparison if available
    if result.comparison:
        response.comparison = ComparisonResponse(
            verdict=result.comparison.verdict.value,
            v1_cost_cents=result.comparison.v1_cost_cents,
            v2_cost_cents=result.comparison.v2_cost_cents,
            cost_delta_cents=result.comparison.cost_delta_cents,
            cost_delta_pct=result.comparison.cost_delta_pct,
            drift_score=result.comparison.drift_score,
            feasibility_match=result.comparison.feasibility_match,
        )

    return response


@router.post("/v2/reset")
async def reset_circuit_breaker(
    reason: Optional[str] = Query(None, description="Reason for reset"),
):
    """
    Reset the V2 circuit breaker.

    This re-enables V2 sandbox after it was auto-disabled due to drift.
    Should only be called after investigating and fixing the drift cause.

    Returns success status and updated circuit breaker state.
    """
    circuit_breaker = get_circuit_breaker()

    # Use async methods in async endpoint
    is_disabled = await circuit_breaker.is_disabled()
    if not is_disabled:
        state = await circuit_breaker.get_state()
        return {
            "success": True,
            "message": "Circuit breaker was already closed",
            "state": state.to_dict(),
        }

    success = await circuit_breaker.reset_v2(reason=reason or "Manual reset via API")

    state = await circuit_breaker.get_state()
    return {
        "success": success,
        "message": "Circuit breaker reset" if success else "Failed to reset",
        "state": state.to_dict(),
    }


@router.get("/v2/incidents")
async def get_incidents(
    include_resolved: bool = Query(False, description="Include resolved incidents"),
    limit: int = Query(10, ge=1, le=100, description="Max incidents to return"),
):
    """
    Get circuit breaker incidents.

    Returns recent incidents that caused circuit breaker trips.
    Useful for investigating drift causes.
    """
    circuit_breaker = get_circuit_breaker()
    incidents = circuit_breaker.get_incidents(
        include_resolved=include_resolved,
        limit=limit,
    )

    return {
        "incidents": [i.to_dict() for i in incidents],
        "total": len(incidents),
    }


@router.get("/divergence", response_model=DivergenceReportResponse)
async def get_divergence_report(
    start_date: Optional[datetime] = Query(None, description="Start of analysis period"),
    end_date: Optional[datetime] = Query(None, description="End of analysis period"),
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    days: int = Query(7, ge=1, le=90, description="Days to analyze (if start_date not provided)"),
):
    """
    Get cost divergence report between V1 and V2.

    Returns metrics:
    - delta_p50: Median cost delta
    - delta_p90: 90th percentile cost delta
    - kl_divergence: KL divergence between distributions
    - outlier_count: Number of outlier samples
    - fail_ratio: Ratio of major drift samples
    - matching_rate: Ratio of matching samples
    """
    if end_date is None:
        end_date = datetime.now(timezone.utc)
    if start_date is None:
        start_date = end_date - timedelta(days=days)

    report = await generate_divergence_report(
        start_date=start_date,
        end_date=end_date,
        tenant_id=tenant_id,
    )

    return DivergenceReportResponse(
        start_date=report.start_date,
        end_date=report.end_date,
        version=report.version,
        sample_count=report.sample_count,
        delta_p50=report.delta_p50,
        delta_p90=report.delta_p90,
        kl_divergence=report.kl_divergence,
        outlier_count=report.outlier_count,
        fail_ratio=report.fail_ratio,
        matching_rate=report.matching_rate,
        detailed_samples=report.detailed_samples,
    )


@router.post("/canary/run", response_model=CanaryRunResponse)
async def trigger_canary_run(
    sample_count: int = Query(100, ge=10, le=1000, description="Number of samples"),
    drift_threshold: float = Query(0.2, ge=0.0, le=1.0, description="Drift threshold"),
):
    """
    Trigger a canary run on-demand.

    The canary run:
    1. Loads samples from recent provenance logs
    2. Runs both V1 and V2 on each sample
    3. Computes drift metrics
    4. Returns pass/fail verdict

    Note: Daily canary runs are automatic via systemd timer.
    This endpoint is for manual testing.
    """
    report = await run_canary(
        sample_count=sample_count,
        drift_threshold=drift_threshold,
    )

    return CanaryRunResponse(
        run_id=report.run_id,
        status=report.status,
        passed=report.passed,
        total_samples=report.total_samples,
        matching_samples=report.matching_samples,
        kl_divergence=report.kl_divergence,
        failure_reasons=report.failure_reasons,
        artifact_paths=report.artifact_paths,
    )


@router.get("/canary/reports")
async def get_canary_reports(
    limit: int = Query(10, ge=1, le=100, description="Max reports to return"),
):
    """
    Get recent canary run reports.

    Returns summaries of recent canary runs.
    Full artifacts are available at the artifact_paths.
    """
    # TODO: Implement canary report storage and retrieval
    return {
        "reports": [],
        "message": "Canary report retrieval not yet implemented",
    }


# ============== Dataset Validation Endpoints ==============

from app.costsim.datasets import get_dataset_validator, validate_all_datasets
from app.costsim.datasets import validate_dataset as validate_ds


class DatasetInfo(BaseModel):
    """Dataset information."""

    id: str
    name: str
    description: str
    sample_count: int
    thresholds: Dict[str, float]


class ValidationResultResponse(BaseModel):
    """Validation result response."""

    dataset_id: str
    dataset_name: str
    sample_count: int
    mean_error: float
    median_error: float
    std_deviation: float
    outlier_pct: float
    drift_score: float
    verdict: str
    details: Dict[str, Any]
    timestamp: datetime


@router.get("/datasets", response_model=List[DatasetInfo])
async def list_datasets():
    """
    List all available reference datasets.

    Reference datasets are used to validate V2 accuracy:
    - low_variance: Simple, predictable plans
    - high_variance: Complex, variable plans
    - mixed_city: Real-world mixed workloads
    - noise_injected: Edge cases and invalid inputs
    - historical: Real production patterns
    """
    validator = get_dataset_validator()
    datasets = validator.list_datasets()
    return [
        DatasetInfo(
            id=ds["id"],
            name=ds["name"],
            description=ds["description"],
            sample_count=ds["sample_count"],
            thresholds=ds["thresholds"],
        )
        for ds in datasets
    ]


@router.get("/datasets/{dataset_id}")
async def get_dataset_info(dataset_id: str):
    """Get information about a specific dataset."""
    validator = get_dataset_validator()
    dataset = validator.get_dataset(dataset_id)

    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")

    return {
        "id": dataset.id,
        "name": dataset.name,
        "description": dataset.description,
        "sample_count": len(dataset.samples),
        "thresholds": dataset.validation_thresholds,
        "sample_tags": list(set(tag for sample in dataset.samples for tag in sample.tags)),
    }


@router.post("/datasets/{dataset_id}/validate", response_model=ValidationResultResponse)
async def validate_against_dataset(dataset_id: str):
    """
    Validate V2 against a specific reference dataset.

    Runs V2 on all samples in the dataset and compares
    against expected values. Returns metrics and verdict.

    Verdict is "acceptable" if all metrics are within thresholds.
    """
    try:
        result = await validate_ds(dataset_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return ValidationResultResponse(
        dataset_id=result.dataset_id,
        dataset_name=result.dataset_name,
        sample_count=result.sample_count,
        mean_error=result.mean_error,
        median_error=result.median_error,
        std_deviation=result.std_deviation,
        outlier_pct=result.outlier_pct,
        drift_score=result.drift_score,
        verdict=result.verdict,
        details=result.details,
        timestamp=result.timestamp,
    )


@router.post("/datasets/validate-all")
async def validate_all():
    """
    Validate V2 against ALL reference datasets.

    This is a comprehensive validation that runs all 5 datasets.
    Use for pre-release validation or debugging.
    """
    results = await validate_all_datasets()

    all_passed = all(r.verdict == "acceptable" for r in results.values())

    return {
        "all_passed": all_passed,
        "results": {
            dataset_id: {
                "dataset_name": result.dataset_name,
                "sample_count": result.sample_count,
                "mean_error": result.mean_error,
                "drift_score": result.drift_score,
                "verdict": result.verdict,
            }
            for dataset_id, result in results.items()
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
