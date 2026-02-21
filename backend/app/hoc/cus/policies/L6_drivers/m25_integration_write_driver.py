# capability_id: CAP-009
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
#   Reads: none
#   Writes: prevention_records, regret_events, policy_regret_summary,
#           timeline_views, graduation_history, m25_graduation_status
# Database:
#   Scope: domain (policies/m25_integration)
#   Models: PreventionRecord, RegretEvent, PolicyRegretSummary, TimelineView, etc.
# Role: DB write driver for M25 Integration APIs (DB boundary crossing) — L6 DOES NOT COMMIT
# Callers: L4 handlers via registry dispatch, L2 M25_integrations.py (transitional)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: L2 first-principles purity — move session.execute() out of L2
# artifact_class: CODE

"""
M25 Integration Write Driver - DB write operations for M25 Integration APIs.

Extracted from hoc/api/cus/policies/M25_integrations.py to achieve L2 first-principles purity.

Constraints (enforced by PIN-250):
- Write operations only, no read operations (use read driver)
- No cross-service calls
- SQL text preserved exactly (no changes)
- L6 drivers DO NOT COMMIT — caller owns transaction
"""

from dataclasses import dataclass
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class PreventionRecordInput:
    """Input for inserting a prevention record."""
    id: str
    policy_id: str
    pattern_id: str
    original_incident_id: str
    blocked_incident_id: str
    tenant_id: str
    confidence: float
    is_simulated: bool = True


@dataclass
class RegretEventInput:
    """Input for inserting a regret event."""
    id: str
    policy_id: str
    tenant_id: str
    regret_type: str
    description: str
    severity: int
    is_simulated: bool = True


@dataclass
class TimelineViewInput:
    """Input for inserting a timeline view."""
    id: str
    incident_id: str
    tenant_id: str
    user_id: str
    has_prevention: bool
    has_rollback: bool
    is_simulated: bool
    session_id: str


@dataclass
class GraduationHistoryInput:
    """Input for inserting graduation history."""
    level: str
    gates_json: str
    is_degraded: bool
    degraded_from: Optional[str]
    degradation_reason: Optional[str]
    evidence_snapshot: str


@dataclass
class GraduationStatusUpdateInput:
    """Input for updating m25_graduation_status."""
    status_label: str
    is_graduated: bool
    gate1_passed: bool
    gate2_passed: bool
    gate3_passed: bool


