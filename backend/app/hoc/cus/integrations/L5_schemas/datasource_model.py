# Layer: L5 — Domain Engines
# AUDIENCE: INTERNAL
# Product: system-wide
# Role: Customer data source models and registry for database/file/API connections
# Reference: GAP-055 (CustomerDataSource model)
"""
CustomerDataSource - Customer data source models and registry.

Provides data source abstraction for:
- Database connections
- File storage
- API endpoints
- Vector stores
- Custom connectors
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
import uuid


class DataSourceType(str, Enum):
    """Types of data sources."""

    DATABASE = "database"       # Relational databases
    DOCUMENT = "document"       # Document stores (MongoDB, etc.)
    FILE = "file"               # File storage (S3, GCS, local)
    VECTOR = "vector"           # Vector databases
    API = "api"                 # REST/GraphQL APIs
    STREAM = "stream"           # Streaming sources (Kafka, etc.)
    CUSTOM = "custom"           # Custom connectors


class DataSourceStatus(str, Enum):
    """Status of a data source."""

    PENDING = "pending"         # Not yet configured
    CONFIGURING = "configuring" # Configuration in progress
    ACTIVE = "active"           # Ready for use
    INACTIVE = "inactive"       # Temporarily disabled
    ERROR = "error"             # Configuration or connection error
    DEPRECATED = "deprecated"   # Marked for removal


@dataclass
class DataSourceConfig:
    """Configuration for a data source."""

    # Connection settings
    connection_string: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None

    # Authentication
    auth_type: Optional[str] = None  # none, basic, api_key, oauth, iam
    api_key: Optional[str] = None
    oauth_config: Optional[dict[str, Any]] = None

    # Connection pool
    pool_size: int = 5
    pool_timeout: int = 30
    max_retries: int = 3

    # SSL/TLS
    ssl_enabled: bool = False
    ssl_verify: bool = True
    ssl_cert_path: Optional[str] = None

    # Additional options
    options: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, include_secrets: bool = False) -> dict[str, Any]:
        """Convert to dictionary, optionally masking secrets."""
        result = {
            "connection_string": (
                "***" if self.connection_string and not include_secrets
                else self.connection_string
            ),
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": "***" if self.password and not include_secrets else self.password,
            "database": self.database,
            "auth_type": self.auth_type,
            "api_key": "***" if self.api_key and not include_secrets else self.api_key,
            "oauth_config": (
                {k: "***" for k in self.oauth_config} if self.oauth_config and not include_secrets
                else self.oauth_config
            ),
            "pool_size": self.pool_size,
            "pool_timeout": self.pool_timeout,
            "max_retries": self.max_retries,
            "ssl_enabled": self.ssl_enabled,
            "ssl_verify": self.ssl_verify,
            "ssl_cert_path": self.ssl_cert_path,
            "options": self.options,
        }
        return result

    def get_connection_url(self) -> Optional[str]:
        """Build connection URL from components."""
        if self.connection_string:
            return self.connection_string

        if not self.host:
            return None

        # Build URL from components
        auth = ""
        if self.username:
            if self.password:
                auth = f"{self.username}:{self.password}@"
            else:
                auth = f"{self.username}@"

        port_str = f":{self.port}" if self.port else ""
        db_str = f"/{self.database}" if self.database else ""

        return f"{auth}{self.host}{port_str}{db_str}"


@dataclass
class CustomerDataSource:
    """Representation of a customer data source."""

    source_id: str
    tenant_id: str
    name: str
    source_type: DataSourceType

    # Configuration
    config: DataSourceConfig = field(default_factory=DataSourceConfig)

    # Status
    status: DataSourceStatus = DataSourceStatus.PENDING

    # Metadata
    description: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Access control
    access_roles: list[str] = field(default_factory=list)
    owner_id: Optional[str] = None

    # Statistics
    last_connected: Optional[datetime] = None
    last_error: Optional[str] = None
    connection_count: int = 0
    error_count: int = 0

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def record_connection(self, now: Optional[datetime] = None) -> None:
        """Record a successful connection."""
        now = now or datetime.now(timezone.utc)
        self.last_connected = now
        self.connection_count += 1
        self.updated_at = now

    def record_error(self, error: str, now: Optional[datetime] = None) -> None:
        """Record a connection error."""
        now = now or datetime.now(timezone.utc)
        self.last_error = error
        self.error_count += 1
        self.status = DataSourceStatus.ERROR
        self.updated_at = now

    def activate(self, now: Optional[datetime] = None) -> None:
        """Activate the data source."""
        now = now or datetime.now(timezone.utc)
        self.status = DataSourceStatus.ACTIVE
        self.last_error = None
        self.updated_at = now

    def deactivate(self, now: Optional[datetime] = None) -> None:
        """Deactivate the data source."""
        now = now or datetime.now(timezone.utc)
        self.status = DataSourceStatus.INACTIVE
        self.updated_at = now

    def deprecate(self, now: Optional[datetime] = None) -> None:
        """Mark data source as deprecated."""
        now = now or datetime.now(timezone.utc)
        self.status = DataSourceStatus.DEPRECATED
        self.updated_at = now

    def update_config(
        self,
        config: DataSourceConfig,
        now: Optional[datetime] = None,
    ) -> None:
        """Update the data source configuration."""
        now = now or datetime.now(timezone.utc)
        self.config = config
        self.status = DataSourceStatus.CONFIGURING
        self.updated_at = now

    def add_tag(self, tag: str) -> None:
        """Add a tag to the data source."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now(timezone.utc)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the data source."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now(timezone.utc)

    def grant_access(self, role: str) -> None:
        """Grant access to a role."""
        if role not in self.access_roles:
            self.access_roles.append(role)
            self.updated_at = datetime.now(timezone.utc)

    def revoke_access(self, role: str) -> None:
        """Revoke access from a role."""
        if role in self.access_roles:
            self.access_roles.remove(role)
            self.updated_at = datetime.now(timezone.utc)

    def has_access(self, role: str) -> bool:
        """Check if a role has access."""
        return role in self.access_roles or len(self.access_roles) == 0

    def to_dict(self, include_secrets: bool = False) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source_id": self.source_id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "source_type": self.source_type.value,
            "config": self.config.to_dict(include_secrets=include_secrets),
            "status": self.status.value,
            "description": self.description,
            "tags": self.tags,
            "metadata": self.metadata,
            "access_roles": self.access_roles,
            "owner_id": self.owner_id,
            "last_connected": (
                self.last_connected.isoformat() if self.last_connected else None
            ),
            "last_error": self.last_error,
            "connection_count": self.connection_count,
            "error_count": self.error_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class DataSourceError(Exception):
    """Exception for data source errors."""

    def __init__(
        self,
        message: str,
        source_id: Optional[str] = None,
        source_type: Optional[DataSourceType] = None,
    ):
        super().__init__(message)
        self.message = message
        self.source_id = source_id
        self.source_type = source_type

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "error": self.message,
            "source_id": self.source_id,
            "source_type": self.source_type.value if self.source_type else None,
        }


