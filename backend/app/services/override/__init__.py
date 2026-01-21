# Layer: L4 — Domain Engines
# Product: system-wide
# Reference: GAP-034 (Override Authority Integration)
"""
Override Authority Integration Service (GAP-034)

Provides integration between OverrideAuthority model and the
prevention engine. The prevention engine must check override
status before enforcing policy actions.

This module provides:
    - OverrideAuthorityChecker: Checks override status for policies
    - OverrideStatus: Result of an override check
    - should_skip_enforcement: Quick helper function
"""

from app.services.override.authority_checker import (
    OverrideAuthorityChecker,
    OverrideCheckResult,
    OverrideStatus,
    should_skip_enforcement,
)

__all__ = [
    "OverrideAuthorityChecker",
    "OverrideCheckResult",
    "OverrideStatus",
    "should_skip_enforcement",
]
