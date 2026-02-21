# capability_id: CAP-012
# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: L4 coordinator — deterministic replay enforcement via ReplayDriver (L6)
# Callers: LogsReplayHandler (L4), job_executor (L4)
# Allowed Imports: hoc_spine, hoc.cus.logs.L6_drivers (lazy)
# Forbidden Imports: L1, L2
# Reference: PIN-513 Wiring Plan (replay_driver), M8 Deliverable
# artifact_class: CODE

"""
Replay Coordinator (PIN-513 Wiring)

L4 coordinator that owns deterministic replay enforcement.

Binds ReplayDriver (L6) to provide:
- Step-level replay behavior enforcement (EXECUTE / SKIP / CHECK)
- Idempotency verification via SHA256 output hashing
- Trace-level replay orchestration

Flow:
  Step execution
    → ReplayCoordinator.enforce_step(...)
        → ReplayEnforcer.enforce_step(step, execute_fn, tenant_id)
        → ReplayResult (executed/skipped/checked)

Rules:
- Coordinator decides WHEN to enforce replay (scheduling authority)
- Driver decides HOW to enforce (idempotency mechanics)
- No business logic — pure replay semantics
"""

import logging
from typing import Any, Awaitable, Callable, Dict

logger = logging.getLogger("nova.hoc_spine.coordinators.replay")


class ReplayCoordinator:
    """L4 coordinator: deterministic replay enforcement.

    Owns the replay lifecycle — no L5 engine or L2 route may
    call ReplayDriver directly.
    """

    def __init__(self):
        self._enforcer = None

    def _get_enforcer(self):
        """Lazy-init ReplayEnforcer singleton."""
        if self._enforcer is None:
            from app.hoc.cus.logs.L6_drivers.replay_driver import (
                get_replay_enforcer,
            )

            self._enforcer = get_replay_enforcer()
        return self._enforcer

    async def enforce_step(
        self,
        step: Dict[str, Any],
        execute_fn: Callable[[], Awaitable[Any]],
        tenant_id: str,
    ) -> Dict[str, Any]:
        """Enforce replay behavior for a single step.

        Args:
            step: Step dict containing idempotency_key, behavior, etc.
            execute_fn: Async callable to run if behavior is EXECUTE
            tenant_id: Tenant for scoped idempotency

        Returns:
            Dict with executed, skipped, checked, output_hash, from_cache
        """
        enforcer = self._get_enforcer()

        result = await enforcer.enforce_step(
            step=step,
            execute_fn=execute_fn,
            tenant_id=tenant_id,
        )

        return {
            "executed": result.executed,
            "skipped": result.skipped,
            "checked": result.checked,
            "output_hash": result.output_hash,
            "from_cache": result.from_cache,
        }

    async def enforce_trace(
        self,
        trace: Dict[str, Any],
        step_executor: Callable[[Dict[str, Any]], Awaitable[Any]],
        tenant_id: str,
    ) -> Dict[str, Any]:
        """Enforce replay behavior for an entire trace.

        Args:
            trace: Trace dict containing steps and metadata
            step_executor: Async callable that executes a single step dict
            tenant_id: Tenant for scoped idempotency

        Returns:
            Dict with results per step, summary counts
        """
        enforcer = self._get_enforcer()

        results = await enforcer.enforce_trace(
            trace=trace,
            step_executor=step_executor,
            tenant_id=tenant_id,
        )

        return {
            "step_results": [
                {
                    "executed": r.executed,
                    "skipped": r.skipped,
                    "checked": r.checked,
                    "output_hash": r.output_hash,
                    "from_cache": r.from_cache,
                }
                for r in results
            ],
            "total_steps": len(results),
            "executed": sum(1 for r in results if r.executed),
            "skipped": sum(1 for r in results if r.skipped),
            "checked": sum(1 for r in results if r.checked),
        }
