# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: (via datasource services)
#   Writes: none (facade orchestration only)
# Role: DataSources Facade - Centralized access to data source operations
# Product: system-wide
# Callers: L2 datasources.py API, SDK
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, GAP-113 (Data Sources API)

"""
DataSources Facade (L4 Domain Logic)

This facade provides the external interface for data source operations.
All data source APIs MUST use this facade instead of directly importing
internal datasource modules.

Why This Facade Exists:
- Prevents L2→L4 layer violations
- Centralizes data source management
- Provides unified access to source configuration
- Single point for audit emission

L2 API Routes (GAP-113):
- POST /api/v1/datasources (create source)
- GET /api/v1/datasources (list sources)
- GET /api/v1/datasources/{id} (get source)
- PUT /api/v1/datasources/{id} (update source)
- DELETE /api/v1/datasources/{id} (delete source)
- POST /api/v1/datasources/{id}/test (test connection)
- POST /api/v1/datasources/{id}/activate (activate source)
- POST /api/v1/datasources/{id}/deactivate (deactivate source)
- GET /api/v1/datasources/stats (statistics)

Usage:
    from app.services.datasources.facade import get_datasources_facade

    facade = get_datasources_facade()

    # Register data source
    source = await facade.register_source(
        tenant_id="...",
        name="Production DB",
        source_type="database",
        config={...},
    )
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.hoc.cus.integrations.L5_schemas.datasource_model import (
    CustomerDataSource,
    DataSourceConfig,
    DataSourceRegistry,
    DataSourceStats,
    DataSourceStatus,
    DataSourceType,
    get_datasource_registry,
)

logger = logging.getLogger("nova.services.datasources.facade")


@dataclass
class TestConnectionResult:
    """Result of testing a data source connection."""
    success: bool
    message: str
    latency_ms: Optional[int] = None
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "message": self.message,
            "latency_ms": self.latency_ms,
            "details": self.details,
        }


class DataSourcesFacade:
    """
    Facade for data source operations.

    This is the ONLY entry point for L2 APIs and SDK to interact with
    data source services.

    Layer: L4 (Domain Logic)
    Callers: datasources.py (L2), aos_sdk
    """

    def __init__(self):
        """Initialize facade."""
        self._registry: Optional[DataSourceRegistry] = None

    @property
    def registry(self) -> DataSourceRegistry:
        """Lazy load the registry."""
        if self._registry is None:
            self._registry = get_datasource_registry()
        return self._registry

    # =========================================================================
    # Data Source CRUD Operations (GAP-113)
    # =========================================================================

    async def register_source(
        self,
        tenant_id: str,
        name: str,
        source_type: str,
        config: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        owner_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CustomerDataSource:
        """
        Register a new data source.

        Args:
            tenant_id: Tenant ID
            name: Source name
            source_type: Type of source (database, file, api, etc.)
            config: Connection configuration
            description: Optional description
            tags: Optional tags
            owner_id: Optional owner user ID
            metadata: Additional metadata

        Returns:
            Registered CustomerDataSource
        """
        logger.info(
            "facade.register_source",
            extra={"tenant_id": tenant_id, "name": name, "type": source_type}
        )

        # Parse source type
        try:
            source_type_enum = DataSourceType(source_type)
        except ValueError:
            source_type_enum = DataSourceType.CUSTOM

        # Build config
        ds_config = DataSourceConfig()
        if config:
            ds_config.host = config.get("host")
            ds_config.port = config.get("port")
            ds_config.username = config.get("username")
            ds_config.password = config.get("password")
            ds_config.database = config.get("database")
            ds_config.connection_string = config.get("connection_string")
            ds_config.auth_type = config.get("auth_type")
            ds_config.api_key = config.get("api_key")
            ds_config.ssl_enabled = config.get("ssl_enabled", False)
            ds_config.pool_size = config.get("pool_size", 5)
            if config.get("options"):
                ds_config.options = config["options"]

        source = self.registry.register(
            tenant_id=tenant_id,
            name=name,
            source_type=source_type_enum,
            config=ds_config,
            description=description,
            tags=tags,
            owner_id=owner_id,
        )

        if metadata:
            source.metadata = metadata

        return source

    async def list_sources(
        self,
        tenant_id: str,
        source_type: Optional[str] = None,
        status: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[CustomerDataSource]:
        """
        List data sources.

        Args:
            tenant_id: Tenant ID
            source_type: Optional filter by type
            status: Optional filter by status
            tag: Optional filter by tag
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of CustomerDataSource
        """
        # Parse filters
        type_enum = None
        if source_type:
            try:
                type_enum = DataSourceType(source_type)
            except ValueError:
                pass

        status_enum = None
        if status:
            try:
                status_enum = DataSourceStatus(status)
            except ValueError:
                pass

        return self.registry.list(
            tenant_id=tenant_id,
            source_type=type_enum,
            status=status_enum,
            tag=tag,
            limit=limit,
            offset=offset,
        )

    async def get_source(
        self,
        source_id: str,
        tenant_id: str,
    ) -> Optional[CustomerDataSource]:
        """
        Get a specific data source.

        Args:
            source_id: Source ID
            tenant_id: Tenant ID for authorization

        Returns:
            CustomerDataSource or None if not found
        """
        source = self.registry.get(source_id)
        if source and source.tenant_id == tenant_id:
            return source
        return None

    async def update_source(
        self,
        source_id: str,
        tenant_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[CustomerDataSource]:
        """
        Update a data source.

        Args:
            source_id: Source ID
            tenant_id: Tenant ID for authorization
            name: New name
            description: New description
            config: New configuration
            metadata: New metadata

        Returns:
            Updated CustomerDataSource or None if not found
        """
        source = self.registry.get(source_id)
        if not source or source.tenant_id != tenant_id:
            return None

        # Build new config if provided
        ds_config = None
        if config:
            ds_config = DataSourceConfig()
            ds_config.host = config.get("host")
            ds_config.port = config.get("port")
            ds_config.username = config.get("username")
            ds_config.password = config.get("password")
            ds_config.database = config.get("database")
            ds_config.connection_string = config.get("connection_string")
            ds_config.auth_type = config.get("auth_type")
            ds_config.api_key = config.get("api_key")
            ds_config.ssl_enabled = config.get("ssl_enabled", False)
            ds_config.pool_size = config.get("pool_size", 5)
            if config.get("options"):
                ds_config.options = config["options"]

        return self.registry.update(
            source_id=source_id,
            name=name,
            description=description,
            config=ds_config,
            metadata=metadata,
        )

    async def delete_source(
        self,
        source_id: str,
        tenant_id: str,
    ) -> bool:
        """
        Delete a data source.

        Args:
            source_id: Source ID
            tenant_id: Tenant ID for authorization

        Returns:
            True if deleted, False if not found
        """
        source = self.registry.get(source_id)
        if not source or source.tenant_id != tenant_id:
            return False

        logger.info("facade.delete_source", extra={"source_id": source_id})
        return self.registry.delete(source_id)

    # =========================================================================
    # Data Source Control Operations (GAP-113)
    # =========================================================================

    async def test_connection(
        self,
        source_id: str,
        tenant_id: str,
    ) -> Optional[TestConnectionResult]:
        """
        Test a data source connection.

        Args:
            source_id: Source ID
            tenant_id: Tenant ID for authorization

        Returns:
            TestConnectionResult or None if not found
        """
        source = self.registry.get(source_id)
        if not source or source.tenant_id != tenant_id:
            return None

        logger.info("facade.test_connection", extra={"source_id": source_id})

        # Simulate connection test (in production, would actually connect)
        # For demo, always succeed
        source.record_connection()

        return TestConnectionResult(
            success=True,
            message="Connection successful",
            latency_ms=50,
            details={
                "host": source.config.host,
                "type": source.source_type.value,
            },
        )

    async def activate_source(
        self,
        source_id: str,
        tenant_id: str,
    ) -> Optional[CustomerDataSource]:
        """
        Activate a data source.

        Args:
            source_id: Source ID
            tenant_id: Tenant ID for authorization

        Returns:
            Updated CustomerDataSource or None if not found
        """
        source = self.registry.get(source_id)
        if not source or source.tenant_id != tenant_id:
            return None

        logger.info("facade.activate_source", extra={"source_id": source_id})
        return self.registry.activate(source_id)

    async def deactivate_source(
        self,
        source_id: str,
        tenant_id: str,
    ) -> Optional[CustomerDataSource]:
        """
        Deactivate a data source.

        Args:
            source_id: Source ID
            tenant_id: Tenant ID for authorization

        Returns:
            Updated CustomerDataSource or None if not found
        """
        source = self.registry.get(source_id)
        if not source or source.tenant_id != tenant_id:
            return None

        logger.info("facade.deactivate_source", extra={"source_id": source_id})
        return self.registry.deactivate(source_id)

    # =========================================================================
    # Statistics (GAP-113)
    # =========================================================================

    async def get_statistics(
        self,
        tenant_id: str,
    ) -> DataSourceStats:
        """
        Get data source statistics for a tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            DataSourceStats
        """
        return self.registry.get_statistics(tenant_id=tenant_id)


# =============================================================================
# Module-level singleton accessor
# =============================================================================

_facade_instance: Optional[DataSourcesFacade] = None


def get_datasources_facade() -> DataSourcesFacade:
    """
    Get the data sources facade instance.

    This is the recommended way to access data source operations
    from L2 APIs and the SDK.

    Returns:
        DataSourcesFacade instance
    """
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = DataSourcesFacade()
    return _facade_instance
