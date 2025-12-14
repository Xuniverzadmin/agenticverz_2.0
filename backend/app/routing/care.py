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
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .models import (
    CapabilityCheckResult,
    DifficultyLevel,
    OrchestratorMode,
    RiskPolicy,
    RouteEvaluationResult,
    RoutingConfig,
    RoutingDecision,
    RoutingRequest,
    RoutingStage,
    StageResult,
    SuccessMetric,
    infer_orchestrator_mode,
    infer_success_metric,
)
from .probes import CapabilityProber, get_capability_prober

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

    def __init__(self):
        self.prober = get_capability_prober()

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
            # Build actionable error message
            failed_names = [p.name for p in check_result.failed_probes]
            fix_instructions = [
                p.fix_instruction for p in check_result.failed_probes
                if p.fix_instruction
            ]

            return StageResult(
                stage=RoutingStage.CAPABILITY,
                passed=False,
                reason=f"Capability check failed: {', '.join(failed_names)}",
                details={
                    "failed_capabilities": failed_names,
                    "fix_instructions": fix_instructions,
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
            }
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

        for agent in agents[:request.max_agents]:
            if not agent.sba:
                # Skip agents without SBA
                evaluated.append(RouteEvaluationResult(
                    agent_id=agent.agent_id,
                    agent_name=agent.agent_name,
                    eligible=False,
                    rejection_reason="No SBA schema",
                    rejection_stage=RoutingStage.ASPIRATION,
                ))
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
        if eligible:
            # Sort by score descending
            eligible.sort(key=lambda e: e.score, reverse=True)
            selected = eligible[0]

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
            routed=selected is not None,
            error=None if selected else self._build_no_agent_error(evaluated, request),
            actionable_fix=None if selected else self._build_actionable_fix(evaluated, request),
            total_latency_ms=total_latency,
            stage_latencies=stage_latencies,
            decided_at=datetime.now(timezone.utc),
            decision_reason=f"Selected {selected.agent_id} (score={selected.score:.2f})" if selected else "No eligible agent",
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
            }
        )

        return decision

    def _build_no_agent_error(
        self,
        evaluated: List[RouteEvaluationResult],
        request: RoutingRequest,
    ) -> str:
        """Build descriptive error when no agent is eligible."""
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
    ) -> str:
        """Build actionable fix instruction."""
        fixes = []

        for e in evaluated:
            if e.rejection_stage == RoutingStage.DOMAIN_FILTER:
                fixes.append(f"Register agent for domain '{request.task_domain}'")
            elif e.rejection_stage == RoutingStage.CAPABILITY:
                if e.capability_check and e.capability_check.failed_probes:
                    for p in e.capability_check.failed_probes:
                        if p.fix_instruction:
                            fixes.append(p.fix_instruction)

        if fixes:
            return "; ".join(list(set(fixes))[:3])  # Top 3 unique fixes

        return "Register agents with complete SBA schema"

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
            for agent in agents[:request.max_agents]:
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
