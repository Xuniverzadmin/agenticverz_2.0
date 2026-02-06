# Layer: L2 — Product APIs
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: M25 Integration System - Loop status, checkpoints, graduation, prevention timeline
# Authority: WRITE checkpoint resolutions, graduation records (API self-authority)
# Callers: Ops Console, Founder Console (NOT Customer Console)
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: M25 Integration System
# capability_id: CAP-018
#
# GOVERNANCE NOTE:
# This is INTERNAL infrastructure for M25 learning loop management.
# NOT the Customer Console "Integrations" domain (that is in integrations.py).
# Requires founder/ops authentication.

"""
M25 Integration API

Endpoints for:
- Loop status monitoring
- Human checkpoint resolution
- Integration statistics
- Retry/revert operations
- Graduation status (M25 learning proof)
- Prevention timeline (Gate 3)
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# PIN-318: Phase 1.2 Authority Hardening - Replace query param auth with proper token auth
from app.auth.console_auth import FounderToken, verify_fops_token

# L4-provided registry and session context (L2 must not import sqlalchemy/sqlmodel/app.db directly)
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    get_async_session_context,
    get_operation_registry,
    OperationContext,
)
from app.schemas.response import wrap_dict


def get_tenant_id_from_token(token: FounderToken = Depends(verify_fops_token)) -> str:
    """Get tenant ID from founder token - PIN-318 secure implementation."""
    # Founders have cross-tenant access, use "system" as default
    return "system"


def get_current_user_from_token(token: FounderToken = Depends(verify_fops_token)) -> dict:
    """Get current user from founder token - PIN-318 secure implementation."""
    return {"sub": token.sub, "role": token.role.value if hasattr(token.role, "value") else str(token.role)}


# Legacy query param helpers (DEPRECATED - kept for backwards compat during migration)
def get_tenant_id(tenant_id: str = Query(..., description="Tenant ID")) -> str:
    """DEPRECATED: Get tenant ID from query parameter. Use get_tenant_id_from_token instead."""
    return tenant_id


def get_current_user(user_id: Optional[str] = Query(None, description="User ID")) -> Optional[dict]:
    """DEPRECATED: Get current user from query parameter. Use get_current_user_from_token instead."""
    if user_id:
        return {"id": user_id}
    return None


from app.integrations.events import (
    LoopStage,
)

logger = logging.getLogger(__name__)

# PIN-318: Router-level auth - all endpoints require founder token (aud="fops")
router = APIRouter(prefix="/integration", tags=["integration"], dependencies=[Depends(verify_fops_token)])


# =============================================================================
# PYDANTIC MODELS
# =============================================================================


class LoopStatusResponse(BaseModel):
    """Response for loop status endpoint."""

    loop_id: str
    incident_id: str
    tenant_id: str
    current_stage: str
    stages_completed: list[str]
    stages_failed: list[str]
    total_stages: int = 5
    completion_pct: float
    is_complete: bool
    is_blocked: bool
    failure_state: Optional[str] = None
    pending_checkpoints: list[str] = []
    narrative: Optional[dict] = None


class StageDetail(BaseModel):
    """Detail for a single stage."""

    stage: str
    status: str  # completed, failed, pending, in_progress
    timestamp: Optional[datetime] = None
    details: Optional[dict] = None
    failure_state: Optional[str] = None
    confidence_band: Optional[str] = None


class CheckpointResponse(BaseModel):
    """Response for human checkpoint."""

    checkpoint_id: str
    checkpoint_type: str
    incident_id: str
    stage: str
    target_id: str
    description: str
    options: list[str]
    created_at: datetime
    is_pending: bool
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution: Optional[str] = None


class ResolveCheckpointRequest(BaseModel):
    """Request to resolve a checkpoint."""

    resolution: str = Field(..., description="One of the available options")


class IntegrationStatsResponse(BaseModel):
    """Statistics for integration loop."""

    total_incidents: int
    patterns_matched: int
    patterns_created: int
    strong_matches: int
    weak_matches: int
    novel_patterns: int
    recoveries_suggested: int
    recoveries_applied: int
    recoveries_rejected: int
    policies_generated: int
    policies_in_shadow: int
    policies_active: int
    routing_adjustments: int
    adjustments_rolled_back: int
    avg_loop_completion_time_ms: float
    loop_completion_rate: float
    checkpoints_pending: int
    checkpoints_resolved: int
    period_hours: int


class RetryStageRequest(BaseModel):
    """Request to retry a failed stage."""

    stage: str = Field(..., description="Stage to retry")


class RevertLoopRequest(BaseModel):
    """Request to revert a loop."""

    reason: str = Field(..., description="Reason for revert")


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("/loop/{incident_id}", response_model=LoopStatusResponse)
async def get_loop_status(
    incident_id: str,
    tenant_id: str = Depends(get_tenant_id),
) -> LoopStatusResponse:
    """
    Get current loop status for an incident.

    Returns the full loop state including:
    - Completed and failed stages
    - Pending human checkpoints
    - Narrative artifacts for storytelling
    """
    # Get dispatcher (lazy import to avoid circular deps)
    from app.integrations import get_dispatcher

    dispatcher = get_dispatcher()

    loop_status = await dispatcher.get_loop_status(incident_id)

    if not loop_status:
        raise HTTPException(status_code=404, detail=f"No loop found for incident {incident_id}")

    if loop_status.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")

    display = loop_status.to_console_display()

    return LoopStatusResponse(
        loop_id=loop_status.loop_id,
        incident_id=loop_status.incident_id,
        tenant_id=loop_status.tenant_id,
        current_stage=loop_status.current_stage.value,
        stages_completed=loop_status.stages_completed,
        stages_failed=loop_status.stages_failed,
        completion_pct=display["completion_pct"],
        is_complete=loop_status.is_complete,
        is_blocked=loop_status.is_blocked,
        failure_state=display["failure_state"],
        pending_checkpoints=loop_status.pending_checkpoints,
        narrative=display.get("narrative"),
    )


@router.get("/loop/{incident_id}/stages", response_model=list[StageDetail])
async def get_loop_stages(
    incident_id: str,
    tenant_id: str = Depends(get_tenant_id),
) -> list[StageDetail]:
    """Get detailed stage information for a loop."""
    async with get_async_session_context() as session:
        registry = get_operation_registry()
        result = await registry.execute(
            "m25.read_stages",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={"incident_id": incident_id},
            ),
        )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Failed to read stages")

    # Handler returns pre-formatted stage data
    stages = []
    for event in result.data:
        stages.append(
            StageDetail(
                stage=event["stage"],
                status="failed" if event.get("failure_state") else "completed",
                timestamp=datetime.fromisoformat(event["created_at"]) if event.get("created_at") else None,
                details=event.get("details") if isinstance(event.get("details"), dict) else {},
                failure_state=event.get("failure_state"),
                confidence_band=event.get("confidence_band"),
            )
        )

    return wrap_dict({"items": [s.model_dump() for s in stages], "total": len(stages)})


@router.get("/loop/{incident_id}/stream")
async def stream_loop_status(
    incident_id: str,
    tenant_id: str = Depends(get_tenant_id),
):
    """
    SSE endpoint for live loop status updates.

    Connect to receive real-time updates as the loop progresses.
    """
    import json

    async def event_generator():
        from app.integrations import get_redis_client

        redis = get_redis_client()

        channel = f"loop:{tenant_id}:{incident_id}"
        pubsub = redis.pubsub()
        await pubsub.subscribe(channel)

        try:
            # Send initial status
            from app.integrations import get_dispatcher

            dispatcher = get_dispatcher()
            status = await dispatcher.get_loop_status(incident_id)
            if status:
                yield f"data: {json.dumps(status.to_console_display())}\n\n"

            # Stream updates
            async for message in pubsub.listen():
                if message["type"] == "message":
                    yield f"data: {message['data']}\n\n"
        finally:
            await pubsub.unsubscribe(channel)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/loop/{incident_id}/retry", response_model=LoopStatusResponse)
async def retry_loop_stage(
    incident_id: str,
    request: RetryStageRequest,
    tenant_id: str = Depends(get_tenant_id),
) -> LoopStatusResponse:
    """Retry a failed loop stage."""
    from app.integrations import get_dispatcher

    dispatcher = get_dispatcher()

    try:
        stage = LoopStage(request.stage)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {request.stage}")

    try:
        await dispatcher.retry_failed_stage(incident_id, stage, tenant_id)
        status = await dispatcher.get_loop_status(incident_id)

        return LoopStatusResponse(
            loop_id=status.loop_id,
            incident_id=status.incident_id,
            tenant_id=status.tenant_id,
            current_stage=status.current_stage.value,
            stages_completed=status.stages_completed,
            stages_failed=status.stages_failed,
            completion_pct=status.completion_pct,
            is_complete=status.is_complete,
            is_blocked=status.is_blocked,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/loop/{incident_id}/revert")
async def revert_loop(
    incident_id: str,
    request: RevertLoopRequest,
    tenant_id: str = Depends(get_tenant_id),
    user: dict = Depends(get_current_user),
) -> dict:
    """
    Revert all changes made by a loop.

    This is the ultimate human override - use with caution.
    """
    from app.integrations import get_dispatcher

    dispatcher = get_dispatcher()

    user_id = user.get("sub", "unknown")

    try:
        await dispatcher.revert_loop(incident_id, user_id, request.reason)
        return wrap_dict({
            "status": "reverted",
            "incident_id": incident_id,
            "reverted_by": user_id,
            "reason": request.reason,
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# CHECKPOINT ENDPOINTS
# =============================================================================


@router.get("/checkpoints", response_model=list[CheckpointResponse])
async def list_pending_checkpoints(
    tenant_id: str = Depends(get_tenant_id),
) -> list[CheckpointResponse]:
    """List all pending human checkpoints for the tenant."""
    from app.integrations import get_dispatcher

    dispatcher = get_dispatcher()

    checkpoints = await dispatcher.get_pending_checkpoints(tenant_id)

    return [
        CheckpointResponse(
            checkpoint_id=cp.checkpoint_id,
            checkpoint_type=cp.checkpoint_type.value,
            incident_id=cp.incident_id,
            stage=cp.stage.value,
            target_id=cp.target_id,
            description=cp.description,
            options=cp.options,
            created_at=cp.created_at,
            is_pending=cp.is_pending,
            resolved_at=cp.resolved_at,
            resolved_by=cp.resolved_by,
            resolution=cp.resolution,
        )
        for cp in checkpoints
    ]


@router.get("/checkpoints/{checkpoint_id}", response_model=CheckpointResponse)
async def get_checkpoint(
    checkpoint_id: str,
    tenant_id: str = Depends(get_tenant_id),
) -> CheckpointResponse:
    """Get details of a specific checkpoint."""
    async with get_async_session_context() as session:
        registry = get_operation_registry()
        result = await registry.execute(
            "m25.read_checkpoint",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={"checkpoint_id": checkpoint_id},
            ),
        )

    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail="Checkpoint not found")
        raise HTTPException(status_code=500, detail=result.error or "Failed to read checkpoint")

    import json

    cp = result.data
    options = cp["options"] if isinstance(cp["options"], list) else json.loads(cp["options"] or "[]")

    return CheckpointResponse(
        checkpoint_id=cp["id"],
        checkpoint_type=cp["checkpoint_type"],
        incident_id=cp["incident_id"],
        stage=cp["stage"],
        target_id=cp["target_id"],
        description=cp["description"] or "",
        options=options,
        created_at=datetime.fromisoformat(cp["created_at"]) if cp.get("created_at") else datetime.now(timezone.utc),
        is_pending=cp.get("resolved_at") is None,
        resolved_at=datetime.fromisoformat(cp["resolved_at"]) if cp.get("resolved_at") else None,
        resolved_by=cp.get("resolved_by"),
        resolution=cp.get("resolution"),
    )


@router.post("/checkpoints/{checkpoint_id}/resolve")
async def resolve_checkpoint(
    checkpoint_id: str,
    request: ResolveCheckpointRequest,
    tenant_id: str = Depends(get_tenant_id),
    user: dict = Depends(get_current_user),
) -> dict:
    """
    Resolve a pending checkpoint.

    Available resolutions depend on checkpoint type:
    - approve_policy: approve, reject, modify
    - approve_recovery: apply, reject, defer
    - simulate_routing: apply, cancel
    - revert_loop: confirm_revert, cancel
    """
    from app.integrations import get_dispatcher

    dispatcher = get_dispatcher()

    user_id = user.get("sub", "unknown")

    try:
        result = await dispatcher.resolve_checkpoint(checkpoint_id, user_id, request.resolution)

        return wrap_dict({
            "status": "resolved",
            "checkpoint_id": checkpoint_id,
            "resolution": request.resolution,
            "resolved_by": user_id,
            "loop_resumed": result is not None,
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# STATISTICS ENDPOINT
# =============================================================================


@router.get("/stats", response_model=IntegrationStatsResponse)
async def get_integration_stats(
    tenant_id: str = Depends(get_tenant_id),
    hours: int = Query(24, ge=1, le=720, description="Period in hours"),
) -> IntegrationStatsResponse:
    """Get integration loop statistics for the specified period."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    async with get_async_session_context() as session:
        registry = get_operation_registry()
        result = await registry.execute(
            "m25.read_stats",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={"cutoff": cutoff.isoformat()},
            ),
        )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Failed to read stats")

    # Handler returns combined stats dict
    stats = result.data
    loops = stats["loops"]
    patterns = stats["patterns"]
    recoveries = stats["recoveries"]
    policies = stats["policies"]
    routing = stats["routing"]
    checkpoints = stats["checkpoints"]

    total = loops["total"]
    complete = loops["complete"]

    return IntegrationStatsResponse(
        total_incidents=total,
        patterns_matched=patterns["total"] - patterns["novel"],
        patterns_created=patterns["novel"],
        strong_matches=patterns["strong"],
        weak_matches=patterns["weak"],
        novel_patterns=patterns["novel"],
        recoveries_suggested=recoveries["total"],
        recoveries_applied=recoveries["applied"],
        recoveries_rejected=recoveries["rejected"],
        policies_generated=policies["total"],
        policies_in_shadow=policies["shadow"],
        policies_active=policies["active"],
        routing_adjustments=routing["total"],
        adjustments_rolled_back=routing["rolled_back"],
        avg_loop_completion_time_ms=loops["avg_time_ms"] or 0,
        loop_completion_rate=complete / total if total > 0 else 0,
        checkpoints_pending=checkpoints["pending"],
        checkpoints_resolved=checkpoints["resolved"],
        period_hours=hours,
    )


