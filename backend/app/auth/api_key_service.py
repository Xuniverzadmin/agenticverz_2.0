# Layer: L4 — Domain Engine (DEPRECATED - use api_key_engine.py)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: DEPRECATED - Backward compatibility shim for ApiKeyService
# Callers: Any legacy imports
# Reference: PIN-468, DRIVER_ENGINE_CONTRACT.md, PIN-306, CAP-006

"""API Key Validation Service - DEPRECATED

This module is deprecated. Use api_key_engine.py instead.

The service has been split into:
- api_key_engine.py (L4 - business logic, decisions)
- api_key_driver.py (L6 - data access, persistence)

PIN-468: Phase 2 Step 2 - L4/L6 Layer Segregation
"""

import warnings

warnings.warn(
    "api_key_service is deprecated. "
    "Use api_key_engine instead. "
    "See PIN-468 for migration details.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from engine
from app.auth.api_key_engine import (
    ApiKeyEngine,
    ApiKeyService,
    get_api_key_engine,
    get_api_key_service,
)

__all__ = [
    "ApiKeyEngine",
    "ApiKeyService",
    "get_api_key_engine",
    "get_api_key_service",
]
