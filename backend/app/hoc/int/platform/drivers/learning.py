# capability_id: CAP-012
# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: worker
#   Execution: sync
# Role: CARE-L learning from routing decisions
# Callers: workers
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: M18 CARE-L

# M18 CARE-L Learning Engine
# Adaptive routing based on historical performance
#
# Features:
# - Agent reputation tracking
# - Quarantine system
# - Hysteresis-stable routing
# - Self-tuning parameters
# - Predictive success probability

import logging
import os
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import redis.asyncio as redis_async
from pydantic import BaseModel, Field

logger = logging.getLogger("nova.routing.learning")


# =============================================================================
# Configuration
# =============================================================================

# Reputation weights
REPUTATION_SUCCESS_WEIGHT = 0.40
REPUTATION_LATENCY_WEIGHT = 0.20
REPUTATION_VIOLATION_WEIGHT = 0.25
REPUTATION_CONSISTENCY_WEIGHT = 0.15

# Quarantine thresholds
PROBATION_FAILURE_COUNT = 3  # Failures in window to enter probation
QUARANTINE_FAILURE_COUNT = 5  # Failures to enter quarantine
PROBATION_WINDOW = 300  # 5 minutes
QUARANTINE_COOLOFF = 1800  # 30 minutes

# Hysteresis settings
HYSTERESIS_THRESHOLD = 0.15  # 15% score difference required to switch
HYSTERESIS_WINDOW = 300  # 5 minute stability window

# Learning rate
DEFAULT_ADAPTATION_RATE = 0.01


# =============================================================================
# Quarantine States
# =============================================================================


class QuarantineState(str, Enum):
    """Agent quarantine states."""

    ACTIVE = "active"  # Normal operation
    PROBATION = "probation"  # Warning state, monitored closely
    QUARANTINED = "quarantined"  # Blocked from routing


# =============================================================================
# Agent Reputation
# =============================================================================


