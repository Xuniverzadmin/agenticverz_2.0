# capability_id: CAP-012
# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: CUSTOMER
# Role: Per-domain bridge for logs capabilities
# Reference: PIN-510 Phase 0A (G1 mitigation — no god object)
# artifact_class: CODE

"""
Logs Bridge (PIN-510)

Domain-scoped capability accessor for logs domain.
"""

import os


class LogsBridge:
    """Capabilities for logs domain. Max 5 methods."""

    def logs_read_service(self):
        """Return LogsReadService singleton."""
        from app.hoc.cus.logs.L5_engines.logs_read_engine import get_logs_read_service
        return get_logs_read_service()

    def traces_store_capability(self):
        """Return TraceStore for run-scoped trace queries (PIN-519).

        PIN-520: Use infrastructure store (not L6_drivers).
        """
        use_postgres_env = os.getenv("USE_POSTGRES_TRACES")
        if use_postgres_env is not None:
            use_postgres = use_postgres_env.lower() == "true"
        else:
            env = os.getenv("ENV", "").lower()
            aos_env = os.getenv("AOS_ENVIRONMENT", "").lower()
            use_postgres = env in ("prod", "production") or aos_env in ("prod", "production")

        if use_postgres:
            from app.hoc.cus.logs.L6_drivers.pg_store import PostgresTraceStore
            return PostgresTraceStore()

        from app.hoc.cus.logs.L6_drivers.trace_store import SQLiteTraceStore
        return SQLiteTraceStore()

    def audit_ledger_read_capability(self, session):
        """Return audit ledger read driver for signal feedback queries (PIN-519)."""
        from app.hoc.cus.logs.L6_drivers.audit_ledger_read_driver import (
            get_audit_ledger_read_driver,
        )
        return get_audit_ledger_read_driver(session)

    def capture_driver_capability(self):
        """
        Return capture_driver module for evidence capture (PIN-520).

        Provides:
            - capture_environment_evidence(ctx, sdk_mode, ...)
        """
        from app.hoc.cus.logs.L6_drivers import capture_driver
        return capture_driver

    def cost_intelligence_capability(self, session):
        """
        Return CostIntelligenceEngine for cost intelligence operations (L2 purity migration).

        Provides:
            - check_feature_tag_exists(tenant_id, tag)
            - list_feature_tags(tenant_id, include_inactive)
            - get_feature_tag(tenant_id, tag)
            - update_feature_tag(tenant_id, tag, ...)
            - get_cost_summary(tenant_id, period_start, period_end, days)
            - get_costs_by_feature(tenant_id, period_start, total_cost)
            - get_costs_by_user(tenant_id, period_start, total_cost)
            - get_costs_by_model(tenant_id, period_start, total_cost)
            - get_recent_anomalies(tenant_id, days, include_resolved)
            - get_cost_projection(tenant_id, lookback_days, forecast_days)
            - list_budgets(tenant_id)
            - get_budget_by_type(tenant_id, budget_type, entity_id)
            - create_budget(...)
            - update_budget(...)
            - get_current_spend(tenant_id, budget_type, entity_id)
        """
        from app.hoc.cus.logs.L6_drivers.cost_intelligence_sync_driver import (
            get_cost_intelligence_sync_driver,
        )
        from app.hoc.cus.logs.L5_engines.cost_intelligence_engine import (
            get_cost_intelligence_engine,
        )

        driver = get_cost_intelligence_sync_driver(session)
        return get_cost_intelligence_engine(driver)


# Singleton
_instance = None


def get_logs_bridge() -> LogsBridge:
    """Get the singleton LogsBridge instance."""
    global _instance
    if _instance is None:
        _instance = LogsBridge()
    return _instance


__all__ = ["LogsBridge", "get_logs_bridge"]
