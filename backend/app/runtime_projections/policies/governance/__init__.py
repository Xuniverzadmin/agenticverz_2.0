# Layer: L3 — Boundary Adapters
# Product: ai-console
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Governance runtime projection package
# Reference: PIN-412 Domain Design

"""
Governance Runtime Projections (GOV-RT-O2)

Exports:
- governance_router: Router for /api/v1/runtime/policies/rules
"""

from .router import router as governance_router

__all__ = ["governance_router"]
