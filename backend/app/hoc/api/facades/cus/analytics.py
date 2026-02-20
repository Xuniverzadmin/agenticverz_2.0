# Layer: L2.1 — Facade (CUS: analytics)

from __future__ import annotations

from fastapi import APIRouter

from app.hoc.api.cus.analytics.analytics_public import router as analytics_public_router
from app.hoc.api.cus.analytics.costsim import router as costsim_router
from app.hoc.api.cus.analytics.feedback import router as feedback_router
from app.hoc.api.cus.analytics.predictions import router as predictions_router
from app.hoc.api.cus.analytics.scenarios import router as scenarios_router
from app.hoc.api.cus.policies.analytics import router as analytics_router

DOMAIN = "analytics"
ROUTERS: list[APIRouter] = [
    analytics_router,
    analytics_public_router,
    costsim_router,
    scenarios_router,
    feedback_router,
    predictions_router,
]
