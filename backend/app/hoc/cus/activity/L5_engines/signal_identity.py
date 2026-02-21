# capability_id: CAP-012
# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Location: hoc/cus/activity/L5_engines/signal_identity.py
# Temporal:
#   Trigger: api
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none (pure computation)
#   Writes: none
# Role: Signal identity computation for deduplication
# Callers: activity_facade.py, signal engines
# Allowed Imports: L5
# Forbidden Imports: L1, L2, L3, L6, sqlalchemy (runtime)
# Reference: PIN-470, PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md
"""Signal identity utilities for fingerprinting and deduplication."""

import hashlib
import json
from typing import Any


def compute_signal_fingerprint_from_row(row: dict[str, Any]) -> str:
    """
    Compute a stable fingerprint for a signal row.

    Used for:
    - Signal deduplication
    - Change detection
    - Idempotent signal creation

    Args:
        row: A dictionary containing signal data

    Returns:
        A hex digest fingerprint string
    """
    # Extract key fields for fingerprinting
    key_fields = {
        "signal_type": row.get("signal_type"),
        "dimension": row.get("dimension"),
        "source": row.get("source"),
        "tenant_id": row.get("tenant_id"),
    }

    # Sort keys for deterministic ordering
    canonical = json.dumps(key_fields, sort_keys=True, default=str)

    # Compute SHA-256 fingerprint
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]


def compute_signal_fingerprint(
    signal_type: str,
    dimension: str,
    source: str,
    tenant_id: str,
) -> str:
    """
    Compute a stable fingerprint for signal identity fields.

    Args:
        signal_type: Type of signal (e.g., "pattern", "anomaly")
        dimension: Dimension being measured
        source: Source of the signal
        tenant_id: Tenant identifier

    Returns:
        A hex digest fingerprint string
    """
    return compute_signal_fingerprint_from_row({
        "signal_type": signal_type,
        "dimension": dimension,
        "source": source,
        "tenant_id": tenant_id,
    })
