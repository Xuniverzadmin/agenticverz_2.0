# capability_id: CAP-012
# Layer: L5 — Domain Schemas
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: Account domain shared result types — importable by L2 without L5 engine dependency
# Callers: L2 APIs (aos_accounts.py), L5 engines (accounts_facade.py)
# Reference: PIN-504 (Cross-Domain Violation Resolution)
# artifact_class: CODE

"""
Account Result Types (L5 Schemas)

Shared data types for account domain results.
Extracted from accounts_facade.py so L2 can import without pulling in L5 engine code.
"""

from dataclasses import dataclass


@dataclass
class AccountsErrorResult:
    """Error result for accounts operations."""

    error: str
    message: str
    status_code: int = 400
