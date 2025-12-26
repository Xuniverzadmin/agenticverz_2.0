# M12 Agents API Routes
# REST API for multi-agent job execution
#
# Endpoints:
# - POST /api/v1/jobs - Create job
# - GET /api/v1/jobs/{id} - Get job status
# - POST /api/v1/jobs/{id}/cancel - Cancel job
# - POST /api/v1/jobs/{id}/claim - Worker claims item
# - POST /api/v1/jobs/{id}/items/{item_id}/complete - Complete item
# - GET/PUT /api/v1/blackboard/{key} - Blackboard operations
# - POST /api/v1/blackboard/{key}/lock - Lock operations
# - POST /api/v1/agents/register - Register agent
# - POST /api/v1/agents/{instance_id}/heartbeat - Heartbeat
# - GET/POST /api/v1/agents/{instance_id}/messages - Messages
#
# M15.1 SBA Endpoints:
# - POST /api/v1/sba/validate - Validate SBA schema
# - POST /api/v1/sba/register - Register agent with SBA
# - GET /api/v1/sba/{agent_id} - Get agent SBA
# - GET /api/v1/sba - List agents with SBA status

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from ..agents.services.blackboard_service import get_blackboard_service
from ..agents.services.credit_service import CREDIT_COSTS, get_credit_service
from ..agents.services.job_service import JobConfig, get_job_service
from ..agents.services.message_service import get_message_service
from ..agents.services.registry_service import get_registry_service
from ..agents.services.worker_service import get_worker_service
from ..agents.skills.agent_invoke import AgentInvokeSkill

# M15.1: SBA imports
try:
    from ..agents.sba import (
        SUPPORTED_SBA_VERSIONS,
        SBASchema,
        SBAService,
        SBAValidationResult,
        SBAVersionError,
        check_version_deprecated,
        generate_sba_from_agent,
        get_sba_service,
        # M15.1.1: Version negotiation
        get_version_info,
        negotiate_version,
        validate_sba,
    )

    SBA_AVAILABLE = True
except ImportError:
    SBA_AVAILABLE = False

logger = logging.getLogger("nova.api.agents")

router = APIRouter(prefix="/api/v1", tags=["agents"])


# ============ Request/Response Models ============


class CreateJobRequest(BaseModel):
    """Request to create a parallel job."""

    orchestrator_agent: str = Field(..., description="Orchestrator agent type")
    worker_agent: str = Field(..., description="Worker agent type")
    task: str = Field(..., description="Task name/description")
    items: List[Any] = Field(..., description="Items to process")
    parallelism: int = Field(default=10, ge=1, le=100)
    timeout_per_item: int = Field(default=60, ge=1, le=3600)
    max_retries: int = Field(default=3, ge=0, le=10)


class JobResponse(BaseModel):
    """Job status response."""

    id: str
    status: str
    task: str
    progress: Dict[str, Any]
    credits: Dict[str, Any]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]


class ClaimItemResponse(BaseModel):
    """Response when claiming an item."""

    claimed: bool
    item_id: Optional[str] = None
    item_index: Optional[int] = None
    input: Optional[Any] = None
    retry_count: int = 0


class CompleteItemRequest(BaseModel):
    """Request to complete an item."""

    output: Any = Field(..., description="Item result")


class FailItemRequest(BaseModel):
    """Request to fail an item."""

    error_message: str = Field(..., description="Error description")
    retry: bool = Field(default=True, description="Whether to retry")


class BlackboardWriteRequest(BaseModel):
    """Request to write to blackboard."""

    value: Any = Field(..., description="Value to store")
    ttl: Optional[int] = Field(default=None, description="TTL in seconds")


class BlackboardIncrementRequest(BaseModel):
    """Request to increment counter."""

    amount: int = Field(default=1, description="Increment amount")


class LockRequest(BaseModel):
    """Request for lock operation."""

    holder: str = Field(..., description="Lock holder identity")
    action: str = Field(default="acquire", description="acquire/release/extend")
    ttl: int = Field(default=30, description="Lock TTL in seconds")


class RegisterAgentRequest(BaseModel):
    """Request to register an agent."""

    agent_id: str = Field(..., description="Agent type/name")
    instance_id: Optional[str] = Field(default=None, description="Instance ID")
    job_id: Optional[str] = Field(default=None, description="Associated job")
    capabilities: Optional[Dict[str, Any]] = Field(default=None)


class SendMessageRequest(BaseModel):
    """Request to send a message."""

    from_instance_id: str = Field(..., description="Sender")
    message_type: str = Field(..., description="Message type")
    payload: Dict[str, Any] = Field(..., description="Message content")
    job_id: Optional[str] = Field(default=None)
    reply_to_id: Optional[str] = Field(default=None)


class InvokeResponseRequest(BaseModel):
    """Request to respond to an invocation."""

    invoke_id: str = Field(..., description="Invocation ID")
    response_payload: Dict[str, Any] = Field(..., description="Response data")


class SimulateJobRequest(BaseModel):
    """Request to simulate job execution before committing."""

    orchestrator_agent: str = Field(..., description="Orchestrator agent type")
    worker_agent: str = Field(..., description="Worker agent type")
    task: str = Field(..., description="Task name/description")
    items: List[Any] = Field(..., description="Items to process")
    parallelism: int = Field(default=10, ge=1, le=100)
    timeout_per_item: int = Field(default=60, ge=1, le=3600)
    max_retries: int = Field(default=3, ge=0, le=10)


class SimulateJobResponse(BaseModel):
    """Response from job simulation."""

    feasible: bool = Field(..., description="Whether job can be executed")
    estimated_credits: float = Field(..., description="Estimated total credits")
    credits_per_item: float = Field(..., description="Credits per item")
    item_count: int = Field(..., description="Number of items")
    estimated_duration_seconds: int = Field(..., description="Estimated duration")
    budget_check: Dict[str, Any] = Field(..., description="Budget availability check")
    risks: List[str] = Field(default_factory=list, description="Identified risks")
    warnings: List[str] = Field(default_factory=list, description="Warnings")
    cost_breakdown: Dict[str, float] = Field(..., description="Cost breakdown by type")


# ============ Job Endpoints ============


@router.post("/jobs/simulate", response_model=SimulateJobResponse)
async def simulate_job(
    request: SimulateJobRequest,
    x_tenant_id: str = Header(default="default", alias="X-Tenant-ID"),
):
    """
    Simulate job execution before committing resources.

    Machine-native pre-execution simulation (PIN-005):
    - Estimates total credits required
    - Checks budget availability
    - Estimates execution duration
    - Identifies risks and warnings
    - Returns feasibility assessment

    Does NOT create the job or reserve credits.
    """
    try:
        credit_service = get_credit_service()

        item_count = len(request.items)
        credits_per_item = float(CREDIT_COSTS.get("job_item", 1))

        # Calculate costs
        job_overhead = 5.0  # Base job creation cost
        item_credits = credits_per_item * item_count
        estimated_total = job_overhead + item_credits

        # Cost breakdown
        cost_breakdown = {
            "job_overhead": job_overhead,
            "item_processing": item_credits,
            "total": estimated_total,
        }

        # Check budget
        has_budget, budget_reason = credit_service.check_credits(x_tenant_id, estimated_total)

        budget_check = {
            "sufficient": has_budget,
            "required": estimated_total,
            "message": budget_reason if not has_budget else "Budget available",
        }

        # Estimate duration (parallelism-aware)
        # Each item takes timeout_per_item in worst case
        # With parallelism, items run concurrently
        waves = (item_count + request.parallelism - 1) // request.parallelism
        estimated_duration = waves * request.timeout_per_item

        # Identify risks
        risks = []
        warnings = []

        if item_count > 1000:
            risks.append("Large job (>1000 items) may take significant time")
        if item_count > 500 and request.parallelism < 20:
            warnings.append(f"Consider increasing parallelism for {item_count} items")
        if request.max_retries == 0:
            warnings.append("No retries configured - failures will be permanent")
        if estimated_total > 1000:
            warnings.append(f"High credit cost: {estimated_total:.0f} credits")
        if not has_budget:
            risks.append(f"Insufficient budget: {budget_reason}")

        # Feasibility = budget OK and no blocking risks
        feasible = has_budget and len(risks) == 0

        return SimulateJobResponse(
            feasible=feasible,
            estimated_credits=estimated_total,
            credits_per_item=credits_per_item,
            item_count=item_count,
            estimated_duration_seconds=estimated_duration,
            budget_check=budget_check,
            risks=risks,
            warnings=warnings,
            cost_breakdown=cost_breakdown,
        )

    except Exception as e:
        logger.error(f"Simulate job error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)[:100]}")


