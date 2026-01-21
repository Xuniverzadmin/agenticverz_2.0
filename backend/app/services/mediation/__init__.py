# Layer: L4 — Domain Engines
# Product: system-wide
# Role: Mediation layer for governed data access

"""
Mediation Package

Contains the retrieval mediation layer for governed data access:
- retrieval_mediator: Central mediation point (GAP-065)
"""

from app.services.mediation.retrieval_mediator import (
    RetrievalMediator,
    MediatedResult,
    MediationDeniedError,
    MediationAction,
    PolicyCheckResult,
    EvidenceRecord,
    get_retrieval_mediator,
    configure_retrieval_mediator,
    Connector,
    ConnectorRegistry,
    PolicyChecker,
    EvidenceService,
)

__all__ = [
    # Main classes
    "RetrievalMediator",
    "MediatedResult",
    "MediationDeniedError",
    "MediationAction",
    "PolicyCheckResult",
    "EvidenceRecord",
    # Factory functions
    "get_retrieval_mediator",
    "configure_retrieval_mediator",
    # Protocols (for type hints)
    "Connector",
    "ConnectorRegistry",
    "PolicyChecker",
    "EvidenceService",
]
