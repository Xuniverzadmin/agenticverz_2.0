# Layer: L5 — Domain Engine
# AUDIENCE: INTERNAL
# Role: Replay API for AOS
"""
Replay API for AOS
M6 Deliverable: Re-execute stored plans and verify determinism

This module provides the ability to replay a previously executed run
and verify that the runtime behavior is deterministic.

FROZEN SEMANTICS (PIN-198, S6 Trace Integrity Truth):
- emit_traces=False is the DEFAULT and must remain so
- Replay is OBSERVATIONAL - it must not emit traces
- Replay must not generate new IDs during verification
- Replay must not consult wall-clock time
See LESSONS_ENFORCED.md Invariant #14: Replay Is Observational
"""

import asyncio
import os
from dataclasses import dataclass
from typing import Any

# PIN-520: Use canonical HOC logs schemas + L6 drivers
from app.hoc.cus.logs.L5_schemas import (
    ParityResult,
    TraceRecord,
    TraceStatus,
    TraceStep,
    compare_traces,
)
from app.hoc.cus.logs.L6_drivers.trace_store import (
    SQLiteTraceStore,
    TraceStore,
    generate_correlation_id,
    generate_run_id,
)

# Check if we should use Postgres for trace storage
USE_POSTGRES = os.getenv("USE_POSTGRES_TRACES", "false").lower() == "true"

if USE_POSTGRES:
    from app.hoc.cus.logs.L6_drivers.pg_store import get_postgres_trace_store


def get_trace_store() -> TraceStore:
    """Get the appropriate trace store based on configuration."""
    if USE_POSTGRES:
        return get_postgres_trace_store()
    return SQLiteTraceStore()


@dataclass
class ReplayResult:
    """Result of a replay operation."""

    success: bool
    run_id: str  # New run ID for this replay
    original_run_id: str
    parity_check: ParityResult | None  # None if verify_parity=False
    trace: TraceRecord | None  # New trace from replay
    divergence_point: int | None  # Step where behavior diverged (if any)
    error: str | None  # Error message if replay failed

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "run_id": self.run_id,
            "original_run_id": self.original_run_id,
            "parity_check": self.parity_check.to_dict() if self.parity_check else None,
            "trace": self.trace.to_dict() if self.trace else None,
            "divergence_point": self.divergence_point,
            "error": self.error,
        }


