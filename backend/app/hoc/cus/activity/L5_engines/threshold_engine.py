# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Location: hoc/cus/activity/L5_engines/threshold_engine.py
# Temporal:
#   Trigger: api, worker
#   Execution: async/sync
# Lifecycle:
#   Emits: THRESHOLD_EVALUATED
#   Subscribes: none
# Data Access:
#   Reads: Limit (via driver)
#   Writes: none (evaluation only)
# Role: Threshold resolution and evaluation logic (decision engine)
# Callers: L3 Adapters, API routes
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md
#
# L4 is reserved for general/L4_runtime/ only per HOC Layer Topology.
#
# L5 ENGINE CONTRACT:
# - Pure business decisions (precedence resolution, threshold evaluation)
# - No sqlalchemy imports
# - Uses ThresholdDriver interface for DB access
# - Decision contracts (ThresholdParams, etc.) owned by this engine

"""
Threshold Decision Engine (L5)

Provides:
- ThresholdParams: Validated threshold configuration (decision contract)
- LLMRunThresholdResolver: Resolves effective params using precedence rules
- LLMRunEvaluator: Evaluates runs against thresholds, determines signals
- Signal helpers: Create and collect threshold signal records

This engine owns the DECISION logic:
- Precedence rules (AGENT > PROJECT > TENANT > GLOBAL)
- Threshold evaluation (compare metrics to limits)
- Signal determination (which signals to emit)

The engine does NOT own:
- Database queries (delegated to ThresholdDriver in L6)
- Signal persistence (delegated to L6)

Reference: ACTIVITY_PHASE2.5_IMPLEMENTATION_PLAN.md
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional, Protocol

from pydantic import BaseModel, Field, field_validator

if TYPE_CHECKING:
    from app.hoc.cus.activity.L6_drivers.threshold_driver import (
        LimitSnapshot,
        ThresholdDriver,
        ThresholdDriverSync,
    )

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
# Decision Contracts (L4 Owned)
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
# Driver Protocol (Interface for L6)
# =============================================================================


class ThresholdDriverProtocol(Protocol):
    """Protocol defining the interface for threshold drivers."""

    async def get_active_threshold_limits(
        self, tenant_id: str
    ) -> list["LimitSnapshot"]:
        """Query active threshold limits for a tenant."""
        ...


class ThresholdDriverSyncProtocol(Protocol):
    """Protocol defining the interface for sync threshold drivers."""

    def get_active_threshold_limits(
        self, tenant_id: str
    ) -> list["LimitSnapshot"]:
        """Query active threshold limits for a tenant (sync)."""
        ...


# =============================================================================
# Threshold Resolver (Business Logic - L4)
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

    L4 CONTRACT: This class contains ONLY precedence logic.
    DB queries are delegated to the ThresholdDriver (L6).
    """

    def __init__(self, driver: "ThresholdDriver"):
        """
        Initialize resolver with a driver.

        Args:
            driver: ThresholdDriver instance for DB access
        """
        self._driver = driver

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

        # Get limits from driver (L6 handles DB query)
        limits = await self._driver.get_active_threshold_limits(tenant_id)

        if not limits:
            logger.debug(
                "No active threshold limits for tenant %s, using defaults",
                tenant_id,
            )
            return ThresholdParams(**effective_params)

        # Apply limits in precedence order (lower precedence first)
        # This is BUSINESS LOGIC - owned by L4 engine
        for limit in limits:
            if not limit.params:
                continue

            # Determine if this limit applies (PRECEDENCE RULES)
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
# Run Evaluator (Business Logic - L4)
# =============================================================================


class LLMRunEvaluator:
    """
    Evaluates LLM runs against threshold params.

    Supports:
    - Live run evaluation (execution time, tokens)
    - Completed run evaluation (all metrics + failure)

    Signals are determined but evaluation is non-blocking.

    L4 CONTRACT: Pure evaluation logic, no DB operations.
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
# Sync Versions (for Worker Context)
# =============================================================================


class LLMRunThresholdResolverSync:
    """
    Sync version of LLMRunThresholdResolver for worker context.

    Uses ThresholdDriverSync for DB access since the worker runs
    in a ThreadPoolExecutor which doesn't support async.

    L4 CONTRACT: Same precedence logic as async version.
    """

    def __init__(self, driver: "ThresholdDriverSync"):
        """
        Initialize resolver with a sync driver.

        Args:
            driver: ThresholdDriverSync instance for DB access
        """
        self._driver = driver

    def resolve(
        self,
        tenant_id: str,
        agent_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> ThresholdParams:
        """
        Resolve effective threshold params for a run (sync version).

        Same logic as async version but uses sync driver.
        """
        # Start with safe defaults
        effective_params = DEFAULT_LLM_RUN_PARAMS.copy()

        try:
            # Get limits from driver (L6 handles DB query)
            limits = self._driver.get_active_threshold_limits(tenant_id)

            if not limits:
                logger.debug(
                    "No active threshold limits for tenant %s, using defaults",
                    tenant_id,
                )
                return ThresholdParams(**effective_params)

            # Apply limits in precedence order (BUSINESS LOGIC)
            for limit in limits:
                if not limit.params:
                    continue

                # Determine if this limit applies
                applies = False
                if limit.scope == "GLOBAL":
                    applies = True
                elif limit.scope == "TENANT":
                    applies = True
                elif limit.scope == "PROJECT" and limit.scope_id == project_id:
                    applies = True
                elif limit.scope == "AGENT" and limit.scope_id == agent_id:
                    applies = True

                if applies:
                    for key, value in limit.params.items():
                        if key in effective_params and value is not None:
                            effective_params[key] = value

            return ThresholdParams(**effective_params)

        except Exception as e:
            logger.warning(
                "Sync threshold resolution failed for tenant %s: %s, using defaults",
                tenant_id,
                str(e),
            )
            return ThresholdParams(**DEFAULT_LLM_RUN_PARAMS)


class LLMRunEvaluatorSync:
    """
    Sync version of LLMRunEvaluator for worker context.

    Uses LLMRunThresholdResolverSync instead of the async resolver.

    L4 CONTRACT: Pure evaluation logic, no DB operations.
    """

    def __init__(self, resolver: LLMRunThresholdResolverSync):
        self._resolver = resolver

    def evaluate_completed_run(
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
        Evaluate a completed LLM run (sync version).

        Same logic as async version but uses sync resolver.
        """
        params = self._resolver.resolve(tenant_id, agent_id, project_id)
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
# Activity Signal Records (L4 Decision Contracts)
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
