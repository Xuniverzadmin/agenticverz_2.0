# Layer: L6 — Driver
# AUDIENCE: CUSTOMER
# Role: CARE-L routing governor/throttling
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Callers: API routes, workers
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: M18 CARE-L

# M18 Governor / Stabilization Layer
# Prevents oscillation and overcorrection in the learning system
#
# Features:
# - Adjustment rate limiting (cooldowns)
# - Maximum adjustment magnitude caps
# - Freeze windows during instability
# - Automatic rollback for bad adjustments
# - System-wide stability metrics


import logging
import os
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

import redis.asyncio as redis_async
from pydantic import BaseModel, Field

logger = logging.getLogger("nova.routing.governor")


# =============================================================================
# Configuration
# =============================================================================

# Adjustment limits
MAX_ADJUSTMENTS_PER_HOUR = 5  # Max parameter adjustments per agent per hour
MAX_ADJUSTMENT_MAGNITUDE = 0.10  # Max 10% change per adjustment
GLOBAL_FREEZE_THRESHOLD = 10  # System-wide freeze after N adjustments/hour
FREEZE_DURATION = 900  # 15 min freeze window

# Rollback settings
ROLLBACK_WINDOW = 1800  # 30 min window to evaluate adjustment impact
MIN_IMPROVEMENT_REQUIRED = 0.05  # 5% improvement required to keep adjustment
AUTO_ROLLBACK_ENABLED = True  # Enable automatic rollback

# Oscillation detection
OSCILLATION_DETECTION_WINDOW = 3600  # 1 hour
OSCILLATION_THRESHOLD = 3  # Same param adjusted 3+ times = oscillation

# Instability metrics
STABILITY_WINDOW = 600  # 10 min stability window
SUCCESS_RATE_VARIANCE_THRESHOLD = 0.1  # High variance = instability


# =============================================================================
# Enums
# =============================================================================


class GovernorState(str, Enum):
    """System stability states."""

    STABLE = "stable"  # Normal operation
    CAUTIOUS = "cautious"  # Reduced adjustment rate
    FROZEN = "frozen"  # No adjustments allowed
    RECOVERY = "recovery"  # Recovering from instability


class RollbackReason(str, Enum):
    """Reasons for rolling back an adjustment."""

    PERFORMANCE_DEGRADED = "performance_degraded"
    OSCILLATION_DETECTED = "oscillation_detected"
    MANUAL_OVERRIDE = "manual_override"
    TIMEOUT_NO_IMPROVEMENT = "timeout_no_improvement"


# =============================================================================
# Models
# =============================================================================


