# capability_id: CAP-012
# Layer: L5 — Execution & Workers
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Run Orchestration Kernel module exports
# Callers: WorkerPool (L5), RunRunner (L5)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L4
# Reference: PIN-454 (Cross-Domain Orchestration Audit)

"""
Run Orchestration Module

This module provides the Run Orchestration Kernel (ROK) for managing
run lifecycle with audit contract integration.

Components:
- RunOrchestrationKernel: Single authority for run lifecycle
- PhaseStateMachine: Phase state tracking
- RunPhase: Phase enum (CREATED → AUTHORIZED → EXECUTING → ...)

Usage:
    from app.hoc.int.worker.orchestration import create_rok, RunPhase

    kernel = create_rok(run_id)
    kernel.declare_expectations()

    if kernel.authorize():
        kernel.begin_execution()
        # ... execution ...
        kernel.execution_complete(success=True)
        kernel.governance_check()
        kernel.begin_finalization()
        kernel.finalize()

Reference: PIN-454 Section 8.1 (ROK Architecture)
"""

from app.hoc.int.worker.orchestration.phases import (
    PhaseContext,
    PhaseStateMachine,
    PhaseTransition,
    PhaseTransitionError,
    PhaseStatusInvariantError,
    RunPhase,
    VALID_TRANSITIONS,
    PHASE_STATUS_INVARIANTS,
    PHASE_STATUS_INVARIANT_ENFORCE,
    assert_phase_status_invariant,
    get_expected_statuses_for_phase,
)
from app.hoc.int.worker.orchestration.run_orchestration_kernel import (
    GovernanceCheckError,
    RunOrchestrationKernel,
    create_rok,
)

__all__ = [
    # Phases
    "RunPhase",
    "PhaseStateMachine",
    "PhaseContext",
    "PhaseTransition",
    "PhaseTransitionError",
    "VALID_TRANSITIONS",
    # Phase-Status Invariants (PIN-454)
    "PhaseStatusInvariantError",
    "PHASE_STATUS_INVARIANTS",
    "PHASE_STATUS_INVARIANT_ENFORCE",
    "assert_phase_status_invariant",
    "get_expected_statuses_for_phase",
    # ROK
    "RunOrchestrationKernel",
    "GovernanceCheckError",
    "create_rok",
]
