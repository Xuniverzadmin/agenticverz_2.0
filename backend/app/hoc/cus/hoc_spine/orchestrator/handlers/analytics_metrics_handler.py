# capability_id: CAP-012
# Layer: L4 — HOC Spine (Handler)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: L4 handler — CostSim metrics and alert rules
# Callers: Admin APIs, monitoring endpoints
# Allowed Imports: hoc_spine, hoc.cus.analytics.L5_engines (lazy)
# Forbidden Imports: L1, L2
# Reference: PIN-513 Batch 3A4 Wiring
# artifact_class: CODE

"""
Analytics Metrics Handler (PIN-513 Batch 3A4 Wiring)

L4 handler for CostSim metrics and alert rules.

Wires from analytics/L5_engines/metrics_engine.py:
- get_metrics()
- get_alert_rules()
"""

import logging
from typing import Any

logger = logging.getLogger("nova.hoc_spine.handlers.analytics_metrics")


class AnalyticsMetricsHandler:
    """L4 handler: CostSim metrics and alert rules."""

    def get_metrics(self) -> Any:
        """Get CostSim metrics singleton."""
        from app.hoc.cus.analytics.L5_engines.metrics_engine import get_metrics

        return get_metrics()

    def get_alert_rules(self) -> str:
        """Get Prometheus alert rules for CostSim."""
        from app.hoc.cus.analytics.L5_engines.metrics_engine import get_alert_rules

        return get_alert_rules()
