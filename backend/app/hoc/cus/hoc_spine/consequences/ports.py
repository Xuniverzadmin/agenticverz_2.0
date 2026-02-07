# Layer: L4 — HOC Spine (Consequences)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (post-dispatch)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: none (protocol definition only)
# Role: Consequence adapter protocol — port for post-dispatch side effects
# Callers: consequences/pipeline.py
# Allowed Imports: dispatch_audit (DispatchRecord type)
# Forbidden Imports: L1, L2, L5, L6, sqlalchemy, app.db
# Reference: Constitution §2.3, Gap G4 closure
# artifact_class: CODE

"""
Consequence Adapter Protocol.

Defines the port that all consequence adapters must satisfy.
Adapters run AFTER dispatch completes — post-commit only,
never inside the operation's transaction (Constitution §2.3).
"""

from typing import Protocol, runtime_checkable

from app.hoc.cus.hoc_spine.services.dispatch_audit import DispatchRecord


@runtime_checkable
class ConsequenceAdapter(Protocol):
    """
    Port for post-dispatch consequence adapters.

    Implementations must:
    - Accept a DispatchRecord (immutable, frozen)
    - Be non-blocking (no long I/O in the sync path)
    - Be side-effect safe (failures must not propagate)
    - Have a name property for logging/diagnostics

    The pipeline wraps each adapter call in try/except,
    so a failing adapter never breaks other adapters.
    """

    @property
    def name(self) -> str:
        """Human-readable adapter name for logging."""
        ...

    def handle(self, record: DispatchRecord) -> None:
        """
        Process a dispatch record.

        Called synchronously after audit store persistence.
        Must not raise — pipeline catches all exceptions.
        """
        ...
