# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: (via CredentialVault)
#   Writes: (via CredentialVault)
# Role: High-level credential service with validation and auditing
# Product: system-wide
# Callers: ConnectorRegistry, LifecycleHandlers, API routes
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, GAP-171 (Credential Vault Integration)

"""
Credential Service (GAP-171)

High-level service for credential management with:
- Input validation
- Audit logging
- Expiration checking
- Rotation scheduling
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..drivers.vault import (
    CredentialData,
    CredentialMetadata,
    CredentialType,
    CredentialVault,
)

logger = logging.getLogger(__name__)


@dataclass
class CredentialAccessRecord:
    """Record of credential access for auditing."""

    credential_id: str
    tenant_id: str
    accessor_id: str
    accessor_type: str  # human, machine, system
    action: str  # get, store, update, delete, rotate
    success: bool
    accessed_at: datetime
    error_message: Optional[str] = None


class CredentialService:
    """
    High-level credential service.

    Features:
    - Credential CRUD with validation
    - Expiration checking
    - Access auditing
    - Rotation support
    """

    def __init__(
        self,
        vault: CredentialVault,
        audit_enabled: bool = True,
    ):
        self._vault = vault
        self._audit_enabled = audit_enabled
        self._access_log: List[CredentialAccessRecord] = []

    async def store_credential(
        self,
        tenant_id: str,
        name: str,
        credential_type: CredentialType,
        secret_data: Dict[str, str],
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None,
        is_rotatable: bool = False,
        rotation_interval_days: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        accessor_id: Optional[str] = None,
        accessor_type: str = "system",
    ) -> str:
        """
        Store a credential with validation.

        Args:
            tenant_id: Tenant identifier
            name: Human-readable name
            credential_type: Type of credential
            secret_data: Secret key-value pairs
            description: Optional description
            tags: Optional tags
            expires_at: Optional expiration
            is_rotatable: Whether auto-rotation is enabled
            rotation_interval_days: Days between rotations
            metadata: Additional metadata
            accessor_id: Who is storing this credential
            accessor_type: Type of accessor

        Returns:
            credential_id

        Raises:
            ValueError: If validation fails
        """
        # Validate inputs
        self._validate_tenant_id(tenant_id)
        self._validate_name(name)
        self._validate_secret_data(credential_type, secret_data)

        try:
            credential_id = await self._vault.store_credential(
                tenant_id=tenant_id,
                name=name,
                credential_type=credential_type,
                secret_data=secret_data,
                description=description,
                tags=tags,
                expires_at=expires_at,
                is_rotatable=is_rotatable,
                rotation_interval_days=rotation_interval_days,
                metadata=metadata,
            )

            self._audit(
                credential_id=credential_id,
                tenant_id=tenant_id,
                accessor_id=accessor_id or "system",
                accessor_type=accessor_type,
                action="store",
                success=True,
            )

            logger.info(f"Stored credential {credential_id} for tenant {tenant_id}")
            return credential_id

        except Exception as e:
            self._audit(
                credential_id="unknown",
                tenant_id=tenant_id,
                accessor_id=accessor_id or "system",
                accessor_type=accessor_type,
                action="store",
                success=False,
                error_message=str(e),
            )
            raise

    async def get_credential(
        self,
        tenant_id: str,
        credential_id: str,
        accessor_id: Optional[str] = None,
        accessor_type: str = "system",
    ) -> Optional[CredentialData]:
        """
        Get a credential with expiration checking.

        Args:
            tenant_id: Tenant identifier
            credential_id: Credential identifier
            accessor_id: Who is accessing
            accessor_type: Type of accessor

        Returns:
            CredentialData or None if not found or expired
        """
        try:
            cred = await self._vault.get_credential(tenant_id, credential_id)

            if cred is None:
                self._audit(
                    credential_id=credential_id,
                    tenant_id=tenant_id,
                    accessor_id=accessor_id or "system",
                    accessor_type=accessor_type,
                    action="get",
                    success=False,
                    error_message="not_found",
                )
                return None

            # Check expiration
            if cred.metadata.expires_at and cred.metadata.expires_at < datetime.now(timezone.utc):
                logger.warning(f"Credential {credential_id} has expired")
                self._audit(
                    credential_id=credential_id,
                    tenant_id=tenant_id,
                    accessor_id=accessor_id or "system",
                    accessor_type=accessor_type,
                    action="get",
                    success=False,
                    error_message="expired",
                )
                return None

            self._audit(
                credential_id=credential_id,
                tenant_id=tenant_id,
                accessor_id=accessor_id or "system",
                accessor_type=accessor_type,
                action="get",
                success=True,
            )

            return cred

        except Exception as e:
            self._audit(
                credential_id=credential_id,
                tenant_id=tenant_id,
                accessor_id=accessor_id or "system",
                accessor_type=accessor_type,
                action="get",
                success=False,
                error_message=str(e),
            )
            raise

    async def get_secret_value(
        self,
        tenant_id: str,
        credential_id: str,
        key: str = "api_key",
        accessor_id: Optional[str] = None,
        accessor_type: str = "system",
    ) -> Optional[str]:
        """
        Get a specific secret value from a credential.

        Convenience method for common use case.

        Args:
            tenant_id: Tenant identifier
            credential_id: Credential identifier
            key: Secret key to retrieve (default: api_key)
            accessor_id: Who is accessing
            accessor_type: Type of accessor

        Returns:
            Secret value or None
        """
        cred = await self.get_credential(
            tenant_id=tenant_id,
            credential_id=credential_id,
            accessor_id=accessor_id,
            accessor_type=accessor_type,
        )
        if cred:
            return cred.secret_data.get(key)
        return None

    async def list_credentials(
        self,
        tenant_id: str,
        credential_type: Optional[CredentialType] = None,
        tags: Optional[List[str]] = None,
        include_expired: bool = False,
    ) -> List[CredentialMetadata]:
        """
        List credentials for a tenant.

        Args:
            tenant_id: Tenant identifier
            credential_type: Optional filter by type
            tags: Optional filter by tags
            include_expired: Whether to include expired credentials

        Returns:
            List of CredentialMetadata
        """
        creds = await self._vault.list_credentials(
            tenant_id=tenant_id,
            credential_type=credential_type,
            tags=tags,
        )

        if not include_expired:
            now = datetime.now(timezone.utc)
            creds = [c for c in creds if c.expires_at is None or c.expires_at > now]

        return creds

    async def update_credential(
        self,
        tenant_id: str,
        credential_id: str,
        secret_data: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        accessor_id: Optional[str] = None,
        accessor_type: str = "system",
    ) -> bool:
        """Update a credential."""
        try:
            result = await self._vault.update_credential(
                tenant_id=tenant_id,
                credential_id=credential_id,
                secret_data=secret_data,
                description=description,
                tags=tags,
                expires_at=expires_at,
                metadata=metadata,
            )

            self._audit(
                credential_id=credential_id,
                tenant_id=tenant_id,
                accessor_id=accessor_id or "system",
                accessor_type=accessor_type,
                action="update",
                success=result,
                error_message=None if result else "not_found",
            )

            return result

        except Exception as e:
            self._audit(
                credential_id=credential_id,
                tenant_id=tenant_id,
                accessor_id=accessor_id or "system",
                accessor_type=accessor_type,
                action="update",
                success=False,
                error_message=str(e),
            )
            raise

    async def delete_credential(
        self,
        tenant_id: str,
        credential_id: str,
        accessor_id: Optional[str] = None,
        accessor_type: str = "system",
    ) -> bool:
        """Delete a credential."""
        try:
            result = await self._vault.delete_credential(tenant_id, credential_id)

            self._audit(
                credential_id=credential_id,
                tenant_id=tenant_id,
                accessor_id=accessor_id or "system",
                accessor_type=accessor_type,
                action="delete",
                success=result,
                error_message=None if result else "not_found",
            )

            return result

        except Exception as e:
            self._audit(
                credential_id=credential_id,
                tenant_id=tenant_id,
                accessor_id=accessor_id or "system",
                accessor_type=accessor_type,
                action="delete",
                success=False,
                error_message=str(e),
            )
            raise

    async def rotate_credential(
        self,
        tenant_id: str,
        credential_id: str,
        new_secret_data: Dict[str, str],
        accessor_id: Optional[str] = None,
        accessor_type: str = "system",
    ) -> bool:
        """Rotate a credential's secrets."""
        try:
            result = await self._vault.rotate_credential(
                tenant_id=tenant_id,
                credential_id=credential_id,
                new_secret_data=new_secret_data,
            )

            self._audit(
                credential_id=credential_id,
                tenant_id=tenant_id,
                accessor_id=accessor_id or "system",
                accessor_type=accessor_type,
                action="rotate",
                success=result,
                error_message=None if result else "not_found",
            )

            return result

        except Exception as e:
            self._audit(
                credential_id=credential_id,
                tenant_id=tenant_id,
                accessor_id=accessor_id or "system",
                accessor_type=accessor_type,
                action="rotate",
                success=False,
                error_message=str(e),
            )
            raise

    async def get_expiring_credentials(
        self,
        tenant_id: str,
        days_until_expiry: int = 7,
    ) -> List[CredentialMetadata]:
        """
        Get credentials expiring within specified days.

        Useful for rotation scheduling.
        """
        from datetime import timedelta

        all_creds = await self._vault.list_credentials(tenant_id)
        now = datetime.now(timezone.utc)
        threshold = now + timedelta(days=days_until_expiry)

        return [
            c for c in all_creds
            if c.expires_at is not None and c.expires_at <= threshold
        ]

    async def get_rotatable_credentials(
        self,
        tenant_id: str,
    ) -> List[CredentialMetadata]:
        """Get credentials that need rotation based on their schedule."""
        from datetime import timedelta

        all_creds = await self._vault.list_credentials(tenant_id)
        now = datetime.now(timezone.utc)
        needing_rotation = []

        for cred in all_creds:
            if not cred.is_rotatable or not cred.rotation_interval_days:
                continue

            # Check if rotation is due
            rotation_due = cred.updated_at + timedelta(days=cred.rotation_interval_days)
            if rotation_due <= now:
                needing_rotation.append(cred)

        return needing_rotation

    def get_access_log(
        self,
        tenant_id: Optional[str] = None,
        credential_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[CredentialAccessRecord]:
        """Get credential access log (for auditing)."""
        records = self._access_log

        if tenant_id:
            records = [r for r in records if r.tenant_id == tenant_id]
        if credential_id:
            records = [r for r in records if r.credential_id == credential_id]

        return records[-limit:]

    def _audit(
        self,
        credential_id: str,
        tenant_id: str,
        accessor_id: str,
        accessor_type: str,
        action: str,
        success: bool,
        error_message: Optional[str] = None,
    ) -> None:
        """Record an access for auditing."""
        if not self._audit_enabled:
            return

        record = CredentialAccessRecord(
            credential_id=credential_id,
            tenant_id=tenant_id,
            accessor_id=accessor_id,
            accessor_type=accessor_type,
            action=action,
            success=success,
            accessed_at=datetime.now(timezone.utc),
            error_message=error_message,
        )
        self._access_log.append(record)

        # Keep log bounded
        if len(self._access_log) > 10000:
            self._access_log = self._access_log[-5000:]

    def _validate_tenant_id(self, tenant_id: str) -> None:
        """Validate tenant ID."""
        if not tenant_id or not tenant_id.strip():
            raise ValueError("tenant_id is required")
        if len(tenant_id) > 64:
            raise ValueError("tenant_id too long (max 64 chars)")

    def _validate_name(self, name: str) -> None:
        """Validate credential name."""
        if not name or not name.strip():
            raise ValueError("name is required")
        if len(name) > 128:
            raise ValueError("name too long (max 128 chars)")

    def _validate_secret_data(
        self,
        credential_type: CredentialType,
        secret_data: Dict[str, str],
    ) -> None:
        """Validate secret data based on credential type."""
        if not secret_data:
            raise ValueError("secret_data is required")

        # Type-specific validation
        if credential_type == CredentialType.API_KEY:
            if "api_key" not in secret_data:
                raise ValueError("api_key field required for API_KEY type")

        elif credential_type == CredentialType.OAUTH:
            required = {"client_id", "client_secret"}
            if not required.issubset(secret_data.keys()):
                raise ValueError(f"OAuth requires: {required}")

        elif credential_type == CredentialType.DATABASE:
            required = {"host", "username", "password"}
            if not required.issubset(secret_data.keys()):
                raise ValueError(f"Database requires: {required}")

        elif credential_type == CredentialType.BASIC_AUTH:
            required = {"username", "password"}
            if not required.issubset(secret_data.keys()):
                raise ValueError(f"Basic auth requires: {required}")

        elif credential_type == CredentialType.BEARER_TOKEN:
            if "token" not in secret_data:
                raise ValueError("token field required for BEARER_TOKEN type")
