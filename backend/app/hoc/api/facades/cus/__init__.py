# Layer: L2.1 — Facade (CUS Router Bundles)
"""
Canonical customer-domain facades (non-optional):
overview, activity, incidents, policies, controls, logs, analytics,
integrations, api_keys, account.
"""

from __future__ import annotations

from fastapi import APIRouter

from .account.account_fac import ROUTERS as ACCOUNT_ROUTERS
from .activity.activity_fac import ROUTERS as ACTIVITY_ROUTERS
from .analytics.analytics_fac import ROUTERS as ANALYTICS_ROUTERS
from .api_keys.api_keys_fac import ROUTERS as API_KEYS_ROUTERS
from .controls.controls_fac import ROUTERS as CONTROLS_ROUTERS
from .incidents.incidents_fac import ROUTERS as INCIDENTS_ROUTERS
from .integrations.integrations_fac import ROUTERS as INTEGRATIONS_ROUTERS
from .logs.logs_fac import ROUTERS as LOGS_ROUTERS
from .overview.overview_fac import ROUTERS as OVERVIEW_ROUTERS
from .policies.policies_fac import ROUTERS as POLICIES_ROUTERS

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
