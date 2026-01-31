# Layer: L5 — Domain Schemas
# AUDIENCE: CUSTOMER
# Role: Account domain schemas - data types and contracts
# Location: hoc/cus/account/L5_schemas/
# Reference: PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md

"""
Account L5 Schemas

Data types and contracts for account domain.
"""

from app.hoc.cus.account.L5_schemas.result_types import AccountsErrorResult  # noqa: F401

__all__ = [
    "AccountsErrorResult",
]
