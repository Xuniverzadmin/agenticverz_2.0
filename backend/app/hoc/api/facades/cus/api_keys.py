# Layer: L2.1 — Facade (CUS: api_keys)

from __future__ import annotations

from fastapi import APIRouter

from app.hoc.api.cus.api_keys.embedding import router as embedding_router
from app.hoc.api.cus.policies.aos_api_key import router as aos_api_key_router

DOMAIN = "api_keys"
ROUTERS: list[APIRouter] = [
    aos_api_key_router,
    embedding_router,
]

