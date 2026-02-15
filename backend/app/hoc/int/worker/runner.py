# Layer: L5 — Execution & Workers
# Product: system-wide
# Temporal:
#   Trigger: worker-pool
#   Execution: sync-over-async
# Role: Run execution (sync entrypoint wrapping async internal execution)
# Authority: Run state mutation (pending → running → succeeded/failed/halted)
# Callers: WorkerPool (via ThreadPoolExecutor)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3
# Contract: EXECUTION_SEMANTIC_CONTRACT.md (Guarantee 3: At-Least-Once Worker Dispatch)
# Pattern: Sync-over-async per contract (ThreadPool requires sync callable)

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
from uuid import UUID

from sqlmodel import Session

from app.infra import FeatureIntent, RetryPolicy

# Phase R-3: Budget enforcement decision emission moved to L4
# The emit_budget_enforcement_decision call has been moved to L4
# BudgetEnforcementEngine. L5 runner publishes run.halted events and
# L4 background task processes pending decisions.
# Reference: PIN-257 Phase R-3 (L5→L4 Violation Fix)
from app.db import Agent, Memory, Provenance, Run, engine
from app.events.publisher import get_publisher
from app.models.logs_records import ExecutionStatus, LLMRunRecord, RecordSource
from app.metrics import (
    nova_runs_failed_total,
    nova_runs_total,
    nova_skill_attempts_total,
    nova_skill_duration_seconds,
)
# L4 Domain Facades (PIN-454 FIX-002: L5 must use facades, not direct engine imports)
from app.hoc.cus.incidents.L5_engines.incident_engine import get_incident_engine
from app.hoc.cus.hoc_spine.orchestrator.run_governance_facade import get_run_governance_facade
# PIN-454 FIX-001: Transaction Coordinator for atomic cross-domain writes
from app.hoc.cus.hoc_spine.drivers.transaction_coordinator import (
    get_transaction_coordinator,
    TransactionFailed,
    TRANSACTION_COORDINATOR_ENABLED,
)
from app.skills import get_skill_config
from app.skills.executor import (
    SkillExecutionError,
    SkillExecutor,
)
from app.hoc.cus.logs.L6_drivers.pg_store import PostgresTraceStore
from app.utils.budget_tracker import deduct_budget

# GAP-030: Enforcement guard to ensure enforcement is never skipped
from app.hoc.int.worker.enforcement.enforcement_guard import (
    enforcement_guard,
    EnforcementSkippedError,
)
# GAP-016: Step enforcement integration
from app.hoc.int.worker.enforcement.step_enforcement import (
    enforce_before_step_completion,
    EnforcementResult,
)

# Evidence Architecture v1.1: ExecutionCursor structural authority
from app.core.execution_context import ExecutionCursor, ExecutionPhase, EvidenceSource
from app.hoc.cus.logs.L6_drivers.capture_driver import capture_integrity_evidence

