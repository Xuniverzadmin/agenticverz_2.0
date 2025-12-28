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
