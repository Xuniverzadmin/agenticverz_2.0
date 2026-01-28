# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: startup
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: none
# Role: Governance Profile configuration and validation
# Callers: main.py (L2), workers (L5)
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, PIN-454 (Cross-Domain Orchestration Audit), Section 2.1
# NOTE: Reclassified L6→L5 (2026-01-24) - no Session imports, pure config logic

"""
Governance Profile Configuration

Reduces cognitive load and configuration drift by providing three
well-defined governance profiles:

- STRICT: Full enforcement, all features enabled, production-ready
- STANDARD: Core features enabled, some optional features disabled
- OBSERVE_ONLY: Audit and observe without enforcement (safe rollout)

Usage:
    from app.hoc.cus.general.L5_engines.profile_policy_mode import (
        get_governance_profile,
        validate_governance_config,
        GovernanceProfile,
    )

    # At startup
    profile = get_governance_profile()
    validate_governance_config()  # Raises if invalid combination

    # Check profile
    if profile == GovernanceProfile.STRICT:
        # Full enforcement mode
        ...

Environment Variables:
    GOVERNANCE_PROFILE: STRICT | STANDARD | OBSERVE_ONLY (default: STANDARD)

    Individual flags (override profile defaults):
    - ROK_ENABLED
    - RAC_ENABLED
    - TRANSACTION_COORDINATOR_ENABLED
    - EVENT_REACTOR_ENABLED
    - MID_EXECUTION_POLICY_CHECK_ENABLED
    - RAC_DURABILITY_ENFORCE (STRICT only)
    - PHASE_STATUS_INVARIANT_ENFORCE (STRICT only)
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict, FrozenSet, List, Optional, Tuple

logger = logging.getLogger("nova.services.governance.profile")


class GovernanceProfile(str, Enum):
    """
    Pre-defined governance profiles.

    Each profile represents a coherent set of feature flag settings
    designed for specific deployment scenarios.
    """

    STRICT = "STRICT"
    """
    Full enforcement mode. All features enabled.
    Use for: Production, high-stakes environments.

    - All audit features enabled
    - All enforcement enabled
    - Durability checks enforced
    - Phase-status invariants enforced
    """

    STANDARD = "STANDARD"
    """
    Balanced mode. Core features enabled, optional features configurable.
    Use for: Staging, development with governance.

    - Core audit features enabled (ROK, RAC)
    - Transaction coordination enabled
    - Event reactor enabled
    - Mid-execution checks optional
    """

    OBSERVE_ONLY = "OBSERVE_ONLY"
    """
    Observation mode. Audit without enforcement.
    Use for: Safe rollout, debugging, learning the system.

    - Audit logging enabled
    - No enforcement (violations logged, not blocked)
    - Good for understanding behavior before enabling enforcement
    """


@dataclass(frozen=True)
class GovernanceConfig:
    """
    Complete governance configuration derived from profile + overrides.
    """

    profile: GovernanceProfile

    # Core orchestration
    rok_enabled: bool
    rac_enabled: bool
    transaction_coordinator_enabled: bool

    # Event system
    event_reactor_enabled: bool
    mid_execution_policy_check_enabled: bool

    # Enforcement levels (STRICT only by default)
    rac_durability_enforce: bool
    phase_status_invariant_enforce: bool

    # Audit trail
    rac_rollback_audit_enabled: bool

    # Alert controls
    alert_fatigue_enabled: bool

    def to_dict(self) -> Dict[str, object]:
        """Serialize for logging."""
        return {
            "profile": self.profile.value,
            "rok_enabled": self.rok_enabled,
            "rac_enabled": self.rac_enabled,
            "transaction_coordinator_enabled": self.transaction_coordinator_enabled,
            "event_reactor_enabled": self.event_reactor_enabled,
            "mid_execution_policy_check_enabled": self.mid_execution_policy_check_enabled,
            "rac_durability_enforce": self.rac_durability_enforce,
            "phase_status_invariant_enforce": self.phase_status_invariant_enforce,
            "rac_rollback_audit_enabled": self.rac_rollback_audit_enabled,
            "alert_fatigue_enabled": self.alert_fatigue_enabled,
        }


# =============================================================================
# Profile Definitions
# =============================================================================

# Default settings for each profile
PROFILE_DEFAULTS: Dict[GovernanceProfile, Dict[str, bool]] = {
    GovernanceProfile.STRICT: {
        "rok_enabled": True,
        "rac_enabled": True,
        "transaction_coordinator_enabled": True,
        "event_reactor_enabled": True,
        "mid_execution_policy_check_enabled": True,
        "rac_durability_enforce": True,
        "phase_status_invariant_enforce": True,
        "rac_rollback_audit_enabled": True,
        "alert_fatigue_enabled": True,
    },
    GovernanceProfile.STANDARD: {
        "rok_enabled": True,
        "rac_enabled": True,
        "transaction_coordinator_enabled": True,
        "event_reactor_enabled": True,
        "mid_execution_policy_check_enabled": False,  # Optional
        "rac_durability_enforce": False,  # Warning only
        "phase_status_invariant_enforce": False,  # Warning only
        "rac_rollback_audit_enabled": True,
        "alert_fatigue_enabled": True,
    },
    GovernanceProfile.OBSERVE_ONLY: {
        "rok_enabled": True,  # Orchestration still runs
        "rac_enabled": True,  # Audit still records
        "transaction_coordinator_enabled": False,  # No enforcement
        "event_reactor_enabled": True,  # Events still flow
        "mid_execution_policy_check_enabled": False,  # No mid-run checks
        "rac_durability_enforce": False,  # No enforcement
        "phase_status_invariant_enforce": False,  # No enforcement
        "rac_rollback_audit_enabled": True,  # Still audit rollbacks
        "alert_fatigue_enabled": False,  # All alerts pass through
    },
}


# =============================================================================
# Validation Rules
# =============================================================================

# Invalid flag combinations (frozenset of flags that cannot all be true)
INVALID_COMBINATIONS: List[Tuple[FrozenSet[str], str]] = [
    # RAC durability enforcement requires RAC to be enabled
    (
        frozenset({"rac_durability_enforce", "!rac_enabled"}),
        "RAC durability enforcement requires RAC to be enabled",
    ),
    # Phase-status invariants require ROK
    (
        frozenset({"phase_status_invariant_enforce", "!rok_enabled"}),
        "Phase-status invariant enforcement requires ROK to be enabled",
    ),
    # Transaction coordinator requires ROK
    (
        frozenset({"transaction_coordinator_enabled", "!rok_enabled"}),
        "Transaction coordinator requires ROK to be enabled",
    ),
    # Mid-execution policy check requires event reactor
    (
        frozenset({"mid_execution_policy_check_enabled", "!event_reactor_enabled"}),
        "Mid-execution policy check requires EventReactor to be enabled",
    ),
]

# Required combinations (if A is true, B must also be true)
REQUIRED_COMBINATIONS: List[Tuple[str, str, str]] = [
    # If transaction coordinator is enabled, RAC should be enabled for audit
    (
        "transaction_coordinator_enabled",
        "rac_enabled",
        "Transaction coordinator should have RAC enabled for rollback audit",
    ),
]


class GovernanceConfigError(Exception):
    """Raised when governance configuration is invalid."""

    def __init__(self, message: str, violations: List[str]):
        self.violations = violations
        super().__init__(f"{message}: {'; '.join(violations)}")


# =============================================================================
# Configuration Loading
# =============================================================================


def _get_bool_env(name: str, default: bool) -> bool:
    """Get boolean from environment variable."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "on")


