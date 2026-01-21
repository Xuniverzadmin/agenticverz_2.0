# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Observability domain services
# Callers: L5 runner, L2 APIs
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: PIN-454 (Cross-Domain Orchestration Audit)

"""
Observability Domain Services

This module provides the facade for trace operations with RAC integration.

Components:
- TraceFacade: Wraps trace store operations with RAC ack emission

Reference: PIN-454 Section 8.2 (Runtime Audit Contract)
"""

from app.services.observability.trace_facade import TraceFacade, get_trace_facade

__all__ = [
    "TraceFacade",
    "get_trace_facade",
]
