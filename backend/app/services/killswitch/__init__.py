# Layer: L4 — Domain Engine
# Product: system-wide
# Role: Killswitch domain services package
# Reference: KILLSWITCH Domain Qualification

"""
Killswitch Domain Services (L4)

This package provides domain-level services for killswitch operations.
L3 adapters should import from this package, NOT from L6 models directly.

Available services:
- CustomerKillswitchReadService: Read operations for customer killswitch status
"""

from app.services.killswitch.customer_killswitch_read_service import (
    CustomerKillswitchReadService,
    GuardrailInfo,
    IncidentStats,
    KillswitchState,
    KillswitchStatusInfo,
    get_customer_killswitch_read_service,
)

__all__ = [
    # Service
    "CustomerKillswitchReadService",
    "get_customer_killswitch_read_service",
    # DTOs
    "KillswitchState",
    "GuardrailInfo",
    "IncidentStats",
    "KillswitchStatusInfo",
]
