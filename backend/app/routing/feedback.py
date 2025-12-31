# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: CARE-L feedback loop processing
# Callers: API routes
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: M18 CARE-L

# M18 Feedback Loop
# Bidirectional reward loop between CARE-L (routing) and SBA Evolution (agents)
#
# Features:
# - CARE-L outcomes → SBA Evolution signals
# - SBA adjustments → CARE-L reputation updates
# - Offline batch learning
# - SLA-aware scoring

import logging
import os
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional
from uuid import uuid4

import redis.asyncio as redis_async
from pydantic import BaseModel, Field

logger = logging.getLogger("nova.routing.feedback")


# =============================================================================
# Configuration
# =============================================================================

# SLA settings
DEFAULT_SLA_TARGET = 0.95  # 95% success rate
CRITICAL_SLA_WEIGHT = 2.0  # Critical tasks weighted 2x
HIGH_SLA_WEIGHT = 1.5  # High priority weighted 1.5x
NORMAL_SLA_WEIGHT = 1.0  # Normal priority

# Complexity weights
COMPLEXITY_SIMPLE = 0.8  # Simple tasks easier to satisfy
COMPLEXITY_MODERATE = 1.0  # Default
COMPLEXITY_COMPLEX = 1.3  # Complex tasks harder

# Batch settings
BATCH_WINDOW = 3600  # 1 hour window for batch processing
MIN_SAMPLES_FOR_LEARNING = 10  # Minimum samples for batch learning


# =============================================================================
# Enums
# =============================================================================


