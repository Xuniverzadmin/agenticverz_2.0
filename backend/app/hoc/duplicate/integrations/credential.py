# ============================================================
# DUPLICATE — QUARANTINED (INTEGRATIONS DOMAIN)
#
# This dataclass is a historical duplicate and MUST NOT be used.
#
# Canonical Definition:
#   hoc/cus/integrations/L5_engines/credentials/types.py
#   class Credential
#
# Duplicate Origins:
#   - http_connector.py (lines 99-103)
#   - mcp_connector.py (lines 90-94)
#   - sql_gateway.py (lines 114-118)
#
# Audit Reference:
#   INT-DUP-001
#
# Status:
#   FROZEN — retained for traceability only
#
# Removal:
#   Eligible after Phase DTO authority unification
# ============================================================

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Credential:
    """
    QUARANTINED — Use Credential from credentials/types.py instead.

    Credential from vault.

    This is the FROZEN connector version. The canonical version lives in:
    hoc/cus/integrations/L5_engines/credentials/types.py

    Attributes:
        value: The credential value (e.g., API key, token)
        expires_at: Optional expiration timestamp
    """

    value: str
    expires_at: Optional[datetime] = None
