# capability_id: CAP-002
# Layer: L5 — Domain Schema
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: import
#   Execution: sync
# Role: Persistence DTOs for cost anomaly detector — replaces CostAnomaly ORM in L5
# Callers: cost_anomaly_detector_engine.py (L5), cost_anomaly_read_driver.py (L6)
# Allowed Imports: stdlib
# Forbidden Imports: sqlalchemy, sqlmodel, app.models, app.db
# Reference: PIN-520 No-Exemptions Phase 2
# artifact_class: CODE

"""
Cost Anomaly Persistence DTOs

Replaces direct CostAnomaly ORM usage in the L5 engine.
L6 driver constructs/updates ORM objects and returns these DTOs.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class PersistedAnomaly:
    """DTO returned by L6 after persisting a CostAnomaly ORM row.

    Contains only the fields the L5 engine needs to read back.
    """

    id: str
    tenant_id: str
    anomaly_type: str
    severity: str
    entity_type: str
    entity_id: Optional[str]
    current_value_cents: float
    expected_value_cents: float
    deviation_pct: float
    message: str
    breach_count: int
    derived_cause: str
    metadata_json: Dict[str, Any] = field(default_factory=dict)
