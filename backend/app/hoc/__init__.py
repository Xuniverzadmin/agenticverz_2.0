# Layer: L4 — Domain Services
# AUDIENCE: ALL
# Role: House of Cards - New isolated domain structure
# Reference: DIRECTORY_REORGANIZATION_PLAN.md

"""
House of Cards (hoc)

Isolated new directory structure for domain reorganization.
This namespace is completely separate from the existing `app/services/` structure.

Structure:
    app/hoc/{audience}/{domain}/{role}/{file}.py

Audiences:
    - customer: Customer-facing domains (10 domains)
    - internal: Infrastructure services (2 domains)
    - founder: Admin/ops tools (1 domain)

Roles:
    - facades: Entry points (L2 APIs call these)
    - drivers: Orchestrators (coordinate engines)
    - engines: Pure domain logic
    - schemas: DTOs, types, contracts

Migration Strategy:
    1. COPY files from app/services/ to app/hoc/
    2. Keep originals unchanged (fallback)
    3. Gradually switch imports to new paths
    4. Delete originals after validation (Step 14)
"""

__all__ = [
    "customer",
    "internal",
    "founder",
]
