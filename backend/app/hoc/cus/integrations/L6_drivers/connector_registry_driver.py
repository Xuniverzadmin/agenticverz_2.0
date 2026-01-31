# Layer: L6 — Domain Driver
# NOTE: Renamed connector_registry.py → connector_registry_driver.py (2026-01-31) per BANNED_NAMING rule
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none (data models only)
#   Writes: none
# Database:
#   Scope: domain (integrations)
#   Models: Connector
# Role: Connector management and registration
# Product: system-wide
# Callers: L5 engines
# Allowed Imports: L6, L7 (models)
# Reference: PIN-470, GAP-057 (ConnectorRegistry), GAP-061/062/064 (Connectors)
"""
ConnectorRegistry - Connector management and registration.

Provides a unified registry for:
- Connector type registration
- Connector instance management
- Capability discovery
- Status monitoring
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
import uuid


class ConnectorType(str, Enum):
    """Types of connectors."""

    HTTP = "http"             # REST/HTTP APIs
    SQL = "sql"               # SQL databases
    MCP = "mcp"               # Model Context Protocol
    VECTOR = "vector"         # Vector databases
    FILE = "file"             # File storage
    SERVERLESS = "serverless" # Serverless functions
    STREAM = "stream"         # Streaming sources
    CUSTOM = "custom"         # Custom connectors


class ConnectorStatus(str, Enum):
    """Status of a connector."""

    REGISTERED = "registered"   # Registered but not configured
    CONFIGURING = "configuring" # Configuration in progress
    READY = "ready"             # Ready for use
    CONNECTED = "connected"     # Actively connected
    DISCONNECTED = "disconnected" # Temporarily disconnected
    ERROR = "error"             # In error state
    DEPRECATED = "deprecated"   # Marked for removal


class ConnectorCapability(str, Enum):
    """Capabilities a connector may have."""

    READ = "read"               # Can read data
    WRITE = "write"             # Can write data
    QUERY = "query"             # Can run queries
    STREAM = "stream"           # Can stream data
    BATCH = "batch"             # Can batch operations
    TRANSACTION = "transaction" # Supports transactions
    SEARCH = "search"           # Supports search
    VECTOR_SEARCH = "vector_search"  # Supports vector search


@dataclass
class ConnectorConfig:
    """Base configuration for connectors."""

    # Connection settings
    endpoint: Optional[str] = None
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay_seconds: int = 1

    # Authentication
    auth_type: Optional[str] = None  # none, api_key, oauth, iam
    credentials: dict[str, Any] = field(default_factory=dict)

    # Rate limiting
    rate_limit_enabled: bool = False
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    # Additional options
    options: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, include_secrets: bool = False) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "endpoint": self.endpoint,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "retry_delay_seconds": self.retry_delay_seconds,
            "auth_type": self.auth_type,
            "credentials": (
                {k: "***" for k in self.credentials}
                if self.credentials and not include_secrets
                else self.credentials
            ),
            "rate_limit_enabled": self.rate_limit_enabled,
            "rate_limit_requests": self.rate_limit_requests,
            "rate_limit_window_seconds": self.rate_limit_window_seconds,
            "options": self.options,
        }


class ConnectorError(Exception):
    """Exception for connector errors."""

    def __init__(
        self,
        message: str,
        connector_id: Optional[str] = None,
        connector_type: Optional[ConnectorType] = None,
    ):
        super().__init__(message)
        self.message = message
        self.connector_id = connector_id
        self.connector_type = connector_type

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "error": self.message,
            "connector_id": self.connector_id,
            "connector_type": (
                self.connector_type.value if self.connector_type else None
            ),
        }


class BaseConnector(ABC):
    """Abstract base class for all connectors."""

    def __init__(
        self,
        connector_id: str,
        tenant_id: str,
        name: str,
        connector_type: ConnectorType,
        config: Optional[ConnectorConfig] = None,
    ):
        self.connector_id = connector_id
        self.tenant_id = tenant_id
        self.name = name
        self.connector_type = connector_type
        self.config = config or ConnectorConfig()

        self.status = ConnectorStatus.REGISTERED
        self.capabilities: list[ConnectorCapability] = []

        self.last_connected: Optional[datetime] = None
        self.last_error: Optional[str] = None
        self.connection_count: int = 0
        self.error_count: int = 0

        self.metadata: dict[str, Any] = {}
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the service."""
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from the service."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if connector is healthy."""
        pass

    def record_connection(self, now: Optional[datetime] = None) -> None:
        """Record a successful connection."""
        now = now or datetime.now(timezone.utc)
        self.last_connected = now
        self.connection_count += 1
        self.status = ConnectorStatus.CONNECTED
        self.updated_at = now

    def record_error(self, error: str, now: Optional[datetime] = None) -> None:
        """Record a connection error."""
        now = now or datetime.now(timezone.utc)
        self.last_error = error
        self.error_count += 1
        self.status = ConnectorStatus.ERROR
        self.updated_at = now

    def to_dict(self, include_secrets: bool = False) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "connector_id": self.connector_id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "connector_type": self.connector_type.value,
            "config": self.config.to_dict(include_secrets=include_secrets),
            "status": self.status.value,
            "capabilities": [c.value for c in self.capabilities],
            "last_connected": (
                self.last_connected.isoformat() if self.last_connected else None
            ),
            "last_error": self.last_error,
            "connection_count": self.connection_count,
            "error_count": self.error_count,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# GAP-061: Vector Connector
