# Layer: L3 — Boundary Adapters
# Product: ai-console
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Policies runtime projection package
# Reference: PIN-412 Domain Design

"""
Policies Runtime Projections

Exports:
- policies_router: Router for /api/v1/runtime/policies/*
"""

from fastapi import APIRouter

from .governance import governance_router
from .limits import limits_router

policies_router = APIRouter(prefix="/policies", tags=["runtime-policies"])

# Mount Governance subdomain routes
policies_router.include_router(governance_router)

# Mount Limits subdomain routes
policies_router.include_router(limits_router)

__all__ = ["policies_router"]
