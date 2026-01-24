# Layer: L4 — Domain Engine (DEPRECATED - use cus_integration_engine.py)
# AUDIENCE: CUSTOMER
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: DEPRECATED - Backward compatibility shim for CusIntegrationService
# Callers: Any legacy imports
# Reference: PIN-468, DRIVER_ENGINE_CONTRACT.md

"""Customer Integration Service - DEPRECATED

This module is deprecated. Use cus_integration_engine.py instead.

The service has been split into:
- cus_integration_engine.py (L4 - business logic, decisions)
- cus_integration_driver.py (L6 - data access, persistence)

This file exists only for backward compatibility with existing imports.
All functionality is re-exported from the engine.

Migration:
    # Old (deprecated):
    from app.services.cus_integration_service import CusIntegrationService

    # New (recommended):
    from app.services.cus_integration_engine import CusIntegrationEngine

PIN-468: Phase 2 Step 2 - L4/L6 Layer Segregation
"""

import warnings

# Emit deprecation warning on import
warnings.warn(
    "cus_integration_service is deprecated. "
    "Use cus_integration_engine instead. "
    "See PIN-468 for migration details.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from the engine for backward compatibility
from app.services.cus_integration_engine import (
    CusIntegrationEngine,
    CusIntegrationService,  # Alias
    DeleteResult,
    EnableResult,
    HealthCheckResult,
    get_cus_integration_engine,
    get_cus_integration_service,  # Alias
)

__all__ = [
    "CusIntegrationEngine",
    "CusIntegrationService",
    "DeleteResult",
    "EnableResult",
    "HealthCheckResult",
    "get_cus_integration_engine",
    "get_cus_integration_service",
]
