# capability_id: CAP-009
# Layer: L6 — Data Access Driver
# AUDIENCE: INTERNAL
# Temporal:
#   Trigger: engine
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: policy_rules, limits, policy_conflicts
#   Writes: none
# Role: Policy graph data access operations
# Callers: policy_graph_engine.py (L5 engine)
# Allowed Imports: L7 (models), sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-470, Phase-3B SQLAlchemy Extraction
#
# ============================================================================
# L6 DRIVER INVARIANT — POLICY GRAPH
# ============================================================================
# This driver handles PERSISTENCE only:
# - Query policy_rules for conflict/dependency analysis
# - Query limits for threshold analysis
# - Query resolved conflicts
#
# NO BUSINESS LOGIC. Conflict detection and dependency graph
# computation stay in L5 engine.
# ============================================================================

"""
Policy Graph Driver (L6 Data Access)

Handles database operations for policy graph computation:
- Fetching policies for conflict detection
- Fetching limits for threshold analysis
- Fetching resolved conflict pairs

Reference: PIN-470, Phase-3B SQLAlchemy Extraction
"""

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class PolicyGraphDriver:
    """
    L6 Driver for policy graph data operations.

    All methods are pure DB operations - no business logic.
    Business decisions (conflict detection, graph computation) stay in L5.
    """

    def __init__(self, session: AsyncSession):
        """Initialize driver with async session."""
        self._session = session

    async def fetch_active_policies(self, tenant_id: str) -> list[dict[str, Any]]:
        """
        Fetch all active policies for a tenant.

        Used by PolicyConflictEngine for conflict detection.

        Args:
            tenant_id: Tenant identifier

        Returns:
            List of policy dicts with id, name, rule_type, scope, etc.
        """
        result = await self._session.execute(
            text("""
                SELECT id, name, rule_type, scope, scope_id, enforcement_mode,
                       conditions, source, status
                FROM policy_rules
                WHERE tenant_id = :tenant_id AND status = 'ACTIVE'
                ORDER BY created_at DESC
            """),
            {"tenant_id": tenant_id},
        )
        rows = result.fetchall()
        return [
            {
                "id": str(row[0]),
                "name": row[1],
                "rule_type": row[2] or "SYSTEM",
                "scope": row[3] or "GLOBAL",
                "scope_id": row[4],
                "enforcement_mode": row[5] or "WARN",
                "conditions": row[6] or {},
                "source": row[7] or "MANUAL",
                "status": row[8] or "ACTIVE",
            }
            for row in rows
        ]

    async def fetch_all_policies(self, tenant_id: str) -> list[dict[str, Any]]:
        """
        Fetch all policies for a tenant (including inactive).

        Used by PolicyDependencyEngine for dependency graph.

        Args:
            tenant_id: Tenant identifier

        Returns:
            List of policy dicts with id, name, rule_type, scope, parent_rule_id, etc.
        """
        result = await self._session.execute(
            text("""
                SELECT id, name, rule_type, scope, scope_id, enforcement_mode,
                       conditions, source, status, parent_rule_id
                FROM policy_rules
                WHERE tenant_id = :tenant_id
                ORDER BY created_at DESC
            """),
            {"tenant_id": tenant_id},
        )
        rows = result.fetchall()
        return [
            {
                "id": str(row[0]),
                "name": row[1],
                "rule_type": row[2] or "SYSTEM",
                "scope": row[3] or "GLOBAL",
                "scope_id": row[4],
                "enforcement_mode": row[5] or "WARN",
                "conditions": row[6] or {},
                "source": row[7] or "MANUAL",
                "status": row[8] or "ACTIVE",
                "parent_rule_id": str(row[9]) if row[9] else None,
            }
            for row in rows
        ]

    async def fetch_active_limits(self, tenant_id: str) -> list[dict[str, Any]]:
        """
        Fetch all active limits for a tenant.

        Used by PolicyConflictEngine for threshold contradiction detection.

        Args:
            tenant_id: Tenant identifier

        Returns:
            List of limit dicts
        """
        result = await self._session.execute(
            text("""
                SELECT id, name, limit_type, limit_value, scope, scope_id
                FROM limits
                WHERE tenant_id = :tenant_id AND status = 'ACTIVE'
                ORDER BY limit_type, scope
            """),
            {"tenant_id": tenant_id},
        )
        rows = result.fetchall()
        return [
            {
                "id": str(row[0]),
                "name": row[1],
                "limit_type": row[2],
                "limit_value": row[3],
                "scope": row[4],
                "scope_id": row[5],
            }
            for row in rows
        ]

    async def fetch_all_limits(self, tenant_id: str) -> list[dict[str, Any]]:
        """
        Fetch all limits for a tenant (including inactive).

        Used by PolicyDependencyEngine for limit dependency detection.

        Args:
            tenant_id: Tenant identifier

        Returns:
            List of limit dicts with status
        """
        result = await self._session.execute(
            text("""
                SELECT id, name, limit_type, limit_value, scope, scope_id, status
                FROM limits
                WHERE tenant_id = :tenant_id
                ORDER BY limit_type
            """),
            {"tenant_id": tenant_id},
        )
        rows = result.fetchall()
        return [
            {
                "id": str(row[0]),
                "name": row[1],
                "limit_type": row[2],
                "limit_value": row[3],
                "scope": row[4],
                "scope_id": row[5],
                "status": row[6],
            }
            for row in rows
        ]

    async def fetch_resolved_conflicts(self) -> set[tuple[str, str]]:
        """
        Get set of resolved conflict pairs.

        Returns:
            Set of (policy_a, policy_b) tuples that have been resolved
        """
        try:
            result = await self._session.execute(
                text("""
                    SELECT policy_a, policy_b FROM policy.policy_conflicts
                    WHERE resolved = true
                """)
            )
            return {(str(row[0]), str(row[1])) for row in result.fetchall()}
        except Exception:
            return set()


def get_policy_graph_driver(session: AsyncSession) -> PolicyGraphDriver:
    """Get a PolicyGraphDriver instance."""
    return PolicyGraphDriver(session)