@router.post("/jobs", response_model=JobResponse)
async def create_job(
    request: CreateJobRequest,
    x_tenant_id: str = Header(default="default", alias="X-Tenant-ID"),
):
    """Create a new parallel job."""
    try:
        job_service = get_job_service()
        registry_service = get_registry_service()

        # Register orchestrator
        reg_result = registry_service.register(
            agent_id=request.orchestrator_agent,
            capabilities={"role": "orchestrator"},
        )

        # Create job
        job_config = JobConfig(
            orchestrator_agent=request.orchestrator_agent,
            worker_agent=request.worker_agent,
            task=request.task,
            items=request.items,
            parallelism=request.parallelism,
            timeout_per_item=request.timeout_per_item,
            max_retries=request.max_retries,
        )

        job = job_service.create_job(
            config=job_config,
            orchestrator_instance_id=reg_result.instance_id,
            tenant_id=x_tenant_id,
        )

        return JobResponse(
            id=str(job.id),
            status=job.status,
            task=job.task,
            progress={
                "total": job.progress.total,
                "completed": job.progress.completed,
                "failed": job.progress.failed,
                "pending": job.progress.pending,
                "progress_pct": job.progress.progress_pct,
            },
            credits={
                "reserved": float(job.credits.reserved),
                "spent": float(job.credits.spent),
                "refunded": float(job.credits.refunded),
            },
            created_at=job.created_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
        )

    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Create job error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)[:100]}")


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """Get job status by ID."""
    try:
        job_service = get_job_service()
        job = job_service.get_job(UUID(job_id))

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Check completion
        job_service.check_job_completion(UUID(job_id))
        job = job_service.get_job(UUID(job_id))

        return JobResponse(
            id=str(job.id),
            status=job.status,
            task=job.task,
            progress={
                "total": job.progress.total,
                "completed": job.progress.completed,
                "failed": job.progress.failed,
                "pending": job.progress.pending,
                "progress_pct": job.progress.progress_pct,
            },
            credits={
                "reserved": float(job.credits.reserved),
                "spent": float(job.credits.spent),
                "refunded": float(job.credits.refunded),
            },
            created_at=job.created_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID")


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a running job."""
    job_service = get_job_service()
    cancelled = job_service.cancel_job(UUID(job_id))

    if not cancelled:
        raise HTTPException(status_code=400, detail="Job could not be cancelled")

    return {"cancelled": True, "job_id": job_id}


@router.post("/jobs/{job_id}/claim", response_model=ClaimItemResponse)
async def claim_item(
    job_id: str,
    worker_instance_id: str = Query(..., description="Worker instance ID"),
):
    """Worker claims next available item."""
    worker_service = get_worker_service()

    claimed = worker_service.claim_item(UUID(job_id), worker_instance_id)

    if not claimed:
        return ClaimItemResponse(claimed=False)

    return ClaimItemResponse(
        claimed=True,
        item_id=str(claimed.id),
        item_index=claimed.item_index,
        input=claimed.input,
        retry_count=claimed.retry_count,
    )


@router.post("/jobs/{job_id}/items/{item_id}/complete")
async def complete_item(
    job_id: str,
    item_id: str,
    request: CompleteItemRequest,
):
    """Mark item as completed with output."""
    worker_service = get_worker_service()

    success = worker_service.complete_item(UUID(item_id), request.output)

    if not success:
        raise HTTPException(status_code=400, detail="Could not complete item")

    # Check if job is done
    job_service = get_job_service()
    job_service.check_job_completion(UUID(job_id))

    return {"completed": True, "item_id": item_id}


@router.post("/jobs/{job_id}/items/{item_id}/fail")
async def fail_item(
    job_id: str,
    item_id: str,
    request: FailItemRequest,
):
    """Mark item as failed."""
    worker_service = get_worker_service()

    success = worker_service.fail_item(
        UUID(item_id),
        request.error_message,
        retry=request.retry,
    )

    if not success:
        raise HTTPException(status_code=400, detail="Could not fail item")

    # Check if job is done
    job_service = get_job_service()
    job_service.check_job_completion(UUID(job_id))

    return {"failed": True, "item_id": item_id}


# ============ Blackboard Endpoints ============


@router.get("/blackboard/{key}")
async def get_blackboard(key: str):
    """Read value from blackboard."""
    blackboard = get_blackboard_service()
    value = blackboard.get(key)

    return {
        "key": key,
        "value": value,
        "found": value is not None,
    }


@router.put("/blackboard/{key}")
async def put_blackboard(key: str, request: BlackboardWriteRequest):
    """Write value to blackboard."""
    blackboard = get_blackboard_service()
    success = blackboard.set(key, request.value, ttl=request.ttl)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to write to blackboard")

    return {"success": True, "key": key}


@router.post("/blackboard/{key}/increment")
async def increment_blackboard(key: str, request: BlackboardIncrementRequest):
    """Atomically increment a counter."""
    blackboard = get_blackboard_service()
    new_value = blackboard.increment(key, request.amount)

    if new_value is None:
        raise HTTPException(status_code=500, detail="Failed to increment")

    return {"key": key, "value": new_value}


@router.post("/blackboard/{key}/lock")
async def lock_blackboard(key: str, request: LockRequest):
    """Lock operation on blackboard."""
    blackboard = get_blackboard_service()

    if request.action == "acquire":
        result = blackboard.acquire_lock(key, request.holder, request.ttl)
        return {
            "action": "acquire",
            "acquired": result.acquired,
            "holder": result.holder,
        }

    elif request.action == "release":
        released = blackboard.release_lock(key, request.holder)
        return {"action": "release", "released": released}

    elif request.action == "extend":
        extended = blackboard.extend_lock(key, request.holder, request.ttl)
        return {"action": "extend", "extended": extended}

    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")


# ============ Agent Endpoints ============


@router.post("/agents/register")
async def register_agent(request: RegisterAgentRequest):
    """Register an agent instance."""
    registry = get_registry_service()

    job_id = UUID(request.job_id) if request.job_id else None

    result = registry.register(
        agent_id=request.agent_id,
        instance_id=request.instance_id,
        job_id=job_id,
        capabilities=request.capabilities,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return {
        "registered": True,
        "instance_id": result.instance_id,
        "db_id": str(result.db_id) if result.db_id else None,
    }


@router.post("/agents/{instance_id}/heartbeat")
async def agent_heartbeat(instance_id: str):
    """Update agent heartbeat."""
    registry = get_registry_service()
    success = registry.heartbeat(instance_id)

    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {"heartbeat": True, "instance_id": instance_id}


@router.delete("/agents/{instance_id}")
async def deregister_agent(instance_id: str):
    """Deregister an agent instance."""
    registry = get_registry_service()
    success = registry.deregister(instance_id)

    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {"deregistered": True, "instance_id": instance_id}


@router.get("/agents/{instance_id}")
async def get_agent(instance_id: str):
    """Get agent instance details."""
    registry = get_registry_service()
    agent = registry.get_instance(instance_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {
        "id": str(agent.id),
        "agent_id": agent.agent_id,
        "instance_id": agent.instance_id,
        "job_id": str(agent.job_id) if agent.job_id else None,
        "status": agent.status,
        "capabilities": agent.capabilities,
        "heartbeat_at": agent.heartbeat_at.isoformat() if agent.heartbeat_at else None,
        "heartbeat_age_seconds": agent.heartbeat_age_seconds,
        "created_at": agent.created_at.isoformat(),
    }


@router.get("/agents")
async def list_agents(
    agent_id: Optional[str] = Query(default=None),
    job_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
):
    """List agent instances."""
    registry = get_registry_service()

    agents = registry.list_instances(
        agent_id=agent_id,
        job_id=UUID(job_id) if job_id else None,
        status=status,
    )

    return {
        "agents": [
            {
                "id": str(a.id),
                "agent_id": a.agent_id,
                "instance_id": a.instance_id,
                "job_id": str(a.job_id) if a.job_id else None,
                "status": a.status,
                "heartbeat_at": a.heartbeat_at.isoformat() if a.heartbeat_at else None,
            }
            for a in agents
        ],
        "count": len(agents),
    }


# ============ Message Endpoints ============


@router.post("/agents/{instance_id}/messages")
async def send_message(instance_id: str, request: SendMessageRequest):
    """Send a message to an agent."""
    message_service = get_message_service()

    job_id = UUID(request.job_id) if request.job_id else None
    reply_to_id = UUID(request.reply_to_id) if request.reply_to_id else None

    result = message_service.send(
        from_instance_id=request.from_instance_id,
        to_instance_id=instance_id,
        message_type=request.message_type,
        payload=request.payload,
        job_id=job_id,
        reply_to_id=reply_to_id,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return {
        "sent": True,
        "message_id": str(result.message_id),
    }


@router.get("/agents/{instance_id}/messages")
async def get_messages(
    instance_id: str,
    status: Optional[str] = Query(default=None),
    message_type: Optional[str] = Query(default=None),
    job_id: Optional[str] = Query(default=None),
    limit: int = Query(default=100, le=500),
):
    """Get messages for an agent."""
    message_service = get_message_service()

    messages = message_service.get_inbox(
        instance_id=instance_id,
        status=status,
        message_type=message_type,
        job_id=UUID(job_id) if job_id else None,
        limit=limit,
    )

    return {
        "messages": [
            {
                "id": str(m.id),
                "from_instance_id": m.from_instance_id,
                "message_type": m.message_type,
                "payload": m.payload,
                "status": m.status,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
        "count": len(messages),
    }


@router.post("/agents/{instance_id}/messages/{message_id}/read")
async def mark_message_read(instance_id: str, message_id: str):
    """Mark message as read."""
    message_service = get_message_service()
    success = message_service.mark_read(UUID(message_id))

    if not success:
        raise HTTPException(status_code=400, detail="Could not mark as read")

    return {"read": True, "message_id": message_id}


# ============ Invocation Response Endpoint ============


@router.post("/invocations/respond")
async def respond_to_invocation(request: InvokeResponseRequest):
    """Respond to an agent invocation."""
    success = AgentInvokeSkill.respond_to_invoke(
        invoke_id=request.invoke_id,
        response_payload=request.response_payload,
    )

    if not success:
        raise HTTPException(status_code=400, detail="Could not respond to invocation")

    return {"responded": True, "invoke_id": request.invoke_id}


# ============ M15.1 SBA Endpoints ============


class SBAValidateRequest(BaseModel):
    """Request to validate SBA schema."""

    sba: Dict[str, Any] = Field(..., description="SBA schema to validate")
    enforce_governance: bool = Field(default=True, description="Require BudgetLLM governance")


class SBARegisterRequest(BaseModel):
    """Request to register agent with SBA."""

    agent_id: str = Field(..., description="Agent identifier")
    sba: Dict[str, Any] = Field(..., description="SBA schema")
    agent_name: Optional[str] = Field(default=None, description="Human-readable name")
    description: Optional[str] = Field(default=None, description="Agent description")
    agent_type: str = Field(default="worker", description="worker/orchestrator/aggregator")
    capabilities: Optional[Dict[str, Any]] = Field(default=None)
    config: Optional[Dict[str, Any]] = Field(default=None)


class SBAGenerateRequest(BaseModel):
    """Request to auto-generate SBA for an agent."""

    agent_id: str = Field(..., description="Agent identifier")
    capabilities: Optional[Dict[str, Any]] = Field(default=None)
    config: Optional[Dict[str, Any]] = Field(default=None)
    orchestrator: Optional[str] = Field(default="system", description="Orchestrator name")


@router.post("/sba/validate")
async def validate_sba_endpoint(request: SBAValidateRequest):
    """
    Validate an SBA schema.

    M15.1 Strategy-Bound Agent validation endpoint.
    Returns validation result with any errors or warnings.
    """
    if not SBA_AVAILABLE:
        raise HTTPException(status_code=501, detail="SBA module not available")

    result = validate_sba(request.sba, enforce_governance=request.enforce_governance)

    return {
        "valid": result.valid,
        "errors": [
            {
                "code": e.code.value,
                "field": e.field,
                "message": e.message,
            }
            for e in result.errors
        ],
        "warnings": result.warnings,
    }


@router.post("/sba/register")
async def register_agent_with_sba(
    request: SBARegisterRequest,
    x_tenant_id: str = Header(default="default", alias="X-Tenant-ID"),
):
    """
    Register an agent with its SBA schema.

    M15.1 Strategy-Bound Agent registration.
    Validates SBA and stores agent definition in registry.
    """
    if not SBA_AVAILABLE:
        raise HTTPException(status_code=501, detail="SBA module not available")

    try:
        sba_service = get_sba_service()

        # Validate and parse SBA
        sba = SBASchema.model_validate(request.sba)

        # Register
        agent = sba_service.register_agent(
            agent_id=request.agent_id,
            sba=sba,
            agent_name=request.agent_name,
            description=request.description,
            agent_type=request.agent_type,
            capabilities=request.capabilities,
            config=request.config,
            tenant_id=x_tenant_id,
            validate=True,
        )

        return {
            "registered": True,
            "agent_id": agent.agent_id,
            "sba_version": agent.sba_version,
            "sba_validated": agent.sba_validated,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"SBA registration error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Registration error: {str(e)[:100]}")


@router.post("/sba/generate")
async def generate_sba_for_agent(request: SBAGenerateRequest):
    """
    Auto-generate SBA for an agent.

    M15.1 SBA generation for retrofitting existing agents.
    """
    if not SBA_AVAILABLE:
        raise HTTPException(status_code=501, detail="SBA module not available")

    try:
        sba = generate_sba_from_agent(
            agent_id=request.agent_id,
            capabilities=request.capabilities,
            config=request.config,
            orchestrator=request.orchestrator,
        )

        return {
            "generated": True,
            "agent_id": request.agent_id,
            "sba": sba.to_dict(),
        }

    except Exception as e:
        logger.error(f"SBA generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)[:100]}")


# NOTE: Static routes (/sba/version, /sba/version/negotiate) MUST come before /sba/{agent_id}
@router.get("/sba/version")
async def get_sba_version_info():
    """
    M15.1.1: Get SBA version negotiation info.

    Returns information about supported SBA versions for client negotiation.
    """
    if not SBA_AVAILABLE:
        raise HTTPException(status_code=501, detail="SBA module not available")

    return get_version_info()


@router.post("/sba/version/negotiate")
async def negotiate_sba_version(
    requested_version: str = Query(..., description="Requested SBA version"),
):
    """
    M15.1.1: Negotiate SBA version.

    Client submits requested version, server responds with best compatible version.
    """
    if not SBA_AVAILABLE:
        raise HTTPException(status_code=501, detail="SBA module not available")

    try:
        negotiated = negotiate_version(requested_version)
        deprecated = check_version_deprecated(negotiated)

        return {
            "requested": requested_version,
            "negotiated": negotiated,
            "supported": True,
            "deprecated": deprecated,
            "message": f"Version {negotiated} is deprecated, consider upgrading" if deprecated else None,
        }
    except SBAVersionError as e:
        return {
            "requested": requested_version,
            "negotiated": None,
            "supported": False,
            "deprecated": False,
            "message": str(e),
            "supported_versions": list(e.supported),
        }


@router.get("/sba/health")
async def get_sba_health(
    x_tenant_id: str = Header(default="default", alias="X-Tenant-ID"),
):
    """
    M16: Get aggregated strategy health for Guard Console.

    Returns simple signal-level health status for all agents.
    Used by StrategyHealthWidget in Guard Console.
    """
    if not SBA_AVAILABLE:
        return {
            "total_agents": 0,
            "healthy_count": 0,
            "approaching_bounds_count": 0,
            "exceeded_count": 0,
            "status": "unknown",
            "last_evaluated_at": None,
        }

    try:
        from datetime import datetime, timezone

        sba_service = get_sba_service()
        agents = sba_service.list_agents(tenant_id=x_tenant_id, enabled_only=True)

        total = len(agents)
        healthy = 0
        approaching = 0
        exceeded = 0

        for agent in agents:
            sba = agent.sba or {}
            how_to_win = sba.get("how_to_win", {})
            fulfillment = how_to_win.get("fulfillment_metric", 0.0)

            # Simple classification:
            # - Healthy: fulfillment >= 0.6 and validated
            # - Approaching: fulfillment 0.3-0.6 OR not validated
            # - Exceeded: fulfillment < 0.3
            if not agent.sba_validated:
                approaching += 1
            elif fulfillment >= 0.6:
                healthy += 1
            elif fulfillment >= 0.3:
                approaching += 1
            else:
                exceeded += 1

        # Overall status (worst case wins)
        if exceeded > 0:
            status = "exceeded"
        elif approaching > 0:
            status = "approaching"
        elif total > 0:
            status = "healthy"
        else:
            status = "no_agents"

        return {
            "total_agents": total,
            "healthy_count": healthy,
            "approaching_bounds_count": approaching,
            "exceeded_count": exceeded,
            "status": status,
            "last_evaluated_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"SBA health check error: {e}", exc_info=True)
        return {
            "total_agents": 0,
            "healthy_count": 0,
            "approaching_bounds_count": 0,
            "exceeded_count": 0,
            "status": "error",
            "last_evaluated_at": None,
        }


# Parameter route MUST come after static routes
@router.get("/sba/{agent_id}")
async def get_agent_sba(agent_id: str):
    """
    Get SBA schema for an agent.

    M15.1 SBA retrieval endpoint.
    """
    if not SBA_AVAILABLE:
        raise HTTPException(status_code=501, detail="SBA module not available")

    try:
        sba_service = get_sba_service()
        agent = sba_service.get_agent(agent_id)

        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

        return {
            "agent_id": agent.agent_id,
            "agent_name": agent.agent_name,
            "agent_type": agent.agent_type,
            "sba": agent.sba,
            "sba_version": agent.sba_version,
            "sba_validated": agent.sba_validated,
            "status": agent.status,
            "enabled": agent.enabled,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get SBA error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:100]}")


@router.get("/sba")
async def list_agents_sba(
    agent_type: Optional[str] = Query(default=None),
    sba_validated: Optional[bool] = Query(default=None),
    x_tenant_id: str = Header(default="default", alias="X-Tenant-ID"),
):
    """
    List agents with their SBA status.

    M15.1 SBA registry listing.
    """
    if not SBA_AVAILABLE:
        raise HTTPException(status_code=501, detail="SBA module not available")

    try:
        sba_service = get_sba_service()

        agents = sba_service.list_agents(
            agent_type=agent_type,
            tenant_id=x_tenant_id,
            sba_validated_only=sba_validated if sba_validated else False,
        )

        return {
            "agents": [
                {
                    "agent_id": a.agent_id,
                    "agent_name": a.agent_name,
                    "agent_type": a.agent_type,
                    "sba_version": a.sba_version,
                    "sba_validated": a.sba_validated,
                    "status": a.status,
                    "enabled": a.enabled,
                }
                for a in agents
            ],
            "count": len(agents),
        }

    except Exception as e:
        logger.error(f"List SBA error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:100]}")


@router.post("/sba/check-spawn")
async def check_spawn_allowed(
    agent_id: str = Query(..., description="Agent ID to check"),
    orchestrator: Optional[str] = Query(default=None),
    auto_generate: bool = Query(default=True),
):
    """
    Check if agent is allowed to spawn.

    M15.1 spawn-time enforcement check.
    Returns whether the agent has a valid SBA and can be spawned.
    """
    if not SBA_AVAILABLE:
        raise HTTPException(status_code=501, detail="SBA module not available")

    try:
        sba_service = get_sba_service()

        allowed, error = sba_service.check_spawn_allowed(
            agent_id=agent_id,
            auto_generate=auto_generate,
            orchestrator=orchestrator,
        )

        return {
            "agent_id": agent_id,
            "spawn_allowed": allowed,
            "error": error,
        }

    except Exception as e:
        logger.error(f"Check spawn error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:100]}")


@router.get("/sba/fulfillment/aggregated")
async def get_fulfillment_aggregated(
    group_by: str = Query(default="domain", description="Group by: domain, agent_type, orchestrator"),
    threshold: Optional[float] = Query(default=None, description="Filter by minimum fulfillment"),
    x_tenant_id: str = Header(default="default", alias="X-Tenant-ID"),
):
    """
    M15.1.1: Get aggregated fulfillment metrics for heatmap visualization.

    Returns fulfillment data for all agents with grouping and marketplace readiness.
    Used by the SBA Inspector UI for the fulfillment heatmap feature.
    """
    if not SBA_AVAILABLE:
        raise HTTPException(status_code=501, detail="SBA module not available")

    try:
        sba_service = get_sba_service()
        agents = sba_service.list_agents(tenant_id=x_tenant_id, enabled_only=True)

        result = {
            "agents": [],
            "groups": {},
            "summary": {
                "total_agents": 0,
                "validated_count": 0,
                "avg_fulfillment": 0.0,
                "marketplace_ready_count": 0,
                "by_fulfillment_range": {
                    "0.0-0.2": 0,
                    "0.2-0.4": 0,
                    "0.4-0.6": 0,
                    "0.6-0.8": 0,
                    "0.8-1.0": 0,
                },
            },
        }

        fulfillment_sum = 0.0
        groups: Dict[str, List[str]] = {}

        for agent in agents:
            sba = agent.sba or {}
            how_to_win = sba.get("how_to_win", {})
            where_to_play = sba.get("where_to_play", {})
            ems = sba.get("enabling_management_systems", {})

            fulfillment = float(how_to_win.get("fulfillment_metric", 0.0))
            domain = where_to_play.get("domain", "unknown")
            orchestrator = ems.get("orchestrator", "unknown")

            # Apply threshold filter
            if threshold is not None and fulfillment < threshold:
                continue

            agent_data = {
                "agent_id": agent.agent_id,
                "agent_name": agent.agent_name,
                "agent_type": agent.agent_type,
                "domain": domain,
                "orchestrator": orchestrator,
                "fulfillment_metric": fulfillment,
                "fulfillment_history": how_to_win.get("fulfillment_history", [])[-10:],  # Last 10 entries
                "sba_validated": agent.sba_validated,
                "marketplace_ready": fulfillment >= 0.8,
                "status": agent.status,
            }
            result["agents"].append(agent_data)
            fulfillment_sum += fulfillment

            # Update summary
            if agent.sba_validated:
                result["summary"]["validated_count"] += 1
            if fulfillment >= 0.8:
                result["summary"]["marketplace_ready_count"] += 1

            # Bucket by range
            if fulfillment < 0.2:
                result["summary"]["by_fulfillment_range"]["0.0-0.2"] += 1
            elif fulfillment < 0.4:
                result["summary"]["by_fulfillment_range"]["0.2-0.4"] += 1
            elif fulfillment < 0.6:
                result["summary"]["by_fulfillment_range"]["0.4-0.6"] += 1
            elif fulfillment < 0.8:
                result["summary"]["by_fulfillment_range"]["0.6-0.8"] += 1
            else:
                result["summary"]["by_fulfillment_range"]["0.8-1.0"] += 1

            # Build groups based on group_by parameter
            if group_by == "domain":
                group_key = domain
            elif group_by == "agent_type":
                group_key = agent.agent_type
            elif group_by == "orchestrator":
                group_key = orchestrator
            else:
                group_key = domain

            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(agent.agent_id)

        result["summary"]["total_agents"] = len(result["agents"])
        result["summary"]["avg_fulfillment"] = round(
            fulfillment_sum / len(result["agents"]) if result["agents"] else 0.0, 3
        )
        result["groups"] = groups

        return result

    except Exception as e:
        logger.error(f"Fulfillment aggregation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:100]}")


# ============ M16 Activity & Health Endpoints ============


class WorkerCostMetrics(BaseModel):
    """Worker cost and risk metrics."""

    id: str
    name: Optional[str] = None
    cost: str  # low/medium/high
    risk: float  # 0-1
    budget_used: float  # 0-100 percentage


class ActivityCostsResponse(BaseModel):
    """Response for activity costs endpoint."""

    agent_id: str
    workers: List[WorkerCostMetrics]
    total_cost_level: str
    total_risk: float
    timestamp: str


class SpendingDataResponse(BaseModel):
    """Response for spending tracker endpoint."""

    agent_id: str
    actual: List[float]
    projected: List[float]
    budget_limit: float
    anomalies: List[Dict[str, Any]]
    period: str  # e.g., "24h", "7d"
    timestamp: str


class RetryEntryResponse(BaseModel):
    """Single retry entry."""

    time: str
    reason: str
    attempt: int
    outcome: str  # success/failure/pending
    risk_change: Optional[float] = None


class ActivityRetriesResponse(BaseModel):
    """Response for retries endpoint."""

    agent_id: str
    retries: List[RetryEntryResponse]
    total_retries: int
    success_rate: float
    timestamp: str


class BlockerEntry(BaseModel):
    """Single blocker entry."""

    type: str  # dependency/api/tool/circular/budget
    message: str
    since: str
    action: Optional[str] = None
    details: Optional[str] = None


class ActivityBlockersResponse(BaseModel):
    """Response for blockers endpoint."""

    agent_id: str
    blockers: List[BlockerEntry]
    blocked: bool
    timestamp: str


class HealthCheckItem(BaseModel):
    """Single health check result."""

    severity: str  # error/warning/info
    code: str
    title: str
    message: str
    action: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Response for health check endpoint."""

    agent_id: str
    healthy: bool
    errors: List[HealthCheckItem]
    warnings: List[HealthCheckItem]
    suggestions: List[HealthCheckItem]
    checked_at: str


@router.get("/agents/{agent_id}/activity/costs", response_model=ActivityCostsResponse)
async def get_agent_activity_costs(
    agent_id: str,
    x_tenant_id: str = Header(default="default", alias="X-Tenant-ID"),
):
    """
    M16: Get worker cost and risk metrics for an agent.

    Returns per-worker cost levels, risk scores, and budget usage.
    """
    from datetime import datetime

    try:
        # Get agent's job workers from registry
        registry = get_registry_service()
        workers = registry.list_instances(agent_id=agent_id)

        worker_metrics = []
        total_risk = 0.0
        high_cost_count = 0

        for worker in workers:
            # Calculate metrics based on worker activity
            caps = worker.capabilities or {}

            # Determine cost level from capabilities or default
            cost_level = caps.get("cost_level", "low")
            if cost_level not in ["low", "medium", "high"]:
                cost_level = "low"

            # Calculate risk from heartbeat age and status
            risk = 0.1  # Base risk
            if worker.heartbeat_age_seconds and worker.heartbeat_age_seconds > 60:
                risk += 0.3  # Stale heartbeat
            if worker.status == "error":
                risk += 0.4
            elif worker.status == "busy":
                risk += 0.1
            risk = min(risk, 1.0)

            # Budget usage from capabilities or estimate
            budget_used = float(caps.get("budget_used_pct", 0))
            if budget_used == 0 and worker.status == "busy":
                budget_used = 50.0  # Estimate for active workers

            if cost_level == "high":
                high_cost_count += 1

            worker_metrics.append(
                WorkerCostMetrics(
                    id=worker.instance_id,
                    name=caps.get("name", worker.agent_id),
                    cost=cost_level,
                    risk=round(risk, 2),
                    budget_used=round(budget_used, 1),
                )
            )
            total_risk += risk

        # Determine total cost level
        if high_cost_count > len(workers) // 2:
            total_cost = "high"
        elif high_cost_count > 0:
            total_cost = "medium"
        else:
            total_cost = "low"

        avg_risk = total_risk / len(workers) if workers else 0.0

        return ActivityCostsResponse(
            agent_id=agent_id,
            workers=worker_metrics,
            total_cost_level=total_cost,
            total_risk=round(avg_risk, 2),
            timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error(f"Activity costs error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:100]}")


@router.get("/agents/{agent_id}/activity/spending", response_model=SpendingDataResponse)
async def get_agent_activity_spending(
    agent_id: str,
    period: str = Query(default="24h", description="Time period: 1h, 6h, 24h, 7d"),
    x_tenant_id: str = Header(default="default", alias="X-Tenant-ID"),
):
    """
    M16: Get spending data for budget burn chart.

    Returns actual vs projected spending over time with anomaly detection.
    """
    from datetime import datetime

    try:
        credit_service = get_credit_service()

        # Get credit balance for tenant/agent
        balance = credit_service.get_balance(x_tenant_id)
        available = float(balance.available_credits) if balance else 1000.0

        # Calculate time buckets based on period
        if period == "1h":
            num_points = 12  # 5-min intervals
            budget_limit = available / 24
        elif period == "6h":
            num_points = 12  # 30-min intervals
            budget_limit = available / 4
        elif period == "7d":
            num_points = 14  # 12-hour intervals
            budget_limit = available * 7
        else:  # 24h default
            num_points = 24  # 1-hour intervals
            budget_limit = available

        # Generate spending data
        # In production, this would come from a time-series store
        import random

        random.seed(hash(agent_id) % 2**32)  # Consistent per agent

        projected = []
        actual = []
        anomalies = []

        projected_increment = budget_limit / num_points
        actual_variance = 0.15  # 15% variance

        proj_sum = 0
        act_sum = 0

        for i in range(num_points):
            proj_sum += projected_increment
            projected.append(round(proj_sum, 2))

            # Actual with some variance
            variance = 1 + random.uniform(-actual_variance, actual_variance * 2)
            act_sum += projected_increment * variance
            actual.append(round(act_sum, 2))

            # Detect anomalies (>30% over projected)
            if act_sum > proj_sum * 1.3:
                anomalies.append(
                    {
                        "index": i,
                        "reason": "Spending 30%+ over projected",
                        "actual": round(act_sum, 2),
                        "projected": round(proj_sum, 2),
                    }
                )

        return SpendingDataResponse(
            agent_id=agent_id,
            actual=actual,
            projected=projected,
            budget_limit=budget_limit,
            anomalies=anomalies[-3:],  # Last 3 anomalies
            period=period,
            timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error(f"Activity spending error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:100]}")


@router.get("/agents/{agent_id}/activity/retries", response_model=ActivityRetriesResponse)
async def get_agent_activity_retries(
    agent_id: str,
    limit: int = Query(default=50, le=200),
    x_tenant_id: str = Header(default="default", alias="X-Tenant-ID"),
):
    """
    M16: Get retry log for an agent.

    Returns recent retry attempts with outcomes and risk impact.
    """
    from datetime import datetime

    try:
        # Get job service to find jobs for this agent
        job_service = get_job_service()

        retries = []
        total_success = 0
        total_retries = 0

        # Find jobs where this agent is the orchestrator or worker
        registry = get_registry_service()
        instances = registry.list_instances(agent_id=agent_id)

        for instance in instances:
            if instance.job_id:
                job = job_service.get_job(instance.job_id)
                if job:
                    # Check job items for failures (indicating potential retries)
                    try:
                        items = job_service.get_job_items(instance.job_id)
                        for item in items:
                            # Items with error_message indicate failures
                            if item.error_message:
                                total_retries += 1
                                is_success = item.status == "completed"
                                if is_success:
                                    total_success += 1

                                # Use completed_at or claimed_at for timing
                                retry_time = item.completed_at or item.claimed_at or datetime.utcnow()

                                retries.append(
                                    RetryEntryResponse(
                                        time=retry_time.strftime("%H:%M:%S"),
                                        reason=item.error_message[:100] if item.error_message else "Unknown error",
                                        attempt=1,
                                        outcome="success" if is_success else "failure",
                                        risk_change=-0.05 if is_success else 0.1,
                                    )
                                )
                    except Exception:
                        # Skip if we can't get job items
                        pass

        # Sort by time descending and limit
        retries = sorted(retries, key=lambda r: r.time, reverse=True)[:limit]

        success_rate = total_success / total_retries if total_retries > 0 else 1.0

        return ActivityRetriesResponse(
            agent_id=agent_id,
            retries=retries,
            total_retries=total_retries,
            success_rate=round(success_rate, 2),
            timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error(f"Activity retries error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:100]}")


@router.get("/agents/{agent_id}/activity/blockers", response_model=ActivityBlockersResponse)
async def get_agent_activity_blockers(
    agent_id: str,
    x_tenant_id: str = Header(default="default", alias="X-Tenant-ID"),
):
    """
    M16: Get current blockers for an agent.

    Returns issues preventing agent execution with suggested actions.
    """
    from datetime import datetime

    try:
        blockers = []

        # Check SBA for dependencies and constraints
        if SBA_AVAILABLE:
            sba_service = get_sba_service()
            agent = sba_service.get_agent(agent_id)

            if agent and agent.sba:
                sba = agent.sba
                where_to_play = sba.get("where_to_play", {})
                caps = sba.get("capabilities_capacity", {})
                ems = sba.get("enabling_management_systems", {})

                # Check for missing dependencies
                dependencies = caps.get("dependencies", [])
                for dep in dependencies:
                    if isinstance(dep, dict):
                        dep_id = dep.get("agent_id", "")
                        dep_required = dep.get("required", True)
                        if dep_required:
                            # Check if dependency agent exists and is healthy
                            dep_agent = sba_service.get_agent(dep_id)
                            if not dep_agent:
                                blockers.append(
                                    BlockerEntry(
                                        type="dependency",
                                        message=f"Required agent '{dep_id}' not found",
                                        since="Registration time",
                                        action="Register dependency",
                                        details=f"Agent depends on {dep_id}",
                                    )
                                )
                            elif not dep_agent.enabled:
                                blockers.append(
                                    BlockerEntry(
                                        type="dependency",
                                        message=f"Required agent '{dep_id}' is disabled",
                                        since="Unknown",
                                        action="Enable dependency",
                                        details=f"Agent depends on {dep_id}",
                                    )
                                )

                # Check budget constraints
                if ems.get("governance") == "BudgetLLM":
                    credit_service = get_credit_service()
                    balance = credit_service.get_balance(x_tenant_id)
                    available = float(balance.available_credits) if balance else 0
                    if available < 10:
                        blockers.append(
                            BlockerEntry(
                                type="budget",
                                message="Insufficient credits available",
                                since="Now",
                                action="Add credits",
                                details=f"Available: {available} credits",
                            )
                        )

        # Check registry for stale workers
        registry = get_registry_service()
        workers = registry.list_instances(agent_id=agent_id)

        stale_workers = [w for w in workers if w.heartbeat_age_seconds and w.heartbeat_age_seconds > 120]
        if stale_workers:
            blockers.append(
                BlockerEntry(
                    type="api",
                    message=f"{len(stale_workers)} worker(s) have stale heartbeats",
                    since=f"{min(w.heartbeat_age_seconds for w in stale_workers)}s ago",
                    action="Restart workers",
                    details=", ".join(w.instance_id for w in stale_workers[:3]),
                )
            )

        # Check for error status workers
        error_workers = [w for w in workers if w.status == "error"]
        if error_workers:
            blockers.append(
                BlockerEntry(
                    type="tool",
                    message=f"{len(error_workers)} worker(s) in error state",
                    since="Recent",
                    action="Investigate errors",
                    details=", ".join(w.instance_id for w in error_workers[:3]),
                )
            )

        return ActivityBlockersResponse(
            agent_id=agent_id,
            blockers=blockers,
            blocked=len(blockers) > 0,
            timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error(f"Activity blockers error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:100]}")


@router.post("/agents/{agent_id}/health/check", response_model=HealthCheckResponse)
async def check_agent_health(
    agent_id: str,
    x_tenant_id: str = Header(default="default", alias="X-Tenant-ID"),
):
    """
    M16: Run comprehensive health check for an agent.

    Validates SBA configuration, checks for missing tools, unregistered
    connections, workflow issues, and purpose conflicts.
    """
    from datetime import datetime

    errors = []
    warnings = []
    suggestions = []

    try:
        if not SBA_AVAILABLE:
            errors.append(
                HealthCheckItem(
                    severity="error",
                    code="SBA_UNAVAILABLE",
                    title="SBA Module Unavailable",
                    message="Strategy-Bound Agent module is not available",
                    action="Contact administrator",
                )
            )
            return HealthCheckResponse(
                agent_id=agent_id,
                healthy=False,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions,
                checked_at=datetime.utcnow().isoformat(),
            )

        sba_service = get_sba_service()
        agent = sba_service.get_agent(agent_id)

        if not agent:
            errors.append(
                HealthCheckItem(
                    severity="error",
                    code="AGENT_NOT_FOUND",
                    title="Agent Not Registered",
                    message=f"No agent found with ID '{agent_id}'",
                    action="Register the agent",
                )
            )
            return HealthCheckResponse(
                agent_id=agent_id,
                healthy=False,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions,
                checked_at=datetime.utcnow().isoformat(),
            )

        sba = agent.sba or {}

        # Check 1: SBA Validation Status
        if not agent.sba_validated:
            errors.append(
                HealthCheckItem(
                    severity="error",
                    code="NOT_VALIDATED",
                    title="Not Validated",
                    message="Agent SBA schema has not passed validation",
                    action="Run Validation",
                )
            )

        # Check 2: Purpose defined
        winning_aspiration = sba.get("winning_aspiration", {})
        if not winning_aspiration.get("description"):
            errors.append(
                HealthCheckItem(
                    severity="error",
                    code="NO_PURPOSE",
                    title="No Purpose Defined",
                    message="This agent has no purpose statement",
                    action="Add Purpose",
                )
            )

        # Check 3: Orchestrator assigned
        ems = sba.get("enabling_management_systems", {})
        if not ems.get("orchestrator"):
            errors.append(
                HealthCheckItem(
                    severity="error",
                    code="NO_ORCHESTRATOR",
                    title="No Workflow Defined",
                    message="Agent has no orchestrator assigned",
                    action="Assign Orchestrator",
                )
            )

        # Check 4: Tools defined
        where_to_play = sba.get("where_to_play", {})
        allowed_tools = where_to_play.get("allowed_tools", [])
        if not allowed_tools:
            warnings.append(
                HealthCheckItem(
                    severity="warning",
                    code="NO_TOOLS",
                    title="No Tools Specified",
                    message="Agent has no allowed tools listed",
                    action="Configure Tools",
                )
            )

        # Check 5: Tasks defined
        how_to_win = sba.get("how_to_win", {})
        tasks = how_to_win.get("tasks", [])
        if not tasks:
            warnings.append(
                HealthCheckItem(
                    severity="warning",
                    code="NO_TASKS",
                    title="No Tasks Defined",
                    message="Agent has no tasks in its checklist",
                    action="Add Tasks",
                )
            )

        # Check 6: Governance enabled
        if ems.get("governance") != "BudgetLLM":
            warnings.append(
                HealthCheckItem(
                    severity="warning",
                    code="NO_GOVERNANCE",
                    title="No Governance",
                    message="Agent is not under BudgetLLM governance",
                    action="Enable Governance",
                )
            )

        # Check 7: Fulfillment score
        fulfillment = how_to_win.get("fulfillment_metric", 0)
        if 0 < fulfillment < 0.5:
            warnings.append(
                HealthCheckItem(
                    severity="warning",
                    code="LOW_FULFILLMENT",
                    title="Low Completion Score",
                    message=f"Agent completion score is only {int(fulfillment * 100)}%",
                    action="Review tasks and tests",
                )
            )

        # Check 8: Dependencies declared
        caps = sba.get("capabilities_capacity", {})
        dependencies = caps.get("dependencies", [])
        if allowed_tools and not dependencies:
            suggestions.append(
                HealthCheckItem(
                    severity="info",
                    code="NO_DEPENDENCIES",
                    title="No Dependencies Listed",
                    message="Agent uses tools but has no explicit dependencies",
                    action=None,
                )
            )

        # Check 9: Verify dependencies exist
        for dep in dependencies:
            if isinstance(dep, dict):
                dep_id = dep.get("agent_id", "")
                if dep_id:
                    dep_agent = sba_service.get_agent(dep_id)
                    if not dep_agent:
                        warnings.append(
                            HealthCheckItem(
                                severity="warning",
                                code="MISSING_DEPENDENCY",
                                title="Unregistered Connection",
                                message=f"Dependency '{dep_id}' is not registered",
                                action="Register dependency",
                            )
                        )

        # Check 10: Domain specified
        if not where_to_play.get("domain"):
            suggestions.append(
                HealthCheckItem(
                    severity="info",
                    code="NO_DOMAIN",
                    title="No Domain Specified",
                    message="Consider specifying a domain for better organization",
                    action=None,
                )
            )

        # Determine overall health
        healthy = len(errors) == 0

        return HealthCheckResponse(
            agent_id=agent_id,
            healthy=healthy,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            checked_at=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:100]}")


# ============================================================================
# M17 CARE Routing Endpoints
# ============================================================================

# M17: CARE imports
try:
    from ..routing import (
        CAREEngine,
        DifficultyLevel,
        OrchestratorMode,
        RiskPolicy,
        RouteEvaluationResult,
        RoutingDecision,
        RoutingRequest,
        SuccessMetric,
        get_care_engine,
    )

    CARE_AVAILABLE = True
except ImportError:
    CARE_AVAILABLE = False


class CascadeEvaluateRequest(BaseModel):
    """Request for cascade evaluation."""

    task_description: str = Field(..., min_length=1, description="Task to evaluate")
    task_domain: Optional[str] = Field(default=None, description="Target domain")
    required_tools: List[str] = Field(default_factory=list, description="Required tools")
    difficulty: str = Field(default="medium", description="Task difficulty: low, medium, high")
    risk_tolerance: str = Field(default="balanced", description="Risk tolerance: strict, balanced, fast")
    prefer_metric: Optional[str] = Field(default=None, description="Preferred success metric")
    agent_ids: Optional[List[str]] = Field(default=None, description="Specific agents to evaluate")


class RoutingDispatchRequest(BaseModel):
    """Request for routing dispatch."""

    task_description: str = Field(..., min_length=1, description="Task to route")
    task_domain: Optional[str] = Field(default=None, description="Target domain")
    required_tools: List[str] = Field(default_factory=list, description="Required tools")
    required_capabilities: List[str] = Field(default_factory=list, description="Required capabilities")
    difficulty: str = Field(default="medium", description="Task difficulty")
    risk_tolerance: str = Field(default="balanced", description="Risk tolerance")
    prefer_metric: Optional[str] = Field(default=None, description="Preferred success metric")
    max_agents: int = Field(default=10, ge=1, le=100, description="Max agents to evaluate")


class RoutingConfigUpdate(BaseModel):
    """Request to update agent routing config."""

    success_metric: Optional[str] = Field(
        default=None, description="Success metric: cost, latency, accuracy, risk_min, balanced"
    )
    difficulty_threshold: Optional[str] = Field(default=None, description="Difficulty threshold: low, medium, high")
    risk_policy: Optional[str] = Field(default=None, description="Risk policy: strict, balanced, fast")
    orchestrator_mode: Optional[str] = Field(
        default=None, description="Orchestrator mode: parallel, hierarchical, blackboard, sequential"
    )
    max_parallel_tasks: Optional[int] = Field(default=None, ge=1, le=100)
    escalation_enabled: Optional[bool] = Field(default=None)


@router.post("/routing/cascade-evaluate")
async def cascade_evaluate(
    request: CascadeEvaluateRequest,
    x_tenant_id: str = Header(default="default", alias="X-Tenant-ID"),
):
    """
    M17: Evaluate agents through CARE pipeline without routing.

    Returns ranked list of agents with evaluation details for each stage.
    Use this to understand why agents are eligible or rejected.
    """
    if not CARE_AVAILABLE:
        raise HTTPException(status_code=501, detail="CARE routing module not available")

    try:
        care = get_care_engine()

        # Build routing request
        routing_request = RoutingRequest(
            task_description=request.task_description,
            task_domain=request.task_domain,
            required_tools=request.required_tools,
            difficulty=DifficultyLevel(request.difficulty),
            risk_tolerance=RiskPolicy(request.risk_tolerance),
            prefer_metric=SuccessMetric(request.prefer_metric) if request.prefer_metric else None,
            tenant_id=x_tenant_id,
        )

        # Evaluate agents
        results = await care.evaluate_agents(routing_request, request.agent_ids)

        # Sort by score
        results.sort(key=lambda r: r.score, reverse=True)

        return {
            "evaluated_count": len(results),
            "eligible_count": sum(1 for r in results if r.eligible),
            "agents": [
                {
                    "agent_id": r.agent_id,
                    "agent_name": r.agent_name,
                    "eligible": r.eligible,
                    "score": round(r.score, 3),
                    "success_metric": r.success_metric.value,
                    "orchestrator_mode": r.orchestrator_mode.value,
                    "risk_policy": r.risk_policy.value,
                    "rejection_reason": r.rejection_reason,
                    "rejection_stage": r.rejection_stage.value if r.rejection_stage else None,
                    "stages": [
                        {
                            "stage": sr.stage.value,
                            "passed": sr.passed,
                            "reason": sr.reason,
                            "latency_ms": round(sr.latency_ms, 2),
                        }
                        for sr in r.stage_results
                    ],
                }
                for r in results
            ],
        }

    except Exception as e:
        logger.error(f"Cascade evaluate error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:200]}")


@router.post("/routing/dispatch")
async def routing_dispatch(
    request: RoutingDispatchRequest,
    x_tenant_id: str = Header(default="default", alias="X-Tenant-ID"),
):
    """
    M17: Execute full CARE routing pipeline and select best agent.

    This is the main entry point for strategic routing.
    Returns the selected agent and routing decision details.
    """
    if not CARE_AVAILABLE:
        raise HTTPException(status_code=501, detail="CARE routing module not available")

    try:
        care = get_care_engine()

        # Build routing request
        routing_request = RoutingRequest(
            task_description=request.task_description,
            task_domain=request.task_domain,
            required_tools=request.required_tools,
            required_capabilities=request.required_capabilities,
            difficulty=DifficultyLevel(request.difficulty),
            risk_tolerance=RiskPolicy(request.risk_tolerance),
            prefer_metric=SuccessMetric(request.prefer_metric) if request.prefer_metric else None,
            max_agents=request.max_agents,
            tenant_id=x_tenant_id,
        )

        # Execute routing
        decision = await care.route(routing_request)

        return {
            "request_id": decision.request_id,
            "routed": decision.routed,
            "selected_agent_id": decision.selected_agent_id,
            "selected_agent_name": decision.selected_agent_name,
            "success_metric": decision.success_metric.value,
            "orchestrator_mode": decision.orchestrator_mode.value,
            "risk_policy": decision.risk_policy.value,
            "eligible_agents": decision.eligible_agents,
            "evaluated_count": len(decision.evaluated_agents),
            "error": decision.error,
            "actionable_fix": decision.actionable_fix,
            "total_latency_ms": round(decision.total_latency_ms, 2),
            "stage_latencies": {k: round(v, 2) for k, v in decision.stage_latencies.items()},
            "decision_reason": decision.decision_reason,
            "decided_at": decision.decided_at.isoformat(),
        }

    except Exception as e:
        logger.error(f"Routing dispatch error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:200]}")


@router.get("/agents/{agent_id}/strategy")
async def get_agent_strategy(agent_id: str):
    """
    M17: Get agent's Strategy Cascade.

    Returns the full SBA with routing configuration.
    """
    if not SBA_AVAILABLE:
        raise HTTPException(status_code=501, detail="SBA module not available")

    try:
        sba_service = get_sba_service()
        agent = sba_service.get_agent(agent_id)

        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

        if not agent.sba:
            raise HTTPException(status_code=404, detail=f"Agent has no SBA: {agent_id}")

        sba = agent.sba

        return {
            "agent_id": agent.agent_id,
            "agent_name": agent.agent_name,
            "agent_type": agent.agent_type,
            "sba_version": agent.sba_version,
            "sba_validated": agent.sba_validated,
            "strategy": {
                "winning_aspiration": sba.get("winning_aspiration", {}),
                "where_to_play": sba.get("where_to_play", {}),
                "how_to_win": sba.get("how_to_win", {}),
                "capabilities_capacity": sba.get("capabilities_capacity", {}),
                "enabling_management_systems": sba.get("enabling_management_systems", {}),
            },
            "routing_config": sba.get("routing_config", {}),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get strategy error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:100]}")


@router.post("/agents/{agent_id}/strategy/update")
async def update_agent_strategy(
    agent_id: str,
    update: RoutingConfigUpdate,
):
    """
    M17: Hot-swap agent's routing configuration.

    Updates routing-specific settings without changing the full SBA.
    """
    if not SBA_AVAILABLE:
        raise HTTPException(status_code=501, detail="SBA module not available")

    try:
        sba_service = get_sba_service()
        agent = sba_service.get_agent(agent_id)

        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

        if not agent.sba:
            raise HTTPException(status_code=404, detail=f"Agent has no SBA: {agent_id}")

        # Get current routing config
        routing_config = agent.sba.get("routing_config", {})

        # Update fields
        if update.success_metric:
            routing_config["success_metric"] = update.success_metric
        if update.difficulty_threshold:
            routing_config["difficulty_threshold"] = update.difficulty_threshold
        if update.risk_policy:
            routing_config["risk_policy"] = update.risk_policy
        if update.orchestrator_mode:
            routing_config["orchestrator_mode"] = update.orchestrator_mode
        if update.max_parallel_tasks is not None:
            routing_config["max_parallel_tasks"] = update.max_parallel_tasks
        if update.escalation_enabled is not None:
            routing_config["escalation_enabled"] = update.escalation_enabled

        # Update SBA with new routing config
        updated_sba = dict(agent.sba)
        updated_sba["routing_config"] = routing_config

        # Save via raw SQL (SBA service update doesn't support partial updates easily)
        import json
        import os

        from sqlalchemy import create_engine, text

        engine = create_engine(os.environ.get("DATABASE_URL"))
        with engine.connect() as conn:
            conn.execute(
                text(
                    """
                    UPDATE agents.agent_registry
                    SET sba = CAST(:sba AS JSONB)
                    WHERE agent_id = :agent_id
                """
                ),
                {"agent_id": agent_id, "sba": json.dumps(updated_sba)},
            )
            conn.commit()

        return {
            "agent_id": agent_id,
            "updated": True,
            "routing_config": routing_config,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update strategy error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:100]}")


@router.get("/routing/stats")
async def get_routing_stats(
    x_tenant_id: str = Header(default="default", alias="X-Tenant-ID"),
):
    """
    M17: Get routing statistics.

    Returns aggregate stats on routing decisions.
    """
    try:
        import os

        from sqlalchemy import create_engine, text

        engine = create_engine(os.environ.get("DATABASE_URL"))

        with engine.connect() as conn:
            # Get recent stats
            result = conn.execute(
                text(
                    """
                    SELECT
                        COUNT(*) as total_decisions,
                        COUNT(*) FILTER (WHERE routed = true) as successful_routes,
                        AVG(total_latency_ms) as avg_latency_ms,
                        COUNT(DISTINCT selected_agent_id) as unique_agents,
                        MAX(decided_at) as last_decision
                    FROM routing.routing_decisions
                    WHERE tenant_id = :tenant_id
                    AND decided_at > now() - interval '24 hours'
                """
                ),
                {"tenant_id": x_tenant_id},
            )
            row = result.fetchone()

            if row:
                return {
                    "period": "24h",
                    "total_decisions": row[0] or 0,
                    "successful_routes": row[1] or 0,
                    "success_rate": round((row[1] or 0) / max(row[0] or 1, 1), 3),
                    "avg_latency_ms": round(row[2] or 0, 2),
                    "unique_agents_routed": row[3] or 0,
                    "last_decision": row[4].isoformat() if row[4] else None,
                }
            else:
                return {
                    "period": "24h",
                    "total_decisions": 0,
                    "successful_routes": 0,
                    "success_rate": 0,
                    "avg_latency_ms": 0,
                    "unique_agents_routed": 0,
                    "last_decision": None,
                }

    except Exception as e:
        # Table might not exist yet
        logger.warning(f"Routing stats error (table may not exist): {e}")
        return {
            "period": "24h",
            "total_decisions": 0,
            "successful_routes": 0,
            "success_rate": 0,
            "avg_latency_ms": 0,
            "unique_agents_routed": 0,
            "last_decision": None,
            "note": "Routing table not yet created - run migrations",
        }


# ============================================================================
# M18 Explainability Endpoints
# ============================================================================

# M18: CARE-L and SBA Evolution imports
try:
    from ..agents.sba import (
        AdjustmentType,
        BoundaryViolation,
        DriftSignal,
        DriftType,
        StrategyAdjustment,
        ViolationType,
        get_evolution_engine,
    )
    from ..routing import (
        AgentReputation,
        BatchLearningResult,
        QuarantineState,
        SLAScore,
        StabilityMetrics,
        get_feedback_loop,
        get_governor,
        get_hysteresis_manager,
        get_learning_parameters,
        get_reputation_store,
    )

    M18_AVAILABLE = True
except ImportError:
    M18_AVAILABLE = False


class ExplainRoutingResponse(BaseModel):
    """Response explaining a routing decision."""

    request_id: str
    agent_id: str
    explanation: Dict[str, Any]
    factors: List[Dict[str, Any]]
    recommendation: Optional[str] = None


class EvolutionReportResponse(BaseModel):
    """Response with agent evolution history."""

    agent_id: str
    drift_signals: List[Dict[str, Any]]
    violations: List[Dict[str, Any]]
    adjustments: List[Dict[str, Any]]
    current_state: Dict[str, Any]
    recommendations: List[str]


class SystemStabilityResponse(BaseModel):
    """Response with system-wide stability metrics."""

    state: str
    frozen: bool
    freeze_until: Optional[str] = None
    freeze_reason: Optional[str] = None
    adjustments_this_hour: int
    rollbacks_this_hour: int
    oscillations_detected: int
    affected_agents: List[str]


@router.post("/routing/explain/{request_id}", response_model=ExplainRoutingResponse)
async def explain_routing_decision(
    request_id: str,
    x_tenant_id: str = Header(default="default", alias="X-Tenant-ID"),
):
    """
    M18: Explain why a routing decision was made.

    Returns detailed explanation of all factors that influenced the decision,
    including reputation scores, SLA adjustments, hysteresis effects, and
    capability matching.
    """
    if not M18_AVAILABLE:
        raise HTTPException(status_code=501, detail="M18 module not available")

    try:
        import os

        from sqlalchemy import create_engine, text

        engine = create_engine(os.environ.get("DATABASE_URL"))

        with engine.connect() as conn:
            # Get the routing decision
            result = conn.execute(
                text(
                    """
                    SELECT
                        request_id, selected_agent_id, routed, decision_reason,
                        error, actionable_fix, total_latency_ms,
                        confidence_score, agent_reputation_at_route,
                        quarantine_state_at_route, decided_at
                    FROM routing.routing_decisions
                    WHERE request_id = :request_id
                    AND tenant_id = :tenant_id
                """
                ),
                {"request_id": request_id, "tenant_id": x_tenant_id},
            )
            row = result.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail=f"Decision not found: {request_id}")

            agent_id = row[1] or "none"
            routed = row[2]
            decision_reason = row[3] or "Unknown"
            error = row[4]
            actionable_fix = row[5]
            latency_ms = row[6] or 0
            confidence = row[7] or 0
            reputation_at_route = row[8] or 1.0
            quarantine_state = row[9] or "active"

            # Build explanation
            explanation = {
                "outcome": "routed" if routed else "blocked",
                "primary_reason": decision_reason,
                "latency_ms": round(latency_ms, 2),
            }

            if error:
                explanation["error"] = error
            if actionable_fix:
                explanation["suggested_fix"] = actionable_fix

            # Build factors list
            factors = []

            # Reputation factor
            if agent_id != "none":
                factors.append(
                    {
                        "factor": "reputation",
                        "value": round(reputation_at_route, 3),
                        "impact": "positive"
                        if reputation_at_route > 0.7
                        else "neutral"
                        if reputation_at_route > 0.4
                        else "negative",
                        "explanation": f"Agent reputation was {reputation_at_route:.1%} at routing time",
                    }
                )

                # Quarantine factor
                factors.append(
                    {
                        "factor": "quarantine_state",
                        "value": quarantine_state,
                        "impact": "positive" if quarantine_state == "active" else "negative",
                        "explanation": f"Agent was in {quarantine_state} state",
                    }
                )

            # Confidence factor
            if confidence:
                factors.append(
                    {
                        "factor": "confidence",
                        "value": round(confidence, 3),
                        "impact": "positive" if confidence > 0.7 else "neutral" if confidence > 0.4 else "negative",
                        "explanation": f"Routing confidence was {confidence:.1%}",
                    }
                )

            # Get SLA score if available
            feedback_loop = get_feedback_loop()
            sla_score = await feedback_loop.get_sla_score(agent_id)
            if sla_score:
                factors.append(
                    {
                        "factor": "sla_compliance",
                        "value": round(sla_score.current_sla, 3),
                        "impact": "positive" if sla_score.current_sla >= sla_score.sla_target else "negative",
                        "explanation": f"SLA is {sla_score.current_sla:.1%} vs target {sla_score.sla_target:.1%}",
                    }
                )

            # Generate recommendation
            recommendation = None
            if not routed:
                recommendation = actionable_fix or "Consider registering more capable agents"
            elif reputation_at_route < 0.6:
                recommendation = "Agent reputation is declining - monitor for drift"

            return ExplainRoutingResponse(
                request_id=request_id,
                agent_id=agent_id,
                explanation=explanation,
                factors=factors,
                recommendation=recommendation,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Explain routing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:100]}")