class VectorConnector(BaseConnector):
    """
    Connector for vector databases (GAP-061).

    Supports:
    - Vector storage and retrieval
    - Similarity search
    - Metadata filtering
    """

    def __init__(
        self,
        connector_id: str,
        tenant_id: str,
        name: str,
        config: Optional[ConnectorConfig] = None,
        vector_dimension: int = 1536,
        distance_metric: str = "cosine",
    ):
        super().__init__(
            connector_id=connector_id,
            tenant_id=tenant_id,
            name=name,
            connector_type=ConnectorType.VECTOR,
            config=config,
        )
        self.vector_dimension = vector_dimension
        self.distance_metric = distance_metric
        self.capabilities = [
            ConnectorCapability.READ,
            ConnectorCapability.WRITE,
            ConnectorCapability.SEARCH,
            ConnectorCapability.VECTOR_SEARCH,
        ]
        self._connected = False

    def connect(self) -> bool:
        """Connect to vector database."""
        try:
            # Simulate connection
            self._connected = True
            self.record_connection()
            return True
        except Exception as e:
            self.record_error(str(e))
            return False

    def disconnect(self) -> bool:
        """Disconnect from vector database."""
        self._connected = False
        self.status = ConnectorStatus.DISCONNECTED
        self.updated_at = datetime.now(timezone.utc)
        return True

    def health_check(self) -> bool:
        """Check vector database health."""
        return self._connected and self.status == ConnectorStatus.CONNECTED

    def upsert_vectors(
        self,
        vectors: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Upsert vectors to the database."""
        if not self._connected:
            raise ConnectorError(
                "Not connected",
                connector_id=self.connector_id,
                connector_type=self.connector_type,
            )

        # Simulate upsert
        return {
            "upserted": len(vectors),
            "status": "success",
        }

    def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        filter_metadata: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors."""
        if not self._connected:
            raise ConnectorError(
                "Not connected",
                connector_id=self.connector_id,
                connector_type=self.connector_type,
            )

        # Simulate search results
        return [
            {"id": f"vec-{i}", "score": 0.9 - (i * 0.1), "metadata": {}}
            for i in range(min(top_k, 5))
        ]

    def delete_vectors(self, ids: list[str]) -> dict[str, Any]:
        """Delete vectors by ID."""
        if not self._connected:
            raise ConnectorError(
                "Not connected",
                connector_id=self.connector_id,
                connector_type=self.connector_type,
            )

        return {
            "deleted": len(ids),
            "status": "success",
        }

    def to_dict(self, include_secrets: bool = False) -> dict[str, Any]:
        """Convert to dictionary with vector-specific fields."""
        result = super().to_dict(include_secrets=include_secrets)
        result["vector_dimension"] = self.vector_dimension
        result["distance_metric"] = self.distance_metric
        return result


# GAP-062: File Connector
class FileConnector(BaseConnector):
    """
    Connector for file storage (GAP-062).

    Supports:
    - File upload/download
    - Directory listing
    - Metadata operations
    """

    def __init__(
        self,
        connector_id: str,
        tenant_id: str,
        name: str,
        config: Optional[ConnectorConfig] = None,
        storage_type: str = "local",
        base_path: str = "/",
    ):
        super().__init__(
            connector_id=connector_id,
            tenant_id=tenant_id,
            name=name,
            connector_type=ConnectorType.FILE,
            config=config,
        )
        self.storage_type = storage_type  # local, s3, gcs, azure
        self.base_path = base_path
        self.capabilities = [
            ConnectorCapability.READ,
            ConnectorCapability.WRITE,
            ConnectorCapability.QUERY,
        ]
        self._connected = False

    def connect(self) -> bool:
        """Connect to file storage."""
        try:
            self._connected = True
            self.record_connection()
            return True
        except Exception as e:
            self.record_error(str(e))
            return False

    def disconnect(self) -> bool:
        """Disconnect from file storage."""
        self._connected = False
        self.status = ConnectorStatus.DISCONNECTED
        self.updated_at = datetime.now(timezone.utc)
        return True

    def health_check(self) -> bool:
        """Check file storage health."""
        return self._connected and self.status == ConnectorStatus.CONNECTED

    def list_files(
        self,
        path: str = "/",
        recursive: bool = False,
    ) -> list[dict[str, Any]]:
        """List files in a directory."""
        if not self._connected:
            raise ConnectorError(
                "Not connected",
                connector_id=self.connector_id,
                connector_type=self.connector_type,
            )

        # Simulate file listing
        return [
            {"name": f"file-{i}.txt", "path": f"{path}/file-{i}.txt", "size": 1024}
            for i in range(3)
        ]

    def read_file(self, path: str) -> bytes:
        """Read a file."""
        if not self._connected:
            raise ConnectorError(
                "Not connected",
                connector_id=self.connector_id,
                connector_type=self.connector_type,
            )

        # Simulate file read
        return b"file content"

    def write_file(self, path: str, content: bytes) -> dict[str, Any]:
        """Write a file."""
        if not self._connected:
            raise ConnectorError(
                "Not connected",
                connector_id=self.connector_id,
                connector_type=self.connector_type,
            )

        return {
            "path": path,
            "size": len(content),
            "status": "success",
        }

    def delete_file(self, path: str) -> dict[str, Any]:
        """Delete a file."""
        if not self._connected:
            raise ConnectorError(
                "Not connected",
                connector_id=self.connector_id,
                connector_type=self.connector_type,
            )

        return {
            "path": path,
            "status": "deleted",
        }

    def to_dict(self, include_secrets: bool = False) -> dict[str, Any]:
        """Convert to dictionary with file-specific fields."""
        result = super().to_dict(include_secrets=include_secrets)
        result["storage_type"] = self.storage_type
        result["base_path"] = self.base_path
        return result


# GAP-064: Serverless Connector
class ServerlessConnector(BaseConnector):
    """
    Connector for serverless functions (GAP-064).

    Supports:
    - Function invocation
    - Async execution
    - Result retrieval
    """

    def __init__(
        self,
        connector_id: str,
        tenant_id: str,
        name: str,
        config: Optional[ConnectorConfig] = None,
        platform: str = "aws_lambda",
        region: str = "us-east-1",
    ):
        super().__init__(
            connector_id=connector_id,
            tenant_id=tenant_id,
            name=name,
            connector_type=ConnectorType.SERVERLESS,
            config=config,
        )
        self.platform = platform  # aws_lambda, gcp_functions, azure_functions
        self.region = region
        self.capabilities = [
            ConnectorCapability.READ,
            ConnectorCapability.WRITE,
        ]
        self._connected = False

    def connect(self) -> bool:
        """Connect to serverless platform."""
        try:
            self._connected = True
            self.record_connection()
            return True
        except Exception as e:
            self.record_error(str(e))
            return False

    def disconnect(self) -> bool:
        """Disconnect from serverless platform."""
        self._connected = False
        self.status = ConnectorStatus.DISCONNECTED
        self.updated_at = datetime.now(timezone.utc)
        return True

    def health_check(self) -> bool:
        """Check serverless platform health."""
        return self._connected and self.status == ConnectorStatus.CONNECTED

    def invoke(
        self,
        function_name: str,
        payload: dict[str, Any],
        async_invoke: bool = False,
    ) -> dict[str, Any]:
        """Invoke a serverless function."""
        if not self._connected:
            raise ConnectorError(
                "Not connected",
                connector_id=self.connector_id,
                connector_type=self.connector_type,
            )

        # Simulate invocation
        return {
            "function": function_name,
            "request_id": str(uuid.uuid4()),
            "status": "invoked" if async_invoke else "completed",
            "result": {"message": "success"} if not async_invoke else None,
        }

    def list_functions(self) -> list[dict[str, Any]]:
        """List available functions."""
        if not self._connected:
            raise ConnectorError(
                "Not connected",
                connector_id=self.connector_id,
                connector_type=self.connector_type,
            )

        # Simulate function listing
        return [
            {"name": f"function-{i}", "runtime": "python3.11", "memory": 128}
            for i in range(3)
        ]

    def get_result(self, request_id: str) -> dict[str, Any]:
        """Get async invocation result."""
        if not self._connected:
            raise ConnectorError(
                "Not connected",
                connector_id=self.connector_id,
                connector_type=self.connector_type,
            )

        # Simulate result
        return {
            "request_id": request_id,
            "status": "completed",
            "result": {"message": "success"},
        }

    def to_dict(self, include_secrets: bool = False) -> dict[str, Any]:
        """Convert to dictionary with serverless-specific fields."""
        result = super().to_dict(include_secrets=include_secrets)
        result["platform"] = self.platform
        result["region"] = self.region
        return result


@dataclass
class ConnectorStats:
    """Statistics for connectors."""

    total_connectors: int = 0
    ready_connectors: int = 0
    connected_connectors: int = 0
    error_connectors: int = 0

    # By type
    connectors_by_type: dict[str, int] = field(default_factory=dict)

    # Totals
    total_connections: int = 0
    total_errors: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_connectors": self.total_connectors,
            "ready_connectors": self.ready_connectors,
            "connected_connectors": self.connected_connectors,
            "error_connectors": self.error_connectors,
            "connectors_by_type": self.connectors_by_type,
            "total_connections": self.total_connections,
            "total_errors": self.total_errors,
        }


