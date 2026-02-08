# Layer: L0 — Entrypoint
# Product: system-wide
# Temporal:
#   Trigger: process start
#   Execution: sync
# Role: Canonical HOC-only FastAPI entrypoint (API surface = app.hoc.api/**)
# Callers: uvicorn/gunicorn (`uvicorn app.hoc_main:app`)
# Allowed Imports: app.hoc.* only (plus framework)
# Reference: HOC_LAYER_TOPOLOGY_V2.0.0

"""
HOC-Only Entrypoint

This entrypoint is intentionally minimal and imports only `app.hoc.*` symbols
for application wiring. It serves the canonical HOC API surface and wires the
auth/gating middleware through `hoc_spine.auth_wiring`.

Use:
  uvicorn app.hoc_main:app
"""

from fastapi import FastAPI

from app.hoc.app import include_hoc
from app.hoc.cus.hoc_spine.auth_wiring import (
    AUTH_GATEWAY_ENABLED,
    OnboardingGateMiddleware,
    RBACMiddleware,
    setup_auth_middleware,
)

app = FastAPI()

# Canonical API surface
include_hoc(app)

# Middleware order: Starlette executes in reverse add order.
# We want: AuthGateway → OnboardingGate → RBAC.
app.add_middleware(RBACMiddleware)
app.add_middleware(OnboardingGateMiddleware)

if AUTH_GATEWAY_ENABLED:
    setup_auth_middleware(app)

