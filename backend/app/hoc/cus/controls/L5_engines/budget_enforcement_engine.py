# Layer: L4 — Domain Engine (System Truth)
# Product: system-wide (NOT console-owned)
# Temporal:
#   Trigger: scheduler (background task)
#   Execution: async
# Role: Budget enforcement decision-making (domain logic)
# Authority: Budget decision generation (M9/M10 pattern)
# Callers: Background tasks, API endpoints
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Contract: DECISION_RECORD_CONTRACT.md
# Reference: PIN-257 Phase R-3 (L5→L4 Violation Fix)
#
# GOVERNANCE NOTE: This L4 engine owns BUDGET ENFORCEMENT DECISION logic.
# L5 runner.py owns only EXECUTION logic (halting the run).
# This separation fixes the L5→L4 import violation identified in
# PHASE_R_L5_L4_VIOLATIONS.md (violation #1).

# M11 Budget Enforcement Engine (L4 Domain Logic)
"""
Domain engine for budget enforcement decisions.

This L4 engine contains the authoritative logic for:
1. Identifying runs halted due to budget enforcement
2. Emitting budget_enforcement decision records

L5 workers must halt runs when budget is exhausted but must NOT
emit decision records directly. Decision emission is L4 responsibility.

Reference: PIN-257 Phase R-3
Governance: PHASE_R_L5_L4_VIOLATIONS.md
"""

import logging
import os
from typing import Optional

logger = logging.getLogger("nova.services.budget_enforcement_engine")

# L4 imports (same layer - allowed)
from app.contracts.decisions import emit_budget_enforcement_decision

# L6 driver import (allowed)
from app.hoc.cus.controls.L6_drivers.budget_enforcement_driver import (
    BudgetEnforcementDriver,
    get_budget_enforcement_driver,
)

# =============================================================================
# Budget Enforcement Engine (L4 Domain Logic)
# =============================================================================


