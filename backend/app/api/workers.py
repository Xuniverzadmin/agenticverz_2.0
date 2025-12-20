# Business Builder Worker API
# Exposes the Business Builder Worker v0.2 as hostable API endpoints
"""
API endpoints for Business Builder Worker.

Endpoints:
- POST /api/v1/workers/business-builder/run - Execute the worker
- POST /api/v1/workers/business-builder/replay - Replay a previous execution
- GET /api/v1/workers/business-builder/runs/{run_id} - Get run details
- GET /api/v1/workers/business-builder/runs - List recent runs
- POST /api/v1/workers/business-builder/validate-brand - Validate brand schema
- GET /api/v1/workers/business-builder/stream/{run_id} - SSE stream for real-time updates

All endpoints require authentication via API key or Bearer token.
"""

import asyncio
import json
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..auth import verify_api_key

logger = logging.getLogger("nova.api.workers")

router = APIRouter(prefix="/api/v1/workers/business-builder", tags=["Workers"])


# =============================================================================
# Request/Response Schemas
# =============================================================================


class ToneRuleRequest(BaseModel):
    """Tone rule for brand."""

    primary: str = Field(default="professional", description="Primary tone")
    avoid: List[str] = Field(default_factory=list, description="Tones to avoid")
    examples_good: List[str] = Field(default_factory=list, description="Good examples")
    examples_bad: List[str] = Field(default_factory=list, description="Bad examples")


class ForbiddenClaimRequest(BaseModel):
    """Forbidden claim definition."""

    pattern: str = Field(..., description="Pattern to match")
    reason: str = Field(default="Policy violation", description="Reason for forbidding")
    severity: str = Field(default="error", description="error or warning")


class VisualIdentityRequest(BaseModel):
    """Visual identity for brand."""

    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    font_heading: str = "Inter"
    font_body: str = "Inter"
    logo_placement: str = "top-left"


class BrandRequest(BaseModel):
    """Brand schema for worker execution."""

    company_name: str = Field(..., min_length=1, description="Company name")
    tagline: Optional[str] = None
    mission: str = Field(..., min_length=10, description="Mission statement")
    vision: Optional[str] = None
    value_proposition: str = Field(..., min_length=20, description="Value proposition")
    target_audience: List[str] = Field(default_factory=lambda: ["b2b_smb"])
    audience_pain_points: List[str] = Field(default_factory=list)
    tone: ToneRuleRequest = Field(default_factory=ToneRuleRequest)
    voice_attributes: List[str] = Field(default_factory=lambda: ["clear", "helpful"])
    forbidden_claims: List[ForbiddenClaimRequest] = Field(default_factory=list)
    required_disclosures: List[str] = Field(default_factory=list)
    visual: VisualIdentityRequest = Field(default_factory=VisualIdentityRequest)
    budget_tokens: Optional[int] = Field(default=None, ge=1000, le=1000000)


class WorkerRunRequest(BaseModel):
    """Request to run the Business Builder Worker."""

    task: str = Field(..., min_length=5, description="Business/product idea to build launch package for")
    brand: Optional[BrandRequest] = Field(
        default=None, description="Brand constraints (optional, creates minimal brand if not provided)"
    )
    budget: Optional[int] = Field(default=None, ge=1000, le=100000, description="Token budget for execution")
    strict_mode: bool = Field(default=False, description="If true, any policy violation stops execution")
    depth: str = Field(default="auto", description="Research depth: auto, shallow, deep")
    async_mode: bool = Field(default=False, description="If true, returns immediately with run_id to poll")


class WorkerRunResponse(BaseModel):
    """Response from worker execution."""

    run_id: str
    success: bool
    status: str  # queued, running, completed, failed
    artifacts: Optional[Dict[str, Any]] = None
    replay_token: Optional[Dict[str, Any]] = None
    cost_report: Optional[Dict[str, Any]] = None
    policy_violations: List[Dict[str, Any]] = Field(default_factory=list)
    recovery_log: List[Dict[str, Any]] = Field(default_factory=list)
    drift_metrics: Dict[str, float] = Field(default_factory=dict)
    execution_trace: List[Dict[str, Any]] = Field(default_factory=list)
    routing_decisions: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None
    total_tokens_used: int = 0
    total_latency_ms: float = 0.0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ReplayRequest(BaseModel):
    """Request to replay a previous execution."""

    replay_token: Dict[str, Any] = Field(..., description="Replay token from previous execution")


