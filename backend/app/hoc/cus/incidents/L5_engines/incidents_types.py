# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Role: Shared type aliases for incidents domain engines
"""
Incidents Domain Shared Types

Canonical type aliases used across multiple engines in the incidents domain.
This file consolidates duplicated type definitions (INC-DUP-008).

Usage:
    from app.hoc.cus.incidents.L5_engines.incidents_types import (
        UuidFn,
        ClockFn,
    )
"""

from datetime import datetime
from typing import Callable

# Type alias for UUID generation function (dependency injection)
UuidFn = Callable[[], str]

# Type alias for clock function (dependency injection)
ClockFn = Callable[[], datetime]


__all__ = [
    "UuidFn",
    "ClockFn",
]
