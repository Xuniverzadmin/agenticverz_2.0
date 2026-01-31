# Layer: L2 — Adapter
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async (delegates to L4)
# Role: Worker execution boundary adapter (L2 → L4)
# Callers: workers.py (L2)
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L5
# Reference: PIN-258 Phase F-3 Workers Cluster
# Contract: PHASE_F_FIX_DESIGN (F-W-RULE-1 to F-W-RULE-5)
#
# GOVERNANCE NOTE (F-W-RULE-4):
# This adapter is the ONLY entry point for L2 workers.py.
# L2 must never import L5 workers directly. This adapter translates
# API requests to L4 command calls.
#
# F-W-RULE-1: No semantic changes - all logic stays where it is.
# F-W-RULE-2: Workers are blind executors - we don't call them directly.
# F-W-RULE-4: Adapter Is the Only Entry - L2 calls only this file.

"""
Workers Adapter (L2)

This adapter sits between L2 (workers.py API) and L4 (worker_execution_command.py).

L2 (API) → L4 (command) → L5 (worker execution)

The adapter:
1. Receives API requests with execution context
2. Translates to domain facts
3. Delegates to L4 commands
4. Returns results to L2

This is a thin translation layer - no business logic, no state mutation.

Reference: PIN-258 Phase F-3 Workers Cluster
"""

from typing import Any, Optional

from app.commands.worker_execution_command import (
    ReplayResult,
    WorkerExecutionResult,
    calculate_cost_cents,
    convert_brand_request,
    execute_worker,
    replay_execution,
)

# =============================================================================
# Adapter Class
# =============================================================================


class WorkersAdapter:
    """
    Boundary adapter for worker operations.

    This class provides the ONLY interface that L2 (workers.py) may use
    to access worker functionality. It translates API context to domain
    facts and delegates to L4 commands.

    F-W-RULE-4: Adapter Is the Only Entry
    """

    async def execute_worker(
        self,
        task: str,
        brand: Optional[Any] = None,
        budget: Optional[int] = None,
        strict_mode: bool = False,
        depth: int = 2,
        run_id: Optional[str] = None,
        event_bus: Optional[Any] = None,
    ) -> WorkerExecutionResult:
        """
        Execute Business Builder Worker.

        This method translates API context to domain facts and
        delegates to L4 execute_worker command.

        Args:
            task: Business/product idea
            brand: Optional brand schema (from API)
            budget: Optional budget
            strict_mode: Whether to use strict mode
            depth: Execution depth
            run_id: Run ID for tracking
            event_bus: Optional event bus for SSE

        Returns:
            WorkerExecutionResult from L4 command

        Reference: PIN-258 Phase F-3 (F-W-RULE-1: No semantic changes)
        """
        # L2 → L4 delegation (allowed import)
        return await execute_worker(
            task=task,
            brand=brand,
            budget=budget,
            strict_mode=strict_mode,
            depth=depth,
            run_id=run_id,
            event_bus=event_bus,
        )

    async def replay_execution(
        self,
        replay_token: str,
        run_id: str,
    ) -> ReplayResult:
        """
        Replay a previous execution.

        This method translates API context to domain facts and
        delegates to L4 replay_execution command.

        Args:
            replay_token: Token from previous execution
            run_id: New run ID for this replay

        Returns:
            ReplayResult from L4 command

        Reference: PIN-258 Phase F-3 (F-W-RULE-1: No semantic changes)
        """
        # L2 → L4 delegation (allowed import)
        return await replay_execution(replay_token=replay_token, run_id=run_id)

    def calculate_cost_cents(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> int:
        """
        Calculate LLM cost in cents.

        This method delegates to L4 for cost calculation.

        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in cents

        Reference: PIN-258 Phase F-3 (F-W-RULE-1: No semantic changes)
        """
        # L2 → L4 delegation (allowed import)
        return calculate_cost_cents(model, input_tokens, output_tokens)

    def convert_brand_request(self, brand_req: Any) -> Any:
        """
        Convert API brand request to BrandSchema.

        This method delegates to L4 for schema conversion.

        Args:
            brand_req: Brand request from API

        Returns:
            BrandSchema instance

        Reference: PIN-258 Phase F-3 (F-W-RULE-1: No semantic changes)
        """
        # L2 → L4 delegation (allowed import)
        return convert_brand_request(brand_req)


# =============================================================================
# Singleton Factory
# =============================================================================

_workers_adapter_instance: Optional[WorkersAdapter] = None


def get_workers_adapter() -> WorkersAdapter:
    """
    Get the singleton WorkersAdapter instance.

    This is the ONLY way L2 should obtain a workers adapter.
    Direct instantiation is discouraged.

    Returns:
        WorkersAdapter singleton instance

    Reference: PIN-258 Phase F-3 (F-W-RULE-4: Adapter Is the Only Entry)
    """
    global _workers_adapter_instance
    if _workers_adapter_instance is None:
        _workers_adapter_instance = WorkersAdapter()
    return _workers_adapter_instance


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "WorkersAdapter",
    "get_workers_adapter",
    # Re-export result types for L2 convenience
    "WorkerExecutionResult",
    "ReplayResult",
]
