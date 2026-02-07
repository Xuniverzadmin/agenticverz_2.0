# Layer: L4 — Authority Policy (Veil Controls)
"""
Veil controls reduce attack-surface observability.

These are not authentication or authorization; they are posture choices:
- schema/docs exposure gating
- deny-as-404 posture for unauthorized paths
- probe rate limiting for unauthenticated requests
"""

from __future__ import annotations

import os


def _mode() -> str:
    return os.getenv("AOS_MODE", "preprod").lower()


def is_prod() -> bool:
    return _mode() == "prod"


def fastapi_schema_urls() -> dict[str, object]:
    """
    Return FastAPI docs/openapi configuration.

    Default posture:
    - Non-prod: keep docs enabled (developer convenience).
    - Prod: hide docs and OpenAPI by default.
    """
    if not is_prod():
        return {}

    enabled = os.getenv("HOC_DOCS_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
    if enabled:
        return {}

    return {"openapi_url": None, "docs_url": None, "redoc_url": None}


def deny_as_404_enabled() -> bool:
    """
    If enabled, deny responses avoid revealing existence of protected resources.
    """
    if not is_prod():
        return False
    return os.getenv("HOC_DENY_AS_404", "true").lower() in {"1", "true", "yes", "on"}


def unauthorized_http_status_code(default: int = 403) -> int:
    return 404 if deny_as_404_enabled() else default


def unauthenticated_http_status_code(default: int = 401) -> int:
    return 404 if deny_as_404_enabled() else default


def probe_rate_limit_enabled() -> bool:
    if not is_prod():
        return False
    return os.getenv("HOC_PROBE_RATE_LIMIT_ENABLED", "true").lower() in {"1", "true", "yes", "on"}


def probe_rate_per_minute() -> int:
    try:
        return int(os.getenv("HOC_PROBE_RATE_PER_MIN", "60"))
    except ValueError:
        return 60

