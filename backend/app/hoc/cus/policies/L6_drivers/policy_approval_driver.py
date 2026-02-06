# Layer: L6 — Data Access Driver
# AUDIENCE: INTERNAL
# Temporal:
#   Trigger: internal (via L4 handler)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: approval_requests, policy_approval_levels
#   Writes: approval_requests
# Role: Data access for policy approval workflow operations
# Callers: L4 policy_approval_handler
# Allowed Imports: L7 (models), sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-470, Goal B (session.execute elimination)
"""
Policy Approval Driver (L6)

Pure data access layer for policy approval workflow operations.
All SQLAlchemy queries live here. No business logic.

Extracted from hoc/api/cus/policies/policy.py to comply with
L2 purity requirements (no session.execute in L2).
"""

import json
import logging
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("nova.hoc.policies.L6.approval_driver")


class PolicyApprovalDriver:
    """Data access operations for policy approval workflow."""

    def __init__(self, session: AsyncSession):
        self._session = session

    # =========================================================================
    # Approval Level Config
    # =========================================================================

    async def get_approval_level_config(
        self,
        policy_type: str,
        tenant_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        skill_id: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Get approval level configuration from PolicyApprovalLevel table.

        Returns the most specific matching config, or None if no match.
        """
        result = await self._session.execute(
            sql_text(
                "SELECT policy_type, tenant_id, agent_id, skill_id, "
                "approval_level, auto_approve_max_cost_cents, "
                "auto_approve_max_tokens, escalate_to, escalation_timeout_seconds "
                "FROM policy_approval_levels "
                "WHERE policy_type = :policy_type"
            ),
            {"policy_type": policy_type},
        )
        configs = result.mappings().all()

        # Find best match (most specific first)
        for config in configs:
            if config["tenant_id"] == tenant_id:
                if config["agent_id"] == agent_id and config["skill_id"] == skill_id:
                    return self._config_to_dict(config)
            elif config["tenant_id"] is None:
                return self._config_to_dict(config)

        return None

    def _config_to_dict(self, config) -> dict[str, Any]:
        """Convert raw SQL row mapping to dict."""
        approval_level = config["approval_level"]
        return {
            "approval_level": (
                int(approval_level)
                if isinstance(approval_level, str) and approval_level.isdigit()
                else (approval_level if isinstance(approval_level, int) else 3)
            ),
            "auto_approve_max_cost_cents": config["auto_approve_max_cost_cents"] or 100,
            "auto_approve_max_tokens": config["auto_approve_max_tokens"] or 1000,
            "escalate_to": config["escalate_to"],
            "escalation_timeout_seconds": config["escalation_timeout_seconds"],
        }

    # =========================================================================
    # Approval Request CRUD
    # =========================================================================

    async def create_approval_request(
        self,
        *,
        approval_id: str,
        correlation_id: str,
        policy_type: str,
        skill_id: str,
        tenant_id: str,
        agent_id: Optional[str],
        requested_by: str,
        justification: Optional[str],
        payload_json: str,
        required_level: int,
        escalate_to: Optional[str],
        escalation_timeout_seconds: int,
        webhook_url: Optional[str],
        webhook_secret_hash: Optional[str],
        expires_at: datetime,
        now: datetime,
    ) -> None:
        """Create a new approval request."""
        await self._session.execute(
            sql_text(
                "INSERT INTO approval_requests "
                "(id, correlation_id, policy_type, skill_id, tenant_id, agent_id, "
                "requested_by, justification, payload_json, status, "
                "required_level, current_level, escalate_to, escalation_timeout_seconds, "
                "webhook_url, webhook_secret_hash, webhook_attempts, "
                "expires_at, created_at, updated_at) "
                "VALUES (:id, :correlation_id, :policy_type, :skill_id, :tenant_id, :agent_id, "
                ":requested_by, :justification, :payload_json, :status, "
                ":required_level, :current_level, :escalate_to, :escalation_timeout_seconds, "
                ":webhook_url, :webhook_secret_hash, :webhook_attempts, "
                ":expires_at, :created_at, :updated_at)"
            ),
            {
                "id": approval_id,
                "correlation_id": correlation_id,
                "policy_type": policy_type,
                "skill_id": skill_id,
                "tenant_id": tenant_id,
                "agent_id": agent_id,
                "requested_by": requested_by,
                "justification": justification,
                "payload_json": payload_json,
                "status": "pending",
                "required_level": required_level,
                "current_level": 0,
                "escalate_to": escalate_to,
                "escalation_timeout_seconds": escalation_timeout_seconds,
                "webhook_url": webhook_url,
                "webhook_secret_hash": webhook_secret_hash,
                "webhook_attempts": 0,
                "expires_at": expires_at,
                "created_at": now,
                "updated_at": now,
            },
        )

    async def get_approval_request(
        self,
        request_id: str,
    ) -> Optional[dict[str, Any]]:
        """Get approval request by ID."""
        result = await self._session.execute(
            sql_text(
                "SELECT id, correlation_id, policy_type, skill_id, tenant_id, agent_id, "
                "requested_by, justification, payload_json, status, status_history_json, "
                "required_level, current_level, approvals_json, escalate_to, "
                "webhook_attempts, last_webhook_status, "
                "expires_at, created_at, updated_at "
                "FROM approval_requests WHERE id = :request_id"
            ),
            {"request_id": request_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    async def get_approval_request_for_action(
        self,
        request_id: str,
    ) -> Optional[dict[str, Any]]:
        """Get approval request data needed for approve/reject actions."""
        result = await self._session.execute(
            sql_text(
                "SELECT id, status, tenant_id, required_level, current_level, "
                "approvals_json, status_history_json, expires_at, webhook_url, correlation_id "
                "FROM approval_requests WHERE id = :request_id"
            ),
            {"request_id": request_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    async def get_approval_request_for_reject(
        self,
        request_id: str,
    ) -> Optional[dict[str, Any]]:
        """Get approval request data needed for rejection."""
        result = await self._session.execute(
            sql_text(
                "SELECT id, status, tenant_id, approvals_json, status_history_json, webhook_url "
                "FROM approval_requests WHERE id = :request_id"
            ),
            {"request_id": request_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    async def update_approval_request_status(
        self,
        request_id: str,
        status: str,
        updated_at: datetime,
    ) -> None:
        """Update approval request status."""
        await self._session.execute(
            sql_text(
                "UPDATE approval_requests SET status = :status, updated_at = :updated_at "
                "WHERE id = :request_id"
            ),
            {"status": status, "updated_at": updated_at, "request_id": request_id},
        )

    async def update_approval_request_approved(
        self,
        request_id: str,
        approvals_json: str,
        current_level: int,
        status: str,
        status_history_json: str,
        updated_at: datetime,
        resolved_at: Optional[datetime],
    ) -> None:
        """Update approval request with approval action."""
        await self._session.execute(
            sql_text(
                "UPDATE approval_requests SET approvals_json = :approvals_json, "
                "current_level = :current_level, status = :status, "
                "status_history_json = :status_history_json, "
                "updated_at = :updated_at, resolved_at = :resolved_at "
                "WHERE id = :id"
            ),
            {
                "approvals_json": approvals_json,
                "current_level": current_level,
                "status": status,
                "status_history_json": status_history_json,
                "updated_at": updated_at,
                "resolved_at": resolved_at,
                "id": request_id,
            },
        )

    async def update_approval_request_escalated(
        self,
        request_id: str,
        status: str,
        status_history_json: str,
        updated_at: datetime,
    ) -> None:
        """Update approval request status to escalated."""
        await self._session.execute(
            sql_text(
                "UPDATE approval_requests SET status = :new_status, "
                "status_history_json = :history, updated_at = :updated_at "
                "WHERE id = :id"
            ),
            {
                "new_status": status,
                "history": status_history_json,
                "updated_at": updated_at,
                "id": request_id,
            },
        )

    async def list_approval_requests(
        self,
        *,
        status: Optional[str] = None,
        tenant_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List approval requests with optional filtering."""
        conditions = []
        params: dict[str, Any] = {"limit_val": limit, "offset_val": offset}

        if status:
            conditions.append("status = :status_val")
            params["status_val"] = status
        if tenant_id:
            conditions.append("tenant_id = :tenant_id_val")
            params["tenant_id_val"] = tenant_id

        where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""

        result = await self._session.execute(
            sql_text(
                "SELECT id, correlation_id, policy_type, skill_id, tenant_id, agent_id, "
                "requested_by, justification, payload_json, status, status_history_json, "
                "required_level, current_level, approvals_json, escalate_to, "
                "webhook_attempts, last_webhook_status, "
                "expires_at, created_at, updated_at "
                f"FROM approval_requests{where_clause} "
                "ORDER BY created_at DESC LIMIT :limit_val OFFSET :offset_val"
            ),
            params,
        )
        return [dict(row) for row in result.mappings().all()]

    async def list_pending_for_escalation(self) -> list[dict[str, Any]]:
        """List pending approval requests for escalation check."""
        result = await self._session.execute(
            sql_text(
                "SELECT id, status, status_history_json, escalation_timeout_seconds, "
                "escalate_to, webhook_url, correlation_id, created_at "
                "FROM approval_requests WHERE status = :status"
            ),
            {"status": "pending"},
        )
        return [dict(row) for row in result.mappings().all()]

    # =========================================================================
    # Policy Rules Queries (for V2 facade)
    # =========================================================================

    async def count_active_policy_rules(
        self,
        tenant_id: str,
        *,
        status: str = "ACTIVE",
        scope: Optional[str] = None,
        enforcement_mode: Optional[str] = None,
    ) -> int:
        """Count active policy rules with optional filters."""
        conditions = ["tenant_id = :tenant_id", "status = :status"]
        params: dict[str, Any] = {
            "tenant_id": tenant_id,
            "status": status,
        }

        if scope:
            conditions.append("scope = :scope")
            params["scope"] = scope
        if enforcement_mode:
            conditions.append("enforcement_mode = :enforcement_mode")
            params["enforcement_mode"] = enforcement_mode

        where_clause = " WHERE " + " AND ".join(conditions)

        count_result = await self._session.execute(
            sql_text(f"SELECT COUNT(*) FROM policy_rules{where_clause}"),
            params,
        )
        return count_result.scalar() or 0

    async def list_policy_rules(
        self,
        tenant_id: str,
        *,
        status: str = "ACTIVE",
        scope: Optional[str] = None,
        enforcement_mode: Optional[str] = None,
        rule_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        List policy rules with filters and pagination.

        Returns (items, total_count).
        """
        conditions = ["tenant_id = :tenant_id"]
        params: dict[str, Any] = {
            "tenant_id": tenant_id,
            "limit_val": limit,
            "offset_val": offset,
        }

        if status:
            conditions.append("status = :status")
            params["status"] = status
        if scope:
            conditions.append("scope = :scope")
            params["scope"] = scope
        if enforcement_mode:
            conditions.append("enforcement_mode = :enforcement_mode")
            params["enforcement_mode"] = enforcement_mode
        if rule_type:
            conditions.append("rule_type = :rule_type")
            params["rule_type"] = rule_type

        where_clause = " WHERE " + " AND ".join(conditions)

        # Count
        count_result = await self._session.execute(
            sql_text(f"SELECT COUNT(*) FROM policy_rules{where_clause}"),
            params,
        )
        total = count_result.scalar() or 0

        # Fetch
        result = await self._session.execute(
            sql_text(
                "SELECT id, name, status, enforcement_mode, scope, source, "
                "created_at, updated_at, rule_type "
                f"FROM policy_rules{where_clause} "
                "ORDER BY created_at DESC LIMIT :limit_val OFFSET :offset_val"
            ),
            params,
        )
        rows = [dict(row) for row in result.mappings().all()]

        return rows, total

    async def get_policy_rule_detail(
        self,
        policy_id: str,
        tenant_id: str,
    ) -> Optional[dict[str, Any]]:
        """Get policy rule detail with integrity info."""
        result = await self._session.execute(
            sql_text(
                "SELECT pr.id, pr.name, pr.description, pr.status, pr.enforcement_mode, "
                "pr.scope, pr.source, pr.rule_type, pr.rule_definition, "
                "pr.created_at, pr.updated_at, "
                "pri.integrity_status, pri.integrity_score "
                "FROM policy_rules pr "
                "LEFT JOIN policy_rule_integrity pri ON pri.rule_id = pr.id "
                "WHERE pr.id = :policy_id AND pr.tenant_id = :tenant_id"
            ),
            {"policy_id": policy_id, "tenant_id": tenant_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    # =========================================================================
    # Limits/Thresholds Queries (for V2 facade)
    # =========================================================================

    async def list_limits(
        self,
        tenant_id: str,
        *,
        status: str = "ACTIVE",
        limit_category: Optional[str] = None,
        scope: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        List limits/thresholds with filters and pagination.

        Returns (items, total_count).
        """
        conditions = ["tenant_id = :tenant_id", "status = :status"]
        params: dict[str, Any] = {
            "tenant_id": tenant_id,
            "status": status,
            "limit_val": limit,
            "offset_val": offset,
        }

        if limit_category:
            conditions.append("limit_category = :limit_category")
            params["limit_category"] = limit_category
        if scope:
            conditions.append("scope = :scope")
            params["scope"] = scope

        where_clause = " WHERE " + " AND ".join(conditions)

        # Count
        count_result = await self._session.execute(
            sql_text(f"SELECT COUNT(*) FROM limits{where_clause}"),
            params,
        )
        total = count_result.scalar() or 0

        # Fetch
        result = await self._session.execute(
            sql_text(
                "SELECT id, name, limit_category, limit_type, scope, enforcement, "
                "max_value, status, created_at, updated_at "
                f"FROM limits{where_clause} "
                "ORDER BY created_at DESC LIMIT :limit_val OFFSET :offset_val"
            ),
            params,
        )
        rows = [dict(row) for row in result.mappings().all()]

        return rows, total

    async def get_limit_detail(
        self,
        threshold_id: str,
        tenant_id: str,
    ) -> Optional[dict[str, Any]]:
        """Get limit/threshold detail with integrity info."""
        result = await self._session.execute(
            sql_text(
                "SELECT l.id, l.name, l.description, l.limit_category, l.limit_type, "
                "l.scope, l.enforcement, l.max_value, l.window_seconds, l.reset_period, "
                "l.status, l.created_at, l.updated_at, "
                "li.integrity_status, li.integrity_score "
                "FROM limits l "
                "LEFT JOIN limit_integrity li ON li.limit_id = l.id "
                "WHERE l.id = :threshold_id AND l.tenant_id = :tenant_id"
            ),
            {"threshold_id": threshold_id, "tenant_id": tenant_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None


def get_policy_approval_driver(session: AsyncSession) -> PolicyApprovalDriver:
    """Factory function for PolicyApprovalDriver."""
    return PolicyApprovalDriver(session)


__all__ = [
    "PolicyApprovalDriver",
    "get_policy_approval_driver",
]