# =============================================================================
# NARRATIVE ARTIFACTS ENDPOINT
# =============================================================================


@router.get("/loop/{incident_id}/narrative")
async def get_loop_narrative(
    incident_id: str,
    tenant_id: str = Depends(get_tenant_id),
) -> dict:
    """
    Get narrative artifacts for an incident loop.

    Returns storytelling elements:
    - before_after: Before vs After this incident
    - policy_origin: Policy born from this failure
    - agent_improvement: How agent behavior improved
    """
    from app.integrations import get_dispatcher

    dispatcher = get_dispatcher()

    loop_status = await dispatcher.get_loop_status(incident_id)

    if not loop_status:
        raise HTTPException(status_code=404, detail="Loop not found")

    if loop_status.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")

    display = loop_status.to_console_display()

    return wrap_dict({
        "incident_id": incident_id,
        "is_complete": loop_status.is_complete,
        "narrative": display.get("narrative", {}),
        "stages": display.get("stages", []),
    })


# =============================================================================
# GRADUATION STATUS ENDPOINTS (M25 Learning Proof - HARDENED)
# =============================================================================
#
# CRITICAL INVARIANTS:
# 1. Graduation is DERIVED from evidence, never manually set
# 2. Simulation state is SEPARATE from real graduation
# 3. Graduation can DEGRADE when evidence regresses
# 4. Capabilities are LOCKED until gates pass


