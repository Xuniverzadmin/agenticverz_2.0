# Layer: L4 — HOC Spine (Schemas)
# AUDIENCE: SHARED
# Product: system-wide
# Role: Shared threshold types — cross-domain data contracts for controls/activity
# Callers: controls/L6_drivers/threshold_driver.py, activity/L6_drivers/__init__.py
# Reference: PIN-504 (Cross-Domain Violation Resolution)
# artifact_class: CODE

"""
Threshold Types (Spine Schemas)

Shared data types for threshold limit operations.
Extracted from controls/L6_drivers/threshold_driver.py so activity domain
can import types without cross-domain L6 dependency.
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
