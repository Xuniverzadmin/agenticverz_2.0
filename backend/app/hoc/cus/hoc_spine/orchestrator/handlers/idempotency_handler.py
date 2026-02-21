# capability_id: CAP-012
# Layer: L4 — HOC Spine (Handler)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: L4 handler — request idempotency
# Callers: API middleware, execution paths
# Allowed Imports: hoc_spine, hoc.cus.logs.L6_drivers (lazy)
# Forbidden Imports: L1, L2
# Reference: PIN-513 Batch 3B3 Wiring
# artifact_class: CODE

"""
Idempotency Handler (PIN-513 Batch 3B3 Wiring)

L4 handler for request idempotency operations.

Wires from logs/L6_drivers/idempotency_driver.py:
- get_idempotency_store()
- canonical_json(obj)
- hash_request(data)
"""

import logging
from typing import Any, Dict

logger = logging.getLogger("nova.hoc_spine.handlers.idempotency")


class IdempotencyHandler:
    """L4 handler: request idempotency."""

    async def get_store(self) -> Any:
        """Get idempotency store instance."""
        from app.hoc.cus.logs.L6_drivers.idempotency_driver import (
            get_idempotency_store,
        )

        return await get_idempotency_store()

    def canonical_json(self, obj: Any) -> str:
        """Produce canonical JSON for hashing."""
        from app.hoc.cus.logs.L6_drivers.idempotency_driver import canonical_json

        return canonical_json(obj=obj)

    def hash_request(self, data: Dict[str, Any]) -> str:
        """Hash request data for idempotency key."""
        from app.hoc.cus.logs.L6_drivers.idempotency_driver import hash_request

        return hash_request(data=data)
