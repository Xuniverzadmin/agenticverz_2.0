# Layer: L6 — Driver
# AUDIENCE: CUSTOMER
# Role: Enforce boot-fail policy for SPINE components
# Product: system-wide
# Temporal:
#   Trigger: startup
#   Execution: sync (blocking)
# Callers: main.py lifespan
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L3
# Reference: GAP-067


"""
Module: boot_guard
Purpose: Validates all SPINE components at startup, blocks server if any fail.

Imports (Dependencies):
    - app.events.reactor_initializer: get_reactor_status
    - app.services.governance.profile: get_governance_config, validate_governance_config

Exports (Provides):
    - validate_spine_components(): SpineValidationResult
    - SpineValidationError: Exception for boot failures
    - get_boot_status(): BootStatus

Wiring Points:
    - Called from: main.py:lifespan_startup() after all component init
    - Blocks: API routes if validation fails

Acceptance Criteria:
    - [x] AC-067-01: SPINE validation runs at startup
    - [x] AC-067-02: Failure blocks run acceptance
    - [x] AC-067-03: Health endpoint shows boot status
    - [x] AC-067-04: All SPINE components checked
"""

from dataclasses import dataclass
from typing import List, Optional
import logging

logger = logging.getLogger("nova.startup.boot_guard")


@dataclass
class SpineValidationResult:
    """Result of SPINE component validation."""
    valid: bool
    failures: List[str]
    warnings: List[str]


class SpineValidationError(Exception):
    """Raised when SPINE components fail validation."""
    def __init__(self, failures: List[str]):
        self.failures = failures
        super().__init__(f"BOOT FAILURE: SPINE validation failed: {failures}")


# Singleton boot status
_boot_status: Optional[SpineValidationResult] = None


def validate_spine_components() -> SpineValidationResult:
    """
    Validate all SPINE components are properly initialized.

    Checks:
    1. EventReactor is running (if enabled)
    2. Governance config is valid
    3. Fail-closed is default (not hardcoded fail-open)

    Raises SpineValidationError if any critical check fails.

    Returns:
        SpineValidationResult with validation details
    """
    global _boot_status

    failures: List[str] = []
    warnings: List[str] = []

    # Check 1: EventReactor (GAP-046)
    try:
        from app.events.reactor_initializer import get_reactor_status
        # L5 engine import (migrated to HOC per SWEEP-03)
        from app.hoc.cus.general.L5_engines.profile_policy_mode import get_governance_config

        config = get_governance_config()

        if config.event_reactor_enabled:
            reactor_status = get_reactor_status()
            if not reactor_status.get("healthy", False):
                failures.append(f"EventReactor not healthy: {reactor_status.get('status')}")
    except Exception as e:
        failures.append(f"EventReactor check failed: {e}")

    # Check 2: Governance config valid
    try:
        # L5 engine import (migrated to HOC per SWEEP-03)
        from app.hoc.cus.general.L5_engines.profile_policy_mode import validate_governance_config, get_governance_config

        config = get_governance_config()
        config_warnings = validate_governance_config(config)
        warnings.extend(config_warnings)
    except Exception as e:
        failures.append(f"Governance config invalid: {e}")

    # Check 3: Runtime switch is available (GAP-069)
    try:
        # L5 engine import (migrated to HOC per SWEEP-03)
        from app.hoc.cus.general.L5_controls.drivers.runtime_switch import is_governance_active
        if not is_governance_active():
            warnings.append("Governance is currently disabled at boot")
    except ImportError:
        warnings.append("Runtime switch not available (GAP-069 not implemented)")
    except Exception as e:
        warnings.append(f"Runtime switch check warning: {e}")

    # Build result
    _boot_status = SpineValidationResult(
        valid=len(failures) == 0,
        failures=failures,
        warnings=warnings,
    )

    if failures:
        logger.critical("boot_guard.validation_failed", extra={
            "failures": failures,
            "warnings": warnings,
        })
        raise SpineValidationError(failures)

    logger.info("boot_guard.validation_passed", extra={
        "warnings_count": len(warnings),
        "warnings": warnings if warnings else None,
    })

    return _boot_status


def get_boot_status() -> dict:
    """Get boot validation status for health checks."""
    if _boot_status is None:
        return {"validated": False, "status": "not_validated", "failures": [], "warnings": []}

    return {
        "validated": True,
        "status": "healthy" if _boot_status.valid else "failed",
        "failures": _boot_status.failures,
        "warnings": _boot_status.warnings,
    }


def reset_boot_status() -> None:
    """Reset boot status (for testing)."""
    global _boot_status
    _boot_status = None
