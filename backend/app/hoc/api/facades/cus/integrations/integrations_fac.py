# Layer: L2.1 — Facade (CUS: integrations)

from __future__ import annotations

from fastapi import APIRouter

from app.hoc.api.cus.integrations.integrations_public import router as integrations_public_router
from app.hoc.api.cus.integrations.cus_telemetry import router as cus_telemetry_router
from app.hoc.api.cus.integrations.mcp_servers import router as mcp_servers_router
from app.hoc.api.cus.integrations.session_context import router as session_context_router
from app.hoc.api.cus.integrations.v1_proxy import router as v1_proxy_router
from app.hoc.api.cus.integrations.aos_cus_integrations import router as aos_cus_integrations_router

DOMAIN = "integrations"
ROUTERS: list[APIRouter] = [
    integrations_public_router,
    aos_cus_integrations_router,
    mcp_servers_router,
    cus_telemetry_router,
    session_context_router,
    v1_proxy_router,
]
