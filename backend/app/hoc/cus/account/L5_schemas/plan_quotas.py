# Layer: L5 — Domain Schema
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: L5-safe plan quota constants for tenant engine
# Callers: tenant_engine.py (L5)
# Allowed Imports: stdlib only
# Forbidden Imports: L1, L2, L3, L7 (app.models)
# Reference: PIN-520 Phase 3 (L5 purity — no runtime app.models imports)
# artifact_class: CODE

"""
Plan quota constants mirror.

Mirrors PLAN_QUOTAS from app.models.tenant so that L5 engines
never need a runtime import of app.models for business-logic constants.
Values MUST stay in sync with the L7 original.

Canonical source: app/models/tenant.py
"""

PLAN_QUOTAS = {
    "free": {
        "max_workers": 3,
        "max_runs_per_day": 100,
        "max_concurrent_runs": 5,
        "max_tokens_per_month": 1_000_000,
        "max_api_keys": 5,
    },
    "pro": {
        "max_workers": 10,
        "max_runs_per_day": 1000,
        "max_concurrent_runs": 20,
        "max_tokens_per_month": 10_000_000,
        "max_api_keys": 20,
    },
    "enterprise": {
        "max_workers": 100,
        "max_runs_per_day": 100000,
        "max_concurrent_runs": 100,
        "max_tokens_per_month": 1_000_000_000,
        "max_api_keys": 100,
    },
}
