# Layer: L4 — Domain Engines
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (via connectors)
#   Execution: async
# Role: Canonical credential types for connector services
# Callers: http_connector.py, mcp_connector.py, sql_gateway.py
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: INT-DUP-001, INT-DUP-002 (Quarantine Resolution)

"""
Credentials Engine — Canonical Types

This package provides the canonical definitions for credential types
used by connector services (HTTP, MCP, SQL Gateway).

AUTHORITY:
    This is the ONLY authoritative source for:
    - Credential dataclass
    - CredentialService protocol

All connector files MUST import from here.
Do NOT define local Credential or CredentialService types in connectors.

Exports:
    - Credential: Simple credential value holder
    - CredentialService: Protocol for credential retrieval
"""

from .types import Credential
from .protocol import CredentialService

__all__ = ["Credential", "CredentialService"]
