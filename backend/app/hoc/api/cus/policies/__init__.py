# Layer: L2 — Product APIs
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Limits API package (PIN-LIM)
# Callers: main.py router registration
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: LIMITS_MANAGEMENT_AUDIT.md

"""
Limits API Package

Provides endpoints for:
- Limit simulation (pre-execution checks)
- Limit overrides (temporary increases)
"""

from app.api.limits.simulate import router as simulate_router
from app.api.limits.override import router as override_router

__all__ = ["simulate_router", "override_router"]
