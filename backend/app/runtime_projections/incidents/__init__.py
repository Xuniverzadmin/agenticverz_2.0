# Layer: L3 — Boundary Adapters
# Product: ai-console
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Incidents runtime projection package
# Reference: PIN-412 Domain Design

"""
Incidents Runtime Projections (INC-RT-O2)

Exports:
- incidents_router: Router for /api/v1/runtime/incidents
"""

from .router import router as incidents_router

__all__ = ["incidents_router"]
