# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Role: Runtime utilities
# Callers: runtime, workers
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: Runtime

"""
Runtime Utilities - Centralized Shared Helpers

CANONICAL LOCATION: All code needing generate_uuid() or utc_now() must import from here.
DO NOT define these functions elsewhere.
DO NOT import them transitively through other modules.

This prevents import hygiene violations where services fail at runtime
because they relied on transitive imports that aren't guaranteed.

See LESSONS_ENFORCED.md Invariant #5: Import Locality
"""

from datetime import datetime, timezone
from uuid import uuid4


def generate_uuid() -> str:
    """
    Generate a UUID string.

    CANONICAL LOCATION: Import from app.utils.runtime, not from other modules.
    """
    return str(uuid4())


def utc_now() -> datetime:
    """
    Return timezone-aware UTC datetime.

    CANONICAL LOCATION: Import from app.utils.runtime, not from other modules.

    For asyncpg compatibility in raw SQL, use utc_now_naive() instead.
    """
    return datetime.now(timezone.utc)


def utc_now_naive() -> datetime:
    """
    Return timezone-naive UTC datetime (for asyncpg raw SQL compatibility).

    Use this ONLY when:
    - Writing raw SQL with asyncpg
    - You explicitly need a naive datetime

    For all other cases, prefer utc_now().
    """
    # Use timezone-aware then strip tzinfo (avoids deprecated utcnow())
    return datetime.now(timezone.utc).replace(tzinfo=None)
