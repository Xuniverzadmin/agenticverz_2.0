# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: internal
#   Execution: sync
# Role: M7→M28 authority mapping package
# Reference: docs/invariants/AUTHZ_AUTHORITY.md

"""
M7→M28 Authority Mapping Package

This package contains the translation layer from legacy M7 (PolicyObject)
to the authoritative M28 (AuthorizationEngine).

INVARIANT: This is a ONE-WAY mapping. No M28→M7 reverse mapping allowed.
"""

"""
M7→M28 Authority Mapping Package

Stale m7_to_m28 re-export removed — module lives at app/auth/mappings/m7_to_m28.py,
not in this package. No consumers import from app.hoc.int.policies.engines (verified 2026-02-06).
"""

__all__: list[str] = []