class GateEvidenceResponse(BaseModel):
    """Evidence for a graduation gate."""

    name: str
    description: str
    passed: bool
    score: float
    evidence: dict
    degraded: bool = False


class CapabilityStatus(BaseModel):
    """Status of a capability gate."""

    unlocked: list[str]
    blocked: list[str]


class SimulationStatus(BaseModel):
    """Simulation mode status - separate from real graduation."""

    is_demo_mode: bool
    simulated_gates: dict[str, bool]
    warning: Optional[str] = None


class HardenedGraduationResponse(BaseModel):
    """
    Hardened graduation status response.

    Key differences from v1:
    - Status is DERIVED from evidence, not manually set
    - Includes capability gates (what's unlocked/blocked)
    - Includes simulation status (separate from real)
    - Includes degradation info
    """

    # Derived status
    status: str
    level: str
    is_graduated: bool
    is_degraded: bool

    # Gates (all derived from evidence)
    gates: dict[str, GateEvidenceResponse]

    # Capability gates (real behavior changes)
    capabilities: CapabilityStatus

    # Simulation state (separate from real)
    simulation: SimulationStatus

    # Metrics
    computed_at: str
    evidence_window_days: int

    # Degradation info (if applicable)
    degradation: Optional[dict] = None

    # What to do next
    next_action: str


