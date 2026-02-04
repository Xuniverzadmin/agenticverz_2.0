# Layer: L2 — Product API
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Business Builder Worker API endpoints
# Callers: External clients via HTTP
# Allowed Imports: L3, L4 (via registry)
# Forbidden Imports: L1, L5, L6 (must route through L4)
# Reference: PIN-258 Phase F-3 Workers Cluster, PIN-520 Phase 1
# Contract: PHASE_F_FIX_DESIGN (F-W-RULE-1 to F-W-RULE-5)
#
# GOVERNANCE NOTE (F-W-RULE-4):
# This L2 module must ONLY call the L3 workers_adapter.
# Direct L5 worker imports are FORBIDDEN.
#
# F-W-RULE-1: No semantic changes - all logic stays where it is.
# F-W-RULE-4: L3 Adapter Is the Only Entry - only workers_adapter.py.
#
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
import os
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select

# Absolute imports (import hygiene - no relative imports)
from app.auth import verify_api_key
from app.auth.authority import AuthorityResult, emit_authority_audit, require_replay_execute

# Phase 5B: Policy Pre-Check Integration
from app.contracts.decisions import emit_policy_precheck_decision
from app.db import CostBudget, get_async_session

# PIN-520 Phase 1: Route L5/L6 through L4 registry
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
)
from app.models.tenant import WorkerRun
from app.hoc.cus.policies.L5_engines.engine import PolicyEngine
from app.schemas.response import wrap_dict
# V2.0.0 - hoc_spine drivers
from app.hoc.cus.hoc_spine.drivers.worker_write_driver_async import WorkerWriteServiceAsync

logger = logging.getLogger("nova.api.workers")


# =============================================================================
# L3 Adapter Access (Phase F-3: F-W-RULE-4)
# =============================================================================


def _get_workers_adapter():
    """
    Get the L3 workers adapter.

    This is the ONLY way L2 should access worker functionality.
    F-W-RULE-4: L3 Adapter Is the Only Entry.
    """
    from app.adapters.workers_adapter import get_workers_adapter

    return get_workers_adapter()


def _calculate_cost_cents(model: str, input_tokens: int, output_tokens: int) -> int:
    """
    Calculate LLM cost in cents via L3 adapter.

    Phase F-3: This replaces the direct L5 import.
    """
    adapter = _get_workers_adapter()
    return adapter.calculate_cost_cents(model, input_tokens, output_tokens)


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
    # Phase 5B: Policy pre-check posture
    policy_posture: str = Field(
        default="advisory",
        description="Policy pre-check mode: 'strict' (block on violation) or 'advisory' (warn only)",
    )
    tenant_id: Optional[str] = Field(default="default", description="Tenant ID for policy evaluation")


class PolicyStatusModel(BaseModel):
    """Phase 5B: Policy pre-check status for PRE-RUN declaration."""

    posture: str = "advisory"  # strict or advisory
    checked: bool = False
    passed: bool = True
    violations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    service_available: bool = True


class WorkerRunResponse(BaseModel):
    """Response from worker execution."""

    run_id: str
    success: bool
    status: str  # queued, running, completed, failed, blocked
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
    # Phase 5B: Policy pre-check status
    policy_status: Optional[PolicyStatusModel] = None


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


class RunRetryResponse(BaseModel):
    """Response for run retry - Phase-2.5."""

    id: str
    parent_run_id: str
    status: str


# =============================================================================
# PostgreSQL Run Storage (P0-005 Fix: Real persistence, not in-memory)
# =============================================================================

# Verification mode: If enabled, raise error if persistence fails
VERIFICATION_MODE = os.getenv("AOS_VERIFICATION_MODE", "false").lower() == "true"

# Cost enforcement: If enabled, runs with budgets MUST have cost_cents
COST_ENFORCEMENT_ENABLED = os.getenv("AOS_COST_ENFORCEMENT", "true").lower() == "true"


