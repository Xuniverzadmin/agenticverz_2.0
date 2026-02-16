# Layer: L2.1 — Facade (CUS: controls)

from __future__ import annotations

from fastapi import APIRouter

from app.hoc.api.cus.controls.controls_public import router as controls_public_router
from app.hoc.api.cus.controls.controls import router as controls_router

DOMAIN = "controls"
ROUTERS: list[APIRouter] = [controls_public_router, controls_router]