class AdjustmentRecord(BaseModel):
    """Record of a parameter adjustment for governor tracking."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    agent_id: Optional[str] = None  # None = system-wide parameter
    parameter_name: str
    old_value: float
    new_value: float
    magnitude: float = 0.0
    applied_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    rolled_back: bool = False
    rollback_reason: Optional[RollbackReason] = None

    # Post-adjustment metrics
    success_rate_before: Optional[float] = None
    success_rate_after: Optional[float] = None
    latency_before: Optional[float] = None
    latency_after: Optional[float] = None

    def compute_magnitude(self) -> float:
        """Compute adjustment magnitude."""
        if self.old_value == 0:
            self.magnitude = abs(self.new_value)
        else:
            self.magnitude = abs(self.new_value - self.old_value) / abs(self.old_value)
        return self.magnitude


class StabilityMetrics(BaseModel):
    """System-wide stability metrics."""

    state: GovernorState = GovernorState.STABLE
    freeze_until: Optional[datetime] = None
    freeze_reason: Optional[str] = None

    # Counters
    adjustments_this_hour: int = 0
    rollbacks_this_hour: int = 0
    oscillations_detected: int = 0

    # Metrics
    avg_success_rate: float = 1.0
    success_rate_variance: float = 0.0
    affected_agents: List[str] = Field(default_factory=list)

    # Timestamps
    last_adjustment_at: Optional[datetime] = None
    last_freeze_at: Optional[datetime] = None
    last_rollback_at: Optional[datetime] = None
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RollbackResult(BaseModel):
    """Result of a rollback operation."""

    success: bool
    adjustment_id: str
    reason: RollbackReason
    message: str
    restored_value: Optional[float] = None


# =============================================================================
# Governor
# =============================================================================


class Governor:
    """
    Stabilization layer that prevents learning system oscillation.

    Responsibilities:
    - Rate limit adjustments (per-agent and system-wide)
    - Cap adjustment magnitudes
    - Detect oscillation patterns
    - Freeze system during instability
    - Rollback bad adjustments
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url if redis_url is not None else os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self._redis: Optional[redis_async.Redis] = None

        # In-memory tracking
        self._adjustments: List[AdjustmentRecord] = []
        self._state = GovernorState.STABLE
        self._freeze_until: Optional[datetime] = None
        self._freeze_reason: Optional[str] = None
        self._parameter_history: Dict[str, List[Tuple[datetime, float]]] = {}

    async def _get_redis(self) -> Optional[redis_async.Redis]:
        """Get Redis connection."""
        if self._redis is None:
            try:
                self._redis = redis_async.from_url(self.redis_url, decode_responses=True)
                await self._redis.ping()
            except Exception:
                self._redis = None
        return self._redis

    # =========================================================================
    # Approval
    # =========================================================================

    async def request_adjustment(
        self,
        parameter_name: str,
        old_value: float,
        new_value: float,
        agent_id: Optional[str] = None,
    ) -> Tuple[bool, str, float]:
        """
        Request approval for a parameter adjustment.

        Args:
            parameter_name: Name of parameter to adjust
            old_value: Current value
            new_value: Proposed new value
            agent_id: Agent ID (None for system-wide)

        Returns:
            (approved, reason, allowed_value)
        """
        # Check if frozen
        if self._is_frozen():
            return False, f"System frozen until {self._freeze_until}", old_value

        # Check adjustment rate limits
        rate_ok, rate_msg = await self._check_rate_limit(agent_id)
        if not rate_ok:
            return False, rate_msg, old_value

        # Check magnitude
        magnitude = abs(new_value - old_value) / abs(old_value) if old_value != 0 else abs(new_value)
        if magnitude > MAX_ADJUSTMENT_MAGNITUDE:
            # Cap the adjustment
            if new_value > old_value:
                capped_value = old_value * (1 + MAX_ADJUSTMENT_MAGNITUDE)
            else:
                capped_value = old_value * (1 - MAX_ADJUSTMENT_MAGNITUDE)

            logger.info(f"Adjustment capped: {new_value} -> {capped_value}")
            return True, f"Adjustment capped from {magnitude:.2%} to {MAX_ADJUSTMENT_MAGNITUDE:.0%}", capped_value

        # Check for oscillation
        if self._detect_oscillation(parameter_name, agent_id):
            self._state = GovernorState.CAUTIOUS
            return False, f"Oscillation detected for {parameter_name}", old_value

        return True, "Adjustment approved", new_value

    async def record_adjustment(
        self,
        parameter_name: str,
        old_value: float,
        new_value: float,
        agent_id: Optional[str] = None,
        success_rate_before: Optional[float] = None,
    ) -> AdjustmentRecord:
        """
        Record that an adjustment was made.

        Args:
            parameter_name: Name of parameter adjusted
            old_value: Previous value
            new_value: New value
            agent_id: Agent ID (None for system-wide)
            success_rate_before: Success rate before adjustment

        Returns:
            Adjustment record
        """
        record = AdjustmentRecord(
            agent_id=agent_id,
            parameter_name=parameter_name,
            old_value=old_value,
            new_value=new_value,
            success_rate_before=success_rate_before,
        )
        record.compute_magnitude()

        self._adjustments.append(record)

        # Track parameter history for oscillation detection
        key = f"{agent_id or 'system'}:{parameter_name}"
        if key not in self._parameter_history:
            self._parameter_history[key] = []
        self._parameter_history[key].append((datetime.now(timezone.utc), new_value))

        # Store in Redis
        r = await self._get_redis()
        if r:
            try:
                redis_key = f"governor:adjustment:{record.id}"
                await r.hset(
                    redis_key,
                    mapping={
                        "agent_id": agent_id or "system",
                        "parameter_name": parameter_name,
                        "old_value": str(old_value),
                        "new_value": str(new_value),
                        "magnitude": str(record.magnitude),
                        "applied_at": record.applied_at.isoformat(),
                        "success_rate_before": str(success_rate_before) if success_rate_before else "",
                    },
                )
                await r.expire(redis_key, 86400)  # 24 hour expiry

                # Increment hourly counter
                hour_key = f"governor:adjustments_hour:{datetime.now(timezone.utc).strftime('%Y%m%d%H')}"
                await r.incr(hour_key)
                await r.expire(hour_key, 7200)
            except Exception as e:
                logger.debug(f"Redis error recording adjustment: {e}")

        # Check if system should freeze
        await self._check_system_stability()

        logger.info(
            "adjustment_recorded",
            extra={
                "id": record.id,
                "agent_id": agent_id,
                "parameter": parameter_name,
                "magnitude": record.magnitude,
            },
        )

        return record

    # =========================================================================
    # Rollback
    # =========================================================================

    async def evaluate_adjustment(
        self,
        adjustment_id: str,
        success_rate_after: float,
        latency_after: Optional[float] = None,
    ) -> Tuple[bool, Optional[RollbackResult]]:
        """
        Evaluate an adjustment's impact and potentially roll back.

        Args:
            adjustment_id: ID of adjustment to evaluate
            success_rate_after: Success rate after adjustment
            latency_after: Latency after adjustment (optional)

        Returns:
            (is_good, rollback_result)
        """
        # Find the adjustment
        record = None
        for adj in self._adjustments:
            if adj.id == adjustment_id:
                record = adj
                break

        if not record:
            return True, None  # Can't evaluate, assume good

        record.success_rate_after = success_rate_after
        record.latency_after = latency_after

        # Check if performance degraded
        if record.success_rate_before is not None:
            improvement = success_rate_after - record.success_rate_before

            if improvement < -MIN_IMPROVEMENT_REQUIRED:
                # Performance degraded, roll back
                if AUTO_ROLLBACK_ENABLED:
                    result = await self.rollback_adjustment(
                        adjustment_id,
                        RollbackReason.PERFORMANCE_DEGRADED,
                    )
                    return False, result

            elif improvement < MIN_IMPROVEMENT_REQUIRED:
                # No meaningful improvement after window
                time_since = datetime.now(timezone.utc) - record.applied_at
                if time_since.total_seconds() > ROLLBACK_WINDOW:
                    if AUTO_ROLLBACK_ENABLED:
                        result = await self.rollback_adjustment(
                            adjustment_id,
                            RollbackReason.TIMEOUT_NO_IMPROVEMENT,
                        )
                        return False, result

        return True, None

    async def rollback_adjustment(
        self,
        adjustment_id: str,
        reason: RollbackReason,
    ) -> RollbackResult:
        """
        Roll back a specific adjustment.

        Args:
            adjustment_id: ID of adjustment to roll back
            reason: Reason for rollback

        Returns:
            Rollback result
        """
        # Find the adjustment
        record = None
        for adj in self._adjustments:
            if adj.id == adjustment_id:
                record = adj
                break

        if not record:
            return RollbackResult(
                success=False,
                adjustment_id=adjustment_id,
                reason=reason,
                message="Adjustment not found",
            )

        if record.rolled_back:
            return RollbackResult(
                success=False,
                adjustment_id=adjustment_id,
                reason=reason,
                message="Adjustment already rolled back",
            )

        # Mark as rolled back
        record.rolled_back = True
        record.rollback_reason = reason

        # Store in Redis
        r = await self._get_redis()
        if r:
            try:
                redis_key = f"governor:rollback:{adjustment_id}"
                await r.hset(
                    redis_key,
                    mapping={
                        "adjustment_id": adjustment_id,
                        "reason": reason.value,
                        "rolled_back_at": datetime.now(timezone.utc).isoformat(),
                        "restored_value": str(record.old_value),
                    },
                )
                await r.expire(redis_key, 86400)
            except Exception:
                pass

        logger.warning(
            "adjustment_rolled_back",
            extra={
                "adjustment_id": adjustment_id,
                "reason": reason.value,
                "parameter": record.parameter_name,
                "restored_value": record.old_value,
            },
        )

        return RollbackResult(
            success=True,
            adjustment_id=adjustment_id,
            reason=reason,
            message=f"Rolled back {record.parameter_name} to {record.old_value}",
            restored_value=record.old_value,
        )

    # =========================================================================
    # Stability
    # =========================================================================

    def _is_frozen(self) -> bool:
        """Check if system is frozen."""
        if self._freeze_until is None:
            return False

        if datetime.now(timezone.utc) > self._freeze_until:
            self._freeze_until = None
            self._freeze_reason = None
            self._state = GovernorState.STABLE
            logger.info("System unfrozen")
            return False

        return True

    async def _check_rate_limit(self, agent_id: Optional[str]) -> Tuple[bool, str]:
        """Check if adjustment is within rate limits."""
        now = datetime.now(timezone.utc)
        hour_ago = now - timedelta(hours=1)

        # Count adjustments for this agent/system
        count = sum(
            1
            for adj in self._adjustments
            if adj.applied_at >= hour_ago and adj.agent_id == agent_id and not adj.rolled_back
        )

        if count >= MAX_ADJUSTMENTS_PER_HOUR:
            return False, f"Rate limit exceeded: {count} adjustments in last hour"

        # Also check Redis for distributed tracking
        r = await self._get_redis()
        if r:
            try:
                hour_key = f"governor:adjustments_hour:{now.strftime('%Y%m%d%H')}"
                global_count = await r.get(hour_key)
                if global_count and int(global_count) >= GLOBAL_FREEZE_THRESHOLD:
                    return False, f"Global rate limit: {global_count} system adjustments this hour"
            except Exception:
                pass

        return True, "Within rate limits"

    def _detect_oscillation(self, parameter_name: str, agent_id: Optional[str]) -> bool:
        """Detect if parameter is oscillating."""
        key = f"{agent_id or 'system'}:{parameter_name}"
        history = self._parameter_history.get(key, [])

        if len(history) < OSCILLATION_THRESHOLD:
            return False

        # Check recent history
        window_start = datetime.now(timezone.utc) - timedelta(seconds=OSCILLATION_DETECTION_WINDOW)
        recent = [v for t, v in history if t >= window_start]

        if len(recent) >= OSCILLATION_THRESHOLD:
            # Check if values are alternating (sign of oscillation)
            directions = []
            for i in range(1, len(recent)):
                if recent[i] > recent[i - 1]:
                    directions.append(1)
                elif recent[i] < recent[i - 1]:
                    directions.append(-1)
                else:
                    directions.append(0)

            # Oscillation = direction changes frequently
            changes = sum(1 for i in range(1, len(directions)) if directions[i] != directions[i - 1])
            if changes >= 2:
                logger.warning(f"Oscillation detected for {parameter_name}")
                return True

        return False

    async def _check_system_stability(self) -> None:
        """Check and update system stability state."""
        now = datetime.now(timezone.utc)
        hour_ago = now - timedelta(hours=1)

        # Count recent adjustments
        recent_adjustments = [adj for adj in self._adjustments if adj.applied_at >= hour_ago]

        if len(recent_adjustments) >= GLOBAL_FREEZE_THRESHOLD:
            self._state = GovernorState.FROZEN
            self._freeze_until = now + timedelta(seconds=FREEZE_DURATION)
            self._freeze_reason = f"Too many adjustments ({len(recent_adjustments)}) in last hour"

            logger.error(
                "system_frozen",
                extra={
                    "reason": self._freeze_reason,
                    "freeze_until": self._freeze_until.isoformat(),
                },
            )

    async def get_stability_metrics(self) -> StabilityMetrics:
        """Get current system stability metrics."""
        now = datetime.now(timezone.utc)
        hour_ago = now - timedelta(hours=1)

        recent_adjustments = [adj for adj in self._adjustments if adj.applied_at >= hour_ago]
        recent_rollbacks = [adj for adj in recent_adjustments if adj.rolled_back]

        # Detect oscillations
        oscillations = 0
        for key in self._parameter_history:
            agent_id, param_name = key.rsplit(":", 1) if ":" in key else (None, key)
            if self._detect_oscillation(param_name, agent_id if agent_id != "system" else None):
                oscillations += 1

        # Get affected agents
        affected_agents = list(set(adj.agent_id for adj in recent_adjustments if adj.agent_id))

        return StabilityMetrics(
            state=self._state,
            freeze_until=self._freeze_until,
            freeze_reason=self._freeze_reason,
            adjustments_this_hour=len(recent_adjustments),
            rollbacks_this_hour=len(recent_rollbacks),
            oscillations_detected=oscillations,
            affected_agents=affected_agents,
            last_adjustment_at=recent_adjustments[-1].applied_at if recent_adjustments else None,
            last_rollback_at=recent_rollbacks[-1].applied_at if recent_rollbacks else None,
        )

    async def force_freeze(self, duration_seconds: int = FREEZE_DURATION, reason: str = "Manual freeze") -> None:
        """Force system into frozen state."""
        self._state = GovernorState.FROZEN
        self._freeze_until = datetime.now(timezone.utc) + timedelta(seconds=duration_seconds)
        self._freeze_reason = reason

        logger.warning(f"System manually frozen: {reason}")

    async def unfreeze(self) -> None:
        """Unfreeze system."""
        self._state = GovernorState.STABLE
        self._freeze_until = None
        self._freeze_reason = None

        logger.info("System manually unfrozen")


# =============================================================================
# Singleton
# =============================================================================

_governor: Optional[Governor] = None


def get_governor() -> Governor:
    """Get singleton governor."""
    global _governor
    if _governor is None:
        _governor = Governor()
    return _governor
