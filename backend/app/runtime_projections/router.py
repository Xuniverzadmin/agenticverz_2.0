# Layer: L3 — Boundary Adapters
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Router mount for all runtime projection endpoints
# Callers: main.py
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2
# Reference: PIN-411, PIN-412, PIN-413

"""
Runtime Projections Router

Mounts all domain-specific runtime projection endpoints.
All endpoints are READ-ONLY.

Domains (Customer Console v1):
- Activity (PIN-411)
- Incidents (PIN-412)
- Policies (PIN-412)
- Overview (PIN-413)
- Logs (PIN-413)
"""

from fastapi import APIRouter

from .activity import activity_runs_router
from .incidents import incidents_router
from .policies import policies_router
from .overview import overview_router
from .logs import logs_router

runtime_projections_router = APIRouter(
    prefix="/api/v1/runtime",
    tags=["runtime-projections"],
)

# Mount Activity domain routes (PIN-411)
runtime_projections_router.include_router(activity_runs_router)

# Mount Incidents domain routes (PIN-412)
runtime_projections_router.include_router(incidents_router)

# Mount Policies domain routes (PIN-412)
runtime_projections_router.include_router(policies_router)

# Mount Overview domain routes (PIN-413)
runtime_projections_router.include_router(overview_router)

# Mount Logs domain routes (PIN-413)
runtime_projections_router.include_router(logs_router)
