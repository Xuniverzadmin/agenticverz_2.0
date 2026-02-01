# Layer: L5 — Domain Schema
# AUDIENCE: CUSTOMER
# Role: Protocol and DTOs for cost anomaly detection
# Reference: PIN-511 Phase 1.2
# artifact_class: CODE

"""
Cost Anomaly Schemas (PIN-511 Phase 1.2)

Defines the CostAnomalyReadProtocol that L5 engines depend on.
L6 drivers implement this Protocol — engine never knows about Session.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Protocol, runtime_checkable

if TYPE_CHECKING:
    from app.db import CostAnomaly, CostBudget


@runtime_checkable
class CostAnomalyReadProtocol(Protocol):
    """Protocol for cost anomaly read/persist operations.

    Implemented by: CostAnomalyReadDriver (L6)
    Consumed by: CostAnomalyDetector (L5 engine)
    """

    def fetch_active_budgets(self, tenant_id: str) -> list:
        """Fetch all active budgets for a tenant."""
        ...

    def find_existing_anomaly(
        self,
        tenant_id: str,
        anomaly_type: str,
        entity_type: str,
        entity_id: Optional[str],
        since: datetime,
    ) -> Optional[CostAnomaly]:
        """Find existing unresolved anomaly for deduplication."""
        ...

    def persist_anomaly(self, anomaly: CostAnomaly) -> None:
        """Add or update an anomaly record."""
        ...

    def flush_and_refresh(self, anomalies: List[CostAnomaly]) -> None:
        """Flush to get generated IDs and refresh."""
        ...