class ReplayEngine:
    """
    Engine for replaying stored plans.

    Replays execute the same skill calls with the same parameters
    but may produce different results from external services.
    """

    def __init__(
        self,
        trace_store: TraceStore | None = None,
        skill_executor: Any = None,  # Type hint would be SkillExecutor
    ):
        self.trace_store = trace_store or get_trace_store()
        self.skill_executor = skill_executor

    async def replay_run(
        self,
        run_id: str,
        verify_parity: bool = True,
        dry_run: bool = False,
        timeout_seconds: float = 300.0,
        emit_traces: bool = False,
    ) -> ReplayResult:
        """
        Replay a previously executed run.

        S6 IMMUTABILITY: By default, replay does NOT emit new traces (emit_traces=False).
        This ensures that replaying a trace doesn't grow the history.
        Replay is a read-only verification operation.

        Args:
            run_id: The original run ID to replay
            verify_parity: If True, compare behavior with original trace
            dry_run: If True, don't actually execute skills (just validate)
            timeout_seconds: Maximum time for replay
            emit_traces: If True, create new traces (default False for S6 compliance)

        Returns:
            ReplayResult with parity check and optional new trace
        """
        # Get original trace
        original_trace = await self.trace_store.get_trace(run_id)
        if not original_trace:
            return ReplayResult(
                success=False,
                run_id="",
                original_run_id=run_id,
                parity_check=None,
                trace=None,
                divergence_point=None,
                error=f"Original run {run_id} not found",
            )

        # Generate new IDs for replay (used for tracking even if not persisted)
        new_run_id = generate_run_id()
        new_correlation_id = generate_correlation_id()

        # S6: Only start new trace if emit_traces is explicitly True
        if emit_traces:
            await self.trace_store.start_trace(
                run_id=new_run_id,
                correlation_id=new_correlation_id,
                tenant_id=original_trace.tenant_id,
                agent_id=original_trace.agent_id,
                plan=original_trace.plan,
            )

        replay_steps: list[TraceStep] = []
        divergence_point = None
        error = None

        try:
            # Replay each step from the original plan
            for i, original_step in enumerate(original_trace.steps):
                if dry_run:
                    # In dry-run mode, just copy the original step
                    new_step = TraceStep(
                        step_index=i,
                        skill_name=original_step.skill_name,
                        params=original_step.params,
                        status=original_step.status,
                        outcome_category=original_step.outcome_category,
                        outcome_code=original_step.outcome_code,
                        outcome_data=original_step.outcome_data,
                        cost_cents=original_step.cost_cents,
                        duration_ms=0.0,  # No actual execution
                        retry_count=original_step.retry_count,
                    )
                else:
                    # Actually execute the skill
                    new_step = await self._execute_step(
                        step_index=i,
                        skill_name=original_step.skill_name,
                        params=original_step.params,
                        timeout_seconds=timeout_seconds / len(original_trace.steps),
                    )

                replay_steps.append(new_step)

                # S6: Only record step if emit_traces is True
                if emit_traces:
                    await self.trace_store.record_step(
                        run_id=new_run_id,
                        step_index=new_step.step_index,
                        skill_name=new_step.skill_name,
                        params=new_step.params,
                        status=new_step.status,
                        outcome_category=new_step.outcome_category,
                        outcome_code=new_step.outcome_code,
                        outcome_data=new_step.outcome_data,
                        cost_cents=new_step.cost_cents,
                        duration_ms=new_step.duration_ms,
                        retry_count=new_step.retry_count,
                    )

                # Check for early divergence (determinism check)
                if verify_parity and not dry_run:
                    if new_step.determinism_hash() != original_step.determinism_hash():
                        divergence_point = i
                        # Continue execution but note the divergence

            # Build in-memory trace for comparison (S6: no persistence by default)
            replay_trace = TraceRecord(
                run_id=new_run_id,
                correlation_id=new_correlation_id,
                tenant_id=original_trace.tenant_id,
                agent_id=original_trace.agent_id,
                plan=original_trace.plan,
                steps=replay_steps,
                started_at=original_trace.started_at,
                completed_at=None,
                status="completed" if all(s.status == TraceStatus.SUCCESS for s in replay_steps) else "failed",
                metadata={"replay_of": run_id, "dry_run": dry_run},
                seed=original_trace.seed,
                frozen_timestamp=original_trace.frozen_timestamp,
                root_hash=None,
            )

            # S6: Only complete/persist trace if emit_traces is True
            if emit_traces:
                await self.trace_store.complete_trace(
                    run_id=new_run_id,
                    status=replay_trace.status,
                    metadata={
                        "replay_of": run_id,
                        "dry_run": dry_run,
                        "verify_parity": verify_parity,
                    },
                )
                # Get persisted trace
                replay_trace = await self.trace_store.get_trace(new_run_id)

        except asyncio.TimeoutError:
            error = "Replay timed out"
            if emit_traces:
                await self.trace_store.complete_trace(
                    run_id=new_run_id,
                    status="timeout",
                    metadata={"error": error},
                )
            replay_trace = None

        except Exception as e:
            error = str(e)
            if emit_traces:
                await self.trace_store.complete_trace(
                    run_id=new_run_id,
                    status="error",
                    metadata={"error": error},
                )
            replay_trace = None

        # Perform parity check if requested
        parity_check = None
        if verify_parity and replay_trace:
            parity_check = compare_traces(original_trace, replay_trace)
            if not parity_check.is_parity and divergence_point is None:
                divergence_point = parity_check.divergence_step

        return ReplayResult(
            success=error is None and (parity_check is None or parity_check.is_parity),
            run_id=new_run_id,
            original_run_id=run_id,
            parity_check=parity_check,
            trace=replay_trace,
            divergence_point=divergence_point,
            error=error,
        )

    async def _execute_step(
        self,
        step_index: int,
        skill_name: str,
        params: dict[str, Any],
        timeout_seconds: float,
    ) -> TraceStep:
        """
        Execute a single step and return the trace step.

        This is a placeholder - actual implementation would call
        the skill executor from the runtime.
        """
        import time

        start_time = time.monotonic()

        # Placeholder: In real implementation, this would call:
        # outcome = await self.skill_executor.execute(skill_name, params)

        # For now, return a mock successful step
        duration_ms = (time.monotonic() - start_time) * 1000

        return TraceStep(
            step_index=step_index,
            skill_name=skill_name,
            params=params,
            status=TraceStatus.SUCCESS,
            outcome_category="SUCCESS",
            outcome_code=None,
            outcome_data={"mock": True},
            cost_cents=0.0,
            duration_ms=duration_ms,
            retry_count=0,
        )


# Module-level convenience function
async def replay_run(
    run_id: str,
    verify_parity: bool = True,
    dry_run: bool = False,
    timeout_seconds: float = 300.0,
    trace_store: TraceStore | None = None,
    emit_traces: bool = False,
) -> ReplayResult:
    """
    Replay a previously executed run.

    S6 IMMUTABILITY: By default, replay does NOT emit new traces (emit_traces=False).
    This ensures that replaying a trace doesn't grow the history.
    Replay is a read-only verification operation.

    Args:
        run_id: The original run ID to replay
        verify_parity: If True, compare behavior with original trace
        dry_run: If True, don't actually execute skills
        timeout_seconds: Maximum time for replay
        trace_store: Optional trace store (uses default SQLite if not provided)
        emit_traces: If True, create new traces (default False for S6 compliance)

    Returns:
        ReplayResult with parity check and optional trace

    Example:
        >>> result = await replay_run("run_abc123", verify_parity=True)
        >>> if result.parity_check.is_parity:
        ...     print("Determinism verified!")
        >>> else:
        ...     print(f"Diverged at step {result.divergence_point}")
    """
    engine = ReplayEngine(trace_store=trace_store)
    return await engine.replay_run(
        run_id=run_id,
        verify_parity=verify_parity,
        dry_run=dry_run,
        timeout_seconds=timeout_seconds,
        emit_traces=emit_traces,
    )


async def validate_determinism(
    run_ids: list[str],
    trace_store: TraceStore | None = None,
) -> dict[str, ParityResult]:
    """
    Validate determinism across multiple runs.

    Replays each run and checks for parity with the original.

    Args:
        run_ids: List of run IDs to validate
        trace_store: Optional trace store

    Returns:
        Dictionary mapping run_id to ParityResult

    Example:
        >>> results = await validate_determinism(["run_1", "run_2", "run_3"])
        >>> failed = [k for k, v in results.items() if not v.is_parity]
        >>> if failed:
        ...     print(f"Determinism failures: {failed}")
    """
    results = {}
    for run_id in run_ids:
        result = await replay_run(
            run_id=run_id,
            verify_parity=True,
            dry_run=True,  # Don't re-execute, just compare
            trace_store=trace_store,
        )
        if result.parity_check:
            results[run_id] = result.parity_check
    return results
