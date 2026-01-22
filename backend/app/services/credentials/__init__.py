# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Credential vault abstraction for secure credential management
# Callers: ConnectorRegistry, LifecycleHandlers, API routes
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: GAP-171 (Credential Vault Integration)

"""
Credential Vault Service (GAP-171)

Provides a unified interface for secure credential management across:
- HashiCorp Vault
- AWS Secrets Manager
- Environment variables (development only)

Features:
- Tenant-isolated credential storage
- Credential type validation
- Automatic rotation support
- Audit logging of credential access
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .vault import CredentialVault
    from .service import CredentialService

__all__ = [
    "CredentialVault",
    "CredentialService",
    "get_credential_vault",
    "get_credential_service",
    "configure_credential_service",
    "reset_credential_service",
]

# Lazy import cache
_credential_vault = None
_credential_service = None


def get_credential_vault():
    """Get the credential vault instance based on configuration."""
    global _credential_vault
    if _credential_vault is None:
        from .vault import create_credential_vault
        _credential_vault = create_credential_vault()
    return _credential_vault


def get_credential_service():
    """Get the singleton credential service."""
    global _credential_service
    if _credential_service is None:
        from .service import CredentialService
        _credential_service = CredentialService(vault=get_credential_vault())
    return _credential_service


def configure_credential_service(vault=None, service=None):
    """Configure the credential service (for testing)."""
    global _credential_vault, _credential_service
    if vault is not None:
        _credential_vault = vault
    if service is not None:
        _credential_service = service


def reset_credential_service():
    """Reset the credential service (for testing)."""
    global _credential_vault, _credential_service
    _credential_vault = None
    _credential_service = None
