# Layer: L3 — Boundary Adapter
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: FastAPI dependency injection utilities
# Callers: API route handlers
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L5

"""API Dependencies Module."""

from .founder_auth import require_founder, verify_fops_token

__all__ = ["require_founder", "verify_fops_token"]