# Phase-2.3: Feature Intent Declaration
# This worker executes runs with state checkpoints and must resume on crash
FEATURE_INTENT = FeatureIntent.RECOVERABLE_OPERATION
RETRY_POLICY = RetryPolicy.SAFE

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
        self.trace_store = PostgresTraceStore()

    def _get_run(self) -> Optional[Run]:
        """Fetch run from database."""
        with Session(engine) as session:
            return session.get(Run, self.run_id)

    def _check_authorization(self, run: Run) -> bool:
        """
        Phase E FIX-02: Check pre-computed authorization from L6.

        Authorization is computed at submission time (L2 → L4) and persisted in L6.
        The runner only reads the decision from L6 - never calls L4 directly.

        This eliminates the L5 → L4 import violation (VIOLATION-002, VIOLATION-003).

        Args:
            run: The run record from L6

        Returns:
            True if authorized, False if denied or pending
        """
        # Check authorization_decision field from L6
        authorization_decision = getattr(run, "authorization_decision", None)

        # Backward compatibility: if field is None or missing, default to GRANTED
        # (for runs created before FIX-02 migration)
        if authorization_decision is None:
            logger.debug(
                "authorization_decision_missing",
                extra={"run_id": self.run_id, "defaulting_to": "GRANTED"},
            )
            return True

        if authorization_decision == "GRANTED":
            return True

        if authorization_decision == "DENIED":
            # Log and fail the run
            authorization_context = getattr(run, "authorization_context", None)
            reason = "unknown"
            if authorization_context:
                try:
                    import json as _json

                    ctx = _json.loads(authorization_context)
                    reason = ctx.get("decision_reason", "unknown")
                except (ValueError, TypeError):
                    pass

            logger.warning(
                "run_authorization_denied",
                extra={
                    "run_id": self.run_id,
                    "authorization_decision": authorization_decision,
                    "reason": reason,
                },
            )

            # Update run status to reflect authorization failure
            error_msg = f"Authorization denied: {reason}"
            self._update_run(
                status="failed",
                attempts=run.attempts or 0,
                completed_at=datetime.now(timezone.utc),
                error_message=error_msg,
            )

            # SDSR: Create incident for failed run (PIN-370)
            self._create_incident_for_failure(error_message=error_msg)

            self.publisher.publish(
                "run.failed",
                {
                    "run_id": self.run_id,
                    "status": "failed",
                    "reason": "authorization_denied",
                    "authorization_decision": authorization_decision,
                },
            )

            return False

        if authorization_decision == "PENDING_APPROVAL":
            logger.info(
                "run_pending_approval",
                extra={
                    "run_id": self.run_id,
                    "authorization_decision": authorization_decision,
                },
            )

            # Don't fail, just don't execute yet - worker will retry later
            # Set status to waiting for approval
            self._update_run(
                status="pending_approval",
                attempts=run.attempts or 0,
                error_message="Waiting for authorization approval",
            )

            return False

        # Unknown authorization decision - log warning and deny
        logger.warning(
            "run_authorization_unknown",
            extra={
                "run_id": self.run_id,
                "authorization_decision": authorization_decision,
            },
        )
        return False

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

    def _create_incident_for_failure(self, error_message: Optional[str] = None):
        """
        Create an incident when a run fails.

        SDSR Cross-Domain Propagation (PIN-370):
        Activity (failed run) → Incident Engine → sdsr_incidents table
        """
        try:
            run = self._get_run()
            if not run:
                logger.warning("create_incident_skip_no_run", extra={"run_id": self.run_id})
                return

            incident_engine = get_incident_engine()
            incident_id = incident_engine.check_and_create_incident(
                run_id=self.run_id,
                status="failed",
                error_message=error_message or run.error_message,
                tenant_id=run.tenant_id,
                agent_id=run.agent_id,
                is_synthetic=run.is_synthetic or False,
                synthetic_scenario_id=run.synthetic_scenario_id,
            )

            if incident_id:
                logger.info(
                    "incident_created_for_failed_run",
                    extra={"run_id": self.run_id, "incident_id": incident_id},
                )
                self.publisher.publish(
                    "incident.created",
                    {"run_id": self.run_id, "incident_id": incident_id},
                )
        except Exception as e:
            # Don't fail the run because of incident creation failure
            logger.error(
                "incident_creation_failed",
                extra={"run_id": self.run_id, "error": str(e)},
            )

    def _create_governance_records_for_run(self, run_status: str):
        """
        Create incident and policy records for ANY run (PIN-407).

        PIN-407: Success as First-Class Data
        - Every run produces an incident record with explicit outcome
        - Every run produces a policy evaluation record with explicit outcome
        - This is NOT limited to failures - successful runs also get records

        PIN-454 FIX-001: Uses Transaction Coordinator for atomic writes
        - When TRANSACTION_COORDINATOR_ENABLED=true, uses atomic transactions
        - Events are published ONLY after successful commit
        - Partial failures trigger rollback

        This method is called from both success and failure paths.
        """
        try:
            run = self._get_run()
            if not run:
                logger.warning("governance_records_skip_no_run", extra={"run_id": self.run_id})
                return

            # PIN-454 FIX-001: Use Transaction Coordinator for atomic cross-domain writes
            if TRANSACTION_COORDINATOR_ENABLED:
                self._create_governance_records_atomic(run, run_status)
            else:
                self._create_governance_records_legacy(run, run_status)

        except Exception as e:
            # Don't fail the run because of governance record creation failure
            logger.error(
                "governance_records_creation_failed",
                extra={"run_id": self.run_id, "status": run_status, "error": str(e)},
            )

    def _create_governance_records_atomic(self, run: Run, run_status: str):
        """
        Create governance records atomically using Transaction Coordinator.

        PIN-454 FIX-001: Atomic cross-domain writes
        - All domain operations in single transaction
        - Events published ONLY after commit
        - Rollback on any failure
        """
        try:
            coordinator = get_transaction_coordinator()
            result = coordinator.execute(
                run_id=self.run_id,
                tenant_id=run.tenant_id or "",
                run_status=run_status,
                agent_id=run.agent_id,
                is_synthetic=run.is_synthetic or False,
                synthetic_scenario_id=run.synthetic_scenario_id,
                skip_events=False,  # Let coordinator handle events
            )

            logger.info(
                "governance_records_created_atomic",
                extra={
                    "run_id": self.run_id,
                    "outcome": run_status,
                    "incident_id": result.incident_result.result_id if result.incident_result else None,
                    "policy_id": result.policy_result.result_id if result.policy_result else None,
                    "duration_ms": result.duration_ms,
                    "events_published": result.events_published,
                },
            )

        except TransactionFailed as e:
            logger.error(
                "governance_records_transaction_failed",
                extra={
                    "run_id": self.run_id,
                    "status": run_status,
                    "phase": e.phase.value,
                    "error": str(e),
                },
            )
            # Fall back to legacy method on transaction failure
            logger.info("governance_records_fallback_to_legacy", extra={"run_id": self.run_id})
            self._create_governance_records_legacy(run, run_status)

    def _create_governance_records_legacy(self, run: Run, run_status: str):
        """
        Create governance records using legacy non-atomic approach.

        This is the original implementation kept as fallback.
        """
        # PIN-407: Create incident record (SUCCESS, FAILURE, BLOCKED, etc.)
        incident_engine = get_incident_engine()
        incident_id = incident_engine.create_incident_for_run(
            run_id=self.run_id,
            tenant_id=run.tenant_id,
            run_status=run_status,
            error_code=None,
            error_message=None,
            agent_id=run.agent_id,
            is_synthetic=run.is_synthetic or False,
            synthetic_scenario_id=run.synthetic_scenario_id,
        )

        if incident_id:
            logger.info(
                "governance_incident_created",
                extra={"run_id": self.run_id, "incident_id": incident_id, "outcome": run_status},
            )
            self.publisher.publish(
                "incident.created",
                {"run_id": self.run_id, "incident_id": incident_id, "outcome": run_status},
            )

        # PIN-407: Create policy evaluation record
        # PIN-454 FIX-002: Use governance facade instead of direct service import
        governance_facade = get_run_governance_facade()
        policy_id = governance_facade.create_policy_evaluation(
            run_id=self.run_id,
            tenant_id=run.tenant_id or "",
            run_status=run_status,
            policies_checked=0,  # Can be enhanced later
            is_synthetic=run.is_synthetic or False,
            synthetic_scenario_id=run.synthetic_scenario_id,
        )

        if policy_id:
            logger.info(
                "governance_policy_created",
                extra={"run_id": self.run_id, "policy_id": policy_id, "outcome": run_status},
            )
            self.publisher.publish(
                "policy.evaluated",
                {"run_id": self.run_id, "policy_id": policy_id, "outcome": run_status},
            )

    def _evaluate_and_emit_threshold_signals(
        self,
        run: Run,
        run_status: str,
        duration_ms: float,
        tool_calls: list,
    ):
        """
        Evaluate run against thresholds and emit dual signals.

        Signal Flow:
        1. Evaluate run against tenant's threshold params
        2. If signals generated:
           - emit to ops_events (Founder Console)
           - update runs.risk_level (Customer Console)

        Reference: Threshold Signal Wiring to Customer Console Plan
        """
        try:
            # Calculate token totals from tool_calls
            total_tokens = 0
            total_cost_usd = 0.0

            for tool_call in tool_calls:
                skill_name = tool_call.get("skill", "")
                if skill_name == "llm_invoke":
                    response = tool_call.get("response", {})
                    total_tokens += response.get("input_tokens", 0)
                    total_tokens += response.get("output_tokens", 0)
                    total_cost_usd += float(response.get("cost_cents", 0)) / 100.0

            # Also check run-level token counts
            if hasattr(run, "input_tokens") and run.input_tokens:
                total_tokens = max(total_tokens, (run.input_tokens or 0) + (run.output_tokens or 0))
            if hasattr(run, "estimated_cost_usd") and run.estimated_cost_usd:
                total_cost_usd = max(total_cost_usd, float(run.estimated_cost_usd or 0))

            # Import sync threshold service (worker runs in ThreadPoolExecutor, not async)
            # L4 engine: business logic (resolver, evaluator)
            from app.hoc.cus.controls.L5_engines.threshold_engine import (
                LLMRunThresholdResolverSync,
                LLMRunEvaluatorSync,
            )
            # L6 driver: DB operations (driver, signal emission)
            from app.hoc.cus.controls.L6_drivers.threshold_driver import (
                ThresholdDriverSync,
            )
            from app.hoc.cus.hoc_spine.orchestrator.coordinators.signal_coordinator import (
                emit_and_persist_threshold_signal,
            )

            # Get a sync session for threshold operations
            with Session(engine) as session:
                driver = ThresholdDriverSync(session)
                resolver = LLMRunThresholdResolverSync(driver)
                evaluator = LLMRunEvaluatorSync(resolver)

                # Evaluate the completed run (sync version)
                evaluation = evaluator.evaluate_completed_run(
                    run_id=self.run_id,
                    tenant_id=run.tenant_id or "",
                    status=run_status,
                    execution_time_ms=int(duration_ms),
                    tokens_used=total_tokens,
                    cost_usd=total_cost_usd,
                )

                # If there are signals, emit to both Founder and Customer consoles
                if evaluation.signals:
                    emit_and_persist_threshold_signal(
                        session=session,
                        tenant_id=run.tenant_id or "",
                        run_id=self.run_id,
                        state="completed",
                        signals=evaluation.signals,
                        params_used=evaluation.params_used,
                    )

                    logger.info(
                        "threshold_signals_emitted",
                        extra={
                            "run_id": self.run_id,
                            "signals": [s.value for s in evaluation.signals],
                            "duration_ms": duration_ms,
                            "tokens_used": total_tokens,
                            "cost_usd": total_cost_usd,
                        },
                    )

        except Exception as e:
            # Don't fail the run because of threshold evaluation failure
            logger.warning(
                "threshold_evaluation_failed",
                extra={"run_id": self.run_id, "error": str(e)},
            )

    def _emit_lessons_on_success(
        self,
        run: Run,
        budget_context: BudgetContext,
        run_consumed_cents: int,
        duration_ms: int,
    ):
        """
        Emit lessons for near-threshold and critical success conditions (PIN-411).

        This method is WORKER-SAFE:
        - Never raises exceptions (wraps all calls)
        - Never blocks run completion
        - Logs failures without interrupting the run

        Near-threshold detection:
        - Triggered when budget utilization >= 85% and < 100%
        - Uses threshold bands (85-90%, 90-95%, 95-100%) for debounce granularity

        Critical success detection:
        - Triggered when run shows exceptional cost efficiency or performance
        - Criteria: < 30% utilization AND fast execution (< 50% of expected)
        """
        if not run:
            return

        try:
            # Calculate budget utilization
            limit_cents = budget_context.limit_cents
            if limit_cents <= 0:
                # No budget configured, skip lessons
                return

            # Total consumed = pre-run consumed + this run's consumption
            total_consumed = budget_context.consumed_cents + run_consumed_cents
            utilization = (total_consumed / limit_cents) * 100

            # Near-threshold detection: 85% <= utilization < 100%
            # PIN-454 FIX-002: Use governance facade instead of direct engine import
            if 85.0 <= utilization < 100.0:
                governance_facade = get_run_governance_facade()
                lesson_id = governance_facade.emit_near_threshold_lesson(
                    tenant_id=run.tenant_id or "",
                    metric="budget",
                    utilization=utilization,
                    threshold_value=limit_cents,
                    current_value=total_consumed,
                    source_event_id=UUID(self.run_id),
                    window="24h",
                    is_synthetic=run.is_synthetic or False,
                    synthetic_scenario_id=run.synthetic_scenario_id,
                )
                if lesson_id:
                    logger.info(
                        "lessons_near_threshold_emitted",
                        extra={
                            "run_id": self.run_id,
                            "lesson_id": str(lesson_id),
                            "utilization": utilization,
                        },
                    )

            # Critical success detection
            # Criteria: Very efficient run (< 30% utilization, fast execution)
            # This helps identify patterns worth documenting as best practices
            if utilization < 30.0 and duration_ms < 5000:  # < 5s execution
                # Calculate efficiency metrics for the lesson
                efficiency_metrics = {
                    "utilization_percent": utilization,
                    "duration_ms": duration_ms,
                    "run_consumed_cents": run_consumed_cents,
                    "budget_remaining_percent": 100.0 - utilization,
                    "efficiency_score": (100.0 - utilization) * (1000.0 / max(duration_ms, 1)),
                }

                # PIN-454 FIX-002: Use governance facade instead of direct engine import
                governance_facade = get_run_governance_facade()
                lesson_id = governance_facade.emit_critical_success_lesson(
                    tenant_id=run.tenant_id or "",
                    success_type="cost_efficiency",
                    metrics=efficiency_metrics,
                    source_event_id=UUID(self.run_id),
                    is_synthetic=run.is_synthetic or False,
                    synthetic_scenario_id=run.synthetic_scenario_id,
                )
                if lesson_id:
                    logger.info(
                        "lessons_critical_success_emitted",
                        extra={
                            "run_id": self.run_id,
                            "lesson_id": str(lesson_id),
                            "success_type": "cost_efficiency",
                            "efficiency_metrics": efficiency_metrics,
                        },
                    )

        except Exception as e:
            # Worker-safe: log and continue, never block run completion
            logger.warning(
                "lessons_emission_failed",
                extra={"run_id": self.run_id, "error": str(e)},
            )

    def _create_llm_run_record(
        self,
        run: Run,
        tool_calls: list,
        execution_status: ExecutionStatus,
        started_at: datetime,
        completed_at: datetime,
        trace_id: Optional[str] = None,
    ):
        """
        Create an immutable LLM run record for the Logs domain (PIN-413).

        This is a TRUST ANCHOR for execution verification:
        - Captures total tokens and cost from all LLM invocations in this run
        - Records are WRITE-ONCE (no UPDATE, no DELETE - enforced by DB trigger)
        - Source = WORKER (this is the authoritative capture point)

        Called at each terminal state transition:
        - SUCCESS: execution_status = SUCCEEDED
        - FAILED: execution_status = FAILED
        - HALTED: execution_status = ABORTED (budget halt)
        """
        try:
            # Aggregate token counts and extract provider/model from LLM invocations
            total_input_tokens = 0
            total_output_tokens = 0
            total_cost_cents = 0
            provider = "unknown"
            model = "unknown"

            for tool_call in tool_calls:
                skill_name = tool_call.get("skill", "")
                if skill_name == "llm_invoke":
                    response = tool_call.get("response", {})
                    total_input_tokens += response.get("input_tokens", 0)
                    total_output_tokens += response.get("output_tokens", 0)
                    total_cost_cents += int(response.get("cost_cents", 0) * 100)  # Store as int cents

                    # Extract provider/model from first successful LLM call
                    if provider == "unknown" and response.get("model"):
                        model = response.get("model", "unknown")
                        # Derive provider from model name pattern
                        if "claude" in model.lower():
                            provider = "anthropic"
                        elif "gpt" in model.lower():
                            provider = "openai"
                        elif model == "stub":
                            provider = "stub"
                        else:
                            provider = "unknown"

            # Create the immutable record
            record = LLMRunRecord(
                tenant_id=run.tenant_id or "",
                run_id=self.run_id,
                trace_id=trace_id,
                provider=provider,
                model=model,
                prompt_hash=None,  # Would need to compute from actual prompts
                response_hash=None,  # Would need to compute from actual responses
                input_tokens=total_input_tokens,
                output_tokens=total_output_tokens,
                cost_cents=total_cost_cents,
                execution_status=execution_status.value,
                started_at=started_at,
                completed_at=completed_at,
                source=RecordSource.WORKER.value,
                is_synthetic=run.is_synthetic or False,
                synthetic_scenario_id=run.synthetic_scenario_id,
            )

            with Session(engine) as session:
                session.add(record)
                session.commit()

            logger.info(
                "llm_run_record_created",
                extra={
                    "run_id": self.run_id,
                    "record_id": record.id,
                    "execution_status": execution_status.value,
                    "input_tokens": total_input_tokens,
                    "output_tokens": total_output_tokens,
                    "cost_cents": total_cost_cents,
                },
            )

        except Exception as e:
            # Don't fail the run because of record creation failure
            # This is observability, not execution-critical
            logger.error(
                "llm_run_record_creation_failed",
                extra={"run_id": self.run_id, "error": str(e)},
            )

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

        # Phase E FIX-02: Check pre-computed authorization from L6
        # Authorization decision is computed at submission time (L2 → L4)
        # Runner only reads the decision - no L4 import needed
        if not self._check_authorization(run):
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
            # Evidence Architecture v1.1: Initialize cursor early for exception handler access
            cursor = None

            # Parse plan
            plan = json.loads(run.plan_json) if run.plan_json else {"steps": []}
            steps = plan.get("steps", [])

            # GAP-LOG-001 FIX: Start trace for this run (PIN-378 SDSR extension)
            # This creates aos_traces row with SDSR inheritance from run
            # PIN-404: Capture trace context for step recording
            trace_id: str | None = None
            is_synthetic = getattr(run, "is_synthetic", False) or False
            synthetic_scenario_id = getattr(run, "synthetic_scenario_id", None)

            try:
                trace_id = await self.trace_store.start_trace(
                    run_id=self.run_id,
                    correlation_id=getattr(run, "correlation_id", None) or self.run_id,
                    tenant_id=run.tenant_id,
                    agent_id=run.agent_id,
                    plan=steps,
                    is_synthetic=is_synthetic,
                    synthetic_scenario_id=synthetic_scenario_id,
                )
                logger.debug("trace_started", extra={"run_id": self.run_id, "trace_id": trace_id})
            except Exception as e:
                # Don't fail the run if trace creation fails
                logger.warning(
                    "trace_start_failed", extra={"run_id": self.run_id, "error": str(e), "error_type": type(e).__name__}
                )
                logger.warning(f"TRACE_ERROR_DETAIL: {type(e).__name__}: {e}")

            # Evidence Architecture v1.1: Create ExecutionCursor for structural step authority
            # ExecutionCursor owns step advancement; evidence writers receive read-only context
            if trace_id:
                try:
                    cursor = ExecutionCursor.create(
                        run_id=self.run_id,
                        trace_id=trace_id,
                        source=EvidenceSource.WORKER,
                        is_synthetic=is_synthetic,
                        synthetic_scenario_id=synthetic_scenario_id,
                    )
                    cursor.with_phase(ExecutionPhase.RUNNING)
                    logger.debug("execution_cursor_created", extra={"run_id": self.run_id, "trace_id": trace_id})
                except Exception as e:
                    logger.warning("execution_cursor_creation_failed", extra={"run_id": self.run_id, "error": str(e)})

            if not steps:
                # Phase R-2: L5 runner must NOT generate plans (L4 responsibility)
                # Plans should be generated by L4 PlanGenerationEngine at run creation time.
                # If we reach here with no plan, it's a governance violation.
                # Reference: PIN-257 Phase R-2 (L5→L4 Violation Fix)
                #
                # GOVERNANCE VIOLATION: Run was queued without a plan.
                # This violates the layer model where L4 owns decisions and L5 owns execution.
                # The run creation flow should call L4 PlanGenerationEngine before queueing.
                logger.error(
                    "L5_GOVERNANCE_VIOLATION_NO_PLAN",
                    extra={
                        "run_id": self.run_id,
                        "agent_id": run.agent_id,
                        "goal": run.goal[:100] if run.goal else None,
                        "violation": "Run queued without plan - L4 should generate plans before L5 execution",
                        "reference": "PIN-257 Phase R-2",
                    },
                )
                raise RuntimeError(
                    f"Governance violation: Run {self.run_id} has no plan. "
                    "Plans must be generated by L4 PlanGenerationEngine at creation time, "
                    "not by L5 runner at execution time. See PIN-257 Phase R-2."
                )

                # NOTE: The following code is intentionally unreachable.
                # It documents what was removed for the Phase R-2 fix.
                # Previously, L5 imported L4 modules to generate plans inline:
                #   from ..memory import get_retriever
                #   from ..planners import get_planner
                #   from ..skills import get_skill_manifest
                # This violated layer boundaries (L5→L4 imports not allowed).
                # Now plan generation happens in L4 before the run is queued.

            # NOTE: Plan validation warnings and planner cost tracking now happen
            # in L4 PlanGenerationEngine at run creation time, not here in L5.
            # The plan.metadata may contain cost info that was tracked in L4.
            # Reference: PIN-257 Phase R-2

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
                        # Evidence Architecture v1.1: Advance step via cursor (structural authority)
                        # Only the cursor can advance steps - evidence writers get read-only context
                        if cursor:
                            cursor.advance()

                        result, step_status = await executor.execute(
                            skill_name=skill_name,
                            params=interpolated_params,
                            step_id=step_id,
                            skill_config=skill_config,
                            execution_context=cursor.context if cursor else None,
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
                        # GAP-LOG-001: Record failed step BEFORE aborting
                        # This ensures trace steps are recorded even for abort failures
                        step_duration = time.time() - step_start
                        try:
                            step_index = steps.index(step)
                            if trace_id:  # PIN-404: Only record if trace was created
                                await self.trace_store.record_step(
                                    trace_id=trace_id,  # PIN-404: Pass actual trace_id
                                    run_id=self.run_id,
                                    step_index=step_index,
                                    skill_name=skill_name,
                                    params=interpolated_params,
                                    status="failure",
                                    outcome_category="execution",
                                    outcome_code="abort",
                                    outcome_data={"error": str(step_error)[:500]},
                                    cost_cents=0,
                                    duration_ms=step_duration * 1000,
                                    retry_count=step_attempts - 1,
                                    source="engine",
                                    is_synthetic=is_synthetic,  # PIN-404: Propagate SDSR context
                                    synthetic_scenario_id=synthetic_scenario_id,
                                )
                            logger.debug("trace_step_recorded_abort", extra={"run_id": self.run_id, "step_id": step_id})
                        except Exception as e:
                            logger.warning(
                                "trace_step_record_failed",
                                extra={"run_id": self.run_id, "step_id": step_id, "error": str(e)},
                            )
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
                        "result": result.get("result", {}) if result else {},
                        "status": tool_call["status"],
                    },
                )

                # GAP-LOG-001 FIX: Record step in trace (PIN-378, PIN-404 SDSR extension)
                # This creates aos_trace_steps row with level derived from status
                # PIN-404: Pass trace_id and SDSR context for proper linkage
                try:
                    step_index = steps.index(step)
                    if trace_id:  # PIN-404: Only record if trace was created
                        await self.trace_store.record_step(
                            trace_id=trace_id,  # PIN-404: Pass actual trace_id
                            run_id=self.run_id,
                            step_index=step_index,
                            skill_name=skill_name,
                            params=interpolated_params,
                            status=tool_call["status"],
                            outcome_category="execution",
                            outcome_code=tool_call["status"],
                            outcome_data=result.get("result", {}) if result else None,
                            cost_cents=result.get("side_effects", {}).get("cost_cents", 0) if result else 0,
                            duration_ms=step_duration * 1000,
                            retry_count=step_attempts - 1,  # -1 because attempts starts at 1
                            source="engine",
                            is_synthetic=is_synthetic,  # PIN-404: Propagate SDSR context
                            synthetic_scenario_id=synthetic_scenario_id,
                        )
                except Exception as e:
                    # Don't fail the run if step recording fails
                    logger.warning(
                        "trace_step_record_failed", extra={"run_id": self.run_id, "step_id": step_id, "error": str(e)}
                    )

                # =============================================================
                # GAP-016: Step Enforcement Integration (CHOKE POINT)
                # Evaluate policies AFTER each step completion, BEFORE next step
                # Uses enforcement guard to ensure enforcement is never skipped
                # =============================================================
                try:
                    step_index_for_enforcement = steps.index(step)
                    step_cost = result.get("side_effects", {}).get("cost_cents", 0) if result else 0
                    step_tokens = result.get("side_effects", {}).get("tokens", 0) if result else 0

                    with enforcement_guard(
                        run_context={"run_id": self.run_id, "tenant_id": run.tenant_id},
                        step_number=step_index_for_enforcement,
                    ) as guard:
                        # Build run context for enforcement
                        run_ctx = type("RunContext", (), {
                            "run_id": self.run_id,
                            "tenant_id": run.tenant_id or "",
                            "step_index": step_index_for_enforcement,
                            "cost_cents": run_consumed_cents,
                        })()

                        enforcement_result = enforce_before_step_completion(
                            run_context=run_ctx,
                            step_result=result,
                            prevention_engine=None,  # Will use default
                        )
                        guard.mark_enforcement_checked(enforcement_result)

                        # Handle enforcement result
                        if enforcement_result.should_halt:
                            # Policy violation - halt the run immediately
                            logger.warning(
                                "step_enforcement_blocked",
                                extra={
                                    "run_id": self.run_id,
                                    "step_id": step_id,
                                    "policy_id": enforcement_result.policy_id,
                                    "halt_reason": enforcement_result.halt_reason,
                                    "message": enforcement_result.message,
                                },
                            )
                            # Set halted status and exit
                            duration_ms = (time.time() - start_time) * 1000
                            completed_at = datetime.now(timezone.utc)
                            self._update_run(
                                status="halted",
                                attempts=run.attempts,
                                completed_at=completed_at,
                                error_message=f"Policy violation: {enforcement_result.message}",
                            )
                            self.publisher.publish(
                                "run.halted",
                                {
                                    "run_id": self.run_id,
                                    "status": "halted",
                                    "halt_reason": str(enforcement_result.halt_reason),
                                    "policy_id": enforcement_result.policy_id,
                                    "message": enforcement_result.message,
                                },
                            )
                            return  # Exit run execution
                        # EnforcementResult has binary state: halt or continue
                        # If not halting, execution proceeds normally

                except EnforcementSkippedError as e:
                    # GAP-030: Enforcement was skipped - critical governance failure
                    logger.critical(
                        "enforcement_skipped_violation",
                        extra={
                            "run_id": self.run_id,
                            "step_id": step_id,
                            "error": str(e),
                        },
                    )
                    # Fail-closed: halt the run
                    duration_ms = (time.time() - start_time) * 1000
                    self._update_run(
                        status="halted",
                        attempts=run.attempts,
                        completed_at=datetime.now(timezone.utc),
                        error_message=f"Enforcement skipped: {str(e)}",
                    )
                    return
                except Exception as e:
                    # Don't fail the run if enforcement fails - log and continue
                    # (fail-open for enforcement errors to avoid blocking legitimate runs)
                    logger.error(
                        "step_enforcement_error",
                        extra={"run_id": self.run_id, "step_id": step_id, "error": str(e)},
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

                    # 4. Decision record emission (L4 responsibility)
                    # Phase R-3: Decision emission moved to L4 BudgetEnforcementEngine
                    # L5 runner must NOT emit decision records (L5→L4 violation).
                    # The run.halted event (step 7) contains all budget info needed.
                    # L4 background task processes pending decisions.
                    # Reference: PIN-257 Phase R-3 (L5→L4 Violation Fix)
                    logger.debug(
                        "budget_halt_decision_deferred_to_L4",
                        extra={
                            "run_id": self.run_id,
                            "budget_limit_cents": budget_context.limit_cents,
                            "budget_consumed_cents": total_consumed,
                            "completed_steps": completed_steps,
                            "total_steps": total_steps,
                        },
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

                    # PIN-413: Create immutable LLM run record for Logs domain (halted = ABORTED)
                    self._create_llm_run_record(
                        run=run,
                        tool_calls=tool_calls,
                        execution_status=ExecutionStatus.ABORTED,
                        started_at=run.started_at or datetime.now(timezone.utc),
                        completed_at=completed_at,
                        trace_id=trace_id,
                    )

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

            # PIN-407: Create governance records (incident + policy) for SUCCESS runs
            # CRITICAL: Must happen BEFORE _update_run(status="succeeded") because
            # SDSR checker polls runs table and immediately queries incidents when
            # it sees "succeeded" status. Records must exist BEFORE status change.
            self._create_governance_records_for_run(run_status="succeeded")

            # Threshold Signal Wiring: Evaluate run against thresholds and emit signals
            # This updates runs.risk_level for Customer Console Activity panels
            # and emits to ops_events for Founder Console monitoring
            self._evaluate_and_emit_threshold_signals(
                run=run,
                run_status="succeeded",
                duration_ms=duration_ms,
                tool_calls=tool_calls,
            )

            # IMPORTANT: Run must not be marked terminal until incident + policy
            # records are created. Moving this call above governance creation
            # will break SDSR integrity checks. See PIN-407.
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

            # PIN-413: Create immutable LLM run record for Logs domain
            self._create_llm_run_record(
                run=run,
                tool_calls=tool_calls,
                execution_status=ExecutionStatus.SUCCEEDED,
                started_at=run.started_at or datetime.now(timezone.utc),
                completed_at=completed_at,
                trace_id=trace_id,
            )

            # GAP-LOG-001 FIX: Complete trace on success (PIN-378 SDSR extension)
            # PIN-406: Fail-closed trace semantics - COMPLETE or ABORTED, no dangling
            try:
                await self.trace_store.complete_trace(
                    run_id=self.run_id,
                    status="completed",
                    metadata={"duration_ms": duration_ms},
                )
                logger.debug("trace_completed", extra={"run_id": self.run_id, "status": "completed"})
            except Exception as e:
                # PIN-406: Fail-closed - mark trace ABORTED, not just logged
                logger.error("trace_complete_failed", extra={"run_id": self.run_id, "error": str(e)})
                try:
                    await self.trace_store.mark_trace_aborted(
                        run_id=self.run_id,
                        reason=f"finalization_failed: {str(e)[:200]}",
                    )
                    logger.warning("trace_aborted", extra={"run_id": self.run_id, "reason": "finalization_failed"})
                except Exception as abort_err:
                    logger.critical(
                        "trace_abort_failed",
                        extra={"run_id": self.run_id, "error": str(abort_err)},
                    )

            self.publisher.publish(
                "run.completed", {"run_id": self.run_id, "status": "succeeded", "duration_ms": duration_ms}
            )

            logger.info(
                "run_completed", extra={"run_id": self.run_id, "status": "succeeded", "duration_ms": duration_ms}
            )
            planner_name = os.getenv("PLANNER_BACKEND", "stub")
            nova_runs_total.labels(status="succeeded", planner=planner_name).inc()

            # Evidence Architecture v1.1: Mark cursor terminal and capture integrity evidence (J)
            if cursor:
                cursor.with_phase(ExecutionPhase.TERMINAL)
            try:
                capture_integrity_evidence(
                    run_id=self.run_id,
                    is_synthetic=run.is_synthetic if run else False,
                    synthetic_scenario_id=run.synthetic_scenario_id if run else None,
                )
                logger.debug("integrity_evidence_captured", extra={"run_id": self.run_id, "status": "succeeded"})
            except Exception as e:
                logger.warning("integrity_evidence_capture_failed", extra={"run_id": self.run_id, "error": str(e)})

            # =============================================================
            # PIN-411: Lessons Learned Engine - Near-Threshold & Critical Success
            # Worker-safe: never raises, never blocks run completion
            # =============================================================
            self._emit_lessons_on_success(
                run=run,
                budget_context=budget_context,
                run_consumed_cents=run_consumed_cents,
                duration_ms=duration_ms,
            )

        except Exception as exc:
            # Failure: increment attempts and set next_attempt_at with exponential backoff
            run = self._get_run()
            attempts = (run.attempts or 0) + 1

            if attempts >= MAX_ATTEMPTS:
                error_msg = str(exc)[:500]
                self._update_run(
                    status="failed",
                    attempts=attempts,
                    error_message=error_msg,
                    completed_at=datetime.now(timezone.utc),
                )

                # SDSR: Create incident for failed run (PIN-370)
                self._create_incident_for_failure(error_message=error_msg)

                # PIN-413: Create immutable LLM run record for Logs domain (failed)
                # Parse tool_calls from run if available (may be partial)
                if run:
                    failed_tool_calls = []
                    if run.tool_calls_json:
                        try:
                            failed_tool_calls = json.loads(run.tool_calls_json)
                        except (json.JSONDecodeError, TypeError):
                            pass

                    # Threshold Signal Wiring: Evaluate failed run against thresholds
                    # Compute duration_ms from run timestamps
                    failed_duration_ms = 0.0
                    if run.started_at:
                        failed_duration_ms = (datetime.now(timezone.utc) - run.started_at).total_seconds() * 1000

                    self._evaluate_and_emit_threshold_signals(
                        run=run,
                        run_status="failed",
                        duration_ms=failed_duration_ms,
                        tool_calls=failed_tool_calls,
                    )

                    self._create_llm_run_record(
                        run=run,
                        tool_calls=failed_tool_calls,
                        execution_status=ExecutionStatus.FAILED,
                        started_at=run.started_at or datetime.now(timezone.utc),
                        completed_at=datetime.now(timezone.utc),
                        trace_id=None,  # trace_id may not be available in exception handler
                    )

                # GAP-LOG-001 FIX: Complete trace on failure (PIN-378 SDSR extension)
                # PIN-406: Fail-closed trace semantics - COMPLETE or ABORTED, no dangling
                try:
                    # We're inside async _execute(), so just await
                    await self.trace_store.complete_trace(
                        run_id=self.run_id,
                        status="failed",
                        metadata={"error": error_msg[:200]},
                    )
                    logger.debug("trace_completed", extra={"run_id": self.run_id, "status": "failed"})
                except Exception as e:
                    # PIN-406: Fail-closed - mark trace ABORTED, not just logged
                    logger.error("trace_complete_failed", extra={"run_id": self.run_id, "error": str(e)})
                    try:
                        await self.trace_store.mark_trace_aborted(
                            run_id=self.run_id,
                            reason=f"finalization_failed: {str(e)[:200]}",
                        )
                        logger.warning("trace_aborted", extra={"run_id": self.run_id, "reason": "finalization_failed"})
                    except Exception as abort_err:
                        logger.critical(
                            "trace_abort_failed",
                            extra={"run_id": self.run_id, "error": str(abort_err)},
                        )

                self.publisher.publish(
                    "run.failed", {"run_id": self.run_id, "attempts": attempts, "error": str(exc)[:200]}
                )
                logger.exception("run_failed_permanent", extra={"run_id": self.run_id, "attempts": attempts})
                planner_name = os.getenv("PLANNER_BACKEND", "stub")
                nova_runs_total.labels(status="failed", planner=planner_name).inc()
                nova_runs_failed_total.inc()

                # Evidence Architecture v1.1: Mark cursor terminal and capture integrity evidence (J)
                if cursor:
                    cursor.with_phase(ExecutionPhase.TERMINAL)
                try:
                    capture_integrity_evidence(
                        run_id=self.run_id,
                        is_synthetic=run.is_synthetic if run else False,
                        synthetic_scenario_id=run.synthetic_scenario_id if run else None,
                    )
                    logger.debug("integrity_evidence_captured", extra={"run_id": self.run_id, "status": "failed"})
                except Exception as e:
                    logger.warning("integrity_evidence_capture_failed", extra={"run_id": self.run_id, "error": str(e)})
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
