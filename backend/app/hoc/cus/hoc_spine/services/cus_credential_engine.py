# capability_id: CAP-012
# Layer: L4 — HOC Spine (Service)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none (pure encryption)
#   Writes: none
# Role: Credential encryption and vault integration for customer LLM integrations
# Callers: cus_health_engine, cus_health_driver
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, docs/architecture/CUSTOMER_INTEGRATIONS_ARCHITECTURE.md

"""Customer Credential Service

PURPOSE:
    Secure handling of customer LLM API credentials.
    Encrypts credentials at rest, provides vault-ready integration.

SECURITY PRINCIPLES:
    1. NO PLAINTEXT PERSISTENCE: All stored credentials are encrypted
    2. ROTATION-READY: Credentials can be rotated without downtime
    3. AUDIT TRAIL: All credential access is logged
    4. MINIMAL EXPOSURE: Decryption only at point of use

CREDENTIAL REFERENCE FORMAT:
    - vault://<path>         - HashiCorp Vault reference
    - encrypted://<id>       - Locally encrypted (AES-256-GCM)
    - env://<var_name>       - Environment variable (dev only)

ENCRYPTION:
    - Algorithm: AES-256-GCM
    - Key derivation: PBKDF2 with per-tenant salt
    - In production: KEK from external key management service
"""

import base64
import hashlib
import hmac
import logging
import os
import secrets
from typing import Dict, Optional, Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)


