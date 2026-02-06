# Layer: L4 — HOC Spine (Handler)
# AUDIENCE: INTERNAL
# Temporal:
#   Trigger: api (via L4 orchestrator dispatch)
#   Execution: async
# Lifecycle:
#   Emits: operation audit records
#   Subscribes: none
# Data Access:
#   Reads: via L5 engine → L6 driver
#   Writes: via L5 engine → L6 driver
# Role: L4 handler for trace mismatch operations
# Callers: L2 traces.py (via operation registry)
# Allowed Imports: hoc_spine (operation_registry), L5_engines
# Forbidden Imports: L1, L2, L6, sqlalchemy
# Reference: PIN-491, L2 first-principles purity migration
# artifact_class: CODE

"""
Traces Handler (L4 Orchestrator)

Wraps L5 trace_mismatch_engine calls in OperationHandler protocol.

Operations registered:
- traces.list_mismatches: List all mismatches with filters
- traces.list_trace_mismatches: List mismatches for a specific trace
- traces.report_mismatch: Report a new mismatch
- traces.resolve_mismatch: Mark a mismatch as resolved
- traces.bulk_report_mismatches: Create bulk GitHub issue
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationHandler,
    OperationResult,
    get_operation_registry,
)

logger = logging.getLogger("nova.hoc_spine.handlers.traces_handler")


# =============================================================================
# List All Mismatches Handler
# =============================================================================


class ListAllMismatchesHandler:
    """
    Handler for listing all mismatches.

    Params:
        window: Optional[str] - Time window (e.g., "24h", "7d")
        status: Optional[str] - Filter by status ("open" or "resolved")
        limit: int - Max results (default 100)
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.logs.L5_engines.trace_mismatch_engine import (
            get_trace_mismatch_engine,
        )
        from app.hoc.cus.logs.L6_drivers.trace_mismatch_driver import (
            get_trace_mismatch_driver,
        )

        try:
            if ctx.session is None:
                return OperationResult.fail("Session required", "SESSION_REQUIRED")
            driver = get_trace_mismatch_driver(ctx.session)
            engine = get_trace_mismatch_engine(driver)
            result = await engine.list_all_mismatches(
                window=ctx.params.get("window"),
                status=ctx.params.get("status"),
                limit=ctx.params.get("limit", 100),
            )
            return OperationResult.ok(result)
        except Exception as e:
            logger.error(
                "traces.list_mismatches failed",
                extra={"error": str(e), "tenant_id": ctx.tenant_id},
                exc_info=True,
            )
            return OperationResult.fail(str(e), "LIST_MISMATCHES_ERROR")


# =============================================================================
# List Trace Mismatches Handler
# =============================================================================


class ListTraceMismatchesHandler:
    """
    Handler for listing mismatches for a specific trace.

    Params:
        trace_id: str - Trace ID to list mismatches for
        is_admin: bool - Whether caller has admin role
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.logs.L5_engines.trace_mismatch_engine import (
            get_trace_mismatch_engine,
        )
        from app.hoc.cus.logs.L6_drivers.trace_mismatch_driver import (
            get_trace_mismatch_driver,
        )

        try:
            if ctx.session is None:
                return OperationResult.fail("Session required", "SESSION_REQUIRED")
            driver = get_trace_mismatch_driver(ctx.session)
            engine = get_trace_mismatch_engine(driver)
            result = await engine.list_trace_mismatches(
                trace_id=ctx.params["trace_id"],
                tenant_id=ctx.tenant_id,
                is_admin=ctx.params.get("is_admin", False),
            )
            return OperationResult.ok(result)
        except ValueError as e:
            return OperationResult.fail(str(e), "TRACE_NOT_FOUND")
        except PermissionError as e:
            return OperationResult.fail(str(e), "ACCESS_DENIED")
        except Exception as e:
            logger.error(
                "traces.list_trace_mismatches failed",
                extra={"error": str(e), "tenant_id": ctx.tenant_id},
                exc_info=True,
            )
            return OperationResult.fail(str(e), "LIST_TRACE_MISMATCHES_ERROR")


# =============================================================================
# Report Mismatch Handler
# =============================================================================


class ReportMismatchHandler:
    """
    Handler for reporting a mismatch.

    Params:
        trace_id: str - Trace ID
        step_index: int - Step index
        reason: str - Reason for mismatch
        expected_hash: Optional[str] - Expected hash
        actual_hash: Optional[str] - Actual hash
        details: dict - Additional details
        user_id: str - User reporting
        is_admin: bool - Whether caller has admin role
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.logs.L5_engines.trace_mismatch_engine import (
            MismatchReportInput,
            get_trace_mismatch_engine,
        )
        from app.hoc.cus.logs.L6_drivers.trace_mismatch_driver import (
            get_trace_mismatch_driver,
        )

        try:
            input_data = MismatchReportInput(
                trace_id=ctx.params["trace_id"],
                step_index=ctx.params["step_index"],
                reason=ctx.params["reason"],
                expected_hash=ctx.params.get("expected_hash"),
                actual_hash=ctx.params.get("actual_hash"),
                details=ctx.params.get("details", {}),
            )

            if ctx.session is None:
                return OperationResult.fail("Session required", "SESSION_REQUIRED")
            driver = get_trace_mismatch_driver(ctx.session)
            engine = get_trace_mismatch_engine(driver)
            result = await engine.report_mismatch(
                input_data=input_data,
                tenant_id=ctx.tenant_id,
                user_id=ctx.params["user_id"],
                is_admin=ctx.params.get("is_admin", False),
            )
            return OperationResult.ok(result)
        except ValueError as e:
            return OperationResult.fail(str(e), "TRACE_NOT_FOUND")
        except PermissionError as e:
            return OperationResult.fail(str(e), "ACCESS_DENIED")
        except Exception as e:
            logger.error(
                "traces.report_mismatch failed",
                extra={"error": str(e), "tenant_id": ctx.tenant_id},
                exc_info=True,
            )
            return OperationResult.fail(str(e), "REPORT_MISMATCH_ERROR")


