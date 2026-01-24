# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: any
#   Execution: sync
# Role: HashiCorp Vault client for secret retrieval
# Callers: config, services needing secrets
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: Core Security

"""
HashiCorp Vault client for secrets management.

This module provides a thin wrapper around Vault's KV v2 secrets engine
for loading secrets at application startup.
"""

import logging
import os
from typing import Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class VaultClient:
    """Client for HashiCorp Vault KV v2 secrets engine."""

    def __init__(
        self,
        addr: Optional[str] = None,
        token: Optional[str] = None,
        mount_path: str = "agenticverz",
    ):
        self.addr = addr or os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
        self.token = token or os.getenv("VAULT_TOKEN")
        self.mount_path = mount_path
        self._client = httpx.Client(
            base_url=self.addr,
            headers={"X-Vault-Token": self.token} if self.token else {},
            timeout=10.0,
        )

    def is_available(self) -> bool:
        """Check if Vault is reachable and unsealed."""
        try:
            resp = self._client.get("/v1/sys/health")
            # 200 = initialized, unsealed, active
            # 429 = unsealed, standby
            # 472 = data recovery mode
            # 473 = performance standby
            # 501 = not initialized
            # 503 = sealed
            return resp.status_code in (200, 429, 472, 473)
        except Exception as e:
            logger.warning(f"Vault not available: {e}")
            return False

    def get_secret(self, path: str) -> Dict[str, str]:
        """
        Get a secret from Vault KV v2.

        Args:
            path: Secret path (e.g., "app-prod", "database")

        Returns:
            Dict of key-value pairs from the secret

        Raises:
            ValueError: If secret not found or Vault error
        """
        if not self.token:
            raise ValueError("VAULT_TOKEN not set")

        url = f"/v1/{self.mount_path}/data/{path}"
        try:
            resp = self._client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", {}).get("data", {})
            elif resp.status_code == 404:
                raise ValueError(f"Secret not found: {path}")
            else:
                raise ValueError(f"Vault error {resp.status_code}: {resp.text}")
        except httpx.HTTPError as e:
            raise ValueError(f"Vault connection error: {e}")

    def close(self):
        """Close the HTTP client."""
        self._client.close()


def load_secrets_to_env(
    paths: Optional[list] = None,
    required: bool = False,
) -> bool:
    """
    Load secrets from Vault and set them as environment variables.

    Args:
        paths: List of secret paths to load (default: app-prod, database, external-apis)
        required: If True, raise error when Vault unavailable

    Returns:
        True if secrets were loaded, False otherwise
    """
    if paths is None:
        paths = ["app-prod", "database", "external-apis"]

    # Check if Vault is configured
    vault_addr = os.getenv("VAULT_ADDR")
    vault_token = os.getenv("VAULT_TOKEN")

    if not vault_addr or not vault_token:
        if required:
            raise ValueError("VAULT_ADDR and VAULT_TOKEN must be set")
        logger.info("Vault not configured, using environment variables")
        return False

    client = VaultClient(addr=vault_addr, token=vault_token)

    if not client.is_available():
        if required:
            raise ValueError("Vault is not available")
        logger.warning("Vault not available, falling back to environment variables")
        client.close()
        return False

    loaded_count = 0
    for path in paths:
        try:
            secrets = client.get_secret(path)
            for key, value in secrets.items():
                # Only set if not already in environment (allow overrides)
                if key not in os.environ:
                    os.environ[key] = str(value)
                    loaded_count += 1
                    logger.debug(f"Loaded secret: {key}")
            logger.info(f"Loaded {len(secrets)} secrets from vault:{path}")
        except ValueError as e:
            logger.warning(f"Failed to load secrets from {path}: {e}")

    client.close()
    logger.info(f"Total secrets loaded from Vault: {loaded_count}")
    return loaded_count > 0


# Singleton instance for app-wide use
_vault_client: Optional[VaultClient] = None


def get_vault_client() -> Optional[VaultClient]:
    """Get the global Vault client instance."""
    global _vault_client
    if _vault_client is None:
        vault_addr = os.getenv("VAULT_ADDR")
        vault_token = os.getenv("VAULT_TOKEN")
        if vault_addr and vault_token:
            _vault_client = VaultClient(addr=vault_addr, token=vault_token)
    return _vault_client
