# Layer: L4 — Domain Engine
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api|worker|scheduler
#   Execution: sync
# Role: Platform Health Authority - THE source of truth for platform state
# Callers: L3 (PlatformEligibilityAdapter), L2 (/platform/health), L7 (bootstrap)
# Allowed Imports: L6 drivers (via injection)
# Forbidden Imports: sqlalchemy, sqlmodel, app.models
# Reference: PIN-468, DRIVER_ENGINE_CONTRACT.md, PIN-284
#
# ==============================================================================
# GOVERNANCE RULE: HEALTH-IS-AUTHORITY (Non-Negotiable)
# ==============================================================================
#
# This engine is the ONLY component allowed to decide the meaning of signals.
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
#   - All platform health checks MUST go through this engine
#   - L3 adapters consume health states, never raw signals
#   - L2 APIs expose health states, never raw signals
#
# ==============================================================================

"""Platform Health Engine

L4 engine for platform health decisions.

Decides: Health state interpretation, thresholds, aggregation rules
Delegates: All data access to PlatformHealthDriver

Responsibilities:
1. Aggregate signals from driver
2. Produce deterministic health states (HEALTHY/DEGRADED/BLOCKED)
3. Provide health for system, domains, and individual capabilities
4. Drive governance consequences via health→qualifier binding

Contract:
- Health states are closed set: {HEALTHY, DEGRADED, BLOCKED}
- Health is computed, never cached
- Health is deterministic: same signals → same state
- Health drives governance: BLOCKED → capability disabled
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Optional

from app.services.platform.platform_health_driver import (
    PlatformHealthDriver,
    SignalRow,
    get_platform_health_driver,
)

if TYPE_CHECKING:
    from sqlmodel import Session


# ==============================================================================
# HEALTH STATE ENUM (Closed Set)
# ==============================================================================


class HealthState(str, Enum):
    """Closed set of health states.

    NO OTHER STATES MAY BE ADDED without governance approval.
    """

    HEALTHY = "HEALTHY"  # All systems operational
    DEGRADED = "DEGRADED"  # Reduced capacity, some impairment
    BLOCKED = "BLOCKED"  # Critical failure, cannot function


# ==============================================================================
# SIGNAL TYPES (What we consume)
# ==============================================================================


class SignalType(str, Enum):
    """Signal types consumed by health engine."""

    BLCA_STATUS = "BLCA_STATUS"
    CI_STATUS = "CI_STATUS"
    GUARD_STATUS = "GUARD_STATUS"
    CONTRACT_STATUS = "CONTRACT_STATUS"
    INCIDENT_OPEN = "INCIDENT_OPEN"
    QUALIFIER_STATUS = "QUALIFIER_STATUS"
    LIFECYCLE_STATUS = "LIFECYCLE_STATUS"


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
    qualifier_state: Optional[str] = None
    lifecycle_status: Optional[str] = None

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
        """Compute domain state from capability states.

        DECISION LOGIC:
        - Any BLOCKED capability → Domain DEGRADED (domain can still function)
        - All BLOCKED → Domain BLOCKED
        - Any DEGRADED → Domain DEGRADED
        - All HEALTHY → Domain HEALTHY
        """
        self.healthy_count = sum(
            1 for c in self.capabilities.values() if c.state == HealthState.HEALTHY
        )
        self.degraded_count = sum(
            1 for c in self.capabilities.values() if c.state == HealthState.DEGRADED
        )
        self.blocked_count = sum(
            1 for c in self.capabilities.values() if c.state == HealthState.BLOCKED
        )

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
        """Compute system state from domain states and system signals.

        DECISION LOGIC:
        - BLCA BLOCKED → System BLOCKED
        - Lifecycle INCOHERENT → System DEGRADED
        - All domains BLOCKED → System BLOCKED
        - Any domain BLOCKED or DEGRADED → System DEGRADED
        - All healthy → System HEALTHY
        """
        # Compute stats from domains
        self.total_capabilities = sum(len(d.capabilities) for d in self.domains.values())
        self.healthy_capabilities = sum(d.healthy_count for d in self.domains.values())
        self.degraded_capabilities = sum(d.degraded_count for d in self.domains.values())
        self.blocked_capabilities = sum(d.blocked_count for d in self.domains.values())

        # DECISION: BLCA BLOCKED → System BLOCKED
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

        # DECISION: Lifecycle INCOHERENT → System DEGRADED
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

        # DECISION: All domains BLOCKED → System BLOCKED
        if self.domains and all(
            d.state == HealthState.BLOCKED for d in self.domains.values()
        ):
            self.state = HealthState.BLOCKED
            return self.state

        # DECISION: Any domain BLOCKED or DEGRADED → System DEGRADED
        if any(
            d.state in (HealthState.BLOCKED, HealthState.DEGRADED)
            for d in self.domains.values()
        ):
            if self.state != HealthState.BLOCKED:
                self.state = HealthState.DEGRADED
            return self.state

        # DECISION: All healthy
        if self.state == HealthState.BLOCKED:
            return self.state

        self.state = HealthState.HEALTHY
        return self.state


# ==============================================================================
# PLATFORM HEALTH ENGINE (L4 AUTHORITY)
# ==============================================================================


class PlatformHealthEngine:
    """L4 Platform Health Authority.

    THE source of truth for platform health state.
    Converts raw signals into deterministic health states.

    Decides: Health state interpretation, thresholds, aggregation
    Delegates: All data access to PlatformHealthDriver
    """

    # Domain to capabilities mapping (from CAPABILITY_LIFECYCLE.yaml)
    DOMAIN_CAPABILITIES = {
        "LOGS": ["LOGS_LIST", "LOGS_DETAIL", "LOGS_EXPORT"],
        "INCIDENTS": [
            "INCIDENTS_LIST",
            "INCIDENTS_DETAIL",
            "INCIDENT_ACKNOWLEDGE",
            "INCIDENT_RESOLVE",
        ],
        "KEYS": ["KEYS_LIST", "KEYS_FREEZE", "KEYS_UNFREEZE"],
        "POLICY": ["POLICY_CONSTRAINTS", "GUARDRAIL_DETAIL"],
        "KILLSWITCH": [
            "KILLSWITCH_STATUS",
            "KILLSWITCH_ACTIVATE",
            "KILLSWITCH_DEACTIVATE",
        ],
        "ACTIVITY": ["ACTIVITY_LIST", "ACTIVITY_DETAIL"],
    }

    # Known disqualified capabilities (hardcoded fallback)
    KNOWN_DISQUALIFIED = {"KILLSWITCH_STATUS"}

    def __init__(self, driver: PlatformHealthDriver):
        """Initialize engine with driver.

        Args:
            driver: PlatformHealthDriver instance for data access
        """
        self._driver = driver

    # ==========================================================================
    # SYSTEM HEALTH
    # ==========================================================================

    def get_system_health(self) -> SystemHealth:
        """Get current system health.

        Aggregates:
        - BLCA status
        - Lifecycle coherence
        - Domain health
        - Open incidents

        Returns:
            SystemHealth with deterministic state
        """
        health = SystemHealth(state=HealthState.HEALTHY)
        health.last_checked = datetime.now(timezone.utc)

        # Fetch BLCA status
        blca = self._driver.fetch_blca_status()
        health.blca_status = blca or "UNKNOWN"
        if health.blca_status == "BLOCKED":
            health.reasons.append(
                HealthReason(
                    signal_type=SignalType.BLCA_STATUS.value,
                    signal_value="BLOCKED",
                    contribution=HealthState.BLOCKED,
                    message="BLCA violations detected",
                )
            )

        # Fetch lifecycle coherence
        coherence = self._driver.fetch_lifecycle_coherence()
        health.lifecycle_coherence = coherence or "UNKNOWN"
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
        """Get health for a specific domain.

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
        """Get health for a specific capability.

        DECISION LOGIC:
        1. Blocking signals → BLOCKED
        2. Warning signals → DEGRADED
        3. Open incidents → DEGRADED
        4. Disqualified → BLOCKED
        5. Otherwise → HEALTHY

        Args:
            capability_name: Capability name (LOGS_LIST, etc.)

        Returns:
            CapabilityHealth with deterministic state
        """
        health = CapabilityHealth(
            capability_name=capability_name, state=HealthState.HEALTHY
        )
        health.last_checked = datetime.now(timezone.utc)

        # DECISION 1: Check blocking signals
        blocking_signals = self._driver.fetch_blocking_signals(capability_name)
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

        # DECISION 2: Check warning signals
        if health.state == HealthState.HEALTHY:
            warning_signals = self._driver.fetch_warning_signals(capability_name)
            if warning_signals:
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

        # DECISION 3: Check open incidents
        if health.state == HealthState.HEALTHY:
            open_incidents = self._driver.fetch_open_incident_count(capability_name)
            if open_incidents > 0:
                health.state = HealthState.DEGRADED
                health.reasons.append(
                    HealthReason(
                        signal_type=SignalType.INCIDENT_OPEN.value,
                        signal_value=str(open_incidents),
                        contribution=HealthState.DEGRADED,
                        message=f"{open_incidents} open incident(s) affecting capability",
                    )
                )

        # Fetch qualifier state
        qualifier = self._driver.fetch_qualifier_state(capability_name)
        if qualifier:
            health.qualifier_state = qualifier
        elif capability_name in self.KNOWN_DISQUALIFIED:
            health.qualifier_state = "DISQUALIFIED"

        # DECISION 4: Disqualified → BLOCKED
        if health.qualifier_state == "DISQUALIFIED":
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

        # Fetch lifecycle status
        health.lifecycle_status = self._driver.fetch_lifecycle_status(capability_name)

        return health

    # ==========================================================================
    # ELIGIBILITY CHECKS
    # ==========================================================================

    def is_capability_eligible(self, capability_name: str) -> bool:
        """Quick check if a capability is eligible (not BLOCKED).

        Args:
            capability_name: Capability name

        Returns:
            True if capability can be used
        """
        health = self.get_capability_health(capability_name)
        return health.is_eligible()

    def get_eligible_capabilities(self) -> list[str]:
        """Get list of all eligible capabilities.

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
        """Get list of all blocked capabilities.

        Returns:
            List of capability names that are BLOCKED
        """
        blocked = []
        for domain_caps in self.DOMAIN_CAPABILITIES.values():
            for cap_name in domain_caps:
                if not self.is_capability_eligible(cap_name):
                    blocked.append(cap_name)
        return blocked


# ==============================================================================
# FACTORY FUNCTION
# ==============================================================================


def get_platform_health_engine(session: "Session") -> PlatformHealthEngine:
    """Factory function to get PlatformHealthEngine instance.

    Args:
        session: SQLModel Session for driver

    Returns:
        PlatformHealthEngine instance
    """
    driver = get_platform_health_driver(session)
    return PlatformHealthEngine(driver=driver)


# ==============================================================================
# BACKWARD COMPATIBILITY
# ==============================================================================

PlatformHealthService = PlatformHealthEngine
get_platform_health_service = get_platform_health_engine

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
    # Engine
    "PlatformHealthEngine",
    "get_platform_health_engine",
    # Backward compatibility
    "PlatformHealthService",
    "get_platform_health_service",
]
