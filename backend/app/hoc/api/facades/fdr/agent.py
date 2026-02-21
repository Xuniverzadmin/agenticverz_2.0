# capability_id: CAP-012
# Layer: L2.1 — Facade (FDR: agent)

from __future__ import annotations

from fastapi import APIRouter

from app.hoc.api.fdr.agent.founder_contract_review import router as founder_contract_review_router

DOMAIN = "fdr.agent"
ROUTERS: list[APIRouter] = [founder_contract_review_router]

