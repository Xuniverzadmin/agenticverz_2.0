# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Role: logs domain - engines package
# Reference: HOC_LAYER_TOPOLOGY_V1.md
# Location: hoc/cus/logs/L5_engines/__init__.py
# L4 is reserved for general/L4_runtime/ only per HOC Layer Topology.

"""
logs / L5_engines

Domain engines and facades for the logs domain.

WARNING: Eager re-exports below cause the entire domain (L5+L6) to load
when ANY single engine in this package is imported. Known Law 0 risk —
masked import failures can hide downstream violations. Deferred refactor
to lazy imports tracked in PIN-507 Law 0 subsection.
"""

from app.hoc.cus.logs.L5_engines.logs_facade import (
    LogsFacade,
    get_logs_facade,
)
from app.hoc.cus.logs.L5_engines.evidence_facade import (
    EvidenceFacade,
    get_evidence_facade,
)
from app.hoc.cus.logs.L5_engines.trace_facade import (
    TraceFacade,
    get_trace_facade,
)

__all__ = [
    # Facades
    "LogsFacade",
    "get_logs_facade",
    "EvidenceFacade",
    "get_evidence_facade",
    "TraceFacade",
    "get_trace_facade",
]