def get_governance_profile() -> GovernanceProfile:
    """
    Get the current governance profile from environment.

    Returns:
        GovernanceProfile enum value
    """
    profile_str = os.getenv("GOVERNANCE_PROFILE", "STANDARD").upper()
    try:
        return GovernanceProfile(profile_str)
    except ValueError:
        logger.warning(
            "governance_profile.invalid",
            extra={
                "provided": profile_str,
                "valid_options": [p.value for p in GovernanceProfile],
                "defaulting_to": "STANDARD",
            },
        )
        return GovernanceProfile.STANDARD


def load_governance_config() -> GovernanceConfig:
    """
    Load complete governance configuration.

    Loads profile defaults, then applies any environment variable overrides.

    Returns:
        GovernanceConfig with all settings
    """
    profile = get_governance_profile()
    defaults = PROFILE_DEFAULTS[profile]

    # Load with profile defaults, allowing env overrides
    config = GovernanceConfig(
        profile=profile,
        rok_enabled=_get_bool_env("ROK_ENABLED", defaults["rok_enabled"]),
        rac_enabled=_get_bool_env("RAC_ENABLED", defaults["rac_enabled"]),
        transaction_coordinator_enabled=_get_bool_env(
            "TRANSACTION_COORDINATOR_ENABLED",
            defaults["transaction_coordinator_enabled"],
        ),
        event_reactor_enabled=_get_bool_env(
            "EVENT_REACTOR_ENABLED", defaults["event_reactor_enabled"]
        ),
        mid_execution_policy_check_enabled=_get_bool_env(
            "MID_EXECUTION_POLICY_CHECK_ENABLED",
            defaults["mid_execution_policy_check_enabled"],
        ),
        rac_durability_enforce=_get_bool_env(
            "RAC_DURABILITY_ENFORCE", defaults["rac_durability_enforce"]
        ),
        phase_status_invariant_enforce=_get_bool_env(
            "PHASE_STATUS_INVARIANT_ENFORCE", defaults["phase_status_invariant_enforce"]
        ),
        rac_rollback_audit_enabled=_get_bool_env(
            "RAC_ROLLBACK_AUDIT_ENABLED", defaults["rac_rollback_audit_enabled"]
        ),
        alert_fatigue_enabled=_get_bool_env(
            "ALERT_FATIGUE_ENABLED", defaults["alert_fatigue_enabled"]
        ),
    )

    logger.info(
        "governance_profile.loaded",
        extra=config.to_dict(),
    )

    return config