async def _store_run(run_id: str, data: Dict[str, Any], tenant_id: str = "default") -> None:
    """
    Persist a run to PostgreSQL.

    P0-005 Fix: Database is the source of truth, not memory.
    """
    async with get_async_session() as session:
        # Phase 2B: Use write service for DB operations
        write_service = WorkerWriteServiceAsync(session)
        await write_service.upsert_worker_run(run_id, tenant_id, data)
        await write_service.commit()

        # Verification mode guardrail
        if VERIFICATION_MODE:
            # Verify the write succeeded
            verify_result = await session.execute(select(WorkerRun).where(WorkerRun.id == run_id))
            verified = verify_result.scalar_one_or_none()
            if not verified:
                raise RuntimeError(f"PERSISTENCE_VIOLATION: Run {run_id} completed without DB commit")

        # P0-006 Fix: Cost invariant enforcement
        # If run completed with tokens but no cost_cents, that's a violation
        if COST_ENFORCEMENT_ENABLED and data.get("status") in ("completed", "failed"):
            has_tokens = (data.get("total_tokens_used") or 0) > 0
            has_cost = data.get("cost_cents") is not None
            if has_tokens and not has_cost:
                error_msg = (
                    f"COST_INVARIANT_VIOLATION: Run {run_id} completed with "
                    f"{data.get('total_tokens_used')} tokens but cost_cents=NULL. "
                    "Cost must be computed and stored with the run."
                )
                logger.error(error_msg)
                # TODO (POST-BETA): Missing cost must fail hard once billing is enforced.
                # Currently only crashes in VERIFICATION_MODE to avoid breaking production
                # during verification phase. After billing goes live, this should always raise.
                if VERIFICATION_MODE:
                    raise RuntimeError(error_msg)

        logger.info("run_persisted", extra={"run_id": run_id, "status": data.get("status")})


