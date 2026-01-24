# ============================================================
# DUPLICATE — QUARANTINED (ANALYTICS DOMAIN)
#
# This enum is a historical duplicate and MUST NOT be used.
#
# Canonical Definition:
#   houseofcards/customer/analytics/engines/cost_anomaly_detector.py
#   Enum: AnomalySeverity (lines 60-65)
#
# Duplicate Origin:
#   houseofcards/customer/analytics/facades/detection_facade.py
#   (lines 67-71, now removed)
#
# Audit Reference:
#   ANA-DUP-001
#
# Status:
#   FROZEN — retained for traceability only
#
# Removal:
#   Eligible after Phase DTO authority unification
# ============================================================

from enum import Enum


class AnomalySeverity(str, Enum):
    """
    QUARANTINED — Use AnomalySeverity from cost_anomaly_detector.py instead.

    Anomaly severity levels.

    This is the FROZEN facade version. The canonical version lives in:
    houseofcards/customer/analytics/engines/cost_anomaly_detector.py

    Members (100% overlap with canonical):
        - LOW = "LOW"      # +15% to +25%
        - MEDIUM = "MEDIUM"  # +25% to +40%
        - HIGH = "HIGH"    # >40%
    """

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
