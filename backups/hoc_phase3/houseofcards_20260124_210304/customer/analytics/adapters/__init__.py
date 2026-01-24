# Layer: L3 — Adapters
# AUDIENCE: CUSTOMER
# Role: Analytics domain boundary adapters
# Reference: Phase-2.5A Analytics Extraction

"""
Analytics Adapters (L3)

Boundary adapters for the analytics domain.
Adapters handle external communication (HTTP, email, etc.)
All business logic stays in L4 engines.

Adapters:
- AlertDeliveryAdapter: HTTP delivery to Alertmanager
"""

from app.houseofcards.customer.analytics.adapters.alert_delivery import (
    AlertDeliveryAdapter,
    get_alert_delivery_adapter,
)

__all__ = [
    "AlertDeliveryAdapter",
    "get_alert_delivery_adapter",
]
