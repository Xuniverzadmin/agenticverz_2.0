# capability_id: CAP-012
# Layer: L4 — HOC Spine (Handler)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: L4 handler — CostSim configuration visibility
# Callers: Admin APIs, canary, enforcement paths
# Allowed Imports: hoc_spine, hoc.cus.analytics.L5_engines (lazy)
# Forbidden Imports: L1, L2
# Reference: PIN-513 Batch 3A2 Wiring
# artifact_class: CODE

"""
Analytics Config Handler (PIN-513 Batch 3A2 Wiring)

L4 handler — single choke-point for CostSim configuration visibility.

Wires from analytics/L5_engines/config_engine.py:
- get_config()
- is_v2_sandbox_enabled()
- is_v2_disabled_by_drift()
- get_commit_sha()
"""

import logging
from typing import Any

logger = logging.getLogger("nova.hoc_spine.handlers.analytics_config")


class AnalyticsConfigHandler:
    """L4 handler: CostSim configuration read logic.

    Single choke-point for config visibility.
    No direct L5 imports outside L4.
    """

    def get_config(self) -> Any:
        """Get current CostSim configuration."""
        from app.hoc.cus.analytics.L5_engines.config_engine import get_config

        return get_config()

    def is_v2_sandbox_enabled(self) -> bool:
        """Check if V2 sandbox mode is enabled."""
        from app.hoc.cus.analytics.L5_engines.config_engine import (
            is_v2_sandbox_enabled,
        )

        return is_v2_sandbox_enabled()

    def is_v2_disabled_by_drift(self) -> bool:
        """Check if V2 is disabled due to drift."""
        from app.hoc.cus.analytics.L5_engines.config_engine import (
            is_v2_disabled_by_drift,
        )

        return is_v2_disabled_by_drift()

    def get_commit_sha(self) -> str:
        """Get current commit SHA."""
        from app.hoc.cus.analytics.L5_engines.config_engine import get_commit_sha

        return get_commit_sha()
