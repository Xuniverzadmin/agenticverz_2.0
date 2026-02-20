# Layer: L2.1 — Facade (CUS: incidents)

from __future__ import annotations

from fastapi import APIRouter

from app.hoc.api.cus.incidents.incidents_public import router as incidents_public_router
from app.hoc.api.cus.incidents.incidents import router as incidents_router
from app.hoc.api.cus.incidents.cost_guard import router as cost_guard_router

DOMAIN = "incidents"
ROUTERS: list[APIRouter] = [incidents_public_router, incidents_router, cost_guard_router]
