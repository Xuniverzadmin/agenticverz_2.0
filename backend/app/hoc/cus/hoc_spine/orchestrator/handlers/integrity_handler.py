# capability_id: CAP-012
# Layer: L4 — HOC Spine (Handler)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: L4 handler — integrity computation (V2)
# Callers: Evidence flows, audit APIs
# Allowed Imports: hoc_spine, hoc.cus.logs.L6_drivers (lazy)
# Forbidden Imports: L1, L2
# Reference: PIN-513 Batch 3B1 Wiring
# artifact_class: CODE

"""
Integrity Handler (PIN-513 Batch 3B1 Wiring)

L4 handler for V2 integrity computation.

Wires from logs/L6_drivers/integrity_driver.py:
- compute_integrity_v2(run_id)
"""

import logging
from typing import Any, Dict

logger = logging.getLogger("nova.hoc_spine.handlers.integrity")


class IntegrityHandler:
    """L4 handler: V2 integrity computation."""

    def compute(self, run_id: str) -> Dict[str, Any]:
        """Compute V2 integrity for a run."""
        from app.hoc.cus.logs.L6_drivers.integrity_driver import compute_integrity_v2

        result = compute_integrity_v2(run_id=run_id)
        logger.info(
            "integrity_v2_computed",
            extra={"run_id": run_id},
        )
        return result
