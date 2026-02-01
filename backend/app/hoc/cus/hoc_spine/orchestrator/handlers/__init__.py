# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Role: Domain operation handlers — one module per domain, registered at import time
# Reference: PIN-491 (L2-L4-L5 Construction Plan)
# artifact_class: CODE

"""
Operation Handlers Package

Each module in this package implements OperationHandler for a specific domain.
Handlers are registered with the OperationRegistry at import time.

Structure:
    handlers/
    ├── __init__.py          # This file — imports all domain handlers
    ├── overview_handler.py  # Phase A.1
    ├── account_handler.py   # Phase A.1
    ├── ...                  # One per domain
    └── policies_handler.py  # Phase A.5

Registration happens via register_all_handlers() called from app startup.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.hoc.cus.hoc_spine.orchestrator.operation_registry import OperationRegistry


def register_all_handlers(registry: "OperationRegistry") -> None:
    """
    Register all domain operation handlers.

    Called once at application startup. Each domain handler module
    provides a register() function that registers its operations.

    Import is lazy (inside this function) so handler modules are only
    loaded when explicitly wired.
    """
    # Phase A.1 — Facade-pattern domains (10 operations)
    from app.hoc.cus.hoc_spine.orchestrator.handlers import overview_handler
    from app.hoc.cus.hoc_spine.orchestrator.handlers import account_handler
    from app.hoc.cus.hoc_spine.orchestrator.handlers import analytics_handler
    from app.hoc.cus.hoc_spine.orchestrator.handlers import api_keys_handler
    from app.hoc.cus.hoc_spine.orchestrator.handlers import incidents_handler
    from app.hoc.cus.hoc_spine.orchestrator.handlers import integrations_handler

    overview_handler.register(registry)      # overview.query
    account_handler.register(registry)       # account.query, account.notifications
    analytics_handler.register(registry)     # analytics.query, analytics.detection
    api_keys_handler.register(registry)      # api_keys.query
    incidents_handler.register(registry)     # incidents.query
    integrations_handler.register(registry)  # integrations.query, .connectors, .datasources

    # Phase A.2 — Compound facade domains (6 operations: logs)
    from app.hoc.cus.hoc_spine.orchestrator.handlers import logs_handler

    logs_handler.register(registry)  # logs.query, .evidence, .certificate, .replay, .evidence_report, .pdf

    # Phase A.3 — Controls domain (2 operations: controls)
    from app.hoc.cus.hoc_spine.orchestrator.handlers import controls_handler

    controls_handler.register(registry)  # controls.query, .thresholds

    # Phase A.4 — Activity domain (4 operations: activity)
    from app.hoc.cus.hoc_spine.orchestrator.handlers import activity_handler

    activity_handler.register(registry)  # activity.query, .signal_fingerprint, .signal_feedback, .telemetry

    # Phase A.5 — Policies domain (9 operations: policies)
    from app.hoc.cus.hoc_spine.orchestrator.handlers import policies_handler

    policies_handler.register(registry)  # policies.query, .enforcement, .governance, .lessons, .policy_facade, .limits, .rules, .rate_limits, .simulate