# =============================================================================
# Resolve Mismatch Handler
# =============================================================================


class ResolveMismatchHandler:
    """
    Handler for resolving a mismatch.

    Params:
        trace_id: str - Trace ID
        mismatch_id: str - Mismatch ID
        user_id: str - User resolving
        resolution_note: Optional[str] - Resolution note
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.logs.L5_engines.trace_mismatch_engine import (
            get_trace_mismatch_engine,
        )
        from app.hoc.cus.logs.L6_drivers.trace_mismatch_driver import (
            get_trace_mismatch_driver,
        )

        try:
            if ctx.session is None:
                return OperationResult.fail("Session required", "SESSION_REQUIRED")
            driver = get_trace_mismatch_driver(ctx.session)
            engine = get_trace_mismatch_engine(driver)
            result = await engine.resolve_mismatch(
                trace_id=ctx.params["trace_id"],
                mismatch_id=ctx.params["mismatch_id"],
                user_id=ctx.params["user_id"],
                resolution_note=ctx.params.get("resolution_note"),
            )
            # L4 owns transaction boundary
            await ctx.session.commit()
            return OperationResult.ok(result)
        except ValueError as e:
            return OperationResult.fail(str(e), "MISMATCH_NOT_FOUND")
        except Exception as e:
            logger.error(
                "traces.resolve_mismatch failed",
                extra={"error": str(e), "tenant_id": ctx.tenant_id},
                exc_info=True,
            )
            return OperationResult.fail(str(e), "RESOLVE_MISMATCH_ERROR")


# =============================================================================
# Bulk Report Mismatches Handler
# =============================================================================


class BulkReportMismatchesHandler:
    """
    Handler for bulk reporting mismatches.

    Params:
        mismatch_ids: list[str] - List of mismatch IDs
        user_id: str - User creating the bulk report
        github_issue: bool - Whether to create GitHub issue (default True)
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.logs.L5_engines.trace_mismatch_engine import (
            get_trace_mismatch_engine,
        )
        from app.hoc.cus.logs.L6_drivers.trace_mismatch_driver import (
            get_trace_mismatch_driver,
        )

        try:
            if ctx.session is None:
                return OperationResult.fail("Session required", "SESSION_REQUIRED")
            driver = get_trace_mismatch_driver(ctx.session)
            engine = get_trace_mismatch_engine(driver)
            result = await engine.bulk_report_mismatches(
                mismatch_ids=ctx.params["mismatch_ids"],
                user_id=ctx.params["user_id"],
                github_issue=ctx.params.get("github_issue", True),
            )
            # L4 owns transaction boundary
            await ctx.session.commit()
            return OperationResult.ok(result)
        except ValueError as e:
            return OperationResult.fail(str(e), "NO_MISMATCHES_FOUND")
        except Exception as e:
            logger.error(
                "traces.bulk_report_mismatches failed",
                extra={"error": str(e), "tenant_id": ctx.tenant_id},
                exc_info=True,
            )
            return OperationResult.fail(str(e), "BULK_REPORT_ERROR")


# =============================================================================
# Verify Trace Tenant Handler
# =============================================================================


class VerifyTraceTenantHandler:
    """
    Handler for verifying trace tenant ownership.

    Params:
        trace_id: str - Trace ID to verify
        is_admin: bool - Whether caller has admin role

    Returns:
        trace_tenant: str - Tenant ID of the trace (if found)
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.logs.L6_drivers.trace_mismatch_driver import (
            get_trace_mismatch_driver,
        )

        try:
            driver = get_trace_mismatch_driver(ctx.session)
            trace_tenant = await driver.fetch_trace_tenant(ctx.params["trace_id"])

            if trace_tenant is None:
                return OperationResult.fail(
                    f"Trace {ctx.params['trace_id']} not found",
                    "TRACE_NOT_FOUND",
                )

            # Check tenant access
            is_admin = ctx.params.get("is_admin", False)
            if trace_tenant != ctx.tenant_id and not is_admin:
                return OperationResult.fail("Access denied", "ACCESS_DENIED")

            return OperationResult.ok({"trace_tenant": trace_tenant})
        except Exception as e:
            logger.error(
                "traces.verify_tenant failed",
                extra={"error": str(e), "tenant_id": ctx.tenant_id},
                exc_info=True,
            )
            return OperationResult.fail(str(e), "VERIFY_TENANT_ERROR")


# =============================================================================
# Registration
# =============================================================================


def register_traces_handlers() -> None:
    """
    Register all trace mismatch handlers with the operation registry.

    Call this once at startup.
    """
    registry = get_operation_registry()

    registry.register("traces.list_mismatches", ListAllMismatchesHandler())
    registry.register("traces.list_trace_mismatches", ListTraceMismatchesHandler())
    registry.register("traces.report_mismatch", ReportMismatchHandler())
    registry.register("traces.resolve_mismatch", ResolveMismatchHandler())
    registry.register("traces.bulk_report_mismatches", BulkReportMismatchesHandler())
    registry.register("traces.verify_tenant", VerifyTraceTenantHandler())

    logger.info("Trace mismatch handlers registered with operation registry")
