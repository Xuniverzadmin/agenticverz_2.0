# Layer: L2.1 — Facade (INT: general)
# AUDIENCE: INTERNAL

from __future__ import annotations

from fastapi import APIRouter

from app.hoc.api.int.general.debug_auth import router as debug_auth_router
from app.hoc.api.int.general.health import router as health_router
from app.hoc.api.int.general.legacy_routes import router as legacy_routes_router
from app.hoc.api.int.general.sdk import router as sdk_router

DOMAIN = "int.general"
ROUTERS: list[APIRouter] = [
    health_router,
    legacy_routes_router,
    sdk_router,
    debug_auth_router,
]
