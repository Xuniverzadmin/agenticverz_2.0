# Layer: L6 — Driver
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (via connectors)
#   Execution: async
# Role: Canonical Credential dataclass for connector services
# Callers: http_connector.py, mcp_connector.py, sql_gateway.py
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: INT-DUP-001 (Quarantine Resolution)

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
