# Layer: L4 — Domain Facades
# AUDIENCE: CUSTOMER
# Role: Facades for logs domain - composition only, delegates to L6 drivers
# Reference: HOC_LAYER_TOPOLOGY_V1.md

"""
Logs Domain Facades (L4)

Composition-only facades for the logs domain.
"""

from app.houseofcards.customer.logs.facades.logs_facade import (
    LogsFacade,
    get_logs_facade,
)

__all__ = [
    "LogsFacade",
    "get_logs_facade",
]
