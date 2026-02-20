# capability_id: CAP-012
# Layer: L4 — HOC Spine (Services)
# AUDIENCE: INTERNAL
# Role: HOC Spine services package
# Reference: PIN-520 Wiring Audit, PIN-521 Config Extraction
# artifact_class: CODE

"""
HOC Spine Services

L5-equivalent services that provide specific capabilities:
- AlertDeliveryAdapter: HTTP delivery to Alertmanager
- CostSimConfig: CostSim V2 configuration (env vars)
"""

from app.hoc.cus.hoc_spine.services.alert_delivery import (
    AlertDeliveryAdapter,
    DeliveryResult,
    get_alert_delivery_adapter,
)
from app.hoc.cus.hoc_spine.services.costsim_config import (
    CostSimConfig,
    get_commit_sha,
    get_config,
    is_v2_disabled_by_drift,
    is_v2_sandbox_enabled,
)
from app.hoc.cus.hoc_spine.services.costsim_metrics import (
    CostSimMetrics,
    get_metrics,
)

__all__ = [
    # Alert delivery
    "AlertDeliveryAdapter",
    "DeliveryResult",
    "get_alert_delivery_adapter",
    # CostSim config (PIN-521)
    "CostSimConfig",
    "get_config",
    "is_v2_sandbox_enabled",
    "is_v2_disabled_by_drift",
    "get_commit_sha",
    # CostSim metrics (PIN-521)
    "CostSimMetrics",
    "get_metrics",
]
