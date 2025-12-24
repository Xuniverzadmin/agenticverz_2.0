"""
Mypy Autofix System - Mechanical type safety enforcement.

This module provides:
- macros: Transform functions for common type fixes
- rules: Configuration for which fixes to apply
- apply: Engine that runs mypy and applies fixes

Usage:
    python -m tools.mypy_autofix.apply
    python -m tools.mypy_autofix.apply --zone-a --dry-run
"""

from tools.mypy_autofix.macros import (
    bool_wrap,
    callable_fix,
    cast_expr,
    float_wrap,
    guard_optional,
    int_wrap,
    return_cast,
    unreachable,
)

__all__ = [
    "guard_optional",
    "cast_expr",
    "return_cast",
    "callable_fix",
    "unreachable",
    "bool_wrap",
    "int_wrap",
    "float_wrap",
]
