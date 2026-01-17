# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Error types for cross-domain governance
# Callers: L2, L3, L4 services
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L5, L6
# Reference: CROSS_DOMAIN_GOVERNANCE.md

"""
Cross-Domain Governance Errors

Foundational error types for mandatory governance operations.
These errors MUST surface to the caller - they cannot be silently caught.
"""

from app.errors.governance import GovernanceError

__all__ = [
    "GovernanceError",
]
