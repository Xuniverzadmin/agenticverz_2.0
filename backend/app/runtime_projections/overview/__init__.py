# Layer: L3 — Boundary Adapters
# Product: ai-console
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Overview runtime projection package
# Reference: PIN-413 Domain Design — Overview & Logs (CORRECTED)

"""
Overview Runtime Projections (PROJECTION-ONLY)

ARCHITECTURAL RULE:
- Overview DOES NOT own any tables
- Overview aggregates/projects from existing domains
- All endpoints are READ-ONLY

Exports:
- overview_router: Router for /api/v1/runtime/overview/*

Overview answers "Is the system okay right now?":
- Cross-Domain Highlights: aggregated counts, system pulse
- Decisions Queue: pending items from incidents, proposals, limit overrides
"""

from .router import router as overview_router

__all__ = ["overview_router"]
