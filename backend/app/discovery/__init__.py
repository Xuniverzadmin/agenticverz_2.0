# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Discovery system package marker
# Callers: Discovery imports
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: Package Structure

"""
Discovery Ledger - Phase C observational signal log.

Passive, append-only system that records interesting signals.
Does NOT enforce visibility. Does NOT require approval.

Usage:
    from app.discovery import emit_signal

    emit_signal(
        artifact="prediction_events",
        signal_type="high_operator_access",
        evidence={"count_7d": 21, "route": "/api/v1/predictions"},
        confidence=0.8,
        detected_by="api_access_monitor"
    )

Reference: docs/contracts/visibility_lifecycle.yaml
"""

from app.discovery.ledger import DiscoverySignal, emit_signal

__all__ = ["emit_signal", "DiscoverySignal"]
