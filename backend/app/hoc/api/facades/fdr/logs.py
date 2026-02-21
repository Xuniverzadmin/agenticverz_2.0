# capability_id: CAP-012
# Layer: L2.1 — Facade (FDR: logs)

from __future__ import annotations

from fastapi import APIRouter

from app.hoc.api.fdr.logs.founder_review import router as founder_review_router
from app.hoc.api.fdr.logs.founder_timeline import router as founder_timeline_router

DOMAIN = "fdr.logs"
ROUTERS: list[APIRouter] = [
    founder_review_router,
    founder_timeline_router,
]

