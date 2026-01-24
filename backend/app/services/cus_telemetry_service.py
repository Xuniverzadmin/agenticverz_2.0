# Layer: L4 — Domain Engine (DEPRECATED - use cus_telemetry_engine.py)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: DEPRECATED - Backward compatibility shim for CusTelemetryService
# Callers: Any legacy imports
# Reference: PIN-468, DRIVER_ENGINE_CONTRACT.md

"""Customer Telemetry Service - DEPRECATED

This module is deprecated. Use cus_telemetry_engine.py instead.

The service has been split into:
- cus_telemetry_engine.py (L4 - business logic, decisions)
- cus_telemetry_driver.py (L6 - data access, persistence)

This file exists only for backward compatibility with existing imports.
All functionality is re-exported from the engine.

Migration:
    # Old (deprecated):
    from app.services.cus_telemetry_service import CusTelemetryService

    # New (recommended):
    from app.services.cus_telemetry_engine import CusTelemetryEngine

PIN-468: Phase 2 Step 2 - L4/L6 Layer Segregation
"""

import warnings

# Emit deprecation warning on import
warnings.warn(
    "cus_telemetry_service is deprecated. "
    "Use cus_telemetry_engine instead. "
    "See PIN-468 for migration details.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from the engine for backward compatibility
from app.services.cus_telemetry_engine import (
    BatchIngestResult,
    CusTelemetryEngine,
    CusTelemetryService,  # Alias
    IngestResult,
    get_cus_telemetry_engine,
    get_cus_telemetry_service,  # Alias
)

__all__ = [
    "CusTelemetryEngine",
    "CusTelemetryService",
    "IngestResult",
    "BatchIngestResult",
    "get_cus_telemetry_engine",
    "get_cus_telemetry_service",
]
