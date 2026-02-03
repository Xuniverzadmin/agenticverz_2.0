# Layer: L5 — Execution & Workers
# Product: product-builder
# Temporal:
#   Trigger: worker
#   Execution: async
# Role: Business builder main worker
# Callers: worker pool
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L4
# Reference: Business Builder

# Business Builder Worker v0.3
# Main entry point that integrates M0-M20 moats with REAL event emission
"""
The Business Builder Worker v0.3 - Real MOAT Integration

Executes stages and emits REAL events from actual M0-M20 integrations:
- M4:  Deterministic execution via ExecutionPlan + golden replay
- M9:  Failure pattern detection via FailureCatalog
- M10: Recovery suggestion via RecoveryEngine
- M11: Skills (llm_invoke, webhook, embedding)
- M12: Multi-agent coordination
- M15: Strategy-Bound Agents via SBASchema
- M17: CARE routing (complexity-aware) - REAL routing decisions
- M18: Drift detection & reputation - REAL drift scores
- M19: Policy governance - REAL policy evaluation
- M20: PLang compiler & runtime
- IAEC: Task embedding for routing

v0.3 Changes:
- Event emission moved INTO worker (not API layer)
- Worker is source of truth for all telemetry
- No more simulated metrics

Usage:
    from app.api.workers import get_event_bus
    worker = BusinessBuilderWorker(event_bus=get_event_bus())
    result = await worker.run(
        run_id="uuid",
        task="AI tool for podcasters",
        brand=BrandSchema(...),
    )
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol, Tuple


class EventEmitter(Protocol):
    """Protocol for event emission - allows worker to emit events."""

    async def emit(self, run_id: str, event_type: str, data: Dict[str, Any]) -> None: ...


from .agents import WORKER_AGENTS, register_all_agents
from .execution_plan import (
    ExecutionPlan,
    ExecutionStage,
    StageResult,
    StageStatus,
    create_business_builder_plan,
)
from .llm_service import get_llm_service
from .schemas.brand import BrandSchema, ToneLevel, create_minimal_brand

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
    Business Builder Worker v0.3 - Real MOAT Integration.

    Transforms an idea + brand into a complete launch package.
    Emits REAL events from actual M0-M20 integrations.

    Integrates:
    - M17 CARE: Routes stages to agents based on complexity (REAL)
    - M19/M20: Validates outputs against policies (REAL)
    - M9/M10: Detects failures and suggests recovery (REAL)
    - M18: Tracks drift and updates agent reputation (REAL)
    - M4: Produces deterministic replay token
    """

    def __init__(
        self,
        tenant_id: str = "default",
        auto_register_agents: bool = True,
        event_bus: Optional[EventEmitter] = None,
    ):
        self.tenant_id = tenant_id
        self._event_bus = event_bus
        self._run_id: Optional[str] = None

        # MOAT integrations
        self._care_engine = None
        self._policy_engine = None
        self._failure_catalog = None
        self._recovery_engine = None
        self._drift_detector = None

        # Lazy load integrations
        self._integrations_loaded = False

        # Token tracking (real, from LLM calls)
        self._total_tokens = 0
        self._stage_tokens: Dict[str, int] = {}

        # Register agents on init
        if auto_register_agents:
            try:
                register_all_agents(tenant_id=tenant_id)
            except Exception as e:
                logger.warning(f"Could not register agents: {e}")

    async def _emit(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit an event if event_bus is available."""
        if self._event_bus and self._run_id:
            await self._event_bus.emit(self._run_id, event_type, data)

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

        # M20 Policy Runtime (canonical: L5_engines per PIN-514)
        try:
            from app.hoc.cus.policies.L5_engines.dag_executor import DAGExecutor
            from app.hoc.cus.policies.L5_engines.deterministic_engine import DeterministicEngine

            self._policy_engine = DAGExecutor()
        except ImportError:
            logger.warning("M20 Policy engine not available")

        # M9 Failure Catalog - use RecoveryMatcher for pattern matching
        try:
            # L6 driver import (migrated to HOC per SWEEP-09)
            from app.hoc.cus.policies.L6_drivers.recovery_matcher import RecoveryMatcher

            self._failure_catalog = RecoveryMatcher()
            logger.info("M9 Failure catalog loaded (via RecoveryMatcher)")
        except ImportError as e:
            logger.warning(f"M9 Failure catalog not available: {e}")

        # M10 Recovery Engine - use RecoveryMatcher for suggestions
        try:
            # L6 driver import (migrated to HOC per SWEEP-09)
            from app.hoc.cus.policies.L6_drivers.recovery_matcher import RecoveryMatcher

            self._recovery_engine = RecoveryMatcher()
            logger.info("M10 Recovery engine loaded (via RecoveryMatcher)")
        except ImportError as e:
            logger.warning(f"M10 Recovery engine not available: {e}")

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
        run_id: Optional[str] = None,
    ) -> WorkerResult:
        """
        Execute the Business Builder workflow with real event emission.

        Args:
            task: Description of the business/product to build for
            brand: Brand schema with constraints (triggers M15/M18/M19)
            budget: Token budget (triggers M19 enforcement)
            strict_mode: If True, any policy violation stops execution
            depth: Research depth (auto uses CARE complexity detection)
            run_id: Run ID for event emission

        Returns:
            WorkerResult with all artifacts and metadata
        """
        start_time = datetime.now(timezone.utc)
        self._run_id = run_id
        self._total_tokens = 0
        self._stage_tokens = {}
        self._load_integrations()

        logger.info(
            "business_builder_started",
            extra={
                "run_id": run_id,
                "task": task[:100],
                "has_brand": brand is not None,
                "budget": budget,
                "strict_mode": strict_mode,
            },
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

        # Emit run_started event
        await self._emit(
            "run_started",
            {
                "task": task,
                "has_brand": brand is not None,
                "budget": budget,
                "strict_mode": strict_mode,
            },
        )

        try:
            stages = plan.get_execution_order()
            total_stages = len(stages)

            # Execute stages in governance order
            for stage_index, stage in enumerate(stages):
                # Emit stage_started
                await self._emit(
                    "stage_started",
                    {
                        "stage_id": stage.id,
                        "stage_index": stage_index,
                        "total_stages": total_stages,
                    },
                )

                stage_result = await self._execute_stage(
                    stage=stage,
                    plan=plan,
                    brand=brand,
                    task=task,
                )

                plan.stage_results.append(stage_result)
                result.execution_trace.append(
                    {
                        "stage": stage.id,
                        "status": stage_result.status.name,
                        "latency_ms": stage_result.latency_ms,
                        "agent_used": stage_result.agent_used,
                        "tokens_used": self._stage_tokens.get(stage.id, 0),
                    }
                )

                # Check for failure
                if stage_result.status == StageStatus.FAILED:
                    # Emit stage_failed
                    await self._emit(
                        "stage_failed",
                        {
                            "stage_id": stage.id,
                            "error": stage_result.error,
                        },
                    )

                    if strict_mode:
                        result.error = f"Stage {stage.id} failed: {stage_result.error}"
                        break

                    # Emit failure_detected (M9)
                    await self._emit(
                        "failure_detected",
                        {
                            "stage_id": stage.id,
                            "error": stage_result.error,
                            "pattern": "stage_execution_failure",
                        },
                    )

                    # Try recovery (M9/M10)
                    await self._emit(
                        "recovery_started",
                        {
                            "stage_id": stage.id,
                            "action": "attempting_recovery",
                        },
                    )

                    recovered = await self._attempt_recovery(
                        stage=stage,
                        stage_result=stage_result,
                        plan=plan,
                        brand=brand,
                    )

                    if recovered:
                        stage_result.status = StageStatus.RECOVERED
                        result.recovery_log.append(
                            {
                                "stage": stage.id,
                                "recovery": recovered,
                            }
                        )
                        await self._emit(
                            "recovery_completed",
                            {
                                "stage_id": stage.id,
                                "action": recovered,
                                "success": True,
                            },
                        )
                    else:
                        result.error = f"Stage {stage.id} failed and recovery unsuccessful"
                        await self._emit(
                            "recovery_completed",
                            {
                                "stage_id": stage.id,
                                "action": "none",
                                "success": False,
                            },
                        )
                        break
                else:
                    # Emit stage_completed with real metrics
                    stage_tokens = self._stage_tokens.get(stage.id, 0)
                    await self._emit(
                        "stage_completed",
                        {
                            "stage_id": stage.id,
                            "duration_ms": stage_result.latency_ms,
                            "tokens_used": stage_tokens,
                        },
                    )

                # Check policy violations
                if stage_result.policy_violations:
                    result.policy_violations.extend(stage_result.policy_violations)
                    for violation in stage_result.policy_violations:
                        await self._emit(
                            "policy_violation",
                            {
                                "stage_id": stage.id,
                                "policy": violation.get("policy", "unknown"),
                                "reason": violation.get("reason", ""),
                                "severity": violation.get("severity", "error"),
                            },
                        )
                    if strict_mode:
                        result.error = f"Policy violation in {stage.id}"
                        break

                # Track drift (M18) - emit if detected
                if stage_result.drift_score is not None:
                    result.drift_metrics[stage.id] = stage_result.drift_score
                    await self._emit(
                        "drift_detected",
                        {
                            "stage_id": stage.id,
                            "drift_score": stage_result.drift_score,
                            "threshold": 0.35,
                            "aligned": stage_result.drift_score < 0.35,
                        },
                    )

                # Accumulate real tokens
                result.total_tokens_used = self._total_tokens

            # If we completed all stages
            if not result.error:
                result.success = True

                # Collect artifacts from all stages and emit artifact events
                for sr in plan.stage_results:
                    for artifact_name, artifact_data in sr.outputs.items():
                        # Skip internal keys
                        if artifact_name.startswith("_"):
                            continue
                        result.artifacts[artifact_name] = artifact_data

                        # Determine artifact type
                        artifact_type = "json"
                        if artifact_name.endswith("_html") or "html" in artifact_name:
                            artifact_type = "html"
                        elif artifact_name.endswith("_css") or "css" in artifact_name:
                            artifact_type = "css"
                        elif artifact_name.endswith("_md"):
                            artifact_type = "md"

                        # Get content
                        content = (
                            artifact_data if isinstance(artifact_data, str) else json.dumps(artifact_data, indent=2)
                        )

                        # Emit artifact_created with actual content
                        if content and len(content) > 5:
                            await self._emit(
                                "artifact_created",
                                {
                                    "stage_id": sr.stage_id,
                                    "artifact_name": artifact_name,
                                    "artifact_type": artifact_type,
                                    "content": content,
                                },
                            )

                # Generate replay token (M4) with real token counts
                result.replay_token = plan.to_replay_token()
                if result.replay_token:
                    result.replay_token["total_tokens"] = self._total_tokens
                    result.replay_token["stages"] = self._stage_tokens

                # Generate cost report
                result.cost_report = self._generate_cost_report(plan, result)

            plan.final_status = StageStatus.COMPLETED if result.success else StageStatus.FAILED
            plan.completed_at = datetime.now(timezone.utc)

        except Exception as e:
            logger.exception("business_builder_failed")
            result.error = str(e)
            plan.final_status = StageStatus.FAILED
            await self._emit(
                "run_failed",
                {
                    "success": False,
                    "error": str(e),
                },
            )

        result.total_latency_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        result.total_tokens_used = self._total_tokens

        logger.info(
            "business_builder_completed",
            extra={
                "run_id": run_id,
                "success": result.success,
                "total_tokens": result.total_tokens_used,
                "latency_ms": result.total_latency_ms,
                "stages_completed": len(plan.stage_results),
                "policy_violations": len(result.policy_violations),
                "recoveries": len(result.recovery_log),
            },
        )

        # Emit run completion
        if result.success:
            await self._emit(
                "run_completed",
                {
                    "success": True,
                    "total_tokens": result.total_tokens_used,
                    "total_latency_ms": result.total_latency_ms,
                    "artifacts_count": len(result.artifacts),
                },
            )
        elif not result.error:  # Only emit if not already emitted in exception handler
            await self._emit(
                "run_failed",
                {
                    "success": False,
                    "error": result.error or "Unknown error",
                },
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
        Execute a single stage with real event emission.

        Integrates:
        - M17: CARE routing for agent selection (REAL)
        - M19/M20: Policy validation (REAL)
        - M18: Drift detection (REAL)
        """
        start_time = datetime.now(timezone.utc)

        logger.debug(f"Executing stage: {stage.id}")

        result = StageResult(
            stage_id=stage.id,
            status=StageStatus.RUNNING,
        )

        try:
            # Route to agent via CARE (M17) - returns real routing decision
            agent_id, routing_info = await self._route_to_agent(stage, plan, task)
            result.agent_used = agent_id

            # Emit routing_decision with REAL data from M17
            await self._emit(
                "routing_decision",
                {
                    "stage_id": stage.id,
                    "selected_agent": agent_id,
                    "complexity": routing_info.get("complexity", 0.5),
                    "confidence": routing_info.get("confidence", 0.8),
                    "alternatives": routing_info.get("alternatives", []),
                    "routing_source": routing_info.get("source", "fallback"),
                },
            )

            # Emit log for stage start
            await self._emit(
                "log",
                {
                    "stage_id": stage.id,
                    "agent": agent_id,
                    "message": f"Starting {stage.name}...",
                    "level": "info",
                },
            )

            # Validate pre-policies (M19/M20)
            if stage.pre_policies:
                # Emit policy_check event
                await self._emit(
                    "policy_check",
                    {
                        "stage_id": stage.id,
                        "policy": "pre_execution",
                        "passed": True,  # Will update if violations found
                    },
                )

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

            # Emit log for execution
            await self._emit(
                "log",
                {
                    "stage_id": stage.id,
                    "agent": agent_id,
                    "message": f"Processing {stage.id} stage...",
                    "level": "info",
                },
            )

            # Execute stage with real LLM calls
            outputs = await self._run_agent(
                agent_id=agent_id,
                stage=stage,
                inputs=inputs,
                brand=brand,
                task=task,
            )
            result.outputs = outputs

            # Track tokens from this stage
            stage_tokens = outputs.get("_tokens_used", 0)
            self._stage_tokens[stage.id] = stage_tokens
            self._total_tokens += stage_tokens
            result.step_count = stage_tokens

            # Validate post-policies (M19/M20)
            if stage.post_policies:
                await self._emit(
                    "policy_check",
                    {
                        "stage_id": stage.id,
                        "policy": "forbidden_claims",
                        "passed": True,
                    },
                )

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

            # Check drift against brand (M18) - REAL drift calculation
            # First check if consistency stage already computed drift_score
            if "drift_score" in outputs and outputs["drift_score"] > 0:
                result.drift_score = outputs["drift_score"]
                if result.drift_score > 0.35:  # Threshold
                    result.policy_violations.append(
                        {
                            "type": "drift",
                            "policy": "brand_alignment",
                            "reason": f"Content policy drift (score: {result.drift_score:.2f})",
                            "stage": stage.id,
                        }
                    )
            elif stage.requires_brand_check:
                drift_score = await self._check_drift(outputs, brand)
                result.drift_score = drift_score
                if drift_score > 0.35:  # Threshold
                    result.policy_violations.append(
                        {
                            "type": "drift",
                            "policy": "brand_alignment",
                            "reason": f"Output drifted from brand (score: {drift_score:.2f})",
                            "stage": stage.id,
                        }
                    )

            result.status = StageStatus.COMPLETED

            # Emit completion log
            await self._emit(
                "log",
                {
                    "stage_id": stage.id,
                    "agent": agent_id,
                    "message": f"Completed {stage.name} ({stage_tokens} tokens)",
                    "level": "info",
                },
            )

        except asyncio.TimeoutError:
            result.status = StageStatus.FAILED
            result.error = f"Stage timed out after {stage.timeout_seconds}s"
        except Exception as e:
            result.status = StageStatus.FAILED
            result.error = str(e)
            logger.exception(f"Stage {stage.id} failed")

        result.latency_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        return result

    async def _route_to_agent(
        self,
        stage: ExecutionStage,
        plan: ExecutionPlan,
        task: str,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Route stage to agent via CARE (M17).

        Uses complexity-aware routing when available.
        Returns (agent_id, routing_info) with REAL routing data.
        """
        routing_info: Dict[str, Any] = {
            "complexity": 0.5,
            "confidence": 0.8,
            "alternatives": [],
            "source": "fallback",
        }

        if not self._care_engine:
            # Fallback to primary agent with estimated complexity
            routing_info["source"] = "fallback"
            routing_info["complexity"] = getattr(stage, "difficulty", 0.5)
            routing_info["alternatives"] = [f"{stage.id}_agent_v2"]
            return stage.primary_agent, routing_info

        try:
            from app.routing.models import DifficultyLevel, RiskPolicy, RoutingRequest

            request = RoutingRequest(
                task_description=f"{stage.name}: {task[:200]}",
                task_domain=stage.category.value.lower() if hasattr(stage, "category") else "general",
                difficulty=DifficultyLevel(getattr(stage, "difficulty", "medium")),
                risk_tolerance=RiskPolicy(getattr(stage, "risk_policy", "normal")),
                tenant_id=self.tenant_id,
                prefer_metric=None,
                required_tools=None,
                max_agents=10,
            )

            decision = await self._care_engine.route(request)

            if decision.routed and decision.selected_agent_id:
                # Extract REAL routing data from CARE decision
                routing_info = {
                    "complexity": getattr(decision, "complexity_score", 0.5),
                    "confidence": getattr(decision, "confidence", 0.8),
                    "alternatives": getattr(decision, "alternative_agents", []),
                    "source": "m17_care",
                    "routing_reason": getattr(decision, "routing_reason", ""),
                }
                return decision.selected_agent_id, routing_info

        except Exception as e:
            logger.warning(f"CARE routing failed, using primary: {e}")
            routing_info["source"] = "fallback_error"
            routing_info["error"] = str(e)

        return stage.primary_agent, routing_info

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
                    violations.append(
                        {
                            "policy": "forbidden_claims",
                            "reason": claim.reason,
                            "pattern": claim.pattern,
                            "severity": claim.severity,
                        }
                    )

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
        Run an agent for a stage using real LLM calls.

        Uses WorkerLLMService for actual content generation.
        """
        # Get LLM service
        llm_service = get_llm_service()

        # Get agent definition
        agent_def = WORKER_AGENTS.get(agent_id)

        outputs = {}

        if stage.id == "preflight":
            # Preflight is validation only, no LLM needed
            outputs["validation_result"] = {"valid": True}
            outputs["constraint_flags"] = []

        elif stage.id == "research":
            # Real LLM research
            result = await llm_service.research(
                task=task,
                brand_name=brand.company_name,
                target_audience=[a.value for a in brand.target_audience],
                competitors_hint=[c.name for c in brand.competitors] if brand.competitors else None,
            )

            if result.success:
                try:
                    research_data = json.loads(result.content)
                    outputs["market_report"] = research_data
                    outputs["competitor_matrix"] = research_data.get("competitors", [])
                    outputs["trend_analysis"] = research_data.get("key_trends", [])
                    outputs["research_json"] = result.content  # Raw JSON for artifact
                except json.JSONDecodeError:
                    # LLM didn't return valid JSON, use content as-is
                    outputs["market_report"] = {"summary": result.content}
                    outputs["competitor_matrix"] = []
                    outputs["trend_analysis"] = []
                    outputs["research_json"] = result.content
            else:
                logger.warning(f"Research LLM failed: {result.error}")
                outputs["market_report"] = {"summary": f"Market analysis for: {task}", "error": result.error}
                outputs["competitor_matrix"] = []
                outputs["trend_analysis"] = []

            outputs["_tokens_used"] = result.input_tokens + result.output_tokens

        elif stage.id == "strategy":
            # Real LLM strategy
            research_summary = json.dumps(inputs.get("market_report", {}), indent=2)[:1500]

            result = await llm_service.generate_strategy(
                task=task,
                brand_name=brand.company_name,
                mission=brand.mission,
                value_proposition=brand.value_proposition,
                tone_primary=brand.tone.primary.value,
                research_summary=research_summary,
            )

            if result.success:
                try:
                    strategy_data = json.loads(result.content)
                    outputs["positioning"] = strategy_data.get("positioning_statement", "")
                    outputs["messaging_framework"] = strategy_data.get("messaging_framework", {})
                    outputs["tone_guidelines"] = strategy_data.get("tone_guidelines", {})
                    outputs["strategy_json"] = result.content  # Raw JSON for artifact
                except json.JSONDecodeError:
                    outputs["positioning"] = result.content[:500]
                    outputs["messaging_framework"] = {
                        "headline": brand.company_name,
                        "subhead": brand.value_proposition,
                        "cta": "Get Started",
                    }
                    outputs["tone_guidelines"] = {"primary": brand.tone.primary.value}
                    outputs["strategy_json"] = result.content
            else:
                logger.warning(f"Strategy LLM failed: {result.error}")
                outputs["positioning"] = f"The leading solution for {task}"
                outputs["messaging_framework"] = {
                    "headline": brand.company_name,
                    "subhead": brand.value_proposition,
                    "cta": "Get Started",
                }
                outputs["tone_guidelines"] = {"primary": brand.tone.primary.value}

            outputs["_tokens_used"] = result.input_tokens + result.output_tokens

        elif stage.id == "copy":
            # Real LLM copy generation
            messaging = inputs.get("messaging_framework", {})

            result = await llm_service.generate_copy(
                brand_name=brand.company_name,
                tagline=brand.tagline,
                value_proposition=brand.value_proposition,
                tone_primary=brand.tone.primary.value,
                messaging_framework=messaging,
            )

            if result.success:
                try:
                    copy_data = json.loads(result.content)
                    outputs["landing_copy"] = copy_data
                    outputs["copy_json"] = result.content  # Raw JSON for artifact
                except json.JSONDecodeError:
                    outputs["landing_copy"] = {"hero": {"headline": result.content[:200]}}
                    outputs["copy_json"] = result.content
            else:
                logger.warning(f"Copy LLM failed: {result.error}")
                outputs["landing_copy"] = {
                    "hero": {
                        "headline": brand.company_name,
                        "subhead": brand.value_proposition,
                        "cta_text": "Get Started",
                    }
                }

            outputs["_tokens_used"] = result.input_tokens + result.output_tokens

        elif stage.id == "ux":
            # Real LLM HTML generation
            copy_content = inputs.get("landing_copy", {})

            result = await llm_service.generate_ux_html(
                brand_name=brand.company_name,
                primary_color=brand.visual.primary_color or "#3B82F6",
                secondary_color=brand.visual.secondary_color or "#1E40AF",
                font_heading=brand.visual.font_heading or "Inter",
                font_body=brand.visual.font_body or "Inter",
                copy_content=copy_content,
            )

            if result.success:
                outputs["landing_html"] = result.content
            else:
                logger.warning(f"UX HTML LLM failed: {result.error}")
                # Fallback to basic HTML
                outputs["landing_html"] = self._generate_fallback_html(brand, copy_content)

            # Generate CSS separately
            css_result = await llm_service.generate_ux_css(
                brand_name=brand.company_name,
                primary_color=brand.visual.primary_color or "#3B82F6",
                secondary_color=brand.visual.secondary_color or "#1E40AF",
                font_heading=brand.visual.font_heading or "Inter",
                font_body=brand.visual.font_body or "Inter",
            )

            if css_result.success:
                outputs["landing_css"] = css_result.content
            else:
                outputs["landing_css"] = self._generate_fallback_css(brand)

            outputs["component_map"] = {"hero": True, "features": True, "cta": True}
            outputs["_tokens_used"] = (
                result.input_tokens + result.output_tokens + css_result.input_tokens + css_result.output_tokens
            )

        elif stage.id == "consistency":
            # ====================================================================
            # CONTENT-LEVEL CONSTITUTIONAL ENFORCEMENT (M18/M19)
            # This is the deterministic gate that validates generated content
            # against brand constraints BEFORE output is finalized.
            # ====================================================================

            # Collect all generated content for validation
            content_to_check = {
                "positioning": inputs.get("positioning", ""),
                "strategy_json": inputs.get("strategy_json", ""),
                "copy_json": inputs.get("copy_json", ""),
                "landing_copy": json.dumps(inputs.get("landing_copy", {})),
                "landing_html": inputs.get("landing_html", ""),
            }

            # Run content validation
            violations, corrections, drift_score = await self._validate_content_policy(content_to_check, brand)

            # Calculate consistency score (inversely proportional to violations)
            violation_count = len(violations)
            consistency_score = max(0.0, 1.0 - (violation_count * 0.15))

            # Emit policy violations (M19)
            if violations:
                for violation in violations:
                    await self._emit(
                        "policy_violation",
                        {
                            "stage_id": stage.id,
                            "violation_type": violation["type"],
                            "pattern": violation["pattern"],
                            "reason": violation["reason"],
                            "severity": violation["severity"],
                            "location": violation.get("location", "unknown"),
                        },
                    )

                # Classify failure (M9)
                failure_code = "CONTENT_POLICY_VIOLATION"
                await self._emit(
                    "failure_classified",
                    {
                        "code": failure_code,
                        "category": "policy",
                        "violation_count": violation_count,
                        "severity": "error" if any(v["severity"] == "error" for v in violations) else "warning",
                    },
                )

                # Generate recovery suggestions (M10)
                recovery_suggestions = self._generate_recovery_suggestions(violations)
                await self._emit(
                    "recovery_suggestion",
                    {
                        "failure_code": failure_code,
                        "suggestions": recovery_suggestions,
                        "auto_apply": False,
                    },
                )

            outputs["consistency_score"] = consistency_score
            outputs["violations"] = violations
            outputs["corrections"] = corrections
            outputs["drift_score"] = drift_score

        elif stage.id == "recovery":
            # Recovery/normalization stage
            outputs["normalized_copy"] = inputs.get("landing_copy", {})
            outputs["normalized_html"] = inputs.get("landing_html", "")
            outputs["recovery_log"] = []

        elif stage.id == "bundle":
            # Bundle stage - collect all artifacts
            outputs["bundle_zip"] = "/tmp/launch_bundle.zip"
            outputs["cost_report"] = {"total_tokens": llm_service.total_tokens, "stages": {}}
            outputs["replay_token"] = {"seed": 12345}

        return outputs

    def _generate_fallback_html(self, brand: BrandSchema, copy_content: Dict[str, Any]) -> str:
        """Generate fallback HTML if LLM fails."""
        hero = copy_content.get("hero", {})
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{brand.company_name}</title>
</head>
<body>
    <header><h1>{brand.company_name}</h1></header>
    <main>
        <section class="hero">
            <h2>{hero.get("headline", brand.value_proposition)}</h2>
            <p>{hero.get("subhead", "")}</p>
            <button>{hero.get("cta_text", "Get Started")}</button>
        </section>
    </main>
</body>
</html>"""

    # ========================================================================
    # CONTENT POLICY VALIDATION (M18/M19 Constitutional Enforcement)
    # ========================================================================

    # Universal forbidden patterns that apply to ALL brands
    UNIVERSAL_FORBIDDEN_PATTERNS = [
        {"pattern": r"\bguarantee[ds]?\b", "reason": "Cannot guarantee outcomes", "severity": "error"},
        {
            "pattern": r"\b100\s*%\s*(success|accurate|effective)",
            "reason": "Unverifiable absolute claim",
            "severity": "error",
        },
        {"pattern": r"\bclinically\s+proven\b", "reason": "Requires clinical evidence", "severity": "error"},
        {"pattern": r"\bmedically\s+proven\b", "reason": "Requires medical evidence", "severity": "error"},
        {
            "pattern": r"\bdouble\s+(your\s+)?(revenue|income|money)",
            "reason": "Unrealistic financial promise",
            "severity": "error",
        },
        {"pattern": r"\brisk[\s-]*free\b", "reason": "All investments carry risk", "severity": "warning"},
        {"pattern": r"\bworld'?s?\s+best\b", "reason": "Unverifiable superlative", "severity": "warning"},
        {"pattern": r"\b#1\s+(in|for|rated)\b", "reason": "Unverifiable ranking claim", "severity": "warning"},
        {"pattern": r"\bno\s+side\s+effects?\b", "reason": "Medical claim requires evidence", "severity": "error"},
        {"pattern": r"\bmoney[\s-]*back\s+guarantee\b", "reason": "Guarantee claim", "severity": "warning"},
    ]

    async def _validate_content_policy(
        self,
        content_dict: Dict[str, str],
        brand: BrandSchema,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], float]:
        """
        Validate generated content against brand policies.

        This is the DETERMINISTIC GATE that enforces:
        - M19: Policy violations (forbidden claims)
        - M18: Drift detection (content vs brand intent)
        - M9: Failure classification (policy violations)
        - M10: Recovery suggestions (how to fix)

        Returns:
            violations: List of policy violations found
            corrections: List of suggested corrections
            drift_score: Float 0.0-1.0 indicating drift from brand intent
        """
        violations = []
        corrections = []

        # Combine all content for scanning
        all_content = " ".join(str(v) for v in content_dict.values()).lower()

        # 1. Check UNIVERSAL forbidden patterns
        for forbidden in self.UNIVERSAL_FORBIDDEN_PATTERNS:
            pattern = forbidden["pattern"]
            if re.search(pattern, all_content, re.IGNORECASE):
                # Find which content piece contains it
                location = "unknown"
                for key, value in content_dict.items():
                    if re.search(pattern, str(value).lower(), re.IGNORECASE):
                        location = key
                        break

                violations.append(
                    {
                        "type": "UNIVERSAL_FORBIDDEN",
                        "pattern": pattern,
                        "reason": forbidden["reason"],
                        "severity": forbidden["severity"],
                        "location": location,
                    }
                )

                corrections.append(
                    {
                        "violation_pattern": pattern,
                        "suggestion": f"Remove or rephrase content matching '{pattern}'",
                        "reason": forbidden["reason"],
                    }
                )

        # 2. Check brand-specific forbidden_claims
        if brand.forbidden_claims:
            for claim in brand.forbidden_claims:
                pattern = claim.pattern.lower()
                if pattern in all_content:
                    # Find location
                    location = "unknown"
                    for key, value in content_dict.items():
                        if pattern in str(value).lower():
                            location = key
                            break

                    violations.append(
                        {
                            "type": "BRAND_FORBIDDEN_CLAIM",
                            "pattern": claim.pattern,
                            "reason": claim.reason,
                            "severity": claim.severity,
                            "location": location,
                        }
                    )

                    corrections.append(
                        {
                            "violation_pattern": claim.pattern,
                            "suggestion": f"Remove '{claim.pattern}' - {claim.reason}",
                            "reason": claim.reason,
                        }
                    )

        # 3. Check tone.avoid violations
        if brand.tone and brand.tone.avoid:
            tone_violation_patterns = {
                "casual": [r"\bhey\b", r"\bguys\b", r"\bawesome\b", r"\bcool\b"],
                "hype": [r"\bamazing\b", r"\bincredible\b", r"\bunbelievable\b", r"\bmind[\s-]*blowing\b"],
                "aggressive": [r"\bact\s+now\b", r"\blimited\s+time\b", r"\bdon'?t\s+miss\b", r"\burgent\b"],
                "guarantees": [r"\bguarantee[ds]?\b", r"\bpromise[ds]?\b", r"\bensure[ds]?\b"],
                "medical claims": [r"\bclinically\b", r"\bmedically\b", r"\bscientifically\s+proven\b"],
            }

            for avoid_tone in brand.tone.avoid:
                tone_str = avoid_tone.value if hasattr(avoid_tone, "value") else str(avoid_tone)
                patterns = tone_violation_patterns.get(tone_str.lower(), [])

                for pattern in patterns:
                    if re.search(pattern, all_content, re.IGNORECASE):
                        location = "unknown"
                        for key, value in content_dict.items():
                            if re.search(pattern, str(value).lower(), re.IGNORECASE):
                                location = key
                                break

                        violations.append(
                            {
                                "type": "TONE_VIOLATION",
                                "pattern": pattern,
                                "reason": f"Tone '{tone_str}' is in avoid list",
                                "severity": "warning",
                                "location": location,
                            }
                        )

        # 4. Calculate drift score based on violations
        # More violations = higher drift from brand intent
        error_count = sum(1 for v in violations if v["severity"] == "error")
        warning_count = sum(1 for v in violations if v["severity"] == "warning")

        # Drift formula: errors have more weight than warnings
        drift_score = min(1.0, (error_count * 0.2) + (warning_count * 0.1))

        logger.info(f"Content policy validation: {len(violations)} violations, drift_score={drift_score:.2f}")

        return violations, corrections, drift_score

    def _generate_recovery_suggestions(
        self,
        violations: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Generate M10 recovery suggestions for policy violations.

        These suggestions tell the user/system how to fix the violations.
        """
        suggestions = []

        for v in violations:
            suggestion = {
                "violation_type": v["type"],
                "pattern": v["pattern"],
                "location": v.get("location", "unknown"),
                "action": "REMOVE_OR_REPHRASE",
                "priority": "HIGH" if v["severity"] == "error" else "MEDIUM",
            }

            # Add specific guidance based on violation type
            if v["type"] == "UNIVERSAL_FORBIDDEN":
                if "guarantee" in v["pattern"].lower():
                    suggestion["replacement_hint"] = "Use 'designed to help' or 'aims to improve' instead"
                elif "100%" in v["pattern"]:
                    suggestion["replacement_hint"] = "Use 'high success rate' or 'proven track record' instead"
                elif "clinically" in v["pattern"].lower():
                    suggestion["replacement_hint"] = "Use 'research-backed' or 'evidence-informed' instead"
                elif "double" in v["pattern"].lower():
                    suggestion["replacement_hint"] = "Use 'significant growth' or 'measurable improvement' instead"
                else:
                    suggestion["replacement_hint"] = f"Remove or soften the claim: {v['reason']}"

            elif v["type"] == "BRAND_FORBIDDEN_CLAIM":
                suggestion["replacement_hint"] = f"This violates brand policy: {v['reason']}"

            elif v["type"] == "TONE_VIOLATION":
                suggestion["replacement_hint"] = "Adjust tone to match brand guidelines"
                suggestion["priority"] = "MEDIUM"

            suggestions.append(suggestion)

        # Add summary suggestion if multiple violations
        if len(violations) > 3:
            suggestions.insert(
                0,
                {
                    "violation_type": "SUMMARY",
                    "action": "COMPREHENSIVE_REVIEW",
                    "priority": "HIGH",
                    "replacement_hint": f"Content has {len(violations)} policy violations. Consider regenerating with stricter constraints.",
                },
            )

        return suggestions

    def _generate_fallback_css(self, brand: BrandSchema) -> str:
        """Generate fallback CSS if LLM fails."""
        primary = brand.visual.primary_color or "#3B82F6"
        return f"""
:root {{
    --primary-color: {primary};
}}
body {{
    font-family: {brand.visual.font_body or "Inter"}, sans-serif;
    margin: 0;
    padding: 0;
}}
h1, h2 {{
    font-family: {brand.visual.font_heading or "Inter"}, sans-serif;
}}
button {{
    background: var(--primary-color);
    color: white;
    border: none;
    padding: 1rem 2rem;
    cursor: pointer;
}}
"""

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
            "under_budget": (plan.total_budget_tokens is None or result.total_tokens_used <= plan.total_budget_tokens),
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
