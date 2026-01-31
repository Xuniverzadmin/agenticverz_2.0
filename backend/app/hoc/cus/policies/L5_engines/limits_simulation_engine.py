# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Role: Limits simulation engine - pre-execution limit checks
# NOTE: Renamed limits_simulation_service.py → limits_simulation_engine.py (2026-01-31)
#       per BANNED_NAMING rule (*_service.py → *_engine.py for L5 files)
# NOTE: Legacy import disconnected (2026-01-31) — was re-exporting from
#       app.services.limits.simulation_engine. Stubbed pending HOC rewiring.
# Temporal:
#   Trigger: api
#   Execution: async
# Callers: simulate.py
# Allowed Imports: L6 (drivers), schemas
# Forbidden Imports: L1, L2, L3, sqlalchemy direct
# Reference: SWEEP-03 Batch 2, PIN-LIM-04

"""
LimitsSimulationEngine (SWEEP-03 Batch 2)

PURPOSE:
    Pre-execution limit simulation for cost, quota, and policy limits.
    Called by simulate.py before execution.

INTERFACE:
    - LimitsSimulationEngine
    - LimitsSimulationService (backward alias)
    - LimitsSimulationServiceError (base exception)
    - TenantNotFoundError (tenant not found)
    - get_limits_simulation_engine(session) -> LimitsSimulationEngine
    - get_limits_simulation_service(session) -> LimitsSimulationService (backward alias)

IMPLEMENTATION STATUS:
    Legacy import from app.services.limits.simulation_engine DISCONNECTED.
    Stubbed with placeholder classes pending HOC rewiring phase.
    TODO: Rewire to HOC equivalent candidate during rewiring phase.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


# =============================================================================
# Stub types — TODO: rewire to HOC equivalent candidate during rewiring phase
# =============================================================================


class LimitsSimulationServiceError(Exception):
    """Base exception for limits simulation."""
    pass


class TenantNotFoundError(LimitsSimulationServiceError):
    """Tenant not found."""
    pass


class LimitsSimulationEngine:
    """Limits simulation engine — stub.

    TODO: Rewire to HOC equivalent candidate during rewiring phase.
    Previously re-exported from app.services.limits.simulation_engine (legacy, now disconnected).
    """

    def __init__(self, session: Any = None) -> None:
        self._session = session

    async def simulate(self, **kwargs: Any) -> dict[str, Any]:
        """Simulate limit check — stub."""
        return {"feasible": True, "warnings": [], "stub": True}


# Backward-compatible alias
LimitsSimulationService = LimitsSimulationEngine


def get_limits_simulation_engine(session: "AsyncSession") -> LimitsSimulationEngine:
    """Get the LimitsSimulationEngine instance."""
    return LimitsSimulationEngine(session)


def get_limits_simulation_service(session: "AsyncSession") -> LimitsSimulationService:
    """Get the LimitsSimulationService instance (backward alias)."""
    return get_limits_simulation_engine(session)


__all__ = [
    "LimitsSimulationService",
    "LimitsSimulationEngine",
    "LimitsSimulationServiceError",
    "TenantNotFoundError",
    "get_limits_simulation_service",
    "get_limits_simulation_engine",
]