async def _insert_cost_record(
    run_id: str,
    tenant_id: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost_cents: int,
) -> None:
    """
    Insert a cost record for a worker run.

    P0-006 Fix: Cost must be recorded as part of worker execution.
    This creates the authoritative cost fact that S2 requires.
    """
    async with get_async_session() as session:
        # Phase 2B: Use write service for DB operations
        write_service = WorkerWriteServiceAsync(session)
        await write_service.insert_cost_record(
            run_id=run_id,
            tenant_id=tenant_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_cents=cost_cents,
        )
        await write_service.commit()
        logger.info(
            "cost_record_inserted",
            extra={
                "run_id": run_id,
                "tenant_id": tenant_id,
                "cost_cents": cost_cents,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
        )


async def _check_and_emit_cost_advisory(
    run_id: str,
    tenant_id: str,
    cost_cents: int,
) -> Dict[str, Any]:
    """
    Check if cost threshold is crossed and emit advisory if needed.

    S2 Advisory Invariant:
    - If threshold crossed AND hard_limit_enabled=false → exactly 1 advisory
    - If threshold NOT crossed → exactly 0 advisories
    - If hard_limit_enabled=true → this is an incident, not advisory (out of S2 scope)

    Returns dict with:
    - threshold_crossed: bool
    - advisory_emitted: bool
    - advisory_id: str | None
    - budget_id: str | None
    """
    result = {
        "threshold_crossed": False,
        "advisory_emitted": False,
        "advisory_id": None,
        "budget_id": None,
        "daily_spend_cents": 0,
        "daily_limit_cents": None,
    }

    async with get_async_session() as session:
        # Get tenant's active budget
        budget_result = await session.execute(
            select(CostBudget).where(
                CostBudget.tenant_id == tenant_id,
                CostBudget.is_active == True,
                CostBudget.budget_type == "tenant",
            )
        )
        budget = budget_result.scalar_one_or_none()

        if not budget or not budget.daily_limit_cents:
            logger.info(
                "no_budget_configured",
                extra={"run_id": run_id, "tenant_id": tenant_id},
            )
            return result

        result["budget_id"] = budget.id
        result["daily_limit_cents"] = budget.daily_limit_cents

        # Calculate today's total spend (including this run)

        from sqlalchemy import text

        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        spend_result = await session.execute(
            text(
                """
                SELECT COALESCE(SUM(cost_cents), 0)
                FROM cost_records
                WHERE tenant_id = :tenant_id
                AND created_at >= :today_start
            """
            ),
            {"tenant_id": tenant_id, "today_start": today_start},
        )
        daily_spend = int(spend_result.scalar() or 0)
        result["daily_spend_cents"] = daily_spend

        # Check if threshold crossed
        warn_threshold = budget.daily_limit_cents * (budget.warn_threshold_pct / 100.0)
        threshold_crossed = daily_spend > warn_threshold
        result["threshold_crossed"] = threshold_crossed

        if threshold_crossed and not budget.hard_limit_enabled:
            # Idempotency check: only emit if no advisory exists for this run
            existing_check = await session.execute(
                text(
                    """
                    SELECT id FROM cost_anomalies
                    WHERE anomaly_type = 'BUDGET_WARNING'
                    AND metadata->>'run_id' = :run_id
                """
                ),
                {"run_id": run_id},
            )
            existing = existing_check.scalar_one_or_none()

            if existing:
                # Advisory already exists for this run (idempotent)
                result["advisory_emitted"] = False
                result["advisory_id"] = existing
                logger.info(
                    "cost_advisory_already_exists",
                    extra={"run_id": run_id, "advisory_id": existing},
                )
            else:
                # Emit advisory (BUDGET_WARNING, not incident)
                # Budget snapshot: capture budget-at-run-time for audit trail
                # This ensures historical analysis uses the budget that was active during the run
                budget_snapshot = {
                    "budget_id": budget.id,
                    "daily_limit_cents": budget.daily_limit_cents,
                    "warn_threshold_pct": budget.warn_threshold_pct,
                    "hard_limit_enabled": budget.hard_limit_enabled,
                }

                # Phase 2B: Use write service for DB operations
                write_service = WorkerWriteServiceAsync(session)
                advisory = await write_service.insert_cost_advisory(
                    tenant_id=tenant_id,
                    run_id=run_id,
                    daily_spend=daily_spend,
                    warn_threshold=warn_threshold,
                    budget_snapshot=budget_snapshot,
                )
                await write_service.commit()

                result["advisory_emitted"] = True
                result["advisory_id"] = advisory.id

                logger.info(
                    "cost_advisory_emitted",
                    extra={
                        "run_id": run_id,
                        "advisory_id": advisory.id,
                        "daily_spend": daily_spend,
                        "threshold": warn_threshold,
                        "budget_snapshot": budget_snapshot,
                    },
                )

        return result


async def _verify_advisory_invariant(
    run_id: str,
    tenant_id: str,
    advisory_result: Dict[str, Any],
) -> None:
    """
    Verify advisory emission invariant in VERIFICATION_MODE.

    S2 Invariant:
    - If threshold_crossed=true AND hard_limit_enabled=false → advisory_count must be 1
    - If threshold_crossed=false → advisory_count must be 0

    Raises RuntimeError if invariant violated.
    """
    if not VERIFICATION_MODE:
        return

    async with get_async_session() as session:
        # Count advisories for this run
        from sqlalchemy import text

        count_result = await session.execute(
            text(
                """
                SELECT COUNT(*)
                FROM cost_anomalies
                WHERE tenant_id = :tenant_id
                AND anomaly_type = 'BUDGET_WARNING'
                AND metadata->>'run_id' = :run_id
            """
            ),
            {"tenant_id": tenant_id, "run_id": run_id},
        )
        advisory_count = int(count_result.scalar() or 0)

        threshold_crossed = advisory_result["threshold_crossed"]

        if threshold_crossed and advisory_count != 1:
            raise RuntimeError(
                f"COST_ADVISORY_INVARIANT_VIOLATION: Run {run_id} crossed threshold "
                f"but advisory_count={advisory_count} (expected 1). "
                f"Daily spend: {advisory_result['daily_spend_cents']}¢, "
                f"Threshold: {advisory_result['daily_limit_cents']}¢"
            )

        if not threshold_crossed and advisory_count != 0:
            raise RuntimeError(
                f"FALSE_COST_ADVISORY: Run {run_id} did NOT cross threshold "
                f"but advisory_count={advisory_count} (expected 0). "
                f"Daily spend: {advisory_result['daily_spend_cents']}¢, "
                f"Threshold: {advisory_result['daily_limit_cents']}¢"
            )

        logger.info(
            "advisory_invariant_verified",
            extra={
                "run_id": run_id,
                "threshold_crossed": threshold_crossed,
                "advisory_count": advisory_count,
            },
        )


async def _get_run(run_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a run from PostgreSQL.

    Returns dict format matching WorkerRunResponse for API compatibility.
    """
    async with get_async_session() as session:
        result = await session.execute(select(WorkerRun).where(WorkerRun.id == run_id))
        run = result.scalar_one_or_none()

        if not run:
            return None

        return wrap_dict({
            "run_id": run.id,
            "task": run.task,
            "status": run.status,
            "success": run.success,
            "error": run.error,
            "artifacts": json.loads(run.output_json) if run.output_json else None,
            "replay_token": json.loads(run.replay_token_json) if run.replay_token_json else None,
            "total_tokens_used": run.total_tokens or 0,
            "total_latency_ms": float(run.total_latency_ms) if run.total_latency_ms else 0.0,
            "policy_violations": [],  # Not stored in detail
            "recovery_log": [],  # Not stored in detail
            "drift_metrics": {},
            "execution_trace": [],
            "routing_decisions": [],
            "cost_report": None,
            "created_at": run.created_at.isoformat() if run.created_at else None,
        })


async def _list_runs(limit: int = 20, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List recent runs from PostgreSQL.
    """
    async with get_async_session() as session:
        query = select(WorkerRun).order_by(WorkerRun.created_at.desc()).limit(limit)
        if tenant_id:
            query = query.where(WorkerRun.tenant_id == tenant_id)

        result = await session.execute(query)
        runs = result.scalars().all()

        return [
            {
                "run_id": run.id,
                "task": run.task,
                "status": run.status,
                "success": run.success,
                "created_at": run.created_at.isoformat() if run.created_at else "",
                "total_latency_ms": float(run.total_latency_ms) if run.total_latency_ms else None,
            }
            for run in runs
        ]


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
    """
    Convert API request to BrandSchema via L3 adapter.

    Phase F-3: This replaces the direct L5 schema import.
    F-W-RULE-4: L3 Adapter Is the Only Entry.
    """
    adapter = _get_workers_adapter()
    return adapter.convert_brand_request(brand_req)


async def _execute_worker_async(run_id: str, request: WorkerRunRequest) -> None:
    """
    Execute worker in background and update run store.

    Phase F-3: Uses L3 adapter instead of direct L5 worker import.
    F-W-RULE-4: L3 Adapter Is the Only Entry.
    """
    # AUTH_DESIGN.md: AUTH-TENANT-005 - No fallback tenant. Missing tenant is hard failure.
    if not request.tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    tenant_id = request.tenant_id
    adapter = _get_workers_adapter()
    try:
        await _store_run(
            run_id,
            {
                "run_id": run_id,
                "task": request.task,
                "status": "running",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            tenant_id=tenant_id,
        )

        # Convert brand if provided
        brand = None
        if request.brand:
            brand = _brand_request_to_schema(request.brand)

        # Execute via L3 adapter (F-W-RULE-4)
        result = await adapter.execute_worker(
            task=request.task,
            brand=brand,
            budget=request.budget,
            strict_mode=request.strict_mode,
            depth=request.depth,
            run_id=run_id,
        )

        # P0-006 Fix: Compute cost from tokens
        # =================================================================
        # COST TRUTH MODEL v0 (HEURISTIC) — See PIN-194
        # =================================================================
        # Input/output token split is estimated at 30/70 for verification only.
        # This is NOT a billing-grade model.
        # Future work: Wire actual input/output token counts from LLM responses.
        # =================================================================
        total_tokens = result.total_tokens_used or 0
        input_tokens = int(total_tokens * 0.3)
        output_tokens = total_tokens - input_tokens
        model = "claude-sonnet-4-20250514"  # Default model
        cost_cents = _calculate_cost_cents(model, input_tokens, output_tokens)

        logger.info(
            "cost_computed",
            extra={
                "run_id": run_id,
                "total_tokens": total_tokens,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_cents": cost_cents,
            },
        )

        # P0-006 Fix: Insert cost record (creates authoritative cost fact)
        if total_tokens > 0:
            await _insert_cost_record(
                run_id=run_id,
                tenant_id=tenant_id,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_cents=cost_cents,
            )

            # S2 Advisory Invariant: Check threshold and emit advisory if needed
            advisory_result = await _check_and_emit_cost_advisory(
                run_id=run_id,
                tenant_id=tenant_id,
                cost_cents=cost_cents,
            )

            # Verify advisory invariant in VERIFICATION_MODE
            await _verify_advisory_invariant(
                run_id=run_id,
                tenant_id=tenant_id,
                advisory_result=advisory_result,
            )

        # Update stored run (now includes cost_cents)
        await _store_run(
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
                "cost_cents": cost_cents,  # P0-006: Store cost with run
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            tenant_id=tenant_id,
        )

    except Exception as e:
        logger.exception(f"Worker execution failed for run {run_id}")
        await _store_run(
            run_id,
            {
                "run_id": run_id,
                "task": request.task,
                "status": "failed",
                "success": False,
                "error": str(e),
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            tenant_id=tenant_id,
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
    request_id = run_id  # Use run_id as request_id for causal binding

    logger.info(
        "worker_run_requested",
        extra={
            "run_id": run_id,
            "task": request.task[:100],
            "has_brand": request.brand is not None,
            "async_mode": request.async_mode,
            "policy_posture": request.policy_posture,
        },
    )

    # =========================================================================
    # Phase 5B: Policy Pre-Check
    # =========================================================================
    # Perform pre-check BEFORE run creation. Emit decision IFF strict mode
    # and (failed OR unavailable).
    policy_status = PolicyStatusModel(
        posture=request.policy_posture,
        checked=True,
    )

    try:
        policy_engine = PolicyEngine()
        pre_check_result = await policy_engine.pre_check(
            request_id=request_id,
            agent_id="business-builder",
            goal=request.task,
            tenant_id=request.tenant_id  # Validated by caller (AUTH_DESIGN.md: AUTH-TENANT-005),
        )

        policy_status.passed = pre_check_result["passed"]
        policy_status.service_available = pre_check_result["service_available"]
        policy_status.violations = pre_check_result.get("violations", [])

        # If not passed, put violations in warnings (advisory) or block (strict)
        if not pre_check_result["passed"]:
            policy_status.warnings = pre_check_result.get("violations", [])

        logger.info(
            "policy_precheck_completed",
            extra={
                "request_id": request_id,
                "posture": request.policy_posture,
                "passed": policy_status.passed,
                "service_available": policy_status.service_available,
                "violations_count": len(policy_status.violations),
            },
        )

    except Exception as e:
        logger.warning(f"Policy pre-check failed: {e}")
        policy_status.service_available = False
        policy_status.passed = False

    # Emit decision IFF strict mode AND (failed OR unavailable)
    # This follows the frozen emission rule from PIN-173
    emit_policy_precheck_decision(
        request_id=request_id,
        posture=request.policy_posture,
        passed=policy_status.passed,
        service_available=policy_status.service_available,
        violations=policy_status.violations,
        tenant_id=request.tenant_id  # Validated by caller (AUTH_DESIGN.md: AUTH-TENANT-005),
    )

    # Block run if strict mode and pre-check failed or service unavailable
    if request.policy_posture == "strict" and (not policy_status.passed or not policy_status.service_available):
        logger.warning(
            "run_blocked_by_policy_precheck",
            extra={
                "request_id": request_id,
                "passed": policy_status.passed,
                "service_available": policy_status.service_available,
            },
        )
        # Return blocked response - NO run created
        return WorkerRunResponse(
            run_id=run_id,
            success=False,
            status="blocked",
            error="Policy pre-check failed (strict mode)"
            if policy_status.passed is False
            else "Policy service unavailable (strict mode)",
            policy_status=policy_status,
        )
    # =========================================================================
    # End Phase 5B Pre-Check
    # =========================================================================

    # AUTH_DESIGN.md: AUTH-TENANT-005 - No fallback tenant. Missing tenant is hard failure.
    if not request.tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    tenant_id = request.tenant_id

    if request.async_mode:
        # Queue for background execution
        await _store_run(
            run_id,
            {
                "run_id": run_id,
                "task": request.task,
                "status": "queued",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            tenant_id=tenant_id,
        )

        # Evidence Architecture v1.0: Capture environment evidence at run creation (H)
        # PIN-520 Phase 1: Route capture_driver through L4 registry
        trace_id = f"trace_{run_id}"  # Matches pg_store.start_trace() pattern
        registry = get_operation_registry()
        capture_ctx = OperationContext(
            session=None,  # capture doesn't need session
            tenant_id=tenant_id,
            params={
                "method": "capture_environment",
                "run_id": run_id,
                "trace_id": trace_id,
                "source": "SDK",
                "is_synthetic": False,
                "sdk_mode": "api",
                "execution_environment": os.getenv("ENV", "prod"),
                "telemetry_delivery_status": "connected",
                "capture_confidence_score": 1.0,
            },
        )
        await registry.execute("logs.capture", capture_ctx)

        background_tasks.add_task(_execute_worker_async, run_id, request)

        return WorkerRunResponse(
            run_id=run_id,
            success=False,  # Not yet complete
            status="queued",
            policy_status=policy_status,  # Phase 5B: Include pre-check result
        )

    # Synchronous execution via L3 adapter (Phase F-3: F-W-RULE-4)
    adapter = _get_workers_adapter()
    try:
        # Convert brand if provided
        brand = None
        if request.brand:
            brand = _brand_request_to_schema(request.brand)

        # Execute via L3 adapter (F-W-RULE-4)
        result = await adapter.execute_worker(
            task=request.task,
            brand=brand,
            budget=request.budget,
            strict_mode=request.strict_mode,
            depth=request.depth,
            run_id=run_id,
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
            policy_status=policy_status,  # Phase 5B: Include pre-check result
        )

        # Store the run
        await _store_run(run_id, response.model_dump(), tenant_id=tenant_id)

        return wrap_dict(response.model_dump())

    except Exception as e:
        logger.exception("worker_run_failed")
        raise HTTPException(status_code=500, detail=f"Worker execution failed: {str(e)}")


@router.post("/replay", response_model=WorkerRunResponse, status_code=202)
async def replay_execution_endpoint(
    request: ReplayRequest,
    auth: AuthorityResult = Depends(require_replay_execute),
):
    """
    Replay a previous execution using Golden Replay (M4).

    Deterministically reproduces the same outputs given the same replay token.

    Phase F-3: Uses L3 adapter instead of direct L5 worker import.
    F-W-RULE-4: L3 Adapter Is the Only Entry.
    """
    # Emit authority audit for capability access
    await emit_authority_audit(auth, "replay", subject_id=request.replay_token)

    run_id = str(uuid.uuid4())
    adapter = _get_workers_adapter()

    try:
        # Replay via L3 adapter (F-W-RULE-4)
        result = await adapter.replay_execution(
            replay_token=request.replay_token,
            run_id=run_id,
        )

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
    run = await _get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return WorkerRunResponse(**run)


@router.get("/runs", response_model=RunListResponse)
async def list_runs(
    limit: int = 20,
    tenant_id: Optional[str] = None,
    _: str = Depends(verify_api_key),
):
    """
    List recent worker runs.

    Returns summary information for recent executions.
    Optionally filter by tenant_id.
    """
    runs = await _list_runs(limit, tenant_id=tenant_id)

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


@router.post("/runs/{run_id}/retry", response_model=RunRetryResponse, status_code=201)
async def retry_run(
    run_id: str,
    _: str = Depends(verify_api_key),
):
    """
    Retry a completed or failed run - Phase-2.5.

    Creates a new run linked to the original via parent_run_id.
    This is a lifecycle event, not execution - the run is queued only.

    Rules:
    - Original run must be COMPLETED or FAILED
    - No agent execution triggered
    - DB write only, deterministic
    """
    from app.db import Run

    async with get_async_session() as session:
        # Get original run
        result = await session.execute(
            select(Run).where(Run.id == run_id)
        )
        original = result.scalar_one_or_none()

        if not original:
            raise HTTPException(status_code=404, detail="Run not found")

        # Validate status - only completed or failed runs can be retried
        valid_statuses = ["completed", "failed", "succeeded"]
        if original.status.lower() not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot retry run with status '{original.status}'. Must be completed or failed."
            )

        # Create new run linked to original
        # Note: Use naive datetime for asyncpg compatibility
        from datetime import datetime as dt
        new_run = Run(
            agent_id=original.agent_id,
            goal=original.goal,
            status="queued",
            parent_run_id=original.id,
            tenant_id=original.tenant_id,
            max_attempts=original.max_attempts,
            priority=original.priority,
            created_at=dt.utcnow(),
        )

        session.add(new_run)
        await session.commit()
        await session.refresh(new_run)

        # Audit log
        logger.info(
            f"run_retry_requested: original={run_id} new={new_run.id} status=queued"
        )

        return RunRetryResponse(
            id=new_run.id,
            parent_run_id=run_id,
            status="queued",
        )


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
    PIN-520 Phase 1: Route L5 health checks through L4 registry.
    """
    moat_status = {}

    # Check M17 CARE (not in HOC domain, keep direct import)
    try:
        from app.routing.care import get_care_engine

        get_care_engine()
        moat_status["m17_care"] = "available"
    except ImportError:
        moat_status["m17_care"] = "unavailable"

    # PIN-520 Phase 1: Route policies L5 health checks through L4 registry
    # Check M20 Policy, M9 Failure Catalog, M10 Recovery via registry
    try:
        registry = get_operation_registry()
        health_ctx = OperationContext(
            session=None,
            tenant_id="default",
            params={},
        )
        health_result = await registry.execute("policies.health", health_ctx)
        if health_result.success:
            moat_status.update(health_result.data)
        else:
            moat_status["m20_policy"] = "unavailable"
            moat_status["m9_failure_catalog"] = "unavailable"
            moat_status["m10_recovery"] = "unavailable"
    except Exception:
        moat_status["m20_policy"] = "unavailable"
        moat_status["m9_failure_catalog"] = "unavailable"
        moat_status["m10_recovery"] = "unavailable"

    # Get count from DB
    run_count = 0
    try:
        async with get_async_session() as session:
            from sqlalchemy import func

            result = await session.execute(select(func.count()).select_from(WorkerRun))
            run_count = result.scalar() or 0
    except Exception:
        pass

    return wrap_dict({
        "status": "healthy",
        "version": "0.4",  # v0.4: P0-005 fix - PostgreSQL persistence (no in-memory)
        "moats": moat_status,
        "runs_in_db": run_count,
        "persistence": "postgresql",  # Explicit indicator of persistence backend
    })


@router.delete("/runs/{run_id}")
async def delete_run(
    run_id: str,
    _: str = Depends(verify_api_key),
):
    """
    Delete a run from storage.

    Note: In production, this would require admin privileges.
    """
    async with get_async_session() as session:
        # Phase 2B: Use write service for DB operations
        write_service = WorkerWriteServiceAsync(session)
        run = await write_service.get_worker_run(run_id)
        if run:
            await write_service.delete_worker_run(run)
            await write_service.commit()
            return wrap_dict({"deleted": True, "run_id": run_id})

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
    run = await _get_run(run_id)
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
    return wrap_dict({
        "run_id": run_id,
        "events": events,
        "count": len(events),
    })


# =============================================================================
# Enhanced Worker Execution with Event Emission
# =============================================================================


async def _execute_worker_with_events(run_id: str, request: WorkerRunRequest) -> None:
    """
    Execute worker with REAL event emission from worker itself.

    v0.4: Worker is source of truth. PostgreSQL persistence. No in-memory storage.

    Phase F-3: Uses L3 adapter instead of direct L5 worker import.
    F-W-RULE-4: L3 Adapter Is the Only Entry.
    """
    event_bus = get_event_bus()
    # AUTH_DESIGN.md: AUTH-TENANT-005 - No fallback tenant. Missing tenant is hard failure.
    if not request.tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    tenant_id = request.tenant_id
    adapter = _get_workers_adapter()

    try:
        await _store_run(
            run_id,
            {
                "run_id": run_id,
                "task": request.task,
                "status": "running",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            tenant_id=tenant_id,
        )

        # Convert brand if provided
        brand = None
        if request.brand:
            brand = _brand_request_to_schema(request.brand)

        # Execute via L3 adapter with event bus (F-W-RULE-4)
        # Worker emits its own events - NO SIMULATION
        result = await adapter.execute_worker(
            task=request.task,
            brand=brand,
            budget=request.budget,
            strict_mode=request.strict_mode,
            depth=request.depth,
            run_id=run_id,
            event_bus=event_bus,
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
        await _store_run(run_id, final_data, tenant_id=tenant_id)

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

        await _store_run(
            run_id,
            {
                "run_id": run_id,
                "task": request.task,
                "status": "failed",
                "success": False,
                "error": str(e),
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            tenant_id=tenant_id,
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

    # AUTH_DESIGN.md: AUTH-TENANT-005 - No fallback tenant. Missing tenant is hard failure.
    if not request.tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required")
    tenant_id = request.tenant_id

    logger.info(
        "worker_streaming_run_requested",
        extra={
            "run_id": run_id,
            "task": request.task[:100],
        },
    )

    # Initialize run
    await _store_run(
        run_id,
        {
            "run_id": run_id,
            "task": request.task,
            "status": "queued",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        tenant_id=tenant_id,
    )

    # Queue for background execution with events
    background_tasks.add_task(_execute_worker_with_events, run_id, request)

    return WorkerRunResponse(
        run_id=run_id,
        success=False,
        status="queued",
    )
