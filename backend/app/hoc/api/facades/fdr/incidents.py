# capability_id: CAP-012
# Layer: L2.1 — Facade (FDR: incidents)

from __future__ import annotations

from fastapi import APIRouter

from app.hoc.api.fdr.incidents.founder_onboarding import router as founder_onboarding_router
from app.hoc.api.fdr.incidents.ops import router as ops_router

DOMAIN = "fdr.incidents"
ROUTERS: list[APIRouter] = [
    ops_router,
    founder_onboarding_router,
]