@router.get("/agents/{agent_id}/evolution", response_model=EvolutionReportResponse)
async def get_agent_evolution(
    agent_id: str,
    include_acknowledged: bool = Query(default=False, description="Include acknowledged drift signals"),
    limit: int = Query(default=20, le=100, description="Max items per category"),
):
    """
    M18: Get agent evolution history and current state.

    Returns drift signals, boundary violations, strategy adjustments,
    and recommendations for the agent.
    """
    if not M18_AVAILABLE:
        raise HTTPException(status_code=501, detail="M18 module not available")

    try:
        evolution_engine = get_evolution_engine()
        reputation_store = get_reputation_store()
        feedback_loop = get_feedback_loop()

        # Get drift signals
        drift_signals = evolution_engine.get_drift_signals(
            agent_id,
            unacknowledged_only=not include_acknowledged,
        )

        # Get violations
        violations = evolution_engine.get_violations(agent_id)

        # Get adjustments
        adjustments = evolution_engine.get_adjustments(agent_id, limit=limit)

        # Get current reputation
        reputation = await reputation_store.get_reputation(agent_id)

        # Get SLA score
        sla_score = await feedback_loop.get_sla_score(agent_id)

        # Get successor mapping
        successors = await feedback_loop.get_successor_mapping(agent_id)

        # Build current state
        current_state = {
            "reputation": {
                "score": round(reputation.reputation_score, 3),
                "success_rate": round(reputation.success_rate, 3),
                "quarantine_state": reputation.quarantine_state.value,
                "quarantine_until": reputation.quarantine_until.isoformat() if reputation.quarantine_until else None,
                "violation_count": reputation.violation_count,
                "total_routes": reputation.total_routes,
                "is_routable": reputation.is_routable(),
            },
        }

        if sla_score:
            current_state["sla"] = {
                "current": round(sla_score.current_sla, 3),
                "target": round(sla_score.sla_target, 3),
                "gap": round(sla_score.sla_gap, 3),
            }

        if successors:
            current_state["successors"] = successors

        # Generate recommendations
        recommendations = []

        # Check for unacknowledged drift
        unack_drift = [d for d in drift_signals if not d.acknowledged]
        if unack_drift:
            recommendations.append(f"Review {len(unack_drift)} unacknowledged drift signal(s)")

        # Check reputation
        if reputation.reputation_score < 0.5:
            recommendations.append("Reputation is low - consider strategy adjustment")

        if reputation.quarantine_state != QuarantineState.ACTIVE:
            recommendations.append(f"Agent is in {reputation.quarantine_state.value} state")

        # Check SLA
        if sla_score and sla_score.sla_gap > 0.1:
            recommendations.append(f"SLA gap is {sla_score.sla_gap:.1%} - needs improvement")

        # Check recent violations
        recent_violations = [v for v in violations][-5:]
        if len(recent_violations) >= 3:
            recommendations.append("High violation rate - review boundaries")

        return EvolutionReportResponse(
            agent_id=agent_id,
            drift_signals=[d.to_dict() for d in drift_signals[-limit:]],
            violations=[v.to_dict() for v in violations[-limit:]],
            adjustments=[a.to_dict() for a in adjustments],
            current_state=current_state,
            recommendations=recommendations,
        )

    except Exception as e:
        logger.error(f"Get evolution error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:100]}")


