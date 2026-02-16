# Layer: L2.1 — Facade (CUS: api_keys)

from __future__ import annotations

from fastapi import APIRouter

from app.hoc.api.cus.api_keys.api_keys_public import router as api_keys_public_router
from app.hoc.api.cus.api_keys.aos_api_key import router as aos_api_key_router
from app.hoc.api.cus.api_keys.api_key_writes import router as api_key_writes_router
from app.hoc.api.cus.api_keys.embedding import router as embedding_router

DOMAIN = "api_keys"
ROUTERS: list[APIRouter] = [
    api_keys_public_router,
    aos_api_key_router,
    api_key_writes_router,
    embedding_router,
]