class BrandValidationResponse(BaseModel):
    """Response from brand validation."""

    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    policy_rules_generated: int = 0
    drift_anchors_count: int = 0


class RunListItem(BaseModel):
    """Summary item for run listing."""

    run_id: str
    task: str
    status: str
    success: Optional[bool] = None
    created_at: str
    total_latency_ms: Optional[float] = None


class RunListResponse(BaseModel):
    """Response for listing runs."""

    runs: List[RunListItem]
    total: int


# =============================================================================
# In-Memory Run Storage (would use DB in production)
# =============================================================================

# Simple in-memory storage for runs
# In production, this would be persisted to PostgreSQL
_runs_store: Dict[str, Dict[str, Any]] = {}


def _store_run(run_id: str, data: Dict[str, Any]) -> None:
    """Store a run in memory."""
    _runs_store[run_id] = data


def _get_run(run_id: str) -> Optional[Dict[str, Any]]:
    """Get a run from memory."""
    return _runs_store.get(run_id)


def _list_runs(limit: int = 20) -> List[Dict[str, Any]]:
    """List recent runs."""
    runs = list(_runs_store.values())
    runs.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return runs[:limit]


# =============================================================================
# SSE Event Bus for Real-Time Streaming
# =============================================================================


class WorkerEventBus:
    """
    Event bus for real-time worker execution streaming.

    Supports multiple subscribers per run_id.
    Events are JSON-serialized and sent as SSE.
    """

    def __init__(self):
        self._subscribers: Dict[str, List[asyncio.Queue]] = defaultdict(list)
        self._run_events: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def subscribe(self, run_id: str) -> asyncio.Queue:
        """Subscribe to events for a run."""
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[run_id].append(queue)
        logger.debug(f"SSE subscriber added for run {run_id}")
        return queue

    def unsubscribe(self, run_id: str, queue: asyncio.Queue) -> None:
        """Unsubscribe from events."""
        if run_id in self._subscribers:
            try:
                self._subscribers[run_id].remove(queue)
                logger.debug(f"SSE subscriber removed for run {run_id}")
            except ValueError:
                pass

    async def emit(self, run_id: str, event_type: str, data: Dict[str, Any]) -> None:
        """Emit an event to all subscribers."""
        event = {
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id,
            "data": data,
        }

        # Store event history
        self._run_events[run_id].append(event)

        # Broadcast to subscribers
        for queue in self._subscribers.get(run_id, []):
            await queue.put(event)

        logger.debug(f"SSE event emitted: {event_type} for run {run_id}")

    def get_history(self, run_id: str) -> List[Dict[str, Any]]:
        """Get event history for a run."""
        return self._run_events.get(run_id, [])

    def cleanup(self, run_id: str) -> None:
        """Clean up resources for a completed run."""
        if run_id in self._subscribers:
            del self._subscribers[run_id]
        # Keep event history for replay


# Global event bus instance
_event_bus = WorkerEventBus()


def get_event_bus() -> WorkerEventBus:
    """Get the global event bus instance."""
    return _event_bus


# SSE Event Types
class EventType:
    """Constants for SSE event types."""

    RUN_STARTED = "run_started"
    STAGE_STARTED = "stage_started"
    STAGE_COMPLETED = "stage_completed"
    STAGE_FAILED = "stage_failed"
    LOG = "log"
    ROUTING_DECISION = "routing_decision"
    POLICY_CHECK = "policy_check"
    POLICY_VIOLATION = "policy_violation"
    DRIFT_DETECTED = "drift_detected"
    FAILURE_DETECTED = "failure_detected"
    RECOVERY_STARTED = "recovery_started"
    RECOVERY_COMPLETED = "recovery_completed"
    ARTIFACT_CREATED = "artifact_created"
    RUN_COMPLETED = "run_completed"
    RUN_FAILED = "run_failed"


# =============================================================================
# Helper Functions
# =============================================================================


