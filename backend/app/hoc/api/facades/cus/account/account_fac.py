# Layer: L2.1 — Facade (CUS: account)

from __future__ import annotations

from fastapi import APIRouter

from app.hoc.api.cus.account.account_public import router as account_public_router
from app.hoc.api.cus.account.memory_pins import router as memory_pins_router
from app.hoc.api.cus.account.aos_accounts import router as accounts_router

DOMAIN = "account"
ROUTERS: list[APIRouter] = [
    account_public_router,
    accounts_router,
    memory_pins_router,
]
