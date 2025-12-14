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

from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel, Field

from ..agents.services.job_service import (
    JobService, JobConfig, get_job_service
)
from ..agents.services.worker_service import (
    WorkerService, get_worker_service
)
from ..agents.services.blackboard_service import (
    BlackboardService, get_blackboard_service
)
from ..agents.services.message_service import (
    MessageService, get_message_service
)
from ..agents.services.registry_service import (
    RegistryService, get_registry_service
)
from ..agents.services.credit_service import (
    CreditService, get_credit_service, CREDIT_COSTS
)
from ..agents.skills.agent_invoke import AgentInvokeSkill

# M15.1: SBA imports
try:
    from ..agents.sba import (
        SBAService, SBASchema, validate_sba, get_sba_service,
        generate_sba_from_agent, SBAValidationResult,
        # M15.1.1: Version negotiation
        get_version_info, negotiate_version, SBAVersionError,
        SUPPORTED_SBA_VERSIONS, check_version_deprecated,
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
        has_budget, budget_reason = credit_service.check_credits(
            x_tenant_id, estimated_total
        )

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
                }
            }
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
