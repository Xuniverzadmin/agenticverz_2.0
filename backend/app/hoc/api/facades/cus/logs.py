# Layer: L2.1 — Facade (CUS: logs)

from __future__ import annotations

from fastapi import APIRouter

from app.hoc.api.cus.logs.cost_intelligence import router as cost_intelligence_router
from app.hoc.api.cus.logs.guard_logs import router as guard_logs_router
from app.hoc.api.cus.logs.tenants import router as tenants_router
from app.hoc.api.cus.logs.traces import router as traces_router

DOMAIN = "logs"
ROUTERS: list[APIRouter] = [
    cost_intelligence_router,
    tenants_router,
    traces_router,
    guard_logs_router,
]

