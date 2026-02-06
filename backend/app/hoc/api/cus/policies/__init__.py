# Layer: L2 — Product APIs
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Limits API package (PIN-LIM)
# Callers: main.py router registration
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: LIMITS_MANAGEMENT_AUDIT.md

"""
Limits API Package

Provides endpoints for:
- Limit simulation (pre-execution checks)
- Limit overrides (temporary increases)
"""

# Legacy imports removed - routers now imported directly in main.py
# TOMBSTONE_EXPIRY: 2026-03-04
# This __init__.py previously re-exported legacy routers
# Now each router module exports its own router directly

__all__: list[str] = []
