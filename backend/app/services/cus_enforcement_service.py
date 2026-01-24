# Layer: L4 — Domain Engine (DEPRECATED - use cus_enforcement_engine.py)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api, sdk
#   Execution: sync
# Role: DEPRECATED - Backward compatibility shim for CusEnforcementService
# Callers: Any legacy imports
# Reference: PIN-468, DRIVER_ENGINE_CONTRACT.md

"""Customer Enforcement Service - DEPRECATED

This module is deprecated. Use cus_enforcement_engine.py instead.

The service has been split into:
- cus_enforcement_engine.py (L4 - business logic, decisions)
- cus_enforcement_driver.py (L6 - data access, persistence)

PIN-468: Phase 2 Step 2 - L4/L6 Layer Segregation
"""

import warnings

warnings.warn(
    "cus_enforcement_service is deprecated. "
    "Use cus_enforcement_engine instead. "
    "See PIN-468 for migration details.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from engine
from app.services.cus_enforcement_engine import (
    CusEnforcementEngine,
    CusEnforcementService,
    EnforcementDecision,
    EnforcementReason,
    EnforcementResult,
    get_cus_enforcement_engine,
    get_cus_enforcement_service,
)

__all__ = [
    "CusEnforcementEngine",
    "CusEnforcementService",
    "EnforcementResult",
    "EnforcementReason",
    "EnforcementDecision",
    "get_cus_enforcement_engine",
    "get_cus_enforcement_service",
]
