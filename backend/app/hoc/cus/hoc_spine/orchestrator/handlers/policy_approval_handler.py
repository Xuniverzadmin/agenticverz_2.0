# capability_id: CAP-012
# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Role: L4 handler — policy approval workflow operations
# Callers: L2 API (hoc/api/cus/policies/policy.py)
# Allowed Imports: hoc_spine, hoc.cus.policies.L6_drivers (lazy)
# Forbidden Imports: L1, L2
# Reference: PIN-513, Goal B (session.execute elimination)
# artifact_class: CODE

"""
Policy Approval Handler (L4)

L4 handler that routes policy approval operations to L6 drivers.
This handler enables L2 to use registry.execute() instead of session.execute().

Wires from policies/L6_drivers/policy_approval_driver.py:
- get_policy_approval_driver(session)

Flow:
  L2 API
    → PolicyApprovalHandler.<method>(ctx)
        → L6 driver call
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationHandler,
    OperationResult,
)

logger = logging.getLogger("nova.hoc_spine.handlers.policy_approval")


class PolicyApprovalHandler(OperationHandler):
    """L4 handler: policy approval workflow operations.

    Dispatches to L6 PolicyApprovalDriver based on ctx.params["method"].
    """

    async def execute(self, ctx: OperationContext) -> OperationResult:
        """Execute the requested approval operation."""
        from app.hoc.cus.policies.L6_drivers.policy_approval_driver import (
            get_policy_approval_driver,
        )

        method = ctx.params.get("method", "")
        driver = get_policy_approval_driver(ctx.session)

        try:
            # Route to appropriate method
            if method == "get_approval_level_config":
                return await self._get_approval_level_config(driver, ctx)
            elif method == "create_approval_request":
                return await self._create_approval_request(driver, ctx)
            elif method == "get_approval_request":
                return await self._get_approval_request(driver, ctx)
            elif method == "get_approval_request_for_action":
                return await self._get_approval_request_for_action(driver, ctx)
            elif method == "get_approval_request_for_reject":
                return await self._get_approval_request_for_reject(driver, ctx)
            elif method == "update_approval_request_status":
                return await self._update_approval_request_status(driver, ctx)
            elif method == "update_approval_request_approved":
                return await self._update_approval_request_approved(driver, ctx)
            elif method == "update_approval_request_escalated":
                return await self._update_approval_request_escalated(driver, ctx)
            elif method == "list_approval_requests":
                return await self._list_approval_requests(driver, ctx)
            elif method == "list_pending_for_escalation":
                return await self._list_pending_for_escalation(driver, ctx)
            elif method == "batch_update_expired":
                return await self._batch_update_expired(driver, ctx)
            elif method == "batch_escalate":
                return await self._batch_escalate(driver, ctx)
            elif method == "list_policy_rules":
                return await self._list_policy_rules(driver, ctx)
            elif method == "get_policy_rule_detail":
                return await self._get_policy_rule_detail(driver, ctx)
            elif method == "list_limits":
                return await self._list_limits(driver, ctx)
            elif method == "get_limit_detail":
                return await self._get_limit_detail(driver, ctx)
            elif method == "review_proposal":
                return await self._review_proposal(ctx)
            else:
                return OperationResult.fail(
                    f"Unknown method: {method}",
                    error_code="UNKNOWN_METHOD",
                )
        except Exception as e:
            logger.exception(f"Policy approval operation failed: {method}")
            return OperationResult.fail(str(e), error_code="OPERATION_FAILED")

    # =========================================================================
    # Approval Level Config
    # =========================================================================

    async def _get_approval_level_config(
        self,
        driver,
        ctx: OperationContext,
    ) -> OperationResult:
        """Get approval level configuration."""
        config = await driver.get_approval_level_config(
            policy_type=ctx.params["policy_type"],
            tenant_id=ctx.params.get("tenant_id"),
            agent_id=ctx.params.get("agent_id"),
            skill_id=ctx.params.get("skill_id"),
        )

        # Return default config if none found
        if config is None:
            config = {
                "approval_level": 3,
                "auto_approve_max_cost_cents": 100,
                "auto_approve_max_tokens": 1000,
                "escalate_to": None,
                "escalation_timeout_seconds": 300,
            }

        return OperationResult.ok(config)

    # =========================================================================
    # Approval Request CRUD
    # =========================================================================

    async def _create_approval_request(
        self,
        driver,
        ctx: OperationContext,
    ) -> OperationResult:
        """Create a new approval request.

        L4 owns transaction boundary: commits after successful driver write.
        """
        await driver.create_approval_request(
            approval_id=ctx.params["approval_id"],
            correlation_id=ctx.params["correlation_id"],
            policy_type=ctx.params["policy_type"],
            skill_id=ctx.params["skill_id"],
            tenant_id=ctx.params["tenant_id"],
            agent_id=ctx.params.get("agent_id"),
            requested_by=ctx.params["requested_by"],
            justification=ctx.params.get("justification"),
            payload_json=ctx.params["payload_json"],
            required_level=ctx.params["required_level"],
            escalate_to=ctx.params.get("escalate_to"),
            escalation_timeout_seconds=ctx.params.get("escalation_timeout_seconds", 300),
            webhook_url=ctx.params.get("webhook_url"),
            webhook_secret_hash=ctx.params.get("webhook_secret_hash"),
            expires_at=ctx.params["expires_at"],
            now=ctx.params["now"],
        )
        # L4 transaction boundary: commit after successful write
        await ctx.session.commit()
        return OperationResult.ok({"created": True})

    async def _get_approval_request(
        self,
        driver,
        ctx: OperationContext,
    ) -> OperationResult:
        """Get approval request by ID."""
        row = await driver.get_approval_request(
            request_id=ctx.params["request_id"],
        )
        return OperationResult.ok(row)

    async def _get_approval_request_for_action(
        self,
        driver,
        ctx: OperationContext,
    ) -> OperationResult:
        """Get approval request data for approve action."""
        row = await driver.get_approval_request_for_action(
            request_id=ctx.params["request_id"],
        )
        return OperationResult.ok(row)

    async def _get_approval_request_for_reject(
        self,
        driver,
        ctx: OperationContext,
    ) -> OperationResult:
        """Get approval request data for reject action."""
        row = await driver.get_approval_request_for_reject(
            request_id=ctx.params["request_id"],
        )
        return OperationResult.ok(row)

    async def _update_approval_request_status(
        self,
        driver,
        ctx: OperationContext,
    ) -> OperationResult:
        """Update approval request status.

        L4 owns transaction boundary: commits after successful driver write.
        """
        await driver.update_approval_request_status(
            request_id=ctx.params["request_id"],
            status=ctx.params["status"],
            updated_at=ctx.params["updated_at"],
        )
        # L4 transaction boundary: commit after successful write
        await ctx.session.commit()
        return OperationResult.ok({"updated": True})

    async def _update_approval_request_approved(
        self,
        driver,
        ctx: OperationContext,
    ) -> OperationResult:
        """Update approval request with approval action.

        L4 owns transaction boundary: commits after successful driver write.
        """
        await driver.update_approval_request_approved(
            request_id=ctx.params["request_id"],
            approvals_json=ctx.params["approvals_json"],
            current_level=ctx.params["current_level"],
            status=ctx.params["status"],
            status_history_json=ctx.params["status_history_json"],
            updated_at=ctx.params["updated_at"],
            resolved_at=ctx.params.get("resolved_at"),
        )
        # L4 transaction boundary: commit after successful write
        await ctx.session.commit()
        return OperationResult.ok({"updated": True})

    async def _update_approval_request_escalated(
        self,
        driver,
        ctx: OperationContext,
    ) -> OperationResult:
        """Update approval request to escalated status.

        L4 owns transaction boundary: commits after successful driver write.
        """
        await driver.update_approval_request_escalated(
            request_id=ctx.params["request_id"],
            status=ctx.params["status"],
            status_history_json=ctx.params["status_history_json"],
            updated_at=ctx.params["updated_at"],
        )
        # L4 transaction boundary: commit after successful write
        await ctx.session.commit()
        return OperationResult.ok({"updated": True})

    async def _list_approval_requests(
        self,
        driver,
        ctx: OperationContext,
    ) -> OperationResult:
        """List approval requests with optional filtering."""
        rows = await driver.list_approval_requests(
            status=ctx.params.get("status"),
            tenant_id=ctx.params.get("tenant_id"),
            limit=ctx.params.get("limit", 50),
            offset=ctx.params.get("offset", 0),
        )
        return OperationResult.ok(rows)

    async def _list_pending_for_escalation(
        self,
        driver,
        ctx: OperationContext,
    ) -> OperationResult:
        """List pending approval requests for escalation check."""
        rows = await driver.list_pending_for_escalation()
        return OperationResult.ok(rows)

    async def _batch_update_expired(
        self,
        driver,
        ctx: OperationContext,
    ) -> OperationResult:
        """Batch update expired approval requests.

        L4 owns transaction boundary: commits after all updates.
        Called by L2 list_approval_requests when expired records found.
        """
        expired_ids = ctx.params.get("expired_ids", [])
        updated_at = ctx.params["updated_at"]

        for eid in expired_ids:
            await driver.update_approval_request_status(
                request_id=eid,
                status="expired",
                updated_at=updated_at,
            )

        # L4 transaction boundary: single commit after all writes
        if expired_ids:
            await ctx.session.commit()

        return OperationResult.ok({"updated_count": len(expired_ids)})

    async def _batch_escalate(
        self,
        driver,
        ctx: OperationContext,
    ) -> OperationResult:
        """Batch escalate approval requests.

        L4 owns transaction boundary: commits after all escalations.
        Called by L2 run_escalation_check.
        """
        escalations = ctx.params.get("escalations", [])
        updated_at = ctx.params["updated_at"]

        for esc in escalations:
            await driver.update_approval_request_escalated(
                request_id=esc["request_id"],
                status="escalated",
                status_history_json=esc["status_history_json"],
                updated_at=updated_at,
            )

        # L4 transaction boundary: single commit after all writes
        if escalations:
            await ctx.session.commit()

        return OperationResult.ok({"escalated_count": len(escalations)})

    # =========================================================================
    # Policy Rules Queries (for V2 facade)
    # =========================================================================

    async def _list_policy_rules(
        self,
        driver,
        ctx: OperationContext,
    ) -> OperationResult:
        """List policy rules with filters and pagination."""
        rows, total = await driver.list_policy_rules(
            tenant_id=ctx.tenant_id,
            status=ctx.params.get("status", "ACTIVE"),
            scope=ctx.params.get("scope"),
            enforcement_mode=ctx.params.get("enforcement_mode"),
            rule_type=ctx.params.get("rule_type"),
            limit=ctx.params.get("limit", 50),
            offset=ctx.params.get("offset", 0),
        )
        return OperationResult.ok({"items": rows, "total": total})

    async def _get_policy_rule_detail(
        self,
        driver,
        ctx: OperationContext,
    ) -> OperationResult:
        """Get policy rule detail."""
        row = await driver.get_policy_rule_detail(
            policy_id=ctx.params["policy_id"],
            tenant_id=ctx.tenant_id,
        )
        return OperationResult.ok(row)

    # =========================================================================
    # Limits/Thresholds Queries (for V2 facade)
    # =========================================================================

    async def _list_limits(
        self,
        driver,
        ctx: OperationContext,
    ) -> OperationResult:
        """List limits with filters and pagination."""
        rows, total = await driver.list_limits(
            tenant_id=ctx.tenant_id,
            status=ctx.params.get("status", "ACTIVE"),
            limit_category=ctx.params.get("limit_category"),
            scope=ctx.params.get("scope"),
            limit=ctx.params.get("limit", 50),
            offset=ctx.params.get("offset", 0),
        )
        return OperationResult.ok({"items": rows, "total": total})

    async def _get_limit_detail(
        self,
        driver,
        ctx: OperationContext,
    ) -> OperationResult:
        """Get limit/threshold detail."""
        row = await driver.get_limit_detail(
            threshold_id=ctx.params["threshold_id"],
            tenant_id=ctx.tenant_id,
        )
        return OperationResult.ok(row)

    # =========================================================================
    # Policy Proposals Review (for policy_proposals.py)
    # =========================================================================

    async def _review_proposal(
        self,
        ctx: OperationContext,
    ) -> OperationResult:
        """Review (approve/reject) a policy proposal.

        L4 owns transaction boundary: commits after successful review.
        Routes to L5 policy_proposal_engine.review_policy_proposal.
        L4 owns the commit to maintain transaction boundary purity.
        """
        from uuid import UUID
        from app.models.policy import PolicyApprovalRequest
        from app.hoc.cus.policies.L5_engines.policy_proposal_engine import review_policy_proposal

        proposal_id = UUID(ctx.params["proposal_id"])
        approval_request = PolicyApprovalRequest(
            action=ctx.params["action"],
            reviewed_by=ctx.params["reviewed_by"],
            review_notes=ctx.params.get("review_notes"),
        )

        # L5 engine performs the review
        updated_proposal = await review_policy_proposal(
            ctx.session, proposal_id, approval_request
        )

        # L4 transaction boundary: commit after successful write
        await ctx.session.commit()

        return OperationResult.ok({
            "id": str(updated_proposal.id),
            "status": updated_proposal.status,
            "reviewed_by": updated_proposal.reviewed_by,
            "reviewed_at": updated_proposal.reviewed_at.isoformat() if updated_proposal.reviewed_at else None,
        })


def get_policy_approval_handler() -> PolicyApprovalHandler:
    """Factory function for PolicyApprovalHandler."""
    return PolicyApprovalHandler()


__all__ = [
    "PolicyApprovalHandler",
    "get_policy_approval_handler",
]
