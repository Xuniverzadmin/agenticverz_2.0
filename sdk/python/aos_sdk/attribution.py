"""
AOS SDK Attribution Enforcement

This module implements attribution validation per:
- AOS_SDK_ATTRIBUTION_CONTRACT.md
- RUN_VALIDATION_RULES.md (R1-R8)
- SDSR_ATTRIBUTION_INVARIANT.md

Every run must have explicit attribution:
- agent_id: REQUIRED
- actor_type: REQUIRED (HUMAN | SYSTEM | SERVICE)
- origin_system_id: REQUIRED
- actor_id: REQUIRED iff actor_type == HUMAN

Validation happens BEFORE any network call.
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import FrozenSet, List, Optional

logger = logging.getLogger("aos_sdk.attribution")


# =============================================================================
# Error Codes (Canonical)
# =============================================================================


class AttributionErrorCode(str, Enum):
    """
    Attribution validation error codes.

    These codes are contractual — do not change without governance approval.
    Reference: docs/sdk/SDK_ATTRIBUTION_ENFORCEMENT.md
    """

    ATTR_AGENT_MISSING = "ATTR_AGENT_MISSING"
    ATTR_ACTOR_TYPE_MISSING = "ATTR_ACTOR_TYPE_MISSING"
    ATTR_ACTOR_TYPE_INVALID = "ATTR_ACTOR_TYPE_INVALID"
    ATTR_ACTOR_ID_REQUIRED = "ATTR_ACTOR_ID_REQUIRED"
    ATTR_ACTOR_ID_FORBIDDEN = "ATTR_ACTOR_ID_FORBIDDEN"
    ATTR_ORIGIN_SYSTEM_MISSING = "ATTR_ORIGIN_SYSTEM_MISSING"


class AttributionError(Exception):
    """
    Raised when attribution validation fails.

    This error is BLOCKING — the run will not be created.
    SDK consumers must fix their code, not catch and ignore.

    Attributes:
        code: The specific error code
        message: Human-readable error message
        field: The field that failed validation
    """

    def __init__(self, code: AttributionErrorCode, message: str, field: str):
        self.code = code
        self.message = message
        self.field = field
        super().__init__(f"[{code.value}] {message}")

    def to_dict(self) -> dict:
        """Convert error to dictionary for logging/serialization."""
        return {
            "error_type": "attribution_validation",
            "code": self.code.value,
            "message": self.message,
            "field": self.field,
        }


# =============================================================================
# Actor Types (Closed Set)
# =============================================================================


class ActorType(str, Enum):
    """
    Actor classification. This is a CLOSED SET.

    Adding new values requires governance approval.
    Reference: RUN_VALIDATION_RULES.md Rule R3
    """

    HUMAN = "HUMAN"  # Real human user with identity
    SYSTEM = "SYSTEM"  # Automated process (cron, scheduler, policy trigger)
    SERVICE = "SERVICE"  # Service-to-service call (internal API, worker)


# Valid actor types as a frozen set for fast lookup
VALID_ACTOR_TYPES: FrozenSet[str] = frozenset({"HUMAN", "SYSTEM", "SERVICE"})

# Legacy sentinel values that are FORBIDDEN in new runs
FORBIDDEN_AGENT_IDS: FrozenSet[str] = frozenset({"legacy-unknown", ""})
FORBIDDEN_ORIGIN_SYSTEM_IDS: FrozenSet[str] = frozenset({"legacy-migration", ""})


# =============================================================================
# Attribution Context
# =============================================================================


@dataclass(frozen=True)
class AttributionContext:
    """
    Attribution context for run creation.

    This is the ONLY way to provide attribution.
    All fields are validated before any network call.

    Attributes:
        agent_id: REQUIRED - Executing agent identifier
        actor_type: REQUIRED - HUMAN | SYSTEM | SERVICE
        origin_system_id: REQUIRED - Originating system identifier
        actor_id: REQUIRED if actor_type == HUMAN, must be None otherwise
        origin_ts: Auto-set if not provided
        origin_ip: Best effort, not validated
    """

    agent_id: str
    actor_type: str
    origin_system_id: str
    actor_id: Optional[str] = None
    origin_ts: Optional[datetime] = None
    origin_ip: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for API payload."""
        result = {
            "agent_id": self.agent_id,
            "actor_type": self.actor_type.upper() if self.actor_type else None,
            "origin_system_id": self.origin_system_id,
        }
        if self.actor_id is not None:
            result["actor_id"] = self.actor_id
        if self.origin_ts is not None:
            result["origin_ts"] = self.origin_ts.isoformat()
        if self.origin_ip is not None:
            result["origin_ip"] = self.origin_ip
        return result


