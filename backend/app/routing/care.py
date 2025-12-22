# M17 CARE - Cascade-Aware Routing Engine
# Strategic router that routes based on agent Strategy Cascade
#
# 5-Stage Pipeline:
# 1. Aspiration → Success Metric Selection
# 2. Where-to-Play → Domain Filter
# 3. How-to-Win → Execution Strategy
# 4. Capabilities & Capacity → Hard Gate
# 5. Enabling Systems → Orchestrator Mode Selection

import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import redis.asyncio as redis_async
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from .models import (
    CONFIDENCE_BLOCK_THRESHOLD,
    CONFIDENCE_FALLBACK_THRESHOLD,
    FAIRNESS_WINDOW,
    RATE_LIMIT_WINDOW,
    RATE_LIMITS,
    STAGE_CONFIDENCE_WEIGHTS,
    AgentPerformanceVector,
    CapabilityCheckResult,
    OrchestratorMode,
    RiskPolicy,
    RouteEvaluationResult,
    RoutingDecision,
    RoutingOutcome,
    RoutingRequest,
    RoutingStage,
    StageResult,
    SuccessMetric,
    infer_orchestrator_mode,
    infer_success_metric,
)
from .probes import get_capability_prober


class RateLimiter:
    """
    Redis-based rate limiter with per-policy limits.

    Falls back to no-op if Redis unavailable (degraded mode).
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url if redis_url is not None else os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self._redis: Optional[redis_async.Redis] = None

    async def _get_redis(self) -> Optional[redis_async.Redis]:
        """Get Redis connection (lazy init)."""
        if self._redis is None:
            try:
                self._redis = redis_async.from_url(self.redis_url, decode_responses=True)
                await self._redis.ping()
            except Exception as e:
                logger.debug(f"Rate limiter Redis unavailable: {e}")
                self._redis = None
        return self._redis

    async def check_rate_limit(
        self,
        tenant_id: str,
        risk_policy: RiskPolicy,
    ) -> tuple[bool, int, int]:
        """
        Check if request is within rate limits.

        Returns:
            (allowed, current_count, limit)
        """
        r = await self._get_redis()
        if not r:
            # Redis unavailable - allow all (degraded mode)
            return True, 0, RATE_LIMITS.get(risk_policy, 30)

        limit = RATE_LIMITS.get(risk_policy, 30)
        key = f"care:ratelimit:{tenant_id}:{risk_policy.value}"

        try:
            # Sliding window counter
            current = await r.incr(key)
            if current == 1:
                await r.expire(key, RATE_LIMIT_WINDOW)

            remaining_ttl = await r.ttl(key)
            if remaining_ttl == -1:
                await r.expire(key, RATE_LIMIT_WINDOW)

            allowed = current <= limit
            return allowed, int(current), limit
        except Exception as e:
            logger.warning(f"Rate limit check failed: {e}")
            return True, 0, limit

    async def get_remaining(
        self,
        tenant_id: str,
        risk_policy: RiskPolicy,
    ) -> int:
        """Get remaining requests in current window."""
        r = await self._get_redis()
        if not r:
            return RATE_LIMITS.get(risk_policy, 30)

        key = f"care:ratelimit:{tenant_id}:{risk_policy.value}"
        try:
            current = await r.get(key)
            if current is None:
                return RATE_LIMITS.get(risk_policy, 30)
            return max(0, RATE_LIMITS.get(risk_policy, 30) - int(current))
        except Exception:
            return RATE_LIMITS.get(risk_policy, 30)


# Singleton rate limiter
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get singleton rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


class FairnessTracker:
    """
    Redis-based tracker for agent assignment fairness.

    Tracks recent assignments per agent within FAIRNESS_WINDOW.
    fairness_score = 1 / (1 + recent_assignments)
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url if redis_url is not None else os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self._redis: Optional[redis_async.Redis] = None

    async def _get_redis(self) -> Optional[redis_async.Redis]:
        """Get Redis connection (lazy init)."""
        if self._redis is None:
            try:
                self._redis = redis_async.from_url(self.redis_url, decode_responses=True)
                await self._redis.ping()
            except Exception as e:
                logger.debug(f"Fairness tracker Redis unavailable: {e}")
                self._redis = None
        return self._redis

    async def record_assignment(self, agent_id: str, tenant_id: str = "default") -> int:
        """
        Record an assignment to an agent.

        Returns the new assignment count.
        """
        r = await self._get_redis()
        if not r:
            return 0  # Can't track without Redis

        key = f"care:fairness:{tenant_id}:{agent_id}"
        try:
            count = await r.incr(key)
            if count == 1:
                await r.expire(key, FAIRNESS_WINDOW)
            return int(count)
        except Exception as e:
            logger.warning(f"Failed to record assignment: {e}")
            return 0

    async def get_recent_assignments(self, agent_id: str, tenant_id: str = "default") -> int:
        """Get recent assignment count for an agent."""
        r = await self._get_redis()
        if not r:
            return 0

        key = f"care:fairness:{tenant_id}:{agent_id}"
        try:
            count = await r.get(key)
            return int(count) if count else 0
        except Exception:
            return 0

    async def get_fairness_scores(
        self,
        agent_ids: List[str],
        tenant_id: str = "default",
    ) -> Dict[str, float]:
        """
        Get fairness scores for multiple agents.

        fairness_score = 1 / (1 + recent_assignments)
        """
        r = await self._get_redis()
        if not r:
            # Without Redis, all agents have equal fairness
            return {agent_id: 1.0 for agent_id in agent_ids}

        scores = {}
        for agent_id in agent_ids:
            key = f"care:fairness:{tenant_id}:{agent_id}"
            try:
                count = await r.get(key)
                recent = int(count) if count else 0
                scores[agent_id] = 1.0 / (1.0 + recent)
            except Exception:
                scores[agent_id] = 1.0

        return scores


