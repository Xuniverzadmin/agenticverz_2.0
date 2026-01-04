# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Platform services package initialization
# Callers: L3 adapters, L2 APIs
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: PIN-284 (Platform Monitoring System)

"""
Platform Services Package (L4)

Provides platform-level domain engines for:
- Platform health monitoring (platform_health_service)
- [Future] Platform eligibility (wire to L3)

Contract:
- All platform services are L4 authority
- They consume L6 signals and produce deterministic states
- No L3/L2 imports allowed
"""

from app.services.platform.platform_health_service import (
    CapabilityHealth,
    DomainHealth,
    HealthReason,
    HealthState,
    PlatformHealthService,
    SignalType,
    SystemHealth,
    get_platform_health_service,
)

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
