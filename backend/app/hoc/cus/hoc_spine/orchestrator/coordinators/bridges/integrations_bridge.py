# capability_id: CAP-012
# Layer: L4 — HOC Spine (Bridge)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (via L4 handler)
#   Execution: async
# Role: Integrations domain bridge — capability factory for integrations L5 engines
# Callers: hoc_spine/orchestrator/handlers/integrations_handler.py
# Allowed Imports: hoc_spine (authority, services, schemas)
# Forbidden Imports: L1, L2, direct L5/L6 at top level
# Reference: PIN-520 (L4 Uniformity Initiative), PIN-504 (C4 Loop Model)
# artifact_class: CODE

"""
Integrations Bridge (L4 Coordinator)

Domain-specific capability factory for integrations L5 engines.
Returns module references for lazy access to integration capabilities.

Bridge Contract:
    - Max 5 capability methods per bridge
    - Returns modules (not sessions)
    - Lazy imports from domain L5/L6
    - No cross-domain imports at top level

Switchboard Pattern (Law 4 - PIN-507):
    - Never accepts session parameters
    - Returns module references
    - Handler binds session (Law 4 responsibility)
    - No retry logic, no decisions, no state

Usage:
    from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.integrations_bridge import (
        get_integrations_bridge,
    )

    bridge = get_integrations_bridge()
    mcp = bridge.mcp_capability()
    result = await mcp.invoke_tool(session, tool_name, params)
"""

from typing import Any


class IntegrationsBridge:
    """
    Integrations domain capability factory.

    Provides lazy access to integrations L5 engines without importing them
    at module level. This preserves layer isolation and enables testing.
    """

    def mcp_capability(self) -> Any:
        """
        Return MCP (Model Context Protocol) module.

        Provides:
            - mcp_tool_invocation_engine (invoke_tool, list_tools)
            - mcp_connector_engine (get_connector, list_connectors)
            - mcp_server_engine (register_server, get_server)
        """
        from app.hoc.cus.integrations.L5_engines import mcp_tool_invocation_engine

        return mcp_tool_invocation_engine

    def connector_capability(self) -> Any:
        """
        Return connector registry module.

        Provides:
            - connectors_facade (get_connector, list_connectors, register_connector)
        """
        from app.hoc.cus.integrations.L5_engines import connectors_facade

        return connectors_facade

    def health_capability(self) -> Any:
        """
        Return integration health module.

        Provides:
            - cus_health_engine (check_health, get_status)
        """
        from app.hoc.cus.integrations.L5_engines import cus_health_engine

        return cus_health_engine

    def datasources_capability(self) -> Any:
        """
        Return datasources module.

        Provides:
            - datasources_facade (get_datasource, list_datasources, create_datasource)
        """
        from app.hoc.cus.integrations.L5_engines import datasources_facade

        return datasources_facade

    def credentials_capability(self) -> Any:
        """
        Return credentials/vault module.

        Provides:
            - cus_integration_engine (resolve_credential, store_credential)
        """
        from app.hoc.cus.integrations.L5_engines import cus_integration_engine

        return cus_integration_engine


# =============================================================================
# MODULE SINGLETON
# =============================================================================

_bridge_instance: IntegrationsBridge | None = None


def get_integrations_bridge() -> IntegrationsBridge:
    """
    Get the integrations bridge singleton.

    Returns the same instance for the lifetime of the process.
    """
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = IntegrationsBridge()
    return _bridge_instance


# =============================================================================
# INTEGRATIONS DRIVER BRIDGE (extends IntegrationsBridge for L6 drivers)
# =============================================================================


class IntegrationsDriverBridge:
    """Extended capabilities for integrations L6 drivers. Max 5 methods."""

    def worker_registry_capability(self, session):
        """
        Return worker registry service for worker lifecycle management (PIN-L2-PURITY).

        Used by tenants.py for worker registration and queries.
        """
        from app.hoc.cus.integrations.L6_drivers.worker_registry_driver import (
            WorkerRegistryService,
        )

        return WorkerRegistryService(session)

    def worker_registry_exceptions(self):
        """
        Return worker registry exception types for except clauses (PIN-L2-PURITY).

        Used by tenants.py for exception handling.
        """
        from app.hoc.cus.integrations.L6_drivers.worker_registry_driver import (
            WorkerNotFoundError,
        )

        return {"WorkerNotFoundError": WorkerNotFoundError}

    def incident_creator_capability(self):
        """
        Return incident creator function for cost anomaly → incident creation (PIN-520).

        Used by cost_bridges_engine.py CostLoopBridge to create incidents without
        importing orchestrator directly. L4 owns the orchestration decision.
        """
        from app.hoc.cus.hoc_spine.orchestrator import create_incident_from_cost_anomaly_sync

        return create_incident_from_cost_anomaly_sync


_driver_bridge_instance: IntegrationsDriverBridge | None = None


def get_integrations_driver_bridge() -> IntegrationsDriverBridge:
    """Get the singleton IntegrationsDriverBridge instance."""
    global _driver_bridge_instance
    if _driver_bridge_instance is None:
        _driver_bridge_instance = IntegrationsDriverBridge()
    return _driver_bridge_instance


__all__ = [
    "IntegrationsBridge",
    "get_integrations_bridge",
    "IntegrationsDriverBridge",
    "get_integrations_driver_bridge",
]
