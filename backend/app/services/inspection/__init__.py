# Layer: L4 — Domain Engines
# Product: system-wide
# Reference: GAP-033 (Inspection Constraints)
"""
Inspection Constraint Enforcement Service (GAP-033)

Enforces MonitorConfig inspection constraints before logging
or data capture operations. These are "negative capabilities" -
things the policy is NOT allowed to inspect.

This module provides:
    - InspectionConstraintChecker: Main enforcement class
    - InspectionOperation: Enum of operations requiring constraint checks
    - check_inspection_allowed: Quick helper function
    - get_constraint_violations: Get all violations for a set of operations
"""

from app.services.inspection.constraint_checker import (
    InspectionConstraintChecker,
    InspectionConstraintViolation,
    InspectionOperation,
    check_inspection_allowed,
    get_constraint_violations,
)

__all__ = [
    "InspectionConstraintChecker",
    "InspectionConstraintViolation",
    "InspectionOperation",
    "check_inspection_allowed",
    "get_constraint_violations",
]
