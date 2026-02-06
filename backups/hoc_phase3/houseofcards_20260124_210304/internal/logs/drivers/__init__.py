# Layer: L6 — Platform Substrate
# Product: system-wide
# Role: Core module - foundational primitives
# Reference: ExecutionContext Specification v1.0

"""
Core Module

Foundational primitives for the AOS runtime.
"""

from app.core.execution_context import (
    EvidenceSource,
    ExecutionContext,
    ExecutionPhase,
)

__all__ = [
    "ExecutionContext",
    "ExecutionPhase",
    "EvidenceSource",
]
