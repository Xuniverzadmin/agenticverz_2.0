# Layer: L6 — Domain Driver
# AUDIENCE: INTERNAL
# Product: system-wide (M25 Integration API)
# Temporal:
#   Trigger: api
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: loop_events, human_checkpoints, loop_traces, recovery_candidates,
#          policy_rules, routing_policy_adjustments, prevention_records,
#          regret_events, timeline_views, incidents
#   Writes: none
# Database:
#   Scope: domain (policies/m25_integration)
#   Models: LoopEvent, HumanCheckpoint, LoopTrace, etc.
# Role: DB read driver for M25 Integration APIs (DB boundary crossing) — L6 DOES NOT COMMIT
# Callers: L4 handlers via registry dispatch, L2 M25_integrations.py (transitional)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: L2 first-principles purity — move session.execute() out of L2
# artifact_class: CODE

"""
M25 Integration Read Driver - DB read operations for M25 Integration APIs.

Extracted from hoc/api/cus/policies/M25_integrations.py to achieve L2 first-principles purity.

Constraints (enforced by PIN-250):
- Read-only: No write operations, no policy logic
- No cross-service calls
- SQL text preserved exactly (no changes)
- L6 drivers DO NOT COMMIT
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class LoopStageRow:
    """Row from loop_events for stage details."""
    stage: str
    details: Optional[dict]
    failure_state: Optional[str]
    confidence_band: Optional[str]
    created_at: Optional[datetime]


@dataclass
class CheckpointRow:
    """Row from human_checkpoints."""
    id: str
    checkpoint_type: str
    incident_id: str
    stage: str
    target_id: str
    description: Optional[str]
    options: Any  # Can be list or JSON string
    created_at: datetime
    resolved_at: Optional[datetime]
    resolved_by: Optional[str]
    resolution: Optional[str]
    tenant_id: str


@dataclass
class LoopStatsRow:
    """Aggregated loop statistics."""
    total: int
    complete: int
    avg_time_ms: Optional[float]


@dataclass
class PatternStatsRow:
    """Aggregated pattern match statistics."""
    total: int
    strong: int
    weak: int
    novel: int


@dataclass
class RecoveryStatsRow:
    """Aggregated recovery statistics."""
    total: int
    applied: int
    rejected: int


@dataclass
class PolicyStatsRow:
    """Aggregated policy statistics."""
    total: int
    shadow: int
    active: int


@dataclass
class RoutingStatsRow:
    """Aggregated routing adjustment statistics."""
    total: int
    rolled_back: int


@dataclass
class CheckpointStatsRow:
    """Aggregated checkpoint statistics."""
    pending: int
    resolved: int


@dataclass
class SimulationStateRow:
    """Simulation state for graduation gates."""
    sim_gate1: bool
    sim_gate2: bool
    sim_gate3: bool


@dataclass
class IncidentRow:
    """Row from incidents table."""
    id: str
    tenant_id: str
    title: Optional[str]
    severity: Optional[str]
    created_at: Optional[datetime]


@dataclass
class PreventionRow:
    """Row from prevention_records."""
    id: str
    blocked_incident_id: str
    policy_id: str
    pattern_id: str
    signature_match_confidence: float
    created_at: datetime


@dataclass
class RegretRow:
    """Row from regret_events."""
    id: str
    policy_id: str
    regret_type: str
    description: Optional[str]
    severity: int
    was_auto_rolled_back: bool
    created_at: datetime


class M25IntegrationReadDriver:
    """
    Async DB read operations for M25 Integration APIs.

    Read-only driver. No writes, no policy logic.
    Raw SQL preserved exactly as extracted from M25_integrations.py.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_loop_stages(self, incident_id: str) -> list[LoopStageRow]:
        """
        Get loop events/stages for an incident.

        SQL preserved exactly from M25_integrations.py get_loop_stages endpoint.

        Args:
            incident_id: Incident ID to fetch stages for

        Returns:
            List of LoopStageRow dataclasses
        """
        result = await self.session.execute(
            text(
                """
                SELECT stage, details, failure_state, confidence_band, created_at
                FROM loop_events
                WHERE incident_id = :incident_id
                ORDER BY created_at ASC
            """
            ),
            {"incident_id": incident_id},
        )
        rows = result.fetchall()

        return [
            LoopStageRow(
                stage=row.stage,
                details=row.details if isinstance(row.details, dict) else {},
                failure_state=row.failure_state,
                confidence_band=row.confidence_band,
                created_at=row.created_at,
            )
            for row in rows
        ]

    async def get_checkpoint(
        self, checkpoint_id: str, tenant_id: str
    ) -> Optional[CheckpointRow]:
        """
        Get a specific human checkpoint by ID.

        SQL preserved exactly from M25_integrations.py get_checkpoint endpoint.

        Args:
            checkpoint_id: Checkpoint ID
            tenant_id: Tenant ID for access control

        Returns:
            CheckpointRow if found, None otherwise
        """
        result = await self.session.execute(
            text(
                """
                SELECT * FROM human_checkpoints
                WHERE id = :id AND tenant_id = :tenant_id
            """
            ),
            {"id": checkpoint_id, "tenant_id": tenant_id},
        )
        row = result.fetchone()

        if not row:
            return None

        return CheckpointRow(
            id=row.id,
            checkpoint_type=row.checkpoint_type,
            incident_id=row.incident_id,
            stage=row.stage,
            target_id=row.target_id,
            description=row.description,
            options=row.options,
            created_at=row.created_at,
            resolved_at=row.resolved_at,
            resolved_by=row.resolved_by,
            resolution=row.resolution,
            tenant_id=row.tenant_id,
        )

    async def get_loop_stats(
        self, tenant_id: str, cutoff: datetime
    ) -> LoopStatsRow:
        """
        Get loop trace statistics for a time period.

        SQL preserved exactly from M25_integrations.py get_integration_stats endpoint.

        Args:
            tenant_id: Tenant ID
            cutoff: Datetime cutoff for the period

        Returns:
            LoopStatsRow with aggregated statistics
        """
        result = await self.session.execute(
            text(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE is_complete) as complete,
                    AVG(EXTRACT(EPOCH FROM (completed_at - started_at)) * 1000)
                        FILTER (WHERE completed_at IS NOT NULL) as avg_time_ms
                FROM loop_traces
                WHERE tenant_id = :tenant_id
                AND started_at >= :cutoff
            """
            ),
            {"tenant_id": tenant_id, "cutoff": cutoff},
        )
        row = result.fetchone()

        return LoopStatsRow(
            total=row.total or 0,
            complete=row.complete or 0,
            avg_time_ms=row.avg_time_ms,
        )

    async def get_pattern_stats(
        self, tenant_id: str, cutoff: datetime
    ) -> PatternStatsRow:
        """
        Get pattern match statistics for a time period.

        SQL preserved exactly from M25_integrations.py get_integration_stats endpoint.

        Args:
            tenant_id: Tenant ID
            cutoff: Datetime cutoff for the period

        Returns:
            PatternStatsRow with aggregated statistics
        """
        result = await self.session.execute(
            text(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE confidence_band = 'strong_match') as strong,
                    COUNT(*) FILTER (WHERE confidence_band = 'weak_match') as weak,
                    COUNT(*) FILTER (WHERE confidence_band = 'novel') as novel
                FROM loop_events
                WHERE tenant_id = :tenant_id
                AND stage = 'pattern_matched'
                AND created_at >= :cutoff
            """
            ),
            {"tenant_id": tenant_id, "cutoff": cutoff},
        )
        row = result.fetchone()

        return PatternStatsRow(
            total=row.total or 0,
            strong=row.strong or 0,
            weak=row.weak or 0,
            novel=row.novel or 0,
        )

    async def get_recovery_stats(
        self, tenant_id: str, cutoff: datetime
    ) -> RecoveryStatsRow:
        """
        Get recovery candidate statistics for a time period.

        SQL preserved exactly from M25_integrations.py get_integration_stats endpoint.

        Args:
            tenant_id: Tenant ID
            cutoff: Datetime cutoff for the period

        Returns:
            RecoveryStatsRow with aggregated statistics
        """
        result = await self.session.execute(
            text(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'applied') as applied,
                    COUNT(*) FILTER (WHERE status = 'rejected') as rejected
                FROM recovery_candidates
                WHERE source_incident_id IN (
                    SELECT incident_id FROM loop_traces
                    WHERE tenant_id = :tenant_id
                )
                AND created_at >= :cutoff
            """
            ),
            {"tenant_id": tenant_id, "cutoff": cutoff},
        )
        row = result.fetchone()

        return RecoveryStatsRow(
            total=row.total or 0,
            applied=row.applied or 0,
            rejected=row.rejected or 0,
        )

    async def get_policy_stats(self, cutoff: datetime) -> PolicyStatsRow:
        """
        Get policy rule statistics for a time period.

        SQL preserved exactly from M25_integrations.py get_integration_stats endpoint.

        Args:
            cutoff: Datetime cutoff for the period

        Returns:
            PolicyStatsRow with aggregated statistics
        """
        result = await self.session.execute(
            text(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE mode = 'shadow') as shadow,
                    COUNT(*) FILTER (WHERE mode = 'active') as active
                FROM policy_rules
                WHERE source_type = 'recovery'
                AND created_at >= :cutoff
            """
            ),
            {"cutoff": cutoff},
        )
        row = result.fetchone()

        return PolicyStatsRow(
            total=row.total or 0,
            shadow=row.shadow or 0,
            active=row.active or 0,
        )

    async def get_routing_stats(self, cutoff: datetime) -> RoutingStatsRow:
        """
        Get routing policy adjustment statistics for a time period.

        SQL preserved exactly from M25_integrations.py get_integration_stats endpoint.

        Args:
            cutoff: Datetime cutoff for the period

        Returns:
            RoutingStatsRow with aggregated statistics
        """
        result = await self.session.execute(
            text(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE was_rolled_back) as rolled_back
                FROM routing_policy_adjustments
                WHERE created_at >= :cutoff
            """
            ),
            {"cutoff": cutoff},
        )
        row = result.fetchone()

        return RoutingStatsRow(
            total=row.total or 0,
            rolled_back=row.rolled_back or 0,
        )

    async def get_checkpoint_stats(
        self, tenant_id: str, cutoff: datetime
    ) -> CheckpointStatsRow:
        """
        Get human checkpoint statistics for a time period.

        SQL preserved exactly from M25_integrations.py get_integration_stats endpoint.

        Args:
            tenant_id: Tenant ID
            cutoff: Datetime cutoff for the period

        Returns:
            CheckpointStatsRow with aggregated statistics
        """
        result = await self.session.execute(
            text(
                """
                SELECT
                    COUNT(*) FILTER (WHERE resolved_at IS NULL) as pending,
                    COUNT(*) FILTER (WHERE resolved_at IS NOT NULL) as resolved
                FROM human_checkpoints
                WHERE tenant_id = :tenant_id
                AND created_at >= :cutoff
            """
            ),
            {"tenant_id": tenant_id, "cutoff": cutoff},
        )
        row = result.fetchone()

        return CheckpointStatsRow(
            pending=row.pending or 0,
            resolved=row.resolved or 0,
        )

    async def get_simulation_state(self) -> SimulationStateRow:
        """
        Get simulation state for graduation gates.

        SQL preserved exactly from M25_integrations.py get_graduation_status endpoint.

        Returns:
            SimulationStateRow with gate simulation states
        """
        result = await self.session.execute(
            text(
                """
                SELECT
                    EXISTS(SELECT 1 FROM prevention_records WHERE is_simulated = true) as sim_gate1,
                    EXISTS(SELECT 1 FROM regret_events WHERE is_simulated = true) as sim_gate2,
                    EXISTS(SELECT 1 FROM timeline_views WHERE is_simulated = true) as sim_gate3
            """
            )
        )
        row = result.fetchone()

        if not row:
            return SimulationStateRow(
                sim_gate1=False,
                sim_gate2=False,
                sim_gate3=False,
            )

        return SimulationStateRow(
            sim_gate1=row.sim_gate1 or False,
            sim_gate2=row.sim_gate2 or False,
            sim_gate3=row.sim_gate3 or False,
        )

    async def get_incident(self, incident_id: str) -> Optional[IncidentRow]:
        """
        Get incident information.

        SQL preserved exactly from M25_integrations.py get_prevention_timeline endpoint.

        Args:
            incident_id: Incident ID

        Returns:
            IncidentRow if found, None otherwise
        """
        result = await self.session.execute(
            text(
                """
                SELECT id, tenant_id, title, severity, created_at
                FROM incidents
                WHERE id = :incident_id
            """
            ),
            {"incident_id": incident_id},
        )
        row = result.fetchone()

        if not row:
            return None

        return IncidentRow(
            id=row.id,
            tenant_id=row.tenant_id,
            title=row.title,
            severity=row.severity,
            created_at=row.created_at,
        )

    async def get_loop_events_for_timeline(
        self, incident_id: str
    ) -> list[LoopStageRow]:
        """
        Get loop events for prevention timeline (different from get_loop_stages).

        SQL preserved exactly from M25_integrations.py get_prevention_timeline endpoint.

        Args:
            incident_id: Incident ID

        Returns:
            List of LoopStageRow for timeline construction
        """
        result = await self.session.execute(
            text(
                """
                SELECT stage, details, confidence_band, created_at
                FROM loop_events
                WHERE incident_id = :incident_id
                ORDER BY created_at ASC
            """
            ),
            {"incident_id": incident_id},
        )
        rows = result.fetchall()

        return [
            LoopStageRow(
                stage=row.stage,
                details=row.details if isinstance(row.details, dict) else {},
                failure_state=None,  # Not selected in this query
                confidence_band=row.confidence_band,
                created_at=row.created_at,
            )
            for row in rows
        ]

    async def get_prevention_records(
        self, original_incident_id: str
    ) -> list[PreventionRow]:
        """
        Get prevention records where incident was the original.

        SQL preserved exactly from M25_integrations.py get_prevention_timeline endpoint.

        Args:
            original_incident_id: Original incident ID that policies were born from

        Returns:
            List of PreventionRow
        """
        result = await self.session.execute(
            text(
                """
                SELECT id, blocked_incident_id, policy_id, pattern_id,
                       signature_match_confidence, created_at
                FROM prevention_records
                WHERE original_incident_id = :incident_id
                ORDER BY created_at ASC
            """
            ),
            {"incident_id": original_incident_id},
        )
        rows = result.fetchall()

        return [
            PreventionRow(
                id=row.id,
                blocked_incident_id=row.blocked_incident_id,
                policy_id=row.policy_id,
                pattern_id=row.pattern_id,
                signature_match_confidence=row.signature_match_confidence,
                created_at=row.created_at,
            )
            for row in rows
        ]

    async def get_regret_events_for_incident(
        self, incident_id: str
    ) -> list[RegretRow]:
        """
        Get regret events for policies born from an incident.

        SQL preserved exactly from M25_integrations.py get_prevention_timeline endpoint.

        Args:
            incident_id: Incident ID whose policies to check for regret

        Returns:
            List of RegretRow
        """
        result = await self.session.execute(
            text(
                """
                SELECT re.id, re.policy_id, re.regret_type, re.description,
                       re.severity, re.was_auto_rolled_back, re.created_at
                FROM regret_events re
                WHERE re.policy_id IN (
                    SELECT DISTINCT details->>'policy_id'
                    FROM loop_events
                    WHERE incident_id = :incident_id
                    AND stage = 'policy_generated'
                )
                ORDER BY re.created_at ASC
            """
            ),
            {"incident_id": incident_id},
        )
        rows = result.fetchall()

        return [
            RegretRow(
                id=row.id,
                policy_id=row.policy_id,
                regret_type=row.regret_type,
                description=row.description,
                severity=row.severity,
                was_auto_rolled_back=row.was_auto_rolled_back,
                created_at=row.created_at,
            )
            for row in rows
        ]


def get_m25_integration_read_driver(session: AsyncSession) -> M25IntegrationReadDriver:
    """Factory function for M25IntegrationReadDriver."""
    return M25IntegrationReadDriver(session)
