# capability_id: CAP-005
# Layer: L6 — Driver
# Product: founder-console
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: ErrorStoreProtocol implementation for OpsIncidentService
# Callers: OpsFacade
# Allowed Imports: L6 (infra, db)
# Forbidden Imports: L1, L2, L3, L5
# Reference: PIN-264 (Phase-S Track 1.3)

"""
Database Error Store

Implements ErrorStoreProtocol for OpsIncidentService using the
infra_error_events table via app.infra.error_store functions.

This bridges the L6 infra layer with the L4 ops aggregation service.
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine
from sqlmodel import Session

from app.infra import error_store as infra_store


class DatabaseErrorStore:
    """
    ErrorStoreProtocol implementation backed by infra_error_events table.

    This class wraps the L6 infra.error_store functions and provides
    the interface expected by OpsIncidentService.
    """

    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize with database connection.

        Args:
            db_url: Database URL. If not provided, uses DATABASE_URL env var.
        """
        self._db_url = db_url or os.environ.get("DATABASE_URL")
        if not self._db_url:
            raise ValueError("DATABASE_URL is required for DatabaseErrorStore")
        self._engine = None

    @property
    def engine(self):
        """Lazy-load database engine."""
        if self._engine is None:
            # _db_url is guaranteed non-None by __init__ validation
            self._engine = create_engine(self._db_url)  # type: ignore[arg-type]
        return self._engine

    def _get_session(self) -> Session:
        """Create a new database session."""
        return Session(self.engine)

    def get_errors_by_component(
        self,
        component: str,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get errors for a specific component.

        Args:
            component: Component name to filter by
            since: Start time (default: today at midnight)
            limit: Maximum number of errors to return

        Returns:
            List of error dictionaries
        """
        with self._get_session() as session:
            return infra_store.get_errors_by_component(
                session=session,
                component=component,
                since=since,
                limit=limit,
            )

    def get_error_counts_by_class(
        self,
        since: datetime,
        until: Optional[datetime] = None,
    ) -> Dict[str, int]:
        """
        Get error counts grouped by error class.

        Args:
            since: Start of time window
            until: End of time window (default: now)

        Returns:
            Dictionary mapping error class to count
        """
        with self._get_session() as session:
            return infra_store.get_error_counts_by_class(
                session=session,
                since=since,
                until=until,
            )

    def get_error_counts_by_component(
        self,
        since: datetime,
        until: Optional[datetime] = None,
    ) -> Dict[str, int]:
        """
        Get error counts grouped by component.

        Args:
            since: Start of time window
            until: End of time window (default: now)

        Returns:
            Dictionary mapping component to count
        """
        with self._get_session() as session:
            return infra_store.get_error_counts_by_component(
                session=session,
                since=since,
                until=until,
            )
