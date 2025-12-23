"""
M25 Graduation Engine

CRITICAL: This module ensures graduation is DERIVED, not DECLARED.

Graduation is:
- Computed from evidence (not manually set)
- Re-evaluated periodically (not one-time)
- Downgradable when evidence regresses
- Separate from simulation state
- Tied to real capability gates

"A badge you flip once and forget" is worthless.
Graduation must be continuously earned.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional, NamedTuple

logger = logging.getLogger(__name__)


# =============================================================================
# GRADUATION THRESHOLDS (Configurable, not hardcoded)
# =============================================================================

@dataclass
class GraduationThresholds:
    """
    Configurable thresholds for graduation gates.

    These can be tightened as the system matures.
    """
    # Gate 1: Prevention Proof
    min_preventions: int = 1              # At least 1 prevention
    prevention_rate_min: float = 0.5      # At least 50% prevention rate
    prevention_window_days: int = 30      # Look back 30 days

    # Gate 2: Regret Rollback
    min_auto_demotions: int = 1           # At least 1 auto-demotion observed
    max_regret_rate: float = 0.3          # Regret rate must be < 30%
    regret_window_days: int = 30          # Look back 30 days

    # Gate 3: Console Proof
    min_timeline_views: int = 1           # At least 1 timeline with prevention viewed
    timeline_window_days: int = 30        # Look back 30 days

    # Downgrade triggers (evidence regression)
    downgrade_if_prevention_rate_below: float = 0.3  # Downgrade if rate drops below 30%
    downgrade_if_regret_rate_above: float = 0.5      # Downgrade if regret exceeds 50%
    downgrade_if_no_prevention_days: int = 14        # Downgrade if no prevention in 14 days


# =============================================================================
# GRADUATION EVIDENCE (Pure data from database)
# =============================================================================

class GateEvidence(NamedTuple):
    """Evidence for a single gate - computed from database."""
    name: str
    passed: bool
    score: float        # 0.0 to 1.0, how well we're doing
    evidence: dict      # Raw evidence
    last_evaluated: datetime
    degraded: bool      # True if recently passed but now failing


@dataclass
class GraduationEvidence:
    """
    All evidence needed to compute graduation status.

    This is a SNAPSHOT of database state - graduation is derived from this.
    """
    # Gate 1: Prevention
    total_preventions: int = 0
    total_prevention_attempts: int = 0
    last_prevention_at: Optional[datetime] = None
    prevention_rate: float = 0.0

    # Gate 2: Regret
    total_regret_events: int = 0
    total_auto_demotions: int = 0
    last_demotion_at: Optional[datetime] = None
    regret_rate: float = 0.0

    # Gate 3: Console
    timeline_views_with_prevention: int = 0
    last_timeline_view_at: Optional[datetime] = None

    # Metadata
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    evidence_window_start: Optional[datetime] = None
    evidence_window_end: Optional[datetime] = None

    @classmethod
    async def fetch_from_database(cls, session, window_days: int = 30) -> "GraduationEvidence":
        """
        Fetch evidence from database.

        This is the ONLY place graduation evidence comes from.
        No manual overrides, no simulations counted here.
        """
        from sqlalchemy import text

        now = datetime.now(timezone.utc)
        window_start = now - timedelta(days=window_days)

        # Gate 1: Prevention evidence (exclude simulated)
        prevention_result = await session.execute(
            text("""
                SELECT
                    COUNT(*) FILTER (WHERE outcome = 'prevented') as prevented,
                    COUNT(*) as total,
                    MAX(created_at) as last_at
                FROM prevention_records
                WHERE created_at >= :window_start
                AND (
                    id NOT LIKE 'prev_sim_%' OR id IS NULL
                )
            """),
            {"window_start": window_start}
        )
        prev_row = prevention_result.fetchone()

        # Gate 2: Regret evidence (exclude simulated)
        regret_result = await session.execute(
            text("""
                SELECT
                    COUNT(*) as total_events,
                    COUNT(*) FILTER (WHERE was_auto_rolled_back = true) as demotions,
                    MAX(created_at) FILTER (WHERE was_auto_rolled_back = true) as last_demotion
                FROM regret_events
                WHERE created_at >= :window_start
                AND (
                    id NOT LIKE 'regret_sim_%' OR id IS NULL
                )
            """),
            {"window_start": window_start}
        )
        regret_row = regret_result.fetchone()

        # Gate 3: Timeline views (real user views only)
        timeline_result = await session.execute(
            text("""
                SELECT
                    COUNT(*) as views_with_prevention,
                    MAX(viewed_at) as last_view
                FROM timeline_views
                WHERE viewed_at >= :window_start
                AND has_prevention = true
                AND is_simulated = false
            """),
            {"window_start": window_start}
        )
        timeline_row = timeline_result.fetchone()

        # Compute rates
        total_prevention_attempts = prev_row.total if prev_row else 0
        total_preventions = prev_row.prevented if prev_row else 0
        prevention_rate = (
            total_preventions / total_prevention_attempts
            if total_prevention_attempts > 0 else 0.0
        )

        total_policy_evaluations = await cls._get_total_policy_evaluations(session, window_start)
        regret_rate = (
            (regret_row.total_events or 0) / total_policy_evaluations
            if total_policy_evaluations > 0 else 0.0
        )

        return cls(
            total_preventions=total_preventions,
            total_prevention_attempts=total_prevention_attempts,
            last_prevention_at=prev_row.last_at if prev_row else None,
            prevention_rate=prevention_rate,
            total_regret_events=regret_row.total_events if regret_row else 0,
            total_auto_demotions=regret_row.demotions if regret_row else 0,
            last_demotion_at=regret_row.last_demotion if regret_row else None,
            regret_rate=regret_rate,
            timeline_views_with_prevention=timeline_row.views_with_prevention if timeline_row else 0,
            last_timeline_view_at=timeline_row.last_view if timeline_row else None,
            evaluated_at=now,
            evidence_window_start=window_start,
            evidence_window_end=now,
        )

    @staticmethod
    async def _get_total_policy_evaluations(session, window_start: datetime) -> int:
        """Get total policy evaluations for regret rate calculation.

        Falls back to policy_rules count if policy_evaluations table doesn't exist.
        Uses table existence check to avoid transaction abort.
        """
        from sqlalchemy import text

        # Check if policy_evaluations table exists first (to avoid aborting transaction)
        table_check = await session.execute(
            text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'policy_evaluations'
                )
            """)
        )
        has_policy_evaluations = table_check.scalar()

        if has_policy_evaluations:
            result = await session.execute(
                text("""
                    SELECT COUNT(*) as total
                    FROM policy_evaluations
                    WHERE created_at >= :window_start
                """),
                {"window_start": window_start}
            )
            row = result.fetchone()
            return row.total if row else 0

        # Fall back to policy_rules count
        table_check2 = await session.execute(
            text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'policy_rules'
                )
            """)
        )
        has_policy_rules = table_check2.scalar()

        if has_policy_rules:
            result = await session.execute(
                text("""
                    SELECT COUNT(*) as total
                    FROM policy_rules
                    WHERE created_at >= :window_start
                """),
                {"window_start": window_start}
            )
            row = result.fetchone()
            return row.total if row else 0

        # Neither table exists - return 0 to avoid division by zero
        return 0


# =============================================================================
# GRADUATION STATE (Derived, not declared)
# =============================================================================

class GraduationLevel(str, Enum):
    """Graduation levels - derived from evidence."""
    ALPHA = "alpha"           # Loop-enabled, not loop-proven
    BETA = "beta"             # Gate 1 passed (prevention proven)
    CANDIDATE = "candidate"   # Gates 1+2 passed (self-correction proven)
    COMPLETE = "complete"     # All gates passed (fully proven)
    DEGRADED = "degraded"     # Was graduated, but evidence regressed


@dataclass
class ComputedGraduationStatus:
    """
    Graduation status computed from evidence.

    This is DERIVED - never set manually.
    """
    level: GraduationLevel
    gates: dict[str, GateEvidence]
    thresholds: GraduationThresholds
    computed_at: datetime

    # Previous state (for degradation detection)
    previous_level: Optional[GraduationLevel] = None
    degraded_from: Optional[GraduationLevel] = None
    degraded_at: Optional[datetime] = None
    degradation_reason: Optional[str] = None

    @property
    def is_graduated(self) -> bool:
        return self.level == GraduationLevel.COMPLETE

    @property
    def is_degraded(self) -> bool:
        return self.degraded_from is not None

    @property
    def status_label(self) -> str:
        if self.level == GraduationLevel.COMPLETE:
            return "M25-COMPLETE (Loop-Proven)"
        elif self.level == GraduationLevel.DEGRADED:
            return f"M25-DEGRADED (was {self.degraded_from.value})"
        else:
            passed = sum(1 for g in self.gates.values() if g.passed)
            return f"M25-{self.level.value.upper()} ({passed}/3 gates)"

    def to_api_response(self) -> dict:
        """Format for API response."""
        return {
            "status": self.status_label,
            "level": self.level.value,
            "is_graduated": self.is_graduated,
            "is_degraded": self.is_degraded,
            "gates": {
                name: {
                    "name": evidence.name,
                    "passed": evidence.passed,
                    "score": evidence.score,
                    "evidence": evidence.evidence,
                    "degraded": evidence.degraded,
                }
                for name, evidence in self.gates.items()
            },
            "computed_at": self.computed_at.isoformat(),
            "degradation": {
                "from_level": self.degraded_from.value if self.degraded_from else None,
                "at": self.degraded_at.isoformat() if self.degraded_at else None,
                "reason": self.degradation_reason,
            } if self.is_degraded else None,
        }


# =============================================================================
# GRADUATION ENGINE (Pure function over evidence)
# =============================================================================

class GraduationEngine:
    """
    Computes graduation status from evidence.

    CRITICAL INVARIANTS:
    1. Graduation is derived, never manually set
    2. Graduation can degrade when evidence regresses
    3. Simulation state is separate from real graduation
    4. Re-evaluation happens periodically
    """

    def __init__(self, thresholds: Optional[GraduationThresholds] = None):
        self.thresholds = thresholds or GraduationThresholds()
        self._last_status: Optional[ComputedGraduationStatus] = None

    def compute(
        self,
        evidence: GraduationEvidence,
        previous_status: Optional[ComputedGraduationStatus] = None,
    ) -> ComputedGraduationStatus:
        """
        Compute graduation status from evidence.

        This is a PURE FUNCTION - same evidence = same result.
        """
        now = datetime.now(timezone.utc)

        # Evaluate each gate
        gate1 = self._evaluate_gate1(evidence)
        gate2 = self._evaluate_gate2(evidence)
        gate3 = self._evaluate_gate3(evidence)

        gates = {
            "prevention": gate1,
            "rollback": gate2,
            "timeline": gate3,
        }

        # Determine level
        passed_count = sum(1 for g in gates.values() if g.passed)

        if passed_count == 3:
            level = GraduationLevel.COMPLETE
        elif passed_count == 2 and gate1.passed and gate2.passed:
            level = GraduationLevel.CANDIDATE
        elif passed_count >= 1 and gate1.passed:
            level = GraduationLevel.BETA
        else:
            level = GraduationLevel.ALPHA

        # Check for degradation
        degraded_from = None
        degraded_at = None
        degradation_reason = None

        if previous_status:
            degradation = self._check_degradation(
                previous_status.level,
                level,
                gates,
                evidence,
            )
            if degradation:
                level = GraduationLevel.DEGRADED
                degraded_from = degradation["from"]
                degraded_at = now
                degradation_reason = degradation["reason"]

        status = ComputedGraduationStatus(
            level=level,
            gates=gates,
            thresholds=self.thresholds,
            computed_at=now,
            previous_level=previous_status.level if previous_status else None,
            degraded_from=degraded_from,
            degraded_at=degraded_at,
            degradation_reason=degradation_reason,
        )

        self._last_status = status
        return status

    def _evaluate_gate1(self, evidence: GraduationEvidence) -> GateEvidence:
        """Gate 1: Prevention Proof"""
        now = datetime.now(timezone.utc)

        # Check thresholds
        has_min_preventions = evidence.total_preventions >= self.thresholds.min_preventions
        has_min_rate = evidence.prevention_rate >= self.thresholds.prevention_rate_min

        # Check recency
        is_recent = True
        if evidence.last_prevention_at:
            days_since = (now - evidence.last_prevention_at).days
            is_recent = days_since <= self.thresholds.downgrade_if_no_prevention_days
        else:
            is_recent = False

        passed = has_min_preventions and has_min_rate

        # Score (0-1)
        rate_score = min(1.0, evidence.prevention_rate / 0.8)  # 80% = perfect
        count_score = min(1.0, evidence.total_preventions / 10)  # 10 = perfect
        score = (rate_score + count_score) / 2

        # Degradation check
        degraded = (
            self._last_status is not None
            and self._last_status.gates.get("prevention", GateEvidence("", False, 0, {}, now, False)).passed
            and not passed
        )

        return GateEvidence(
            name="Prevention Proof",
            passed=passed,
            score=score,
            evidence={
                "total_preventions": evidence.total_preventions,
                "prevention_rate": f"{evidence.prevention_rate:.1%}",
                "last_prevention": evidence.last_prevention_at.isoformat() if evidence.last_prevention_at else None,
                "is_recent": is_recent,
            },
            last_evaluated=now,
            degraded=degraded,
        )

    def _evaluate_gate2(self, evidence: GraduationEvidence) -> GateEvidence:
        """Gate 2: Regret Rollback"""
        now = datetime.now(timezone.utc)

        # Check thresholds
        has_min_demotions = evidence.total_auto_demotions >= self.thresholds.min_auto_demotions
        regret_under_control = evidence.regret_rate <= self.thresholds.max_regret_rate

        passed = has_min_demotions and regret_under_control

        # Score
        demotion_score = min(1.0, evidence.total_auto_demotions / 3)  # 3 = good signal
        regret_score = 1.0 - min(1.0, evidence.regret_rate / 0.3)  # Lower is better
        score = (demotion_score + regret_score) / 2

        # Degradation check
        degraded = (
            self._last_status is not None
            and self._last_status.gates.get("rollback", GateEvidence("", False, 0, {}, now, False)).passed
            and not passed
        )

        return GateEvidence(
            name="Regret Rollback",
            passed=passed,
            score=score,
            evidence={
                "total_auto_demotions": evidence.total_auto_demotions,
                "total_regret_events": evidence.total_regret_events,
                "regret_rate": f"{evidence.regret_rate:.1%}",
                "regret_under_control": regret_under_control,
            },
            last_evaluated=now,
            degraded=degraded,
        )

    def _evaluate_gate3(self, evidence: GraduationEvidence) -> GateEvidence:
        """Gate 3: Console Timeline"""
        now = datetime.now(timezone.utc)

        # Check thresholds
        has_min_views = evidence.timeline_views_with_prevention >= self.thresholds.min_timeline_views

        passed = has_min_views

        # Score
        score = min(1.0, evidence.timeline_views_with_prevention / 5)  # 5 = good adoption

        # Degradation check
        degraded = (
            self._last_status is not None
            and self._last_status.gates.get("timeline", GateEvidence("", False, 0, {}, now, False)).passed
            and not passed
        )

        return GateEvidence(
            name="Console Timeline",
            passed=passed,
            score=score,
            evidence={
                "timeline_views_with_prevention": evidence.timeline_views_with_prevention,
                "last_view": evidence.last_timeline_view_at.isoformat() if evidence.last_timeline_view_at else None,
            },
            last_evaluated=now,
            degraded=degraded,
        )

    def _check_degradation(
        self,
        previous_level: GraduationLevel,
        current_level: GraduationLevel,
        gates: dict[str, GateEvidence],
        evidence: GraduationEvidence,
    ) -> Optional[dict]:
        """
        Check if graduation should be degraded.

        Degradation happens when:
        1. A previously passing gate now fails
        2. Evidence metrics drop below thresholds
        3. Extended period with no evidence
        """
        # Can't degrade from alpha
        if previous_level == GraduationLevel.ALPHA:
            return None

        # Check prevention rate collapse
        if evidence.prevention_rate < self.thresholds.downgrade_if_prevention_rate_below:
            return {
                "from": previous_level,
                "reason": f"Prevention rate dropped to {evidence.prevention_rate:.1%} (threshold: {self.thresholds.downgrade_if_prevention_rate_below:.1%})",
            }

        # Check regret rate spike
        if evidence.regret_rate > self.thresholds.downgrade_if_regret_rate_above:
            return {
                "from": previous_level,
                "reason": f"Regret rate spiked to {evidence.regret_rate:.1%} (threshold: {self.thresholds.downgrade_if_regret_rate_above:.1%})",
            }

        # Check for stale evidence (no prevention in N days)
        if evidence.last_prevention_at:
            now = datetime.now(timezone.utc)
            days_since = (now - evidence.last_prevention_at).days
            if days_since > self.thresholds.downgrade_if_no_prevention_days:
                return {
                    "from": previous_level,
                    "reason": f"No prevention in {days_since} days (threshold: {self.thresholds.downgrade_if_no_prevention_days})",
                }

        # Check if any gate degraded
        for name, gate in gates.items():
            if gate.degraded:
                return {
                    "from": previous_level,
                    "reason": f"Gate '{name}' no longer passing",
                }

        return None


# =============================================================================
# CAPABILITY GATES (Graduation unlocks features)
# =============================================================================

@dataclass
class CapabilityGates:
    """
    Capabilities that are LOCKED until graduation passes specific gates.

    This makes graduation meaningful, not decorative.
    """

    @staticmethod
    def can_auto_apply_recovery(status: ComputedGraduationStatus) -> bool:
        """
        Gate 1 required: Auto-apply recovery only after prevention proven.

        Rationale: Until we've proven a policy can prevent recurrence,
        auto-applying recoveries is gambling.
        """
        gate1 = status.gates.get("prevention")
        return gate1 is not None and gate1.passed

    @staticmethod
    def can_auto_activate_policy(status: ComputedGraduationStatus) -> bool:
        """
        Gate 2 required: Auto-activate policies only after self-correction proven.

        Rationale: Until we've proven the system can demote harmful policies,
        auto-activation is dangerous.
        """
        gate2 = status.gates.get("rollback")
        return gate2 is not None and gate2.passed

    @staticmethod
    def can_full_auto_routing(status: ComputedGraduationStatus) -> bool:
        """
        All gates required: Full autonomous routing only after proven.

        Rationale: CARE routing changes require full confidence.
        """
        return status.is_graduated

    @staticmethod
    def get_blocked_capabilities(status: ComputedGraduationStatus) -> list[str]:
        """Get list of currently blocked capabilities."""
        blocked = []

        if not CapabilityGates.can_auto_apply_recovery(status):
            blocked.append("auto_apply_recovery")

        if not CapabilityGates.can_auto_activate_policy(status):
            blocked.append("auto_activate_policy")

        if not CapabilityGates.can_full_auto_routing(status):
            blocked.append("full_auto_routing")

        return blocked

    @staticmethod
    def get_unlocked_capabilities(status: ComputedGraduationStatus) -> list[str]:
        """Get list of currently unlocked capabilities."""
        unlocked = []

        if CapabilityGates.can_auto_apply_recovery(status):
            unlocked.append("auto_apply_recovery")

        if CapabilityGates.can_auto_activate_policy(status):
            unlocked.append("auto_activate_policy")

        if CapabilityGates.can_full_auto_routing(status):
            unlocked.append("full_auto_routing")

        return unlocked


# =============================================================================
# SIMULATION ISOLATION (Keep demo separate from real)
# =============================================================================

@dataclass
class SimulationState:
    """
    Simulation state - SEPARATE from real graduation.

    Simulations are for demos only. They never affect real graduation.
    """
    simulated_gate1: bool = False
    simulated_gate2: bool = False
    simulated_gate3: bool = False
    simulated_at: Optional[datetime] = None

    @property
    def is_demo_mode(self) -> bool:
        """True if any simulation is active."""
        return self.simulated_gate1 or self.simulated_gate2 or self.simulated_gate3

    def to_display(self) -> dict:
        """Display format - clearly marked as simulation."""
        return {
            "is_demo_mode": self.is_demo_mode,
            "simulated_gates": {
                "gate1": self.simulated_gate1,
                "gate2": self.simulated_gate2,
                "gate3": self.simulated_gate3,
            },
            "warning": "SIMULATION MODE - This does not reflect real graduation" if self.is_demo_mode else None,
        }


# =============================================================================
# PERIODIC RE-EVALUATION
# =============================================================================

async def evaluate_graduation_status(
    session,
    engine: Optional[GraduationEngine] = None,
    previous_status: Optional[ComputedGraduationStatus] = None,
) -> ComputedGraduationStatus:
    """
    Evaluate graduation status from database evidence.

    This should be called:
    1. On API request (cached for 1 minute)
    2. Periodically by background job (every 5 minutes)
    3. After significant events (prevention, regret, demotion)
    """
    if engine is None:
        engine = GraduationEngine()

    # Fetch evidence from database
    evidence = await GraduationEvidence.fetch_from_database(session)

    # Compute status
    status = engine.compute(evidence, previous_status)

    # Log degradation
    if status.is_degraded:
        logger.warning(
            f"M25 graduation DEGRADED: {status.degraded_from} -> DEGRADED. "
            f"Reason: {status.degradation_reason}"
        )

    return status


async def persist_graduation_status(session, status: ComputedGraduationStatus) -> None:
    """
    Persist graduation status to database for historical tracking.

    Note: This is for AUDIT/HISTORY only. The real status is always
    computed fresh from evidence.
    """
    from sqlalchemy import text

    await session.execute(
        text("""
            INSERT INTO graduation_history (
                level, gates_json, computed_at,
                is_degraded, degraded_from, degradation_reason
            ) VALUES (
                :level, :gates, :computed_at,
                :is_degraded, :degraded_from, :reason
            )
        """),
        {
            "level": status.level.value,
            "gates": status.to_api_response()["gates"],
            "computed_at": status.computed_at,
            "is_degraded": status.is_degraded,
            "degraded_from": status.degraded_from.value if status.degraded_from else None,
            "reason": status.degradation_reason,
        }
    )
    await session.commit()
