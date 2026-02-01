# Layer: L4 — HOC Spine (Schema)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Consumers: analytics, incidents
# Role: Cross-domain anomaly fact types — pure data, no behavior
# Reference: PIN-510 Phase 1C (G4 mitigation — schema admission compliant)
# artifact_class: CODE
#
# SCHEMA ADMISSION:
#   1. >=2 domain consumers: analytics (emitter), incidents (ingester)
#   2. Facts/types only: dataclass with no methods beyond __init__
#   3. Append-only evolution: existing fields never removed
#   4. Consumers declared in header

"""
Anomaly Types (Spine Schemas)

Cross-domain fact types for anomaly detection → incident creation flow.

Analytics emits CostAnomalyFact; incidents bridge ingests it.
This type lives in hoc_spine because it crosses domain boundaries.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class CostAnomalyFact:
    """
    Pure fact emitted by analytics when a cost anomaly is detected.

    This dataclass contains NO database references, NO session objects,
    and NO imports from analytics. It is a pure data transfer object.

    Analytics engines emit this; the incidents bridge decides what to do with it.

    Moved from incidents/L5_engines/anomaly_bridge.py to hoc_spine/schemas/
    per PIN-510 Phase 1C (schema admission: >=2 consumers, facts only, append-only).
    """

    tenant_id: str
    anomaly_id: str
    anomaly_type: str  # BUDGET_EXCEEDED, ABSOLUTE_SPIKE, SUSTAINED_DRIFT, etc.
    severity: str  # LOW, MEDIUM, HIGH
    current_value_cents: int
    expected_value_cents: int
    entity_type: Optional[str] = None  # user, feature, tenant
    entity_id: Optional[str] = None
    deviation_pct: float = 0.0
    confidence: float = 1.0
    observed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = field(default_factory=dict)


__all__ = ["CostAnomalyFact"]
