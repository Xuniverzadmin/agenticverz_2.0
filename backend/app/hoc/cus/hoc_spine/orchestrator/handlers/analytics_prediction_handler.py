# capability_id: CAP-012
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

Routes prediction operations to PredictionEngine and PredictionReadEngine (L5).
Predictions are read-only advisory outputs — no execution side effects.

Operations:
  - analytics.prediction → PredictionEngine (generate, summary, cycle)
  - analytics.prediction_read → PredictionReadEngine (list, get, for_subject, stats)

Note: predict_failure_likelihood and predict_cost_overrun require a
PredictionDriver (L6) instance. run_prediction_cycle and get_prediction_summary
receive their session from the L4 handler (PIN-520 Phase 4).
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

        result = await run_prediction_cycle(tenant_id=ctx.tenant_id, session=ctx.session)
        return OperationResult.ok(result)

    async def _get_summary(self, ctx: OperationContext) -> OperationResult:
        """Get prediction summary (current valid predictions)."""
        from app.hoc.cus.analytics.L5_engines.prediction_engine import (
            get_prediction_summary,
        )

        result = await get_prediction_summary(tenant_id=ctx.tenant_id, session=ctx.session)
        return OperationResult.ok(result)


class AnalyticsPredictionReadHandler:
    """
    Handler for analytics.prediction_read operations.

    Dispatches to PredictionReadEngine (L5) methods.
    Pure read operations - no side effects.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        dispatch = {
            "list": self._list_predictions,
            "get": self._get_prediction,
            "for_subject": self._get_for_subject,
            "stats": self._get_stats,
        }
        method = dispatch.get(method_name)
        if method is None:
            return OperationResult.fail(
                f"Unknown prediction read method: {method_name}", "UNKNOWN_METHOD"
            )

        return await method(ctx)

    async def _list_predictions(self, ctx: OperationContext) -> OperationResult:
        """List predictions with filters and pagination."""
        from app.hoc.cus.analytics.L5_engines.prediction_read_engine import (
            get_prediction_read_engine,
        )

        engine = get_prediction_read_engine()
        result = await engine.list_predictions(
            session=ctx.session,
            tenant_id=ctx.tenant_id,
            prediction_type=ctx.params.get("prediction_type"),
            subject_type=ctx.params.get("subject_type"),
            subject_id=ctx.params.get("subject_id"),
            include_expired=ctx.params.get("include_expired", False),
            limit=ctx.params.get("limit", 50),
            offset=ctx.params.get("offset", 0),
        )
        return OperationResult.ok(result)

    async def _get_prediction(self, ctx: OperationContext) -> OperationResult:
        """Get single prediction by ID."""
        from app.hoc.cus.analytics.L5_engines.prediction_read_engine import (
            get_prediction_read_engine,
        )

        prediction_id = ctx.params.get("prediction_id")
        if not prediction_id:
            return OperationResult.fail(
                "Missing 'prediction_id' in params", "MISSING_PREDICTION_ID"
            )

        engine = get_prediction_read_engine()
        result = await engine.get_prediction(
            session=ctx.session,
            tenant_id=ctx.tenant_id,
            prediction_id=prediction_id,
        )
        if result is None:
            return OperationResult.fail(
                f"Prediction {prediction_id} not found", "NOT_FOUND"
            )
        return OperationResult.ok(result)

    async def _get_for_subject(self, ctx: OperationContext) -> OperationResult:
        """Get predictions for a specific subject."""
        from app.hoc.cus.analytics.L5_engines.prediction_read_engine import (
            get_prediction_read_engine,
        )

        subject_type = ctx.params.get("subject_type")
        subject_id = ctx.params.get("subject_id")
        if not subject_type or not subject_id:
            return OperationResult.fail(
                "Missing 'subject_type' or 'subject_id' in params",
                "MISSING_SUBJECT_PARAMS",
            )

        engine = get_prediction_read_engine()
        result = await engine.get_predictions_for_subject(
            session=ctx.session,
            tenant_id=ctx.tenant_id,
            subject_type=subject_type,
            subject_id=subject_id,
            include_expired=ctx.params.get("include_expired", False),
            limit=ctx.params.get("limit", 20),
        )
        return OperationResult.ok(result)

    async def _get_stats(self, ctx: OperationContext) -> OperationResult:
        """Get prediction statistics."""
        from app.hoc.cus.analytics.L5_engines.prediction_read_engine import (
            get_prediction_read_engine,
        )

        engine = get_prediction_read_engine()
        result = await engine.get_prediction_stats(
            session=ctx.session,
            tenant_id=ctx.tenant_id,
            include_expired=ctx.params.get("include_expired", False),
        )
        return OperationResult.ok(result)


def register(registry: OperationRegistry) -> None:
    """Register analytics prediction operations with the OperationRegistry."""
    # Prediction write/generate operations
    handler = AnalyticsPredictionHandler()
    registry.register("analytics.prediction", handler)

    # Prediction read operations
    read_handler = AnalyticsPredictionReadHandler()
    registry.register("analytics.prediction_read", read_handler)
