# Layer: L4 — HOC Spine (Bridge)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (via L4 handler)
#   Execution: async
# Role: Overview domain bridge — capability factory for overview L5 engines
# Callers: hoc_spine/orchestrator/handlers/overview_handler.py
# Allowed Imports: hoc_spine (authority, services, schemas)
# Forbidden Imports: L1, L2, direct L5/L6 at top level
# Reference: PIN-520 (L4 Uniformity Initiative), PIN-504 (C4 Loop Model)
# artifact_class: CODE

"""
Overview Bridge (L4 Coordinator)

Domain-specific capability factory for overview L5 engines.
Returns module references for lazy access to overview capabilities.

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

Note:
    Overview is a minimal domain (dashboard aggregation point).
    It has a single facade that aggregates data from other domains
    via hoc_spine coordinators.

Usage:
    from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.overview_bridge import (
        get_overview_bridge,
    )

    bridge = get_overview_bridge()
    facade = bridge.overview_capability()
    highlights = await facade.get_highlights(session, tenant_id)
"""

from typing import Any


class OverviewBridge:
    """
    Overview domain capability factory.

    Provides lazy access to overview L5 engines without importing them
    at module level. This preserves layer isolation and enables testing.

    Note: Overview is a minimal domain with primarily a single facade.
    """

    def overview_capability(self) -> Any:
        """
        Return overview facade module.

        Provides:
            - overview_facade (get_highlights, get_dashboard_data, get_summary)
        """
        from app.hoc.cus.overview.L5_engines import overview_facade

        return overview_facade

    def dashboard_capability(self) -> Any:
        """
        Return dashboard-specific capability (alias for overview).

        Provides same as overview_capability but with semantic clarity
        for dashboard-focused operations.
        """
        from app.hoc.cus.overview.L5_engines import overview_facade

        return overview_facade


# =============================================================================
# MODULE SINGLETON
# =============================================================================

_bridge_instance: OverviewBridge | None = None


def get_overview_bridge() -> OverviewBridge:
    """
    Get the overview bridge singleton.

    Returns the same instance for the lifetime of the process.
    """
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = OverviewBridge()
    return _bridge_instance


__all__ = [
    "OverviewBridge",
    "get_overview_bridge",
]
