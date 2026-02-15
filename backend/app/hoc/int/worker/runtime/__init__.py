# runtime/__init__.py
"""
Machine-Native Runtime Interfaces (M1 + M2)

This module provides the core runtime APIs for AOS:
- runtime.execute() - Execute skills, never throws, returns StructuredOutcome
- runtime.describe_skill() - Get skill metadata
- runtime.query() - Query budget, state, history
- runtime.get_resource_contract() - Get resource constraints

All interfaces are designed for machine-native operation:
- Queryable state (not log parsing)
- Capability contracts (not just tool lists)
- Structured outcomes (never throws)
- Failure as data (navigable, not opaque)

M2 adds:
- IntegratedRuntime - Runtime with SkillRegistry v2 integration
- create_integrated_runtime() - Factory with optional stub registration

Note: IntegratedRuntime requires pydantic. Use lazy import to avoid
breaking tests that only need core Runtime.
"""

from .core import ErrorCategory, ResourceContract, Runtime, SkillDescriptor, StructuredOutcome

__all__ = [
    "Runtime",
    "StructuredOutcome",
    "SkillDescriptor",
    "ResourceContract",
    "ErrorCategory",
]


def get_integrated_runtime_class():
    """Lazy import for IntegratedRuntime (requires pydantic)."""
    from .integrated_runtime import IntegratedRuntime

    return IntegratedRuntime


def create_integrated_runtime(*args, **kwargs):
    """Lazy factory for IntegratedRuntime (requires pydantic)."""
    from .integrated_runtime import create_integrated_runtime as _create

    return _create(*args, **kwargs)
