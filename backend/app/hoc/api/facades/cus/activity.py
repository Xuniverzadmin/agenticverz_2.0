# capability_id: CAP-012
# Layer: L2.1 — Facade (CUS: activity)

from __future__ import annotations

from fastapi import APIRouter

from app.hoc.api.cus.activity.activity import router as activity_router
from app.hoc.api.cus.activity.runs_facade import router as runs_facade_router

DOMAIN = "activity"
ROUTERS: list[APIRouter] = [activity_router, runs_facade_router]
