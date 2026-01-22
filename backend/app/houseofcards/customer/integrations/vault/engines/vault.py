# Layer: L4 — Domain Engines
# AUDIENCE: INTERNAL
# PHASE: W2
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Credential vault abstraction with multiple provider support
# Callers: CredentialService
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: GAP-171 (Credential Vault Integration), HOC_integrations_analysis_v1.md
#
# GOVERNANCE: TRANSITIONAL FILE — INV-INT-006
# This file is AUDIENCE: INTERNAL but currently lives under customer/.
# It will be moved to internal/platform/vault/engines/ in Phase 5.
#
# IMPORT GUARD: New customer-facing code MUST NOT import this file directly.
# Access only through CredentialService or CusCredentialService.
# Phase 5 will wire all imports systematically.

"""
Credential Vault Abstraction (GAP-171)

Supports multiple vault providers:
- HashiCorp Vault (production)
- AWS Secrets Manager (production)
- Environment variables (development only)
"""

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class VaultProvider(str, Enum):
    """Supported vault providers."""

    HASHICORP = "hashicorp"
    AWS_SECRETS = "aws_secrets"
    ENV = "env"  # Development only


class CredentialType(str, Enum):
    """Types of credentials."""

    API_KEY = "api_key"
    OAUTH = "oauth"
    DATABASE = "database"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"
    SSH_KEY = "ssh_key"
    CERTIFICATE = "certificate"
    CUSTOM = "custom"


@dataclass
class CredentialMetadata:
    """Metadata about a stored credential (without secret values)."""

    credential_id: str
    tenant_id: str
    name: str
    credential_type: CredentialType
    description: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None
    access_count: int = 0
    is_rotatable: bool = False
    rotation_interval_days: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CredentialData:
    """Full credential including secret values."""

    metadata: CredentialMetadata
    secret_data: Dict[str, str]

    @property
    def credential_id(self) -> str:
        return self.metadata.credential_id

    @property
    def tenant_id(self) -> str:
        return self.metadata.tenant_id


