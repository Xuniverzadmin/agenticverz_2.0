# Layer: L4 — Domain Services
# AUDIENCE: CUSTOMER
# Role: account domain - engines
# Reference: DIRECTORY_REORGANIZATION_PLAN.md, HOC_account_analysis_v1.md

"""
account / engines

CUSTOMER-facing account engines.

NOTE: iam_service.py was moved to internal/platform/iam/engines/
because it declares AUDIENCE: INTERNAL.

For INTERNAL IAM operations, use:
    from app.houseofcards.internal.platform.iam.engines import get_iam_service

For CUSTOMER account operations, use the facades:
    from app.houseofcards.customer.account.facades import get_accounts_facade
"""
