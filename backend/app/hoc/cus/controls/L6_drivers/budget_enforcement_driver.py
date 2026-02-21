# capability_id: CAP-009
# Layer: L6 — Data Access Driver
# AUDIENCE: INTERNAL
# Temporal:
#   Trigger: engine
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: runs, provenances, decision_records
#   Writes: none
# Role: Budget enforcement data access operations
# Callers: budget_enforcement_engine.py (L5 engine)
# Allowed Imports: L7 (models), sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-470, Phase-3B SQLAlchemy Extraction
#
# ============================================================================
# L6 DRIVER INVARIANT — BUDGET ENFORCEMENT
# ============================================================================
# This driver handles PERSISTENCE only:
# - Query halted runs without decision records
#
# NO BUSINESS LOGIC. Decisions happen in L4 engine.
# ============================================================================

"""
Budget Enforcement Driver (L6 Data Access)

Handles database operations for budget enforcement:
- Fetching halted runs that lack decision records

Reference: PIN-470, Phase-3B SQLAlchemy Extraction
"""

import logging
import os
from typing import Any, Optional

from sqlalchemy import create_engine, text

logger = logging.getLogger("nova.drivers.budget_enforcement_driver")


class BudgetEnforcementDriver:
    """
    L6 Driver for budget enforcement data operations.

    All methods are pure DB operations - no business logic.
    Business decisions (parsing, emit logic) stay in L4.
    """

    def __init__(self, db_url: Optional[str] = None):
        """Initialize driver with database URL."""
        self._db_url = db_url or os.environ.get("DATABASE_URL")
        self._engine = None

    def _get_engine(self):
        """Lazy engine creation."""
        if self._engine is None:
            if not self._db_url:
                raise RuntimeError("DATABASE_URL not configured")
            self._engine = create_engine(self._db_url)
        return self._engine

    def fetch_pending_budget_halts(self, limit: int = 100) -> list[dict[str, Any]]:
        """
        Fetch runs halted for budget that don't have decision records.

        Args:
            limit: Maximum number of rows to return

        Returns:
            List of dicts with run_id, tenant_id, error_message, plan_json, tool_calls_json
        """
        engine = self._get_engine()

        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text(
                        """
                        SELECT r.id, r.tenant_id, r.error_message, p.plan_json, p.tool_calls_json
                        FROM runs r
                        LEFT JOIN provenances p ON p.run_id = r.id
                        WHERE r.status = 'halted'
                          AND r.error_message LIKE '%Hard budget limit%'
                          AND NOT EXISTS (
                              SELECT 1 FROM contracts.decision_records d
                              WHERE d.run_id = r.id
                                AND d.decision_type = 'budget_enforcement'
                          )
                        LIMIT :limit
                        """
                    ),
                    {"limit": limit},
                )

                rows = []
                for row in result:
                    rows.append({
                        "run_id": row[0],
                        "tenant_id": row[1],
                        "error_message": row[2],
                        "plan_json": row[3],
                        "tool_calls_json": row[4],
                    })

                return rows

        except Exception as e:
            logger.error(f"Failed to fetch pending budget halts: {e}")
            raise

    def dispose(self) -> None:
        """Dispose of the engine connection pool."""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None


def get_budget_enforcement_driver(db_url: Optional[str] = None) -> BudgetEnforcementDriver:
    """Get a BudgetEnforcementDriver instance."""
    return BudgetEnforcementDriver(db_url)
