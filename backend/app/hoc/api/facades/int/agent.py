# Layer: L2.1 — Facade (INT: agent)
# AUDIENCE: INTERNAL

from __future__ import annotations

from fastapi import APIRouter

from app.hoc.api.int.agent.agents import router as agents_router
from app.hoc.api.int.agent.authz_status import router as authz_status_router
from app.hoc.api.int.agent.discovery import router as discovery_router
from app.hoc.api.int.agent.onboarding import router as onboarding_router
from app.hoc.api.int.agent.platform import router as platform_router

DOMAIN = "int.agent"
ROUTERS: list[APIRouter] = [
    agents_router,
    authz_status_router,
    onboarding_router,
    platform_router,
    discovery_router,
]
