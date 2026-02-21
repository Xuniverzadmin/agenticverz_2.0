# capability_id: CAP-012
# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: CUSTOMER
# Role: Per-domain bridge package — domain-scoped capability accessors
# Reference: PIN-510 Phase 0A
# artifact_class: CODE

"""
Per-Domain Bridges (PIN-510 Phase 0A)

Each bridge provides lazy-loaded capability accessors for one target domain.
Replaces monolithic DomainBridge with domain-scoped bridges.

Rules:
- Max 5 capability methods per bridge (CI check 19)
- Bridge never accepts session — returns capability bound to caller's session
- Lazy imports only (no circular deps)
- Only L4 handlers and coordinators may use bridges
"""

from .account_bridge import AccountBridge, get_account_bridge
from .activity_bridge import ActivityBridge, get_activity_bridge
from .analytics_bridge import AnalyticsBridge, get_analytics_bridge
from .api_keys_bridge import ApiKeysBridge, get_api_keys_bridge
from .controls_bridge import ControlsBridge, get_controls_bridge
from .incidents_bridge import (
    IncidentsBridge,
    IncidentsEngineBridge,
    get_incidents_bridge,
    get_incidents_engine_bridge,
)
from .integrations_bridge import (
    IntegrationsBridge,
    IntegrationsDriverBridge,
    get_integrations_bridge,
    get_integrations_driver_bridge,
)
from .logs_bridge import LogsBridge, get_logs_bridge
from .overview_bridge import OverviewBridge, get_overview_bridge
from .policies_bridge import (
    PoliciesBridge,
    PoliciesEngineBridge,
    get_policies_bridge,
    get_policies_engine_bridge,
)

__all__ = [
    "AccountBridge", "get_account_bridge",
    "ActivityBridge", "get_activity_bridge",
    "AnalyticsBridge", "get_analytics_bridge",
    "ApiKeysBridge", "get_api_keys_bridge",
    "ControlsBridge", "get_controls_bridge",
    "IncidentsBridge", "get_incidents_bridge",
    "IncidentsEngineBridge", "get_incidents_engine_bridge",
    "IntegrationsBridge", "get_integrations_bridge",
    "IntegrationsDriverBridge", "get_integrations_driver_bridge",
    "LogsBridge", "get_logs_bridge",
    "OverviewBridge", "get_overview_bridge",
    "PoliciesBridge", "get_policies_bridge",
    "PoliciesEngineBridge", "get_policies_engine_bridge",
]
