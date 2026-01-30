# Layer: L2 — Product APIs
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Limit simulation endpoint (PIN-LIM-04)
# Callers: SDK, Worker runtime, Customer Console
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: PIN-LIM-04

"""
Limit Simulation API (PIN-LIM-04)

Pre-execution limit check endpoint.

Allows callers to test whether an execution would be permitted
before actually running it.

Endpoint:
    POST /api/v1/limits/simulate

Returns:
    - decision: ALLOW | BLOCK | WARN
    - blocking_limit_id (if blocked)
    - headroom (remaining capacity)
    - warnings (soft limit warnings)
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.gateway_middleware import get_auth_context
from app.db import get_async_session_dep
from app.hoc.cus.controls.L5_schemas.simulation import (
    LimitSimulationRequest,
    LimitSimulationResponse,
    SimulationDecision,
)
from app.hoc.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
)


router = APIRouter(prefix="/limits", tags=["limits"])


# =============================================================================
# Request/Response Wrappers
# =============================================================================


class SimulateRequest(BaseModel):
    """Wrapper for simulation request."""

    estimated_tokens: int = Field(ge=0, description="Estimated tokens to consume")
    estimated_cost_cents: int = Field(default=0, ge=0, description="Estimated cost in cents")
    run_count: int = Field(default=1, ge=1, description="Number of runs to simulate")
    concurrency_delta: int = Field(default=1, ge=0, description="Concurrency increase")
    worker_id: str | None = Field(default=None, description="Optional worker ID")
    feature_id: str | None = Field(default=None, description="Optional feature ID")
    user_id: str | None = Field(default=None, description="Optional user ID")
    project_id: str | None = Field(default=None, description="Optional project ID")


class SimulateResponse(BaseModel):
    """Simulation response with decision and details."""

    decision: str  # ALLOW, BLOCK, WARN
    allowed: bool
    blocking_limit_id: str | None = None
    blocking_limit_type: str | None = None
    message_code: str | None = None
    warnings: list[str] = []
    headroom: dict[str, int] | None = None
    checks_performed: int = 0
    overrides_applied: list[str] = []


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "/simulate",
    response_model=SimulateResponse,
    summary="Simulate execution against limits",
    description="Pre-check whether an execution would be permitted by current limits.",
)
async def simulate_execution(
    request: Request,
    body: SimulateRequest,
    session: AsyncSession = Depends(get_async_session_dep),
) -> SimulateResponse:
    """
    Simulate an execution against all limits.

    This endpoint allows callers to check whether an execution would be
    permitted BEFORE actually running it. Useful for:
    - SDK pre-checks
    - UI feedback on resource availability
    - Worker admission control
    """
    auth_context = get_auth_context(request)
    tenant_id = auth_context.tenant_id

    registry = get_operation_registry()
    op = await registry.execute(
        "policies.simulate",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={
                "method": "simulate",
                "estimated_tokens": body.estimated_tokens,
                "estimated_cost_cents": body.estimated_cost_cents,
                "run_count": body.run_count,
                "concurrency_delta": body.concurrency_delta,
                "worker_id": body.worker_id,
                "feature_id": body.feature_id,
                "user_id": body.user_id,
                "project_id": body.project_id,
            },
        ),
    )

    if not op.success:
        error_code = getattr(op, "error_code", None) or ""
        if error_code == "TENANT_NOT_FOUND":
            raise HTTPException(
                status_code=404,
                detail={"error": "tenant_not_found", "message": op.error},
            )
        elif error_code == "SIMULATION_ERROR":
            raise HTTPException(
                status_code=400,
                detail={"error": "simulation_error", "message": op.error},
            )
        else:
            raise HTTPException(
                status_code=500,
                detail={"error": "operation_failed", "message": op.error},
            )

    result = op.data

    # Convert to response
    return SimulateResponse(
        decision=result.decision.value,
        allowed=result.decision == SimulationDecision.ALLOW,
        blocking_limit_id=result.blocking_limit_id,
        blocking_limit_type=result.blocking_limit_type,
        message_code=result.blocking_message_code.value if result.blocking_message_code else None,
        warnings=result.warnings,
        headroom={
            "tokens_remaining": result.headroom.tokens if result.headroom else 0,
            "runs_remaining": result.headroom.runs if result.headroom else 0,
            "cost_remaining_cents": result.headroom.cost_cents if result.headroom else 0,
        } if result.headroom else None,
        checks_performed=len(result.checks),
        overrides_applied=result.overrides_applied,
    )
