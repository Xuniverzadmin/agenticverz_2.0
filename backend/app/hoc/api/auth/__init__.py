# Layer: L2 — Product APIs
# Product: system-wide
# AUDIENCE: SHARED
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async
# Role: HOC Identity API router aggregation
# Callers: app/hoc/app.py
# Allowed Imports: L2 (sibling routers)
# Forbidden Imports: L5, L6
# Reference: HOC_AUTH_CLERK_REPLACEMENT_DESIGN_V1_2026-02-21.md

"""
HOC Identity API — Router Aggregation

Provides the canonical /hoc/api/auth/* endpoint surface for in-house
authentication (register, login, refresh, switch-tenant, logout, me,
password reset).

All endpoints are scaffolds with TODO markers — no auth logic implemented yet.
"""

from __future__ import annotations

from fastapi import APIRouter

from .routes import router as auth_router

ROUTERS: list[APIRouter] = [auth_router]

__all__ = ["ROUTERS"]
