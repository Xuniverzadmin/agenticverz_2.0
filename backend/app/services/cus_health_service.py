# Layer: L4 — Domain Engine (DEPRECATED - use cus_health_engine.py)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api, scheduler
#   Execution: async
# Role: DEPRECATED - Backward compatibility shim for CusHealthService
# Callers: Any legacy imports
# Reference: PIN-468, DRIVER_ENGINE_CONTRACT.md

"""Customer Health Service - DEPRECATED

This module is deprecated. Use cus_health_engine.py instead.

The service has been split into:
- cus_health_engine.py (L4 - business logic, decisions)
- cus_health_driver.py (L6 - data access, persistence)

PIN-468: Phase 2 Step 2 - L4/L6 Layer Segregation
"""

import warnings

warnings.warn(
    "cus_health_service is deprecated. "
    "Use cus_health_engine instead. "
    "See PIN-468 for migration details.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from engine
from app.services.cus_health_engine import (
    CusHealthEngine,
    CusHealthService,
    get_cus_health_engine,
    get_cus_health_service,
)

__all__ = [
    "CusHealthEngine",
    "CusHealthService",
    "get_cus_health_engine",
    "get_cus_health_service",
]
