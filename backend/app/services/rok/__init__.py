# Layer: L4 — Domain Engines
# Product: system-wide
# Reference: GAP-051 (Phase-Status Invariants)
"""
ROK (Run Orchestration Kernel) Services (GAP-051)

Provides services for ROK phase-status invariant enforcement
using GovernanceConfig flags.

This module provides:
    - PhaseStatusInvariantChecker: Validates phase-status combinations
    - PhaseStatusInvariantEnforcementError: Raised on violations
    - PHASE_STATUS_INVARIANTS: Valid combinations map
    - Helper functions for quick validation
"""

from app.services.rok.phase_status_invariants import (
    InvariantCheckResponse,
    InvariantCheckResult,
    PHASE_STATUS_INVARIANTS,
    PhaseStatusInvariantChecker,
    PhaseStatusInvariantEnforcementError,
    check_phase_status_invariant,
    ensure_phase_status_invariant,
)

__all__ = [
    "InvariantCheckResponse",
    "InvariantCheckResult",
    "PHASE_STATUS_INVARIANTS",
    "PhaseStatusInvariantChecker",
    "PhaseStatusInvariantEnforcementError",
    "check_phase_status_invariant",
    "ensure_phase_status_invariant",
]
