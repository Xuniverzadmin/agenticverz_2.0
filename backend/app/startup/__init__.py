# Layer: L5 — Execution & Workers
# Product: system-wide
# Role: Startup validation and boot guards

"""
Startup Package

Contains boot-time validation and guards:
- boot_guard: SPINE component validation (GAP-067)
"""

from app.startup.boot_guard import (
    validate_spine_components,
    SpineValidationError,
    get_boot_status,
)

__all__ = [
    "validate_spine_components",
    "SpineValidationError",
    "get_boot_status",
]
