# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (L2 HTTP request via registry dispatch)
#   Execution: async
# Role: Analytics domain handler — routes analytics operations to L5 facades via L4 registry
# Callers: OperationRegistry (L4)
# Allowed Imports: hoc_spine (orchestrator), hoc.cus.analytics.L5_engines (lazy)
# Forbidden Imports: L1, L2, L6, sqlalchemy (except types)
# Reference: PIN-491 (L2-L4-L5 Construction Plan), Phase A.1
# artifact_class: CODE

"""
Analytics Handler (L4 Orchestrator)

Routes analytics domain operations to L5 facades and coordinators.
Registers four operations:
  - analytics.query → AnalyticsFacade
  - analytics.detection → DetectionFacade
  - analytics.canary_reports → CanaryReportDriver (L6 queries)
  - analytics.canary → CanaryCoordinator (scheduled validation runs)
"""

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)


class FeedbackReadHandler:
    """
    Handler for analytics.feedback operations.

    Dispatches to FeedbackReadEngine methods (list_feedback,
    get_feedback, get_feedback_stats).

    PB-S3 Pattern: READ-ONLY operations only.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from uuid import UUID

        from app.hoc.cus.analytics.L5_engines.feedback_read_engine import (
            get_feedback_read_engine,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        engine = get_feedback_read_engine()

        # Handle get_feedback with UUID validation
        if method_name == "get_feedback":
            feedback_id = ctx.params.get("feedback_id")
            if not feedback_id:
                return OperationResult.fail(
                    "Missing 'feedback_id' in params", "MISSING_FEEDBACK_ID"
                )
            try:
                UUID(feedback_id)
            except ValueError:
                return OperationResult.fail(
                    "Invalid feedback ID format", "INVALID_FORMAT"
                )

        dispatch = {
            "list_feedback": engine.list_feedback,
            "get_feedback": engine.get_feedback,
            "get_feedback_stats": engine.get_feedback_stats,
        }
        method = dispatch.get(method_name)
        if method is None:
            return OperationResult.fail(
                f"Unknown feedback method: {method_name}", "UNKNOWN_METHOD"
            )

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        data = await method(session=ctx.session, tenant_id=ctx.tenant_id, **kwargs)

        # Handle not found case for get_feedback
        if method_name == "get_feedback" and data is None:
            feedback_id = kwargs.get("feedback_id", "unknown")
            return OperationResult.fail(
                f"Feedback {feedback_id} not found", "NOT_FOUND"
            )

        return OperationResult.ok(data)


class AnalyticsQueryHandler:
    """
    Handler for analytics.query operations.

    Dispatches to AnalyticsFacade methods (get_usage_statistics,
    get_cost_statistics, get_status).
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.analytics.L5_engines.analytics_facade import (
            get_analytics_facade,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        facade = get_analytics_facade()
        dispatch = {
            "get_usage_statistics": facade.get_usage_statistics,
            "get_cost_statistics": facade.get_cost_statistics,
            "get_status": facade.get_status,
        }
        method = dispatch.get(method_name)
        if method is None:
            return OperationResult.fail(
                f"Unknown facade method: {method_name}", "UNKNOWN_METHOD"
            )

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        data = await method(session=ctx.session, tenant_id=ctx.tenant_id, **kwargs)
        return OperationResult.ok(data)


class AnalyticsDetectionHandler:
    """
    Handler for analytics.detection operations.

    Dispatches to DetectionFacade methods (run_detection, list_anomalies,
    get_anomaly, resolve_anomaly, acknowledge_anomaly, get_detection_status).
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.analytics.L5_engines.detection_facade import (
            get_detection_facade,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        facade = get_detection_facade()
        dispatch = {
            "run_detection": facade.run_detection,
            "list_anomalies": facade.list_anomalies,
            "get_anomaly": facade.get_anomaly,
            "resolve_anomaly": facade.resolve_anomaly,
            "acknowledge_anomaly": facade.acknowledge_anomaly,
            "get_detection_status": facade.get_detection_status,
        }
        method = dispatch.get(method_name)
        if method is None:
            return OperationResult.fail(
                f"Unknown facade method: {method_name}", "UNKNOWN_METHOD"
            )

        kwargs = dict(ctx.params)
        kwargs.pop("method", None)
        data = await method(tenant_id=ctx.tenant_id, **kwargs)
        return OperationResult.ok(data)


class CanaryReportHandler:
    """
    Handler for analytics.canary_reports operations.

    Routes canary report queries through L4 to L6.
    Ensures policy/audit hooks can be added later.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.analytics.L6_drivers.canary_report_driver import (
            query_canary_reports,
            get_canary_report_by_run_id,
        )

        method_name = ctx.params.get("method", "list")

        if method_name == "list":
            reports = await query_canary_reports(
                status=ctx.params.get("status"),
                passed=ctx.params.get("passed"),
                limit=ctx.params.get("limit", 10),
                offset=ctx.params.get("offset", 0),
            )
            return OperationResult.ok({
                "reports": reports,
                "total": len(reports),
            })

        elif method_name == "get":
            run_id = ctx.params.get("run_id")
            if not run_id:
                return OperationResult.fail("Missing 'run_id'", "MISSING_RUN_ID")
            report = await get_canary_report_by_run_id(run_id)
            if report is None:
                return OperationResult.fail(
                    f"Canary report not found: {run_id}", "NOT_FOUND"
                )
            return OperationResult.ok(report)

        else:
            return OperationResult.fail(
                f"Unknown canary method: {method_name}", "UNKNOWN_METHOD"
            )


class CanaryRunHandler:
    """
    Handler for analytics.canary operations.

    Dispatches to CanaryCoordinator for scheduled canary validation runs.
    This is the L4 entry point for scheduler/cron invocations.

    Methods:
      - run: Execute canary validation (sample_count, drift_threshold)

    Reference: PIN-520 Wiring Audit
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.hoc_spine.orchestrator.coordinators import CanaryCoordinator

        method_name = ctx.params.get("method", "run")

        if method_name == "run":
            coordinator = CanaryCoordinator()
            result = await coordinator.run(
                sample_count=ctx.params.get("sample_count", 100),
                drift_threshold=ctx.params.get("drift_threshold", 0.2),
            )
            return OperationResult.ok(result)

        else:
            return OperationResult.fail(
                f"Unknown canary method: {method_name}", "UNKNOWN_METHOD"
            )


# =============================================================================
# PIN-520: CostSim V2 Handlers (L2→L4 Migration)
# =============================================================================


class CostsimStatusHandler:
    """
    Handler for analytics.costsim.status operations.

    Returns V2 sandbox status including feature flags, circuit breaker state,
    model version, and drift thresholds.

    PIN-520 Phase 3: Migrates costsim.py /v2/status endpoint to L4.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.analytics.L5_engines.config_engine import (
            get_config,
            is_v2_disabled_by_drift,
            is_v2_sandbox_enabled,
        )
        from app.hoc.cus.controls.L6_drivers.circuit_breaker_async_driver import (
            get_circuit_breaker,
        )

        config = get_config()
        circuit_breaker = get_circuit_breaker()
        circuit_breaker_open = await circuit_breaker.is_disabled()

        return OperationResult.ok({
            "sandbox_enabled": is_v2_sandbox_enabled(),
            "circuit_breaker_open": circuit_breaker_open,
            "disabled_by_drift": is_v2_disabled_by_drift(),
            "model_version": config.model_version,
            "adapter_version": config.adapter_version,
            "drift_threshold": config.drift_threshold,
        })


class CostsimSimulateHandler:
    """
    Handler for analytics.costsim.simulate operations.

    Runs V2 simulation through sandbox. Always runs V1 for production results,
    optionally runs V2 in shadow mode for comparison.

    PIN-520 Phase 3: Migrates costsim.py /v2/simulate endpoint to L4.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.analytics.L5_engines.sandbox_engine import (
            simulate_with_sandbox,
        )

        plan = ctx.params.get("plan", [])
        budget_cents = ctx.params.get("budget_cents", 1000)
        run_id = ctx.params.get("run_id")

        if not plan:
            return OperationResult.fail("Missing 'plan' in params", "MISSING_PLAN")

        result = await simulate_with_sandbox(
            plan=plan,
            budget_cents=budget_cents,
            tenant_id=ctx.tenant_id,
            run_id=run_id,
        )

        # Convert result to dict for serialization
        return OperationResult.ok({
            "v1_result": {
                "feasible": result.v1_result.feasible,
                "estimated_cost_cents": result.v1_result.estimated_cost_cents,
                "estimated_duration_ms": result.v1_result.estimated_duration_ms,
            },
            "v2_result": result.v2_result.__dict__ if result.v2_result else None,
            "comparison": result.comparison.__dict__ if result.comparison else None,
            "sandbox_enabled": result.sandbox_enabled,
            "v2_error": result.v2_error,
        })


class CostsimDivergenceHandler:
    """
    Handler for analytics.costsim.divergence operations.

    Generates cost divergence report between V1 and V2.

    PIN-520 Phase 3: Migrates costsim.py /divergence endpoint to L4.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from datetime import datetime, timedelta, timezone

        from app.hoc.cus.analytics.L5_engines.divergence_engine import (
            generate_divergence_report,
        )

        start_date = ctx.params.get("start_date")
        end_date = ctx.params.get("end_date")
        days = ctx.params.get("days", 7)

        if end_date is None:
            end_date = datetime.now(timezone.utc)
        if start_date is None:
            start_date = end_date - timedelta(days=days)

        report = await generate_divergence_report(
            start_date=start_date,
            end_date=end_date,
            tenant_id=ctx.tenant_id if ctx.tenant_id != "system" else None,
        )

        return OperationResult.ok({
            "start_date": report.start_date.isoformat(),
            "end_date": report.end_date.isoformat(),
            "version": report.version,
            "sample_count": report.sample_count,
            "delta_p50": report.delta_p50,
            "delta_p90": report.delta_p90,
            "kl_divergence": report.kl_divergence,
            "outlier_count": report.outlier_count,
            "fail_ratio": report.fail_ratio,
            "matching_rate": report.matching_rate,
            "detailed_samples": report.detailed_samples,
        })


class CostsimDatasetsHandler:
    """
    Handler for analytics.costsim.datasets operations.

    Provides dataset validation capabilities:
      - list: List all reference datasets
      - info: Get dataset info by ID
      - validate: Validate against specific dataset
      - validate_all: Validate against all datasets

    PIN-520 Phase 3: Migrates costsim.py /datasets/* endpoints to L4.
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.analytics.L5_engines.datasets_engine import (
            get_dataset_validator,
            validate_all_datasets,
            validate_dataset,
        )

        method_name = ctx.params.get("method", "list")

        if method_name == "list":
            validator = get_dataset_validator()
            datasets = validator.list_datasets()
            return OperationResult.ok({"datasets": datasets})

        elif method_name == "info":
            dataset_id = ctx.params.get("dataset_id")
            if not dataset_id:
                return OperationResult.fail("Missing 'dataset_id'", "MISSING_DATASET_ID")
            validator = get_dataset_validator()
            dataset = validator.get_dataset(dataset_id)
            if not dataset:
                return OperationResult.fail(f"Dataset not found: {dataset_id}", "NOT_FOUND")
            return OperationResult.ok({
                "id": dataset.id,
                "name": dataset.name,
                "description": dataset.description,
                "sample_count": len(dataset.samples),
                "thresholds": dataset.validation_thresholds,
                "sample_tags": list(set(tag for sample in dataset.samples for tag in sample.tags)),
            })

        elif method_name == "validate":
            dataset_id = ctx.params.get("dataset_id")
            if not dataset_id:
                return OperationResult.fail("Missing 'dataset_id'", "MISSING_DATASET_ID")
            try:
                result = await validate_dataset(dataset_id)
            except ValueError as e:
                return OperationResult.fail(str(e), "NOT_FOUND")
            return OperationResult.ok({
                "dataset_id": result.dataset_id,
                "dataset_name": result.dataset_name,
                "sample_count": result.sample_count,
                "mean_error": result.mean_error,
                "median_error": result.median_error,
                "std_deviation": result.std_deviation,
                "outlier_pct": result.outlier_pct,
                "drift_score": result.drift_score,
                "verdict": result.verdict,
                "details": result.details,
                "timestamp": result.timestamp.isoformat(),
            })

        elif method_name == "validate_all":
            results = await validate_all_datasets()
            all_passed = all(r.verdict == "acceptable" for r in results.values())
            return OperationResult.ok({
                "all_passed": all_passed,
                "results": {
                    dataset_id: {
                        "dataset_name": result.dataset_name,
                        "sample_count": result.sample_count,
                        "mean_error": result.mean_error,
                        "drift_score": result.drift_score,
                        "verdict": result.verdict,
                    }
                    for dataset_id, result in results.items()
                },
            })

        else:
            return OperationResult.fail(
                f"Unknown datasets method: {method_name}", "UNKNOWN_METHOD"
            )


# =============================================================================
# UC-MON-06: Analytics Artifacts Reproducibility Handler
# =============================================================================

import logging
import uuid as _uuid

logger = logging.getLogger(__name__)


def _emit_analytics_event(
    event_type: str,
    tenant_id: str,
    dataset_id: str,
    extra: dict | None = None,
) -> None:
    """Emit a validated analytics domain event."""
    from app.hoc.cus.hoc_spine.authority.event_schema_contract import (
        CURRENT_SCHEMA_VERSION,
        validate_event_payload,
    )

    event = {
        "event_id": str(_uuid.uuid4()),
        "event_type": event_type,
        "tenant_id": tenant_id,
        "project_id": "__system__",
        "actor_type": "system",
        "actor_id": "analytics",
        "decision_owner": "analytics",
        "sequence_no": 0,
        "schema_version": CURRENT_SCHEMA_VERSION,
        "dataset_id": dataset_id,
    }
    if extra:
        event.update(extra)
    validate_event_payload(event)
    logger.info("analytics_event", extra=event)


class AnalyticsArtifactsHandler:
    """
    Handler for analytics.artifacts operations.

    Dispatches to AnalyticsArtifactsDriver for reproducibility persistence.
    Supports UC-MON-06 reproducibility contract (migration 131).

    Methods:
      - save: Persist analytics artifact metadata
      - get: Query artifacts by dataset_id
      - list: List all artifacts for tenant
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.analytics.L6_drivers.analytics_artifacts_driver import (
            AnalyticsArtifactsDriver,
        )

        method_name = ctx.params.get("method")
        if not method_name:
            return OperationResult.fail(
                "Missing 'method' in params", "MISSING_METHOD"
            )

        driver = AnalyticsArtifactsDriver()

        if method_name == "save":
            required = ["dataset_id", "dataset_version", "input_window_hash",
                        "as_of", "compute_code_version"]
            missing = [f for f in required if not ctx.params.get(f)]
            if missing:
                return OperationResult.fail(
                    f"Missing required fields: {', '.join(missing)}", "MISSING_FIELDS"
                )

            async with ctx.session.begin():
                data = await driver.save_artifact(
                    ctx.session,
                    tenant_id=ctx.tenant_id,
                    dataset_id=ctx.params["dataset_id"],
                    dataset_version=ctx.params["dataset_version"],
                    input_window_hash=ctx.params["input_window_hash"],
                    as_of=ctx.params["as_of"],
                    compute_code_version=ctx.params["compute_code_version"],
                )

            _emit_analytics_event(
                "analytics.ArtifactRecorded",
                ctx.tenant_id,
                ctx.params["dataset_id"],
                extra={
                    "dataset_version": ctx.params["dataset_version"],
                    "input_window_hash": ctx.params["input_window_hash"],
                    "as_of": ctx.params["as_of"],
                    "compute_code_version": ctx.params["compute_code_version"],
                },
            )

            return OperationResult.ok(data)

        elif method_name == "get":
            dataset_id = ctx.params.get("dataset_id")
            if not dataset_id:
                return OperationResult.fail(
                    "Missing 'dataset_id'", "MISSING_DATASET_ID"
                )
            data = await driver.get_artifact(
                ctx.session,
                tenant_id=ctx.tenant_id,
                dataset_id=dataset_id,
                dataset_version=ctx.params.get("dataset_version"),
            )
            return OperationResult.ok(data)

        elif method_name == "list":
            data = await driver.list_artifacts(
                ctx.session,
                tenant_id=ctx.tenant_id,
                limit=ctx.params.get("limit", 100),
            )
            return OperationResult.ok(data)

        return OperationResult.fail(
            f"Unknown artifacts method: {method_name}", "UNKNOWN_METHOD"
        )


def register(registry: OperationRegistry) -> None:
    """Register analytics operations with the registry."""
    registry.register("analytics.feedback", FeedbackReadHandler())
    registry.register("analytics.query", AnalyticsQueryHandler())
    registry.register("analytics.detection", AnalyticsDetectionHandler())
    registry.register("analytics.canary_reports", CanaryReportHandler())
    registry.register("analytics.canary", CanaryRunHandler())  # PIN-520: Scheduler integration
    # PIN-520 Phase 3: CostSim V2 handlers
    registry.register("analytics.costsim.status", CostsimStatusHandler())
    registry.register("analytics.costsim.simulate", CostsimSimulateHandler())
    registry.register("analytics.costsim.divergence", CostsimDivergenceHandler())
    registry.register("analytics.costsim.datasets", CostsimDatasetsHandler())
    # UC-MON-06: Analytics artifacts reproducibility
    registry.register("analytics.artifacts", AnalyticsArtifactsHandler())
