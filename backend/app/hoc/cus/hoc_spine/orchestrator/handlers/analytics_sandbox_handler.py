# capability_id: CAP-012
# Layer: L4 — HOC Spine (Handler)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: L4 handler — CostSim sandbox experimentation
# Callers: Admin APIs, runtime simulation paths
# Allowed Imports: hoc_spine, hoc.cus.analytics.L5_engines (lazy)
# Forbidden Imports: L1, L2
# Reference: PIN-513 Batch 3A5 Wiring
# artifact_class: CODE

"""
Analytics Sandbox Handler (PIN-513 Batch 3A5 Wiring)

L4 handler for controlled CostSim sandbox experimentation.

Wires from analytics/L5_engines/sandbox_engine.py:
- simulate_with_sandbox(plan, budget_cents, allowed_skills, tenant_id, run_id)
- get_sandbox(budget_cents, tenant_id)
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nova.hoc_spine.handlers.analytics_sandbox")


class AnalyticsSandboxHandler:
    """L4 handler: CostSim sandbox experimentation."""

    async def simulate(
        self,
        plan: List[Dict[str, Any]],
        budget_cents: int = 1000,
        allowed_skills: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> Any:
        """Run a sandbox simulation."""
        from app.hoc.cus.analytics.L5_engines.sandbox_engine import (
            simulate_with_sandbox,
        )

        result = await simulate_with_sandbox(
            plan=plan,
            budget_cents=budget_cents,
            allowed_skills=allowed_skills,
            tenant_id=tenant_id,
            run_id=run_id,
        )
        logger.info(
            "sandbox_simulation_completed",
            extra={"tenant_id": tenant_id, "run_id": run_id},
        )
        return result

    def get_sandbox(
        self,
        budget_cents: int = 1000,
        tenant_id: Optional[str] = None,
    ) -> Any:
        """Get a sandbox instance for manual use."""
        from app.hoc.cus.analytics.L5_engines.sandbox_engine import get_sandbox

        return get_sandbox(
            budget_cents=budget_cents,
            tenant_id=tenant_id,
        )