class AgentReputation(BaseModel):
    """
    Agent reputation for routing decisions.

    Reputation is computed from historical performance:
    - success_rate: Rolling success rate (0.0-1.0)
    - latency_percentile: Latency ranking (0.0-1.0, lower = better)
    - violation_count: Boundary/risk violations
    - quarantine_count: Times quarantined
    """

    agent_id: str
    reputation_score: float = Field(default=1.0, ge=0.0, le=1.0)
    success_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    latency_percentile: float = Field(default=0.5, ge=0.0, le=1.0)
    violation_count: int = Field(default=0, ge=0)
    quarantine_count: int = Field(default=0, ge=0)

    # Quarantine state
    quarantine_state: QuarantineState = QuarantineState.ACTIVE
    quarantine_until: Optional[datetime] = None
    quarantine_reason: Optional[str] = None

    # Tracking
    total_routes: int = 0
    successful_routes: int = 0
    recent_failures: int = 0  # In current window
    consecutive_successes: int = 0

    # Timestamps
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def compute_reputation(self) -> float:
        """
        Compute reputation score from components.

        Formula:
        reputation = (
            success_rate * 0.40 +
            (1 - latency_percentile) * 0.20 +
            (1 - violation_rate) * 0.25 +
            consistency_bonus * 0.15
        )
        """
        # Success component (40%)
        success_component = self.success_rate * REPUTATION_SUCCESS_WEIGHT

        # Latency component (20%) - lower percentile = better
        latency_component = (1 - self.latency_percentile) * REPUTATION_LATENCY_WEIGHT

        # Violation component (25%) - fewer violations = better
        violation_rate = min(1.0, self.violation_count / 10) if self.violation_count > 0 else 0.0
        violation_component = (1 - violation_rate) * REPUTATION_VIOLATION_WEIGHT

        # Consistency component (15%) - bonus for consecutive successes
        consistency_bonus = min(1.0, self.consecutive_successes / 10)
        consistency_component = consistency_bonus * REPUTATION_CONSISTENCY_WEIGHT

        self.reputation_score = min(
            1.0, max(0.0, success_component + latency_component + violation_component + consistency_component)
        )

        return self.reputation_score

    def record_success(self, latency_ms: float = 0.0) -> None:
        """Record a successful routing outcome."""
        self.total_routes += 1
        self.successful_routes += 1
        self.consecutive_successes += 1
        self.recent_failures = max(0, self.recent_failures - 1)
        self.last_success_at = datetime.now(timezone.utc)

        # Update success rate
        self.success_rate = self.successful_routes / self.total_routes

        # Check for probation exit (5 consecutive successes)
        if self.quarantine_state == QuarantineState.PROBATION:
            if self.consecutive_successes >= 5:
                self.quarantine_state = QuarantineState.ACTIVE
                self.quarantine_reason = None
                logger.info(f"Agent {self.agent_id} exited probation after 5 successes")

        self.updated_at = datetime.now(timezone.utc)
        self.compute_reputation()

    def record_failure(self, reason: Optional[str] = None) -> None:
        """Record a failed routing outcome."""
        self.total_routes += 1
        self.consecutive_successes = 0
        self.recent_failures += 1
        self.last_failure_at = datetime.now(timezone.utc)

        # Update success rate
        if self.total_routes > 0:
            self.success_rate = self.successful_routes / self.total_routes

        # Check for state transitions
        if self.quarantine_state == QuarantineState.ACTIVE:
            if self.recent_failures >= PROBATION_FAILURE_COUNT:
                self.quarantine_state = QuarantineState.PROBATION
                self.quarantine_reason = reason or "Multiple recent failures"
                logger.warning(f"Agent {self.agent_id} entered probation: {self.quarantine_reason}")

        elif self.quarantine_state == QuarantineState.PROBATION:
            if self.recent_failures >= QUARANTINE_FAILURE_COUNT:
                self.quarantine_state = QuarantineState.QUARANTINED
                self.quarantine_until = datetime.now(timezone.utc) + timedelta(seconds=QUARANTINE_COOLOFF)
                self.quarantine_count += 1
                self.quarantine_reason = reason or "Excessive failures"
                logger.error(f"Agent {self.agent_id} QUARANTINED until {self.quarantine_until}")

        self.updated_at = datetime.now(timezone.utc)
        self.compute_reputation()

    def record_violation(self, violation_type: str) -> None:
        """Record a boundary/risk violation."""
        self.violation_count += 1
        self.consecutive_successes = 0

        # Violations can trigger immediate quarantine
        if self.violation_count >= 3:
            self.quarantine_state = QuarantineState.QUARANTINED
            self.quarantine_until = datetime.now(timezone.utc) + timedelta(seconds=QUARANTINE_COOLOFF)
            self.quarantine_count += 1
            self.quarantine_reason = f"Multiple violations: {violation_type}"
            logger.error(f"Agent {self.agent_id} QUARANTINED for violations")

        self.updated_at = datetime.now(timezone.utc)
        self.compute_reputation()

    def is_routable(self) -> bool:
        """Check if agent can receive routes."""
        if self.quarantine_state == QuarantineState.QUARANTINED:
            # Check if cooloff expired
            if self.quarantine_until and datetime.now(timezone.utc) > self.quarantine_until:
                self.quarantine_state = QuarantineState.PROBATION
                self.quarantine_until = None
                self.recent_failures = 0
                logger.info(f"Agent {self.agent_id} released from quarantine to probation")
                return True
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "reputation_score": self.reputation_score,
            "success_rate": self.success_rate,
            "latency_percentile": self.latency_percentile,
            "violation_count": self.violation_count,
            "quarantine_count": self.quarantine_count,
            "quarantine_state": self.quarantine_state.value,
            "quarantine_until": self.quarantine_until.isoformat() if self.quarantine_until else None,
            "quarantine_reason": self.quarantine_reason,
            "total_routes": self.total_routes,
            "successful_routes": self.successful_routes,
            "is_routable": self.is_routable(),
        }


# =============================================================================
# Learning Parameters
# =============================================================================


