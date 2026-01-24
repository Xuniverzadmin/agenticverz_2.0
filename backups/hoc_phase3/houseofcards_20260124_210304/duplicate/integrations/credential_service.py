# ============================================================
# DUPLICATE — QUARANTINED (INTEGRATIONS DOMAIN)
#
# This protocol is a historical duplicate and MUST NOT be used.
#
# Canonical Definition:
#   houseofcards/customer/integrations/engines/credentials/protocol.py
#   class CredentialService
#
# Duplicate Origins:
#   - http_connector.py (lines 106-112)
#   - mcp_connector.py (lines 97-103)
#   - sql_gateway.py (lines 121-127)
#
# Audit Reference:
#   INT-DUP-002
#
# Status:
#   FROZEN — retained for traceability only
#
# Removal:
#   Eligible after Phase DTO authority unification
# ============================================================

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Protocol, runtime_checkable


@dataclass
class Credential:
    """Credential from vault (local copy for protocol definition)."""
    value: str
    expires_at: Optional[datetime] = None


@runtime_checkable
class CredentialService(Protocol):
    """
    QUARANTINED — Use CredentialService from credentials/protocol.py instead.

    Protocol for credential service.

    This is the FROZEN connector version. The canonical version lives in:
    houseofcards/customer/integrations/engines/credentials/protocol.py
    """

    async def get(self, credential_ref: str) -> Credential:
        """Get credential from vault."""
        ...
