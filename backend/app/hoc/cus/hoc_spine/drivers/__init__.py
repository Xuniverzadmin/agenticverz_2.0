# capability_id: CAP-012
# Layer: L4 — HOC Spine (Drivers)
# AUDIENCE: INTERNAL
# Role: HOC Spine drivers package
# Reference: PIN-520 Wiring Audit
# artifact_class: CODE

"""
HOC Spine Drivers

L6-equivalent drivers that provide specific data access:
- Discovery Ledger: Signal recording for artifact tracking
"""

from app.hoc.cus.hoc_spine.drivers.ledger import (
    DiscoverySignal,
    emit_signal,
    get_signals,
)

__all__ = [
    "DiscoverySignal",
    "emit_signal",
    "get_signals",
]
