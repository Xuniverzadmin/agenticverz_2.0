# capability_id: CAP-006
# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Secrets management package marker
# Callers: Secrets imports
# Allowed Imports: None
# Forbidden Imports: None
# Reference: Package Structure

"""Secrets management module."""

from .vault_client import (
    VaultClient,
    get_vault_client,
    load_secrets_to_env,
)

__all__ = [
    "VaultClient",
    "get_vault_client",
    "load_secrets_to_env",
]
