# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Role: Limits simulation service - pre-execution limit checks
# Temporal:
#   Trigger: api
#   Execution: async
# Callers: simulate.py
# Allowed Imports: L6 (drivers), schemas
# Forbidden Imports: L1, L2, L3, sqlalchemy direct
# Reference: SWEEP-03 Batch 2, PIN-LIM-04

"""
LimitsSimulationService (SWEEP-03 Batch 2)

PURPOSE:
    Pre-execution limit simulation for cost, quota, and policy limits.
    Called by simulate.py before execution.

INTERFACE:
    - LimitsSimulationService (alias for LimitsSimulationEngine)
    - LimitsSimulationServiceError (base exception)
    - TenantNotFoundError (tenant not found)
    - get_limits_simulation_service(session) -> LimitsSimulationService

IMPLEMENTATION NOTES:
    Re-exports from existing simulation_engine.py which is already
    properly structured with L4/L6 separation.
    Future work may fully migrate the implementation to HOC.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

# =============================================================================
# Re-export from existing engine
# =============================================================================
# The simulation engine already has proper L4/L6 separation
# This module provides the HOC import path for callers

from app.services.limits.simulation_engine import (
    LimitsSimulationEngine,
    LimitsSimulationServiceError,
    TenantNotFoundError,
    get_limits_simulation_engine,
)

# =============================================================================
# HOC Aliases
# =============================================================================

# Alias for backward compatibility
LimitsSimulationService = LimitsSimulationEngine


def get_limits_simulation_service(session: "AsyncSession") -> LimitsSimulationService:
    """Get the LimitsSimulationService instance.

    Args:
        session: AsyncSession for database access

    Returns:
        LimitsSimulationService instance

    Note:
        Delegates to get_limits_simulation_engine() which creates the engine
        with proper L6 driver injection.
    """
    return get_limits_simulation_engine(session)


__all__ = [
    "LimitsSimulationService",
    "LimitsSimulationEngine",
    "LimitsSimulationServiceError",
    "TenantNotFoundError",
    "get_limits_simulation_service",
    "get_limits_simulation_engine",
]