class BudgetEnforcementEngine:
    """
    L4 Domain Engine for budget enforcement decisions.

    This engine contains the decision emission logic that was previously
    in L5 runner.py. It processes halted runs and emits budget_enforcement
    decision records.

    L5 may NOT:
    - Import app.contracts.decisions
    - Emit decision records directly
    - Call emit_budget_enforcement_decision()

    L5 may ONLY:
    - Check budget and halt execution when exhausted
    - Update run status to "halted"
    - Publish run.halted events
    - Store halt information in provenance

    Reference: PIN-257 Phase R-3
    Governance: PHASE_R_L5_L4_VIOLATIONS.md Section 3.2
    """

    def __init__(self):
        """Initialize the budget enforcement engine."""
        self._db_url = os.environ.get("DATABASE_URL")

    def emit_decision_for_halt(
        self,
        run_id: str,
        budget_limit_cents: int,
        budget_consumed_cents: int,
        step_cost_cents: int,
        completed_steps: int,
        total_steps: int,
        tenant_id: str = "default",
    ) -> bool:
        """
        Emit budget enforcement decision for a halted run.

        This is the L4 entry point for decision emission. It wraps the
        emit_budget_enforcement_decision function and handles errors.

        Args:
            run_id: ID of the halted run
            budget_limit_cents: Budget limit in cents
            budget_consumed_cents: Total consumed including this run
            step_cost_cents: Cost of the last step before halt
            completed_steps: Number of steps completed before halt
            total_steps: Total steps in the plan
            tenant_id: Tenant ID

        Returns:
            True if decision was emitted, False if skipped or failed

        Reference: PIN-257 Phase R-3
        """
        logger.info(
            "L4 emitting budget enforcement decision",
            extra={
                "run_id": run_id,
                "budget_limit_cents": budget_limit_cents,
                "budget_consumed_cents": budget_consumed_cents,
            },
        )

        try:
            result = emit_budget_enforcement_decision(
                run_id=run_id,
                budget_limit_cents=budget_limit_cents,
                budget_consumed_cents=budget_consumed_cents,
                step_cost_cents=step_cost_cents,
                completed_steps=completed_steps,
                total_steps=total_steps,
                tenant_id=tenant_id,
            )

            if result is None:
                logger.debug(
                    "L4 budget enforcement decision already emitted (idempotent)",
                    extra={"run_id": run_id},
                )
                return False

            logger.info(
                "L4 budget enforcement decision emitted",
                extra={
                    "run_id": run_id,
                    "decision_id": result.decision_id,
                },
            )
            return True

        except Exception as e:
            logger.error(
                "L4 failed to emit budget enforcement decision",
                extra={"run_id": run_id, "error": str(e)},
            )
            return False

    def process_pending_halts(self) -> int:
        """
        Process runs halted for budget that don't have decision records.

        This method is called by background tasks to ensure all budget
        halts have corresponding decision records. It handles the case
        where L5 halted a run but the decision record wasn't emitted
        (e.g., due to process crash, or due to Phase R-3 migration).

        Returns:
            Number of decision records emitted

        Reference: PIN-257 Phase R-3
        """
        if not self._db_url:
            logger.warning("DATABASE_URL not set, cannot process pending halts")
            return 0

        emitted = 0
        driver = get_budget_enforcement_driver(self._db_url)

        try:
            # L6: Delegate query to driver
            rows = driver.fetch_pending_budget_halts(limit=100)

            for row in rows:
                run_id = row["run_id"]
                # AUTH_DESIGN.md: AUTH-TENANT-005 - No fallback tenant.
                # Skip rows without tenant_id (legacy data) rather than using fake tenant.
                tenant_id = row["tenant_id"]
                if not tenant_id:
                    logger.warning("Skipping run without tenant_id", extra={"run_id": run_id})
                    continue
                error_message = row["error_message"] or ""
                plan_json_str = row["plan_json"]
                tool_calls_json_str = row["tool_calls_json"]

                # L4 DECISION: Parse budget info from error message
                # Format: "Hard budget limit reached: Xc consumed >= Yc limit"
                budget_info = self._parse_budget_from_error(error_message)
                if not budget_info:
                    logger.warning(
                        "Could not parse budget info from error message",
                        extra={"run_id": run_id, "error_message": error_message[:100]},
                    )
                    continue

                # L4 DECISION: Count steps from plan and tool_calls
                import json

                total_steps = 0
                completed_steps = 0

                if plan_json_str:
                    try:
                        plan = json.loads(plan_json_str)
                        total_steps = len(plan.get("steps", []))
                    except (json.JSONDecodeError, TypeError):
                        pass

                if tool_calls_json_str:
                    try:
                        tool_calls = json.loads(tool_calls_json_str)
                        completed_steps = len(tool_calls)
                    except (json.JSONDecodeError, TypeError):
                        pass

                # L4 DECISION: Emit decision
                success = self.emit_decision_for_halt(
                    run_id=run_id,
                    budget_limit_cents=budget_info["limit_cents"],
                    budget_consumed_cents=budget_info["consumed_cents"],
                    step_cost_cents=0,  # Not available from error message
                    completed_steps=completed_steps,
                    total_steps=total_steps,
                    tenant_id=tenant_id,
                )

                if success:
                    emitted += 1

            driver.dispose()

        except Exception as e:
            logger.error(
                "Failed to process pending budget halts",
                extra={"error": str(e)},
            )

        if emitted > 0:
            logger.info(
                "L4 processed pending budget halts",
                extra={"decisions_emitted": emitted},
            )

        return emitted

    def _parse_budget_from_error(self, error_message: str) -> Optional[dict]:
        """
        Parse budget information from error message.

        Expected format: "Hard budget limit reached: Xc consumed >= Yc limit"
        """
        import re

        match = re.search(r"(\d+)c consumed >= (\d+)c limit", error_message)
        if not match:
            return None

        return {
            "consumed_cents": int(match.group(1)),
            "limit_cents": int(match.group(2)),
        }


# =============================================================================
# Convenience Functions
# =============================================================================


def emit_budget_halt_decision(
    run_id: str,
    budget_limit_cents: int,
    budget_consumed_cents: int,
    step_cost_cents: int,
    completed_steps: int,
    total_steps: int,
    tenant_id: str = "default",
) -> bool:
    """
    Convenience function to emit a budget enforcement decision.

    This is the L4 entry point for budget enforcement decision emission.
    It should be called by L4 orchestration code (e.g., background tasks,
    event handlers) when a run is halted due to budget enforcement.

    Args:
        run_id: ID of the halted run
        budget_limit_cents: Budget limit in cents
        budget_consumed_cents: Total consumed including this run
        step_cost_cents: Cost of the last step before halt
        completed_steps: Number of steps completed before halt
        total_steps: Total steps in the plan
        tenant_id: Tenant ID

    Returns:
        True if decision was emitted, False if skipped or failed

    Reference: PIN-257 Phase R-3
    """
    engine = BudgetEnforcementEngine()
    return engine.emit_decision_for_halt(
        run_id=run_id,
        budget_limit_cents=budget_limit_cents,
        budget_consumed_cents=budget_consumed_cents,
        step_cost_cents=step_cost_cents,
        completed_steps=completed_steps,
        total_steps=total_steps,
        tenant_id=tenant_id,
    )


async def process_pending_budget_decisions() -> int:
    """
    Process all pending budget halt decisions.

    This function is intended to be called by a background task at startup
    or periodically to ensure all budget halts have corresponding decision
    records.

    Returns:
        Number of decision records emitted

    Reference: PIN-257 Phase R-3
    """
    engine = BudgetEnforcementEngine()
    return engine.process_pending_halts()


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "BudgetEnforcementEngine",
    "emit_budget_halt_decision",
    "process_pending_budget_decisions",
]
