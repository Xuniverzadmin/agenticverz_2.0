# Layer: L3 — Boundary Adapters
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Runtime data projection for Aurora UI panels (DEPRECATED)
# Callers: Frontend via slot binding
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2
# Reference: PIN-411

"""
Runtime Projections Module

STATUS: DEPRECATED - All domains consolidated into unified facades

All runtime projection endpoints have been moved to unified domain facades:

| Domain       | Old Path                      | New Unified Facade              |
|--------------|-------------------------------|---------------------------------|
| Activity     | /api/v1/runtime/activity/*    | /activity/*                     |
| Incidents    | /api/v1/runtime/incidents/*   | /incidents/*                    |
| Overview     | /api/v1/runtime/overview/*    | /overview/*                     |
| Policies     | /api/v1/runtime/policies/*    | /policies/*                     |
| Logs         | /api/v1/runtime/logs/*        | /logs/*                         |

Additional unified facades:
- /integrations/* (SDK/worker integrations) → aos_cus_integrations.py
- /api-keys/* (API key management) → aos_api_key.py
- /accounts/* (projects, users, profile, billing)

This package is preserved for reference only.
The /api/v1/runtime/* prefix is no longer served.
The /api/v1/* prefix is legacy-only (410 Gone) and must not be treated as canonical.
"""

# DEPRECATED: No exports - all domains now have unified facades
# See:
#   app/hoc/api/cus/activity/activity.py    → /activity/*
#   app/hoc/api/cus/incidents/incidents.py  → /incidents/*
#   app/hoc/api/cus/overview/overview.py    → /overview/*
#   app/hoc/api/cus/policies/policies.py    → /policies/*
#   app/hoc/api/cus/policies/logs.py        → /logs/*
#   app/hoc/api/cus/policies/aos_cus_integrations.py  → /integrations/*
#   app/hoc/api/cus/policies/aos_api_key.py  → /api-keys/*
#   app/hoc/api/cus/policies/aos_accounts.py  → /accounts/*

__all__: list[str] = []