@router.get("/graduation", response_model=HardenedGraduationResponse)
async def get_graduation_status(
    tenant_id: str = Depends(get_tenant_id),
) -> HardenedGraduationResponse:
    """
    Get M25 graduation status (HARDENED).

    CRITICAL: This status is DERIVED from evidence, not manually set.

    Returns:
    - Derived graduation level (alpha/beta/candidate/complete/degraded)
    - Gate status with evidence
    - Capability gates (what's unlocked/blocked)
    - Simulation state (separate from real graduation)
    - Degradation info if status has regressed

    Graduation is computed from real evidence only:
    - Simulated records are excluded
    - Status is re-evaluated on each call
    - Degradation occurs when evidence regresses
    """
    # Import graduation engine
    from app.integrations.graduation_engine import (
        CapabilityGates,
        GraduationEngine,
        GraduationEvidence,
    )

    async with get_async_session_context() as session:
        # Compute derived status from evidence
        engine = GraduationEngine()

        try:
            evidence = await GraduationEvidence.fetch_from_database(session)
            status = engine.compute(evidence)
        except Exception as e:
            # Fallback if tables don't exist yet
            logger.warning(f"Graduation evidence fetch failed: {e}")
            # Return alpha status
            return HardenedGraduationResponse(
                status="M25-ALPHA (0/3 gates) [evidence unavailable]",
                level="alpha",
                is_graduated=False,
                is_degraded=False,
                gates={
                    "prevention": GateEvidenceResponse(
                        name="Prevention Proof",
                        description="Policy prevented at least one incident recurrence",
                        passed=False,
                        score=0.0,
                        evidence={"error": "Evidence tables not yet available"},
                        degraded=False,
                    ),
                    "rollback": GateEvidenceResponse(
                        name="Regret Rollback",
                        description="At least one policy auto-demoted due to causing harm",
                        passed=False,
                        score=0.0,
                        evidence={"error": "Evidence tables not yet available"},
                        degraded=False,
                    ),
                    "timeline": GateEvidenceResponse(
                        name="Console Timeline",
                        description="Timeline visibly shows learning in action",
                        passed=False,
                        score=0.0,
                        evidence={"error": "Evidence tables not yet available"},
                        degraded=False,
                    ),
                },
                capabilities=CapabilityStatus(
                    unlocked=[], blocked=["auto_apply_recovery", "auto_activate_policy", "full_auto_routing"]
                ),
                simulation=SimulationStatus(
                    is_demo_mode=False, simulated_gates={"gate1": False, "gate2": False, "gate3": False}
                ),
                computed_at=datetime.now(timezone.utc).isoformat(),
                evidence_window_days=30,
                next_action="Run migration 044_m25_graduation_hardening first",
            )

        # Get simulation state (separate from real) via registry dispatch
        registry = get_operation_registry()
        sim_result = await registry.execute(
            "m25.read_simulation_state",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
            ),
        )

        if not sim_result.success:
            # Fallback to empty sim state if read fails
            sim_state = {"sim_gate1": False, "sim_gate2": False, "sim_gate3": False}
        else:
            sim_state = sim_result.data

        simulation = SimulationStatus(
            is_demo_mode=(sim_state["sim_gate1"] or sim_state["sim_gate2"] or sim_state["sim_gate3"]),
            simulated_gates={
                "gate1": sim_state["sim_gate1"],
                "gate2": sim_state["sim_gate2"],
                "gate3": sim_state["sim_gate3"],
            },
            warning="SIMULATION DATA EXISTS - Real graduation excludes simulated records"
            if (sim_state["sim_gate1"] or sim_state["sim_gate2"] or sim_state["sim_gate3"])
            else None,
        )

    # Build gate responses
    gates = {}
    for name, gate in status.gates.items():
        gates[name] = GateEvidenceResponse(
            name=gate.name,
            description={
                "prevention": "Policy prevented at least one incident recurrence",
                "rollback": "At least one policy auto-demoted due to causing harm",
                "timeline": "Timeline visibly shows learning in action",
            }.get(name, gate.name),
            passed=gate.passed,
            score=gate.score,
            evidence=gate.evidence,
            degraded=gate.degraded,
        )

    # Capability gates
    capabilities = CapabilityStatus(
        unlocked=CapabilityGates.get_unlocked_capabilities(status),
        blocked=CapabilityGates.get_blocked_capabilities(status),
    )

    # Next action
    if status.is_graduated:
        next_action = "M25 COMPLETE. All capabilities unlocked. Proceed to M26."
    elif status.is_degraded:
        next_action = f"DEGRADED: {status.degradation_reason}. Fix evidence regression."
    elif not gates.get(
        "prevention", GateEvidenceResponse(name="", description="", passed=False, score=0, evidence={}, degraded=False)
    ).passed:
        next_action = "Waiting for real prevention evidence (not simulated)"
    elif not gates.get(
        "rollback", GateEvidenceResponse(name="", description="", passed=False, score=0, evidence={}, degraded=False)
    ).passed:
        next_action = "Waiting for real regret/demotion evidence (not simulated)"
    else:
        next_action = "Waiting for real timeline view evidence (not simulated)"

    return HardenedGraduationResponse(
        status=status.status_label,
        level=status.level.value,
        is_graduated=status.is_graduated,
        is_degraded=status.is_degraded,
        gates=gates,
        capabilities=capabilities,
        simulation=simulation,
        computed_at=status.computed_at.isoformat(),
        evidence_window_days=30,
        degradation={
            "from_level": status.degraded_from.value if status.degraded_from else None,
            "at": status.degraded_at.isoformat() if status.degraded_at else None,
            "reason": status.degradation_reason,
        }
        if status.is_degraded
        else None,
        next_action=next_action,
    )


