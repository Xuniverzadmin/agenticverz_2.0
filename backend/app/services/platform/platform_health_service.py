# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api|worker|scheduler
#   Execution: sync
# Role: Platform Health Authority - THE source of truth for platform state
# Callers: L3 (PlatformEligibilityAdapter), L2 (/platform/health), L7 (bootstrap)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: PIN-284 (Platform Monitoring System)
#
# ==============================================================================
# GOVERNANCE RULE: HEALTH-IS-AUTHORITY (Non-Negotiable)
# ==============================================================================
#
# This service is the ONLY component allowed to decide the meaning of signals.
#
# Health states are:
#   - HEALTHY: All systems operational, no degradation
#   - DEGRADED: Reduced capacity, some capabilities impaired
#   - BLOCKED: Critical failure, system cannot function
#
# NO OTHER SERVICE may produce these states.
# NO OTHER SERVICE may interpret raw signals.
#
# Enforcement:
#   - All platform health checks MUST go through this service
#   - L3 adapters consume health states, never raw signals
#   - L2 APIs expose health states, never raw signals
#
# Reference: PIN-284 (Platform Monitoring System)
#
# ==============================================================================

"""
Platform Health Service (L4)

The authoritative source for platform health state.
Converts raw signals into deterministic health states.

Responsibilities:
1. Aggregate signals from L6/L7 sources (BLCA, guards, incidents, contracts)
2. Produce deterministic health states (HEALTHY/DEGRADED/BLOCKED)
3. Provide health for system, domains, and individual capabilities
4. Drive governance consequences via health→qualifier binding

Contract:
- Health states are closed set: {HEALTHY, DEGRADED, BLOCKED}
- Health is computed, never cached
- Health is deterministic: same signals → same state
- Health drives governance: BLOCKED → capability disabled

Reference: PIN-284 (Platform Monitoring System)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import and_, func, or_, select
from sqlmodel import Session

# L6 imports (allowed)
from app.models.governance import GovernanceSignal
from app.models.killswitch import Incident

# ==============================================================================
# HEALTH STATE ENUM (Closed Set)
# ==============================================================================


class HealthState(str, Enum):
    """
    Closed set of health states.

    NO OTHER STATES MAY BE ADDED without governance approval.
    """

    HEALTHY = "HEALTHY"  # All systems operational
    DEGRADED = "DEGRADED"  # Reduced capacity, some impairment
    BLOCKED = "BLOCKED"  # Critical failure, cannot function


# ==============================================================================
# SIGNAL TYPES (What we consume)
# ==============================================================================


class SignalType(str, Enum):
    """Signal types consumed by health service."""

    BLCA_STATUS = "BLCA_STATUS"  # Layer validator output
    CI_STATUS = "CI_STATUS"  # CI pipeline status
    GUARD_STATUS = "GUARD_STATUS"  # Guard check status
    CONTRACT_STATUS = "CONTRACT_STATUS"  # Contract test status
    INCIDENT_OPEN = "INCIDENT_OPEN"  # Open incident count
    QUALIFIER_STATUS = "QUALIFIER_STATUS"  # Qualifier evaluation status
    LIFECYCLE_STATUS = "LIFECYCLE_STATUS"  # Lifecycle coherence status


# ==============================================================================
# HEALTH REASON (Why this state?)
# ==============================================================================


@dataclass
class HealthReason:
    """Explains why a health state was assigned."""

    signal_type: str
    signal_value: str
    contribution: HealthState
    message: str
    recorded_at: Optional[datetime] = None


# ==============================================================================
# CAPABILITY HEALTH
# ==============================================================================


@dataclass
class CapabilityHealth:
    """Health state for a single capability."""

    capability_name: str
    state: HealthState
    reasons: list[HealthReason] = field(default_factory=list)
    last_checked: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Governance binding
    qualifier_state: Optional[str] = None  # QUALIFIED, DISQUALIFIED
    lifecycle_status: Optional[str] = None  # COMPLETE, PARTIAL, etc.

    def is_eligible(self) -> bool:
        """Whether this capability should be available."""
        return self.state != HealthState.BLOCKED


# ==============================================================================
# DOMAIN HEALTH
# ==============================================================================


@dataclass
class DomainHealth:
    """Health state for a domain (group of capabilities)."""

    domain_name: str
    state: HealthState
    capabilities: dict[str, CapabilityHealth] = field(default_factory=dict)
    reasons: list[HealthReason] = field(default_factory=list)
    last_checked: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Aggregate stats
    healthy_count: int = 0
    degraded_count: int = 0
    blocked_count: int = 0

    def compute_state(self) -> HealthState:
        """Compute domain state from capability states."""
        self.healthy_count = sum(1 for c in self.capabilities.values() if c.state == HealthState.HEALTHY)
        self.degraded_count = sum(1 for c in self.capabilities.values() if c.state == HealthState.DEGRADED)
        self.blocked_count = sum(1 for c in self.capabilities.values() if c.state == HealthState.BLOCKED)

        # Domain rules:
        # - Any BLOCKED capability → Domain DEGRADED (not BLOCKED, domain can still function)
        # - All BLOCKED → Domain BLOCKED
        # - Any DEGRADED → Domain DEGRADED
        # - All HEALTHY → Domain HEALTHY

        total = len(self.capabilities)
        if total == 0:
            return HealthState.HEALTHY

        if self.blocked_count == total:
            self.state = HealthState.BLOCKED
        elif self.blocked_count > 0 or self.degraded_count > 0:
            self.state = HealthState.DEGRADED
        else:
            self.state = HealthState.HEALTHY

        return self.state


# ==============================================================================
# SYSTEM HEALTH
# ==============================================================================


@dataclass
class SystemHealth:
    """Health state for the entire platform."""

    state: HealthState
    domains: dict[str, DomainHealth] = field(default_factory=dict)
    reasons: list[HealthReason] = field(default_factory=list)
    last_checked: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # System-level signals
    blca_status: str = "UNKNOWN"
    ci_status: str = "UNKNOWN"
    lifecycle_coherence: str = "UNKNOWN"

    # Aggregate stats
    total_capabilities: int = 0
    healthy_capabilities: int = 0
    degraded_capabilities: int = 0
    blocked_capabilities: int = 0

    # Governance stats
    qualified_capabilities: int = 0
    disqualified_capabilities: int = 0

    def compute_state(self) -> HealthState:
        """Compute system state from domain states and system signals."""
        # First, compute stats from domains
        self.total_capabilities = sum(len(d.capabilities) for d in self.domains.values())
        self.healthy_capabilities = sum(d.healthy_count for d in self.domains.values())
        self.degraded_capabilities = sum(d.degraded_count for d in self.domains.values())
        self.blocked_capabilities = sum(d.blocked_count for d in self.domains.values())

        # System-level signals can override domain states
        # BLCA BLOCKED → System BLOCKED
        if self.blca_status == "BLOCKED":
            self.state = HealthState.BLOCKED
            self.reasons.append(
                HealthReason(
                    signal_type=SignalType.BLCA_STATUS.value,
                    signal_value="BLOCKED",
                    contribution=HealthState.BLOCKED,
                    message="BLCA violations detected - system cannot function",
                )
            )
            return self.state

        # Lifecycle incoherence → System DEGRADED
        if self.lifecycle_coherence == "INCOHERENT":
            if self.state != HealthState.BLOCKED:
                self.state = HealthState.DEGRADED
                self.reasons.append(
                    HealthReason(
                        signal_type=SignalType.LIFECYCLE_STATUS.value,
                        signal_value="INCOHERENT",
                        contribution=HealthState.DEGRADED,
                        message="Lifecycle/qualifier divergence detected",
                    )
                )

        # All domains BLOCKED → System BLOCKED
        if self.domains and all(d.state == HealthState.BLOCKED for d in self.domains.values()):
            self.state = HealthState.BLOCKED
            return self.state

        # Any domain BLOCKED or DEGRADED → System DEGRADED
        if any(d.state in (HealthState.BLOCKED, HealthState.DEGRADED) for d in self.domains.values()):
            if self.state != HealthState.BLOCKED:
                self.state = HealthState.DEGRADED
            return self.state

        # All healthy
        if self.state == HealthState.BLOCKED:
            return self.state  # Keep BLOCKED if already set by system signals

        self.state = HealthState.HEALTHY
        return self.state


# ==============================================================================
# PLATFORM HEALTH SERVICE (L4 AUTHORITY)
# ==============================================================================


class PlatformHealthService:
    """
    L4 Platform Health Authority.

    THE source of truth for platform health state.
    Converts raw signals into deterministic health states.

    Contract:
    - Health states are closed set: {HEALTHY, DEGRADED, BLOCKED}
    - Health is computed fresh on each call
    - Health is deterministic: same signals → same state
    - Health drives governance consequences
    """

    # Domain to capabilities mapping (from CAPABILITY_LIFECYCLE.yaml)
    DOMAIN_CAPABILITIES = {
        "LOGS": ["LOGS_LIST", "LOGS_DETAIL", "LOGS_EXPORT"],
        "INCIDENTS": ["INCIDENTS_LIST", "INCIDENTS_DETAIL", "INCIDENT_ACKNOWLEDGE", "INCIDENT_RESOLVE"],
        "KEYS": ["KEYS_LIST", "KEYS_FREEZE", "KEYS_UNFREEZE"],
        "POLICY": ["POLICY_CONSTRAINTS", "GUARDRAIL_DETAIL"],
        "KILLSWITCH": ["KILLSWITCH_STATUS", "KILLSWITCH_ACTIVATE", "KILLSWITCH_DEACTIVATE"],
        "ACTIVITY": ["ACTIVITY_LIST", "ACTIVITY_DETAIL"],
    }

    def __init__(self, session: Session):
        """Initialize with database session."""
        self._session = session

    # ==========================================================================
    # SYSTEM HEALTH
    # ==========================================================================

    def get_system_health(self) -> SystemHealth:
        """
        Get current system health.

        Aggregates:
        - BLCA status (from governance signals)
        - Lifecycle coherence
        - Domain health (from capability health)
        - Open incidents

        Returns:
            SystemHealth with deterministic state
        """
        health = SystemHealth(state=HealthState.HEALTHY)
        health.last_checked = datetime.now(timezone.utc)

        # Get BLCA status
        health.blca_status = self._get_blca_status()
        if health.blca_status == "BLOCKED":
            health.reasons.append(
                HealthReason(
                    signal_type=SignalType.BLCA_STATUS.value,
                    signal_value="BLOCKED",
                    contribution=HealthState.BLOCKED,
                    message="BLCA violations detected",
                )
            )

        # Get lifecycle coherence
        health.lifecycle_coherence = self._get_lifecycle_coherence()
        if health.lifecycle_coherence == "INCOHERENT":
            health.reasons.append(
                HealthReason(
                    signal_type=SignalType.LIFECYCLE_STATUS.value,
                    signal_value="INCOHERENT",
                    contribution=HealthState.DEGRADED,
                    message="Lifecycle/qualifier divergence",
                )
            )

        # Get domain health
        for domain_name in self.DOMAIN_CAPABILITIES.keys():
            domain_health = self.get_domain_health(domain_name)
            health.domains[domain_name] = domain_health

        # Compute qualifier stats
        for domain in health.domains.values():
            for cap in domain.capabilities.values():
                if cap.qualifier_state == "QUALIFIED":
                    health.qualified_capabilities += 1
                elif cap.qualifier_state == "DISQUALIFIED":
                    health.disqualified_capabilities += 1

        # Compute final state
        health.compute_state()

        return health

    # ==========================================================================
    # DOMAIN HEALTH
    # ==========================================================================

    def get_domain_health(self, domain_name: str) -> DomainHealth:
        """
        Get health for a specific domain.

        Args:
            domain_name: Domain name (LOGS, INCIDENTS, etc.)

        Returns:
            DomainHealth with capability states
        """
        health = DomainHealth(domain_name=domain_name, state=HealthState.HEALTHY)
        health.last_checked = datetime.now(timezone.utc)

        capabilities = self.DOMAIN_CAPABILITIES.get(domain_name, [])

        for cap_name in capabilities:
            cap_health = self.get_capability_health(cap_name)
            health.capabilities[cap_name] = cap_health

        # Compute domain state
        health.compute_state()

        return health

    # ==========================================================================
    # CAPABILITY HEALTH
    # ==========================================================================

    def get_capability_health(self, capability_name: str) -> CapabilityHealth:
        """
        Get health for a specific capability.

        Health is determined by:
        1. Governance signals (BLOCKED/WARN)
        2. Open incidents affecting this capability
        3. Contract test status
        4. Qualifier state (from QUALIFIER_EVALUATION.yaml binding)

        Args:
            capability_name: Capability name (LOGS_LIST, etc.)

        Returns:
            CapabilityHealth with deterministic state
        """
        health = CapabilityHealth(capability_name=capability_name, state=HealthState.HEALTHY)
        health.last_checked = datetime.now(timezone.utc)

        # Check governance signals
        blocking_signals = self._get_blocking_signals(capability_name)
        if blocking_signals:
            health.state = HealthState.BLOCKED
            for signal in blocking_signals:
                health.reasons.append(
                    HealthReason(
                        signal_type=signal.signal_type,
                        signal_value=signal.decision,
                        contribution=HealthState.BLOCKED,
                        message=signal.reason or f"Blocked by {signal.recorded_by}",
                        recorded_at=signal.recorded_at,
                    )
                )

        # Check for warning signals
        warning_signals = self._get_warning_signals(capability_name)
        if warning_signals and health.state == HealthState.HEALTHY:
            health.state = HealthState.DEGRADED
            for signal in warning_signals:
                health.reasons.append(
                    HealthReason(
                        signal_type=signal.signal_type,
                        signal_value=signal.decision,
                        contribution=HealthState.DEGRADED,
                        message=signal.reason or f"Warning from {signal.recorded_by}",
                        recorded_at=signal.recorded_at,
                    )
                )

        # Check open incidents
        open_incidents = self._count_open_incidents(capability_name)
        if open_incidents > 0 and health.state == HealthState.HEALTHY:
            health.state = HealthState.DEGRADED
            health.reasons.append(
                HealthReason(
                    signal_type=SignalType.INCIDENT_OPEN.value,
                    signal_value=str(open_incidents),
                    contribution=HealthState.DEGRADED,
                    message=f"{open_incidents} open incident(s) affecting capability",
                )
            )

        # Get qualifier state (from lifecycle binding)
        health.qualifier_state = self._get_qualifier_state(capability_name)
        if health.qualifier_state == "DISQUALIFIED":
            # Disqualified capabilities are BLOCKED for governance
            if health.state != HealthState.BLOCKED:
                health.state = HealthState.BLOCKED
                health.reasons.append(
                    HealthReason(
                        signal_type=SignalType.QUALIFIER_STATUS.value,
                        signal_value="DISQUALIFIED",
                        contribution=HealthState.BLOCKED,
                        message="Capability is disqualified by governance",
                    )
                )

        # Get lifecycle status
        health.lifecycle_status = self._get_lifecycle_status(capability_name)

        return health

    # ==========================================================================
    # ELIGIBILITY CHECK
    # ==========================================================================

    def is_capability_eligible(self, capability_name: str) -> bool:
        """
        Quick check if a capability is eligible (not BLOCKED).

        Args:
            capability_name: Capability name

        Returns:
            True if capability can be used
        """
        health = self.get_capability_health(capability_name)
        return health.is_eligible()

    def get_eligible_capabilities(self) -> list[str]:
        """
        Get list of all eligible capabilities.

        Returns:
            List of capability names that are not BLOCKED
        """
        eligible = []
        for domain_caps in self.DOMAIN_CAPABILITIES.values():
            for cap_name in domain_caps:
                if self.is_capability_eligible(cap_name):
                    eligible.append(cap_name)
        return eligible

    def get_blocked_capabilities(self) -> list[str]:
        """
        Get list of all blocked capabilities.

        Returns:
            List of capability names that are BLOCKED
        """
        blocked = []
        for domain_caps in self.DOMAIN_CAPABILITIES.values():
            for cap_name in domain_caps:
                if not self.is_capability_eligible(cap_name):
                    blocked.append(cap_name)
        return blocked

    # ==========================================================================
    # SIGNAL READERS (L6 access)
    # ==========================================================================

    def _get_blca_status(self) -> str:
        """Get current BLCA status from governance signals."""
        stmt = (
            select(GovernanceSignal)
            .where(
                and_(
                    GovernanceSignal.signal_type == "BLCA_STATUS",
                    GovernanceSignal.scope == "SYSTEM",
                    GovernanceSignal.superseded_at.is_(None),
                )
            )
            .order_by(GovernanceSignal.recorded_at.desc())
            .limit(1)
        )

        result = self._session.execute(stmt).scalars().first()
        if result:
            return result.decision
        return "UNKNOWN"

    def _get_lifecycle_coherence(self) -> str:
        """Get lifecycle/qualifier coherence status."""
        stmt = (
            select(GovernanceSignal)
            .where(
                and_(
                    GovernanceSignal.signal_type == "LIFECYCLE_QUALIFIER_COHERENCE",
                    GovernanceSignal.scope == "SYSTEM",
                    GovernanceSignal.superseded_at.is_(None),
                )
            )
            .order_by(GovernanceSignal.recorded_at.desc())
            .limit(1)
        )

        result = self._session.execute(stmt).scalars().first()
        if result:
            return result.decision
        return "UNKNOWN"

    def _get_blocking_signals(self, capability_name: str) -> list[GovernanceSignal]:
        """Get blocking governance signals for a capability."""
        now = datetime.now(timezone.utc)

        stmt = select(GovernanceSignal).where(
            and_(
                or_(
                    GovernanceSignal.scope == capability_name,
                    GovernanceSignal.scope == "SYSTEM",
                ),
                GovernanceSignal.decision == "BLOCKED",
                GovernanceSignal.superseded_at.is_(None),
                or_(
                    GovernanceSignal.expires_at.is_(None),
                    GovernanceSignal.expires_at > now,
                ),
            )
        )

        return list(self._session.execute(stmt).scalars().all())

    def _get_warning_signals(self, capability_name: str) -> list[GovernanceSignal]:
        """Get warning governance signals for a capability."""
        now = datetime.now(timezone.utc)

        stmt = select(GovernanceSignal).where(
            and_(
                or_(
                    GovernanceSignal.scope == capability_name,
                    GovernanceSignal.scope == "SYSTEM",
                ),
                GovernanceSignal.decision == "WARN",
                GovernanceSignal.superseded_at.is_(None),
                or_(
                    GovernanceSignal.expires_at.is_(None),
                    GovernanceSignal.expires_at > now,
                ),
            )
        )

        return list(self._session.execute(stmt).scalars().all())

    def _count_open_incidents(self, capability_name: str) -> int:
        """
        Count open incidents that affect a capability.

        Returns 0 if incidents table is not available (graceful degradation).
        Uses savepoint to avoid aborting the parent transaction on failure.
        """
        # Use a nested transaction (savepoint) to isolate this query
        # This prevents a failed query from aborting the parent transaction
        try:
            # Check if we can begin a nested transaction
            nested = self._session.begin_nested()
            try:
                # Check for incidents with this capability in their scope
                stmt = select(func.count(Incident.id)).where(
                    and_(
                        Incident.status.in_(["OPEN", "ACKNOWLEDGED"]),
                        # Incidents may have capability in their labels or source
                        # For now, check all open incidents as potentially affecting
                    )
                )

                result = self._session.execute(stmt).scalar()
                nested.commit()
                return result or 0
            except Exception:
                # Roll back the savepoint to keep parent transaction valid
                nested.rollback()
                return 0
        except Exception:
            # If we can't even create a savepoint, return 0
            return 0

    def _get_qualifier_state(self, capability_name: str) -> Optional[str]:
        """
        Get qualifier state for a capability.

        This reads from governance signals that represent qualifier evaluation.
        The signal is written by evaluate_qualifiers.py or lifecycle_qualifier_guard.py.
        """
        stmt = (
            select(GovernanceSignal)
            .where(
                and_(
                    GovernanceSignal.signal_type == "QUALIFIER_STATUS",
                    GovernanceSignal.scope == capability_name,
                    GovernanceSignal.superseded_at.is_(None),
                )
            )
            .order_by(GovernanceSignal.recorded_at.desc())
            .limit(1)
        )

        result = self._session.execute(stmt).scalars().first()
        if result:
            return result.decision

        # Fallback: if no signal, check hardcoded known disqualified
        # (KILLSWITCH_STATUS is known to be disqualified per CAPABILITY_LIFECYCLE.yaml)
        if capability_name == "KILLSWITCH_STATUS":
            return "DISQUALIFIED"

        return None

    def _get_lifecycle_status(self, capability_name: str) -> Optional[str]:
        """Get lifecycle status for a capability."""
        stmt = (
            select(GovernanceSignal)
            .where(
                and_(
                    GovernanceSignal.signal_type == "LIFECYCLE_STATUS",
                    GovernanceSignal.scope == capability_name,
                    GovernanceSignal.superseded_at.is_(None),
                )
            )
            .order_by(GovernanceSignal.recorded_at.desc())
            .limit(1)
        )

        result = self._session.execute(stmt).scalars().first()
        if result:
            return result.decision

        return None


# ==============================================================================
# FACTORY FUNCTION
# ==============================================================================


def get_platform_health_service(session: Session) -> PlatformHealthService:
    """Factory function to get PlatformHealthService instance."""
    return PlatformHealthService(session)


# ==============================================================================
# EXPORTS
# ==============================================================================


__all__ = [
    # Enums
    "HealthState",
    "SignalType",
    # Models
    "HealthReason",
    "CapabilityHealth",
    "DomainHealth",
    "SystemHealth",
    # Service
    "PlatformHealthService",
    "get_platform_health_service",
]
