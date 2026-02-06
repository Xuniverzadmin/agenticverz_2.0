# Layer: L4 — HOC Spine (Bridge)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (via L4 handler)
#   Execution: async
# Role: Analytics domain bridge — capability factory for analytics L5 engines
# Callers: hoc_spine/orchestrator/handlers/analytics_*.py
# Allowed Imports: hoc_spine (authority, services, schemas)
# Forbidden Imports: L1, L2, direct L5/L6 at top level
# Reference: PIN-520 (L4 Uniformity Initiative), PIN-504 (C4 Loop Model)
# artifact_class: CODE

"""
Analytics Bridge (L4 Coordinator)

Domain-specific capability factory for analytics L5 engines.
Returns factory callables that handlers bind with session.

Bridge Contract:
    - Max 5 methods per bridge
    - Returns facades/engines (not sessions)
    - Lazy imports from domain L5/L6
    - No cross-domain imports at top level

Switchboard Pattern (Law 4 - PIN-507):
    - Never accepts session parameters
    - Returns factory callables
    - Handler binds session (Law 4 responsibility)
    - No retry logic, no decisions, no state

Usage:
    from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.analytics_bridge import (
        get_analytics_bridge,
    )

    bridge = get_analytics_bridge()
    config = bridge.config_capability()
    result = await config.is_v2_disabled_by_drift()
"""

from typing import Any


class AnalyticsBridge:
    """
    Analytics domain capability factory.

    Provides lazy access to analytics L5 engines without importing them
    at module level. This preserves layer isolation and enables testing.
    """

    def config_capability(self) -> Any:
        """
        Return analytics config engine module.

        Provides:
            - is_v2_disabled_by_drift()
            - is_v2_sandbox_enabled()
            - get_config()
        """
        from app.hoc.cus.analytics.L5_engines import config_engine

        return config_engine

    def sandbox_capability(self) -> Any:
        """
        Return sandbox simulation module.

        Provides:
            - simulate_with_sandbox(session, params)
        """
        from app.hoc.cus.analytics.L5_engines import sandbox_engine

        return sandbox_engine

    def canary_capability(self) -> Any:
        """
        Return canary deployment module.

        Provides:
            - run_canary(session, params)
        """
        from app.hoc.cus.analytics.L5_engines import canary_engine

        return canary_engine

    def divergence_capability(self) -> Any:
        """
        Return divergence detection module.

        Provides:
            - generate_divergence_report(session, params)
        """
        from app.hoc.cus.analytics.L5_engines import divergence_engine

        return divergence_engine

    def datasets_capability(self) -> Any:
        """
        Return dataset validation module.

        Provides:
            - get_dataset_validator()
            - validate_all_datasets()
            - validate_dataset()
        """
        from app.hoc.cus.analytics.L5_engines import datasets_engine

        return datasets_engine

    def cost_write_capability(self, session) -> Any:
        """
        Return cost write service for sync DB operations (PIN-520 Phase 1).

        Used by cost_intelligence.py for creating/updating cost records,
        feature tags, and budgets.

        Args:
            session: SQLModel Session for DB operations

        Returns:
            CostWriteService instance bound to session
        """
        from app.hoc.cus.analytics.L6_drivers.cost_write_driver import (
            CostWriteDriver,
        )

        return CostWriteDriver(session)


# =============================================================================
# MODULE SINGLETON
# =============================================================================

_bridge_instance: AnalyticsBridge | None = None


def get_analytics_bridge() -> AnalyticsBridge:
    """
    Get the analytics bridge singleton.

    Returns the same instance for the lifetime of the process.
    """
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = AnalyticsBridge()
    return _bridge_instance


# =============================================================================
# ANALYTICS ENGINE BRIDGE (extends AnalyticsBridge to avoid 5-method limit)
# =============================================================================


class AnalyticsEngineBridge:
    """Extended capabilities for analytics domain coordinators. Max 5 methods."""

    def anomaly_coordinator_capability(self):
        """
        Return anomaly incident coordinator for detection + ingestion (PIN-520).

        Used by detection_facade.py to run cost anomaly detection without
        importing L4 orchestrator directly. L4 owns the orchestration decision.
        """
        from app.hoc.cus.hoc_spine.orchestrator.coordinators.anomaly_incident_coordinator import (
            get_anomaly_incident_coordinator,
        )

        return get_anomaly_incident_coordinator()

    def detection_facade_capability(self):
        """
        Return detection facade module for anomaly detection operations (PIN-520).

        Provides access to DetectionFacade for L4 handlers.
        """
        from app.hoc.cus.analytics.L5_engines import detection_facade

        return detection_facade

    def alert_driver_capability(self):
        """
        Return AlertDriver class for alert queue DB operations (PIN-520).

        Used by alert_worker_engine.py for alert processing.
        L4 owns access to hoc_spine drivers; L5 receives via injection.
        """
        from app.hoc.cus.hoc_spine.drivers.alert_driver import AlertDriver

        return AlertDriver

    def alert_adapter_factory_capability(self):
        """
        Return get_alert_delivery_adapter factory for HTTP delivery (PIN-520).

        Used by alert_worker_engine.py for Alertmanager delivery.
        L4 owns access to hoc_spine services; L5 receives via injection.
        """
        from app.hoc.cus.hoc_spine.services import get_alert_delivery_adapter

        return get_alert_delivery_adapter


_engine_bridge_instance: AnalyticsEngineBridge | None = None


def get_analytics_engine_bridge() -> AnalyticsEngineBridge:
    """Get the singleton AnalyticsEngineBridge instance."""
    global _engine_bridge_instance
    if _engine_bridge_instance is None:
        _engine_bridge_instance = AnalyticsEngineBridge()
    return _engine_bridge_instance


__all__ = [
    "AnalyticsBridge",
    "get_analytics_bridge",
    "AnalyticsEngineBridge",
    "get_analytics_engine_bridge",
]