# =============================================================================
# Enforcement Mode
# =============================================================================


class EnforcementMode(str, Enum):
    """
    Attribution enforcement mode.

    Reference: docs/sdk/SDK_ATTRIBUTION_ENFORCEMENT.md Section 4
    """

    SHADOW = "shadow"  # Log violations, don't reject
    SOFT = "soft"  # Reject unless override flag is set
    HARD = "hard"  # Always reject invalid attribution


def get_enforcement_mode() -> EnforcementMode:
    """Get enforcement mode from environment."""
    mode = os.getenv("AOS_ATTRIBUTION_ENFORCEMENT", "hard").lower()
    if mode == "shadow":
        return EnforcementMode.SHADOW
    elif mode == "soft":
        return EnforcementMode.SOFT
    else:
        return EnforcementMode.HARD


def is_legacy_override_enabled() -> bool:
    """Check if legacy override is enabled (soft mode only)."""
    return os.getenv("AOS_ALLOW_ATTRIBUTION_LEGACY", "false").lower() == "true"


# =============================================================================
# Validation Logic
# =============================================================================


def validate_attribution(
    ctx: AttributionContext,
    *,
    enforcement_mode: Optional[EnforcementMode] = None,
    allow_legacy_override: Optional[bool] = None,
) -> List[AttributionError]:
    """
    Validate attribution context before run creation.

    This function enforces:
    - R1: agent_id is REQUIRED and non-empty
    - R2: actor_type is REQUIRED
    - R3: actor_type must be from closed set (HUMAN | SYSTEM | SERVICE)
    - R4: actor_id is REQUIRED if actor_type == HUMAN
    - R5: actor_id MUST be NULL if actor_type != HUMAN
    - origin_system_id is REQUIRED

    Args:
        ctx: Attribution context to validate
        enforcement_mode: Override for enforcement mode (default: from env)
        allow_legacy_override: Override for legacy flag (default: from env)

    Returns:
        List of validation errors (empty if valid)

    Raises:
        AttributionError: In hard mode, or soft mode without override
    """
    # Determine enforcement mode
    mode = enforcement_mode or get_enforcement_mode()
    override = (
        allow_legacy_override
        if allow_legacy_override is not None
        else is_legacy_override_enabled()
    )

    errors: List[AttributionError] = []

    # ─────────────────────────────────────────────────────────────────────────
    # Rule R1: agent_id REQUIRED
    # ─────────────────────────────────────────────────────────────────────────
    if not ctx.agent_id or ctx.agent_id.strip() == "":
        errors.append(
            AttributionError(
                code=AttributionErrorCode.ATTR_AGENT_MISSING,
                message="agent_id is required and cannot be empty",
                field="agent_id",
            )
        )
    elif ctx.agent_id in FORBIDDEN_AGENT_IDS:
        errors.append(
            AttributionError(
                code=AttributionErrorCode.ATTR_AGENT_MISSING,
                message=f"agent_id cannot be '{ctx.agent_id}' - provide real agent identifier",
                field="agent_id",
            )
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Rule R2 + R3: actor_type REQUIRED and from closed set
    # ─────────────────────────────────────────────────────────────────────────
    if not ctx.actor_type or ctx.actor_type.strip() == "":
        errors.append(
            AttributionError(
                code=AttributionErrorCode.ATTR_ACTOR_TYPE_MISSING,
                message="actor_type is required (HUMAN | SYSTEM | SERVICE)",
                field="actor_type",
            )
        )
    elif ctx.actor_type.upper() not in VALID_ACTOR_TYPES:
        errors.append(
            AttributionError(
                code=AttributionErrorCode.ATTR_ACTOR_TYPE_INVALID,
                message=f"actor_type must be one of: {', '.join(sorted(VALID_ACTOR_TYPES))}",
                field="actor_type",
            )
        )

    # ─────────────────────────────────────────────────────────────────────────
    # origin_system_id REQUIRED
    # ─────────────────────────────────────────────────────────────────────────
    if not ctx.origin_system_id or ctx.origin_system_id.strip() == "":
        errors.append(
            AttributionError(
                code=AttributionErrorCode.ATTR_ORIGIN_SYSTEM_MISSING,
                message="origin_system_id is required for accountability",
                field="origin_system_id",
            )
        )
    elif ctx.origin_system_id in FORBIDDEN_ORIGIN_SYSTEM_IDS:
        errors.append(
            AttributionError(
                code=AttributionErrorCode.ATTR_ORIGIN_SYSTEM_MISSING,
                message=f"origin_system_id cannot be '{ctx.origin_system_id}' - provide real system identifier",
                field="origin_system_id",
            )
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Rule R4: actor_id REQUIRED iff actor_type == HUMAN
    # ─────────────────────────────────────────────────────────────────────────
    actor_type_upper = (ctx.actor_type or "").upper()

    if actor_type_upper == "HUMAN":
        if not ctx.actor_id or ctx.actor_id.strip() == "":
            errors.append(
                AttributionError(
                    code=AttributionErrorCode.ATTR_ACTOR_ID_REQUIRED,
                    message="actor_id is required when actor_type is HUMAN",
                    field="actor_id",
                )
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Rule R5: actor_id MUST be NULL if actor_type != HUMAN
    # ─────────────────────────────────────────────────────────────────────────
    if actor_type_upper in ("SYSTEM", "SERVICE"):
        if ctx.actor_id is not None and ctx.actor_id.strip() != "":
            errors.append(
                AttributionError(
                    code=AttributionErrorCode.ATTR_ACTOR_ID_FORBIDDEN,
                    message=f"actor_id must be null when actor_type is {actor_type_upper}",
                    field="actor_id",
                )
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Enforcement Decision
    # ─────────────────────────────────────────────────────────────────────────
    if errors:
        _log_violations(ctx, errors, mode)

        if mode == EnforcementMode.SHADOW:
            # Log only, do not reject
            return errors

        if mode == EnforcementMode.SOFT and override:
            # Log override usage for audit
            logger.warning(
                "attribution_override_used",
                extra={
                    "agent_id": ctx.agent_id,
                    "origin_system_id": ctx.origin_system_id,
                    "errors": [e.code.value for e in errors],
                },
            )
            return errors

        # Hard fail (or soft fail without override)
        raise errors[0]  # Raise first error

    return []


def _log_violations(
    ctx: AttributionContext,
    errors: List[AttributionError],
    mode: EnforcementMode,
) -> None:
    """Log attribution violations for monitoring."""
    logger.warning(
        "attribution_validation_failed",
        extra={
            "enforcement_mode": mode.value,
            "agent_id": ctx.agent_id,
            "actor_type": ctx.actor_type,
            "origin_system_id": ctx.origin_system_id,
            "has_actor_id": ctx.actor_id is not None,
            "error_codes": [e.code.value for e in errors],
            "error_count": len(errors),
        },
    )


# =============================================================================
# Helper Functions
# =============================================================================


def create_system_attribution(
    agent_id: str,
    origin_system_id: str,
) -> AttributionContext:
    """
    Create attribution context for SYSTEM-initiated runs.

    Use for: cron jobs, schedulers, policy triggers, automation.

    Args:
        agent_id: Executing agent identifier
        origin_system_id: Originating system identifier

    Returns:
        Validated attribution context
    """
    return AttributionContext(
        agent_id=agent_id,
        actor_type="SYSTEM",
        origin_system_id=origin_system_id,
        actor_id=None,
        origin_ts=datetime.now(timezone.utc),
    )


def create_human_attribution(
    agent_id: str,
    actor_id: str,
    origin_system_id: str,
) -> AttributionContext:
    """
    Create attribution context for HUMAN-initiated runs.

    Use for: user-triggered actions, console operations.

    Args:
        agent_id: Executing agent identifier
        actor_id: Human actor identity (required)
        origin_system_id: Originating system identifier

    Returns:
        Validated attribution context
    """
    return AttributionContext(
        agent_id=agent_id,
        actor_type="HUMAN",
        origin_system_id=origin_system_id,
        actor_id=actor_id,
        origin_ts=datetime.now(timezone.utc),
    )


def create_service_attribution(
    agent_id: str,
    origin_system_id: str,
) -> AttributionContext:
    """
    Create attribution context for SERVICE-initiated runs.

    Use for: service-to-service calls, internal APIs, workers.

    Args:
        agent_id: Executing agent identifier
        origin_system_id: Originating system identifier

    Returns:
        Validated attribution context
    """
    return AttributionContext(
        agent_id=agent_id,
        actor_type="SERVICE",
        origin_system_id=origin_system_id,
        actor_id=None,
        origin_ts=datetime.now(timezone.utc),
    )
