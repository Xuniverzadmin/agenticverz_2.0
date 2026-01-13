# Layer: L3 — Boundary Adapters
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Runtime data projection for Aurora UI panels
# Callers: Frontend via slot binding
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2
# Reference: PIN-411

"""
Runtime Projections Module

READ-ONLY endpoints for Aurora O2-O5 data panels.
All data is pre-computed upstream and stored in Neon.
NO computation at query time.
"""

from .router import runtime_projections_router

__all__ = ["runtime_projections_router"]
