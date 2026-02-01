# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Role: Coordinator package — cross-domain mediation (C4 Loop Model)
# Reference: PIN-504 (Cross-Domain Violation Resolution), PIN-487 (Loop Model), PIN-507 (Law 4)
# artifact_class: CODE

# TOMBSTONE: audit_coordinator.py deleted (PIN-507 Law 4, 2026-02-01).
# Handlers inject audit services directly into L5 engines — no coordinator needed.
# Do NOT recreate. See PIN-507 Law 4 remediation.

"""
Coordinators (C4 — Loop Model)

Cross-domain mediators at L4. Coordinators own TOPOLOGY only.
They must NEVER accept session or execution context (Law 4).

- SignalCoordinator: Threshold signal dispatch order (controls→activity)
- DomainBridge: Cross-domain service accessor (returns factories, not instances)
"""

from app.hoc.hoc_spine.orchestrator.coordinators.signal_coordinator import (
    emit_and_persist_threshold_signal,
)

__all__ = [
    "emit_and_persist_threshold_signal",
]
