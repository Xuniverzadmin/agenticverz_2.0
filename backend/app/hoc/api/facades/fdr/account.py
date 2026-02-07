# Layer: L2.1 — Facade (FDR: account)

from __future__ import annotations

from fastapi import APIRouter

from app.hoc.api.fdr.account.founder_explorer import router as explorer_router
from app.hoc.api.fdr.account.founder_lifecycle import router as founder_lifecycle_router

DOMAIN = "fdr.account"
ROUTERS: list[APIRouter] = [
    explorer_router,
    founder_lifecycle_router,
]