class TaskPriority(str, Enum):
    """Task priority levels for SLA weighting."""

    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class TaskComplexity(str, Enum):
    """Task complexity for scoring adjustment."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class FeedbackDirection(str, Enum):
    """Direction of feedback in the loop."""

    CARE_TO_SBA = "care_to_sba"  # Routing outcome → Evolution
    SBA_TO_CARE = "sba_to_care"  # Strategy adjustment → Routing


# =============================================================================
# Models
# =============================================================================


class RoutingOutcomeSignal(BaseModel):
    """Signal from CARE-L to SBA Evolution."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    agent_id: str
    task_id: str

    # Outcome
    success: bool
    latency_ms: float = 0.0
    error_type: Optional[str] = None
    error_message: Optional[str] = None

    # Context
    task_description: Optional[str] = None
    task_domain: Optional[str] = None
    task_priority: TaskPriority = TaskPriority.NORMAL
    task_complexity: TaskComplexity = TaskComplexity.MODERATE

    # Routing context
    confidence_at_route: float = 1.0
    was_fallback: bool = False
    reputation_at_route: float = 1.0

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StrategyAdjustmentSignal(BaseModel):
    """Signal from SBA Evolution to CARE-L."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    agent_id: str

    # Adjustment info
    adjustment_type: str
    old_fulfillment: float
    new_fulfillment: float

    # Impact on routing
    reputation_delta: float = 0.0  # How much to adjust reputation
    capability_changes: List[str] = Field(default_factory=list)  # New/removed capabilities

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SLAScore(BaseModel):
    """SLA-aware score for an agent."""

    agent_id: str
    raw_score: float  # Base reputation score
    sla_adjusted_score: float  # After SLA weighting
    sla_target: float  # Target SLA
    current_sla: float  # Current SLA achievement
    sla_gap: float  # How far from target

    # Breakdown
    critical_success_rate: float = 1.0
    high_success_rate: float = 1.0
    normal_success_rate: float = 1.0

    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BatchLearningResult(BaseModel):
    """Result of batch learning process."""

    batch_id: str = Field(default_factory=lambda: str(uuid4()))
    window_start: datetime
    window_end: datetime

    # Samples
    total_outcomes: int = 0
    successful_outcomes: int = 0
    failed_outcomes: int = 0

    # Learning output
    parameter_adjustments: Dict[str, float] = Field(default_factory=dict)
    reputation_updates: Dict[str, float] = Field(default_factory=dict)
    drift_signals_generated: int = 0
    adjustments_recommended: int = 0

    processed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# =============================================================================
# Feedback Loop Engine
# =============================================================================


class FeedbackLoop:
    """
    Bidirectional feedback loop between CARE-L and SBA Evolution.

    Flow:
    1. CARE-L routing outcome → FeedbackLoop
    2. FeedbackLoop analyzes outcome → SBA Evolution
    3. SBA Evolution adjusts strategy → FeedbackLoop
    4. FeedbackLoop updates reputation → CARE-L

    Also handles:
    - Offline batch learning
    - SLA-aware scoring
    - Inter-agent coordination signals
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url if redis_url is not None else os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self._redis: Optional[redis_async.Redis] = None

        # In-memory buffers
        self._routing_outcomes: List[RoutingOutcomeSignal] = []
        self._strategy_adjustments: List[StrategyAdjustmentSignal] = []
        self._sla_scores: Dict[str, SLAScore] = {}

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
    # CARE-L → SBA (Routing Outcomes)
    # =========================================================================

    async def record_routing_outcome(
        self,
        agent_id: str,
        task_id: str,
        success: bool,
        latency_ms: float = 0.0,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
        task_description: Optional[str] = None,
        task_domain: Optional[str] = None,
        task_priority: TaskPriority = TaskPriority.NORMAL,
        task_complexity: TaskComplexity = TaskComplexity.MODERATE,
        confidence_at_route: float = 1.0,
        was_fallback: bool = False,
        reputation_at_route: float = 1.0,
    ) -> RoutingOutcomeSignal:
        """
        Record a routing outcome for the feedback loop.

        This creates a signal from CARE-L that will be processed by SBA Evolution.
        """
        signal = RoutingOutcomeSignal(
            agent_id=agent_id,
            task_id=task_id,
            success=success,
            latency_ms=latency_ms,
            error_type=error_type,
            error_message=error_message,
            task_description=task_description,
            task_domain=task_domain,
            task_priority=task_priority,
            task_complexity=task_complexity,
            confidence_at_route=confidence_at_route,
            was_fallback=was_fallback,
            reputation_at_route=reputation_at_route,
        )

        self._routing_outcomes.append(signal)

        # Store in Redis for batch processing
        r = await self._get_redis()
        if r:
            try:
                key = f"feedback:outcome:{signal.id}"
                await r.hset(
                    key,
                    mapping={
                        "agent_id": agent_id,
                        "task_id": task_id,
                        "success": str(success),
                        "latency_ms": str(latency_ms),
                        "error_type": error_type or "",
                        "task_priority": task_priority.value,
                        "task_complexity": task_complexity.value,
                        "created_at": signal.created_at.isoformat(),
                    },
                )
                await r.expire(key, BATCH_WINDOW * 2)

                # Add to batch queue
                queue_key = f"feedback:batch_queue:{datetime.now(timezone.utc).strftime('%Y%m%d%H')}"
                await r.sadd(queue_key, signal.id)
                await r.expire(queue_key, BATCH_WINDOW * 2)
            except Exception as e:
                logger.debug(f"Redis error recording outcome: {e}")

        # Update SLA score immediately
        await self._update_sla_score(agent_id, signal)

        logger.debug(
            "routing_outcome_recorded",
            extra={
                "agent_id": agent_id,
                "task_id": task_id,
                "success": success,
                "priority": task_priority.value,
            },
        )

        return signal

    async def get_signals_for_sba(
        self,
        agent_id: str,
        since: Optional[datetime] = None,
    ) -> List[RoutingOutcomeSignal]:
        """
        Get routing outcome signals for SBA Evolution to process.

        Args:
            agent_id: Agent to get signals for
            since: Only signals after this time

        Returns:
            List of routing outcome signals
        """
        signals = [s for s in self._routing_outcomes if s.agent_id == agent_id]

        if since:
            signals = [s for s in signals if s.created_at >= since]

        return signals

    # =========================================================================
    # SBA → CARE-L (Strategy Adjustments)
    # =========================================================================

    async def record_strategy_adjustment(
        self,
        agent_id: str,
        adjustment_type: str,
        old_fulfillment: float,
        new_fulfillment: float,
        capability_changes: Optional[List[str]] = None,
    ) -> StrategyAdjustmentSignal:
        """
        Record a strategy adjustment from SBA Evolution.

        This creates a signal that will update CARE-L routing decisions.
        """
        # Calculate reputation delta based on fulfillment change
        fulfillment_delta = new_fulfillment - old_fulfillment
        reputation_delta = fulfillment_delta * 0.2  # 20% of fulfillment change

        signal = StrategyAdjustmentSignal(
            agent_id=agent_id,
            adjustment_type=adjustment_type,
            old_fulfillment=old_fulfillment,
            new_fulfillment=new_fulfillment,
            reputation_delta=reputation_delta,
            capability_changes=capability_changes or [],
        )

        self._strategy_adjustments.append(signal)

        # Store in Redis
        r = await self._get_redis()
        if r:
            try:
                key = f"feedback:adjustment:{signal.id}"
                await r.hset(
                    key,
                    mapping={
                        "agent_id": agent_id,
                        "adjustment_type": adjustment_type,
                        "old_fulfillment": str(old_fulfillment),
                        "new_fulfillment": str(new_fulfillment),
                        "reputation_delta": str(reputation_delta),
                        "created_at": signal.created_at.isoformat(),
                    },
                )
                await r.expire(key, BATCH_WINDOW * 2)
            except Exception as e:
                logger.debug(f"Redis error recording adjustment: {e}")

        logger.info(
            "strategy_adjustment_recorded",
            extra={
                "agent_id": agent_id,
                "adjustment_type": adjustment_type,
                "reputation_delta": reputation_delta,
            },
        )

        return signal

    async def get_reputation_updates_for_care(
        self,
        since: Optional[datetime] = None,
    ) -> Dict[str, float]:
        """
        Get reputation updates for CARE-L from recent strategy adjustments.

        Returns:
            Dict of agent_id → reputation_delta
        """
        updates: Dict[str, float] = {}

        adjustments = self._strategy_adjustments
        if since:
            adjustments = [a for a in adjustments if a.created_at >= since]

        for adj in adjustments:
            if adj.agent_id not in updates:
                updates[adj.agent_id] = 0.0
            updates[adj.agent_id] += adj.reputation_delta

        return updates

    # =========================================================================
    # SLA-Aware Scoring
    # =========================================================================

    async def _update_sla_score(
        self,
        agent_id: str,
        outcome: RoutingOutcomeSignal,
    ) -> None:
        """Update SLA score based on new outcome."""
        if agent_id not in self._sla_scores:
            self._sla_scores[agent_id] = SLAScore(
                agent_id=agent_id,
                raw_score=1.0,
                sla_adjusted_score=1.0,
                sla_target=DEFAULT_SLA_TARGET,
                current_sla=1.0,
                sla_gap=0.0,
            )

        score = self._sla_scores[agent_id]

        # Calculate weighted success
        weight = NORMAL_SLA_WEIGHT
        if outcome.task_priority == TaskPriority.CRITICAL:
            weight = CRITICAL_SLA_WEIGHT
        elif outcome.task_priority == TaskPriority.HIGH:
            weight = HIGH_SLA_WEIGHT

        # Apply complexity modifier
        complexity_mod = COMPLEXITY_MODERATE
        if outcome.task_complexity == TaskComplexity.SIMPLE:
            complexity_mod = COMPLEXITY_SIMPLE
        elif outcome.task_complexity == TaskComplexity.COMPLEX:
            complexity_mod = COMPLEXITY_COMPLEX

        # Update running averages (exponential moving average)
        alpha = 0.1  # Learning rate
        outcome_value = 1.0 if outcome.success else 0.0
        weighted_outcome = outcome_value * weight / complexity_mod

        score.current_sla = (1 - alpha) * score.current_sla + alpha * outcome_value
        score.sla_gap = score.sla_target - score.current_sla
        score.sla_adjusted_score = score.raw_score * (1 - score.sla_gap)
        score.updated_at = datetime.now(timezone.utc)

    async def get_sla_score(self, agent_id: str) -> Optional[SLAScore]:
        """Get SLA score for an agent."""
        return self._sla_scores.get(agent_id)

    async def compute_sla_adjusted_reputation(
        self,
        agent_id: str,
        base_reputation: float,
    ) -> float:
        """
        Compute SLA-adjusted reputation score.

        Args:
            agent_id: Agent ID
            base_reputation: Base reputation score

        Returns:
            SLA-adjusted reputation
        """
        sla_score = self._sla_scores.get(agent_id)

        if not sla_score:
            return base_reputation

        # Penalize for SLA gap
        adjustment = 1.0 - (sla_score.sla_gap * 0.5)  # 50% of gap affects reputation
        adjustment = max(0.5, min(1.5, adjustment))  # Cap adjustment

        return base_reputation * adjustment

    # =========================================================================
    # Batch Learning
    # =========================================================================

    async def run_batch_learning(
        self,
        window_hours: int = 1,
    ) -> BatchLearningResult:
        """
        Run batch learning over a time window.

        This is the offline learning component that processes accumulated
        outcomes and produces parameter adjustments.

        Args:
            window_hours: Hours of data to process

        Returns:
            Batch learning result
        """
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(hours=window_hours)

        # Get outcomes in window
        outcomes = [o for o in self._routing_outcomes if o.created_at >= window_start]

        result = BatchLearningResult(
            window_start=window_start,
            window_end=now,
            total_outcomes=len(outcomes),
            successful_outcomes=sum(1 for o in outcomes if o.success),
            failed_outcomes=sum(1 for o in outcomes if not o.success),
        )

        if len(outcomes) < MIN_SAMPLES_FOR_LEARNING:
            logger.info(f"Insufficient samples for batch learning: {len(outcomes)}")
            return result

        # Group by agent
        agent_outcomes: Dict[str, List[RoutingOutcomeSignal]] = {}
        for outcome in outcomes:
            if outcome.agent_id not in agent_outcomes:
                agent_outcomes[outcome.agent_id] = []
            agent_outcomes[outcome.agent_id].append(outcome)

        # Calculate per-agent metrics and recommendations
        for agent_id, agent_outcomes_list in agent_outcomes.items():
            success_rate = sum(1 for o in agent_outcomes_list if o.success) / len(agent_outcomes_list)

            # Calculate domain-specific success rates
            domain_success: Dict[str, List[bool]] = {}
            for o in agent_outcomes_list:
                domain = o.task_domain or "unknown"
                if domain not in domain_success:
                    domain_success[domain] = []
                domain_success[domain].append(o.success)

            # Identify weak domains (< 70% success)
            weak_domains = [
                d for d, results in domain_success.items() if len(results) >= 3 and sum(results) / len(results) < 0.7
            ]

            if weak_domains:
                result.drift_signals_generated += 1
                result.adjustments_recommended += 1

            # Calculate reputation update
            base_delta = (success_rate - 0.8) * 0.1  # Center around 80%
            result.reputation_updates[agent_id] = base_delta

        # Suggest system-wide parameter adjustments
        overall_success = sum(1 for o in outcomes if o.success) / len(outcomes)

        if overall_success < 0.7:
            # Too many failures, tighten confidence thresholds
            result.parameter_adjustments["confidence_fallback"] = 0.02  # Increase
        elif overall_success > 0.95:
            # Very high success, can loosen thresholds
            result.parameter_adjustments["confidence_block"] = -0.02  # Decrease

        # Check for fallback effectiveness
        fallback_outcomes = [o for o in outcomes if o.was_fallback]
        if fallback_outcomes:
            fallback_success = sum(1 for o in fallback_outcomes if o.success) / len(fallback_outcomes)
            if fallback_success < 0.5:
                result.parameter_adjustments["confidence_fallback"] = 0.05  # Raise threshold

        logger.info(
            "batch_learning_complete",
            extra={
                "total_outcomes": result.total_outcomes,
                "success_rate": overall_success,
                "adjustments": len(result.parameter_adjustments),
                "reputation_updates": len(result.reputation_updates),
            },
        )

        return result

    # =========================================================================
    # Inter-Agent Coordination
    # =========================================================================

    async def recommend_capability_redistribution(
        self,
        weak_agent_id: str,
        capability: str,
    ) -> Optional[str]:
        """
        Recommend another agent to handle a capability that weak_agent is failing at.

        Args:
            weak_agent_id: Agent that's struggling
            capability: Capability/domain they're failing at

        Returns:
            Suggested successor agent ID or None
        """
        # Find agents that handle similar tasks well
        candidates: Dict[str, float] = {}

        for outcome in self._routing_outcomes:
            if outcome.agent_id == weak_agent_id:
                continue

            # Check if this agent handles similar tasks
            if outcome.task_domain == capability or capability in (outcome.task_description or ""):
                if outcome.agent_id not in candidates:
                    candidates[outcome.agent_id] = 0.0

                if outcome.success:
                    candidates[outcome.agent_id] += 1.0
                else:
                    candidates[outcome.agent_id] -= 0.5

        if not candidates:
            return None

        # Return best candidate
        best = max(candidates.items(), key=lambda x: x[1])
        if best[1] > 0:
            logger.info(
                "capability_redistribution_recommended",
                extra={
                    "weak_agent": weak_agent_id,
                    "capability": capability,
                    "recommended_agent": best[0],
                },
            )
            return best[0]

        return None

    async def get_successor_mapping(
        self,
        agent_id: str,
    ) -> Dict[str, str]:
        """
        Get mapping of capabilities to successor agents for failover.

        Args:
            agent_id: Agent to get successors for

        Returns:
            Dict of capability → successor_agent_id
        """
        # Get this agent's weak domains
        agent_outcomes = [o for o in self._routing_outcomes if o.agent_id == agent_id]

        if not agent_outcomes:
            return {}

        # Group by domain
        domain_success: Dict[str, List[bool]] = {}
        for o in agent_outcomes:
            domain = o.task_domain or "general"
            if domain not in domain_success:
                domain_success[domain] = []
            domain_success[domain].append(o.success)

        # Find successors for weak domains
        successors: Dict[str, str] = {}
        for domain, results in domain_success.items():
            if len(results) >= 3:
                success_rate = sum(results) / len(results)
                if success_rate < 0.7:
                    successor = await self.recommend_capability_redistribution(agent_id, domain)
                    if successor:
                        successors[domain] = successor

        return successors


# =============================================================================
# Singleton
# =============================================================================

_feedback_loop: Optional[FeedbackLoop] = None


def get_feedback_loop() -> FeedbackLoop:
    """Get singleton feedback loop."""
    global _feedback_loop
    if _feedback_loop is None:
        _feedback_loop = FeedbackLoop()
    return _feedback_loop