class SimulatePreventionRequest(BaseModel):
    """Request to simulate a prevention event for demo/testing."""

    policy_id: str = Field(..., description="Policy that prevented the recurrence")
    pattern_id: str = Field(..., description="Pattern that matched")
    original_incident_id: str = Field(..., description="Original incident that created the policy")
    confidence: float = Field(0.92, ge=0.0, le=1.0, description="Match confidence")


@router.post("/graduation/simulate/prevention")
async def simulate_prevention(
    request: SimulatePreventionRequest,
    tenant_id: str = Depends(get_tenant_id),
) -> dict:
    """
    Simulate a prevention event for demo/testing purposes.

    IMPORTANT: Simulated records are marked with is_simulated=true
    and DO NOT count toward real graduation.

    This endpoint creates demo data for UI testing only.
    Real graduation requires real prevention evidence.
    """
    # Use sim_ prefix to make simulated records obvious
    record_id = f"prev_sim_{uuid.uuid4().hex[:12]}"
    blocked_id = f"inc_sim_prevented_{uuid.uuid4().hex[:8]}"

    async with get_async_session_context() as session:
        # Insert prevention record WITH is_simulated=true via registry dispatch
        # This record is EXCLUDED from real graduation computation
        registry = get_operation_registry()
        result = await registry.execute(
            "m25.write_prevention",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "id": record_id,
                    "policy_id": request.policy_id,
                    "pattern_id": request.pattern_id,
                    "original_incident_id": request.original_incident_id,
                    "blocked_incident_id": blocked_id,
                    "confidence": request.confidence,
                    "is_simulated": True,
                },
            ),
        )

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error or "Failed to simulate prevention")

        # DO NOT update m25_graduation_status directly!
        # Graduation is DERIVED from real evidence only.
        # The GraduationEngine will exclude is_simulated=true records.
        # L4 handler owns the commit - no L2 commit needed.

    return wrap_dict({
        "status": "simulated",
        "prevention_id": record_id,
        "blocked_incident_id": blocked_id,
        "is_simulated": True,
        "counts_toward_graduation": False,
        "warning": "SIMULATION ONLY: This record is marked is_simulated=true and does NOT count toward real M25 graduation. Real graduation requires real prevention evidence.",
        "message": "Prevention event simulated for demo purposes.",
    })