class CusCredentialService:
    """Service for managing customer LLM credentials.

    Phase 4: Secure credential storage and retrieval.
    Production deployments should use external vault integration.
    """

    # Encryption parameters
    KEY_LENGTH = 32  # 256 bits
    NONCE_LENGTH = 12  # 96 bits for GCM
    TAG_LENGTH = 16  # 128 bits

    def __init__(self, master_key: Optional[bytes] = None):
        """Initialize credential service.

        Args:
            master_key: 32-byte master encryption key.
                        If None, derives from CREDENTIAL_MASTER_KEY env var.

        Raises:
            ValueError: If no valid master key available
        """
        if master_key:
            self._master_key = master_key
        else:
            # Try to get from environment
            key_b64 = os.environ.get("CREDENTIAL_MASTER_KEY")
            if key_b64:
                self._master_key = base64.b64decode(key_b64)
            else:
                # Development fallback - NOT FOR PRODUCTION
                logger.warning(
                    "CREDENTIAL_MASTER_KEY not set - using development key. "
                    "DO NOT USE IN PRODUCTION."
                )
                self._master_key = self._derive_dev_key()

        if len(self._master_key) != self.KEY_LENGTH:
            raise ValueError(
                f"Master key must be {self.KEY_LENGTH} bytes, "
                f"got {len(self._master_key)}"
            )

    def _derive_dev_key(self) -> bytes:
        """Derive a development key (NOT SECURE FOR PRODUCTION).

        Returns:
            32-byte key derived from static seed
        """
        # This is intentionally weak - only for development
        seed = b"agenticverz-dev-credential-key-do-not-use-in-prod"
        return hashlib.sha256(seed).digest()

    def _derive_tenant_key(self, tenant_id: str) -> bytes:
        """Derive a tenant-specific encryption key.

        Uses HKDF-like key derivation to isolate tenant keys.

        Args:
            tenant_id: Tenant identifier

        Returns:
            32-byte tenant-specific key
        """
        # Use HMAC-SHA256 for key derivation
        return hmac.new(
            self._master_key,
            f"tenant:{tenant_id}".encode(),
            hashlib.sha256,
        ).digest()

    # =========================================================================
    # ENCRYPT / DECRYPT
    # =========================================================================

    def encrypt_credential(
        self,
        tenant_id: str,
        plaintext: str,
        context: Optional[Dict[str, str]] = None,
    ) -> str:
        """Encrypt a credential for storage.

        Args:
            tenant_id: Owning tenant (used for key derivation)
            plaintext: The credential to encrypt (e.g., API key)
            context: Optional additional authenticated data

        Returns:
            Credential reference in format: encrypted://<base64_blob>
        """
        # Derive tenant key
        tenant_key = self._derive_tenant_key(tenant_id)
        aesgcm = AESGCM(tenant_key)

        # Generate random nonce
        nonce = secrets.token_bytes(self.NONCE_LENGTH)

        # Build AAD (Additional Authenticated Data)
        aad = f"tenant:{tenant_id}".encode()
        if context:
            for k, v in sorted(context.items()):
                aad += f"|{k}:{v}".encode()

        # Encrypt
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), aad)

        # Pack: nonce + ciphertext (includes tag)
        blob = nonce + ciphertext
        encoded = base64.urlsafe_b64encode(blob).decode("ascii")

        logger.info(
            f"Encrypted credential for tenant {tenant_id[:8]}...",
            extra={"tenant_id": tenant_id},
        )

        return f"encrypted://{encoded}"

    def decrypt_credential(
        self,
        tenant_id: str,
        credential_ref: str,
        context: Optional[Dict[str, str]] = None,
    ) -> str:
        """Decrypt a credential reference.

        Args:
            tenant_id: Owning tenant (used for key derivation)
            credential_ref: The credential reference (encrypted://... format)
            context: Optional additional authenticated data (must match encrypt)

        Returns:
            Decrypted plaintext credential

        Raises:
            ValueError: If credential format is invalid or decryption fails
        """
        # Parse reference
        if not credential_ref.startswith("encrypted://"):
            raise ValueError(
                f"Invalid credential reference format: {credential_ref[:20]}..."
            )

        encoded = credential_ref[len("encrypted://") :]

        try:
            blob = base64.urlsafe_b64decode(encoded)
        except Exception as e:
            raise ValueError(f"Invalid base64 encoding in credential reference: {e}")

        if len(blob) < self.NONCE_LENGTH + self.TAG_LENGTH:
            raise ValueError("Credential blob too short")

        # Unpack
        nonce = blob[: self.NONCE_LENGTH]
        ciphertext = blob[self.NONCE_LENGTH :]

        # Derive tenant key
        tenant_key = self._derive_tenant_key(tenant_id)
        aesgcm = AESGCM(tenant_key)

        # Build AAD
        aad = f"tenant:{tenant_id}".encode()
        if context:
            for k, v in sorted(context.items()):
                aad += f"|{k}:{v}".encode()

        try:
            plaintext = aesgcm.decrypt(nonce, ciphertext, aad)
        except Exception as e:
            logger.warning(
                f"Failed to decrypt credential for tenant {tenant_id[:8]}...: {e}",
                extra={"tenant_id": tenant_id},
            )
            raise ValueError("Credential decryption failed - invalid key or tampering")

        logger.info(
            f"Decrypted credential for tenant {tenant_id[:8]}...",
            extra={"tenant_id": tenant_id},
        )

        return plaintext.decode("utf-8")

    # =========================================================================
    # CREDENTIAL REFERENCE RESOLUTION
    # =========================================================================

    def resolve_credential(
        self,
        tenant_id: str,
        credential_ref: str,
        context: Optional[Dict[str, str]] = None,
    ) -> str:
        """Resolve a credential reference to plaintext (SYNC).

        Supports multiple credential reference formats:
        - encrypted://<blob>   - Decrypt locally (sync)
        - vault://<path>       - Legacy format (raises error)
        - env://<var>          - Read from environment (dev only, sync)
        - cus-vault://<t>/<id> - Use resolve_cus_vault_credential() (async)

        Args:
            tenant_id: Owning tenant
            credential_ref: Credential reference
            context: Optional context for encryption

        Returns:
            Plaintext credential

        Raises:
            ValueError: If reference format unknown or resolution fails
        """
        if credential_ref.startswith("encrypted://"):
            return self.decrypt_credential(tenant_id, credential_ref, context)

        elif credential_ref.startswith("cus-vault://"):
            raise ValueError(
                "cus-vault:// references require async resolution. "
                "Use resolve_cus_vault_credential() instead."
            )

        elif credential_ref.startswith("vault://"):
            return self._resolve_vault_credential(credential_ref)

        elif credential_ref.startswith("env://"):
            return self._resolve_env_credential(credential_ref)

        else:
            # Reject plaintext credentials
            raise ValueError(
                "Invalid credential reference. Must use encrypted://, cus-vault://, or env:// prefix. "
                "Raw API keys are not permitted."
            )

    def _resolve_vault_credential(self, credential_ref: str) -> str:
        """Resolve a HashiCorp Vault credential reference (legacy format).

        Args:
            credential_ref: vault://<path> reference

        Returns:
            Plaintext credential from vault

        Raises:
            ValueError: Use cus-vault:// format instead
        """
        path = credential_ref[len("vault://") :]
        logger.warning(f"Legacy vault:// format used: {path}")
        raise ValueError(
            f"Legacy vault:// format not supported. "
            f"Use cus-vault://<tenant_id>/<credential_id> format instead. Path: {path}"
        )

    async def resolve_cus_vault_credential(
        self,
        credential_ref: str,
        *,
        accessor_id: str,
        accessor_type: str,
        access_reason: Optional[str] = None,
    ) -> str:
        """Resolve a cus-vault:// credential reference (PIN-517).

        Format: cus-vault://<tenant_id>/<credential_id>

        Args:
            credential_ref: cus-vault://<tenant_id>/<credential_id> reference
            accessor_id: Who is accessing (user_id, run_id, tool_id)
            accessor_type: Type of accessor ("human", "machine", "mcp_tool")
            access_reason: Why access is needed

        Returns:
            Plaintext credential value

        Raises:
            ValueError: If reference format invalid or credential not found
            PermissionError: If access denied by policy
        """
        from app.hoc.cus.integrations.L5_vault.drivers.vault import create_credential_vault
        from app.hoc.cus.integrations.L5_vault.engines.service import CredentialService
        from app.hoc.cus.integrations.L5_vault.engines.vault_rule_check import (
            DefaultCredentialAccessRuleChecker,
        )

        if not credential_ref.startswith("cus-vault://"):
            raise ValueError(f"Invalid cus-vault reference: {credential_ref}")

        # Parse: cus-vault://<tenant_id>/<credential_id>
        path = credential_ref[len("cus-vault://"):]
        parts = path.split("/", 1)
        if len(parts) != 2:
            raise ValueError(
                f"Invalid cus-vault path: {path}. "
                "Expected: cus-vault://<tenant_id>/<credential_id>"
            )

        tenant_id, credential_id = parts

        # Create customer-scope vault (fail-closed)
        try:
            vault = create_credential_vault(scope="customer")
        except ValueError as e:
            logger.error(f"Failed to create customer vault: {e}")
            raise

        # Check access rules
        rule_checker = DefaultCredentialAccessRuleChecker()
        rule_result = await rule_checker.check_credential_access(
            tenant_id=tenant_id,
            credential_ref=credential_ref,
            accessor_id=accessor_id,
            accessor_type=accessor_type,
            access_reason=access_reason,
        )

        if not rule_result.allowed:
            logger.warning(
                f"Credential access denied: {credential_ref} by {accessor_id}",
                extra={"rule_id": rule_result.rule_id, "reason": rule_result.deny_reason},
            )
            raise PermissionError(
                f"Credential access denied: {rule_result.deny_reason}"
            )

        # Fetch credential via service (with audit)
        service = CredentialService(vault=vault, audit_enabled=True)
        cred_data = await service.get_credential(
            tenant_id=tenant_id,
            credential_id=credential_id,
            accessor_id=accessor_id,
            accessor_type=accessor_type,
        )

        if cred_data is None:
            raise ValueError(f"Credential not found: {credential_ref}")

        # Extract the actual secret value
        secret_data = cred_data.secret_data
        return secret_data.get("api_key") or next(iter(secret_data.values()), "")

    def _resolve_env_credential(self, credential_ref: str) -> str:
        """Resolve an environment variable credential reference.

        DEVELOPMENT ONLY - not for production use.

        Args:
            credential_ref: env://<var_name> reference

        Returns:
            Value from environment variable

        Raises:
            ValueError: If environment variable not set
        """
        var_name = credential_ref[len("env://") :]

        # Security: Only allow specific prefixes
        allowed_prefixes = ("CUS_CRED_", "LLM_API_KEY_", "DEV_")
        if not any(var_name.startswith(p) for p in allowed_prefixes):
            raise ValueError(
                f"Environment credential {var_name} must start with one of: "
                f"{allowed_prefixes}"
            )

        value = os.environ.get(var_name)
        if not value:
            raise ValueError(f"Environment variable {var_name} not set")

        logger.warning(
            f"Using environment credential {var_name} - NOT FOR PRODUCTION",
            extra={"var_name": var_name},
        )

        return value

    # =========================================================================
    # ROTATION SUPPORT
    # =========================================================================

    def rotate_credential(
        self,
        tenant_id: str,
        old_credential_ref: str,
        new_plaintext: str,
        context: Optional[Dict[str, str]] = None,
    ) -> Tuple[str, bool]:
        """Rotate a credential (encrypt new, verify old is different).

        Args:
            tenant_id: Owning tenant
            old_credential_ref: Current credential reference
            new_plaintext: New credential value
            context: Optional encryption context

        Returns:
            Tuple of (new_credential_ref, old_was_valid)
        """
        # Encrypt new credential
        new_ref = self.encrypt_credential(tenant_id, new_plaintext, context)

        # Try to validate old was decryptable
        old_valid = False
        try:
            old_value = self.resolve_credential(tenant_id, old_credential_ref, context)
            old_valid = True

            # Warn if credentials are the same
            if old_value == new_plaintext:
                logger.warning(
                    f"Credential rotation for tenant {tenant_id[:8]}... "
                    "- new credential same as old"
                )
        except Exception:
            logger.warning(
                f"Old credential for tenant {tenant_id[:8]}... was not decryptable"
            )

        logger.info(
            f"Rotated credential for tenant {tenant_id[:8]}...",
            extra={"tenant_id": tenant_id, "old_valid": old_valid},
        )

        return new_ref, old_valid

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def validate_credential_format(self, credential_ref: str) -> Tuple[bool, str]:
        """Validate credential reference format without decrypting.

        Args:
            credential_ref: Credential reference to validate

        Returns:
            Tuple of (is_valid, error_message or "")
        """
        if not credential_ref:
            return False, "Credential reference cannot be empty"

        # Check for plaintext API keys (common patterns)
        plaintext_patterns = [
            ("sk-", "OpenAI API key"),
            ("sk-ant-", "Anthropic API key"),
            ("AIza", "Google API key"),
            ("xai-", "X.AI API key"),
        ]

        for pattern, provider in plaintext_patterns:
            if credential_ref.startswith(pattern):
                return False, f"Raw {provider} detected. Use encrypted:// reference."

        # Validate known prefixes
        valid_prefixes = ("encrypted://", "vault://", "env://")
        if not any(credential_ref.startswith(p) for p in valid_prefixes):
            return False, f"Unknown credential format. Must use: {valid_prefixes}"

        # Format-specific validation
        if credential_ref.startswith("encrypted://"):
            encoded = credential_ref[len("encrypted://") :]
            try:
                blob = base64.urlsafe_b64decode(encoded)
                if len(blob) < self.NONCE_LENGTH + self.TAG_LENGTH:
                    return False, "Encrypted credential blob too short"
            except Exception:
                return False, "Invalid base64 encoding in encrypted credential"

        elif credential_ref.startswith("vault://"):
            path = credential_ref[len("vault://") :]
            if not path or "/" not in path:
                return False, "Vault path must include secret engine and path"

        elif credential_ref.startswith("env://"):
            var_name = credential_ref[len("env://") :]
            if not var_name:
                return False, "Environment variable name cannot be empty"

        return True, ""

    # =========================================================================
    # UTILITY
    # =========================================================================

    @staticmethod
    def generate_master_key() -> str:
        """Generate a new master encryption key.

        Returns:
            Base64-encoded 32-byte key suitable for CREDENTIAL_MASTER_KEY env var
        """
        key = secrets.token_bytes(32)
        return base64.b64encode(key).decode("ascii")

    def mask_credential(self, credential_ref: str) -> str:
        """Mask a credential reference for logging/display.

        Args:
            credential_ref: Full credential reference

        Returns:
            Masked version safe for logs
        """
        if credential_ref.startswith("encrypted://"):
            # Show first 8 chars of blob
            encoded = credential_ref[len("encrypted://") :]
            return f"encrypted://{encoded[:8]}...{encoded[-4:]}"

        elif credential_ref.startswith("vault://"):
            return credential_ref  # Vault paths are safe to log

        elif credential_ref.startswith("env://"):
            return credential_ref  # Var names are safe to log

        else:
            # Unknown format - mask aggressively
            return f"{credential_ref[:4]}...{credential_ref[-2:]}"
