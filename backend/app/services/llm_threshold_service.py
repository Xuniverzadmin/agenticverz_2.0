# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: api | worker
#   Execution: sync
# Role: LLM run threshold resolution and evaluation
# Callers: api/activity/*, worker/runtime/*
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: Policies → Limits → Thresholds → Set Params panel
#
# =============================================================================
# SIGNAL EMISSION ARCHITECTURE
# =============================================================================
#
# This service emits threshold signals to TWO destinations:
#
# 1. ops_events table (via EventEmitter)
#    - PURPOSE: Founder Console operational monitoring
#    - CONSUMER: api/ops.py endpoints (protected by verify_fops_token)
#    - NOTE: NOT accessible to Customer Console
#
# 2. runs table (via RunSignalService)
#    - PURPOSE: Customer Console Activity panels
#    - CONSUMER: v_runs_o2 -> api/activity.py -> Customer Console
#    - Updates: risk_level column
#
# Both emissions happen on threshold evaluation. They serve different audiences.
#
# Signal Audience Map:
# +-----------------+-------------------+---------------------+
# | Signal Type     | Founder Console   | Customer Console    |
# +-----------------+-------------------+---------------------+
# | Threshold       | ops_events        | runs.risk_level     |
# +-----------------+-------------------+---------------------+
#
# =============================================================================

