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
- CanaryCoordinator: Scheduled canary validation runs
- ExecutionCoordinator: Pre-execution scoping + job lifecycle
- ReplayCoordinator: Deterministic replay enforcement
"""

from app.hoc.cus.hoc_spine.orchestrator.coordinators.signal_coordinator import (
    emit_and_persist_threshold_signal,
)

# PIN-520 Wiring: Export coordinators awaiting integration
from app.hoc.cus.hoc_spine.orchestrator.coordinators.canary_coordinator import (
    CanaryCoordinator,
)
from app.hoc.cus.hoc_spine.orchestrator.coordinators.execution_coordinator import (
    ExecutionCoordinator,
)
from app.hoc.cus.hoc_spine.orchestrator.coordinators.replay_coordinator import (
    ReplayCoordinator,
)

__all__ = [
    "emit_and_persist_threshold_signal",
    # Coordinators (PIN-520)
    "CanaryCoordinator",
    "ExecutionCoordinator",
    "ReplayCoordinator",
]