def _brand_request_to_schema(brand_req: BrandRequest):
    """Convert API request to BrandSchema."""
    from ..workers.business_builder.schemas.brand import (
        AudienceSegment,
        BrandSchema,
        ForbiddenClaim,
        ToneLevel,
        ToneRule,
        VisualIdentity,
    )

    # Convert tone
    tone = ToneRule(
        primary=ToneLevel(brand_req.tone.primary),
        avoid=[ToneLevel(t) for t in brand_req.tone.avoid if t in [e.value for e in ToneLevel]],
        examples_good=brand_req.tone.examples_good,
        examples_bad=brand_req.tone.examples_bad,
    )

    # Convert forbidden claims
    forbidden = [
        ForbiddenClaim(
            pattern=fc.pattern,
            reason=fc.reason,
            severity=fc.severity,
        )
        for fc in brand_req.forbidden_claims
    ]

    # Convert visual
    visual = VisualIdentity(
        primary_color=brand_req.visual.primary_color,
        secondary_color=brand_req.visual.secondary_color,
        font_heading=brand_req.visual.font_heading,
        font_body=brand_req.visual.font_body,
        logo_placement=brand_req.visual.logo_placement,
    )

    # Convert audience
    audience = []
    for a in brand_req.target_audience:
        try:
            audience.append(AudienceSegment(a))
        except ValueError:
            pass
    if not audience:
        audience = [AudienceSegment.B2B_SMB]

    return BrandSchema(
        company_name=brand_req.company_name,
        tagline=brand_req.tagline,
        mission=brand_req.mission,
        vision=brand_req.vision,
        value_proposition=brand_req.value_proposition,
        target_audience=audience,
        audience_pain_points=brand_req.audience_pain_points,
        tone=tone,
        voice_attributes=brand_req.voice_attributes,
        forbidden_claims=forbidden,
        required_disclosures=brand_req.required_disclosures,
        visual=visual,
        budget_tokens=brand_req.budget_tokens,
    )


