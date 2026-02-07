# Layer: L2.1 — Facade (CUS: overview)

from __future__ import annotations

from fastapi import APIRouter

from app.hoc.api.cus.overview.overview import router as overview_router

DOMAIN = "overview"
ROUTERS: list[APIRouter] = [overview_router]

