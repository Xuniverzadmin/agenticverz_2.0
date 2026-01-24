# Layer: L4 — Domain Services
# AUDIENCE: CUSTOMER
# Role: Analytics domain - Usage and cost intelligence
# Reference: DIRECTORY_REORGANIZATION_PLAN.md, HOC_analytics_analysis_v1.md

"""
Analytics Domain

Topics: usage, cost, trends
Roles: facades, engines, schemas

CONCEPTUAL SPLIT (Do not merge these concerns)
==============================================

INSIGHT LAYER (Customer Console owned):
  - analytics_facade.py — aggregations, statistics, trends
  - detection_facade.py — anomaly lifecycle, read models

TRUTH LAYER (System-wide, governance-adjacent):
  - cost_model_engine.py — system truth, all products depend
  - cost_anomaly_detector.py — system truth, incident escalation
  - cost_write_service.py — DB delegation

ADVISORY LAYER (Zero side-effects per PB-S5):
  - prediction.py — failure/cost predictions, advisory only

DORMANT (Quarantined):
  - pattern_detection.py — complete but unwired, PB-S3 safe

Future migrations may physically separate Truth from Insight.
Until then, this comment is the boundary marker.

GOVERNANCE CONTRACTS
====================

PB-S3: Observe patterns → create feedback → no mutation
PB-S5: Advise → observe → zero side-effects
COST-GOV: HIGH+ anomaly → incident creation enforced
"""
