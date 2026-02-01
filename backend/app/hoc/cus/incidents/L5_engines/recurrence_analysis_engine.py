# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Temporal:
#   Trigger: api
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: Incident (via driver)
#   Writes: none
# Role: Analyze recurring incident patterns (business logic)
# Callers: Incidents API (L2), incidents_facade.py (L5)
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, docs/architecture/incidents/INCIDENTS_DOMAIN_SQL.md#9-hist-o3
# NOTE: Renamed recurrence_analysis_service.py → recurrence_analysis_engine.py (2026-01-24)
#       per BANNED_NAMING rule (*_service.py → *_engine.py)
#       Reclassified L4→L5 - Per HOC topology, engines are L5 (business logic)
#
# EXTRACTION COMPLETE (2026-01-24):
# All DB operations extracted to recurrence_analysis_driver.py (L6).
# This engine now delegates to driver, no direct sqlalchemy imports.

"""
Recurrence Analysis Service (L4 Engine)

Answers "how often does this type repeat?":
- Group by (category, resolution_method)
- Count occurrences over time window
- Calculate recurrence rate

Design Rules:
- Statistical analysis only
- Read-only (no writes)
- No cross-service calls
- Delegates to L6 driver for DB access
"""

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from app.hoc.cus.hoc_spine.services.time import utc_now
from app.hoc.cus.incidents.L6_drivers.recurrence_analysis_driver import (
    RecurrenceAnalysisDriver,
    RecurrenceGroupSnapshot,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class RecurrenceGroup:
    """A group of recurring incidents."""
    category: str
    resolution_method: str | None
    total_occurrences: int
    distinct_days: int
    occurrences_per_day: float
    first_occurrence: datetime
    last_occurrence: datetime
    recent_incident_ids: list[str]


@dataclass
class RecurrenceResult:
    """Result of recurrence analysis."""
    groups: list[RecurrenceGroup]
    baseline_days: int
    total_recurring: int
    generated_at: datetime


class RecurrenceAnalysisService:
    """
    Analyze recurring incident patterns.

    RESPONSIBILITIES (L4):
    - Validate input parameters (threshold, baseline days)
    - Delegate to L6 driver for data access
    - Compose RecurrenceResult from driver snapshots
    - Calculate aggregates (total_recurring)

    FORBIDDEN:
    - Write to any table
    - Call other services
    - Import sqlalchemy at runtime
    """

    # Analysis thresholds (business rules)
    DEFAULT_BASELINE_DAYS = 30
    DEFAULT_RECURRENCE_THRESHOLD = 3  # Min occurrences to be "recurring"
    MAX_BASELINE_DAYS = 90  # Cap at 90 days

    def __init__(self, session: "AsyncSession"):
        self._driver = RecurrenceAnalysisDriver(session)

    async def analyze_recurrence(
        self,
        tenant_id: str,
        baseline_days: int = DEFAULT_BASELINE_DAYS,
        recurrence_threshold: int = DEFAULT_RECURRENCE_THRESHOLD,
        limit: int = 20,
    ) -> RecurrenceResult:
        """
        Analyze incident recurrence patterns.

        Args:
            tenant_id: Tenant scope
            baseline_days: Days to analyze (max 90)
            recurrence_threshold: Min occurrences to flag as recurring
            limit: Max groups to return

        Returns:
            RecurrenceResult with recurring incident groups
        """
        # Business rule: cap baseline days
        baseline_days = min(baseline_days, self.MAX_BASELINE_DAYS)

        # Business rule: min 2 occurrences to be recurring
        recurrence_threshold = max(recurrence_threshold, 2)

        # Delegate to L6 driver
        snapshots = await self._driver.fetch_recurrence_groups(
            tenant_id=tenant_id,
            baseline_days=baseline_days,
            recurrence_threshold=recurrence_threshold,
            limit=limit,
        )

        # Compose result from driver snapshots
        groups: list[RecurrenceGroup] = []
        total_recurring = 0

        for snapshot in snapshots:
            total_recurring += snapshot.total_occurrences
            groups.append(self._snapshot_to_group(snapshot))

        return RecurrenceResult(
            groups=groups,
            baseline_days=baseline_days,
            total_recurring=total_recurring,
            generated_at=utc_now(),
        )

    async def get_recurrence_for_category(
        self,
        tenant_id: str,
        category: str,
        baseline_days: int = DEFAULT_BASELINE_DAYS,
    ) -> RecurrenceGroup | None:
        """
        Get recurrence details for a specific category.

        Args:
            tenant_id: Tenant scope
            category: Category to analyze
            baseline_days: Days to analyze

        Returns:
            RecurrenceGroup if found, None otherwise
        """
        # Delegate to L6 driver
        snapshot = await self._driver.fetch_recurrence_for_category(
            tenant_id=tenant_id,
            category=category,
            baseline_days=baseline_days,
        )

        if not snapshot:
            return None

        return self._snapshot_to_group(snapshot)

    def _snapshot_to_group(self, snapshot: RecurrenceGroupSnapshot) -> RecurrenceGroup:
        """Convert driver snapshot to domain type. No business logic."""
        return RecurrenceGroup(
            category=snapshot.category,
            resolution_method=snapshot.resolution_method,
            total_occurrences=snapshot.total_occurrences,
            distinct_days=snapshot.distinct_days,
            occurrences_per_day=snapshot.occurrences_per_day,
            first_occurrence=snapshot.first_occurrence,
            last_occurrence=snapshot.last_occurrence,
            recent_incident_ids=snapshot.recent_incident_ids,
        )