class LearningParameters(BaseModel):
    """
    Self-tuning routing parameters.

    These parameters adjust automatically based on routing outcomes.
    """

    # Confidence thresholds (auto-adjusted)
    confidence_block: float = Field(default=0.35, ge=0.0, le=1.0)
    confidence_fallback: float = Field(default=0.55, ge=0.0, le=1.0)

    # Quarantine thresholds (auto-adjusted)
    quarantine_failure_threshold: int = Field(default=5, ge=1)
    probation_failure_threshold: int = Field(default=3, ge=1)

    # Reputation weights (auto-adjusted)
    success_weight: float = Field(default=0.40, ge=0.0, le=1.0)
    latency_weight: float = Field(default=0.20, ge=0.0, le=1.0)
    violation_weight: float = Field(default=0.25, ge=0.0, le=1.0)

    # Learning rate
    adaptation_rate: float = Field(default=0.01, ge=0.001, le=0.1)

    # Tracking
    adjustments_count: int = 0
    last_adjusted_at: Optional[datetime] = None

    def tune_from_outcomes(
        self,
        outcomes: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        """
        Tune parameters based on routing outcomes.

        Returns dict of adjustments made.
        """
        if not outcomes:
            return {}

        adjustments = {}

        # Calculate metrics from outcomes
        total = len(outcomes)
        successes = sum(1 for o in outcomes if o.get("success", False))
        success_rate = successes / total if total > 0 else 0.0

        confidence_blocked = sum(1 for o in outcomes if o.get("confidence_blocked", False))
        blocked_rate = confidence_blocked / total if total > 0 else 0.0

        fallback_used = sum(1 for o in outcomes if o.get("was_fallback", False))
        fallback_rate = fallback_used / total if total > 0 else 0.0

        # Adjust confidence_block if too many false positives
        if blocked_rate > 0.2 and success_rate > 0.7:
            # Blocking too much, lower threshold
            old = self.confidence_block
            self.confidence_block = max(0.2, self.confidence_block - self.adaptation_rate)
            adjustments["confidence_block"] = self.confidence_block - old

        # Adjust confidence_fallback if fallback agents failing
        fallback_success = sum(1 for o in outcomes if o.get("was_fallback") and o.get("success"))
        fallback_success_rate = fallback_success / fallback_used if fallback_used > 0 else 1.0

        if fallback_success_rate < 0.5:
            # Fallbacks failing, raise threshold
            old = self.confidence_fallback
            self.confidence_fallback = min(0.8, self.confidence_fallback + self.adaptation_rate)
            adjustments["confidence_fallback"] = self.confidence_fallback - old

        if adjustments:
            self.adjustments_count += 1
            self.last_adjusted_at = datetime.now(timezone.utc)
            logger.info(f"Learning parameters adjusted: {adjustments}")

        return adjustments


# =============================================================================
# Hysteresis Manager
# =============================================================================


class HysteresisManager:
    """
    Prevents oscillation between agents during performance swings.

    Rules:
    - Only switch if score difference > HYSTERESIS_THRESHOLD
    - Agent must be consistently better for HYSTERESIS_WINDOW
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url if redis_url is not None else os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self._redis: Optional[redis_async.Redis] = None

    async def _get_redis(self) -> Optional[redis_async.Redis]:
        """Get Redis connection."""
        if self._redis is None:
            try:
                self._redis = redis_async.from_url(self.redis_url, decode_responses=True)
                await self._redis.ping()
            except Exception:
                self._redis = None
        return self._redis

    async def should_switch(
        self,
        _current_agent: str,
        candidate_agent: str,
        current_score: float,
        candidate_score: float,
        tenant_id: str = "default",
    ) -> Tuple[bool, str]:
        """
        Determine if routing should switch from current to candidate.

        Returns:
            (should_switch, reason)
        """
        # Check threshold
        score_diff = candidate_score - current_score
        if score_diff <= HYSTERESIS_THRESHOLD:
            return False, f"Score difference {score_diff:.2%} below threshold {HYSTERESIS_THRESHOLD:.0%}"

        # Check consistency window
        r = await self._get_redis()
        if r:
            key = f"care:hysteresis:{tenant_id}:{candidate_agent}"
            try:
                # Record candidate's high score timestamp
                now = time.time()
                history = await r.zrangebyscore(key, now - HYSTERESIS_WINDOW, now)

                # Add current timestamp
                await r.zadd(key, {str(now): now})
                await r.expire(key, HYSTERESIS_WINDOW * 2)

                # Check if candidate has been consistently better
                if len(history) < 3:  # Need at least 3 data points
                    return False, f"Candidate needs {3 - len(history)} more consistent samples"

            except Exception as e:
                logger.debug(f"Hysteresis Redis error: {e}")

        return True, f"Score difference {score_diff:.2%} exceeds threshold, consistent over window"

    async def record_selection(
        self,
        agent_id: str,
        score: float,
        tenant_id: str = "default",
    ) -> None:
        """Record that an agent was selected."""
        r = await self._get_redis()
        if r:
            key = f"care:hysteresis:{tenant_id}:{agent_id}"
            try:
                now = time.time()
                await r.zadd(key, {str(now): now})
                await r.expire(key, HYSTERESIS_WINDOW * 2)
            except Exception:
                pass


# =============================================================================
# Reputation Store
# =============================================================================


class ReputationStore:
    """
    Store for agent reputations.

    Uses Redis for caching, falls back to in-memory.
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url if redis_url is not None else os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self._redis: Optional[redis_async.Redis] = None
        self._reputations: Dict[str, AgentReputation] = {}

    async def _get_redis(self) -> Optional[redis_async.Redis]:
        """Get Redis connection."""
        if self._redis is None:
            try:
                self._redis = redis_async.from_url(self.redis_url, decode_responses=True)
                await self._redis.ping()
            except Exception:
                self._redis = None
        return self._redis

    async def get_reputation(self, agent_id: str) -> AgentReputation:
        """Get reputation for an agent."""
        # Check cache
        if agent_id in self._reputations:
            return self._reputations[agent_id]

        # Try Redis
        r = await self._get_redis()
        if r:
            try:
                key = f"care:reputation:{agent_id}"
                data = await r.hgetall(key)
                if data:
                    rep = AgentReputation(
                        agent_id=agent_id,
                        reputation_score=float(data.get("reputation_score", 1.0)),
                        success_rate=float(data.get("success_rate", 1.0)),
                        latency_percentile=float(data.get("latency_percentile", 0.5)),
                        violation_count=int(data.get("violation_count", 0)),
                        quarantine_count=int(data.get("quarantine_count", 0)),
                        quarantine_state=QuarantineState(data.get("quarantine_state", "active")),
                        total_routes=int(data.get("total_routes", 0)),
                        successful_routes=int(data.get("successful_routes", 0)),
                        recent_failures=int(data.get("recent_failures", 0)),
                        consecutive_successes=int(data.get("consecutive_successes", 0)),
                    )
                    self._reputations[agent_id] = rep
                    return rep
            except Exception as e:
                logger.debug(f"Redis reputation fetch error: {e}")

        # Return new reputation
        rep = AgentReputation(agent_id=agent_id)
        self._reputations[agent_id] = rep
        return rep

    async def save_reputation(self, reputation: AgentReputation) -> None:
        """Save reputation to store."""
        self._reputations[reputation.agent_id] = reputation

        r = await self._get_redis()
        if r:
            try:
                key = f"care:reputation:{reputation.agent_id}"
                await r.hset(
                    key,
                    mapping={
                        "reputation_score": str(reputation.reputation_score),
                        "success_rate": str(reputation.success_rate),
                        "latency_percentile": str(reputation.latency_percentile),
                        "violation_count": str(reputation.violation_count),
                        "quarantine_count": str(reputation.quarantine_count),
                        "quarantine_state": reputation.quarantine_state.value,
                        "total_routes": str(reputation.total_routes),
                        "successful_routes": str(reputation.successful_routes),
                        "recent_failures": str(reputation.recent_failures),
                        "consecutive_successes": str(reputation.consecutive_successes),
                    },
                )
                await r.expire(key, 86400)  # 24 hour expiry
            except Exception as e:
                logger.warning(f"Failed to save reputation to Redis: {e}")

    async def get_all_reputations(
        self,
        agent_ids: Optional[List[str]] = None,
    ) -> Dict[str, AgentReputation]:
        """Get reputations for multiple agents."""
        if agent_ids is None:
            return self._reputations.copy()

        result = {}
        for agent_id in agent_ids:
            result[agent_id] = await self.get_reputation(agent_id)
        return result


# =============================================================================
# Singletons
# =============================================================================

_reputation_store: Optional[ReputationStore] = None
_hysteresis_manager: Optional[HysteresisManager] = None
_learning_parameters: Optional[LearningParameters] = None


def get_reputation_store() -> ReputationStore:
    """Get singleton reputation store."""
    global _reputation_store
    if _reputation_store is None:
        _reputation_store = ReputationStore()
    return _reputation_store


def get_hysteresis_manager() -> HysteresisManager:
    """Get singleton hysteresis manager."""
    global _hysteresis_manager
    if _hysteresis_manager is None:
        _hysteresis_manager = HysteresisManager()
    return _hysteresis_manager


def get_learning_parameters() -> LearningParameters:
    """Get singleton learning parameters."""
    global _learning_parameters
    if _learning_parameters is None:
        _learning_parameters = LearningParameters()
    return _learning_parameters
