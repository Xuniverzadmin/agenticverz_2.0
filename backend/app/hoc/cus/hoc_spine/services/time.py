# Layer: L4 — HOC Spine (Service)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: none
# Role: Common time utilities for customer domain modules (pure datetime computation)
# Callers: All customer modules
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L6 (no DB), sqlalchemy
# Reference: PIN-470, Runtime Utilities
# NOTE: Reclassified L6→L5 (2026-01-24) - Pure datetime utility, no boundary crossing

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)
