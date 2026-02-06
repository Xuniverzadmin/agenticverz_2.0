# Layer: L6 — Domain Driver
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: L4 handler dispatch
#   Execution: async
# Role: Data access for routing decisions and agent strategy operations
# Callers: agents_handler (L4)
# Allowed Imports: sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-484 (HOC Topology V2.0.0)
# artifact_class: CODE

"""
Routing Driver (L6)

Pure data access layer for routing decisions and agent strategy.
No business logic - only query construction and data retrieval.

Operations:
    - get_routing_stats: Aggregate stats from routing.routing_decisions
    - get_routing_decision: Single routing decision by request_id
    - update_agent_sba: Update agent SBA JSONB in agents.agent_registry
"""

import json
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class RoutingDriver:
    """
    L6 driver for routing and agent strategy DB operations.

    Pure data access - no business logic.
    Uses raw SQL for performance.
    """

    def __init__(self, session: AsyncSession):
        """Initialize driver with async session."""
        self._session = session

    async def get_routing_stats(
        self,
        tenant_id: str,
        hours: int = 24,
    ) -> Optional[Dict[str, Any]]:
        """
        Get aggregate routing statistics for a tenant.

        Args:
            tenant_id: Tenant ID for isolation
            hours: Lookback window in hours (default 24)

        Returns:
            Dict with stats or None if no data / table doesn't exist
        """
        try:
            result = await self._session.execute(
                text(
                    """
                    SELECT
                        COUNT(*) as total_decisions,
                        COUNT(*) FILTER (WHERE routed = true) as successful_routes,
                        AVG(total_latency_ms) as avg_latency_ms,
                        COUNT(DISTINCT selected_agent_id) as unique_agents,
                        MAX(decided_at) as last_decision
                    FROM routing.routing_decisions
                    WHERE tenant_id = :tenant_id
                    AND decided_at > now() - interval '1 hour' * :hours
                    """
                ),
                {"tenant_id": tenant_id, "hours": hours},
            )
            row = result.fetchone()

            if row:
                return {
                    "total_decisions": row[0] or 0,
                    "successful_routes": row[1] or 0,
                    "avg_latency_ms": row[2],
                    "unique_agents": row[3] or 0,
                    "last_decision": row[4],
                }
            return None
        except Exception:
            # Table might not exist yet
            return None

    async def get_routing_decision(
        self,
        request_id: str,
        tenant_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get a single routing decision by request_id.

        Args:
            request_id: The routing request ID
            tenant_id: Tenant ID for isolation

        Returns:
            Dict with decision data or None if not found
        """
        result = await self._session.execute(
            text(
                """
                SELECT
                    request_id, selected_agent_id, routed, decision_reason,
                    error, actionable_fix, total_latency_ms,
                    confidence_score, agent_reputation_at_route,
                    quarantine_state_at_route, decided_at
                FROM routing.routing_decisions
                WHERE request_id = :request_id
                AND tenant_id = :tenant_id
                """
            ),
            {"request_id": request_id, "tenant_id": tenant_id},
        )
        row = result.fetchone()

        if not row:
            return None

        return {
            "request_id": row[0],
            "selected_agent_id": row[1],
            "routed": row[2],
            "decision_reason": row[3],
            "error": row[4],
            "actionable_fix": row[5],
            "total_latency_ms": row[6],
            "confidence_score": row[7],
            "agent_reputation_at_route": row[8],
            "quarantine_state_at_route": row[9],
            "decided_at": row[10],
        }

    async def update_agent_sba(
        self,
        agent_id: str,
        sba: Dict[str, Any],
    ) -> bool:
        """
        Update an agent's SBA JSONB field.

        Args:
            agent_id: The agent ID
            sba: The updated SBA dictionary

        Returns:
            True if updated successfully
        """
        await self._session.execute(
            text(
                """
                UPDATE agents.agent_registry
                SET sba = CAST(:sba AS JSONB)
                WHERE agent_id = :agent_id
                """
            ),
            {"agent_id": agent_id, "sba": json.dumps(sba)},
        )
        # L6 does NOT commit — L4 handler owns transaction boundary
        return True


def get_routing_driver(session: AsyncSession) -> RoutingDriver:
    """
    Get RoutingDriver instance.

    Args:
        session: AsyncSession for database operations

    Returns:
        RoutingDriver instance
    """
    return RoutingDriver(session)


__all__ = [
    "RoutingDriver",
    "get_routing_driver",
]
