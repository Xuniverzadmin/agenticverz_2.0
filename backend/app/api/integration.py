# Layer: L2 — Product APIs
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Loop status, checkpoints, graduation, and prevention timeline
# Authority: WRITE checkpoint resolutions, graduation records (API self-authority)
# Callers: Ops Console, Customer Console, SDK
# Reference: M25 Integration System

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


# Simple tenant/user helpers for integration endpoints
def get_tenant_id(tenant_id: str = Query(..., description="Tenant ID")) -> str:
    """Get tenant ID from query parameter."""
    return tenant_id


def get_current_user(user_id: Optional[str] = Query(None, description="User ID")) -> Optional[dict]:
    """Get current user from query parameter (optional)."""
    if user_id:
        return {"id": user_id}
    return None


from app.integrations.events import (
    LoopStage,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integration", tags=["integration"])


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
    from sqlalchemy import text

    from app.db import get_async_session

    async with get_async_session() as session:
        result = await session.execute(
            text(
                """
                SELECT stage, details, failure_state, confidence_band, created_at
                FROM loop_events
                WHERE incident_id = :incident_id
                ORDER BY created_at ASC
            """
            ),
            {"incident_id": incident_id},
        )
        events = result.fetchall()

    stages = []
    for event in events:
        stages.append(
            StageDetail(
                stage=event.stage,
                status="failed" if event.failure_state else "completed",
                timestamp=event.created_at,
                details=event.details if isinstance(event.details, dict) else {},
                failure_state=event.failure_state,
                confidence_band=event.confidence_band,
            )
        )

    return stages


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
        result = await dispatcher.retry_failed_stage(incident_id, stage, tenant_id)
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
        return {
            "status": "reverted",
            "incident_id": incident_id,
            "reverted_by": user_id,
            "reason": request.reason,
        }
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
    from sqlalchemy import text

    from app.db import get_async_session

    async with get_async_session() as session:
        result = await session.execute(
            text(
                """
                SELECT * FROM human_checkpoints
                WHERE id = :id AND tenant_id = :tenant_id
            """
            ),
            {"id": checkpoint_id, "tenant_id": tenant_id},
        )
        row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Checkpoint not found")

    import json

    options = row.options if isinstance(row.options, list) else json.loads(row.options or "[]")

    return CheckpointResponse(
        checkpoint_id=row.id,
        checkpoint_type=row.checkpoint_type,
        incident_id=row.incident_id,
        stage=row.stage,
        target_id=row.target_id,
        description=row.description or "",
        options=options,
        created_at=row.created_at,
        is_pending=row.resolved_at is None,
        resolved_at=row.resolved_at,
        resolved_by=row.resolved_by,
        resolution=row.resolution,
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

        return {
            "status": "resolved",
            "checkpoint_id": checkpoint_id,
            "resolution": request.resolution,
            "resolved_by": user_id,
            "loop_resumed": result is not None,
        }
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
    from sqlalchemy import text

    from app.db import get_async_session

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    async with get_async_session() as session:
        # Get loop counts
        loops_result = await session.execute(
            text(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE is_complete) as complete,
                    AVG(EXTRACT(EPOCH FROM (completed_at - started_at)) * 1000)
                        FILTER (WHERE completed_at IS NOT NULL) as avg_time_ms
                FROM loop_traces
                WHERE tenant_id = :tenant_id
                AND started_at >= :cutoff
            """
            ),
            {"tenant_id": tenant_id, "cutoff": cutoff},
        )
        loops = loops_result.fetchone()

        # Get pattern match stats
        patterns_result = await session.execute(
            text(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE confidence_band = 'strong_match') as strong,
                    COUNT(*) FILTER (WHERE confidence_band = 'weak_match') as weak,
                    COUNT(*) FILTER (WHERE confidence_band = 'novel') as novel
                FROM loop_events
                WHERE tenant_id = :tenant_id
                AND stage = 'pattern_matched'
                AND created_at >= :cutoff
            """
            ),
            {"tenant_id": tenant_id, "cutoff": cutoff},
        )
        patterns = patterns_result.fetchone()

        # Get recovery stats
        recovery_result = await session.execute(
            text(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'applied') as applied,
                    COUNT(*) FILTER (WHERE status = 'rejected') as rejected
                FROM recovery_candidates
                WHERE source_incident_id IN (
                    SELECT incident_id FROM loop_traces
                    WHERE tenant_id = :tenant_id
                )
                AND created_at >= :cutoff
            """
            ),
            {"tenant_id": tenant_id, "cutoff": cutoff},
        )
        recoveries = recovery_result.fetchone()

        # Get policy stats
        policy_result = await session.execute(
            text(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE mode = 'shadow') as shadow,
                    COUNT(*) FILTER (WHERE mode = 'active') as active
                FROM policy_rules
                WHERE source_type = 'recovery'
                AND created_at >= :cutoff
            """
            ),
            {"cutoff": cutoff},
        )
        policies = policy_result.fetchone()

        # Get routing adjustment stats
        routing_result = await session.execute(
            text(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE was_rolled_back) as rolled_back
                FROM routing_policy_adjustments
                WHERE created_at >= :cutoff
            """
            ),
            {"cutoff": cutoff},
        )
        routing = routing_result.fetchone()

        # Get checkpoint stats
        checkpoint_result = await session.execute(
            text(
                """
                SELECT
                    COUNT(*) FILTER (WHERE resolved_at IS NULL) as pending,
                    COUNT(*) FILTER (WHERE resolved_at IS NOT NULL) as resolved
                FROM human_checkpoints
                WHERE tenant_id = :tenant_id
                AND created_at >= :cutoff
            """
            ),
            {"tenant_id": tenant_id, "cutoff": cutoff},
        )
        checkpoints = checkpoint_result.fetchone()

    assert loops is not None
    total = loops.total or 0
    complete = loops.complete or 0

    return IntegrationStatsResponse(
        total_incidents=total,
        patterns_matched=(patterns.total or 0) - (patterns.novel or 0),
        patterns_created=patterns.novel or 0,
        strong_matches=patterns.strong or 0,
        weak_matches=patterns.weak or 0,
        novel_patterns=patterns.novel or 0,
        recoveries_suggested=recoveries.total or 0,
        recoveries_applied=recoveries.applied or 0,
        recoveries_rejected=recoveries.rejected or 0,
        policies_generated=policies.total or 0,
        policies_in_shadow=policies.shadow or 0,
        policies_active=policies.active or 0,
        routing_adjustments=routing.total or 0,
        adjustments_rolled_back=routing.rolled_back or 0,
        avg_loop_completion_time_ms=loops.avg_time_ms or 0,
        loop_completion_rate=complete / total if total > 0 else 0,
        checkpoints_pending=checkpoints.pending or 0,
        checkpoints_resolved=checkpoints.resolved or 0,
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

    return {
        "incident_id": incident_id,
        "is_complete": loop_status.is_complete,
        "narrative": display.get("narrative", {}),
        "stages": display.get("stages", []),
    }


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
    from sqlalchemy import text

    from app.db import get_async_session

    # Import graduation engine
    from app.integrations.graduation_engine import (
        CapabilityGates,
        GraduationEngine,
        GraduationEvidence,
    )

    async with get_async_session() as session:
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

        # Get simulation state (separate from real)
        sim_result = await session.execute(
            text(
                """
                SELECT
                    EXISTS(SELECT 1 FROM prevention_records WHERE is_simulated = true) as sim_gate1,
                    EXISTS(SELECT 1 FROM regret_events WHERE is_simulated = true) as sim_gate2,
                    EXISTS(SELECT 1 FROM timeline_views WHERE is_simulated = true) as sim_gate3
            """
            )
        )
        sim_row = sim_result.fetchone()

        simulation = SimulationStatus(
            is_demo_mode=(sim_row.sim_gate1 or sim_row.sim_gate2 or sim_row.sim_gate3) if sim_row else False,
            simulated_gates={
                "gate1": sim_row.sim_gate1 if sim_row else False,
                "gate2": sim_row.sim_gate2 if sim_row else False,
                "gate3": sim_row.sim_gate3 if sim_row else False,
            },
            warning="SIMULATION DATA EXISTS - Real graduation excludes simulated records"
            if (sim_row and (sim_row.sim_gate1 or sim_row.sim_gate2 or sim_row.sim_gate3))
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
    from sqlalchemy import text

    from app.db import get_async_session

    # Use sim_ prefix to make simulated records obvious
    record_id = f"prev_sim_{uuid.uuid4().hex[:12]}"
    blocked_id = f"inc_sim_prevented_{uuid.uuid4().hex[:8]}"

    async with get_async_session() as session:
        # Insert prevention record WITH is_simulated=true
        # This record is EXCLUDED from real graduation computation
        await session.execute(
            text(
                """
                INSERT INTO prevention_records (
                    id, policy_id, pattern_id, original_incident_id,
                    blocked_incident_id, tenant_id, outcome,
                    signature_match_confidence, policy_age_seconds,
                    is_simulated, created_at
                ) VALUES (
                    :id, :policy_id, :pattern_id, :original_incident_id,
                    :blocked_incident_id, :tenant_id, 'prevented',
                    :confidence, 3600,
                    true, NOW()
                )
            """
            ),
            {
                "id": record_id,
                "policy_id": request.policy_id,
                "pattern_id": request.pattern_id,
                "original_incident_id": request.original_incident_id,
                "blocked_incident_id": blocked_id,
                "tenant_id": tenant_id,
                "confidence": request.confidence,
            },
        )

        # DO NOT update m25_graduation_status directly!
        # Graduation is DERIVED from real evidence only.
        # The GraduationEngine will exclude is_simulated=true records.

        await session.commit()

    return {
        "status": "simulated",
        "prevention_id": record_id,
        "blocked_incident_id": blocked_id,
        "is_simulated": True,
        "counts_toward_graduation": False,
        "warning": "SIMULATION ONLY: This record is marked is_simulated=true and does NOT count toward real M25 graduation. Real graduation requires real prevention evidence.",
        "message": "Prevention event simulated for demo purposes.",
    }


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
    from sqlalchemy import text

    from app.db import get_async_session

    # Use sim_ prefix to make simulated records obvious
    regret_id = f"regret_sim_{uuid.uuid4().hex[:12]}"

    async with get_async_session() as session:
        # Insert regret event WITH is_simulated=true
        # This record is EXCLUDED from real graduation computation
        await session.execute(
            text(
                """
                INSERT INTO regret_events (
                    id, policy_id, tenant_id, regret_type,
                    description, severity, affected_calls, affected_users,
                    was_auto_rolled_back, is_simulated, created_at
                ) VALUES (
                    :id, :policy_id, :tenant_id, :regret_type,
                    :description, :severity, 50, 10,
                    true, true, NOW()
                )
            """
            ),
            {
                "id": regret_id,
                "policy_id": request.policy_id,
                "tenant_id": tenant_id,
                "regret_type": request.regret_type,
                "description": request.description,
                "severity": request.severity,
            },
        )

        # Insert or update policy regret summary for demo purposes
        # Note: This is simulated demotion, not real
        await session.execute(
            text(
                """
                INSERT INTO policy_regret_summary (
                    policy_id, regret_score, regret_event_count,
                    demoted_at, demoted_reason, last_updated
                ) VALUES (
                    :policy_id, :score, 1,
                    NOW(), 'SIMULATED demotion - does not count toward graduation',
                    NOW()
                )
                ON CONFLICT (policy_id) DO UPDATE SET
                    regret_score = policy_regret_summary.regret_score + :score,
                    regret_event_count = policy_regret_summary.regret_event_count + 1,
                    demoted_at = NOW(),
                    demoted_reason = 'SIMULATED demotion - does not count toward graduation',
                    last_updated = NOW()
            """
            ),
            {
                "policy_id": request.policy_id,
                "score": request.severity * 0.5,
            },
        )

        # DO NOT update m25_graduation_status directly!
        # Graduation is DERIVED from real evidence only.
        # The GraduationEngine will exclude is_simulated=true records.

        await session.commit()

    return {
        "status": "simulated",
        "regret_id": regret_id,
        "policy_demoted": True,
        "is_simulated": True,
        "counts_toward_graduation": False,
        "warning": "SIMULATION ONLY: This record is marked is_simulated=true and does NOT count toward real M25 graduation. Real graduation requires real regret/demotion evidence.",
        "message": "Regret event simulated for demo purposes.",
    }


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
    from sqlalchemy import text

    from app.db import get_async_session

    view_id = f"tv_sim_{uuid.uuid4().hex[:12]}"

    async with get_async_session() as session:
        # Insert into timeline_views WITH is_simulated=true
        # This record is EXCLUDED from real graduation computation
        await session.execute(
            text(
                """
                INSERT INTO timeline_views (
                    id, incident_id, tenant_id, user_id,
                    has_prevention, has_rollback,
                    is_simulated, session_id, viewed_at
                ) VALUES (
                    :id, :incident_id, :tenant_id, 'demo_user',
                    true, false,
                    true, :session_id, NOW()
                )
            """
            ),
            {
                "id": view_id,
                "incident_id": incident_id,
                "tenant_id": tenant_id,
                "session_id": f"sim_session_{uuid.uuid4().hex[:8]}",
            },
        )

        # DO NOT update m25_graduation_status directly!
        # Graduation is DERIVED from real evidence only.
        # The GraduationEngine will exclude is_simulated=true records.

        await session.commit()

    return {
        "status": "simulated",
        "view_id": view_id,
        "incident_id": incident_id,
        "is_simulated": True,
        "counts_toward_graduation": False,
        "warning": "SIMULATION ONLY: This view is marked is_simulated=true and does NOT count toward real M25 graduation. Real graduation requires real timeline views from operators.",
        "message": "Timeline view simulated for demo purposes.",
    }


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
    from sqlalchemy import text

    from app.db import get_async_session

    view_id = f"tv_{uuid.uuid4().hex[:12]}"
    user_id = user.get("sub", "unknown")
    session_id = f"session_{uuid.uuid4().hex[:8]}"

    async with get_async_session() as session:
        # Insert REAL timeline view (is_simulated=false)
        # This COUNTS toward graduation
        await session.execute(
            text(
                """
                INSERT INTO timeline_views (
                    id, incident_id, tenant_id, user_id,
                    has_prevention, has_rollback,
                    is_simulated, session_id, viewed_at
                ) VALUES (
                    :id, :incident_id, :tenant_id, :user_id,
                    :has_prevention, :has_rollback,
                    false, :session_id, NOW()
                )
            """
            ),
            {
                "id": view_id,
                "incident_id": incident_id,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "has_prevention": has_prevention,
                "has_rollback": has_rollback,
                "session_id": session_id,
            },
        )

        await session.commit()

    return {
        "status": "recorded",
        "view_id": view_id,
        "incident_id": incident_id,
        "is_simulated": False,
        "counts_toward_graduation": True,
        "message": "Timeline view recorded. This contributes to Gate 3 (Console Timeline) graduation.",
    }


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

    from sqlalchemy import text

    from app.db import get_async_session
    from app.integrations.graduation_engine import (
        GraduationEngine,
        GraduationEvidence,
    )

    async with get_async_session() as session:
        engine = GraduationEngine()

        try:
            evidence = await GraduationEvidence.fetch_from_database(session)
            status = engine.compute(evidence)
        except Exception as e:
            logger.warning(f"Re-evaluation failed: {e}")
            return {
                "status": "error",
                "message": f"Failed to compute graduation: {str(e)}",
            }

        # Store in graduation_history for audit trail
        await session.execute(
            text(
                """
                INSERT INTO graduation_history (
                    level, gates_json, computed_at, is_degraded,
                    degraded_from, degradation_reason, evidence_snapshot
                ) VALUES (
                    :level, :gates_json, NOW(), :is_degraded,
                    :degraded_from, :degradation_reason, :evidence_snapshot
                )
            """
            ),
            {
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
            },
        )

        # Update m25_graduation_status with derived values
        # (This table still exists for backward compat, but values are DERIVED)
        await session.execute(
            text(
                """
                UPDATE m25_graduation_status
                SET is_derived = true,
                    last_evidence_eval = NOW(),
                    status_label = :status_label,
                    is_graduated = :is_graduated,
                    gate1_passed = :gate1_passed,
                    gate2_passed = :gate2_passed,
                    gate3_passed = :gate3_passed,
                    last_checked = NOW()
                WHERE id = 1
            """
            ),
            {
                "status_label": status.status_label,
                "is_graduated": status.is_graduated,
                "gate1_passed": status.gates.get("prevention", type("", (), {"passed": False})).passed,
                "gate2_passed": status.gates.get("rollback", type("", (), {"passed": False})).passed,
                "gate3_passed": status.gates.get("timeline", type("", (), {"passed": False})).passed,
            },
        )

        await session.commit()

    return {
        "status": "re-evaluated",
        "level": status.level.value,
        "status_label": status.status_label,
        "is_graduated": status.is_graduated,
        "is_degraded": status.is_degraded,
        "gates_passed": sum(1 for g in status.gates.values() if g.passed),
        "message": "Graduation status re-computed from evidence.",
    }


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
    from sqlalchemy import text

    from app.db import get_async_session

    timeline_events = []

    async with get_async_session() as session:
        # Get incident info
        incident_result = await session.execute(
            text(
                """
                SELECT id, tenant_id, title, severity, created_at
                FROM incidents
                WHERE id = :incident_id
            """
            ),
            {"incident_id": incident_id},
        )
        incident = incident_result.fetchone()

        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")

        if incident.tenant_id != tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Add incident created event
        timeline_events.append(
            TimelineEventResponse(
                type="incident_created",
                timestamp=incident.created_at.isoformat()
                if incident.created_at
                else datetime.now(timezone.utc).isoformat(),
                icon="🚨",
                headline="Incident detected",
                description=incident.title or "Incident occurred",
                details={"severity": incident.severity, "id": incident.id},
            )
        )

        # Get loop events for this incident
        events_result = await session.execute(
            text(
                """
                SELECT stage, details, confidence_band, created_at
                FROM loop_events
                WHERE incident_id = :incident_id
                ORDER BY created_at ASC
            """
            ),
            {"incident_id": incident_id},
        )
        loop_events = events_result.fetchall()

        for event in loop_events:
            if event.stage == "pattern_matched":
                timeline_events.append(
                    TimelineEventResponse(
                        type="pattern_matched",
                        timestamp=event.created_at.isoformat(),
                        icon="🔍",
                        headline="Pattern identified",
                        description=f"Matched with confidence: {event.confidence_band or 'unknown'}",
                        details=event.details if isinstance(event.details, dict) else {},
                    )
                )
            elif event.stage == "policy_generated":
                timeline_events.append(
                    TimelineEventResponse(
                        type="policy_born",
                        timestamp=event.created_at.isoformat(),
                        icon="📋",
                        headline="Policy born from failure",
                        description="New policy created to prevent recurrence",
                        details=event.details if isinstance(event.details, dict) else {},
                    )
                )

        # Get prevention records where this incident was the ORIGINAL
        prevention_result = await session.execute(
            text(
                """
                SELECT id, blocked_incident_id, policy_id, pattern_id,
                       signature_match_confidence, created_at
                FROM prevention_records
                WHERE original_incident_id = :incident_id
                ORDER BY created_at ASC
            """
            ),
            {"incident_id": incident_id},
        )
        preventions = prevention_result.fetchall()

        for prev in preventions:
            timeline_events.append(
                TimelineEventResponse(
                    type="prevention",
                    timestamp=prev.created_at.isoformat(),
                    icon="🛡️",
                    headline="PREVENTION: Similar incident BLOCKED",
                    description=f"Policy prevented recurrence with {prev.signature_match_confidence:.0%} confidence",
                    details={
                        "blocked_incident": prev.blocked_incident_id,
                        "policy": prev.policy_id,
                        "pattern": prev.pattern_id,
                    },
                    is_milestone=True,
                )
            )

        # Get regret events for policies born from this incident
        regret_result = await session.execute(
            text(
                """
                SELECT re.id, re.policy_id, re.regret_type, re.description,
                       re.severity, re.was_auto_rolled_back, re.created_at
                FROM regret_events re
                WHERE re.policy_id IN (
                    SELECT DISTINCT details->>'policy_id'
                    FROM loop_events
                    WHERE incident_id = :incident_id
                    AND stage = 'policy_generated'
                )
                ORDER BY re.created_at ASC
            """
            ),
            {"incident_id": incident_id},
        )
        regrets = regret_result.fetchall()

        for regret in regrets:
            timeline_events.append(
                TimelineEventResponse(
                    type="regret",
                    timestamp=regret.created_at.isoformat(),
                    icon="⚠️",
                    headline="Policy caused harm (regret)",
                    description=regret.description or f"Regret type: {regret.regret_type}",
                    details={
                        "regret_type": regret.regret_type,
                        "severity": regret.severity,
                        "auto_rolled_back": regret.was_auto_rolled_back,
                    },
                )
            )

            if regret.was_auto_rolled_back:
                timeline_events.append(
                    TimelineEventResponse(
                        type="rollback",
                        timestamp=regret.created_at.isoformat(),
                        icon="↩️",
                        headline="Policy auto-demoted",
                        description="System self-corrected by demoting harmful policy",
                        details={"policy": regret.policy_id},
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
            "failure → policy → prevention → feedback. "
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
