# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: test
#   Execution: sync
# Role: Test helper module exports
# Callers: Test files
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-270 (Infrastructure State Governance)

"""
Test helpers for infrastructure dependency management.

This module provides utilities for declaring and checking
infrastructure dependencies in tests, aligned with INFRA_REGISTRY.md.
"""

from tests.helpers.infra import (
    INFRA_REGISTRY,
    InfraBucket,
    InfraState,
    check_infra_available,
    get_infra_skip_reason,
    requires_infra,
)

__all__ = [
    "InfraState",
    "InfraBucket",
    "INFRA_REGISTRY",
    "requires_infra",
    "check_infra_available",
    "get_infra_skip_reason",
]
