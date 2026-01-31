# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (called by integrations adapter)
#   Execution: async
# Role: Logs coordinator — cross-domain logs read access (C4 Loop Model)
# Callers: integrations/adapters/customer_logs_adapter.py
# Allowed Imports: hoc_spine, hoc.cus.logs (lazy — L4 can import L5/L6)
# Forbidden Imports: L1, L2
# Reference: PIN-504 (Cross-Domain Violation Resolution), PIN-487 (Loop Model)
# artifact_class: CODE

"""
Logs Coordinator (C4 — Loop Model)

Provides cross-domain access to logs read services.
Replaces direct integrations→logs L5 import.

Pattern:
    integrations adapter → LogsCoordinator → logs L5 engine
"""


def get_logs_read_service_via_spine():
    """
    Get the LogsReadService singleton via L4 spine.

    This function exists so that non-logs domains can access logs read
    services without importing L5 engines directly (PIN-504).

    Legal: L4 can import L5.
    """
    from app.hoc.cus.logs.L5_engines.logs_read_engine import get_logs_read_service

    return get_logs_read_service()