class CredentialVault(ABC):
    """Abstract credential vault interface."""

    @abstractmethod
    async def store_credential(
        self,
        tenant_id: str,
        name: str,
        credential_type: CredentialType,
        secret_data: Dict[str, str],
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        expires_at: Optional[datetime] = None,
        is_rotatable: bool = False,
        rotation_interval_days: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Store a credential and return its ID.

        Args:
            tenant_id: Tenant identifier
            name: Human-readable name
            credential_type: Type of credential
            secret_data: Secret key-value pairs
            description: Optional description
            tags: Optional tags for organization
            expires_at: Optional expiration time
            is_rotatable: Whether credential can be auto-rotated
            rotation_interval_days: Days between rotations
            metadata: Additional metadata

        Returns:
            credential_id: Unique identifier for the credential
        """
        pass

    @abstractmethod
    async def get_credential(
        self,
        tenant_id: str,
        credential_id: str,
    ) -> Optional[CredentialData]:
        """
        Get a credential by ID.

        Args:
            tenant_id: Tenant identifier
            credential_id: Credential identifier

        Returns:
            CredentialData or None if not found
        """
        pass

    @abstractmethod
    async def get_metadata(
        self,
        tenant_id: str,
        credential_id: str,
    ) -> Optional[CredentialMetadata]:
        """
        Get credential metadata without secret values.

        Args:
            tenant_id: Tenant identifier
            credential_id: Credential identifier

        Returns:
            CredentialMetadata or None if not found
        """
        pass

    @abstractmethod
    async def list_credentials(
        self,
        tenant_id: str,
        credential_type: Optional[CredentialType] = None,
        tags: Optional[list[str]] = None,
    ) -> list[CredentialMetadata]:
        """
        List credentials for a tenant (metadata only).

        Args:
            tenant_id: Tenant identifier
            credential_type: Optional filter by type
            tags: Optional filter by tags

        Returns:
            List of CredentialMetadata
        """
        pass

    @abstractmethod
    async def update_credential(
        self,
        tenant_id: str,
        credential_id: str,
        secret_data: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update a credential.

        Args:
            tenant_id: Tenant identifier
            credential_id: Credential identifier
            secret_data: New secret values (if updating)
            description: New description
            tags: New tags
            expires_at: New expiration
            metadata: New metadata

        Returns:
            True if updated, False if not found
        """
        pass

    @abstractmethod
    async def delete_credential(
        self,
        tenant_id: str,
        credential_id: str,
    ) -> bool:
        """
        Delete a credential.

        Args:
            tenant_id: Tenant identifier
            credential_id: Credential identifier

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def rotate_credential(
        self,
        tenant_id: str,
        credential_id: str,
        new_secret_data: Dict[str, str],
    ) -> bool:
        """
        Rotate a credential's secret values.

        Args:
            tenant_id: Tenant identifier
            credential_id: Credential identifier
            new_secret_data: New secret values

        Returns:
            True if rotated, False if not found
        """
        pass


class HashiCorpVault(CredentialVault):
    """HashiCorp Vault implementation."""

    def __init__(
        self,
        vault_url: str,
        token: str,
        mount_path: str = "agenticverz",
    ):
        self._vault_url = vault_url
        self._token = token
        self._mount_path = mount_path
        self._metadata_cache: Dict[str, CredentialMetadata] = {}

    async def store_credential(
        self,
        tenant_id: str,
        name: str,
        credential_type: CredentialType,
        secret_data: Dict[str, str],
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        expires_at: Optional[datetime] = None,
        is_rotatable: bool = False,
        rotation_interval_days: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store credential in Vault."""
        import uuid
        import httpx

        credential_id = str(uuid.uuid4())
        path = f"{self._mount_path}/data/{tenant_id}/{credential_id}"

        now = datetime.now(timezone.utc)
        meta = CredentialMetadata(
            credential_id=credential_id,
            tenant_id=tenant_id,
            name=name,
            credential_type=credential_type,
            description=description,
            tags=tags or [],
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
            is_rotatable=is_rotatable,
            rotation_interval_days=rotation_interval_days,
            metadata=metadata or {},
        )

        # Store in Vault
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._vault_url}/v1/{path}",
                headers={"X-Vault-Token": self._token},
                json={
                    "data": {
                        "_metadata": {
                            "name": meta.name,
                            "type": meta.credential_type.value,
                            "description": meta.description,
                            "tags": meta.tags,
                            "created_at": meta.created_at.isoformat(),
                            "updated_at": meta.updated_at.isoformat(),
                            "expires_at": meta.expires_at.isoformat() if meta.expires_at else None,
                            "is_rotatable": meta.is_rotatable,
                            "rotation_interval_days": meta.rotation_interval_days,
                            "custom_metadata": meta.metadata,
                        },
                        **secret_data,
                    }
                },
                timeout=10.0,
            )
            response.raise_for_status()

        self._metadata_cache[f"{tenant_id}:{credential_id}"] = meta
        logger.info(f"Stored credential {credential_id} for tenant {tenant_id}")
        return credential_id

    async def get_credential(
        self,
        tenant_id: str,
        credential_id: str,
    ) -> Optional[CredentialData]:
        """Get credential from Vault."""
        import httpx

        path = f"{self._mount_path}/data/{tenant_id}/{credential_id}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self._vault_url}/v1/{path}",
                    headers={"X-Vault-Token": self._token},
                    timeout=10.0,
                )

                if response.status_code == 404:
                    return None

                response.raise_for_status()
                data = response.json().get("data", {}).get("data", {})

                # Extract metadata and secrets
                meta_data = data.pop("_metadata", {})
                secret_data = data

                meta = CredentialMetadata(
                    credential_id=credential_id,
                    tenant_id=tenant_id,
                    name=meta_data.get("name", ""),
                    credential_type=CredentialType(meta_data.get("type", "custom")),
                    description=meta_data.get("description"),
                    tags=meta_data.get("tags", []),
                    created_at=datetime.fromisoformat(meta_data["created_at"]) if meta_data.get("created_at") else datetime.now(timezone.utc),
                    updated_at=datetime.fromisoformat(meta_data["updated_at"]) if meta_data.get("updated_at") else datetime.now(timezone.utc),
                    expires_at=datetime.fromisoformat(meta_data["expires_at"]) if meta_data.get("expires_at") else None,
                    is_rotatable=meta_data.get("is_rotatable", False),
                    rotation_interval_days=meta_data.get("rotation_interval_days"),
                    metadata=meta_data.get("custom_metadata", {}),
                )

                # Update access tracking
                meta.last_accessed_at = datetime.now(timezone.utc)
                meta.access_count += 1

                return CredentialData(metadata=meta, secret_data=secret_data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def get_metadata(
        self,
        tenant_id: str,
        credential_id: str,
    ) -> Optional[CredentialMetadata]:
        """Get credential metadata without secrets."""
        cache_key = f"{tenant_id}:{credential_id}"
        if cache_key in self._metadata_cache:
            return self._metadata_cache[cache_key]

        cred = await self.get_credential(tenant_id, credential_id)
        if cred:
            self._metadata_cache[cache_key] = cred.metadata
            return cred.metadata
        return None

    async def list_credentials(
        self,
        tenant_id: str,
        credential_type: Optional[CredentialType] = None,
        tags: Optional[list[str]] = None,
    ) -> list[CredentialMetadata]:
        """List credentials for tenant."""
        import httpx

        path = f"{self._mount_path}/metadata/{tenant_id}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    "LIST",
                    f"{self._vault_url}/v1/{path}",
                    headers={"X-Vault-Token": self._token},
                    timeout=10.0,
                )

                if response.status_code == 404:
                    return []

                response.raise_for_status()
                keys = response.json().get("data", {}).get("keys", [])

                # Fetch metadata for each credential
                results = []
                for cred_id in keys:
                    meta = await self.get_metadata(tenant_id, cred_id)
                    if meta:
                        # Apply filters
                        if credential_type and meta.credential_type != credential_type:
                            continue
                        if tags and not all(t in meta.tags for t in tags):
                            continue
                        results.append(meta)

                return results

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return []
            raise

    async def update_credential(
        self,
        tenant_id: str,
        credential_id: str,
        secret_data: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update a credential."""
        existing = await self.get_credential(tenant_id, credential_id)
        if not existing:
            return False

        # Merge updates
        new_secret = secret_data if secret_data is not None else existing.secret_data
        new_meta = existing.metadata
        new_meta.updated_at = datetime.now(timezone.utc)

        if description is not None:
            new_meta.description = description
        if tags is not None:
            new_meta.tags = tags
        if expires_at is not None:
            new_meta.expires_at = expires_at
        if metadata is not None:
            new_meta.metadata = metadata

        # Re-store
        import httpx
        path = f"{self._mount_path}/data/{tenant_id}/{credential_id}"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._vault_url}/v1/{path}",
                headers={"X-Vault-Token": self._token},
                json={
                    "data": {
                        "_metadata": {
                            "name": new_meta.name,
                            "type": new_meta.credential_type.value,
                            "description": new_meta.description,
                            "tags": new_meta.tags,
                            "created_at": new_meta.created_at.isoformat(),
                            "updated_at": new_meta.updated_at.isoformat(),
                            "expires_at": new_meta.expires_at.isoformat() if new_meta.expires_at else None,
                            "is_rotatable": new_meta.is_rotatable,
                            "rotation_interval_days": new_meta.rotation_interval_days,
                            "custom_metadata": new_meta.metadata,
                        },
                        **new_secret,
                    }
                },
                timeout=10.0,
            )
            response.raise_for_status()

        self._metadata_cache[f"{tenant_id}:{credential_id}"] = new_meta
        return True

    async def delete_credential(
        self,
        tenant_id: str,
        credential_id: str,
    ) -> bool:
        """Delete a credential."""
        import httpx

        path = f"{self._mount_path}/metadata/{tenant_id}/{credential_id}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self._vault_url}/v1/{path}",
                    headers={"X-Vault-Token": self._token},
                    timeout=10.0,
                )

                if response.status_code == 204 or response.status_code == 200:
                    self._metadata_cache.pop(f"{tenant_id}:{credential_id}", None)
                    return True
                return False

        except httpx.HTTPStatusError:
            return False

    async def rotate_credential(
        self,
        tenant_id: str,
        credential_id: str,
        new_secret_data: Dict[str, str],
    ) -> bool:
        """Rotate credential secrets."""
        return await self.update_credential(
            tenant_id=tenant_id,
            credential_id=credential_id,
            secret_data=new_secret_data,
        )


class EnvCredentialVault(CredentialVault):
    """
    Environment variable credential vault (development only).

    Credentials are stored in memory with secrets read from environment.
    """

    def __init__(self):
        self._credentials: Dict[str, CredentialMetadata] = {}
        self._secrets: Dict[str, Dict[str, str]] = {}

    async def store_credential(
        self,
        tenant_id: str,
        name: str,
        credential_type: CredentialType,
        secret_data: Dict[str, str],
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        expires_at: Optional[datetime] = None,
        is_rotatable: bool = False,
        rotation_interval_days: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store credential in memory."""
        import uuid

        credential_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        meta = CredentialMetadata(
            credential_id=credential_id,
            tenant_id=tenant_id,
            name=name,
            credential_type=credential_type,
            description=description,
            tags=tags or [],
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
            is_rotatable=is_rotatable,
            rotation_interval_days=rotation_interval_days,
            metadata=metadata or {},
        )

        key = f"{tenant_id}:{credential_id}"
        self._credentials[key] = meta
        self._secrets[key] = secret_data

        logger.info(f"[EnvVault] Stored credential {credential_id} for tenant {tenant_id}")
        return credential_id

    async def get_credential(
        self,
        tenant_id: str,
        credential_id: str,
    ) -> Optional[CredentialData]:
        """Get credential from memory or environment."""
        key = f"{tenant_id}:{credential_id}"

        # Check memory first
        if key in self._credentials:
            meta = self._credentials[key]
            secret = self._secrets.get(key, {})
            meta.last_accessed_at = datetime.now(timezone.utc)
            meta.access_count += 1
            return CredentialData(metadata=meta, secret_data=secret)

        # Check environment variable fallback
        env_key = f"AOS_CRED_{credential_id.upper().replace('-', '_')}"
        env_value = os.getenv(env_key)
        if env_value:
            meta = CredentialMetadata(
                credential_id=credential_id,
                tenant_id=tenant_id,
                name=f"env:{credential_id}",
                credential_type=CredentialType.API_KEY,
            )
            return CredentialData(metadata=meta, secret_data={"api_key": env_value})

        return None

    async def get_metadata(
        self,
        tenant_id: str,
        credential_id: str,
    ) -> Optional[CredentialMetadata]:
        """Get credential metadata."""
        key = f"{tenant_id}:{credential_id}"
        return self._credentials.get(key)

    async def list_credentials(
        self,
        tenant_id: str,
        credential_type: Optional[CredentialType] = None,
        tags: Optional[list[str]] = None,
    ) -> list[CredentialMetadata]:
        """List credentials for tenant."""
        results = []
        for key, meta in self._credentials.items():
            if not key.startswith(f"{tenant_id}:"):
                continue
            if credential_type and meta.credential_type != credential_type:
                continue
            if tags and not all(t in meta.tags for t in tags):
                continue
            results.append(meta)
        return results

    async def update_credential(
        self,
        tenant_id: str,
        credential_id: str,
        secret_data: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update a credential."""
        key = f"{tenant_id}:{credential_id}"
        if key not in self._credentials:
            return False

        meta = self._credentials[key]
        meta.updated_at = datetime.now(timezone.utc)

        if description is not None:
            meta.description = description
        if tags is not None:
            meta.tags = tags
        if expires_at is not None:
            meta.expires_at = expires_at
        if metadata is not None:
            meta.metadata = metadata
        if secret_data is not None:
            self._secrets[key] = secret_data

        return True

    async def delete_credential(
        self,
        tenant_id: str,
        credential_id: str,
    ) -> bool:
        """Delete a credential."""
        key = f"{tenant_id}:{credential_id}"
        if key in self._credentials:
            del self._credentials[key]
            self._secrets.pop(key, None)
            return True
        return False

    async def rotate_credential(
        self,
        tenant_id: str,
        credential_id: str,
        new_secret_data: Dict[str, str],
    ) -> bool:
        """Rotate credential secrets."""
        return await self.update_credential(
            tenant_id=tenant_id,
            credential_id=credential_id,
            secret_data=new_secret_data,
        )


def create_credential_vault() -> CredentialVault:
    """Factory function to create appropriate vault based on configuration."""
    provider = os.getenv("CREDENTIAL_VAULT_PROVIDER", "env")

    if provider == "hashicorp":
        vault_url = os.getenv("VAULT_ADDR", "http://localhost:8200")
        vault_token = os.getenv("VAULT_TOKEN")
        if not vault_token:
            logger.warning("VAULT_TOKEN not set, falling back to env vault")
            return EnvCredentialVault()
        return HashiCorpVault(vault_url=vault_url, token=vault_token)

    elif provider == "aws_secrets":
        # TODO: Implement AWS Secrets Manager
        logger.warning("AWS Secrets Manager not yet implemented, falling back to env vault")
        return EnvCredentialVault()

    else:
        # Default: environment variable vault (development)
        logger.info("Using environment variable credential vault")
        return EnvCredentialVault()
