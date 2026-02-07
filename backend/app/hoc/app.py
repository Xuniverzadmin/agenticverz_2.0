# Layer: L2.1 — Facade (HOC Surface Wiring)
"""
Single HOC wiring node for entrypoints.

Contract:
- Imports facades (L2.1) only.
- Includes routers only (no endpoint definitions).
"""

from __future__ import annotations

from fastapi import APIRouter, FastAPI

from app.hoc.api.facades.cus import ALL_CUS_ROUTERS
from app.hoc.api.facades.fdr.account import ROUTERS as FDR_ACCOUNT_ROUTERS
from app.hoc.api.facades.fdr.agent import ROUTERS as FDR_AGENT_ROUTERS
from app.hoc.api.facades.fdr.incidents import ROUTERS as FDR_INCIDENTS_ROUTERS
from app.hoc.api.facades.fdr.logs import ROUTERS as FDR_LOGS_ROUTERS
from app.hoc.api.facades.fdr.ops import ROUTERS as FDR_OPS_ROUTERS
from app.hoc.api.facades.int.agent import ROUTERS as INT_AGENT_ROUTERS
from app.hoc.api.facades.int.general import ROUTERS as INT_GENERAL_ROUTERS
from app.hoc.api.facades.int.recovery import ROUTERS as INT_RECOVERY_ROUTERS


def build_hoc_router() -> APIRouter:
    router = APIRouter()

    # Canonical CUS domains (non-optional)
    for r in ALL_CUS_ROUTERS:
        router.include_router(r)

    # Internal surfaces (INT)
    for r in INT_GENERAL_ROUTERS:
        router.include_router(r)
    for r in INT_AGENT_ROUTERS:
        router.include_router(r)
    for r in INT_RECOVERY_ROUTERS:
        router.include_router(r)

    # Founder surfaces (FDR)
    for r in FDR_ACCOUNT_ROUTERS:
        router.include_router(r)
    for r in FDR_AGENT_ROUTERS:
        router.include_router(r)
    for r in FDR_INCIDENTS_ROUTERS:
        router.include_router(r)
    for r in FDR_LOGS_ROUTERS:
        router.include_router(r)
    for r in FDR_OPS_ROUTERS:
        router.include_router(r)

    return router


hoc_router: APIRouter = build_hoc_router()


def include_hoc(app: FastAPI) -> None:
    """Entrypoint API: include the canonical HOC router surface into `app`."""
    app.include_router(hoc_router)