class ConnectorRegistry:
    """
    Registry for managing connectors (GAP-057).

    Features:
    - Connector registration and lookup
    - Type-based filtering
    - Status management
    - Tenant isolation
    """

    def __init__(self):
        """Initialize the registry."""
        self._connectors: dict[str, BaseConnector] = {}
        self._tenant_connectors: dict[str, set[str]] = {}

    def register(
        self,
        connector: BaseConnector,
    ) -> BaseConnector:
        """Register a connector."""
        self._connectors[connector.connector_id] = connector

        # Track by tenant
        tenant_id = connector.tenant_id
        if tenant_id not in self._tenant_connectors:
            self._tenant_connectors[tenant_id] = set()
        self._tenant_connectors[tenant_id].add(connector.connector_id)

        return connector

    def create_vector_connector(
        self,
        tenant_id: str,
        name: str,
        config: Optional[ConnectorConfig] = None,
        vector_dimension: int = 1536,
        connector_id: Optional[str] = None,
    ) -> VectorConnector:
        """Create and register a vector connector."""
        connector = VectorConnector(
            connector_id=connector_id or str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=name,
            config=config,
            vector_dimension=vector_dimension,
        )
        return self.register(connector)

    def create_file_connector(
        self,
        tenant_id: str,
        name: str,
        config: Optional[ConnectorConfig] = None,
        storage_type: str = "local",
        base_path: str = "/",
        connector_id: Optional[str] = None,
    ) -> FileConnector:
        """Create and register a file connector."""
        connector = FileConnector(
            connector_id=connector_id or str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=name,
            config=config,
            storage_type=storage_type,
            base_path=base_path,
        )
        return self.register(connector)

    def create_serverless_connector(
        self,
        tenant_id: str,
        name: str,
        config: Optional[ConnectorConfig] = None,
        platform: str = "aws_lambda",
        region: str = "us-east-1",
        connector_id: Optional[str] = None,
    ) -> ServerlessConnector:
        """Create and register a serverless connector."""
        connector = ServerlessConnector(
            connector_id=connector_id or str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=name,
            config=config,
            platform=platform,
            region=region,
        )
        return self.register(connector)

    def get(self, connector_id: str) -> Optional[BaseConnector]:
        """Get a connector by ID."""
        return self._connectors.get(connector_id)

    def get_by_name(
        self,
        tenant_id: str,
        name: str,
    ) -> Optional[BaseConnector]:
        """Get a connector by name within a tenant."""
        for connector in self._connectors.values():
            if connector.tenant_id == tenant_id and connector.name == name:
                return connector
        return None

    def list(
        self,
        tenant_id: Optional[str] = None,
        connector_type: Optional[ConnectorType] = None,
        status: Optional[ConnectorStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[BaseConnector]:
        """List connectors with optional filters."""
        connectors = list(self._connectors.values())

        if tenant_id:
            connectors = [c for c in connectors if c.tenant_id == tenant_id]

        if connector_type:
            connectors = [c for c in connectors if c.connector_type == connector_type]

        if status:
            connectors = [c for c in connectors if c.status == status]

        connectors.sort(key=lambda c: c.name)

        return connectors[offset:offset + limit]

    def delete(self, connector_id: str) -> bool:
        """Delete a connector."""
        connector = self._connectors.get(connector_id)
        if not connector:
            return False

        del self._connectors[connector_id]

        # Remove from tenant tracking
        if connector.tenant_id in self._tenant_connectors:
            self._tenant_connectors[connector.tenant_id].discard(connector_id)

        return True

    def get_statistics(
        self,
        tenant_id: Optional[str] = None,
    ) -> ConnectorStats:
        """Get registry statistics."""
        stats = ConnectorStats()

        for connector in self._connectors.values():
            if tenant_id and connector.tenant_id != tenant_id:
                continue

            stats.total_connectors += 1
            stats.total_connections += connector.connection_count
            stats.total_errors += connector.error_count

            if connector.status == ConnectorStatus.READY:
                stats.ready_connectors += 1
            elif connector.status == ConnectorStatus.CONNECTED:
                stats.connected_connectors += 1
            elif connector.status == ConnectorStatus.ERROR:
                stats.error_connectors += 1

            type_key = connector.connector_type.value
            stats.connectors_by_type[type_key] = (
                stats.connectors_by_type.get(type_key, 0) + 1
            )

        return stats

    def clear_tenant(self, tenant_id: str) -> int:
        """Clear all connectors for a tenant."""
        connector_ids = list(self._tenant_connectors.get(tenant_id, set()))
        for connector_id in connector_ids:
            self.delete(connector_id)
        return len(connector_ids)

    def reset(self) -> None:
        """Reset all state (for testing)."""
        self._connectors.clear()
        self._tenant_connectors.clear()


# Module-level singleton
_registry: Optional[ConnectorRegistry] = None


def get_connector_registry() -> ConnectorRegistry:
    """Get the singleton registry instance."""
    global _registry
    if _registry is None:
        _registry = ConnectorRegistry()
    return _registry


def _reset_registry() -> None:
    """Reset the singleton (for testing)."""
    global _registry
    if _registry:
        _registry.reset()
    _registry = None


# Helper functions
def register_connector(connector: BaseConnector) -> BaseConnector:
    """Register a connector using the singleton registry."""
    registry = get_connector_registry()
    return registry.register(connector)


def get_connector(connector_id: str) -> Optional[BaseConnector]:
    """Get a connector by ID using the singleton registry."""
    registry = get_connector_registry()
    return registry.get(connector_id)


def list_connectors(
    tenant_id: Optional[str] = None,
    connector_type: Optional[ConnectorType] = None,
) -> list[BaseConnector]:
    """List connectors using the singleton registry."""
    registry = get_connector_registry()
    return registry.list(tenant_id=tenant_id, connector_type=connector_type)