class SimulateRegretRequest(BaseModel):
    """Request to simulate a regret event for demo/testing."""

    policy_id: str = Field(..., description="Policy that caused harm")
    regret_type: str = Field("false_positive", description="Type of regret")
    severity: int = Field(7, ge=1, le=10, description="Severity 1-10")
    description: str = Field("Simulated regret event for demo", description="Description")


@router.post("/graduation/simulate/regret")
async def simulate_regret(
    request: SimulateRegretRequest,
    tenant_id: str = Depends(get_tenant_id),
) -> dict:
    """
    Simulate a regret event for demo/testing purposes.

    IMPORTANT: Simulated records are marked with is_simulated=true
    and DO NOT count toward real graduation.

    This endpoint creates demo data for UI testing only.
    Real graduation requires real regret/demotion evidence.
    """
    # Use sim_ prefix to make simulated records obvious
    regret_id = f"regret_sim_{uuid.uuid4().hex[:12]}"

    async with get_async_session_context() as session:
        # Insert regret event WITH is_simulated=true via registry dispatch
        # This record is EXCLUDED from real graduation computation
        # Note: The handler also upserts policy_regret_summary with severity * 0.5
        registry = get_operation_registry()
        result = await registry.execute(
            "m25.write_regret",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "id": regret_id,
                    "policy_id": request.policy_id,
                    "regret_type": request.regret_type,
                    "description": request.description,
                    "severity": request.severity,
                    "is_simulated": True,
                },
            ),
        )

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error or "Failed to simulate regret")

        # DO NOT update m25_graduation_status directly!
        # Graduation is DERIVED from real evidence only.
        # The GraduationEngine will exclude is_simulated=true records.
        # L4 handler owns the commit - no L2 commit needed.

    return wrap_dict({
        "status": "simulated",
        "regret_id": regret_id,
        "policy_demoted": True,
        "is_simulated": True,
        "counts_toward_graduation": False,
        "warning": "SIMULATION ONLY: This record is marked is_simulated=true and does NOT count toward real M25 graduation. Real graduation requires real regret/demotion evidence.",
        "message": "Regret event simulated for demo purposes.",
    })


@router.post("/graduation/simulate/timeline-view")
async def simulate_timeline_view(
    incident_id: str = Query(..., description="Incident ID to mark as viewed in timeline"),
    tenant_id: str = Depends(get_tenant_id),
) -> dict:
    """
    Simulate viewing a prevention timeline for Gate 3.

    IMPORTANT: Simulated views are marked with is_simulated=true
    and DO NOT count toward real graduation.

    This endpoint creates demo data for UI testing only.
    Real graduation requires real timeline views.
    """
    view_id = f"tv_sim_{uuid.uuid4().hex[:12]}"
    session_id = f"sim_session_{uuid.uuid4().hex[:8]}"

    async with get_async_session_context() as session:
        # Insert into timeline_views WITH is_simulated=true via registry dispatch
        # This record is EXCLUDED from real graduation computation
        registry = get_operation_registry()
        result = await registry.execute(
            "m25.write_timeline_view",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "id": view_id,
                    "incident_id": incident_id,
                    "user_id": "demo_user",
                    "has_prevention": True,
                    "has_rollback": False,
                    "is_simulated": True,
                    "session_id": session_id,
                },
            ),
        )

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error or "Failed to simulate timeline view")

        # DO NOT update m25_graduation_status directly!
        # Graduation is DERIVED from real evidence only.
        # The GraduationEngine will exclude is_simulated=true records.
        # L4 handler owns the commit - no L2 commit needed.

    return wrap_dict({
        "status": "simulated",
        "view_id": view_id,
        "incident_id": incident_id,
        "is_simulated": True,
        "counts_toward_graduation": False,
        "warning": "SIMULATION ONLY: This view is marked is_simulated=true and does NOT count toward real M25 graduation. Real graduation requires real timeline views from operators.",
        "message": "Timeline view simulated for demo purposes.",
    })


