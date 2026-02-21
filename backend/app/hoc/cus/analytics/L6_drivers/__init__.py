# capability_id: CAP-002
# Layer: L6 — Domain Drivers
# AUDIENCE: CUSTOMER
# Role: Analytics domain data access drivers
# Reference: PIN-470, Phase-2.5A Analytics Extraction

"""
Analytics Drivers (L6)

Data access drivers for the analytics domain.
All business logic stays in L4 engines.

Drivers:
- CostAnomalyDriver: Cost anomaly detection DB operations
- AlertDriver: Alert queue DB operations
- PredictionDriver: Prediction event DB operations
"""

from app.hoc.cus.analytics.L6_drivers.cost_anomaly_driver import (
    CostAnomalyDriver,
    get_cost_anomaly_driver,
)
from app.hoc.cus.analytics.L6_drivers.prediction_driver import (
    PredictionDriver,
    get_prediction_driver,
)
from app.hoc.cus.analytics.L6_drivers.canary_report_driver import (
    write_canary_report,
    query_canary_reports,
    get_canary_report_by_run_id,
)

__all__ = [
    "CostAnomalyDriver",
    "get_cost_anomaly_driver",
    "PredictionDriver",
    "get_prediction_driver",
    # Canary Report Driver (PIN-518)
    "write_canary_report",
    "query_canary_reports",
    "get_canary_report_by_run_id",
]
