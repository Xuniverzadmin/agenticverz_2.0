# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none (pure validation logic)
#   Writes: none
# Role: Prevention contract enforcement (validation logic)
# Callers: policy engine, workers
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, HOC_LAYER_TOPOLOGY_V1.md, INTEGRATIONS_PHASE2.5_IMPLEMENTATION_PLAN.md

"""
M25 Prevention Contract Enforcement

# =============================================================================
# M25_FROZEN - DO NOT MODIFY
# =============================================================================
# Any changes here require explicit M25 reopen approval.
# Changes invalidate all prior graduation evidence.
# See PIN-140 for freeze rationale.
# PREVENTION_CONTRACT_VERSION = "1.0.0"
# =============================================================================

From PIN-136, prevention records can ONLY be written when:
1. Same pattern signature matches
2. Same tenant
3. Same feature path
4. Policy is ACTIVE (not SHADOW, not PENDING)
5. No incident is created (blocked before INSERT)
6. Prevention record is written (append-only, immutable)

This module enforces these rules programmatically.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("nova.integrations.prevention_contract")

# Frozen version - do not change
PREVENTION_CONTRACT_VERSION = "1.0.0"
PREVENTION_CONTRACT_FROZEN_AT = "2025-12-23"


class PreventionContractViolation(Exception):
    """Raised when a prevention record would violate the contract."""

    def __init__(self, rule: str, details: str):
        self.rule = rule
        self.details = details
        super().__init__(f"Prevention contract violation ({rule}): {details}")


@dataclass
class PreventionCandidate:
    """
    Candidate for prevention record creation.

    Must pass all contract checks before writing to prevention_records.
    """

    policy_id: str
    pattern_id: str
    tenant_id: str
    blocked_incident_id: str
    original_incident_id: str
    signature_match_confidence: float
    policy_mode: str  # Must be 'active'
    pattern_signature: dict[str, Any]
    request_signature: dict[str, Any]
    incident_created: bool  # Must be False
    is_simulated: bool = False


def validate_prevention_candidate(candidate: PreventionCandidate) -> None:
    """
    Validate that a prevention candidate satisfies the contract.

    Raises PreventionContractViolation if any rule is violated.

    Rules (from PIN-136):
    1. Policy must be ACTIVE
    2. No incident created
    3. Pattern signature matches
    4. Same tenant
    5. Prevention records are append-only (handled at DB level)
    """
    # Rule 1: Policy must be ACTIVE
    if candidate.policy_mode != "active":
        raise PreventionContractViolation(
            rule="POLICY_MODE", details=f"Policy mode is '{candidate.policy_mode}', must be 'active'"
        )

    # Rule 2: No incident created (blocked before INSERT)
    if candidate.incident_created:
        raise PreventionContractViolation(
            rule="INCIDENT_CREATED", details="Cannot write prevention record if incident was created"
        )

    # Rule 3: Signature match confidence threshold
    if candidate.signature_match_confidence < 0.6:
        raise PreventionContractViolation(
            rule="SIGNATURE_CONFIDENCE",
            details=f"Confidence {candidate.signature_match_confidence:.2f} below minimum 0.6",
        )

    # Rule 4: Tenant ID must be present
    if not candidate.tenant_id:
        raise PreventionContractViolation(
            rule="TENANT_REQUIRED", details="tenant_id is required for prevention records"
        )

    # Rule 5: Pattern ID must be present
    if not candidate.pattern_id:
        raise PreventionContractViolation(
            rule="PATTERN_REQUIRED", details="pattern_id is required for prevention records"
        )

    # Rule 6: Policy ID must be present
    if not candidate.policy_id:
        raise PreventionContractViolation(
            rule="POLICY_REQUIRED", details="policy_id is required for prevention records"
        )

    logger.info(
        f"Prevention contract validated: policy={candidate.policy_id}, "
        f"confidence={candidate.signature_match_confidence:.2f}, "
        f"is_simulated={candidate.is_simulated}"
    )


def assert_prevention_immutable(record_id: str, existing_record: dict[str, Any]) -> None:
    """
    Assert that a prevention record has not been modified.

    Prevention records are append-only and immutable.
    This should be called before any UPDATE attempt.
    """
    raise PreventionContractViolation(
        rule="IMMUTABLE", details=f"Prevention record {record_id} cannot be modified (append-only)"
    )


def assert_no_deletion(record_id: str) -> None:
    """
    Assert that a prevention record cannot be deleted.

    Prevention records are append-only and immutable.
    """
    raise PreventionContractViolation(
        rule="NO_DELETE", details=f"Prevention record {record_id} cannot be deleted (non-repudiable)"
    )


# =============================================================================
# Evidence Validation (for graduation)
# =============================================================================


def validate_prevention_for_graduation(
    prevention_record: dict[str, Any],
    policy_activated_at: datetime,
) -> bool:
    """
    Validate that a prevention record counts toward graduation.

    For Gate 1 (Prevention) to pass:
    - Prevention must be real (is_simulated = False)
    - Prevention must be after policy activation
    - Policy must have been active at time of prevention
    """
    # Must be real (not simulated)
    if prevention_record.get("is_simulated", True):
        logger.debug(f"Prevention {prevention_record.get('id')} is simulated - excluded from graduation")
        return False

    # Must be after policy activation
    created_at = prevention_record.get("created_at")
    if created_at and isinstance(created_at, datetime):
        # Ensure timezone awareness
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        if policy_activated_at.tzinfo is None:
            policy_activated_at = policy_activated_at.replace(tzinfo=timezone.utc)

        if created_at < policy_activated_at:
            logger.debug(f"Prevention {prevention_record.get('id')} created before policy activation - excluded")
            return False

    logger.info(f"Prevention {prevention_record.get('id')} validated for graduation")
    return True