"""
LLM Threshold Service

Provides:
- ThresholdParams: Validated threshold configuration
- LLMRunThresholdResolver: Resolves effective params from Policy → Limit chain
- LLMRunEvaluator: Evaluates runs against thresholds, emits signals
- emit_and_persist_threshold_signal: Dual emit to Founder AND Customer consoles

This is the governance layer that enables:
- ACT-LLM-LIVE-O2: "Surface live runs exceeding expected execution time"
- ACT-LLM-COMP-O3: "Expose completed runs that ended in failure"

Safe defaults ensure protection even when no policy is configured.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.policy_control_plane import Limit, LimitCategory, LimitStatus

logger = logging.getLogger(__name__)


# =============================================================================
# Safe Defaults (Non-Negotiable)
# =============================================================================

DEFAULT_LLM_RUN_PARAMS = {
    "max_execution_time_ms": 60_000,  # 60s safe default
    "max_tokens": 8_192,
    "max_cost_usd": 1.00,
    "failure_signal": True,
}


# =============================================================================
# Threshold Params Model (Strict Validation)
# =============================================================================


class ThresholdParams(BaseModel):
    """
    Validated threshold parameters for LLM run governance.

    Validation Rules (Hard Stop):
    - max_execution_time_ms: 1000-300000 (1s to 5min)
    - max_tokens: 256-200000
    - max_cost_usd: 0.01-100.00
    - failure_signal: boolean

    No partial garbage. No unknown keys. No absurd values.
    """

    max_execution_time_ms: int = Field(
        default=DEFAULT_LLM_RUN_PARAMS["max_execution_time_ms"],
        ge=1000,
        le=300_000,
        description="Maximum execution time in milliseconds (1s-5min)",
    )
    max_tokens: int = Field(
        default=DEFAULT_LLM_RUN_PARAMS["max_tokens"],
        ge=256,
        le=200_000,
        description="Maximum tokens allowed (256-200k)",
    )
    max_cost_usd: float = Field(
        default=DEFAULT_LLM_RUN_PARAMS["max_cost_usd"],
        ge=0.01,
        le=100.0,
        description="Maximum cost in USD (0.01-100)",
    )
    failure_signal: bool = Field(
        default=DEFAULT_LLM_RUN_PARAMS["failure_signal"],
        description="Emit signal on run failure",
    )

    @field_validator("max_cost_usd", mode="before")
    @classmethod
    def coerce_decimal_to_float(cls, v):
        """Handle Decimal input from database."""
        if isinstance(v, Decimal):
            return float(v)
        return v

    model_config = {"extra": "forbid"}  # Reject unknown keys


class ThresholdParamsUpdate(BaseModel):
    """
    Partial update for threshold params.
    All fields optional - only provided fields are updated.
    """

    max_execution_time_ms: Optional[int] = Field(
        default=None, ge=1000, le=300_000
    )
    max_tokens: Optional[int] = Field(default=None, ge=256, le=200_000)
    max_cost_usd: Optional[float] = Field(default=None, ge=0.01, le=100.0)
    failure_signal: Optional[bool] = None

    model_config = {"extra": "forbid"}


# =============================================================================
# Signal Types (Canonical)
# =============================================================================


class ThresholdSignal(str, Enum):
    """
    Signals emitted when runs breach thresholds.
    These appear in Activity → LLM Runs → Signal panels.
    """

    EXECUTION_TIME_EXCEEDED = "EXECUTION_TIME_EXCEEDED"
    TOKEN_LIMIT_EXCEEDED = "TOKEN_LIMIT_EXCEEDED"
    COST_LIMIT_EXCEEDED = "COST_LIMIT_EXCEEDED"
    RUN_FAILED = "RUN_FAILED"


@dataclass(frozen=True)
class ThresholdEvaluationResult:
    """Result of threshold evaluation."""

    run_id: str
    signals: list[ThresholdSignal]
    params_used: dict
    evaluated_at: datetime


# =============================================================================
# Threshold Resolver (Single Source of Truth)
# =============================================================================


class LLMRunThresholdResolver:
    """
    Resolves effective threshold params for an LLM run
    using Policy → Limit → Threshold precedence.

    Resolution order (highest to lowest precedence):
    1. Agent-scoped threshold (scope=AGENT, scope_id=agent_id)
    2. Project-scoped threshold (scope=PROJECT, scope_id=project_id)
    3. Tenant-scoped threshold (scope=TENANT)
    4. Global defaults (DEFAULT_LLM_RUN_PARAMS)

    Properties:
    - Deterministic
    - Merge-based (higher precedence overrides)
    - Safe if nothing exists
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def resolve(
        self,
        tenant_id: str,
        agent_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> ThresholdParams:
        """
        Resolve effective threshold params for a run.

        Args:
            tenant_id: Tenant identifier
            agent_id: Optional agent for agent-scoped resolution
            project_id: Optional project for project-scoped resolution

        Returns:
            ThresholdParams with effective values
        """
        # Start with safe defaults
        effective_params = DEFAULT_LLM_RUN_PARAMS.copy()

        # Build query for active threshold limits
        stmt = (
            select(Limit)
            .where(Limit.tenant_id == tenant_id)
            .where(Limit.limit_category == LimitCategory.THRESHOLD.value)
            .where(Limit.status == LimitStatus.ACTIVE.value)
            .order_by("created_at")  # Older limits first
        )

        result = await self._session.execute(stmt)
        limits = result.scalars().all()

        if not limits:
            logger.debug(
                "No active threshold limits for tenant %s, using defaults",
                tenant_id,
            )
            return ThresholdParams(**effective_params)

        # Apply limits in precedence order (lower precedence first)
        for limit in limits:
            if not limit.params:
                continue

            # Determine if this limit applies
            applies = False

            if limit.scope == "GLOBAL":
                applies = True
            elif limit.scope == "TENANT":
                applies = True  # Tenant-scoped applies to all runs
            elif limit.scope == "PROJECT" and limit.scope_id == project_id:
                applies = True
            elif limit.scope == "AGENT" and limit.scope_id == agent_id:
                applies = True

            if applies:
                # Merge params (later/higher precedence overwrites)
                for key, value in limit.params.items():
                    if key in effective_params and value is not None:
                        effective_params[key] = value

        # Validate and return
        try:
            return ThresholdParams(**effective_params)
        except Exception as e:
            logger.warning(
                "Invalid threshold params for tenant %s: %s, using defaults",
                tenant_id,
                str(e),
            )
            return ThresholdParams(**DEFAULT_LLM_RUN_PARAMS)


# =============================================================================
# Run Evaluator
# =============================================================================


class LLMRunEvaluator:
    """
    Evaluates LLM runs against threshold params.

    Supports:
    - Live run evaluation (execution time, tokens)
    - Completed run evaluation (all metrics + failure)

    Signals are emitted but evaluation is non-blocking.
    """

    def __init__(self, resolver: LLMRunThresholdResolver):
        self._resolver = resolver

    async def evaluate_live_run(
        self,
        run_id: str,
        tenant_id: str,
        started_at_ms: int,
        tokens_used: int,
        agent_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> ThresholdEvaluationResult:
        """
        Evaluate a live (running) LLM run.

        Checks:
        - Execution time exceeded
        - Token limit exceeded

        Args:
            run_id: Run identifier
            tenant_id: Tenant identifier
            started_at_ms: Run start time in epoch milliseconds
            tokens_used: Current token usage
            agent_id: Optional agent identifier
            project_id: Optional project identifier

        Returns:
            ThresholdEvaluationResult with any triggered signals
        """
        params = await self._resolver.resolve(tenant_id, agent_id, project_id)
        signals: list[ThresholdSignal] = []

        # Check execution time
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        elapsed_ms = now_ms - started_at_ms

        if elapsed_ms > params.max_execution_time_ms:
            signals.append(ThresholdSignal.EXECUTION_TIME_EXCEEDED)
            logger.info(
                "Run %s exceeded execution time: %dms > %dms",
                run_id,
                elapsed_ms,
                params.max_execution_time_ms,
            )

        # Check tokens
        if tokens_used > params.max_tokens:
            signals.append(ThresholdSignal.TOKEN_LIMIT_EXCEEDED)
            logger.info(
                "Run %s exceeded token limit: %d > %d",
                run_id,
                tokens_used,
                params.max_tokens,
            )

        return ThresholdEvaluationResult(
            run_id=run_id,
            signals=signals,
            params_used=params.model_dump(),
            evaluated_at=datetime.now(timezone.utc),
        )

    async def evaluate_completed_run(
        self,
        run_id: str,
        tenant_id: str,
        status: str,
        execution_time_ms: int,
        tokens_used: int,
        cost_usd: float,
        agent_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> ThresholdEvaluationResult:
        """
        Evaluate a completed LLM run.

        Checks:
        - Run failure (if failure_signal enabled)
        - Execution time exceeded
        - Token limit exceeded
        - Cost limit exceeded

        Args:
            run_id: Run identifier
            tenant_id: Tenant identifier
            status: Final run status (completed, failed, etc.)
            execution_time_ms: Total execution time
            tokens_used: Total tokens used
            cost_usd: Total cost in USD
            agent_id: Optional agent identifier
            project_id: Optional project identifier

        Returns:
            ThresholdEvaluationResult with any triggered signals
        """
        params = await self._resolver.resolve(tenant_id, agent_id, project_id)
        signals: list[ThresholdSignal] = []

        # Check failure
        if status == "failed" and params.failure_signal:
            signals.append(ThresholdSignal.RUN_FAILED)
            logger.info("Run %s failed, emitting signal", run_id)

        # Check execution time
        if execution_time_ms > params.max_execution_time_ms:
            signals.append(ThresholdSignal.EXECUTION_TIME_EXCEEDED)
            logger.info(
                "Run %s exceeded execution time: %dms > %dms",
                run_id,
                execution_time_ms,
                params.max_execution_time_ms,
            )

        # Check tokens
        if tokens_used > params.max_tokens:
            signals.append(ThresholdSignal.TOKEN_LIMIT_EXCEEDED)
            logger.info(
                "Run %s exceeded token limit: %d > %d",
                run_id,
                tokens_used,
                params.max_tokens,
            )

        # Check cost
        if cost_usd > params.max_cost_usd:
            signals.append(ThresholdSignal.COST_LIMIT_EXCEEDED)
            logger.info(
                "Run %s exceeded cost limit: $%.4f > $%.4f",
                run_id,
                cost_usd,
                params.max_cost_usd,
            )

        return ThresholdEvaluationResult(
            run_id=run_id,
            signals=signals,
            params_used=params.model_dump(),
            evaluated_at=datetime.now(timezone.utc),
        )


# =============================================================================
# Activity Signal Emitter (Minimal Extension)
# =============================================================================


@dataclass
class ThresholdSignalRecord:
    """
    Record of a threshold signal for activity domain.

    This structure is used for:
    - Activity → LLM Runs → Live → Signals
    - Activity → LLM Runs → Completed → Signals
    """

    tenant_id: str
    run_id: str
    state: str  # "live" | "completed"
    signal: ThresholdSignal
    params_used: dict
    emitted_at: datetime


def create_threshold_signal_record(
    tenant_id: str,
    run_id: str,
    state: str,
    signal: ThresholdSignal,
    params_used: dict,
) -> ThresholdSignalRecord:
    """
    Create a threshold signal record for activity domain.

    This creates a record that surfaces in:
    - Activity → LLM Runs → Live → Signals
    - Activity → LLM Runs → Completed → Signals

    Args:
        tenant_id: Tenant identifier
        run_id: Run identifier
        state: Run state (live or completed)
        signal: The threshold signal triggered
        params_used: The params that were evaluated against

    Returns:
        ThresholdSignalRecord for persistence/emission
    """
    record = ThresholdSignalRecord(
        tenant_id=tenant_id,
        run_id=run_id,
        state=state,
        signal=signal,
        params_used=params_used,
        emitted_at=datetime.now(timezone.utc),
    )

    logger.info(
        "Created threshold signal %s for run %s (state=%s)",
        signal.value,
        run_id,
        state,
    )

    return record


def collect_signals_from_evaluation(
    evaluation: ThresholdEvaluationResult,
    tenant_id: str,
    state: str,
) -> list[ThresholdSignalRecord]:
    """
    Collect all signals from an evaluation result into records.

    Args:
        evaluation: The evaluation result
        tenant_id: Tenant identifier
        state: Run state (live or completed)

    Returns:
        List of ThresholdSignalRecord for persistence
    """
    records = []
    for signal in evaluation.signals:
        records.append(
            create_threshold_signal_record(
                tenant_id=tenant_id,
                run_id=evaluation.run_id,
                state=state,
                signal=signal,
                params_used=evaluation.params_used,
            )
        )
    return records


# =============================================================================
# Sync Event Emission (for use with sync EventEmitter)
# =============================================================================


def emit_threshold_signal_sync(
    session,  # Sync Session
    tenant_id: str,
    run_id: str,
    state: str,
    signal: ThresholdSignal,
    params_used: dict,
) -> None:
    """
    Emit a threshold signal using the sync EventEmitter.

    For use in sync contexts (e.g., worker callbacks).
    """
    from app.services.event_emitter import (
        EntityType,
        EventEmitter,
        EventType,
        OpsEvent,
    )

    emitter = EventEmitter(session)

    # Map signal to event type
    event_type_map = {
        ThresholdSignal.EXECUTION_TIME_EXCEEDED: EventType.INFRA_LIMIT_HIT,
        ThresholdSignal.TOKEN_LIMIT_EXCEEDED: EventType.INFRA_LIMIT_HIT,
        ThresholdSignal.COST_LIMIT_EXCEEDED: EventType.INFRA_LIMIT_HIT,
        ThresholdSignal.RUN_FAILED: EventType.LLM_CALL_FAILED,
    }

    event_type = event_type_map.get(signal, EventType.INFRA_LIMIT_HIT)

    import uuid as uuid_module

    event = OpsEvent(
        tenant_id=uuid_module.UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id,
        event_type=event_type,
        entity_type=EntityType.LLM_CALL,
        entity_id=uuid_module.UUID(run_id) if isinstance(run_id, str) else run_id,
        severity=3 if signal == ThresholdSignal.RUN_FAILED else 2,
        metadata={
            "signal": signal.value,
            "state": state,
            "params_used": params_used,
            "domain": "llm_runs",
        },
    )

    emitter.emit(event)

    logger.info(
        "Emitted threshold signal %s for run %s (state=%s)",
        signal.value,
        run_id,
        state,
    )


# =============================================================================
# Dual Signal Emission (Founder Console + Customer Console)
# =============================================================================


def emit_and_persist_threshold_signal(
    session,  # Sync Session
    tenant_id: str,
    run_id: str,
    state: str,
    signals: list[ThresholdSignal],
    params_used: dict,
) -> None:
    """
    Emit threshold signals to both Founder and Customer consoles.

    This function performs DUAL emission:
    1. ops_events (Founder Console) - via emit_threshold_signal_sync()
       - For operational monitoring in Founder Console
       - Protected by verify_fops_token() in api/ops.py
       - NOTE: ops_events is FOUNDER CONSOLE ONLY - not transmitted to customer endpoints

    2. runs.risk_level (Customer Console) - via RunSignalService
       - For Activity panels in Customer Console
       - Consumed by v_runs_o2 -> api/activity.py -> Customer Console

    Args:
        session: SQLAlchemy sync session
        tenant_id: Tenant identifier
        run_id: Run identifier
        state: Run state ("live" or "completed")
        signals: List of ThresholdSignal values
        params_used: The threshold params that were evaluated against

    Reference: Threshold Signal Wiring to Customer Console Plan
    """
    from app.services.activity.run_signal_service import RunSignalService

    # 1. Emit to ops_events for Founder Console monitoring
    # NOTE: ops_events is FOUNDER CONSOLE ONLY - not transmitted to customer endpoints
    for signal in signals:
        emit_threshold_signal_sync(session, tenant_id, run_id, state, signal, params_used)

    # 2. Update runs.risk_level for Customer Console Activity panels
    run_signal_service = RunSignalService(session)
    run_signal_service.update_risk_level(run_id, signals)

    logger.info(
        "dual_signal_emission_complete",
        extra={
            "run_id": run_id,
            "tenant_id": tenant_id,
            "state": state,
            "signal_count": len(signals),
        },
    )
