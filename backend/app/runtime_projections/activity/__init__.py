# Layer: L3 — Boundary Adapters
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Activity domain runtime projections (O2-O5)
# Callers: Frontend via slot binding
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2
# Reference: PIN-411

"""
Activity Domain Runtime Projections

Endpoints:
- GET /runs - O2 list (Live, Completed, Risk Signals topics)
- GET /runs/{run_id} - O3 detail
- GET /runs/{run_id}/evidence - O4 evidence (preflight only)
- GET /runs/{run_id}/proof - O5 proof (preflight only)
"""

from .runs import activity_runs_router

__all__ = ["activity_runs_router"]
