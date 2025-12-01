# planner/__init__.py
"""
Planner Module (M2.5)

This module provides planner abstractions for AOS:
- PlannerInterface - Protocol for planner implementations
- StubPlanner - Rule-based planner for testing
- LegacyStubPlanner - Backwards-compatible interface
"""

from typing import TYPE_CHECKING

# Lazy imports to avoid circular dependencies
_StubPlanner = None
_LegacyStubPlanner = None
_PlannerInterface = None


def get_stub_planner():
    """Get StubPlanner class (lazy import)."""
    global _StubPlanner
    if _StubPlanner is None:
        from .stub_planner import StubPlanner
        _StubPlanner = StubPlanner
    return _StubPlanner


def get_legacy_stub_planner():
    """Get LegacyStubPlanner class (lazy import)."""
    global _LegacyStubPlanner
    if _LegacyStubPlanner is None:
        from .stub_planner import LegacyStubPlanner
        _LegacyStubPlanner = LegacyStubPlanner
    return _LegacyStubPlanner


if TYPE_CHECKING:
    from .interface import PlannerInterface, PlannerOutput, PlannerError
    from .stub_planner import StubPlanner, LegacyStubPlanner


__all__ = [
    "get_stub_planner",
    "get_legacy_stub_planner",
]
