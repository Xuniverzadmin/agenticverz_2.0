# capability_id: CAP-018
# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api|worker (via L5 engine)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: (module exports)
#   Writes: (module exports)
# Database:
#   Scope: domain (integrations)
#   Models: (see individual drivers)
# Role: integrations domain - drivers (pure DB operations)
# Callers: L5 engines
# Allowed Imports: L6, L7 (models)
# Reference: PIN-470, HOC_LAYER_TOPOLOGY_V1.md, INTEGRATIONS_PHASE2.5_IMPLEMENTATION_PLAN.md

"""
integrations / drivers

L6 Driver exports for the integrations domain.
"""

from .bridges_driver import record_policy_activation
from .cus_health_driver import (
    CusHealthDriver,
    HealthIntegrationRow,
    cus_health_driver_session,
    get_cus_health_driver,
)
from .mcp_driver import (
    McpDriver,
    McpInvocationRow,
    McpServerRow,
    McpToolRow,
    compute_input_hash,
    compute_output_hash,
)
from .proxy_driver import (
    ApiKeyRow,
    GuardrailRow,
    IncidentRow,
    KillSwitchStateRow,
    LatencyStats,
    ProxyDriver,
    TenantRow,
    get_proxy_driver,
)

__all__ = [
    # bridges_driver
    "record_policy_activation",
    # cus_health_driver
    "CusHealthDriver",
    "HealthIntegrationRow",
    "cus_health_driver_session",
    "get_cus_health_driver",
    # mcp_driver (PIN-516)
    "McpDriver",
    "McpServerRow",
    "McpToolRow",
    "McpInvocationRow",
    "compute_input_hash",
    "compute_output_hash",
    # proxy_driver (L2 session.execute refactor)
    "ProxyDriver",
    "ApiKeyRow",
    "TenantRow",
    "KillSwitchStateRow",
    "GuardrailRow",
    "LatencyStats",
    "IncidentRow",
    "get_proxy_driver",
]
