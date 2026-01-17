# Layer: L4 — Domain Engine
# Product: founder-console
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Ops domain services for Founder Console
# Callers: Ops API (L2)
# Allowed Imports: L5, L6 (infra, db)
# Forbidden Imports: L1, L2, L3
# Reference: API-001 Guardrail (Domain Facade Required)

"""
Ops Domain Services

L4 services for Founder Console operations:
- OpsFacade: External access point for ops operations
- DatabaseErrorStore: ErrorStoreProtocol implementation

Design Rules:
- External code MUST use OpsFacade (API-001)
- Internal services accessed only via facade
"""

from app.services.ops.facade import OpsFacade, get_ops_facade

__all__ = [
    "OpsFacade",
    "get_ops_facade",
]