async def _execute_worker_async(run_id: str, request: WorkerRunRequest) -> None:
    """Execute worker in background and update run store."""
    try:
        from ..workers.business_builder.worker import BusinessBuilderWorker

        _store_run(
            run_id,
            {
                "run_id": run_id,
                "task": request.task,
                "status": "running",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        worker = BusinessBuilderWorker()

        # Convert brand if provided
        brand = None
        if request.brand:
            brand = _brand_request_to_schema(request.brand)

        result = await worker.run(
            task=request.task,
            brand=brand,
            budget=request.budget,
            strict_mode=request.strict_mode,
            depth=request.depth,
        )

        # Update stored run
        _store_run(
            run_id,
            {
                "run_id": run_id,
                "task": request.task,
                "status": "completed" if result.success else "failed",
                "success": result.success,
                "artifacts": result.artifacts,
                "replay_token": result.replay_token,
                "cost_report": result.cost_report,
                "policy_violations": result.policy_violations,
                "recovery_log": result.recovery_log,
                "drift_metrics": result.drift_metrics,
                "execution_trace": result.execution_trace,
                "routing_decisions": result.routing_decisions,
                "error": result.error,
                "total_tokens_used": result.total_tokens_used,
                "total_latency_ms": result.total_latency_ms,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    except Exception as e:
        logger.exception(f"Worker execution failed for run {run_id}")
        _store_run(
            run_id,
            {
                "run_id": run_id,
                "task": request.task,
                "status": "failed",
                "success": False,
                "error": str(e),
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )


# =============================================================================
# API Endpoints
# =============================================================================


@router.post("/run", response_model=WorkerRunResponse, status_code=202)
async def run_worker(
    request: WorkerRunRequest,
    background_tasks: BackgroundTasks,
    _: str = Depends(verify_api_key),
):
    """
    Execute the Business Builder Worker.

    Takes a business idea and optionally brand constraints, produces a complete
    launch package including:
    - Market research
    - Brand strategy
    - Landing page copy
    - HTML/CSS assets
    - Replay token for deterministic reproduction

    Integrates with:
    - M4: Golden replay (deterministic execution)
    - M9: Failure catalog (pattern detection)
    - M10: Recovery engine (auto-recovery)
    - M15: SBA (strategy-bound agents)
    - M17: CARE (complexity-aware routing)
    - M18: Drift detection
    - M19/M20: Policy governance
    """
    run_id = str(uuid.uuid4())

    logger.info(
        "worker_run_requested",
        extra={
            "run_id": run_id,
            "task": request.task[:100],
            "has_brand": request.brand is not None,
            "async_mode": request.async_mode,
        },
    )

    if request.async_mode:
        # Queue for background execution
        _store_run(
            run_id,
            {
                "run_id": run_id,
                "task": request.task,
                "status": "queued",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        background_tasks.add_task(_execute_worker_async, run_id, request)

        return WorkerRunResponse(
            run_id=run_id,
            success=False,  # Not yet complete
            status="queued",
        )

    # Synchronous execution
    try:
        from ..workers.business_builder.worker import BusinessBuilderWorker

        worker = BusinessBuilderWorker()

        # Convert brand if provided
        brand = None
        if request.brand:
            brand = _brand_request_to_schema(request.brand)

        result = await worker.run(
            task=request.task,
            brand=brand,
            budget=request.budget,
            strict_mode=request.strict_mode,
            depth=request.depth,
        )

        response = WorkerRunResponse(
            run_id=run_id,
            success=result.success,
            status="completed" if result.success else "failed",
            artifacts=result.artifacts,
            replay_token=result.replay_token,
            cost_report=result.cost_report,
            policy_violations=result.policy_violations,
            recovery_log=result.recovery_log,
            drift_metrics=result.drift_metrics,
            execution_trace=result.execution_trace,
            routing_decisions=result.routing_decisions,
            error=result.error,
            total_tokens_used=result.total_tokens_used,
            total_latency_ms=result.total_latency_ms,
        )

        # Store the run
        _store_run(run_id, response.model_dump())

        return response

    except Exception as e:
        logger.exception("worker_run_failed")
        raise HTTPException(status_code=500, detail=f"Worker execution failed: {str(e)}")


@router.post("/replay", response_model=WorkerRunResponse, status_code=202)
async def replay_execution(
    request: ReplayRequest,
    _: str = Depends(verify_api_key),
):
    """
    Replay a previous execution using Golden Replay (M4).

    Deterministically reproduces the same outputs given the same replay token.
    """
    run_id = str(uuid.uuid4())

    try:
        from ..workers.business_builder.worker import replay

        result = await replay(request.replay_token)

        return WorkerRunResponse(
            run_id=run_id,
            success=result.success,
            status="completed" if result.success else "failed",
            artifacts=result.artifacts,
            replay_token=result.replay_token,
            cost_report=result.cost_report,
            policy_violations=result.policy_violations,
            recovery_log=result.recovery_log,
            drift_metrics=result.drift_metrics,
            execution_trace=result.execution_trace,
            error=result.error,
            total_tokens_used=result.total_tokens_used,
            total_latency_ms=result.total_latency_ms,
        )

    except Exception as e:
        logger.exception("replay_failed")
        raise HTTPException(status_code=500, detail=f"Replay failed: {str(e)}")


@router.get("/runs/{run_id}", response_model=WorkerRunResponse)
async def get_run(
    run_id: str,
    _: str = Depends(verify_api_key),
):
    """
    Get details of a worker run.

    Use this to poll for async run completion or inspect past runs.
    """
    run = _get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return WorkerRunResponse(**run)


@router.get("/runs", response_model=RunListResponse)
async def list_runs(
    limit: int = 20,
    _: str = Depends(verify_api_key),
):
    """
    List recent worker runs.

    Returns summary information for recent executions.
    """
    runs = _list_runs(limit)

    items = [
        RunListItem(
            run_id=r.get("run_id", ""),
            task=r.get("task", "")[:100],
            status=r.get("status", "unknown"),
            success=r.get("success"),
            created_at=r.get("created_at", ""),
            total_latency_ms=r.get("total_latency_ms"),
        )
        for r in runs
    ]

    return RunListResponse(runs=items, total=len(items))


@router.post("/validate-brand", response_model=BrandValidationResponse)
async def validate_brand(
    request: BrandRequest,
    _: str = Depends(verify_api_key),
):
    """
    Validate a brand schema without executing the worker.

    Checks:
    - Schema validity
    - Policy rules generation (M19)
    - Drift anchors extraction (M18)
    """
    errors = []
    warnings = []

    try:
        brand = _brand_request_to_schema(request)

        # Generate policy rules
        policy_rules = brand.to_policy_rules()

        # Get drift anchors
        drift_anchors = brand.get_drift_anchors()

        return BrandValidationResponse(
            valid=True,
            errors=[],
            warnings=warnings,
            policy_rules_generated=len(policy_rules),
            drift_anchors_count=len(drift_anchors),
        )

    except ValueError as e:
        errors.append(str(e))
        return BrandValidationResponse(
            valid=False,
            errors=errors,
            warnings=warnings,
        )

    except Exception as e:
        logger.exception("brand_validation_failed")
        errors.append(f"Validation error: {str(e)}")
        return BrandValidationResponse(
            valid=False,
            errors=errors,
            warnings=warnings,
        )


@router.get("/health")
async def worker_health():
    """
    Health check for Business Builder Worker.

    Returns status of all integrated moats.
    """
    moat_status = {}

    # Check M17 CARE
    try:
        from ..routing.care import get_care_engine

        get_care_engine()
        moat_status["m17_care"] = "available"
    except ImportError:
        moat_status["m17_care"] = "unavailable"

    # Check M20 Policy
    try:
        from ..policy.runtime.dag_executor import DAGExecutor

        DAGExecutor()
        moat_status["m20_policy"] = "available"
    except ImportError:
        moat_status["m20_policy"] = "unavailable"

    # Check M9 Failure Catalog (via RecoveryMatcher)
    try:
        from ..services.recovery_matcher import RecoveryMatcher

        RecoveryMatcher()
        moat_status["m9_failure_catalog"] = "available"
    except ImportError:
        moat_status["m9_failure_catalog"] = "unavailable"

    # Check M10 Recovery (via RecoveryMatcher)
    try:
        from ..services.recovery_matcher import RecoveryMatcher

        RecoveryMatcher()
        moat_status["m10_recovery"] = "available"
    except ImportError:
        moat_status["m10_recovery"] = "unavailable"

    return {
        "status": "healthy",
        "version": "0.3",  # v0.3: Worker is source of truth for events
        "moats": moat_status,
        "runs_in_memory": len(_runs_store),
    }


@router.delete("/runs/{run_id}")
async def delete_run(
    run_id: str,
    _: str = Depends(verify_api_key),
):
    """
    Delete a run from storage.

    Note: In production, this would require admin privileges.
    """
    if run_id in _runs_store:
        del _runs_store[run_id]
        return {"deleted": True, "run_id": run_id}

    raise HTTPException(status_code=404, detail="Run not found")


@router.get("/schema/brand")
async def get_brand_schema():
    """
    Get the JSON schema for BrandRequest.

    Useful for clients to understand the expected format.
    """
    return BrandRequest.model_json_schema()


@router.get("/schema/run")
async def get_run_schema():
    """
    Get the JSON schema for WorkerRunRequest.
    """
    return WorkerRunRequest.model_json_schema()


# =============================================================================
# SSE Streaming Endpoint
# =============================================================================


async def _sse_event_generator(run_id: str, queue: asyncio.Queue) -> AsyncGenerator[str, None]:
    """Generate SSE events from the queue."""
    try:
        # Send initial connection event
        yield f"event: connected\ndata: {json.dumps({'run_id': run_id})}\n\n"

        # Send event history first (for late joiners)
        history = _event_bus.get_history(run_id)
        for event in history:
            yield f"event: {event['type']}\ndata: {json.dumps(event)}\n\n"

        # Stream live events
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield f"event: {event['type']}\ndata: {json.dumps(event)}\n\n"

                # Check for terminal events
                if event["type"] in (EventType.RUN_COMPLETED, EventType.RUN_FAILED):
                    yield f"event: stream_end\ndata: {json.dumps({'run_id': run_id, 'reason': 'run_completed'})}\n\n"
                    break

            except asyncio.TimeoutError:
                # Send keepalive
                yield ": keepalive\n\n"

    except asyncio.CancelledError:
        logger.debug(f"SSE stream cancelled for run {run_id}")
    finally:
        _event_bus.unsubscribe(run_id, queue)


@router.get("/stream/{run_id}")
async def stream_run_events(
    run_id: str,
    request: Request,
):
    """
    Stream real-time events for a worker run via Server-Sent Events (SSE).

    Events include:
    - run_started: Worker execution began
    - stage_started/completed/failed: Stage lifecycle
    - log: Agent output logs
    - routing_decision: CARE routing decisions
    - policy_check/violation: M19 policy events
    - drift_detected: M18 drift detection
    - failure_detected: M9 failure pattern match
    - recovery_started/completed: M10 recovery actions
    - artifact_created: New artifact generated
    - run_completed/failed: Terminal state

    Usage (JavaScript):
    ```js
    const sse = new EventSource('/api/v1/workers/business-builder/stream/{run_id}');
    sse.onmessage = (event) => console.log(JSON.parse(event.data));
    sse.addEventListener('stage_completed', (event) => { ... });
    ```
    """
    # Check if run exists
    run = _get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Subscribe to events
    queue = _event_bus.subscribe(run_id)

    return StreamingResponse(
        _sse_event_generator(run_id, queue),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get("/events/{run_id}")
async def get_run_events(
    run_id: str,
    _: str = Depends(verify_api_key),
):
    """
    Get all events for a run (non-streaming).

    Useful for replaying events or debugging.
    """
    events = _event_bus.get_history(run_id)
    return {
        "run_id": run_id,
        "events": events,
        "count": len(events),
    }


# =============================================================================
# Enhanced Worker Execution with Event Emission
# =============================================================================


async def _execute_worker_with_events(run_id: str, request: WorkerRunRequest) -> None:
    """
    Execute worker with REAL event emission from worker itself.

    v0.3: Worker is source of truth. No simulation. API just relays events.
    """
    event_bus = get_event_bus()

    try:
        from ..workers.business_builder.worker import BusinessBuilderWorker

        _store_run(
            run_id,
            {
                "run_id": run_id,
                "task": request.task,
                "status": "running",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        # Convert brand if provided
        brand = None
        if request.brand:
            brand = _brand_request_to_schema(request.brand)

        # Create worker WITH event bus - worker emits its own events
        worker = BusinessBuilderWorker(event_bus=event_bus)

        # Run worker - all events are emitted by worker itself
        # NO SIMULATION - real execution with real events
        result = await worker.run(
            task=request.task,
            brand=brand,
            budget=request.budget,
            strict_mode=request.strict_mode,
            depth=request.depth,
            run_id=run_id,
        )

        # Store final result
        final_data = {
            "run_id": run_id,
            "task": request.task,
            "status": "completed" if result.success else "failed",
            "success": result.success,
            "artifacts": result.artifacts,
            "replay_token": result.replay_token,
            "cost_report": result.cost_report,
            "policy_violations": result.policy_violations,
            "recovery_log": result.recovery_log,
            "drift_metrics": result.drift_metrics,
            "execution_trace": result.execution_trace,
            "routing_decisions": result.routing_decisions,
            "error": result.error,
            "total_tokens_used": result.total_tokens_used,
            "total_latency_ms": result.total_latency_ms,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        _store_run(run_id, final_data)

        # Note: All events (stage_started, stage_completed, routing_decision,
        # policy_check, drift_detected, artifact_created, run_completed)
        # are now emitted by the worker itself - NOT simulated here.

    except Exception as e:
        logger.exception(f"Worker execution failed for run {run_id}")

        await event_bus.emit(
            run_id,
            EventType.RUN_FAILED,
            {
                "success": False,
                "error": str(e),
            },
        )

        _store_run(
            run_id,
            {
                "run_id": run_id,
                "task": request.task,
                "status": "failed",
                "success": False,
                "error": str(e),
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )


@router.post("/run-streaming", response_model=WorkerRunResponse, status_code=202)
async def run_worker_streaming(
    request: WorkerRunRequest,
    background_tasks: BackgroundTasks,
    _: str = Depends(verify_api_key),
):
    """
    Execute the Business Builder Worker with real-time event streaming.

    Returns immediately with run_id. Connect to /stream/{run_id} for real-time events.

    This is the preferred endpoint for UI-driven execution where you want to
    show progress, routing decisions, and artifacts building in real-time.
    """
    run_id = str(uuid.uuid4())

    logger.info(
        "worker_streaming_run_requested",
        extra={
            "run_id": run_id,
            "task": request.task[:100],
        },
    )

    # Initialize run
    _store_run(
        run_id,
        {
            "run_id": run_id,
            "task": request.task,
            "status": "queued",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    # Queue for background execution with events
    background_tasks.add_task(_execute_worker_with_events, run_id, request)

    return WorkerRunResponse(
        run_id=run_id,
        success=False,
        status="queued",
    )
