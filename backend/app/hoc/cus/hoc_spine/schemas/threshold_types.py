# Layer: L4 — HOC Spine (Schemas)
# AUDIENCE: SHARED
# Product: system-wide
# Consumers: legacy (docs), optional ports
# Role: Legacy threshold types — historical cross-domain contract
# Reference: PIN-504 (Cross-Domain Violation Resolution)
# artifact_class: CODE

"""
Threshold Types (Spine Schemas)

Shared data types for threshold limit operations.
Historical extraction point for `LimitSnapshot`.

As of 2026-02-08 (T0 strict mode), L6 drivers under `hoc/cus/*/L6_drivers`
must not import `hoc_spine`. Domain-local DTOs are preferred (e.g.
`controls/L6_drivers/threshold_driver.py` defines its own `LimitSnapshot`).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class LimitSnapshot:
    """
    Immutable snapshot of a Limit record returned to engines.

    This is the boundary contract between L6 (driver) and L5 (engine).
    Engines receive snapshots, not ORM models.
    """

    id: str
    tenant_id: str
    scope: str
    scope_id: Optional[str]
    params: dict
    status: str
    created_at: datetime
