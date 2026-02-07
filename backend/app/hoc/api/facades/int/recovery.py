# Layer: L2.1 — Facade (INT: recovery)
# AUDIENCE: INTERNAL

from __future__ import annotations

from fastapi import APIRouter

from app.hoc.api.int.recovery.recovery import router as recovery_router
from app.hoc.api.int.recovery.recovery_ingest import router as recovery_ingest_router

DOMAIN = "int.recovery"
ROUTERS: list[APIRouter] = [
    recovery_router,
    recovery_ingest_router,
]