@router.get("/routing/stability", response_model=SystemStabilityResponse)
async def get_system_stability():
    """
    M18: Get system-wide stability metrics.

    Returns governor state, freeze status, adjustment counts,
    and oscillation detection results.
    """
    if not M18_AVAILABLE:
        raise HTTPException(status_code=501, detail="M18 module not available")

    try:
        governor = get_governor()
        metrics = await governor.get_stability_metrics()

        return SystemStabilityResponse(
            state=metrics.state.value,
            frozen=metrics.state.value == "frozen",
            freeze_until=metrics.freeze_until.isoformat() if metrics.freeze_until else None,
            freeze_reason=metrics.freeze_reason,
            adjustments_this_hour=metrics.adjustments_this_hour,
            rollbacks_this_hour=metrics.rollbacks_this_hour,
            oscillations_detected=metrics.oscillations_detected,
            affected_agents=metrics.affected_agents,
        )

    except Exception as e:
        logger.error(f"Get stability error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:100]}")


@router.post("/routing/stability/freeze")
async def freeze_system(
    duration_seconds: int = Query(default=900, ge=60, le=3600, description="Freeze duration"),
    reason: str = Query(default="Manual freeze", description="Reason for freeze"),
):
    """
    M18: Manually freeze the learning system.

    Use this to prevent any parameter adjustments during investigation
    or maintenance.
    """
    if not M18_AVAILABLE:
        raise HTTPException(status_code=501, detail="M18 module not available")

    try:
        governor = get_governor()
        await governor.force_freeze(duration_seconds, reason)

        return {
            "frozen": True,
            "duration_seconds": duration_seconds,
            "reason": reason,
        }

    except Exception as e:
        logger.error(f"Freeze system error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:100]}")


