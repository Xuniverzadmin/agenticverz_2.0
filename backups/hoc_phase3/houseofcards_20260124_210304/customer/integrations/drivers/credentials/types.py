# Layer: L5 — Domain Engine
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (via connectors)
#   Execution: sync
# Role: Canonical Credential dataclass for connector services
# Callers: http_connector.py, mcp_connector.py, sql_gateway.py
# Allowed Imports: L6, L7 (stdlib, dataclasses)
# Forbidden Imports: L1, L2, L3, L4, sqlalchemy, sqlmodel
# Reference: INT-DUP-001 (Quarantine Resolution)
# NOTE: Reclassified L6→L5 (2026-01-24) - Pure dataclass definition, not SQL driver
#       Remains in drivers/ per Layer ≠ Directory principle

"""
Credential Type — Canonical Definition

This is the CANONICAL and ONLY authoritative definition of the
Credential dataclass used by connector services.

History:
    Previously duplicated in:
    - http_connector.py (lines 99-103)
    - mcp_connector.py (lines 90-94)
    - sql_gateway.py (lines 114-118)

    Consolidated here per INT-DUP-001 quarantine resolution.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Credential:
    """
    Credential from vault.

    A simple container for credential values retrieved from
    the credential service. Used by connector services to
    authenticate with external systems.

    Attributes:
        value: The credential value (e.g., API key, token)
        expires_at: Optional expiration timestamp
    """

    value: str
    expires_at: Optional[datetime] = None
