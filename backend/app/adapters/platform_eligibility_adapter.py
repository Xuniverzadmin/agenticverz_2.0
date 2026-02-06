# Layer: L3 — Boundary Adapter
# Product: system-wide (platform health visibility)
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Translate L4 PlatformHealthService outputs to API-friendly views
# Callers: L2 (/platform/health, /platform/capabilities)
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L5
# Reference: PIN-284 (Platform Monitoring System)

"""
Platform Eligibility Adapter (L3)

Translates L4 PlatformHealthService outputs to Founder-facing API views.

L4 (PlatformHealthService) → L3 (this adapter) → L2 (platform endpoints)

The adapter:
1. Receives health states from L4 (SystemHealth, DomainHealth, CapabilityHealth)
2. Selects/renames fields for Founder audience
3. Converts dataclasses to JSON-serializable dicts
4. Returns views suitable for REST APIs

HARD RULES (from PIN-264):
- NO infra queries (that's L4's job)
- NO health computation (that's L4's job)
- NO permissions logic (that's L2's job)
- ONLY field selection and JSON serialization
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

# L4 imports (allowed)
from app.hoc.int.platform.engines.platform_health_engine import (
    CapabilityHealth,
    DomainHealth,
    HealthReason,
    PlatformHealthService,
    SystemHealth,
)

# =============================================================================
# L3 View DTOs (Founder-facing, JSON-serializable)
# =============================================================================


@dataclass(frozen=True)
class HealthReasonView:
    """Founder-facing reason for health state."""

    signal_type: str
    signal_value: str
    contribution: str  # HEALTHY, DEGRADED, BLOCKED
    message: str
    recorded_at: Optional[str]  # ISO8601 or None


@dataclass(frozen=True)
class CapabilityHealthView:
    """Founder-facing capability health."""

    capability_name: str
    state: str  # HEALTHY, DEGRADED, BLOCKED
    is_eligible: bool
    qualifier_state: Optional[str]  # QUALIFIED, DISQUALIFIED
    lifecycle_status: Optional[str]  # COMPLETE, PARTIAL
    reasons: List[HealthReasonView]
    last_checked: str  # ISO8601


@dataclass(frozen=True)
class DomainHealthView:
    """Founder-facing domain health."""

    domain_name: str
    state: str  # HEALTHY, DEGRADED, BLOCKED
    capabilities: Dict[str, CapabilityHealthView]
    healthy_count: int
    degraded_count: int
    blocked_count: int
    last_checked: str  # ISO8601


@dataclass
class SystemHealthView:
    """Founder-facing system health."""

    state: str  # HEALTHY, DEGRADED, BLOCKED
    blca_status: str
    lifecycle_coherence: str
    domains: Dict[str, DomainHealthView] = field(default_factory=dict)
    total_capabilities: int = 0
    healthy_capabilities: int = 0
    degraded_capabilities: int = 0
    blocked_capabilities: int = 0
    qualified_capabilities: int = 0
    disqualified_capabilities: int = 0
    reasons: List[HealthReasonView] = field(default_factory=list)
    last_checked: str = ""


@dataclass(frozen=True)
class CapabilityEligibilityView:
    """Simple eligibility view for a capability."""

    capability_name: str
    is_eligible: bool
    state: str
    reason: Optional[str]


@dataclass
class PlatformEligibilityResponse:
    """Response for GET /platform/capabilities."""

    total_capabilities: int
    eligible_count: int
    blocked_count: int
    capabilities: List[CapabilityEligibilityView] = field(default_factory=list)


# =============================================================================
# L3 Adapter Class
# =============================================================================


class PlatformEligibilityAdapter:
    """
    Boundary adapter for Platform Health views.

    This class provides the ONLY interface that L2 (/platform/*) may use
    to access PlatformHealthService data. It translates domain models to
    Founder-facing views.

    PIN-284 L3 Rule: Translation only, no business logic.
    """

    def _reason_to_view(self, reason: HealthReason) -> HealthReasonView:
        """Convert HealthReason to view."""
        return HealthReasonView(
            signal_type=reason.signal_type,
            signal_value=reason.signal_value,
            contribution=reason.contribution.value,
            message=reason.message,
            recorded_at=reason.recorded_at.isoformat() if reason.recorded_at else None,
        )

    def capability_to_view(self, cap: CapabilityHealth) -> CapabilityHealthView:
        """Convert CapabilityHealth to view."""
        return CapabilityHealthView(
            capability_name=cap.capability_name,
            state=cap.state.value,
            is_eligible=cap.is_eligible(),
            qualifier_state=cap.qualifier_state,
            lifecycle_status=cap.lifecycle_status,
            reasons=[self._reason_to_view(r) for r in cap.reasons],
            last_checked=cap.last_checked.isoformat(),
        )

    def domain_to_view(self, domain: DomainHealth) -> DomainHealthView:
        """Convert DomainHealth to view."""
        return DomainHealthView(
            domain_name=domain.domain_name,
            state=domain.state.value,
            capabilities={name: self.capability_to_view(cap) for name, cap in domain.capabilities.items()},
            healthy_count=domain.healthy_count,
            degraded_count=domain.degraded_count,
            blocked_count=domain.blocked_count,
            last_checked=domain.last_checked.isoformat(),
        )

    def system_to_view(self, system: SystemHealth) -> SystemHealthView:
        """Convert SystemHealth to view."""
        return SystemHealthView(
            state=system.state.value,
            blca_status=system.blca_status,
            lifecycle_coherence=system.lifecycle_coherence,
            domains={name: self.domain_to_view(domain) for name, domain in system.domains.items()},
            total_capabilities=system.total_capabilities,
            healthy_capabilities=system.healthy_capabilities,
            degraded_capabilities=system.degraded_capabilities,
            blocked_capabilities=system.blocked_capabilities,
            qualified_capabilities=system.qualified_capabilities,
            disqualified_capabilities=system.disqualified_capabilities,
            reasons=[self._reason_to_view(r) for r in system.reasons],
            last_checked=system.last_checked.isoformat(),
        )

    def to_eligibility_response(
        self,
        health_service: PlatformHealthService,
    ) -> PlatformEligibilityResponse:
        """
        Build eligibility response from health service.

        This is a convenience method that queries the health service
        and builds a simple eligibility response.
        """
        system = health_service.get_system_health()

        capabilities = []
        eligible_count = 0
        blocked_count = 0

        for domain in system.domains.values():
            for name, cap in domain.capabilities.items():
                is_eligible = cap.is_eligible()

                # Get primary reason if blocked
                reason = None
                if cap.reasons:
                    reason = cap.reasons[0].message

                capabilities.append(
                    CapabilityEligibilityView(
                        capability_name=name,
                        is_eligible=is_eligible,
                        state=cap.state.value,
                        reason=reason,
                    )
                )

                if is_eligible:
                    eligible_count += 1
                else:
                    blocked_count += 1

        return PlatformEligibilityResponse(
            total_capabilities=len(capabilities),
            eligible_count=eligible_count,
            blocked_count=blocked_count,
            capabilities=sorted(capabilities, key=lambda c: c.capability_name),
        )


# =============================================================================
# Factory Function
# =============================================================================


def get_platform_eligibility_adapter() -> PlatformEligibilityAdapter:
    """Factory function to get PlatformEligibilityAdapter instance."""
    return PlatformEligibilityAdapter()


# =============================================================================
# Exports
# =============================================================================


__all__ = [
    # Views
    "HealthReasonView",
    "CapabilityHealthView",
    "DomainHealthView",
    "SystemHealthView",
    "CapabilityEligibilityView",
    "PlatformEligibilityResponse",
    # Adapter
    "PlatformEligibilityAdapter",
    "get_platform_eligibility_adapter",
]
