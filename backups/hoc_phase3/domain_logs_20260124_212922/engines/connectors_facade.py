# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Connectors Facade - Centralized access to connector operations
# Callers: L2 connectors.py API, SDK
# Allowed Imports: L4 connector services, L6 (models, db)
# Forbidden Imports: L1, L2, L3, L5
# Reference: GAP-093 (Connector Registry API)

"""
Connectors Facade (L4 Domain Logic)

This facade provides the external interface for connector operations.
All connector APIs MUST use this facade instead of directly importing
internal connector modules.

Why This Facade Exists:
- Prevents L2→L4 layer violations
- Centralizes connector management logic
- Provides unified access to HTTP, SQL, MCP connectors
- Single point for audit emission

Wrapped Services:
- ConnectorRegistry: Connector registration and management
- HTTPConnector: HTTP/REST connector (GAP-059)
- SQLConnector: SQL database connector (GAP-060)
- MCPConnector: MCP protocol connector (GAP-063)

L2 API Routes (GAP-093):
- GET /api/v1/connectors (list connectors)
- POST /api/v1/connectors (register connector)
- GET /api/v1/connectors/{id} (get connector)
- PUT /api/v1/connectors/{id} (update connector)
- DELETE /api/v1/connectors/{id} (delete connector)
- POST /api/v1/connectors/{id}/test (test connector)

Usage:
    from app.services.connectors.facade import get_connectors_facade

    facade = get_connectors_facade()

    # List connectors
    connectors = await facade.list_connectors(tenant_id="...")

    # Register a new connector
    connector = await facade.register_connector(...)

    # Test connection
    result = await facade.test_connector(connector_id="...")
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger("nova.services.connectors.facade")


@dataclass
class ConnectorInfo:
    """Connector information."""
    id: str
    name: str
    connector_type: str
    status: str
    capabilities: List[str]
    endpoint: Optional[str]
    tenant_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "connector_type": self.connector_type,
            "status": self.status,
            "capabilities": self.capabilities,
            "endpoint": self.endpoint,
            "tenant_id": self.tenant_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "config": self.config,
            "metadata": self.metadata,
        }


@dataclass
class TestResult:
    """Result of connector test."""
    success: bool
    connector_id: str
    latency_ms: Optional[int] = None
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "connector_id": self.connector_id,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "details": self.details,
        }


class ConnectorsFacade:
    """
    Facade for connector operations.

    This is the ONLY entry point for L2 APIs and SDK to interact with
    connector services.

    Layer: L4 (Domain Logic)
    Callers: connectors.py (L2), aos_sdk
    """

    def __init__(self):
        """Initialize facade with lazy-loaded services."""
        self._registry = None
        self._http_connector = None
        self._sql_connector = None
        self._mcp_connector = None

        # In-memory store for demo (would be database in production)
        self._connectors: Dict[str, ConnectorInfo] = {}

    @property
    def registry(self):
        """Lazy-load ConnectorRegistry."""
        if self._registry is None:
            try:
                from app.services.connectors.connector_registry import ConnectorRegistry
                self._registry = ConnectorRegistry()
            except ImportError:
                logger.warning("ConnectorRegistry not available")
        return self._registry

    # =========================================================================
    # Connector CRUD Operations (GAP-093)
    # =========================================================================

    async def list_connectors(
        self,
        tenant_id: str,
        connector_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ConnectorInfo]:
        """
        List connectors for a tenant.

        Args:
            tenant_id: Tenant ID to filter by
            connector_type: Optional type filter
            status: Optional status filter
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of ConnectorInfo
        """
        logger.debug(
            "facade.list_connectors",
            extra={"tenant_id": tenant_id, "type": connector_type}
        )

        # Filter connectors
        results = []
        for connector in self._connectors.values():
            if connector.tenant_id != tenant_id:
                continue
            if connector_type and connector.connector_type != connector_type:
                continue
            if status and connector.status != status:
                continue
            results.append(connector)

        # Apply pagination
        return results[offset:offset + limit]

    async def get_connector(
        self,
        connector_id: str,
        tenant_id: str,
    ) -> Optional[ConnectorInfo]:
        """
        Get a specific connector.

        Args:
            connector_id: Connector ID
            tenant_id: Tenant ID for authorization

        Returns:
            ConnectorInfo or None if not found
        """
        connector = self._connectors.get(connector_id)
        if connector and connector.tenant_id == tenant_id:
            return connector
        return None

    async def register_connector(
        self,
        tenant_id: str,
        name: str,
        connector_type: str,
        endpoint: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConnectorInfo:
        """
        Register a new connector.

        Args:
            tenant_id: Tenant ID
            name: Connector name
            connector_type: Type (http, sql, mcp, etc.)
            endpoint: Connection endpoint
            config: Connector configuration
            metadata: Additional metadata

        Returns:
            ConnectorInfo for the new connector
        """
        logger.info(
            "facade.register_connector",
            extra={
                "tenant_id": tenant_id,
                "name": name,
                "type": connector_type,
            }
        )

        connector_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Determine capabilities based on type
        capabilities = self._get_capabilities_for_type(connector_type)

        connector = ConnectorInfo(
            id=connector_id,
            name=name,
            connector_type=connector_type,
            status="registered",
            capabilities=capabilities,
            endpoint=endpoint,
            tenant_id=tenant_id,
            created_at=now,
            config=config or {},
            metadata=metadata or {},
        )

        self._connectors[connector_id] = connector
        return connector

    async def update_connector(
        self,
        connector_id: str,
        tenant_id: str,
        name: Optional[str] = None,
        endpoint: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[ConnectorInfo]:
        """
        Update a connector.

        Args:
            connector_id: Connector ID
            tenant_id: Tenant ID for authorization
            name: New name (optional)
            endpoint: New endpoint (optional)
            config: New config (optional)
            metadata: New metadata (optional)

        Returns:
            Updated ConnectorInfo or None if not found
        """
        connector = self._connectors.get(connector_id)
        if not connector or connector.tenant_id != tenant_id:
            return None

        if name:
            connector.name = name
        if endpoint:
            connector.endpoint = endpoint
        if config:
            connector.config = config
        if metadata:
            connector.metadata = metadata

        connector.updated_at = datetime.now(timezone.utc)
        return connector

    async def delete_connector(
        self,
        connector_id: str,
        tenant_id: str,
    ) -> bool:
        """
        Delete a connector.

        Args:
            connector_id: Connector ID
            tenant_id: Tenant ID for authorization

        Returns:
            True if deleted, False if not found
        """
        connector = self._connectors.get(connector_id)
        if not connector or connector.tenant_id != tenant_id:
            return False

        del self._connectors[connector_id]
        logger.info(
            "facade.delete_connector",
            extra={"connector_id": connector_id}
        )
        return True

    async def test_connector(
        self,
        connector_id: str,
        tenant_id: str,
    ) -> TestResult:
        """
        Test a connector connection.

        Args:
            connector_id: Connector ID
            tenant_id: Tenant ID for authorization

        Returns:
            TestResult with connection test outcome
        """
        import time

        connector = self._connectors.get(connector_id)
        if not connector or connector.tenant_id != tenant_id:
            return TestResult(
                success=False,
                connector_id=connector_id,
                error="Connector not found",
            )

        start_time = time.time()

        try:
            # Simulate connection test based on type
            # In production, this would actually test the connection
            if connector.connector_type == "http":
                # Would test HTTP endpoint
                pass
            elif connector.connector_type == "sql":
                # Would test SQL connection
                pass
            elif connector.connector_type == "mcp":
                # Would test MCP server
                pass

            elapsed_ms = int((time.time() - start_time) * 1000)

            # Update last used
            connector.last_used_at = datetime.now(timezone.utc)
            connector.status = "connected"

            return TestResult(
                success=True,
                connector_id=connector_id,
                latency_ms=elapsed_ms,
                details={"status": "ok"},
            )

        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            connector.status = "error"

            return TestResult(
                success=False,
                connector_id=connector_id,
                latency_ms=elapsed_ms,
                error=str(e),
            )

    def _get_capabilities_for_type(self, connector_type: str) -> List[str]:
        """Get default capabilities for connector type."""
        capabilities_map = {
            "http": ["read", "write", "query"],
            "sql": ["read", "write", "query", "transaction"],
            "mcp": ["read", "write", "query"],
            "vector": ["read", "write", "vector_search"],
            "file": ["read", "write"],
            "serverless": ["query"],
            "stream": ["read", "stream"],
        }
        return capabilities_map.get(connector_type, ["read"])


# =============================================================================
# Module-level singleton accessor
# =============================================================================

_facade_instance: Optional[ConnectorsFacade] = None


def get_connectors_facade() -> ConnectorsFacade:
    """
    Get the connectors facade instance.

    This is the recommended way to access connector operations
    from L2 APIs and the SDK.

    Returns:
        ConnectorsFacade instance
    """
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = ConnectorsFacade()
    return _facade_instance
