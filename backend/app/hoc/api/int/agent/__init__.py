# capability_id: CAP-012
# Layer: L3 — Boundary Adapter
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: FastAPI dependency injection utilities
# Callers: API route handlers
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L5

"""API Dependencies Module.

NOTE: founder_auth re-export removed — module lives at app/api/dependencies/founder_auth.py,
not in this package. No consumers import from app.hoc.api.int.agent (verified 2026-02-06).
"""

__all__: list[str] = []
