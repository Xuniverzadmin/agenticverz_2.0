# Layer: L5 — Domain Engine
# NOTE: Renamed cus_integration_service.py → cus_integration_engine.py (2026-01-31) per BANNED_NAMING rule
# AUDIENCE: CUSTOMER
# Role: Customer integration service - LLM BYOK, SDK, RAG management
# Temporal:
#   Trigger: api
#   Execution: sync
# Callers: integrations_facade.py
# Allowed Imports: L6 (drivers)
# Forbidden Imports: L1, L2, L3, sqlalchemy direct
# Reference: SWEEP-03 Batch 3, PIN-468

"""
CusIntegrationService (SWEEP-03 Batch 3)

PURPOSE:
    Business logic for Customer Integration domain (LLM BYOK, SDK, RAG).
    Called by integrations_facade.py.

INTERFACE:
    - CusIntegrationService (alias for CusIntegrationEngine)
    - get_cus_integration_service() -> CusIntegrationService

IMPLEMENTATION NOTES:
    Re-exports from existing cus_integration_engine.py which is already
    properly structured with L4/L6 separation.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# =============================================================================
# LEGACY DISCONNECTED (2026-01-31)
# Was: from app.services.cus_integration_engine import (...)
# TODO: rewire to HOC equivalent candidate during rewiring phase
# =============================================================================

from typing import NamedTuple


class EnableResult(NamedTuple):
    """Stub: result of enabling an integration."""
    success: bool = False
    message: str = ""


class DeleteResult(NamedTuple):
    """Stub: result of deleting an integration."""
    success: bool = False
    message: str = ""


class HealthCheckResult(NamedTuple):
    """Stub: result of a health check."""
    healthy: bool = False
    message: str = ""


class CusIntegrationEngine:
    """Stub: Customer Integration Engine.

    TODO: rewire to HOC equivalent candidate during rewiring phase.
    Previously re-exported from app.services.cus_integration_engine.
    """
    pass


CusIntegrationService = CusIntegrationEngine


def get_cus_integration_engine() -> CusIntegrationEngine:
    """Stub factory.

    TODO: rewire to HOC equivalent candidate during rewiring phase.
    """
    return CusIntegrationEngine()

# =============================================================================
# HOC Aliases
# =============================================================================


def get_cus_integration_service() -> CusIntegrationService:
    """Get the CusIntegrationService instance.

    Returns:
        CusIntegrationService instance
    """
    return get_cus_integration_engine()


__all__ = [
    "CusIntegrationService",
    "CusIntegrationEngine",
    "EnableResult",
    "DeleteResult",
    "HealthCheckResult",
    "get_cus_integration_service",
    "get_cus_integration_engine",
]
