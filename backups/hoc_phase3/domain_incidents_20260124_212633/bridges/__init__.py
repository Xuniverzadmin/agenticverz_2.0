# Layer: L4 — Domain Bridge
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: Bridge module for cross-domain fact ingestion
# Reference: R1 Resolution (Analytics → Incidents authority boundary)

"""
Incidents Domain Bridges

Domain-owned ingestion points for facts from other domains.
Bridges apply incident creation rules - they are NOT general services.

Available bridges:
- AnomalyIncidentBridge: Accepts CostAnomalyFact from analytics
"""

from app.hoc.cus.incidents.bridges.anomaly_bridge import (
    AnomalyIncidentBridge,
    CostAnomalyFact,
)

__all__ = [
    "AnomalyIncidentBridge",
    "CostAnomalyFact",
]
