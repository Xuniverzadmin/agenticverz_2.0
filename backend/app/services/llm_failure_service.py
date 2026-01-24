# Layer: L4 — Domain Engine (DEPRECATED - use llm_failure_engine.py)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: worker
#   Execution: async
# Role: DEPRECATED - Backward compatibility shim for LLMFailureService
# Callers: Any legacy imports
# Reference: PIN-468, PIN-196, DRIVER_ENGINE_CONTRACT.md

"""LLM Failure Service - DEPRECATED

This module is deprecated. Use llm_failure_engine.py instead.

The service has been split into:
- llm_failure_engine.py (L4 - business logic, S4 decisions)
- llm_failure_driver.py (L6 - data access, persistence)

PIN-468: Phase 2 Step 2 - L4/L6 Layer Segregation
"""

import warnings

warnings.warn(
    "llm_failure_service is deprecated. "
    "Use llm_failure_engine instead. "
    "See PIN-468 for migration details.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from engine
from app.services.llm_failure_engine import (
    LLMFailureEngine,
    LLMFailureFact,
    LLMFailureResult,
    LLMFailureService,
)

__all__ = [
    "LLMFailureFact",
    "LLMFailureResult",
    "LLMFailureEngine",
    "LLMFailureService",
]
