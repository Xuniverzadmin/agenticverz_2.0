# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Runtime safety switches for console deployment
# Callers: API routes, services, middleware
# Allowed Imports: None (foundational config)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: Console Deployment Plan

"""
Console Runtime Safety Switches

Three environment variables control console behavior:

CONSOLE_MODE:
    - DRAFT: Console is in draft/development mode
    - LIVE: Console is production-ready
    - MAINTENANCE: Console is in maintenance mode

DATA_MODE:
    - SYNTHETIC: Use synthetic/mock data
    - REAL: Use real production data

ACTION_MODE:
    - NOOP: All write/activate actions are logged but not executed
    - LIVE: All actions execute normally

Safety Matrix:
┌─────────────────┬──────────────┬──────────────┬───────────────┐
│ Configuration   │ CONSOLE_MODE │ DATA_MODE    │ ACTION_MODE   │
├─────────────────┼──────────────┼──────────────┼───────────────┤
│ Development     │ DRAFT        │ SYNTHETIC    │ NOOP          │
│ Staging         │ DRAFT        │ REAL         │ NOOP          │
│ Pre-Production  │ LIVE         │ REAL         │ NOOP          │
│ Production      │ LIVE         │ REAL         │ LIVE          │
└─────────────────┴──────────────┴──────────────┴───────────────┘

Usage:
    from app.config.console_modes import (
        get_console_mode,
        get_data_mode,
        get_action_mode,
        is_action_noop,
        should_execute_action,
    )

    # Check if actions should execute
    if should_execute_action():
        perform_mutation()
    else:
        log_noop_action("mutation", details)

    # Get current modes
    console_mode = get_console_mode()  # "DRAFT" | "LIVE" | "MAINTENANCE"
    data_mode = get_data_mode()        # "SYNTHETIC" | "REAL"
    action_mode = get_action_mode()    # "NOOP" | "LIVE"
"""

import logging
import os
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# =============================================================================
# MODE ENUMS
# =============================================================================


class ConsoleMode(str, Enum):
    """Console operational mode."""

    DRAFT = "DRAFT"  # Development/preview mode
    LIVE = "LIVE"  # Production mode
    MAINTENANCE = "MAINTENANCE"  # Maintenance mode (read-only)


class DataMode(str, Enum):
    """Data source mode."""

    SYNTHETIC = "SYNTHETIC"  # Use synthetic/mock data
    REAL = "REAL"  # Use real production data


class ActionMode(str, Enum):
    """Action execution mode."""

    NOOP = "NOOP"  # Log actions but don't execute
    LIVE = "LIVE"  # Execute actions normally


# =============================================================================
# MODE GETTERS
# =============================================================================


def get_console_mode() -> ConsoleMode:
    """
    Get the current console mode.

    Environment: CONSOLE_MODE
    Default: DRAFT (safe default)
    """
    mode = os.getenv("CONSOLE_MODE", "DRAFT").upper()
    try:
        return ConsoleMode(mode)
    except ValueError:
        logger.warning(f"Invalid CONSOLE_MODE '{mode}', defaulting to DRAFT")
        return ConsoleMode.DRAFT


def get_data_mode() -> DataMode:
    """
    Get the current data mode.

    Environment: DATA_MODE
    Default: SYNTHETIC (safe default)
    """
    mode = os.getenv("DATA_MODE", "SYNTHETIC").upper()
    try:
        return DataMode(mode)
    except ValueError:
        logger.warning(f"Invalid DATA_MODE '{mode}', defaulting to SYNTHETIC")
        return DataMode.SYNTHETIC


def get_action_mode() -> ActionMode:
    """
    Get the current action mode.

    Environment: ACTION_MODE
    Default: NOOP (safe default)
    """
    mode = os.getenv("ACTION_MODE", "NOOP").upper()
    try:
        return ActionMode(mode)
    except ValueError:
        logger.warning(f"Invalid ACTION_MODE '{mode}', defaulting to NOOP")
        return ActionMode.NOOP


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def is_draft_mode() -> bool:
    """Check if console is in draft mode."""
    return get_console_mode() == ConsoleMode.DRAFT


def is_live_mode() -> bool:
    """Check if console is in live mode."""
    return get_console_mode() == ConsoleMode.LIVE


def is_maintenance_mode() -> bool:
    """Check if console is in maintenance mode."""
    return get_console_mode() == ConsoleMode.MAINTENANCE


def is_synthetic_data() -> bool:
    """Check if using synthetic data."""
    return get_data_mode() == DataMode.SYNTHETIC


def is_real_data() -> bool:
    """Check if using real data."""
    return get_data_mode() == DataMode.REAL


def is_action_noop() -> bool:
    """Check if actions are in NOOP mode (logged but not executed)."""
    return get_action_mode() == ActionMode.NOOP


def is_action_live() -> bool:
    """Check if actions execute normally."""
    return get_action_mode() == ActionMode.LIVE


def should_execute_action() -> bool:
    """
    Determine if actions should be executed.

    Returns True only if:
    - ACTION_MODE is LIVE
    - CONSOLE_MODE is not MAINTENANCE

    This is the canonical check for mutation operations.
    """
    if is_maintenance_mode():
        return False
    return is_action_live()


# =============================================================================
# NOOP LOGGING
# =============================================================================

_noop_actions: list[dict] = []


def log_noop_action(
    action_type: str,
    resource_type: str,
    resource_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict:
    """
    Log a NOOP action for audit purposes.

    When ACTION_MODE=NOOP, this function records what WOULD have happened.
    Useful for testing, staging verification, and audit trails.

    Args:
        action_type: Type of action (WRITE, ACTIVATE, DELETE, etc.)
        resource_type: Type of resource (incident, policy, etc.)
        resource_id: ID of the resource (optional)
        details: Additional context (optional)

    Returns:
        The logged action record
    """
    from datetime import datetime, timezone

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action_type": action_type,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "details": details or {},
        "console_mode": get_console_mode().value,
        "data_mode": get_data_mode().value,
        "action_mode": "NOOP",
        "executed": False,
    }

    _noop_actions.append(record)

    logger.info(
        f"NOOP_ACTION: {action_type} on {resource_type}"
        f"{f'/{resource_id}' if resource_id else ''}"
        f" - action logged but not executed"
    )

    return record


def get_noop_actions() -> list[dict]:
    """Get all logged NOOP actions (for testing/debugging)."""
    return _noop_actions.copy()


def clear_noop_actions() -> None:
    """Clear the NOOP action log (for testing)."""
    _noop_actions.clear()


# =============================================================================
# STATUS SUMMARY
# =============================================================================


def get_console_status() -> dict[str, str]:
    """
    Get a summary of all console modes.

    Useful for health checks, status endpoints, and debugging.
    """
    return {
        "console_mode": get_console_mode().value,
        "data_mode": get_data_mode().value,
        "action_mode": get_action_mode().value,
        "actions_will_execute": should_execute_action(),
    }


def log_console_status() -> None:
    """Log the current console status on startup."""
    status = get_console_status()
    logger.info(
        f"Console Status: "
        f"CONSOLE_MODE={status['console_mode']}, "
        f"DATA_MODE={status['data_mode']}, "
        f"ACTION_MODE={status['action_mode']}, "
        f"actions_execute={status['actions_will_execute']}"
    )
