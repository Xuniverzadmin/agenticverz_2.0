# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Webhook signature verification
# Callers: webhook API
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: Webhook Security

"""
Webhook Signature Verification Utility

Provides HMAC-SHA256 signature verification for webhook receivers with
support for key versioning and grace periods during rotation.

Usage (FastAPI example):
    from app.utils.webhook_verify import WebhookVerifier

    verifier = WebhookVerifier(keys={
        "v1": "old_key_hex...",
        "v2": "new_key_hex...",
    }, current_version="v2", grace_versions=["v1"])

    @app.post("/webhook")
    async def receive_webhook(request: Request):
        body = await request.body()
        signature = request.headers.get("X-Webhook-Signature")
        key_version = request.headers.get("X-Webhook-Key-Version")

        if not verifier.verify(body, signature, key_version):
            raise HTTPException(status_code=401, detail="Invalid signature")
        # Process webhook...
"""

import hashlib
import hmac
import logging
import os
from typing import Callable, Dict, List, Optional, Union

logger = logging.getLogger("nova.utils.webhook_verify")


class WebhookVerifier:
    """Webhook signature verifier with key version support.

    Supports zero-downtime key rotation by accepting:
    1. The specified key version from X-Webhook-Key-Version header
    2. Grace period versions during rotation
    3. Current version as fallback if no header provided
    """

    def __init__(
        self,
        keys: Optional[Dict[str, str]] = None,
        current_version: Optional[str] = None,
        grace_versions: Optional[List[str]] = None,
        key_loader: Optional[Callable[[str], Optional[str]]] = None,
    ):
        """Initialize verifier.

        Args:
            keys: Dict mapping version -> hex-encoded secret key
            current_version: Current active key version (default from env)
            grace_versions: List of versions still accepted during rotation
            key_loader: Optional function to dynamically load keys
        """
        self._keys = keys or {}
        self._current = current_version or os.getenv("WEBHOOK_KEY_VERSION", "v1")
        self._grace = grace_versions or self._parse_grace_env()
        self._key_loader = key_loader

    def _parse_grace_env(self) -> List[str]:
        """Parse grace versions from environment."""
        grace_csv = os.getenv("WEBHOOK_KEY_GRACE_VERSIONS", "")
        return [v.strip() for v in grace_csv.split(",") if v.strip()]

    def _get_key(self, version: str) -> Optional[bytes]:
        """Get key bytes for a version."""
        # Try static keys first
        if version in self._keys:
            try:
                return bytes.fromhex(self._keys[version])
            except ValueError:
                logger.error(f"Invalid hex key for version {version}")
                return None

        # Try dynamic loader
        if self._key_loader:
            try:
                key_hex = self._key_loader(version)
                if key_hex:
                    return bytes.fromhex(key_hex)
            except Exception as e:
                logger.error(f"Key loader failed for {version}: {e}")

        return None

    def _compute_signature(self, body: bytes, key: bytes) -> str:
        """Compute HMAC-SHA256 signature."""
        return hmac.new(key, body, hashlib.sha256).hexdigest()

    def verify(
        self,
        body: Union[bytes, str],
        signature: Optional[str],
        key_version: Optional[str] = None,
    ) -> bool:
        """Verify webhook signature.

        Args:
            body: Raw request body
            signature: X-Webhook-Signature header value (format: "sha256=<hex>")
            key_version: X-Webhook-Key-Version header value

        Returns:
            True if signature is valid
        """
        if not signature:
            logger.warning("No signature provided")
            return False

        # Parse signature
        if signature.startswith("sha256="):
            provided_sig = signature[7:]
        else:
            logger.warning("Invalid signature format (expected sha256=...)")
            return False

        # Ensure body is bytes
        if isinstance(body, str):
            body = body.encode("utf-8")

        # Build list of versions to try
        versions_to_try: List[str] = []

        # 1. Explicit version from header
        if key_version:
            versions_to_try.append(key_version)

        # 2. Grace versions
        versions_to_try.extend(self._grace)

        # 3. Current version as fallback
        if self._current not in versions_to_try:
            versions_to_try.append(self._current)

        # Remove duplicates while preserving order
        seen = set()
        unique_versions = []
        for v in versions_to_try:
            if v not in seen:
                seen.add(v)
                unique_versions.append(v)

        # Try each version
        for version in unique_versions:
            key = self._get_key(version)
            if key is None:
                continue

            computed = self._compute_signature(body, key)
            if hmac.compare_digest(computed, provided_sig):
                if version != key_version and key_version:
                    logger.info(f"Signature verified with grace version {version} (header specified {key_version})")
                return True

        logger.warning(
            f"Signature verification failed. Tried versions: {unique_versions}, header version: {key_version}"
        )
        return False

    def sign(
        self,
        body: Union[bytes, str],
        version: Optional[str] = None,
    ) -> tuple:
        """Sign a payload (for testing or forwarding).

        Args:
            body: Payload to sign
            version: Key version to use (default: current)

        Returns:
            Tuple of (signature_header, version_header)

        Raises:
            ValueError: If key not found for version
        """
        version = version or self._current
        key = self._get_key(version)

        if key is None:
            raise ValueError(f"No key found for version {version}")

        if isinstance(body, str):
            body = body.encode("utf-8")

        signature = self._compute_signature(body, key)
        return f"sha256={signature}", version


def create_file_key_loader(keys_path: str) -> Callable[[str], Optional[str]]:
    """Create a key loader that reads from files.

    Args:
        keys_path: Directory containing key files (e.g., /var/lib/aos/webhook-keys)

    Returns:
        Function that loads key hex string for a version
    """

    def loader(version: str) -> Optional[str]:
        key_file = os.path.join(keys_path, version)
        if os.path.isfile(key_file):
            with open(key_file, "r") as f:
                return f.read().strip()
        return None

    return loader


def create_vault_key_loader(
    mount_path: str = "secret",
    secret_path: str = "webhook/keys",
) -> Callable[[str], Optional[str]]:
    """Create a key loader that reads from Vault.

    Requires hvac library: pip install hvac

    Args:
        mount_path: Vault KV v2 mount path
        secret_path: Path to secret within mount

    Returns:
        Function that loads key hex string for a version
    """

    def loader(version: str) -> Optional[str]:
        try:
            import hvac

            client = hvac.Client(
                url=os.getenv("VAULT_ADDR"),
                token=os.getenv("VAULT_TOKEN"),
            )
            secret = client.secrets.kv.v2.read_secret_version(
                mount_point=mount_path,
                path=secret_path,
            )
            return secret["data"]["data"].get(version)
        except Exception as e:
            logger.error(f"Vault key load failed: {e}")
            return None

    return loader


# Convenience function for quick verification
def verify_webhook(
    body: bytes,
    signature: str,
    key_version: Optional[str],
    keys: Dict[str, str],
    grace_versions: Optional[List[str]] = None,
) -> bool:
    """Quick verification without creating a WebhookVerifier instance.

    Args:
        body: Raw request body
        signature: X-Webhook-Signature header
        key_version: X-Webhook-Key-Version header
        keys: Dict of version -> hex key
        grace_versions: List of grace period versions

    Returns:
        True if valid
    """
    verifier = WebhookVerifier(
        keys=keys,
        current_version=key_version or list(keys.keys())[-1],
        grace_versions=grace_versions or [],
    )
    return verifier.verify(body, signature, key_version)
