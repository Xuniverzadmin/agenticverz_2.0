# capability_id: CAP-012
# Layer: L2.1 — Facade (FDR: ops)

from __future__ import annotations

from fastapi import APIRouter

from app.hoc.api.fdr.ops.cost_ops import router as cost_ops_router
from app.hoc.api.fdr.ops.founder_actions import router as founder_actions_router
from app.hoc.api.fdr.ops.retrieval_admin import router as retrieval_admin_router
from app.hoc.api.fdr.ops.stagetest import router as stagetest_router

DOMAIN = "fdr.ops"
ROUTERS: list[APIRouter] = [founder_actions_router, cost_ops_router, retrieval_admin_router, stagetest_router]
