# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (L2 HTTP request via registry dispatch)
#   Execution: async
# Role: Analytics prediction handler — routes prediction queries to L5 engine
# Callers: OperationRegistry (L4)
# Allowed Imports: hoc_spine (orchestrator), hoc.cus.analytics.L5_engines (lazy), L6_drivers (lazy)
# Forbidden Imports: L1, L2, sqlalchemy (except types)
# Reference: PIN-513 Wiring Plan (prediction_engine)
# artifact_class: CODE

"""
Analytics Prediction Handler (L4 Orchestrator)

Routes prediction operations to PredictionEngine (L5).
Predictions are read-only advisory outputs — no execution side effects.

Operations:
  - analytics.prediction → PredictionEngine (generate, summary, cycle)

Note: predict_failure_likelihood and predict_cost_overrun require a
PredictionDriver (L6) instance. run_prediction_cycle and get_prediction_summary
manage their own sessions internally.
"""

import logging
from typing import Any

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)

logger = logging.getLogger("nova.hoc_spine.handlers.analytics_prediction")


class AnalyticsPredictionHandler:
    """
    Handler for analytics.prediction operations.

    Dispatches to PredictionEngine (L5) methods.
    All predictions are advisory — zero execution impact.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        dispatch = {
            "predict_failure": self._predict_failure,
            "predict_cost_overrun": self._predict_cost_overrun,
            "run_cycle": self._run_cycle,
            "get_summary": self._get_summary,
        }
        method = dispatch.get(method_name)
        if method is None:
            return OperationResult.fail(
                f"Unknown prediction method: {method_name}", "UNKNOWN_METHOD"
            )

        return await method(ctx)

    async def _predict_failure(self, ctx: OperationContext) -> OperationResult:
        """Generate failure likelihood predictions."""
        from app.hoc.cus.analytics.L5_engines.prediction_engine import (
            predict_failure_likelihood,
        )
        from app.hoc.cus.analytics.L6_drivers.prediction_driver import (
            get_prediction_driver,
        )

        driver = get_prediction_driver(session=ctx.session)
        result = await predict_failure_likelihood(
            driver=driver, tenant_id=ctx.tenant_id
        )
        return OperationResult.ok(result)

    async def _predict_cost_overrun(self, ctx: OperationContext) -> OperationResult:
        """Generate cost overrun predictions."""
        from app.hoc.cus.analytics.L5_engines.prediction_engine import (
            predict_cost_overrun,
        )
        from app.hoc.cus.analytics.L6_drivers.prediction_driver import (
            get_prediction_driver,
        )

        driver = get_prediction_driver(session=ctx.session)
        result = await predict_cost_overrun(
            driver=driver, tenant_id=ctx.tenant_id
        )
        return OperationResult.ok(result)

    async def _run_cycle(self, ctx: OperationContext) -> OperationResult:
        """Run full prediction cycle (failure + cost overrun)."""
        from app.hoc.cus.analytics.L5_engines.prediction_engine import (
            run_prediction_cycle,
        )

        result = await run_prediction_cycle(tenant_id=ctx.tenant_id)
        return OperationResult.ok(result)

    async def _get_summary(self, ctx: OperationContext) -> OperationResult:
        """Get prediction summary (current valid predictions)."""
        from app.hoc.cus.analytics.L5_engines.prediction_engine import (
            get_prediction_summary,
        )

        result = await get_prediction_summary(tenant_id=ctx.tenant_id)
        return OperationResult.ok(result)


def register(registry: OperationRegistry) -> None:
    """Register analytics.prediction operation with the OperationRegistry."""
    handler = AnalyticsPredictionHandler()
    registry.register("analytics.prediction", handler)
