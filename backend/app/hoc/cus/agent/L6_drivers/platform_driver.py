# Layer: L6 — Driver
# AUDIENCE: FOUNDER
# Product: founder-console (fops.agenticverz.com)
# Temporal:
#   Trigger: L4 handler dispatch
#   Execution: sync
# Role: Data access for platform health and governance queries
# Callers: agent_handler (L4)
# Allowed Imports: ORM models, sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-284 (Platform Monitoring System)
# artifact_class: CODE

"""
Platform Driver (L6)

Pure data access layer for platform health and capability queries.
No business logic - only query construction and data retrieval.

Operations:
    - get_blca_status: Query BLCA governance status
    - get_lifecycle_coherence: Query lifecycle qualifier coherence
    - get_blocked_scopes: Query all blocked scopes
    - get_capability_signals: Query signals for a specific capability
    - count_blocked_for_capability: Count blocking signals for a capability

All methods use raw SQL via sqlalchemy text() for performance.
"""

from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import text
from sqlmodel import Session

from app.db import get_session


class PlatformDriver:
    """
    L6 driver for platform health queries.

    Pure data access - no business logic.
    Uses raw SQL for lightweight, efficient queries.
    """

    def __init__(self, session: Optional[Session] = None):
        """Initialize driver with optional session (lazy loaded)."""
        self._session = session

    def _get_session(self) -> Session:
        """Get the database session (lazy loaded)."""
        if self._session is None:
            self._session = next(get_session())
        return self._session

    def get_blca_status(self) -> Optional[str]:
        """
        Get the current BLCA status from governance signals.

        Returns:
            Decision string (e.g., "CLEAN", "BLOCKED", "WARN") or None if not found.
        """
        session = self._get_session()
        result = session.execute(
            text("""
                SELECT decision FROM governance_signals
                WHERE signal_type = 'BLCA_STATUS'
                AND scope = 'SYSTEM'
                AND superseded_at IS NULL
                ORDER BY recorded_at DESC
                LIMIT 1
            """)
        ).fetchone()
        return result[0] if result else None

    def get_lifecycle_coherence(self) -> Optional[str]:
        """
        Get the current lifecycle qualifier coherence status.

        Returns:
            Decision string (e.g., "COHERENT", "INCOHERENT") or None if not found.
        """
        session = self._get_session()
        result = session.execute(
            text("""
                SELECT decision FROM governance_signals
                WHERE signal_type = 'LIFECYCLE_QUALIFIER_COHERENCE'
                AND scope = 'SYSTEM'
                AND superseded_at IS NULL
                ORDER BY recorded_at DESC
                LIMIT 1
            """)
        ).fetchone()
        return result[0] if result else None

    def get_blocked_scopes(self) -> Set[str]:
        """
        Get all currently blocked scopes.

        Returns:
            Set of scope strings that are currently blocked.
        """
        session = self._get_session()
        result = session.execute(
            text("""
                SELECT DISTINCT scope FROM governance_signals
                WHERE decision = 'BLOCKED'
                AND superseded_at IS NULL
                AND (expires_at IS NULL OR expires_at > NOW())
            """)
        ).fetchall()
        return {row[0] for row in result}

    def get_capability_signals(
        self,
        capability_name: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Get blocking/warning signals for a specific capability.

        Args:
            capability_name: The capability name (e.g., "LOGS_LIST")
            limit: Maximum number of signals to return

        Returns:
            List of signal dictionaries with signal_type, decision, reason, recorded_by, recorded_at.
        """
        session = self._get_session()
        result = session.execute(
            text("""
                SELECT signal_type, decision, reason, recorded_by, recorded_at
                FROM governance_signals
                WHERE (scope = :cap_name OR scope = 'SYSTEM')
                AND decision IN ('BLOCKED', 'WARN')
                AND superseded_at IS NULL
                AND (expires_at IS NULL OR expires_at > NOW())
                ORDER BY recorded_at DESC
                LIMIT :limit
            """),
            {"cap_name": capability_name, "limit": limit},
        ).fetchall()

        signals = []
        for row in result:
            signal_type, decision, reason, recorded_by, recorded_at = row
            signals.append({
                "signal_type": signal_type,
                "decision": decision,
                "reason": reason,
                "recorded_by": recorded_by,
                "recorded_at": recorded_at,
            })
        return signals

    def count_blocked_for_capability(self, capability_name: str) -> int:
        """
        Count blocking signals for a specific capability.

        Args:
            capability_name: The capability name (e.g., "LOGS_LIST")

        Returns:
            Count of blocking signals.
        """
        session = self._get_session()
        result = session.execute(
            text("""
                SELECT COUNT(*) FROM governance_signals
                WHERE (scope = :cap_name OR scope = 'SYSTEM')
                AND decision = 'BLOCKED'
                AND superseded_at IS NULL
                AND (expires_at IS NULL OR expires_at > NOW())
            """),
            {"cap_name": capability_name},
        ).scalar()
        return result or 0


def get_platform_driver(session: Optional[Session] = None) -> PlatformDriver:
    """
    Get PlatformDriver instance.

    Args:
        session: Optional SQLModel session. If not provided, creates one internally.

    Returns:
        PlatformDriver instance.
    """
    return PlatformDriver(session)


__all__ = [
    "PlatformDriver",
    "get_platform_driver",
]
