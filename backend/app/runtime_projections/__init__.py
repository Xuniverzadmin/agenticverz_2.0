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
| Activity     | /api/v1/runtime/activity/*    | /api/v1/activity/*              |
| Incidents    | /api/v1/runtime/incidents/*   | /api/v1/incidents/*             |
| Overview     | /api/v1/runtime/overview/*    | /api/v1/overview/*              |
| Policies     | /api/v1/runtime/policies/*    | /api/v1/policies/*              |
| Logs         | /api/v1/runtime/logs/*        | /api/v1/logs/*                  |

Additional unified facades:
- /api/v1/integrations/* (SDK/worker integrations) → aos_cus_integrations.py
- /api/v1/api-keys/* (API key management) → aos_api_key.py
- /api/v1/accounts/* (projects, users, profile, billing)

This package is preserved for reference only.
The /api/v1/runtime/* prefix is no longer served.
"""

# DEPRECATED: No exports - all domains now have unified facades
# See:
#   app/api/activity.py      → /api/v1/activity/*
#   app/api/incidents.py     → /api/v1/incidents/*
#   app/api/overview.py      → /api/v1/overview/*
#   app/api/policies.py      → /api/v1/policies/*
#   app/api/logs.py          → /api/v1/logs/*
#   app/api/aos_cus_integrations.py  → /api/v1/integrations/*
#   app/api/aos_api_key.py  → /api/v1/api-keys/*
#   app/api/aos_accounts.py  → /api/v1/accounts/*

__all__: list[str] = []