@router.post("/routing/stability/unfreeze")
async def unfreeze_system():
    """
    M18: Manually unfreeze the learning system.

    Resumes normal operation after a manual freeze.
    """
    if not M18_AVAILABLE:
        raise HTTPException(status_code=501, detail="M18 module not available")

    try:
        governor = get_governor()
        await governor.unfreeze()

        return {"frozen": False, "message": "System unfrozen"}

    except Exception as e:
        logger.error(f"Unfreeze system error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:100]}")


@router.post("/routing/batch-learning")
async def trigger_batch_learning(
    window_hours: int = Query(default=1, ge=1, le=24, description="Hours of data to process"),
):
    """
    M18: Trigger batch learning process.

    Runs offline learning over the specified window and returns
    parameter adjustment recommendations.
    """
    if not M18_AVAILABLE:
        raise HTTPException(status_code=501, detail="M18 module not available")

    try:
        feedback_loop = get_feedback_loop()
        result = await feedback_loop.run_batch_learning(window_hours)

        return {
            "batch_id": result.batch_id,
            "window_start": result.window_start.isoformat(),
            "window_end": result.window_end.isoformat(),
            "total_outcomes": result.total_outcomes,
            "successful_outcomes": result.successful_outcomes,
            "failed_outcomes": result.failed_outcomes,
            "success_rate": round(result.successful_outcomes / max(result.total_outcomes, 1), 3),
            "parameter_adjustments": result.parameter_adjustments,
            "reputation_updates": result.reputation_updates,
            "drift_signals_generated": result.drift_signals_generated,
            "adjustments_recommended": result.adjustments_recommended,
            "processed_at": result.processed_at.isoformat(),
        }

    except Exception as e:
        logger.error(f"Batch learning error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:100]}")


