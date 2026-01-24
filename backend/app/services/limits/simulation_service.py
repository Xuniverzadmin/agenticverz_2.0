# Layer: L4 — Domain Engine (DEPRECATED - use simulation_engine.py)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: DEPRECATED - Backward compatibility shim for LimitsSimulationService
# Callers: Any legacy imports
# Reference: PIN-468, DRIVER_ENGINE_CONTRACT.md, PIN-LIM-04

"""Limits Simulation Service - DEPRECATED

This module is deprecated. Use simulation_engine.py instead.

The service has been split into:
- simulation_engine.py (L4 - business logic, decisions)
- simulation_driver.py (L6 - data access, persistence)

PIN-468: Phase 2 Step 2 - L4/L6 Layer Segregation
"""

import warnings

warnings.warn(
    "simulation_service (LimitsSimulationService) is deprecated. "
    "Use simulation_engine (LimitsSimulationEngine) instead. "
    "See PIN-468 for migration details.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from engine
from app.services.limits.simulation_engine import (
    LimitsSimulationEngine,
    LimitsSimulationService,
    LimitsSimulationServiceError,
    TenantNotFoundError,
    get_limits_simulation_engine,
    get_limits_simulation_service,
)

__all__ = [
    "LimitsSimulationEngine",
    "LimitsSimulationService",
    "LimitsSimulationServiceError",
    "TenantNotFoundError",
    "get_limits_simulation_engine",
    "get_limits_simulation_service",
]
