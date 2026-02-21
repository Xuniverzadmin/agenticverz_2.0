# capability_id: CAP-018
# Layer: L5 — Domain Engine
# AUDIENCE: INTERNAL
# Temporal:
#   Trigger: api (via connectors)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none (protocol definition)
#   Writes: none
# Role: Canonical CredentialService protocol for connector services
# Product: system-wide
# Callers: http_connector.py, mcp_connector.py, sql_gateway.py
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, INT-DUP-002 (Quarantine Resolution)

"""
CredentialService Protocol — Canonical Definition

This is the CANONICAL and ONLY authoritative definition of the
CredentialService protocol used by connector services.

History:
    Previously duplicated in:
    - http_connector.py (lines 106-112)
    - mcp_connector.py (lines 97-103)
    - sql_gateway.py (lines 121-127)

    Consolidated here per INT-DUP-002 quarantine resolution.
"""

from typing import Protocol, runtime_checkable

from app.hoc.cus.integrations.L5_engines.types import Credential


@runtime_checkable
class CredentialService(Protocol):
    """
    Protocol for credential service.

    Defines the contract for services that retrieve credentials
    from a vault or other secure storage. Connector services
    depend on this protocol for authentication.

    Implementations:
        - CusCredentialService (vault/engines/cus_credential_service.py)
        - Any vault adapter that provides credential retrieval
    """

    async def get(self, credential_ref: str) -> Credential:
        """
        Get credential from vault.

        Args:
            credential_ref: Reference to the credential (e.g., vault path)

        Returns:
            Credential with value and optional expiration
        """
        ...
