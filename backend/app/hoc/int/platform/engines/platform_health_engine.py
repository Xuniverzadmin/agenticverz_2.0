# capability_id: CAP-012
# Layer: L5 — Engine
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api|worker|scheduler
#   Execution: sync
# Role: Platform Health Authority - THE source of truth for platform state
# Callers: L3 (PlatformEligibilityAdapter), L2 (/platform/health), L7 (bootstrap)
# Allowed Imports: L6 drivers (via injection)
# Forbidden Imports: sqlalchemy, sqlmodel, app.models
# Reference: PIN-468, PIN-513 Phase 7
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
# ==============================================================================

"""Platform Health Engine

L5 engine for platform health decisions.

Decides: Health state interpretation, thresholds, aggregation rules
Delegates: All data access to PlatformHealthDriver

Extracted from app/services/platform/platform_health_engine.py (PIN-513 Phase 7).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Optional

from app.hoc.int.platform.drivers.platform_health_driver import (
    PlatformHealthDriver,
    SignalRow,  # noqa: F401 — re-exported for consumers
    get_platform_health_driver,
)

if TYPE_CHECKING:
    from sqlmodel import Session


# ==============================================================================
# HEALTH STATE ENUM (Closed Set)
# ==============================================================================


class HealthState(str, Enum):
    """Closed set of health states."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    BLOCKED = "BLOCKED"


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
# HEALTH REASON
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

    healthy_count: int = 0
    degraded_count: int = 0
    blocked_count: int = 0

    def compute_state(self) -> HealthState:
        """Compute domain state from capability states."""
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

    blca_status: str = "UNKNOWN"
    ci_status: str = "UNKNOWN"
    lifecycle_coherence: str = "UNKNOWN"

    total_capabilities: int = 0
    healthy_capabilities: int = 0
    degraded_capabilities: int = 0
    blocked_capabilities: int = 0

    qualified_capabilities: int = 0
    disqualified_capabilities: int = 0

    def compute_state(self) -> HealthState:
        """Compute system state from domain states and system signals."""
        self.total_capabilities = sum(len(d.capabilities) for d in self.domains.values())
        self.healthy_capabilities = sum(d.healthy_count for d in self.domains.values())
        self.degraded_capabilities = sum(d.degraded_count for d in self.domains.values())
        self.blocked_capabilities = sum(d.blocked_count for d in self.domains.values())

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

        if self.domains and all(
            d.state == HealthState.BLOCKED for d in self.domains.values()
        ):
            self.state = HealthState.BLOCKED
            return self.state

        if any(
            d.state in (HealthState.BLOCKED, HealthState.DEGRADED)
            for d in self.domains.values()
        ):
            if self.state != HealthState.BLOCKED:
                self.state = HealthState.DEGRADED
            return self.state

        if self.state == HealthState.BLOCKED:
            return self.state

        self.state = HealthState.HEALTHY
        return self.state


# ==============================================================================
# PLATFORM HEALTH ENGINE (L5 AUTHORITY)
# ==============================================================================


class PlatformHealthEngine:
    """L5 Platform Health Authority.

    THE source of truth for platform health state.
    Converts raw signals into deterministic health states.
    """

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

    KNOWN_DISQUALIFIED = {"KILLSWITCH_STATUS"}

    def __init__(self, driver: PlatformHealthDriver):
        self._driver = driver

    # ==========================================================================
    # SYSTEM HEALTH
    # ==========================================================================

    def get_system_health(self) -> SystemHealth:
        """Get current system health."""
        health = SystemHealth(state=HealthState.HEALTHY)
        health.last_checked = datetime.now(timezone.utc)

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

        for domain_name in self.DOMAIN_CAPABILITIES.keys():
            domain_health = self.get_domain_health(domain_name)
            health.domains[domain_name] = domain_health

        for domain in health.domains.values():
            for cap in domain.capabilities.values():
                if cap.qualifier_state == "QUALIFIED":
                    health.qualified_capabilities += 1
                elif cap.qualifier_state == "DISQUALIFIED":
                    health.disqualified_capabilities += 1

        health.compute_state()
        return health

    # ==========================================================================
    # DOMAIN HEALTH
    # ==========================================================================

    def get_domain_health(self, domain_name: str) -> DomainHealth:
        """Get health for a specific domain."""
        health = DomainHealth(domain_name=domain_name, state=HealthState.HEALTHY)
        health.last_checked = datetime.now(timezone.utc)

        capabilities = self.DOMAIN_CAPABILITIES.get(domain_name, [])
        for cap_name in capabilities:
            cap_health = self.get_capability_health(cap_name)
            health.capabilities[cap_name] = cap_health

        health.compute_state()
        return health

    # ==========================================================================
    # CAPABILITY HEALTH
    # ==========================================================================

    def get_capability_health(self, capability_name: str) -> CapabilityHealth:
        """Get health for a specific capability."""
        health = CapabilityHealth(
            capability_name=capability_name, state=HealthState.HEALTHY
        )
        health.last_checked = datetime.now(timezone.utc)

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

        qualifier = self._driver.fetch_qualifier_state(capability_name)
        if qualifier:
            health.qualifier_state = qualifier
        elif capability_name in self.KNOWN_DISQUALIFIED:
            health.qualifier_state = "DISQUALIFIED"

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

        health.lifecycle_status = self._driver.fetch_lifecycle_status(capability_name)
        return health

    # ==========================================================================
    # ELIGIBILITY CHECKS
    # ==========================================================================

    def is_capability_eligible(self, capability_name: str) -> bool:
        """Quick check if a capability is eligible (not BLOCKED)."""
        health = self.get_capability_health(capability_name)
        return health.is_eligible()

    def get_eligible_capabilities(self) -> list[str]:
        """Get list of all eligible capabilities."""
        eligible = []
        for domain_caps in self.DOMAIN_CAPABILITIES.values():
            for cap_name in domain_caps:
                if self.is_capability_eligible(cap_name):
                    eligible.append(cap_name)
        return eligible

    def get_blocked_capabilities(self) -> list[str]:
        """Get list of all blocked capabilities."""
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
    """Factory function to get PlatformHealthEngine instance."""
    driver = get_platform_health_driver(session)
    return PlatformHealthEngine(driver=driver)


# ==============================================================================
# BACKWARD COMPATIBILITY
# ==============================================================================

PlatformHealthService = PlatformHealthEngine
get_platform_health_service = get_platform_health_engine

__all__ = [
    "HealthState",
    "SignalType",
    "HealthReason",
    "CapabilityHealth",
    "DomainHealth",
    "SystemHealth",
    "PlatformHealthEngine",
    "get_platform_health_engine",
    "PlatformHealthService",
    "get_platform_health_service",
]
