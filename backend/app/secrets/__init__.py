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