@router.post("/graduation/record-view")
async def record_timeline_view(
    incident_id: str = Query(..., description="Incident ID viewed in timeline"),
    has_prevention: bool = Query(False, description="Timeline shows prevention event"),
    has_rollback: bool = Query(False, description="Timeline shows rollback event"),
    tenant_id: str = Depends(get_tenant_id),
    user: dict = Depends(get_current_user),
) -> dict:
    """
    Record a REAL timeline view for Gate 3 graduation.

    This endpoint is called by the console when a user ACTUALLY views
    an incident's prevention timeline. This counts toward real graduation.

    Call this when:
    - User opens the prevention timeline UI
    - Timeline shows learning proof (prevention or rollback)
    """
    view_id = f"tv_{uuid.uuid4().hex[:12]}"
    user_id = user.get("sub", "unknown")
    session_id = f"session_{uuid.uuid4().hex[:8]}"

    async with get_async_session_context() as session:
        # Insert REAL timeline view (is_simulated=false) via registry dispatch
        # This COUNTS toward graduation
        registry = get_operation_registry()
        result = await registry.execute(
            "m25.write_timeline_view",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "id": view_id,
                    "incident_id": incident_id,
                    "user_id": user_id,
                    "has_prevention": has_prevention,
                    "has_rollback": has_rollback,
                    "is_simulated": False,
                    "session_id": session_id,
                },
            ),
        )

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error or "Failed to record timeline view")

        # L4 handler owns the commit - no L2 commit needed.

    return wrap_dict({
        "status": "recorded",
        "view_id": view_id,
        "incident_id": incident_id,
        "is_simulated": False,
        "counts_toward_graduation": True,
        "message": "Timeline view recorded. This contributes to Gate 3 (Console Timeline) graduation.",
    })


@router.post("/graduation/re-evaluate")
async def trigger_graduation_re_evaluation(
    tenant_id: str = Depends(get_tenant_id),
) -> dict:
    """
    Trigger a re-evaluation of graduation status.

    This recalculates graduation level from current evidence.
    Useful after:
    - New prevention/regret events
    - Timeline views recorded
    - Manual verification

    Note: Graduation is automatically re-evaluated on GET /graduation,
    but this endpoint forces a fresh computation and stores history.
    """
    import json

    from app.integrations.graduation_engine import (
        GraduationEngine,
        GraduationEvidence,
    )

    async with get_async_session_context() as session:
        engine = GraduationEngine()

        try:
            evidence = await GraduationEvidence.fetch_from_database(session)
            status = engine.compute(evidence)
        except Exception as e:
            logger.warning(f"Re-evaluation failed: {e}")
            return wrap_dict({
                "status": "error",
                "message": f"Failed to compute graduation: {str(e)}",
            })

        # Store in graduation_history for audit trail via registry dispatch
        # Note: commit=False here because update_graduation_status will commit both
        registry = get_operation_registry()
        hist_result = await registry.execute(
            "m25.write_graduation_history",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "level": status.level.value,
                    "gates_json": json.dumps(
                        {
                            name: {
                                "passed": gate.passed,
                                "score": gate.score,
                                "degraded": gate.degraded,
                            }
                            for name, gate in status.gates.items()
                        }
                    ),
                    "is_degraded": status.is_degraded,
                    "degraded_from": status.degraded_from.value if status.degraded_from else None,
                    "degradation_reason": status.degradation_reason,
                    "evidence_snapshot": json.dumps(
                        {
                            "prevention_count": evidence.prevention_count,
                            "regret_count": evidence.regret_count,
                            "demotion_count": evidence.demotion_count,
                            "timeline_view_count": evidence.timeline_view_count,
                            "prevention_rate": evidence.prevention_rate,
                            "regret_rate": evidence.regret_rate,
                        }
                    ),
                    "commit": False,  # L4 will NOT commit - next operation will
                },
            ),
        )

        if not hist_result.success:
            logger.warning(f"Failed to insert graduation history: {hist_result.error}")

        # Update m25_graduation_status with derived values via registry dispatch
        # (This table still exists for backward compat, but values are DERIVED)
        # This operation commits both writes atomically (L4 owns transaction boundary)
        status_result = await registry.execute(
            "m25.update_graduation_status",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={
                    "status_label": status.status_label,
                    "is_graduated": status.is_graduated,
                    "gate1_passed": status.gates.get("prevention", type("", (), {"passed": False})).passed,
                    "gate2_passed": status.gates.get("rollback", type("", (), {"passed": False})).passed,
                    "gate3_passed": status.gates.get("timeline", type("", (), {"passed": False})).passed,
                    # commit=True (default) - L4 handler commits both writes
                },
            ),
        )

        if not status_result.success:
            logger.warning(f"Failed to update graduation status: {status_result.error}")

    return wrap_dict({
        "status": "re-evaluated",
        "level": status.level.value,
        "status_label": status.status_label,
        "is_graduated": status.is_graduated,
        "is_degraded": status.is_degraded,
        "gates_passed": sum(1 for g in status.gates.values() if g.passed),
        "message": "Graduation status re-computed from evidence.",
    })


# =============================================================================
# PREVENTION TIMELINE ENDPOINT (Gate 3 UI)
# =============================================================================


class TimelineEventResponse(BaseModel):
    """A single event in the prevention timeline."""

    type: str
    timestamp: str
    icon: str
    headline: str
    description: str
    details: dict
    is_milestone: bool = False


class PreventionTimelineResponse(BaseModel):
    """Response for prevention timeline endpoint."""

    incident_id: str
    tenant_id: str
    timeline: list[TimelineEventResponse]
    summary: dict
    narrative: str


