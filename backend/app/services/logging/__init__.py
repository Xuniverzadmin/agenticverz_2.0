# Layer: L4 — Domain Engines
# Product: system-wide
# Reference: GAP-019 (Alert → Log Linking)
"""
Logging Services (GAP-019)

Provides alert-to-log linking for explicit correlation between
threshold alerts and run execution logs.

This module provides:
    - AlertLogLink: Model for alert-log relationships
    - AlertLogLinker: Service for creating and querying links
    - AlertLogLinkResponse: Response model for API
    - Helper functions for quick access
"""

from app.services.logging.alert_log_linker import (
    AlertLogLink,
    AlertLogLinker,
    AlertLogLinkError,
    AlertLogLinkResponse,
    AlertLogLinkStatus,
    AlertLogLinkType,
    create_alert_log_link,
    get_alerts_for_run,
    get_logs_for_alert,
)

__all__ = [
    "AlertLogLink",
    "AlertLogLinker",
    "AlertLogLinkError",
    "AlertLogLinkResponse",
    "AlertLogLinkStatus",
    "AlertLogLinkType",
    "create_alert_log_link",
    "get_alerts_for_run",
    "get_logs_for_alert",
]
