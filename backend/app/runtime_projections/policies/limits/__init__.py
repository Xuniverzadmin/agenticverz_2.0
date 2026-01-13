# Layer: L3 — Boundary Adapters
# Product: ai-console
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Limits runtime projection package
# Reference: PIN-412 Domain Design

"""
Limits Runtime Projections (LIM-RT-O2)

Exports:
- limits_router: Router for /api/v1/runtime/policies/limits
"""

from .router import router as limits_router

__all__ = ["limits_router"]
