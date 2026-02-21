# capability_id: CAP-001
# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Temporal:
#   Trigger: n/a (type definitions)
#   Execution: n/a
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: none
# Role: Shared type aliases for incidents domain engines
# Callers: All incidents domain engines
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470
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
