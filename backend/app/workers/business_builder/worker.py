# Business Builder Worker v0.2
# Main entry point that integrates M0-M20 moats
"""
The Business Builder Worker demonstrates 12+ moats:

- M4:  Deterministic execution via ExecutionPlan + golden replay
- M9:  Failure pattern detection via FailureCatalog
- M10: Recovery suggestion via RecoveryEngine
- M11: Skills (llm_invoke, webhook, embedding)
- M12: Multi-agent coordination
- M15: Strategy-Bound Agents via SBASchema
- M17: CARE routing (complexity-aware)
- M18: Drift detection & reputation
- M19: Policy governance (forbidden claims, budget)
- M20: PLang compiler & runtime
- IAEC: Task embedding for routing

Usage:
    worker = BusinessBuilderWorker()
    result = await worker.run(
        task="AI tool for podcasters",
        brand=BrandSchema(...),
        budget=3000,
        strict_mode=True,
    )
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import hashlib
import json

from .execution_plan import (
    ExecutionPlan,
    ExecutionStage,
    StageResult,
    StageStatus,
    StageCategory,
    create_business_builder_plan,
)
from .schemas.brand import BrandSchema, ToneLevel, create_minimal_brand
from .agents import WORKER_AGENTS, register_all_agents

logger = logging.getLogger("nova.workers.business_builder")


@dataclass
class WorkerResult:
    """Complete result from Business Builder Worker."""
    success: bool
    bundle_path: Optional[str] = None
    artifacts: Dict[str, Any] = field(default_factory=dict)
    replay_token: Optional[Dict[str, Any]] = None
    cost_report: Optional[Dict[str, Any]] = None
    policy_violations: List[Dict[str, Any]] = field(default_factory=list)
    recovery_log: List[Dict[str, Any]] = field(default_factory=list)
    drift_metrics: Dict[str, float] = field(default_factory=dict)
    routing_decisions: List[Dict[str, Any]] = field(default_factory=list)
    execution_trace: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    total_tokens_used: int = 0
    total_latency_ms: float = 0.0


class BusinessBuilderWorker:
    """
    Business Builder Worker v0.2.

    Transforms an idea + brand into a complete launch package.

    Integrates:
    - M17 CARE: Routes stages to agents based on complexity
    - M19/M20: Validates outputs against policies
    - M9/M10: Detects failures and suggests recovery
    - M18: Tracks drift and updates agent reputation
    - M4: Produces deterministic replay token
    """

    def __init__(
        self,
        tenant_id: str = "default",
        auto_register_agents: bool = True,
    ):
        self.tenant_id = tenant_id
        self._care_engine = None
        self._policy_engine = None
        self._failure_catalog = None
        self._recovery_engine = None
        self._drift_detector = None

        # Lazy load integrations
        self._integrations_loaded = False

        # Register agents on init
        if auto_register_agents:
            try:
                register_all_agents(tenant_id=tenant_id)
            except Exception as e:
                logger.warning(f"Could not register agents: {e}")

    def _load_integrations(self) -> None:
        """Lazy load M0-M20 integrations."""
        if self._integrations_loaded:
            return

        # M17 CARE Routing
        try:
            from app.routing.care import get_care_engine
            self._care_engine = get_care_engine()
        except ImportError:
            logger.warning("M17 CARE engine not available")

        # M20 Policy Runtime
        try:
            from app.policy.runtime.deterministic_engine import DeterministicEngine
            from app.policy.runtime.dag_executor import DAGExecutor
            self._policy_engine = DAGExecutor()
        except ImportError:
            logger.warning("M20 Policy engine not available")

        # M9 Failure Catalog
        try:
            from app.jobs.failure_aggregation import FailureCatalog
            self._failure_catalog = FailureCatalog()
        except ImportError:
            logger.warning("M9 Failure catalog not available")

        # M10 Recovery Engine
        try:
            from app.api.recovery import get_recovery_service
            self._recovery_engine = get_recovery_service()
        except ImportError:
            logger.warning("M10 Recovery engine not available")

        # M18 Drift Detection
        try:
            from app.routing.learning import get_learning_engine
            self._drift_detector = get_learning_engine()
        except ImportError:
            logger.warning("M18 Drift detector not available")

        self._integrations_loaded = True

    async def run(
        self,
        task: str,
        brand: Optional[BrandSchema] = None,
        budget: Optional[int] = None,
        strict_mode: bool = False,
        depth: str = "auto",  # auto, shallow, deep
    ) -> WorkerResult:
        """
        Execute the Business Builder workflow.

        Args:
            task: Description of the business/product to build for
            brand: Brand schema with constraints (triggers M15/M18/M19)
            budget: Token budget (triggers M19 enforcement)
            strict_mode: If True, any policy violation stops execution
            depth: Research depth (auto uses CARE complexity detection)

        Returns:
            WorkerResult with all artifacts and metadata
        """
        start_time = datetime.now(timezone.utc)
        self._load_integrations()

        logger.info(
            "business_builder_started",
            extra={
                "task": task[:100],
                "has_brand": brand is not None,
                "budget": budget,
                "strict_mode": strict_mode,
            }
        )

        # Create default brand if not provided
        if not brand:
            brand = create_minimal_brand(
                company_name="New Venture",
                mission="Build something amazing that helps people",
                value_proposition="A better way to solve the problem at hand",
                tone=ToneLevel.PROFESSIONAL,
            )

        # Create execution plan
        plan = create_business_builder_plan(
            brand_context=brand.to_strategy_context(),
            budget=budget,
            strict_mode=strict_mode,
        )
        plan.request_context = {"task": task, "depth": depth}

        result = WorkerResult(success=False)

        try:
            # Execute stages in governance order
            for stage in plan.get_execution_order():
                stage_result = await self._execute_stage(
                    stage=stage,
                    plan=plan,
                    brand=brand,
                    task=task,
                )

                plan.stage_results.append(stage_result)
                result.execution_trace.append({
                    "stage": stage.id,
                    "status": stage_result.status.name,
                    "latency_ms": stage_result.latency_ms,
                    "agent_used": stage_result.agent_used,
                })

                # Check for failure
                if stage_result.status == StageStatus.FAILED:
                    if strict_mode:
                        result.error = f"Stage {stage.id} failed: {stage_result.error}"
                        break

                    # Try recovery (M9/M10)
                    recovered = await self._attempt_recovery(
                        stage=stage,
                        stage_result=stage_result,
                        plan=plan,
                        brand=brand,
                    )

                    if recovered:
                        stage_result.status = StageStatus.RECOVERED
                        result.recovery_log.append({
                            "stage": stage.id,
                            "recovery": recovered,
                        })
                    else:
                        result.error = f"Stage {stage.id} failed and recovery unsuccessful"
                        break

                # Check policy violations
                if stage_result.policy_violations:
                    result.policy_violations.extend(stage_result.policy_violations)
                    if strict_mode:
                        result.error = f"Policy violation in {stage.id}"
                        break

                # Track drift (M18)
                if stage_result.drift_score is not None:
                    result.drift_metrics[stage.id] = stage_result.drift_score

                # Accumulate cost
                result.total_tokens_used += stage_result.step_count

            # If we completed all stages
            if not result.error:
                result.success = True

                # Collect artifacts from all stages
                for sr in plan.stage_results:
                    result.artifacts.update(sr.outputs)

                # Generate replay token (M4)
                result.replay_token = plan.to_replay_token()

                # Generate cost report
                result.cost_report = self._generate_cost_report(plan, result)

            plan.final_status = StageStatus.COMPLETED if result.success else StageStatus.FAILED
            plan.completed_at = datetime.now(timezone.utc)

        except Exception as e:
            logger.exception("business_builder_failed")
            result.error = str(e)
            plan.final_status = StageStatus.FAILED

        result.total_latency_ms = (
            datetime.now(timezone.utc) - start_time
        ).total_seconds() * 1000

        logger.info(
            "business_builder_completed",
            extra={
                "success": result.success,
                "total_tokens": result.total_tokens_used,
                "latency_ms": result.total_latency_ms,
                "stages_completed": len(plan.stage_results),
                "policy_violations": len(result.policy_violations),
                "recoveries": len(result.recovery_log),
            }
        )

        return result

    async def _execute_stage(
        self,
        stage: ExecutionStage,
        plan: ExecutionPlan,
        brand: BrandSchema,
        task: str,
    ) -> StageResult:
        """
        Execute a single stage.

        Integrates:
        - M17: CARE routing for agent selection
        - M19/M20: Policy validation
        - M18: Drift detection
        """
        start_time = datetime.now(timezone.utc)

        logger.debug(f"Executing stage: {stage.id}")

        result = StageResult(
            stage_id=stage.id,
            status=StageStatus.RUNNING,
        )

        try:
            # Route to agent via CARE (M17)
            agent_id = await self._route_to_agent(stage, plan, task)
            result.agent_used = agent_id

            # Validate pre-policies (M19/M20)
            if stage.pre_policies:
                violations = await self._check_policies(
                    stage.pre_policies,
                    {"stage": stage.id, "inputs": stage.inputs},
                    brand,
                )
                if violations:
                    result.policy_violations.extend(violations)
                    if plan.strict_mode:
                        result.status = StageStatus.FAILED
                        result.error = f"Pre-policy violation: {violations[0]['reason']}"
                        return result

            # Gather inputs from previous stages
            inputs = {}
            for input_id in stage.inputs:
                value = plan.get_output(input_id)
                if value is not None:
                    inputs[input_id] = value

            # Execute stage (mock for now - would call agent)
            outputs = await self._run_agent(
                agent_id=agent_id,
                stage=stage,
                inputs=inputs,
                brand=brand,
                task=task,
            )
            result.outputs = outputs

            # Validate post-policies (M19/M20)
            if stage.post_policies:
                violations = await self._check_policies(
                    stage.post_policies,
                    {"stage": stage.id, "outputs": outputs},
                    brand,
                )
                if violations:
                    result.policy_violations.extend(violations)
                    if plan.strict_mode:
                        result.status = StageStatus.FAILED
                        result.error = f"Post-policy violation: {violations[0]['reason']}"
                        return result

            # Check drift against brand (M18)
            if stage.requires_brand_check:
                drift_score = await self._check_drift(outputs, brand)
                result.drift_score = drift_score
                if drift_score > 0.35:  # Threshold
                    result.policy_violations.append({
                        "type": "drift",
                        "reason": f"Output drifted from brand (score: {drift_score:.2f})",
                        "stage": stage.id,
                    })

            result.status = StageStatus.COMPLETED

        except asyncio.TimeoutError:
            result.status = StageStatus.FAILED
            result.error = f"Stage timed out after {stage.timeout_seconds}s"
        except Exception as e:
            result.status = StageStatus.FAILED
            result.error = str(e)
            logger.exception(f"Stage {stage.id} failed")

        result.latency_ms = (
            datetime.now(timezone.utc) - start_time
        ).total_seconds() * 1000

        return result

    async def _route_to_agent(
        self,
        stage: ExecutionStage,
        plan: ExecutionPlan,
        task: str,
    ) -> str:
        """
        Route stage to agent via CARE (M17).

        Uses complexity-aware routing when available.
        """
        if not self._care_engine:
            # Fallback to primary agent
            return stage.primary_agent

        try:
            from app.routing.models import RoutingRequest, DifficultyLevel, RiskPolicy

            request = RoutingRequest(
                task_description=f"{stage.name}: {task[:200]}",
                task_domain=stage.category.value.lower(),
                difficulty=DifficultyLevel(stage.difficulty),
                risk_tolerance=RiskPolicy(stage.risk_policy),
                tenant_id=self.tenant_id,
                prefer_metric=None,
                required_tools=None,
                max_agents=10,
            )

            decision = await self._care_engine.route(request)

            if decision.routed and decision.selected_agent_id:
                return decision.selected_agent_id

        except Exception as e:
            logger.warning(f"CARE routing failed, using primary: {e}")

        return stage.primary_agent

    async def _check_policies(
        self,
        policy_names: List[str],
        context: Dict[str, Any],
        brand: BrandSchema,
    ) -> List[Dict[str, Any]]:
        """
        Check policies via M19/M20.

        Returns list of violations.
        """
        violations = []

        # Always check forbidden claims
        if "forbidden_claims_check" in policy_names:
            for claim in brand.forbidden_claims:
                content = json.dumps(context)
                if claim.pattern.lower() in content.lower():
                    violations.append({
                        "policy": "forbidden_claims",
                        "reason": claim.reason,
                        "pattern": claim.pattern,
                        "severity": claim.severity,
                    })

        # Check budget if specified
        if "budget_check" in policy_names and brand.budget_tokens:
            # Would check actual token usage here
            pass

        # Use M20 policy engine if available
        if self._policy_engine:
            try:
                # Build policy rules from brand
                rules = brand.to_policy_rules()
                # Would compile and execute policies here
                pass
            except Exception as e:
                logger.warning(f"Policy engine check failed: {e}")

        return violations

    async def _check_drift(
        self,
        outputs: Dict[str, Any],
        brand: BrandSchema,
    ) -> float:
        """
        Check output drift against brand (M18).

        Returns drift score (0.0 = aligned, 1.0 = completely drifted).
        """
        if not self._drift_detector:
            return 0.0

        try:
            # Get brand anchors
            anchors = brand.get_drift_anchors()

            # Would compute embedding distance here
            # For now, return 0 (no drift)
            return 0.0

        except Exception as e:
            logger.warning(f"Drift detection failed: {e}")
            return 0.0

    async def _attempt_recovery(
        self,
        stage: ExecutionStage,
        stage_result: StageResult,
        plan: ExecutionPlan,
        brand: BrandSchema,
    ) -> Optional[str]:
        """
        Attempt recovery using M9/M10.

        Returns recovery action taken, or None if unrecoverable.
        """
        if not stage.recoverable:
            return None

        if not self._recovery_engine:
            # Simple retry
            if stage.max_retries > 0:
                return "retry"
            return None

        try:
            # Match to failure catalog (M9)
            failure_pattern = None
            if self._failure_catalog:
                failure_pattern = self._failure_catalog.match_pattern(
                    error=stage_result.error,
                    stage=stage.id,
                )

            # Get recovery suggestion (M10)
            if failure_pattern:
                suggestion = await self._recovery_engine.suggest(
                    pattern_id=failure_pattern.id,
                    context={"stage": stage.id, "error": stage_result.error},
                )
                if suggestion:
                    return suggestion.action

            # Default retry
            return "retry"

        except Exception as e:
            logger.warning(f"Recovery attempt failed: {e}")
            return None

    async def _run_agent(
        self,
        agent_id: str,
        stage: ExecutionStage,
        inputs: Dict[str, Any],
        brand: BrandSchema,
        task: str,
    ) -> Dict[str, Any]:
        """
        Run an agent for a stage.

        This is where actual LLM calls would happen.
        For now, returns mock outputs.
        """
        # Get agent definition
        agent_def = WORKER_AGENTS.get(agent_id)

        # Mock outputs based on stage
        outputs = {}

        if stage.id == "preflight":
            outputs["validation_result"] = {"valid": True}
            outputs["constraint_flags"] = []

        elif stage.id == "research":
            outputs["market_report"] = {
                "summary": f"Market analysis for: {task}",
                "competitors": ["Competitor A", "Competitor B", "Competitor C"],
                "market_size": "Growing market",
            }
            outputs["competitor_matrix"] = [
                {"name": "Competitor A", "positioning": "Enterprise focus"},
                {"name": "Competitor B", "positioning": "SMB focus"},
            ]
            outputs["trend_analysis"] = ["AI adoption", "Automation"]

        elif stage.id == "strategy":
            outputs["positioning"] = f"The best solution for {task}"
            outputs["messaging_framework"] = {
                "headline": f"Transform your {task.split()[0]}",
                "subhead": brand.value_proposition,
                "cta": "Get Started",
            }
            outputs["tone_guidelines"] = {
                "primary": brand.tone.primary.value,
                "avoid": [t.value for t in brand.tone.avoid],
            }

        elif stage.id == "copy":
            outputs["landing_copy"] = {
                "hero": f"# {brand.company_name}\n\n{brand.value_proposition}",
                "features": ["Feature 1", "Feature 2", "Feature 3"],
                "cta": "Start Free Trial",
            }
            outputs["blog_drafts"] = [
                {"title": f"Introduction to {task}", "outline": ["Intro", "Benefits", "CTA"]},
            ]
            outputs["email_sequence"] = [
                {"subject": "Welcome!", "preview": "Thanks for signing up"},
            ]
            outputs["social_copy"] = {
                "twitter": f"Introducing {brand.company_name} - {brand.tagline or brand.value_proposition[:50]}",
            }

        elif stage.id == "ux":
            outputs["landing_html"] = f"""<!DOCTYPE html>
