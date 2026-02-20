# capability_id: CAP-002
# Layer: L5 — Domain Schema
# AUDIENCE: CUSTOMER
# Role: Analytics query type definitions (enums shared across L2 and L5)
# Callers: api/cus/policies/analytics.py (L2), analytics/L5_engines/analytics_facade.py (L5)
# Reference: PIN-504 (Cross-Domain Violation Resolution)
# artifact_class: CODE

"""
Analytics Query Types

Shared enum definitions for analytics query parameters.
Lives in L5_schemas so L2 can import without violating L2→L5 rules.
"""

from enum import Enum


class ResolutionType(str, Enum):
    """Time resolution for analytics data."""

    HOUR = "hour"
    DAY = "day"


class ScopeType(str, Enum):
    """Scope of analytics aggregation."""

    ORG = "org"
    PROJECT = "project"
    ENV = "env"


__all__ = [
    "ResolutionType",
    "ScopeType",
]
