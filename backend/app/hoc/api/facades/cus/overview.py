# Layer: L2.1 — Facade (CUS: overview)

from __future__ import annotations

from fastapi import APIRouter

from app.hoc.api.cus.overview.overview import router as overview_router
from app.hoc.api.cus.overview.overview_public import router as overview_public_router

DOMAIN = "overview"
ROUTERS: list[APIRouter] = [
    overview_router,
    overview_public_router,
]