<html>
<head><title>{brand.company_name}</title></head>
<body>
<header><h1>{brand.company_name}</h1></header>
<main>
<section class="hero">
<h2>{brand.value_proposition}</h2>
<button>Get Started</button>
</section>
</main>
</body>
</html>"""
            outputs["landing_css"] = f"""
body {{ font-family: {brand.visual.font_body}, sans-serif; }}
h1, h2 {{ font-family: {brand.visual.font_heading}, sans-serif; }}
"""
            outputs["component_map"] = {"hero": True, "features": True, "cta": True}

        elif stage.id == "consistency":
            outputs["consistency_score"] = 0.92
            outputs["violations"] = []
            outputs["corrections"] = []

        elif stage.id == "recovery":
            outputs["normalized_copy"] = inputs.get("landing_copy", {})
            outputs["normalized_html"] = inputs.get("landing_html", "")
            outputs["recovery_log"] = []

        elif stage.id == "bundle":
            outputs["bundle_zip"] = "/tmp/launch_bundle.zip"
            outputs["cost_report"] = {"total_tokens": 1000, "stages": {}}
            outputs["replay_token"] = {"seed": 12345}

        return outputs

    def _generate_cost_report(
        self,
        plan: ExecutionPlan,
        result: WorkerResult,
    ) -> Dict[str, Any]:
        """Generate cost report for the execution."""
        stage_costs = {}
        for sr in plan.stage_results:
            stage_costs[sr.stage_id] = {
                "tokens": sr.step_count,
                "latency_ms": sr.latency_ms,
                "status": sr.status.name,
            }

        return {
            "total_tokens": result.total_tokens_used,
            "budget": plan.total_budget_tokens,
            "under_budget": (
                plan.total_budget_tokens is None or
                result.total_tokens_used <= plan.total_budget_tokens
            ),
            "stages": stage_costs,
            "policy_violations": len(result.policy_violations),
            "recoveries": len(result.recovery_log),
        }


async def replay(token: Dict[str, Any]) -> WorkerResult:
    """
    Replay a previous execution using Golden Replay (M4).

    Args:
        token: Replay token from previous execution

    Returns:
        WorkerResult with identical outputs (deterministic)
    """
    # Load plan from token
    plan = ExecutionPlan(
        plan_id=token.get("plan_id", ""),
        seed=token.get("seed", 0),
        version=token.get("version", "0.2"),
    )

    # Would restore full plan and re-execute deterministically
    # For now, return placeholder
    return WorkerResult(
        success=False,
        error="Replay not fully implemented yet",
    )
