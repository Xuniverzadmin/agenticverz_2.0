# Layer: L6 — Drivers
# AUDIENCE: CUSTOMER
# Role: Analytics domain data access drivers
# Reference: Phase-2.5A Analytics Extraction

"""
Analytics Drivers (L6)

Data access drivers for the analytics domain.
All business logic stays in L4 engines.

Drivers:
- CostAnomalyDriver: Cost anomaly detection DB operations
- AlertDriver: Alert queue DB operations
- PredictionDriver: Prediction event DB operations
"""

from app.hoc.cus.analytics.drivers.alert_driver import (
    AlertDriver,
    get_alert_driver,
)
from app.hoc.cus.analytics.drivers.cost_anomaly_driver import (
    CostAnomalyDriver,
    get_cost_anomaly_driver,
)
from app.hoc.cus.analytics.drivers.prediction_driver import (
    PredictionDriver,
    get_prediction_driver,
)

__all__ = [
    "AlertDriver",
    "get_alert_driver",
    "CostAnomalyDriver",
    "get_cost_anomaly_driver",
    "PredictionDriver",
    "get_prediction_driver",
]