class PerformanceStore:
    """
    Store for agent performance vectors.

    Used for success metrics feedback loop.
    Vectors are updated after each routing outcome.
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url if redis_url is not None else os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self._redis: Optional[redis_async.Redis] = None
        # In-memory fallback if Redis unavailable
        self._vectors: Dict[str, AgentPerformanceVector] = {}

    async def _get_redis(self) -> Optional[redis_async.Redis]:
        """Get Redis connection (lazy init)."""
        if self._redis is None:
            try:
                self._redis = redis_async.from_url(self.redis_url, decode_responses=True)
                await self._redis.ping()
            except Exception:
                self._redis = None
        return self._redis

    async def get_vector(self, agent_id: str) -> AgentPerformanceVector:
        """Get performance vector for an agent."""
        r = await self._get_redis()

        if r:
            try:
                key = f"care:perf:{agent_id}"
                data = await r.hgetall(key)
                if data:
                    return AgentPerformanceVector(
                        agent_id=agent_id,
                        avg_latency_ms=float(data.get("avg_latency_ms", 0)),
                        p95_latency_ms=float(data.get("p95_latency_ms", 0)),
                        latency_samples=int(data.get("latency_samples", 0)),
                        total_routes=int(data.get("total_routes", 0)),
                        successful_routes=int(data.get("successful_routes", 0)),
                        success_rate=float(data.get("success_rate", 1.0)),
                        risk_violation_count=int(data.get("risk_violation_count", 0)),
                        risk_violation_rate=float(data.get("risk_violation_rate", 0)),
                        fallback_count=int(data.get("fallback_count", 0)),
                        fallback_rate=float(data.get("fallback_rate", 0)),
                        primary_selection_count=int(data.get("primary_selection_count", 0)),
                        recent_assignments=int(data.get("recent_assignments", 0)),
                        fairness_score=float(data.get("fairness_score", 1.0)),
                    )
            except Exception as e:
                logger.debug(f"Failed to get performance vector from Redis: {e}")

        # Fallback to in-memory
        if agent_id in self._vectors:
            return self._vectors[agent_id]

        return AgentPerformanceVector(agent_id=agent_id)

    async def update_vector(
        self,
        agent_id: str,
        outcome: RoutingOutcome,
    ) -> AgentPerformanceVector:
        """
        Update performance vector based on routing outcome.

        This is the feedback loop that makes CARE adaptive.
        """
        vector = await self.get_vector(agent_id)

        # Update totals
        vector.total_routes += 1
        if outcome.success:
            vector.successful_routes += 1
        if outcome.risk_violated:
            vector.risk_violation_count += 1
        if outcome.was_fallback:
            vector.fallback_count += 1
        else:
            vector.primary_selection_count += 1

        # Update latency (exponential moving average)
        if outcome.latency_ms > 0:
            vector.latency_samples += 1
            alpha = 0.1  # Smoothing factor
            vector.avg_latency_ms = alpha * outcome.latency_ms + (1 - alpha) * vector.avg_latency_ms
            # Track p95 approximation (simple max tracking)
            vector.p95_latency_ms = max(vector.p95_latency_ms, outcome.latency_ms)

        # Recalculate rates
        vector.update_success_rate()
        vector.update_fallback_rate()
        if vector.total_routes > 0:
            vector.risk_violation_rate = vector.risk_violation_count / vector.total_routes

        vector.last_routed_at = outcome.completed_at
        if outcome.success:
            vector.last_success_at = outcome.completed_at
        vector.updated_at = datetime.now(timezone.utc)

        # Persist to Redis
        r = await self._get_redis()
        if r:
            try:
                key = f"care:perf:{agent_id}"
                await r.hset(
                    key,
                    mapping={
                        "avg_latency_ms": str(vector.avg_latency_ms),
                        "p95_latency_ms": str(vector.p95_latency_ms),
                        "latency_samples": str(vector.latency_samples),
                        "total_routes": str(vector.total_routes),
                        "successful_routes": str(vector.successful_routes),
                        "success_rate": str(vector.success_rate),
                        "risk_violation_count": str(vector.risk_violation_count),
                        "risk_violation_rate": str(vector.risk_violation_rate),
                        "fallback_count": str(vector.fallback_count),
                        "fallback_rate": str(vector.fallback_rate),
                        "primary_selection_count": str(vector.primary_selection_count),
                        "fairness_score": str(vector.fairness_score),
                    },
                )
                # Expire after 24 hours of inactivity
                await r.expire(key, 86400)
            except Exception as e:
                logger.warning(f"Failed to persist performance vector: {e}")

        # Update in-memory cache
        self._vectors[agent_id] = vector

        return vector

    async def get_vectors_for_agents(
        self,
        agent_ids: List[str],
    ) -> Dict[str, AgentPerformanceVector]:
        """Get performance vectors for multiple agents."""
        vectors = {}
        for agent_id in agent_ids:
            vectors[agent_id] = await self.get_vector(agent_id)
        return vectors


# Singletons
_fairness_tracker: Optional[FairnessTracker] = None
_performance_store: Optional[PerformanceStore] = None


def get_fairness_tracker() -> FairnessTracker:
    """Get singleton fairness tracker instance."""
    global _fairness_tracker
    if _fairness_tracker is None:
        _fairness_tracker = FairnessTracker()
    return _fairness_tracker


def get_performance_store() -> PerformanceStore:
    """Get singleton performance store instance."""
    global _performance_store
    if _performance_store is None:
        _performance_store = PerformanceStore()
    return _performance_store


logger = logging.getLogger("nova.routing.care")


class CAREEngine:
    """
    Cascade-Aware Routing Engine.

    Routes tasks to agents based on their Strategy Cascade:
    1. Winning Aspiration → Success metric
    2. Where-to-Play → Domain filter
    3. How-to-Win → Execution strategy
    4. Capabilities & Capacity → Hard gate
    5. Enabling Systems → Orchestrator mode

    Every routing decision is logged with structured JSON for audit.
    """

    def __init__(
        self,
        persist_decisions: bool = True,
        rate_limit_enabled: bool = True,
        fairness_enabled: bool = True,
        confidence_enabled: bool = True,
    ):
        self.prober = get_capability_prober()
        self.persist_decisions = persist_decisions
        self.rate_limit_enabled = rate_limit_enabled
        self.fairness_enabled = fairness_enabled
        self.confidence_enabled = confidence_enabled
        self._db_url = os.environ.get("DATABASE_URL")
        self._rate_limiter = get_rate_limiter() if rate_limit_enabled else None
        self._fairness_tracker = get_fairness_tracker() if fairness_enabled else None
        self._performance_store = get_performance_store()

    async def _persist_decision(
        self,
        decision: RoutingDecision,
        request: RoutingRequest,
    ) -> bool:
        """
        Persist routing decision to audit table.

        Returns True if persistence succeeded, False otherwise.
        Non-blocking - failures are logged but don't affect routing.
        """
        if not self.persist_decisions or not self._db_url:
            return False

        try:
            engine = create_engine(self._db_url)
            with engine.connect() as conn:
                conn.execute(
                    text(
                        """
                        INSERT INTO routing.routing_decisions (
                            request_id, task_description, task_domain,
                            selected_agent_id, success_metric, orchestrator_mode,
                            risk_policy, eligible_agents, fallback_agents,
                            degraded, degraded_reason, evaluated_count, routed,
                            error, actionable_fix, total_latency_ms,
                            stage_latencies, decision_details, tenant_id, decided_at
                        ) VALUES (
                            :request_id, :task_description, :task_domain,
                            :selected_agent_id, :success_metric, :orchestrator_mode,
                            :risk_policy, :eligible_agents, :fallback_agents,
                            :degraded, :degraded_reason, :evaluated_count, :routed,
                            :error, :actionable_fix, :total_latency_ms,
                            :stage_latencies, :decision_details, :tenant_id, :decided_at
                        )
                    """
                    ),
                    {
                        "request_id": decision.request_id,
                        "task_description": decision.task_description[:1000],
                        "task_domain": request.task_domain,
                        "selected_agent_id": decision.selected_agent_id,
                        "success_metric": decision.success_metric.value,
                        "orchestrator_mode": decision.orchestrator_mode.value,
                        "risk_policy": decision.risk_policy.value,
                        "eligible_agents": json.dumps(decision.eligible_agents),
                        "fallback_agents": json.dumps(decision.fallback_agents),
                        "degraded": decision.degraded,
                        "degraded_reason": decision.degraded_reason,
                        "evaluated_count": len(decision.evaluated_agents),
                        "routed": decision.routed,
                        "error": decision.error,
                        "actionable_fix": decision.actionable_fix,
                        "total_latency_ms": decision.total_latency_ms,
                        "stage_latencies": json.dumps(decision.stage_latencies),
                        "decision_details": json.dumps(
                            {
                                "decision_reason": decision.decision_reason,
                                "difficulty": request.difficulty.value,
                                "risk_tolerance": request.risk_tolerance.value,
                                "confidence_score": decision.confidence_score,
                                "confidence_blocked": decision.confidence_blocked,
                                "confidence_enforced_fallback": decision.confidence_enforced_fallback,
                            }
                        ),
                        "tenant_id": request.tenant_id,
                        "decided_at": decision.decided_at,
                    },
                )
                conn.commit()
            engine.dispose()
            logger.debug(f"Persisted routing decision {decision.request_id}")
            return True
        except SQLAlchemyError as e:
            logger.warning(f"Failed to persist routing decision: {e}")
            return False
        except Exception as e:
            logger.warning(f"Unexpected error persisting decision: {e}")
            return False

    # =========================================================================
    # Stage 1: Aspiration → Success Metric
    # =========================================================================

    def _evaluate_aspiration(
        self,
        agent_sba: Dict[str, Any],
        request: RoutingRequest,
    ) -> StageResult:
        """
        Stage 1: Derive success metric from winning aspiration.

        Maps aspiration keywords to metrics:
        - cost/budget → COST
        - fast/quick → LATENCY
        - accurate/correct → ACCURACY
        - safe/risk → RISK_MIN
        """
        start = time.time()

        aspiration = agent_sba.get("winning_aspiration", {})

        # Handle malformed data - aspiration must be a dict
        if not isinstance(aspiration, dict):
            return StageResult(
                stage=RoutingStage.ASPIRATION,
                passed=False,
                reason="Malformed winning_aspiration (expected dict)",
                latency_ms=(time.time() - start) * 1000,
            )

        description = aspiration.get("description", "")

        if not description:
            return StageResult(
                stage=RoutingStage.ASPIRATION,
                passed=False,
                reason="Missing winning_aspiration.description",
                latency_ms=(time.time() - start) * 1000,
            )

        # Infer success metric
        metric = infer_success_metric(description)

        # If request prefers a specific metric, check compatibility
        if request.prefer_metric and request.prefer_metric != metric:
            # Allow if agent is BALANCED
            if metric != SuccessMetric.BALANCED:
                return StageResult(
                    stage=RoutingStage.ASPIRATION,
                    passed=False,
                    reason=f"Metric mismatch: agent={metric.value}, request={request.prefer_metric.value}",
                    details={"agent_metric": metric.value, "requested_metric": request.prefer_metric.value},
                    latency_ms=(time.time() - start) * 1000,
                )

        return StageResult(
            stage=RoutingStage.ASPIRATION,
            passed=True,
            reason=f"Success metric: {metric.value}",
            details={"success_metric": metric.value, "aspiration": description[:100]},
            latency_ms=(time.time() - start) * 1000,
        )

    # =========================================================================
    # Stage 2: Where-to-Play → Domain Filter
    # =========================================================================

    def _evaluate_domain(
        self,
        agent_sba: Dict[str, Any],
        request: RoutingRequest,
    ) -> StageResult:
        """
        Stage 2: Filter agents by domain and boundaries.

        Checks:
        - Domain match (if task specifies domain)
        - Tool availability
        - Context allowance
        """
        start = time.time()

        where_to_play = agent_sba.get("where_to_play", {})
        agent_domain = where_to_play.get("domain", "")
        allowed_tools = where_to_play.get("allowed_tools", [])
        allowed_contexts = where_to_play.get("allowed_contexts", ["job"])
        boundaries = where_to_play.get("boundaries", "")

        # Check domain match
        if request.task_domain:
            # Fuzzy domain match (agent domain contains or equals request domain)
            if request.task_domain.lower() not in agent_domain.lower():
                return StageResult(
                    stage=RoutingStage.DOMAIN_FILTER,
                    passed=False,
                    reason=f"Domain mismatch: agent={agent_domain}, request={request.task_domain}",
                    details={"agent_domain": agent_domain, "request_domain": request.task_domain},
                    latency_ms=(time.time() - start) * 1000,
                )

        # Check required tools
        if request.required_tools:
            missing_tools = [t for t in request.required_tools if t not in allowed_tools]
            if missing_tools:
                return StageResult(
                    stage=RoutingStage.DOMAIN_FILTER,
                    passed=False,
                    reason=f"Missing tools: {missing_tools}",
                    details={"missing_tools": missing_tools, "allowed_tools": allowed_tools},
                    latency_ms=(time.time() - start) * 1000,
                )

        return StageResult(
            stage=RoutingStage.DOMAIN_FILTER,
            passed=True,
            reason=f"Domain: {agent_domain}, Tools: {len(allowed_tools)}",
            details={
                "domain": agent_domain,
                "tools_count": len(allowed_tools),
                "contexts": allowed_contexts,
            },
            latency_ms=(time.time() - start) * 1000,
        )

    # =========================================================================
    # Stage 3: How-to-Win → Execution Strategy
    # =========================================================================

    def _evaluate_strategy(
        self,
        agent_sba: Dict[str, Any],
        request: RoutingRequest,
    ) -> StageResult:
        """
        Stage 3: Check execution strategy compatibility.

        Inspects:
        - Difficulty threshold vs task difficulty
        - Risk policy compatibility
        - Task pattern matching
        - Fulfillment score threshold
        """
        start = time.time()

        how_to_win = agent_sba.get("how_to_win", {})
        tasks = how_to_win.get("tasks", [])
        fulfillment = how_to_win.get("fulfillment_metric", 0.0)

        # Check if agent has tasks defined
        if not tasks:
            return StageResult(
                stage=RoutingStage.STRATEGY,
                passed=False,
                reason="No tasks defined in how_to_win",
                latency_ms=(time.time() - start) * 1000,
            )

        # Extract routing config if present
        routing_config = agent_sba.get("routing_config", {})
        difficulty_threshold = routing_config.get("difficulty_threshold", "medium")
        risk_policy = routing_config.get("risk_policy", "balanced")

        # Check difficulty threshold
        difficulty_order = {"low": 1, "medium": 2, "high": 3}
        agent_difficulty = difficulty_order.get(difficulty_threshold.lower(), 2)
        request_difficulty = difficulty_order.get(request.difficulty.value, 2)

        if request_difficulty > agent_difficulty:
            return StageResult(
                stage=RoutingStage.STRATEGY,
                passed=False,
                reason=f"Task too difficult: agent_max={difficulty_threshold}, task={request.difficulty.value}",
                details={
                    "agent_difficulty_threshold": difficulty_threshold,
                    "task_difficulty": request.difficulty.value,
                    "escalation_needed": True,
                },
                latency_ms=(time.time() - start) * 1000,
            )

        # Check risk policy compatibility
        risk_order = {"strict": 1, "balanced": 2, "fast": 3}
        agent_risk = risk_order.get(risk_policy.lower(), 2)
        request_risk = risk_order.get(request.risk_tolerance.value, 2)

        # Agent must be at least as careful as request
        if agent_risk > request_risk:
            return StageResult(
                stage=RoutingStage.STRATEGY,
                passed=False,
                reason=f"Risk policy mismatch: agent={risk_policy}, request={request.risk_tolerance.value}",
                details={
                    "agent_risk_policy": risk_policy,
                    "request_risk_tolerance": request.risk_tolerance.value,
                },
                latency_ms=(time.time() - start) * 1000,
            )

        # Check fulfillment score (agents with <30% fulfillment are deprioritized)
        if fulfillment < 0.3:
            return StageResult(
                stage=RoutingStage.STRATEGY,
                passed=True,  # Don't reject, but note low fulfillment
                reason=f"Low fulfillment ({fulfillment:.0%}), consider alternatives",
                details={
                    "fulfillment": fulfillment,
                    "risk_policy": risk_policy,
                    "tasks_count": len(tasks),
                    "low_fulfillment_warning": True,
                },
                latency_ms=(time.time() - start) * 1000,
            )

        return StageResult(
            stage=RoutingStage.STRATEGY,
            passed=True,
            reason=f"Fulfillment: {fulfillment:.0%}, Risk: {risk_policy}",
            details={
                "fulfillment": fulfillment,
                "risk_policy": risk_policy,
                "difficulty_threshold": difficulty_threshold,
                "tasks_count": len(tasks),
            },
            latency_ms=(time.time() - start) * 1000,
        )

    # =========================================================================
    # Stage 4: Capabilities & Capacity → Hard Gate
    # =========================================================================

    async def _evaluate_capabilities(
        self,
        agent_sba: Dict[str, Any],
        agent_id: str,
    ) -> tuple[StageResult, Optional[CapabilityCheckResult]]:
        """
        Stage 4: Hard gate on capabilities and capacity.

        Real-time infrastructure checks:
        - Dependencies available
        - API keys present
        - Services reachable
        - Resource limits OK
        """
        start = time.time()

        capabilities = agent_sba.get("capabilities_capacity", {})
        dependencies = capabilities.get("dependencies", [])
        legacy_deps = capabilities.get("legacy_dependencies", [])
        env = capabilities.get("env", {})

        # Extract API key dependencies
        api_keys = []
        for dep in dependencies:
            if dep.get("type") == "api":
                api_keys.append(dep.get("name"))

        # Run capability checks
        try:
            check_result = await self.prober.check_capabilities(
                dependencies=dependencies,
                required_api_keys=api_keys if api_keys else None,
                check_database=True,
                check_redis=True,
            )
        except Exception as e:
            logger.error(f"Capability check failed: {e}")
            return StageResult(
                stage=RoutingStage.CAPABILITY,
                passed=False,
                reason=f"Capability check error: {str(e)}",
                latency_ms=(time.time() - start) * 1000,
            ), None

        latency = (time.time() - start) * 1000

        if not check_result.passed:
            # HARD dependency failures - block routing
            hard_names = [p.name for p in check_result.hard_failures]
            fix_instructions = [p.fix_instruction for p in check_result.hard_failures if p.fix_instruction]

            return StageResult(
                stage=RoutingStage.CAPABILITY,
                passed=False,
                reason=f"Hard dependency failed: {', '.join(hard_names)}",
                details={
                    "failed_capabilities": hard_names,
                    "fix_instructions": fix_instructions,
                    "hard_failures": len(check_result.hard_failures),
                    "soft_failures": len(check_result.soft_failures),
                    "probe_latency_ms": check_result.total_latency_ms,
                },
                latency_ms=latency,
            ), check_result

        # Check for degraded mode (soft deps failed but routing continues)
        if check_result.degraded:
            soft_names = [p.name for p in check_result.soft_failures]
            return StageResult(
                stage=RoutingStage.CAPABILITY,
                passed=True,  # Still passes - only soft deps failed
                reason=f"DEGRADED: {len(check_result.soft_failures)} soft deps unavailable",
                details={
                    "capabilities_checked": len(check_result.probes),
                    "degraded": True,
                    "soft_failures": soft_names,
                    "probe_latency_ms": check_result.total_latency_ms,
                },
                latency_ms=latency,
            ), check_result

        return StageResult(
            stage=RoutingStage.CAPABILITY,
            passed=True,
            reason=f"All {len(check_result.probes)} capabilities available",
            details={
                "capabilities_checked": len(check_result.probes),
                "degraded": False,
                "probe_latency_ms": check_result.total_latency_ms,
            },
            latency_ms=latency,
        ), check_result

    # =========================================================================
    # Stage 5: Enabling Systems → Orchestrator Mode
    # =========================================================================

    def _evaluate_orchestrator(
        self,
        agent_sba: Dict[str, Any],
        agent_type: str,
    ) -> StageResult:
        """
        Stage 5: Select orchestrator mode.

        Determines:
        - parallel: Independent tasks scattered to workers
        - hierarchical: Parent delegates to sub-agents
        - blackboard: Shared memory, opportunistic picking
        - sequential: One-by-one execution
        """
        start = time.time()

        enabling = agent_sba.get("enabling_management_systems", {})
        orchestrator = enabling.get("orchestrator", "system")
        governance = enabling.get("governance", "BudgetLLM")

        # Infer orchestrator mode
        mode = infer_orchestrator_mode(orchestrator, agent_type)

        # Check governance (BudgetLLM required for production)
        if governance not in ["BudgetLLM", "None"]:
            return StageResult(
                stage=RoutingStage.ORCHESTRATOR,
                passed=False,
                reason=f"Unknown governance provider: {governance}",
                latency_ms=(time.time() - start) * 1000,
            )

        return StageResult(
            stage=RoutingStage.ORCHESTRATOR,
            passed=True,
            reason=f"Mode: {mode.value}, Orchestrator: {orchestrator}",
            details={
                "orchestrator_mode": mode.value,
                "orchestrator": orchestrator,
                "governance": governance,
            },
            latency_ms=(time.time() - start) * 1000,
        )

    # =========================================================================
    # Main Routing Pipeline
    # =========================================================================

    async def evaluate_agent(
        self,
        agent_id: str,
        agent_name: Optional[str],
        agent_type: str,
        agent_sba: Dict[str, Any],
        request: RoutingRequest,
    ) -> RouteEvaluationResult:
        """
        Evaluate a single agent through the 5-stage CARE pipeline.
        """
        stage_results: List[StageResult] = []
        rejection_reason = None
        rejection_stage = None

        # Stage 1: Aspiration
        stage1 = self._evaluate_aspiration(agent_sba, request)
        stage_results.append(stage1)
        if not stage1.passed:
            rejection_reason = stage1.reason
            rejection_stage = RoutingStage.ASPIRATION

        # Stage 2: Domain Filter (only if stage 1 passed)
        if stage1.passed:
            stage2 = self._evaluate_domain(agent_sba, request)
            stage_results.append(stage2)
            if not stage2.passed:
                rejection_reason = stage2.reason
                rejection_stage = RoutingStage.DOMAIN_FILTER

        # Stage 3: Strategy (only if stage 2 passed)
        if len(stage_results) == 2 and stage_results[-1].passed:
            stage3 = self._evaluate_strategy(agent_sba, request)
            stage_results.append(stage3)
            if not stage3.passed:
                rejection_reason = stage3.reason
                rejection_stage = RoutingStage.STRATEGY

        # Stage 4: Capabilities (only if stage 3 passed)
        capability_check = None
        if len(stage_results) == 3 and stage_results[-1].passed:
            stage4, capability_check = await self._evaluate_capabilities(agent_sba, agent_id)
            stage_results.append(stage4)
            if not stage4.passed:
                rejection_reason = stage4.reason
                rejection_stage = RoutingStage.CAPABILITY

        # Stage 5: Orchestrator (only if stage 4 passed)
        if len(stage_results) == 4 and stage_results[-1].passed:
            stage5 = self._evaluate_orchestrator(agent_sba, agent_type)
            stage_results.append(stage5)
            if not stage5.passed:
                rejection_reason = stage5.reason
                rejection_stage = RoutingStage.ORCHESTRATOR

        # Determine eligibility
        eligible = all(sr.passed for sr in stage_results)

        # Extract derived values
        success_metric = SuccessMetric.BALANCED
        orchestrator_mode = OrchestratorMode.SEQUENTIAL
        risk_policy = RiskPolicy.BALANCED

        for sr in stage_results:
            if sr.stage == RoutingStage.ASPIRATION and sr.passed:
                success_metric = SuccessMetric(sr.details.get("success_metric", "balanced"))
            if sr.stage == RoutingStage.STRATEGY and sr.passed:
                risk_policy = RiskPolicy(sr.details.get("risk_policy", "balanced"))
            if sr.stage == RoutingStage.ORCHESTRATOR and sr.passed:
                orchestrator_mode = OrchestratorMode(sr.details.get("orchestrator_mode", "sequential"))

        # Calculate routing score
        score = self._calculate_routing_score(agent_sba, stage_results, request)

        return RouteEvaluationResult(
            agent_id=agent_id,
            agent_name=agent_name,
            eligible=eligible,
            score=score,
            success_metric=success_metric,
            orchestrator_mode=orchestrator_mode,
            risk_policy=risk_policy,
            stage_results=stage_results,
            rejection_reason=rejection_reason,
            rejection_stage=rejection_stage,
            capability_check=capability_check,
        )

    def _calculate_routing_score(
        self,
        agent_sba: Dict[str, Any],
        stage_results: List[StageResult],
        request: RoutingRequest,
    ) -> float:
        """
        Calculate routing score (0-1) for agent ranking.

        Factors:
        - Fulfillment metric (40%)
        - Stage pass count (30%)
        - Metric alignment (20%)
        - Low fulfillment penalty (10%)
        """
        how_to_win = agent_sba.get("how_to_win", {})
        fulfillment = how_to_win.get("fulfillment_metric", 0.0)

        # Base score from fulfillment
        score = fulfillment * 0.4

        # Stage pass bonus
        passed_stages = sum(1 for sr in stage_results if sr.passed)
        score += (passed_stages / 5) * 0.3

        # Metric alignment bonus
        for sr in stage_results:
            if sr.stage == RoutingStage.ASPIRATION and sr.passed:
                agent_metric = sr.details.get("success_metric", "balanced")
                if request.prefer_metric and agent_metric == request.prefer_metric.value:
                    score += 0.2
                elif agent_metric == "balanced":
                    score += 0.1
                break

        # Low fulfillment penalty
        if fulfillment < 0.3:
            score *= 0.9

        return min(1.0, max(0.0, score))

    def _calculate_confidence_score(
        self,
        stage_results: List[StageResult],
    ) -> float:
        """
        Calculate routing confidence score from stage results.

        Uses weighted sum of stage pass rates:
        confidence = sum(weight * pass_score for each stage)

        Where pass_score = 1.0 if passed, 0.0 if failed
        """
        confidence = 0.0

        for sr in stage_results:
            weight = STAGE_CONFIDENCE_WEIGHTS.get(sr.stage, 0.0)
            pass_score = 1.0 if sr.passed else 0.0

            # Reduce confidence for stages that passed with warnings
            if sr.passed and sr.details.get("low_fulfillment_warning"):
                pass_score = 0.7  # Partial credit for low fulfillment
            if sr.passed and sr.details.get("degraded"):
                pass_score = 0.8  # Partial credit for degraded mode

            confidence += weight * pass_score

        return min(1.0, max(0.0, confidence))

    def _apply_confidence_thresholds(
        self,
        confidence: float,
        eligible_agents: List[RouteEvaluationResult],
        fallback_agents: List[str],
    ) -> tuple[bool, bool, List[str]]:
        """
        Apply confidence thresholds to routing decision.

        Returns:
            (blocked, enforce_fallback, updated_fallback_agents)
        """
        if not self.confidence_enabled:
            return False, False, fallback_agents

        # Very low confidence - block routing
        if confidence < CONFIDENCE_BLOCK_THRESHOLD:
            return True, False, fallback_agents

        # Low confidence - enforce fallback if available
        if confidence < CONFIDENCE_FALLBACK_THRESHOLD:
            if fallback_agents:
                return False, True, fallback_agents
            # No fallback available, still allow routing with warning
            return False, True, fallback_agents

        return False, False, fallback_agents

    async def _apply_fairness_adjustment(
        self,
        eligible: List[RouteEvaluationResult],
        tenant_id: str,
    ) -> List[RouteEvaluationResult]:
        """
        Adjust routing scores based on fairness.

        Agents with many recent assignments get score penalties.
        fairness_score = 1 / (1 + recent_assignments)
        Final score = base_score * fairness_weight + fairness_score * (1 - fairness_weight)
        """
        if not self._fairness_tracker or not eligible:
            return eligible

        agent_ids = [e.agent_id for e in eligible]
        fairness_scores = await self._fairness_tracker.get_fairness_scores(agent_ids, tenant_id)

        # Apply fairness adjustment (20% weight on fairness)
        fairness_weight = 0.2
        for e in eligible:
            fairness = fairness_scores.get(e.agent_id, 1.0)
            # Blend fairness with base score
            e.score = (e.score * (1 - fairness_weight)) + (fairness * fairness_weight)

        # Re-sort by adjusted score
        eligible.sort(key=lambda e: e.score, reverse=True)

        return eligible

    async def record_outcome(
        self,
        outcome: RoutingOutcome,
    ) -> AgentPerformanceVector:
        """
        Record routing outcome for feedback loop.

        This updates the agent's performance vector, making future
        routing decisions adaptive based on actual results.
        """
        return await self._performance_store.update_vector(
            outcome.agent_id,
            outcome,
        )

    async def get_agent_performance(
        self,
        agent_id: str,
    ) -> AgentPerformanceVector:
        """Get performance vector for an agent."""
        return await self._performance_store.get_vector(agent_id)

    async def route(self, request: RoutingRequest) -> RoutingDecision:
        """
        Route a task to the best available agent.

        Main entry point for CARE routing.
        """
        start = time.time()
        request_id = str(uuid.uuid4())[:8]

        logger.info(
            "care_routing_started",
            extra={
                "request_id": request_id,
                "task_domain": request.task_domain,
                "difficulty": request.difficulty.value,
            },
        )

        # Rate limit check (per tenant and risk policy)
        rate_limited = False
        rate_limit_remaining = 0
        if self._rate_limiter:
            allowed, current, limit = await self._rate_limiter.check_rate_limit(
                request.tenant_id, request.risk_tolerance
            )
            rate_limit_remaining = max(0, limit - current)
            if not allowed:
                rate_limited = True
                logger.warning(
                    "care_rate_limited",
                    extra={
                        "request_id": request_id,
                        "tenant_id": request.tenant_id,
                        "risk_policy": request.risk_tolerance.value,
                        "current": current,
                        "limit": limit,
                    },
                )
                return RoutingDecision(
                    request_id=request_id,
                    task_description=request.task_description,
                    routed=False,
                    rate_limited=True,
                    rate_limit_remaining=0,
                    error=f"Rate limit exceeded: {current}/{limit} requests in {RATE_LIMIT_WINDOW}s",
                    actionable_fix=f"Wait {RATE_LIMIT_WINDOW}s or use FAST risk policy for higher limits",
                    total_latency_ms=(time.time() - start) * 1000,
                    decided_at=datetime.now(timezone.utc),
                )

        # Get agents from SBA registry
        try:
            from ..agents.sba import get_sba_service

            sba_service = get_sba_service()
            agents = sba_service.list_agents(
                tenant_id=request.tenant_id,
                enabled_only=True,
                sba_validated_only=False,  # Evaluate all, mark non-validated
            )
        except Exception as e:
            logger.error(f"Failed to get agents: {e}")
            return RoutingDecision(
                request_id=request_id,
                task_description=request.task_description,
                routed=False,
                error=f"Failed to get agents: {str(e)}",
                total_latency_ms=(time.time() - start) * 1000,
                decided_at=datetime.now(timezone.utc),
            )

        if not agents:
            return RoutingDecision(
                request_id=request_id,
                task_description=request.task_description,
                routed=False,
                error="No agents available",
                actionable_fix="Register agents with SBA schema using POST /api/v1/sba/register",
                total_latency_ms=(time.time() - start) * 1000,
                decided_at=datetime.now(timezone.utc),
            )

        # Evaluate all agents
        evaluated: List[RouteEvaluationResult] = []
        stage_latencies: Dict[str, float] = {
            "aspiration": 0,
            "domain_filter": 0,
            "strategy": 0,
            "capability": 0,
            "orchestrator": 0,
        }

        for agent in agents[: request.max_agents]:
            if not agent.sba:
                # Skip agents without SBA
                evaluated.append(
                    RouteEvaluationResult(
                        agent_id=agent.agent_id,
                        agent_name=agent.agent_name,
                        eligible=False,
                        rejection_reason="No SBA schema",
                        rejection_stage=RoutingStage.ASPIRATION,
                    )
                )
                continue

            result = await self.evaluate_agent(
                agent_id=agent.agent_id,
                agent_name=agent.agent_name,
                agent_type=agent.agent_type,
                agent_sba=agent.sba,
                request=request,
            )
            evaluated.append(result)

            # Aggregate stage latencies
            for sr in result.stage_results:
                stage_latencies[sr.stage.value] += sr.latency_ms

        # Select best agent
        eligible = [e for e in evaluated if e.eligible]
        eligible_ids = [e.agent_id for e in eligible]

        selected = None
        fallback_agents = []
        confidence_score = 0.0
        confidence_blocked = False
        confidence_enforced_fallback = False

        if eligible:
            # Sort by score descending
            eligible.sort(key=lambda e: e.score, reverse=True)

            # Apply fairness adjustment (redistributes scores based on recent assignments)
            eligible = await self._apply_fairness_adjustment(eligible, request.tenant_id)

            selected = eligible[0]

            # Build fallback chain (next best agents, up to 3)
            if len(eligible) > 1:
                fallback_agents = [e.agent_id for e in eligible[1:4]]

            # Calculate confidence score from stage results
            confidence_score = self._calculate_confidence_score(selected.stage_results)

            # Apply confidence thresholds
            confidence_blocked, confidence_enforced_fallback, fallback_agents = self._apply_confidence_thresholds(
                confidence_score,
                eligible,
                fallback_agents,
            )

            # If confidence blocked, clear the selection
            if confidence_blocked:
                logger.warning(
                    "care_confidence_blocked",
                    extra={
                        "request_id": request_id,
                        "confidence": confidence_score,
                        "threshold": CONFIDENCE_BLOCK_THRESHOLD,
                        "selected_agent": selected.agent_id,
                    },
                )
                selected = None

            # If confidence enforced fallback, switch to first fallback
            elif confidence_enforced_fallback and fallback_agents:
                original_agent = selected.agent_id
                # Find the fallback agent in eligible list
                for e in eligible[1:4]:
                    if e.agent_id == fallback_agents[0]:
                        selected = e
                        break
                logger.info(
                    "care_confidence_enforced_fallback",
                    extra={
                        "request_id": request_id,
                        "confidence": confidence_score,
                        "original_agent": original_agent,
                        "fallback_agent": selected.agent_id,
                    },
                )

            # Record assignment for fairness tracking
            if selected and self._fairness_tracker:
                await self._fairness_tracker.record_assignment(selected.agent_id, request.tenant_id)

        # Check for degraded mode (any soft dependency failures)
        degraded = False
        degraded_reason = None
        if selected and selected.capability_check:
            if selected.capability_check.degraded:
                degraded = True
                soft_names = [p.name for p in selected.capability_check.soft_failures]
                degraded_reason = f"Soft dependencies unavailable: {', '.join(soft_names)}"

        total_latency = (time.time() - start) * 1000

        # Build decision
        decision = RoutingDecision(
            request_id=request_id,
            task_description=request.task_description,
            selected_agent_id=selected.agent_id if selected else None,
            selected_agent_name=selected.agent_name if selected else None,
            success_metric=selected.success_metric if selected else SuccessMetric.BALANCED,
            orchestrator_mode=selected.orchestrator_mode if selected else OrchestratorMode.SEQUENTIAL,
            risk_policy=selected.risk_policy if selected else RiskPolicy.BALANCED,
            evaluated_agents=evaluated,
            eligible_agents=eligible_ids,
            fallback_agents=fallback_agents,
            degraded=degraded,
            degraded_reason=degraded_reason,
            rate_limited=False,
            rate_limit_remaining=rate_limit_remaining,
            confidence_score=confidence_score,
            confidence_blocked=confidence_blocked,
            confidence_enforced_fallback=confidence_enforced_fallback,
            routed=selected is not None,
            error=None if selected else self._build_no_agent_error(evaluated, request, confidence_blocked),
            actionable_fix=None if selected else self._build_actionable_fix(evaluated, request, confidence_blocked),
            total_latency_ms=total_latency,
            stage_latencies=stage_latencies,
            decided_at=datetime.now(timezone.utc),
            decision_reason=self._build_decision_reason(
                selected, fallback_agents, degraded, confidence_score, confidence_enforced_fallback
            ),
        )

        # Log decision
        logger.info(
            "care_routing_completed",
            extra={
                "request_id": request_id,
                "routed": decision.routed,
                "selected_agent": decision.selected_agent_id,
                "eligible_count": len(eligible_ids),
                "evaluated_count": len(evaluated),
                "latency_ms": total_latency,
                "degraded": degraded,
                "confidence_score": confidence_score,
                "confidence_blocked": confidence_blocked,
                "confidence_enforced_fallback": confidence_enforced_fallback,
            },
        )

        # Persist to audit table (non-blocking)
        await self._persist_decision(decision, request)

        return decision

    def _build_no_agent_error(
        self,
        evaluated: List[RouteEvaluationResult],
        request: RoutingRequest,
        confidence_blocked: bool = False,
    ) -> str:
        """Build descriptive error when no agent is eligible."""
        if confidence_blocked:
            return f"Routing blocked due to low confidence (<{CONFIDENCE_BLOCK_THRESHOLD:.0%})"

        if not evaluated:
            return "No agents in registry"

        # Count rejections by stage
        stage_counts: Dict[str, int] = {}
        for e in evaluated:
            if e.rejection_stage:
                stage = e.rejection_stage.value
                stage_counts[stage] = stage_counts.get(stage, 0) + 1

        if stage_counts:
            most_common = max(stage_counts, key=lambda s: stage_counts[s])
            return f"No eligible agent: {stage_counts[most_common]} rejected at {most_common} stage"

        return "No eligible agent found"

    def _build_actionable_fix(
        self,
        evaluated: List[RouteEvaluationResult],
        request: RoutingRequest,
        confidence_blocked: bool = False,
    ) -> str:
        """Build actionable fix instruction."""
        if confidence_blocked:
            return "Improve agent SBA schemas or add fallback agents; check capability probes for failures"

        fixes = []

        for e in evaluated:
            if e.rejection_stage == RoutingStage.DOMAIN_FILTER:
                fixes.append(f"Register agent for domain '{request.task_domain}'")
            elif e.rejection_stage == RoutingStage.CAPABILITY:
                if e.capability_check and e.capability_check.hard_failures:
                    # Only show fix for HARD failures (blocking)
                    for p in e.capability_check.hard_failures:
                        if p.fix_instruction:
                            fixes.append(p.fix_instruction)

        if fixes:
            return "; ".join(list(set(fixes))[:3])  # Top 3 unique fixes

        return "Register agents with complete SBA schema"

    def _build_decision_reason(
        self,
        selected: Optional[RouteEvaluationResult],
        fallback_agents: List[str],
        degraded: bool,
        confidence_score: float = 0.0,
        confidence_enforced_fallback: bool = False,
    ) -> str:
        """Build human-readable decision reason."""
        if not selected:
            return "No eligible agent"

        parts = [f"Selected {selected.agent_id} (score={selected.score:.2f}, conf={confidence_score:.0%})"]

        if confidence_enforced_fallback:
            parts.append("FALLBACK ENFORCED (low confidence)")

        if fallback_agents:
            parts.append(f"fallbacks: {', '.join(fallback_agents)}")

        if degraded:
            parts.append("DEGRADED MODE")

        return "; ".join(parts)

    # =========================================================================
    # API Methods
    # =========================================================================

    async def evaluate_agents(
        self,
        request: RoutingRequest,
        agent_ids: Optional[List[str]] = None,
    ) -> List[RouteEvaluationResult]:
        """
        Evaluate specific agents without routing.

        Used by POST /routing/cascade-evaluate
        """
        from ..agents.sba import get_sba_service

        sba_service = get_sba_service()

        results = []

        if agent_ids:
            for agent_id in agent_ids:
                agent = sba_service.get_agent(agent_id)
                if agent and agent.sba:
                    result = await self.evaluate_agent(
                        agent_id=agent.agent_id,
                        agent_name=agent.agent_name,
                        agent_type=agent.agent_type,
                        agent_sba=agent.sba,
                        request=request,
                    )
                    results.append(result)
        else:
            # Evaluate all agents
            agents = sba_service.list_agents(tenant_id=request.tenant_id)
            for agent in agents[: request.max_agents]:
                if agent.sba:
                    result = await self.evaluate_agent(
                        agent_id=agent.agent_id,
                        agent_name=agent.agent_name,
                        agent_type=agent.agent_type,
                        agent_sba=agent.sba,
                        request=request,
                    )
                    results.append(result)

        return results


# =============================================================================
# Singleton
# =============================================================================

_engine: Optional[CAREEngine] = None


def get_care_engine() -> CAREEngine:
    """Get singleton CARE engine instance."""
    global _engine
    if _engine is None:
        _engine = CAREEngine()
    return _engine