def validate_governance_config(config: Optional[GovernanceConfig] = None) -> List[str]:
    """
    Validate governance configuration for invalid combinations.

    Args:
        config: Configuration to validate (loads from env if not provided)

    Returns:
        List of warning messages (empty if valid)

    Raises:
        GovernanceConfigError: If configuration has blocking violations
    """
    if config is None:
        config = load_governance_config()

    warnings: List[str] = []
    errors: List[str] = []

    # Build flag state map
    flags = {
        "rok_enabled": config.rok_enabled,
        "rac_enabled": config.rac_enabled,
        "transaction_coordinator_enabled": config.transaction_coordinator_enabled,
        "event_reactor_enabled": config.event_reactor_enabled,
        "mid_execution_policy_check_enabled": config.mid_execution_policy_check_enabled,
        "rac_durability_enforce": config.rac_durability_enforce,
        "phase_status_invariant_enforce": config.phase_status_invariant_enforce,
        "rac_rollback_audit_enabled": config.rac_rollback_audit_enabled,
        "alert_fatigue_enabled": config.alert_fatigue_enabled,
        # Negated flags for validation rules
        "!rok_enabled": not config.rok_enabled,
        "!rac_enabled": not config.rac_enabled,
        "!event_reactor_enabled": not config.event_reactor_enabled,
    }

    # Check invalid combinations
    for invalid_set, message in INVALID_COMBINATIONS:
        if all(flags.get(flag, False) for flag in invalid_set):
            errors.append(message)

    # Check required combinations (warnings)
    for flag_a, flag_b, message in REQUIRED_COMBINATIONS:
        if flags.get(flag_a, False) and not flags.get(flag_b, False):
            warnings.append(message)

    # Log findings
    if warnings:
        logger.warning(
            "governance_config.warnings",
            extra={
                "profile": config.profile.value,
                "warnings": warnings,
            },
        )

    if errors:
        logger.error(
            "governance_config.invalid",
            extra={
                "profile": config.profile.value,
                "errors": errors,
            },
        )
        raise GovernanceConfigError("Invalid governance configuration", errors)

    logger.info(
        "governance_config.validated",
        extra={
            "profile": config.profile.value,
            "warnings_count": len(warnings),
            "status": "VALID",
        },
    )

    return warnings


# =============================================================================
# Singleton
# =============================================================================

_governance_config: Optional[GovernanceConfig] = None


def get_governance_config() -> GovernanceConfig:
    """
    Get the validated governance configuration singleton.

    Loads and validates on first call, caches thereafter.

    Returns:
        Validated GovernanceConfig
    """
    global _governance_config
    if _governance_config is None:
        _governance_config = load_governance_config()
        validate_governance_config(_governance_config)
    return _governance_config


def reset_governance_config() -> None:
    """Reset the singleton (for testing)."""
    global _governance_config
    _governance_config = None


# =============================================================================
# Startup Hook
# =============================================================================


def validate_governance_at_startup() -> None:
    """
    Validate governance configuration at application startup.

    Call this from main.py during FastAPI lifespan startup.

    Raises:
        GovernanceConfigError: If configuration is invalid
    """
    config = get_governance_config()

    logger.info(
        "governance_profile.startup_validated",
        extra={
            "profile": config.profile.value,
            "rok_enabled": config.rok_enabled,
            "rac_enabled": config.rac_enabled,
            "transaction_coordinator_enabled": config.transaction_coordinator_enabled,
            "event_reactor_enabled": config.event_reactor_enabled,
            "mid_execution_policy_check_enabled": config.mid_execution_policy_check_enabled,
        },
    )
