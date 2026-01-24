# Layer: L8 — Catalyst / Meta
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: none (QUARANTINE)
#   Execution: none
# Role: QUARANTINE - Files pending domain reassignment or archival
# Callers: None
# Allowed Imports: none (QUARANTINE)
# Forbidden Imports: all (QUARANTINE)
# Reference: LOGS_PHASE2.5_IMPLEMENTATION_PLAN.md
#
# STATUS: QUARANTINE
# REASON: Files in this directory violate domain boundaries or are duplicates.
#
# QUARANTINED FILES:
#
# FROM logs/engines/ (Decision Logic - Wrong Domain):
# - cost_anomaly_detector.py: Decides "Was this anomalous?" → belongs in analytics
# - pattern_detection.py: Decides "Is this a pattern?" → belongs in analytics
#
# FROM logs/engines/ (Deprecated/Misplaced L2 Routes):
# - api.py: L2 API routes misplaced in engines/ (C2 Predictions - DEPRECATED)
# - M17_internal_worker.py: L2 API routes misplaced in engines/ (DEPRECATED - not served)
#
# RESTORED FILES (no longer quarantined):
# - logs_facade.py: RESTORED to logs/facades/logs_facade.py (split into L4 facade + L6 driver)
# - export_bundle_service.py: RESTORED to logs/adapters/export_bundle_adapter.py (split into L3 adapter + L6 driver)
#
# ACTION:
# - Decision logic files: Reassign to analytics/activity domains
# - Deprecated files: Archive

"""
Quarantine Directory

Files in this directory have been removed from their original domains
because they violate domain boundaries, are deprecated, or are orphans
(duplicates of files in app/services/ that are the active versions).

They are preserved here for reference until properly reassigned or archived.
"""