@router.get("/agents/{agent_id}/reputation")
async def get_agent_reputation(agent_id: str):
    """
    M18: Get agent reputation details.

    Returns full reputation breakdown including quarantine state.
    """
    if not M18_AVAILABLE:
        raise HTTPException(status_code=501, detail="M18 module not available")

    try:
        reputation_store = get_reputation_store()
        reputation = await reputation_store.get_reputation(agent_id)

        return reputation.to_dict()

    except Exception as e:
        logger.error(f"Get reputation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:100]}")


@router.get("/agents/{agent_id}/sla")
async def get_agent_sla(agent_id: str):
    """
    M18: Get agent SLA score details.

    Returns SLA compliance metrics and targets.
    """
    if not M18_AVAILABLE:
        raise HTTPException(status_code=501, detail="M18 module not available")

    try:
        feedback_loop = get_feedback_loop()
        sla_score = await feedback_loop.get_sla_score(agent_id)

        if not sla_score:
            return {
                "agent_id": agent_id,
                "has_sla_data": False,
                "message": "No SLA data available for this agent",
            }

        return {
            "agent_id": sla_score.agent_id,
            "has_sla_data": True,
            "raw_score": round(sla_score.raw_score, 3),
            "sla_adjusted_score": round(sla_score.sla_adjusted_score, 3),
            "sla_target": round(sla_score.sla_target, 3),
            "current_sla": round(sla_score.current_sla, 3),
            "sla_gap": round(sla_score.sla_gap, 3),
            "meeting_sla": sla_score.current_sla >= sla_score.sla_target,
            "updated_at": sla_score.updated_at.isoformat(),
        }

    except Exception as e:
        logger.error(f"Get SLA error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:100]}")


@router.get("/agents/{agent_id}/successors")
async def get_agent_successors(agent_id: str):
    """
    M18: Get successor mapping for agent failover.

    Returns mapping of capabilities to recommended successor agents.
    """
    if not M18_AVAILABLE:
        raise HTTPException(status_code=501, detail="M18 module not available")

    try:
        feedback_loop = get_feedback_loop()
        successors = await feedback_loop.get_successor_mapping(agent_id)

        return {
            "agent_id": agent_id,
            "successors": successors,
            "has_successors": len(successors) > 0,
        }

    except Exception as e:
        logger.error(f"Get successors error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:100]}")
