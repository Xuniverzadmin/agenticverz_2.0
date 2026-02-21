# capability_id: CAP-008
# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Product: founder-console
# Temporal:
#   Trigger: api (via L5 engine / L4 handler)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: discovery_ledger
#   Writes: none
# Database:
#   Scope: domain (agent)
#   Models: discovery_ledger (raw SQL — no ORM model)
# Role: Discovery stats data access — pure DB operations for stats queries
# Callers: agent_handler.py (L4)
# Allowed Imports: L7 (models), sqlalchemy
# Forbidden: session.commit() — L4 coordinator owns transaction boundary
# artifact_class: CODE

"""
Discovery Stats Driver (L6)

Pure data access layer for discovery statistics operations.
All methods accept a Session and return raw data.
No business logic — that belongs in L5.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlmodel import Session

logger = logging.getLogger("nova.hoc.agent.L6.discovery_stats_driver")


class DiscoveryStatsDriver:
    """Pure data access for discovery_ledger statistics."""

    def get_stats(self, session: Session) -> Dict[str, Any]:
        """
        Get discovery ledger statistics.
        
        Returns counts grouped by:
        - artifact (with count and total_seen)
        - signal_type (with count and total_seen)
        - status (with count)
        """
        by_artifact = self._get_by_artifact(session)
        by_signal_type = self._get_by_signal_type(session)
        by_status = self._get_by_status(session)

        return {
            "by_artifact": by_artifact,
            "by_signal_type": by_signal_type,
            "by_status": by_status,
        }

    def _get_by_artifact(self, session: Session) -> List[Dict[str, Any]]:
        """Get counts grouped by artifact."""
        result = session.execute(
            text(
                """
                SELECT artifact, COUNT(*) as count, SUM(seen_count) as total_seen
                FROM discovery_ledger
                GROUP BY artifact
                ORDER BY total_seen DESC
                """
            )
        ).fetchall()
        return [
            {"artifact": r.artifact, "count": r.count, "total_seen": r.total_seen}
            for r in result
        ]

    def _get_by_signal_type(self, session: Session) -> List[Dict[str, Any]]:
        """Get counts grouped by signal_type."""
        result = session.execute(
            text(
                """
                SELECT signal_type, COUNT(*) as count, SUM(seen_count) as total_seen
                FROM discovery_ledger
                GROUP BY signal_type
                ORDER BY total_seen DESC
                """
            )
        ).fetchall()
        return [
            {"signal_type": r.signal_type, "count": r.count, "total_seen": r.total_seen}
            for r in result
        ]

    def _get_by_status(self, session: Session) -> List[Dict[str, Any]]:
        """Get counts grouped by status."""
        result = session.execute(
            text(
                """
                SELECT status, COUNT(*) as count
                FROM discovery_ledger
                GROUP BY status
                """
            )
        ).fetchall()
        return [{"status": r.status, "count": r.count} for r in result]


_instance: Optional[DiscoveryStatsDriver] = None


def get_discovery_stats_driver() -> DiscoveryStatsDriver:
    """Get or create the singleton DiscoveryStatsDriver."""
    global _instance
    if _instance is None:
        _instance = DiscoveryStatsDriver()
    return _instance
