# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Phase-7 Protection package exports
# Callers: Any module needing abuse protection functionality
# Allowed Imports: L4 (protection submodules)
# Forbidden Imports: L1, L2, L3, L5, L6
# Reference: PIN-399 Phase-7 (Abuse & Protection Layer)

"""
Phase-7 Abuse Protection Package

PIN-399 Phase-7: Abuse protection constrains behavior, not identity.

This package provides:
- Decision: Enforcement outcomes (ALLOW, THROTTLE, REJECT, WARN)
- ProtectionResult: Result of protection checks
- AnomalySignal: Non-blocking anomaly detection signals
- AbuseProtectionProvider: Protocol for protection operations
- MockAbuseProtectionProvider: Deterministic mock implementation

DESIGN INVARIANTS (LOCKED):
- ABUSE-001: Protection does not affect onboarding, roles, or billing state
- ABUSE-002: All enforcement outcomes are explicit (no silent failure)
- ABUSE-003: Anomaly detection never blocks user traffic
- ABUSE-004: Protection providers are swappable behind a fixed interface
- ABUSE-005: Mock provider must be behavior-compatible with real provider

PROTECTION DIMENSIONS:
- Rate limits: Time-based (e.g., 1000 req/min)
- Burst control: Short window (e.g., 100 req/sec)
- Cost guards: Value-based (e.g., $500/day)
- Anomaly signals: Pattern-based (e.g., sudden 10x jump)

APPLICABILITY:
    Protection applies to:
    - SDK endpoints
    - Runtime execution paths
    - Background workers

    Protection does NOT apply to:
    - Onboarding endpoints
    - Auth endpoints
    - Founder endpoints
    - Internal ops endpoints
"""

from app.protection.decisions import (
    Decision,
    ProtectionResult,
    AnomalySignal,
    allow,
    reject_rate_limit,
    reject_cost_limit,
    throttle,
    warn,
)
from app.protection.provider import (
    AbuseProtectionProvider,
    MockAbuseProtectionProvider,
    get_protection_provider,
    set_protection_provider,
)

# NOTE: FastAPI dependencies moved to app/api/protection_dependencies.py
# Domain packages must not export HTTP adapters (see LAYER_MODEL.md)

__all__ = [
    # Decision types
    "Decision",
    "ProtectionResult",
    "AnomalySignal",
    # Helper functions
    "allow",
    "reject_rate_limit",
    "reject_cost_limit",
    "throttle",
    "warn",
    # Provider
    "AbuseProtectionProvider",
    "MockAbuseProtectionProvider",
    "get_protection_provider",
    "set_protection_provider",
]
