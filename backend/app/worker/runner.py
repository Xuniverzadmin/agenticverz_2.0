"""
Runner: executes a single run's plan steps, handles retries and backoff.
This runner expects `run_row` to contain id, agent_id, goal, plan_json, attempts.
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlmodel import Session

# Phase 5A: Budget enforcement decision emission
from ..contracts.decisions import emit_budget_enforcement_decision
from ..db import Agent, Memory, Provenance, Run, engine
from ..events import get_publisher
from ..metrics import (
    nova_runs_failed_total,
    nova_runs_total,
    nova_skill_attempts_total,
    nova_skill_duration_seconds,
)
from ..skills import get_skill_config
from ..skills.executor import (
    SkillExecutionError,
    SkillExecutor,
)
from ..utils.budget_tracker import deduct_budget, get_budget_tracker, record_cost
from ..utils.plan_inspector import validate_plan

logger = logging.getLogger("nova.worker.runner")

MAX_ATTEMPTS = int(os.getenv("RUN_MAX_ATTEMPTS", "5"))


# =============================================================================
# Phase 5A: Budget Context for Hard Budget Enforcement
# =============================================================================


@dataclass
class BudgetContext:
    """
    Immutable budget context loaded from PRE-RUN (Agent configuration).

    This is read-only during run execution. The runner enforces; it does not decide.
    """

    mode: str  # "hard" or "soft"
    limit_cents: int  # Total budget limit in cents
    consumed_cents: int  # Already spent before this run
    hard_limit: bool  # Whether to halt on budget exhaustion

    @property
    def remaining_cents(self) -> int:
        """Remaining budget in cents."""
        return max(0, self.limit_cents - self.consumed_cents)

    def would_exceed(self, additional_cents: int) -> bool:
        """Check if additional spending would exceed budget (for hard mode)."""
        if not self.hard_limit:
            return False
        return (self.consumed_cents + additional_cents) > self.limit_cents


def _load_budget_context(agent_id: str) -> BudgetContext:
    """
    Load budget context from Agent configuration.

    This is the PRE-RUN snapshot. It's immutable for the duration of the run.
    Default to soft mode if agent not found or no budget configured.
    """
    with Session(engine) as session:
        agent = session.get(Agent, agent_id)
        if not agent:
            logger.warning("budget_context_agent_not_found", extra={"agent_id": agent_id})
            return BudgetContext(
                mode="soft",
                limit_cents=0,
                consumed_cents=0,
                hard_limit=False,
            )

        # Get budget configuration from agent
        budget_cents = agent.budget_cents or 0
        spent_cents = agent.spent_cents or 0

        # Determine if hard limit is enabled
        # Check capabilities_json for hard_limit setting
        hard_limit = True  # Default to hard limit per BudgetConfig schema
        if agent.capabilities_json:
            try:
                caps = json.loads(agent.capabilities_json)
                # Look for budget config in capabilities
                budget_config = caps.get("budget", {})
                hard_limit = budget_config.get("hard_limit", True)
            except (json.JSONDecodeError, TypeError):
                pass

        mode = "hard" if hard_limit and budget_cents > 0 else "soft"

        return BudgetContext(
            mode=mode,
            limit_cents=budget_cents,
            consumed_cents=spent_cents,
            hard_limit=hard_limit and budget_cents > 0,
        )


# Anthropic pricing (as of 2024) - cents per 1M tokens
# Claude Sonnet 4: $3/1M input, $15/1M output
ANTHROPIC_PRICING = {
    "claude-sonnet-4-20250514": {"input": 300, "output": 1500},  # cents per 1M tokens
    "claude-3-5-sonnet-20241022": {"input": 300, "output": 1500},
    "claude-3-opus-20240229": {"input": 1500, "output": 7500},
    "claude-3-haiku-20240307": {"input": 25, "output": 125},
}
DEFAULT_PRICING = {"input": 300, "output": 1500}  # Default to Sonnet pricing


def calculate_llm_cost_cents(model: str, input_tokens: int, output_tokens: int) -> int:
    """Calculate LLM cost in cents based on token usage.

    Args:
        model: Model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Cost in cents (rounded up)
    """
    pricing = ANTHROPIC_PRICING.get(model, DEFAULT_PRICING)

    # Cost = (tokens / 1M) * price_per_1M
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]

    total_cents = input_cost + output_cost

    # Round up to nearest cent (minimum 1 cent if any tokens used)
    import math

    return max(1, math.ceil(total_cents)) if (input_tokens + output_tokens) > 0 else 0


class RunRunner:
    """Executes a single run's plan steps."""

    def __init__(self, run_id: str, publisher=None):
        self.run_id = run_id
        self.publisher = publisher or get_publisher()

    def _get_run(self) -> Optional[Run]:
        """Fetch run from database."""
        with Session(engine) as session:
            return session.get(Run, self.run_id)

    def _update_run(
        self,
        status: str,
        attempts: Optional[int] = None,
        next_attempt_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        error_message: Optional[str] = None,
        plan_json: Optional[str] = None,
        tool_calls_json: Optional[str] = None,
        duration_ms: Optional[float] = None,
    ):
        """Update run in database."""
        with Session(engine) as session:
            run = session.get(Run, self.run_id)
            if run:
                run.status = status
                if attempts is not None:
                    run.attempts = attempts
                if next_attempt_at is not None:
                    run.next_attempt_at = next_attempt_at
                if completed_at is not None:
                    run.completed_at = completed_at
                if error_message is not None:
                    run.error_message = error_message
                if plan_json is not None:
                    run.plan_json = plan_json
                if tool_calls_json is not None:
                    run.tool_calls_json = tool_calls_json
                if duration_ms is not None:
                    run.duration_ms = duration_ms
                session.add(run)
                session.commit()

    def run(self):
        """Execute the run synchronously (called from thread pool)."""
        # Run the async execute in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._execute())
        finally:
            # INFRA-001 FIX: Properly clean up async resources before closing loop
            # This prevents CLOSE_WAIT socket leaks from httpx connections
            try:
                # Cancel all pending tasks
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                # Allow cancelled tasks to complete
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                # Shutdown async generators
                loop.run_until_complete(loop.shutdown_asyncgens())
                # Shutdown default executor (Python 3.9+)
                if hasattr(loop, "shutdown_default_executor"):
                    loop.run_until_complete(loop.shutdown_default_executor())
            except Exception:
                logger.debug("cleanup_exception_during_loop_close", exc_info=True)
            finally:
                loop.close()

    async def _execute(self):
        """Execute run steps asynchronously."""
        run = self._get_run()
        if not run:
            logger.error("run_not_found", extra={"run_id": self.run_id})
            return

        start_time = time.time()
        self.publisher.publish("run.started", {"run_id": self.run_id, "agent_id": run.agent_id, "goal": run.goal})
        planner_name = os.getenv("PLANNER_BACKEND", "stub")
        nova_runs_total.labels(status="started", planner=planner_name).inc()

        logger.info("run_execution_start", extra={"run_id": self.run_id, "agent_id": run.agent_id, "goal": run.goal})

        # Phase 5A: Load budget context from PRE-RUN (Agent configuration)
        # This is immutable for the duration of the run
        budget_context = _load_budget_context(run.agent_id)
        run_consumed_cents = 0  # Track costs accumulated during THIS run

        logger.debug(
            "budget_context_loaded",
            extra={
                "run_id": self.run_id,
                "mode": budget_context.mode,
                "limit_cents": budget_context.limit_cents,
                "consumed_cents": budget_context.consumed_cents,
                "hard_limit": budget_context.hard_limit,
            },
        )

        try:
            # Parse plan
            plan = json.loads(run.plan_json) if run.plan_json else {"steps": []}
            steps = plan.get("steps", [])

            if not steps:
                # No plan yet - generate one using planner with memory context
                from ..memory import get_retriever
                from ..planners import get_planner
                from ..skills import get_skill_manifest

                # Retrieve memory context for planning
                retriever = get_retriever()
                context = retriever.get_context_for_planning(
                    agent_id=run.agent_id,
                    goal=run.goal,
                    current_run_id=self.run_id,
                )

                logger.debug(
                    "planning_with_context",
                    extra={
                        "run_id": self.run_id,
                        "has_summary": context.get("context_summary") is not None,
                        "memory_count": len(context.get("memory_snippets") or []),
                    },
                )

                # Generate plan
                planner = get_planner()
                plan = planner.plan(
                    agent_id=run.agent_id,
                    goal=run.goal,
                    context_summary=context.get("context_summary"),
                    memory_snippets=context.get("memory_snippets"),
                    tool_manifest=get_skill_manifest(),
                )
                steps = plan.get("steps", [])

                # Validate plan safety before execution
                budget_status = get_budget_tracker().get_status(run.agent_id)
                agent_budget = budget_status.remaining_cents if budget_status else 0

                validation = validate_plan(plan, agent_budget_cents=agent_budget)
                if not validation.valid:
                    error_messages = "; ".join(e.message for e in validation.errors[:3])
                    raise RuntimeError(f"Plan validation failed: {error_messages}")

                if validation.warnings:
                    logger.warning(
                        "plan_validation_warnings",
                        extra={
                            "run_id": self.run_id,
                            "warnings": [w.message for w in validation.warnings],
                        },
                    )

                # Track planner LLM costs if available
                metadata = plan.get("metadata", {})
                if metadata.get("input_tokens") or metadata.get("output_tokens"):
                    input_tokens = metadata.get("input_tokens", 0)
                    output_tokens = metadata.get("output_tokens", 0)
                    model = metadata.get("model", "claude-sonnet-4-20250514")
                    provider = metadata.get("planner", "anthropic")

                    # Calculate cost
                    cost_cents = calculate_llm_cost_cents(model, input_tokens, output_tokens)

                    # Record cost for auditing
                    record_cost(
                        run_id=self.run_id,
                        agent_id=run.agent_id,
                        provider=provider,
                        model=model,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        cost_cents=cost_cents,
                    )

                    # Deduct from agent budget
                    deduct_success = deduct_budget(run.agent_id, cost_cents)
                    if not deduct_success:
                        logger.warning(
                            "planner_cost_deduction_failed",
                            extra={
                                "run_id": self.run_id,
                                "agent_id": run.agent_id,
                                "cost_cents": cost_cents,
                            },
                        )

                    logger.info(
                        "planner_cost_tracked",
                        extra={
                            "run_id": self.run_id,
                            "model": model,
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "cost_cents": cost_cents,
                        },
                    )

            tool_calls = []
            step_context = {}  # Context for step output interpolation

            # Create executor with validation enabled
            executor = SkillExecutor(
                validate_input=True,
                validate_output=False,  # Output validation optional
                strict_mode=False,  # Don't fail on validation warnings
            )

            for step in steps:
                skill_name = step.get("skill", "http_call")
                step_id = step.get("step_id", "s1")
                params = step.get("params", {})
                on_error = step.get("on_error", "abort")  # abort, continue, retry
                max_step_retries = step.get("retry_count", 3)

                # Get skill config from global config or use defaults
                skill_config = get_skill_config(skill_name)

                # Interpolate params with step context
                interpolated_params = executor._interpolate_params(params, step_context)

                step_start = time.time()
                step_attempts = 0
                step_error = None
                result = None
                step_status = None

                # Step-level retry loop
                while step_attempts < max_step_retries:
                    step_attempts += 1
                    nova_skill_attempts_total.labels(skill=skill_name).inc()

                    try:
                        # Execute through validated executor
                        result, step_status = await executor.execute(
                            skill_name=skill_name,
                            params=interpolated_params,
                            step_id=step_id,
                            skill_config=skill_config,
                        )
                        step_error = None  # Clear error on success
                        break  # Success - exit retry loop

                    except SkillExecutionError as e:
                        step_error = e
                        logger.warning(
                            "step_execution_error",
                            extra={
                                "run_id": self.run_id,
                                "step_id": step_id,
                                "skill": skill_name,
                                "attempt": step_attempts,
                                "max_attempts": max_step_retries,
                                "error": str(e)[:200],
                                "retryable": e.is_retryable,
                            },
                        )

                        # Don't retry if error is not retryable
                        if not e.is_retryable:
                            break

                        # Retry with backoff
                        if step_attempts < max_step_retries:
                            backoff = min(0.5 * (2 ** (step_attempts - 1)), 30)
                            await asyncio.sleep(backoff)

                # Handle step failure based on on_error policy
                if step_error:
                    if on_error == "abort":
                        raise RuntimeError(f"step_failed:{step_id}:{step_error}") from step_error
                    elif on_error == "continue":
                        # Log and continue to next step
                        logger.warning(
                            "step_failed_continuing",
                            extra={
                                "run_id": self.run_id,
                                "step_id": step_id,
                                "skill": skill_name,
                                "error": str(step_error)[:200],
                            },
                        )
                        # Create a failure result for tool_calls
                        result = {
                            "skill": skill_name,
                            "skill_version": "unknown",
                            "result": {"error": str(step_error)[:200], "status": "failed"},
                            "side_effects": {},
                        }
                        step_status = "failed"
                    # "retry" is handled by the loop above

                step_duration = time.time() - step_start
                nova_skill_duration_seconds.labels(skill=skill_name).observe(step_duration)

                # Store step output in context for later steps
                output_key = step.get("output_key", step_id)
                step_context[output_key] = result.get("result", {}) if result else {}

                tool_call = {
                    "step_id": step_id,
                    "skill": skill_name,
                    "skill_version": result.get("skill_version") if result else "unknown",
                    "request": interpolated_params,
                    "response": result.get("result", {}) if result else {},
                    "side_effects": result.get("side_effects", {}) if result else {},
                    "duration": round(step_duration, 3),
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "status": step_status.value
                    if hasattr(step_status, "value")
                    else str(step_status)
                    if step_status
                    else "unknown",
                    "attempts": step_attempts,
                    "on_error": on_error,
                }
                tool_calls.append(tool_call)

                logger.info(
                    "run_step_result",
                    extra={
                        "run_id": self.run_id,
                        "step_id": step_id,
                        "skill": skill_name,
                        "duration": round(step_duration, 3),
                        "status": tool_call["status"],
                    },
                )

                self.publisher.publish(
                    "run.step.completed",
                    {
                        "run_id": self.run_id,
                        "step_id": step_id,
                        "skill": skill_name,
                        "duration": round(step_duration, 3),
                        "result": result.get("result", {}),
                        "status": tool_call["status"],
                    },
                )

                # Store memory
                with Session(engine) as session:
                    memory = Memory(
                        agent_id=run.agent_id,
                        memory_type="skill_result",
                        text=f"Skill result: {json.dumps(result.get('result', {}))}",
                        meta=json.dumps(
                            {
                                "goal": run.goal,
                                "skill": skill_name,
                                "skill_version": result.get("skill_version"),
                                "run_id": self.run_id,
                                "step_id": step_id,
                            }
                        ),
                    )
                    session.add(memory)
                    session.commit()

                # =============================================================
                # Phase 5A: Hard Budget Enforcement (THE CHOKE POINT)
                # This is BETWEEN steps - never mid-step.
                # =============================================================

                # 1. Extract step cost from side_effects
                step_cost_cents = 0
                if result:
                    side_effects = result.get("side_effects", {})
                    step_cost_cents = side_effects.get("cost_cents", 0)

                # 2. Track run consumed and deduct from agent budget
                if step_cost_cents > 0:
                    run_consumed_cents += step_cost_cents
                    deduct_budget(run.agent_id, step_cost_cents)

                    logger.debug(
                        "step_cost_tracked",
                        extra={
                            "run_id": self.run_id,
                            "step_id": step_id,
                            "step_cost_cents": step_cost_cents,
                            "run_consumed_cents": run_consumed_cents,
                        },
                    )

                # 3. Check hard budget enforcement
                # Total consumed = initial consumed + this run's consumed
                total_consumed = budget_context.consumed_cents + run_consumed_cents

                if budget_context.hard_limit and total_consumed >= budget_context.limit_cents:
                    # HARD BUDGET HALT - Deterministic, clean, immediate
                    completed_steps = len(tool_calls)
                    total_steps = len(steps)

                    logger.warning(
                        "hard_budget_halt",
                        extra={
                            "run_id": self.run_id,
                            "budget_limit_cents": budget_context.limit_cents,
                            "total_consumed_cents": total_consumed,
                            "run_consumed_cents": run_consumed_cents,
                            "completed_steps": completed_steps,
                            "total_steps": total_steps,
                        },
                    )

                    # 4. Emit decision record (exactly once)
                    emit_budget_enforcement_decision(
                        run_id=self.run_id,
                        budget_limit_cents=budget_context.limit_cents,
                        budget_consumed_cents=total_consumed,
                        step_cost_cents=step_cost_cents,
                        completed_steps=completed_steps,
                        total_steps=total_steps,
                        tenant_id=run.tenant_id or "default",
                    )

                    # 5. Update run with halted status and partial results
                    duration_ms = (time.time() - start_time) * 1000
                    completed_at = datetime.now(timezone.utc)

                    self._update_run(
                        status="halted",
                        attempts=run.attempts,
                        completed_at=completed_at,
                        plan_json=json.dumps(plan),
                        tool_calls_json=json.dumps(tool_calls),
                        duration_ms=duration_ms,
                        error_message=f"Hard budget limit reached: {total_consumed}c consumed >= {budget_context.limit_cents}c limit",
                    )

                    # 6. Create provenance record for outcome reconciliation
                    with Session(engine) as session:
                        provenance = Provenance(
                            run_id=self.run_id,
                            agent_id=run.agent_id,
                            goal=run.goal,
                            status="halted",  # New status for partial completion
                            plan_json=json.dumps(plan),
                            tool_calls_json=json.dumps(tool_calls),
                            attempts=run.attempts,
                            started_at=run.started_at,
                            completed_at=completed_at,
                            duration_ms=duration_ms,
                        )
                        session.add(provenance)
                        session.commit()

                    # 7. Publish halted event
                    self.publisher.publish(
                        "run.halted",
                        {
                            "run_id": self.run_id,
                            "status": "halted",
                            "halt_reason": "hard_budget_limit",
                            "budget_limit_cents": budget_context.limit_cents,
                            "budget_consumed_cents": total_consumed,
                            "completed_steps": completed_steps,
                            "total_steps": total_steps,
                            "duration_ms": duration_ms,
                        },
                    )

                    nova_runs_total.labels(status="halted", planner=planner_name).inc()

                    # Clean exit - no exception, no retry
                    return

            # Success
            duration_ms = (time.time() - start_time) * 1000
            completed_at = datetime.now(timezone.utc)

            self._update_run(
                status="succeeded",
                attempts=run.attempts,
                completed_at=completed_at,
                plan_json=json.dumps(plan),
                tool_calls_json=json.dumps(tool_calls),
                duration_ms=duration_ms,
            )

            # Create provenance record
            with Session(engine) as session:
                provenance = Provenance(
                    run_id=self.run_id,
                    agent_id=run.agent_id,
                    goal=run.goal,
                    status="succeeded",
                    plan_json=json.dumps(plan),
                    tool_calls_json=json.dumps(tool_calls),
                    attempts=run.attempts,
                    started_at=run.started_at,
                    completed_at=completed_at,
                    duration_ms=duration_ms,
                )
                session.add(provenance)
                session.commit()

            self.publisher.publish(
                "run.completed", {"run_id": self.run_id, "status": "succeeded", "duration_ms": duration_ms}
            )

            logger.info(
                "run_completed", extra={"run_id": self.run_id, "status": "succeeded", "duration_ms": duration_ms}
            )
            planner_name = os.getenv("PLANNER_BACKEND", "stub")
            nova_runs_total.labels(status="succeeded", planner=planner_name).inc()

        except Exception as exc:
            # Failure: increment attempts and set next_attempt_at with exponential backoff
            run = self._get_run()
            attempts = (run.attempts or 0) + 1

            if attempts >= MAX_ATTEMPTS:
                self._update_run(
                    status="failed",
                    attempts=attempts,
                    error_message=str(exc)[:500],
                    completed_at=datetime.now(timezone.utc),
                )
                self.publisher.publish(
                    "run.failed", {"run_id": self.run_id, "attempts": attempts, "error": str(exc)[:200]}
                )
                logger.exception("run_failed_permanent", extra={"run_id": self.run_id, "attempts": attempts})
                planner_name = os.getenv("PLANNER_BACKEND", "stub")
                nova_runs_total.labels(status="failed", planner=planner_name).inc()
                nova_runs_failed_total.inc()
            else:
                # Schedule retry with exponential backoff (capped at 1 hour)
                backoff_seconds = min(60 * (2 ** (attempts - 1)), 3600)
                next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=backoff_seconds)

                self._update_run(
                    status="retry", attempts=attempts, next_attempt_at=next_attempt_at, error_message=str(exc)[:500]
                )
                self.publisher.publish(
                    "run.retry_scheduled",
                    {"run_id": self.run_id, "attempts": attempts, "backoff_seconds": backoff_seconds},
                )
                logger.exception(
                    "run_failed_transient",
                    extra={"run_id": self.run_id, "attempts": attempts, "retry_after_seconds": backoff_seconds},
                )
