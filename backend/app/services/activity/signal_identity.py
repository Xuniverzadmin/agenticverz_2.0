# Layer: L4 — Domain Engine
# Product: ai-console
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Canonical signal fingerprint computation (SIGNAL-ID-001)
# Callers: signal_feedback_service.py, activity.py (L2)
# Allowed Imports: standard library only
# Forbidden Imports: L1, L2, L3, L5, L6
# Reference: Attention Feedback Loop Implementation Plan

"""
Signal Identity Module

Computes canonical signal fingerprints from projection rows.

INVARIANT (SIGNAL-ID-001):
- Signal identity MUST be derived from backend-computed projection
- NEVER derive from client-supplied payload
- Format: sig-{hash[:16]}

This module uses only standard library imports to maintain purity.
"""

import hashlib
from typing import Any


def compute_signal_fingerprint_from_row(row: dict[str, Any]) -> str:
    """
    Compute canonical signal fingerprint from projection row.

    INVARIANT (SIGNAL-ID-001):
    - MUST be called with backend-computed projection row
    - NEVER derive from client-supplied payload
    - Format: sig-{hash[:16]}

    The fingerprint is deterministic and based on:
    - run_id: The run that generated the signal
    - signal_type: Type of signal (COST_RISK, TIME_RISK, etc.)
    - risk_type: Risk category (COST, TIME, TOKENS, RATE)
    - evaluation_outcome: Policy evaluation result (BREACH, NEAR_THRESHOLD, etc.)

    Args:
        row: Projection row from v_runs_o2 or signals query containing:
            - run_id (str): Run identifier
            - signal_type (str): Signal type classification
            - risk_type (str): Risk type classification
            - evaluation_outcome (str): Policy evaluation outcome

    Returns:
        Canonical fingerprint in format: sig-{hash[:16]}

    Example:
        >>> row = {
        ...     "run_id": "run-abc123",
        ...     "signal_type": "COST_RISK",
        ...     "risk_type": "COST",
        ...     "evaluation_outcome": "BREACH"
        ... }
        >>> fingerprint = compute_signal_fingerprint_from_row(row)
        >>> fingerprint.startswith("sig-")
        True
        >>> len(fingerprint) == 20  # "sig-" + 16 hex chars
        True
    """
    # Extract required fields with safe defaults
    run_id = row.get("run_id", "")
    signal_type = row.get("signal_type", "UNKNOWN")
    risk_type = row.get("risk_type", "UNKNOWN")
    evaluation_outcome = row.get("evaluation_outcome", "UNKNOWN")

    # Build deterministic raw string
    raw = f"{run_id}:{signal_type}:{risk_type}:{evaluation_outcome}"

    # Compute SHA256 hash and truncate
    hash_hex = hashlib.sha256(raw.encode("utf-8")).hexdigest()

    return f"sig-{hash_hex[:16]}"


def validate_signal_fingerprint(fingerprint: str) -> bool:
    """
    Validate that a fingerprint matches the expected format.

    Args:
        fingerprint: String to validate

    Returns:
        True if fingerprint matches format sig-{16 hex chars}
    """
    if not fingerprint or not isinstance(fingerprint, str):
        return False

    if not fingerprint.startswith("sig-"):
        return False

    hash_part = fingerprint[4:]
    if len(hash_part) != 16:
        return False

    try:
        int(hash_part, 16)
        return True
    except ValueError:
        return False


__all__ = [
    "compute_signal_fingerprint_from_row",
    "validate_signal_fingerprint",
]
