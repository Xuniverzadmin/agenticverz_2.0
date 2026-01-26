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

__all__ = [
    # bridges_driver
    "record_policy_activation",
]