@dataclass
class DataSourceStats:
    """Statistics for data sources."""

    total_sources: int = 0
    active_sources: int = 0
    inactive_sources: int = 0
    error_sources: int = 0
    pending_sources: int = 0

    # By type
    sources_by_type: dict[str, int] = field(default_factory=dict)

    # Totals
    total_connections: int = 0
    total_errors: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_sources": self.total_sources,
            "active_sources": self.active_sources,
            "inactive_sources": self.inactive_sources,
            "error_sources": self.error_sources,
            "pending_sources": self.pending_sources,
            "sources_by_type": self.sources_by_type,
            "total_connections": self.total_connections,
            "total_errors": self.total_errors,
        }


class DataSourceRegistry:
    """
    Registry for managing customer data sources.

    Features:
    - CRUD operations for data sources
    - Status management
    - Tenant isolation
    - Access control
    """

    def __init__(self):
        """Initialize the registry."""
        self._sources: dict[str, CustomerDataSource] = {}
        self._tenant_sources: dict[str, set[str]] = {}

    def register(
        self,
        tenant_id: str,
        name: str,
        source_type: DataSourceType,
        config: Optional[DataSourceConfig] = None,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        owner_id: Optional[str] = None,
        source_id: Optional[str] = None,
    ) -> CustomerDataSource:
        """
        Register a new data source.

        Args:
            tenant_id: Tenant identifier
            name: Human-readable name
            source_type: Type of data source
            config: Optional configuration
            description: Optional description
            tags: Optional tags
            owner_id: Optional owner user ID
            source_id: Optional specific ID

        Returns:
            The registered data source
        """
        source_id = source_id or str(uuid.uuid4())

        source = CustomerDataSource(
            source_id=source_id,
            tenant_id=tenant_id,
            name=name,
            source_type=source_type,
            config=config or DataSourceConfig(),
            description=description,
            tags=tags or [],
            owner_id=owner_id,
        )

        # Store source
        self._sources[source_id] = source

        # Track by tenant
        if tenant_id not in self._tenant_sources:
            self._tenant_sources[tenant_id] = set()
        self._tenant_sources[tenant_id].add(source_id)

        return source

    def get(self, source_id: str) -> Optional[CustomerDataSource]:
        """Get a data source by ID."""
        return self._sources.get(source_id)

    def get_by_name(
        self,
        tenant_id: str,
        name: str,
    ) -> Optional[CustomerDataSource]:
        """Get a data source by name within a tenant."""
        for source in self._sources.values():
            if source.tenant_id == tenant_id and source.name == name:
                return source
        return None

    def list(
        self,
        tenant_id: Optional[str] = None,
        source_type: Optional[DataSourceType] = None,
        status: Optional[DataSourceStatus] = None,
        tag: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CustomerDataSource]:
        """
        List data sources with optional filters.

        Args:
            tenant_id: Filter by tenant
            source_type: Filter by type
            status: Filter by status
            tag: Filter by tag
            limit: Max results
            offset: Skip first N results

        Returns:
            List of matching data sources
        """
        sources = list(self._sources.values())

        if tenant_id:
            sources = [s for s in sources if s.tenant_id == tenant_id]

        if source_type:
            sources = [s for s in sources if s.source_type == source_type]

        if status:
            sources = [s for s in sources if s.status == status]

        if tag:
            sources = [s for s in sources if tag in s.tags]

        # Sort by name
        sources.sort(key=lambda s: s.name)

        return sources[offset:offset + limit]

    def update(
        self,
        source_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[DataSourceConfig] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Optional[CustomerDataSource]:
        """Update a data source."""
        source = self._sources.get(source_id)
        if not source:
            return None

        if name is not None:
            source.name = name
        if description is not None:
            source.description = description
        if config is not None:
            source.update_config(config)
        if metadata is not None:
            source.metadata = metadata

        source.updated_at = datetime.now(timezone.utc)
        return source

    def activate(self, source_id: str) -> Optional[CustomerDataSource]:
        """Activate a data source."""
        source = self._sources.get(source_id)
        if source:
            source.activate()
        return source

    def deactivate(self, source_id: str) -> Optional[CustomerDataSource]:
        """Deactivate a data source."""
        source = self._sources.get(source_id)
        if source:
            source.deactivate()
        return source

    def delete(self, source_id: str) -> bool:
        """Delete a data source."""
        source = self._sources.get(source_id)
        if not source:
            return False

        del self._sources[source_id]

        # Remove from tenant tracking
        if source.tenant_id in self._tenant_sources:
            self._tenant_sources[source.tenant_id].discard(source_id)

        return True

    def get_statistics(
        self,
        tenant_id: Optional[str] = None,
    ) -> DataSourceStats:
        """Get registry statistics."""
        stats = DataSourceStats()

        for source in self._sources.values():
            if tenant_id and source.tenant_id != tenant_id:
                continue

            stats.total_sources += 1
            stats.total_connections += source.connection_count
            stats.total_errors += source.error_count

            # Count by status
            if source.status == DataSourceStatus.ACTIVE:
                stats.active_sources += 1
            elif source.status == DataSourceStatus.INACTIVE:
                stats.inactive_sources += 1
            elif source.status == DataSourceStatus.ERROR:
                stats.error_sources += 1
            elif source.status == DataSourceStatus.PENDING:
                stats.pending_sources += 1

            # Count by type
            type_key = source.source_type.value
            stats.sources_by_type[type_key] = (
                stats.sources_by_type.get(type_key, 0) + 1
            )

        return stats

    def clear_tenant(self, tenant_id: str) -> int:
        """Clear all sources for a tenant."""
        source_ids = list(self._tenant_sources.get(tenant_id, set()))
        for source_id in source_ids:
            self.delete(source_id)
        return len(source_ids)

    def reset(self) -> None:
        """Reset all state (for testing)."""
        self._sources.clear()
        self._tenant_sources.clear()


# Module-level singleton
_registry: Optional[DataSourceRegistry] = None


def get_datasource_registry() -> DataSourceRegistry:
    """Get the singleton registry instance."""
    global _registry
    if _registry is None:
        _registry = DataSourceRegistry()
    return _registry


def _reset_registry() -> None:
    """Reset the singleton (for testing)."""
    global _registry
    if _registry:
        _registry.reset()
    _registry = None


# Helper functions
def create_datasource(
    tenant_id: str,
    name: str,
    source_type: DataSourceType,
    config: Optional[DataSourceConfig] = None,
) -> CustomerDataSource:
    """Create a new data source using the singleton registry."""
    registry = get_datasource_registry()
    return registry.register(
        tenant_id=tenant_id,
        name=name,
        source_type=source_type,
        config=config,
    )


def get_datasource(source_id: str) -> Optional[CustomerDataSource]:
    """Get a data source by ID using the singleton registry."""
    registry = get_datasource_registry()
    return registry.get(source_id)


def list_datasources(
    tenant_id: Optional[str] = None,
    source_type: Optional[DataSourceType] = None,
) -> list[CustomerDataSource]:
    """List data sources using the singleton registry."""
    registry = get_datasource_registry()
    return registry.list(tenant_id=tenant_id, source_type=source_type)
