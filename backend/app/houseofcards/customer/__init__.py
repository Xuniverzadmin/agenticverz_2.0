# Layer: L4 — Domain Services
# AUDIENCE: CUSTOMER
# Role: Customer-facing domain services package
# Reference: DIRECTORY_REORGANIZATION_PLAN.md

"""
Customer Domain Services (houseofcards)

All customer-facing domain logic organized by:
- Domain (overview, activity, incidents, policies, logs, analytics, account, integrations, api_keys, general)
- Role (facades, drivers, engines, schemas)

Pattern: app/houseofcards/customer/{domain}/{role}/{file}.py
"""

__all__ = [
    "overview",
    "activity",
    "incidents",
    "policies",
    "logs",
    "analytics",
    "account",
    "integrations",
    "api_keys",
    "general",
]
