# Layer: L7 — Legacy Shim (DEPRECATED)
# AUDIENCE: INTERNAL
# Role: Backward-compatible re-export for policy violation service
# Status: DEPRECATED - Will be deleted when callers migrate to direct HOC imports
#
# MIGRATION PATH:
#   Current:  from app.services.policy_violation_service import create_policy_evaluation_sync
#   Future:   from app.hoc.cus.incidents.L5_engines.policy_violation_service import create_policy_evaluation_sync
#
# This shim exists for Phase-2.5 migration. Delete when all callers are updated.
# Reference: PIN-468, POLICIES_CROSS_DOMAIN_OWNERSHIP.md
#
# CANONICAL SOURCE: app/hoc/cus/incidents/L5_engines/policy_violation_service.py

"""
Policy Violation Service - DEPRECATED SHIM

This file re-exports from the canonical incidents domain engine.
Do not add logic here. All implementation is in:
    app.hoc.cus.incidents.L5_engines.policy_violation_service

Migration: Update imports to use the canonical path directly.
"""

# Re-export everything from canonical source
from app.hoc.cus.incidents.L5_engines.policy_violation_service import (
    # Constants
    POLICY_OUTCOME_ADVISORY,
    POLICY_OUTCOME_NO_VIOLATION,
    POLICY_OUTCOME_NOT_APPLICABLE,
    POLICY_OUTCOME_VIOLATION,
    VERIFICATION_MODE,
    # Dataclasses
    PolicyEvaluationResult,
    ViolationFact,
    ViolationIncident,
    # Classes
    PolicyViolationService,
    # Functions
    create_policy_evaluation_sync,
)

__all__ = [
    # Constants
    "POLICY_OUTCOME_ADVISORY",
    "POLICY_OUTCOME_NO_VIOLATION",
    "POLICY_OUTCOME_NOT_APPLICABLE",
    "POLICY_OUTCOME_VIOLATION",
    "VERIFICATION_MODE",
    # Dataclasses
    "PolicyEvaluationResult",
    "ViolationFact",
    "ViolationIncident",
    # Classes
    "PolicyViolationService",
    # Functions
    "create_policy_evaluation_sync",
]
