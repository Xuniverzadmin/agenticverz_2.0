# Layer: L6 — Platform Substrate
# AUDIENCE: CUSTOMER
# Role: Common time utilities for customer domain modules

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)
