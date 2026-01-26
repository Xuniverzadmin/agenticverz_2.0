# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Role: Customer telemetry service - LLM usage ingestion and reporting
# Temporal:
#   Trigger: api
#   Execution: async
# Callers: cus_telemetry.py
# Allowed Imports: L6 (drivers)
# Forbidden Imports: L1, L2, L3, sqlalchemy direct
# Reference: SWEEP-03 Batch 2, PIN-468

"""
CusTelemetryService (SWEEP-03 Batch 2)

PURPOSE:
    Customer telemetry ingestion and usage reporting.
    Called by cus_telemetry.py API endpoints.

INTERFACE:
    - CusTelemetryService (alias for CusTelemetryEngine)
    - IngestResult (dataclass)
    - BatchIngestResult (dataclass)
    - get_cus_telemetry_service() -> CusTelemetryService

IMPLEMENTATION NOTES:
    Re-exports from existing cus_telemetry_engine.py which is already
    properly structured with L4/L6 separation.
    Future work may fully migrate the implementation to HOC.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# =============================================================================
# Re-export from existing engine
# =============================================================================
# The telemetry engine already has proper L4/L6 separation
# This module provides the HOC import path for callers

from app.services.cus_telemetry_engine import (
    BatchIngestResult,
    CusTelemetryEngine,
    IngestResult,
    get_cus_telemetry_engine,
)

# =============================================================================
# HOC Aliases
# =============================================================================

# Alias for backward compatibility
CusTelemetryService = CusTelemetryEngine


def get_cus_telemetry_service() -> CusTelemetryService:
    """Get the CusTelemetryService instance.

    Returns:
        CusTelemetryService instance

    Note:
        Delegates to get_cus_telemetry_engine() which creates the engine
        with proper L6 driver injection.
    """
    return get_cus_telemetry_engine()


__all__ = [
    "CusTelemetryService",
    "CusTelemetryEngine",
    "IngestResult",
    "BatchIngestResult",
    "get_cus_telemetry_service",
    "get_cus_telemetry_engine",
]
