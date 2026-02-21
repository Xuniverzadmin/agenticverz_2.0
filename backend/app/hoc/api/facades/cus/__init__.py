# capability_id: CAP-012
# Layer: L2.1 — Facade (CUS Router Bundles)
"""
Canonical customer-domain facades (non-optional):
overview, activity, incidents, policies, controls, logs, analytics,
integrations, api_keys, account.
"""

from __future__ import annotations

from fastapi import APIRouter

from .account import ROUTERS as ACCOUNT_ROUTERS
from .activity import ROUTERS as ACTIVITY_ROUTERS
from .analytics import ROUTERS as ANALYTICS_ROUTERS
from .api_keys import ROUTERS as API_KEYS_ROUTERS
from .controls import ROUTERS as CONTROLS_ROUTERS
from .incidents import ROUTERS as INCIDENTS_ROUTERS
from .integrations import ROUTERS as INTEGRATIONS_ROUTERS
from .logs import ROUTERS as LOGS_ROUTERS
from .overview import ROUTERS as OVERVIEW_ROUTERS
from .policies import ROUTERS as POLICIES_ROUTERS

CANONICAL_CUS_DOMAINS: tuple[str, ...] = (
    "overview",
    "activity",
    "incidents",
    "policies",
    "controls",
    "logs",
    "analytics",
    "integrations",
    "api_keys",
    "account",
)

ALL_CUS_ROUTERS: list[APIRouter] = [
    *OVERVIEW_ROUTERS,
    *ACTIVITY_ROUTERS,
    *INCIDENTS_ROUTERS,
    *POLICIES_ROUTERS,
    *CONTROLS_ROUTERS,
    *LOGS_ROUTERS,
    *ANALYTICS_ROUTERS,
    *INTEGRATIONS_ROUTERS,
    *API_KEYS_ROUTERS,
    *ACCOUNT_ROUTERS,
]