class M25IntegrationWriteDriver:
    """
    Async DB write operations for M25 Integration APIs.

    Write-only driver. L6 drivers DO NOT COMMIT.
    Raw SQL preserved exactly as extracted from M25_integrations.py.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def insert_prevention_record(
        self, data: PreventionRecordInput
    ) -> None:
        """
        Insert a prevention record (simulated or real).

        SQL preserved exactly from M25_integrations.py simulate_prevention endpoint.

        Args:
            data: PreventionRecordInput with all fields

        Note: L6 driver does NOT commit. Caller owns transaction.
        """
        await self.session.execute(
            text(
                """
                INSERT INTO prevention_records (
                    id, policy_id, pattern_id, original_incident_id,
                    blocked_incident_id, tenant_id, outcome,
                    signature_match_confidence, policy_age_seconds,
                    is_simulated, created_at
                ) VALUES (
                    :id, :policy_id, :pattern_id, :original_incident_id,
                    :blocked_incident_id, :tenant_id, 'prevented',
                    :confidence, 3600,
                    :is_simulated, NOW()
                )
            """
            ),
            {
                "id": data.id,
                "policy_id": data.policy_id,
                "pattern_id": data.pattern_id,
                "original_incident_id": data.original_incident_id,
                "blocked_incident_id": data.blocked_incident_id,
                "tenant_id": data.tenant_id,
                "confidence": data.confidence,
                "is_simulated": data.is_simulated,
            },
        )

    async def insert_regret_event(self, data: RegretEventInput) -> None:
        """
        Insert a regret event (simulated or real).

        SQL preserved exactly from M25_integrations.py simulate_regret endpoint.

        Args:
            data: RegretEventInput with all fields

        Note: L6 driver does NOT commit. Caller owns transaction.
        """
        await self.session.execute(
            text(
                """
                INSERT INTO regret_events (
                    id, policy_id, tenant_id, regret_type,
                    description, severity, affected_calls, affected_users,
                    was_auto_rolled_back, is_simulated, created_at
                ) VALUES (
                    :id, :policy_id, :tenant_id, :regret_type,
                    :description, :severity, 50, 10,
                    true, :is_simulated, NOW()
                )
            """
            ),
            {
                "id": data.id,
                "policy_id": data.policy_id,
                "tenant_id": data.tenant_id,
                "regret_type": data.regret_type,
                "description": data.description,
                "severity": data.severity,
                "is_simulated": data.is_simulated,
            },
        )

    async def upsert_policy_regret_summary(
        self, policy_id: str, score: float
    ) -> None:
        """
        Insert or update policy regret summary.

        SQL preserved exactly from M25_integrations.py simulate_regret endpoint.

        Args:
            policy_id: Policy ID
            score: Regret score to add

        Note: L6 driver does NOT commit. Caller owns transaction.
        """
        await self.session.execute(
            text(
                """
                INSERT INTO policy_regret_summary (
                    policy_id, regret_score, regret_event_count,
                    demoted_at, demoted_reason, last_updated
                ) VALUES (
                    :policy_id, :score, 1,
                    NOW(), 'SIMULATED demotion - does not count toward graduation',
                    NOW()
                )
                ON CONFLICT (policy_id) DO UPDATE SET
                    regret_score = policy_regret_summary.regret_score + :score,
                    regret_event_count = policy_regret_summary.regret_event_count + 1,
                    demoted_at = NOW(),
                    demoted_reason = 'SIMULATED demotion - does not count toward graduation',
                    last_updated = NOW()
            """
            ),
            {
                "policy_id": policy_id,
                "score": score,
            },
        )

    async def insert_timeline_view(self, data: TimelineViewInput) -> None:
        """
        Insert a timeline view (simulated or real).

        SQL preserved exactly from M25_integrations.py simulate_timeline_view
        and record_timeline_view endpoints.

        Args:
            data: TimelineViewInput with all fields

        Note: L6 driver does NOT commit. Caller owns transaction.
        """
        await self.session.execute(
            text(
                """
                INSERT INTO timeline_views (
                    id, incident_id, tenant_id, user_id,
                    has_prevention, has_rollback,
                    is_simulated, session_id, viewed_at
                ) VALUES (
                    :id, :incident_id, :tenant_id, :user_id,
                    :has_prevention, :has_rollback,
                    :is_simulated, :session_id, NOW()
                )
            """
            ),
            {
                "id": data.id,
                "incident_id": data.incident_id,
                "tenant_id": data.tenant_id,
                "user_id": data.user_id,
                "has_prevention": data.has_prevention,
                "has_rollback": data.has_rollback,
                "is_simulated": data.is_simulated,
                "session_id": data.session_id,
            },
        )

    async def insert_graduation_history(
        self, data: GraduationHistoryInput
    ) -> None:
        """
        Insert graduation history for audit trail.

        SQL preserved exactly from M25_integrations.py trigger_graduation_re_evaluation.

        Args:
            data: GraduationHistoryInput with all fields

        Note: L6 driver does NOT commit. Caller owns transaction.
        """
        await self.session.execute(
            text(
                """
                INSERT INTO graduation_history (
                    level, gates_json, computed_at, is_degraded,
                    degraded_from, degradation_reason, evidence_snapshot
                ) VALUES (
                    :level, :gates_json, NOW(), :is_degraded,
                    :degraded_from, :degradation_reason, :evidence_snapshot
                )
            """
            ),
            {
                "level": data.level,
                "gates_json": data.gates_json,
                "is_degraded": data.is_degraded,
                "degraded_from": data.degraded_from,
                "degradation_reason": data.degradation_reason,
                "evidence_snapshot": data.evidence_snapshot,
            },
        )

    async def update_graduation_status(
        self, data: GraduationStatusUpdateInput
    ) -> None:
        """
        Update m25_graduation_status with derived values.

        SQL preserved exactly from M25_integrations.py trigger_graduation_re_evaluation.

        Args:
            data: GraduationStatusUpdateInput with all fields

        Note: L6 driver does NOT commit. Caller owns transaction.
        """
        await self.session.execute(
            text(
                """
                UPDATE m25_graduation_status
                SET is_derived = true,
                    last_evidence_eval = NOW(),
                    status_label = :status_label,
                    is_graduated = :is_graduated,
                    gate1_passed = :gate1_passed,
                    gate2_passed = :gate2_passed,
                    gate3_passed = :gate3_passed,
                    last_checked = NOW()
                WHERE id = 1
            """
            ),
            {
                "status_label": data.status_label,
                "is_graduated": data.is_graduated,
                "gate1_passed": data.gate1_passed,
                "gate2_passed": data.gate2_passed,
                "gate3_passed": data.gate3_passed,
            },
        )


def get_m25_integration_write_driver(
    session: AsyncSession,
) -> M25IntegrationWriteDriver:
    """Factory function for M25IntegrationWriteDriver."""
    return M25IntegrationWriteDriver(session)