@router.get("/timeline/{incident_id}", response_model=PreventionTimelineResponse)
async def get_prevention_timeline(
    incident_id: str,
    tenant_id: str = Depends(get_tenant_id),
) -> PreventionTimelineResponse:
    """
    Get the prevention timeline for an incident.

    This is the Gate 3 UI - shows the learning loop in action:
    1. Original incident detected
    2. Pattern identified
    3. Policy born from failure
    4. (later) Similar incident detected
    5. Policy PREVENTED recurrence

    Viewing this timeline with a prevention event proves Gate 3.
    """
    timeline_events = []

    async with get_async_session_context() as session:
        # Get combined timeline data via registry dispatch
        registry = get_operation_registry()
        result = await registry.execute(
            "m25.read_timeline",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={"incident_id": incident_id},
            ),
        )

        if not result.success:
            if result.error_code == "NOT_FOUND":
                raise HTTPException(status_code=404, detail="Incident not found")
            if result.error_code == "FORBIDDEN":
                raise HTTPException(status_code=403, detail="Access denied")
            raise HTTPException(status_code=500, detail=result.error or "Failed to read timeline")

        data = result.data
        incident = data["incident"]

        # Add incident created event
        timeline_events.append(
            TimelineEventResponse(
                type="incident_created",
                timestamp=incident["created_at"]
                if incident.get("created_at")
                else datetime.now(timezone.utc).isoformat(),
                icon="incident",
                headline="Incident detected",
                description=incident.get("title") or "Incident occurred",
                details={"severity": incident.get("severity"), "id": incident["id"]},
            )
        )

        # Process loop events from handler response
        for event in data.get("events", []):
            if event.get("stage") == "pattern_matched":
                timeline_events.append(
                    TimelineEventResponse(
                        type="pattern_matched",
                        timestamp=event.get("created_at") or "",
                        icon="search",
                        headline="Pattern identified",
                        description=f"Matched with confidence: {event.get('confidence_band') or 'unknown'}",
                        details=event.get("details") if isinstance(event.get("details"), dict) else {},
                    )
                )
            elif event.get("stage") == "policy_generated":
                timeline_events.append(
                    TimelineEventResponse(
                        type="policy_born",
                        timestamp=event.get("created_at") or "",
                        icon="policy",
                        headline="Policy born from failure",
                        description="New policy created to prevent recurrence",
                        details=event.get("details") if isinstance(event.get("details"), dict) else {},
                    )
                )

        # Process prevention records from handler response
        for prev in data.get("preventions", []):
            confidence = prev.get("signature_match_confidence", 0)
            timeline_events.append(
                TimelineEventResponse(
                    type="prevention",
                    timestamp=prev.get("created_at") or "",
                    icon="shield",
                    headline="PREVENTION: Similar incident BLOCKED",
                    description=f"Policy prevented recurrence with {confidence:.0%} confidence",
                    details={
                        "blocked_incident": prev.get("blocked_incident_id"),
                        "policy": prev.get("policy_id"),
                        "pattern": prev.get("pattern_id"),
                    },
                    is_milestone=True,
                )
            )

        # Process regret events from handler response
        for regret in data.get("regrets", []):
            timeline_events.append(
                TimelineEventResponse(
                    type="regret",
                    timestamp=regret.get("created_at") or "",
                    icon="warning",
                    headline="Policy caused harm (regret)",
                    description=regret.get("description") or f"Regret type: {regret.get('regret_type')}",
                    details={
                        "regret_type": regret.get("regret_type"),
                        "severity": regret.get("severity"),
                        "auto_rolled_back": regret.get("was_auto_rolled_back"),
                    },
                )
            )

            if regret.get("was_auto_rolled_back"):
                timeline_events.append(
                    TimelineEventResponse(
                        type="rollback",
                        timestamp=regret.get("created_at") or "",
                        icon="undo",
                        headline="Policy auto-demoted",
                        description="System self-corrected by demoting harmful policy",
                        details={"policy": regret.get("policy_id")},
                        is_milestone=True,
                    )
                )

    # Sort by timestamp
    sorted_events = sorted(timeline_events, key=lambda e: e.timestamp)

    # Build summary
    has_prevention = any(e.type == "prevention" for e in sorted_events)
    has_rollback = any(e.type == "rollback" for e in sorted_events)

    # Generate narrative
    if has_prevention and has_rollback:
        narrative = (
            "This incident shows the full learning loop: "
            "failure -> policy -> prevention -> feedback. "
            "The system learned, protected, and self-corrected."
        )
    elif has_prevention:
        narrative = "This incident proves learning: a policy born from failure successfully prevented a recurrence."
    elif has_rollback:
        narrative = "This incident shows self-correction: a policy that caused harm was automatically demoted."
    else:
        narrative = "This incident is part of the feedback loop."

    return PreventionTimelineResponse(
        incident_id=incident_id,
        tenant_id=tenant_id,
        timeline=sorted_events,
        summary={
            "event_count": len(sorted_events),
            "has_prevention": has_prevention,
            "has_rollback": has_rollback,
            "is_learning_proof": has_prevention,
        },
        narrative=narrative,
    )
