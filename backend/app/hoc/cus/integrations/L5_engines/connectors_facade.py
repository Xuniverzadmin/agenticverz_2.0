# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: (via connector services)
#   Writes: none (facade orchestration only)
# Role: Connectors Facade - Centralized access to connector operations
# Product: system-wide
# Callers: L2 connectors.py API, SDK
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, GAP-093 (Connector Registry API)


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
    # L5 engine import (migrated to HOC per SWEEP-13)
    from app.hoc.cus.integrations.L5_engines.connectors_facade import get_connectors_facade

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

    Layer: L5 (Domain Engine)
    Callers: L4 integrations handler
    """

    def __init__(self, session=None):
        """Initialize facade with L6 driver delegation.

        Args:
            session: Database session from L4 handler (optional for now,
                     required when DB-backed persistence is added).
        """
        self._session = session
        self._registry = None

    @property
    def registry(self):
        """Lazy-load ConnectorRegistry from L6 driver."""
        if self._registry is None:
            try:
                from app.hoc.cus.integrations.L6_drivers.connector_registry_driver import get_connector_registry
                self._registry = get_connector_registry()
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
        """List connectors for a tenant via L6 driver registry."""
        logger.debug(
            "facade.list_connectors",
            extra={"tenant_id": tenant_id, "type": connector_type}
        )

        if not self.registry:
            return []

        # Delegate to L6 driver
        raw = self.registry.list(tenant_id=tenant_id, limit=limit, offset=offset)
        results = []
        for c in raw:
            if connector_type and c.connector_type.value != connector_type:
                continue
            if status and c.status.value != status:
                continue
            results.append(ConnectorInfo(
                id=c.connector_id,
                name=c.name,
                connector_type=c.connector_type.value,
                status=c.status.value,
                capabilities=[cap.value for cap in c.capabilities],
                endpoint=c.config.endpoint if c.config else None,
                tenant_id=c.tenant_id,
                created_at=c.created_at,
                updated_at=c.updated_at,
                last_used_at=c.last_connected,
                config=c.config.to_dict() if c.config else {},
                metadata=c.metadata,
            ))
        return results

    async def get_connector(
        self,
        connector_id: str,
        tenant_id: str,
    ) -> Optional[ConnectorInfo]:
        """Get a specific connector via L6 driver registry."""
        if not self.registry:
            return None

        c = self.registry.get(connector_id)
        if not c or c.tenant_id != tenant_id:
            return None

        return ConnectorInfo(
            id=c.connector_id,
            name=c.name,
            connector_type=c.connector_type.value,
            status=c.status.value,
            capabilities=[cap.value for cap in c.capabilities],
            endpoint=c.config.endpoint if c.config else None,
            tenant_id=c.tenant_id,
            created_at=c.created_at,
            updated_at=c.updated_at,
            last_used_at=c.last_connected,
            config=c.config.to_dict() if c.config else {},
            metadata=c.metadata,
        )

    async def register_connector(
        self,
        tenant_id: str,
        name: str,
        connector_type: str,
        endpoint: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConnectorInfo:
        """Register a new connector via L6 driver registry."""
        logger.info(
            "facade.register_connector",
            extra={
                "tenant_id": tenant_id,
                "name": name,
                "type": connector_type,
            }
        )

        from app.hoc.cus.integrations.L6_drivers.connector_registry_driver import (
            ConnectorConfig as DriverConfig,
            ConnectorType as DriverType,
            BaseConnector,
        )

        connector_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Build L6 config
        driver_config = DriverConfig(endpoint=endpoint, **(config or {})) if endpoint or config else DriverConfig()

        # Map string type to enum
        try:
            driver_type = DriverType(connector_type)
        except ValueError:
            driver_type = DriverType.CUSTOM

        # Use registry factory methods where available, fallback to generic register
        if self.registry:
            if driver_type == DriverType.VECTOR:
                base = self.registry.create_vector_connector(
                    tenant_id=tenant_id, name=name, config=driver_config, connector_id=connector_id,
                )
            elif driver_type == DriverType.FILE:
                base = self.registry.create_file_connector(
                    tenant_id=tenant_id, name=name, config=driver_config, connector_id=connector_id,
                )
            elif driver_type == DriverType.SERVERLESS:
                base = self.registry.create_serverless_connector(
                    tenant_id=tenant_id, name=name, config=driver_config, connector_id=connector_id,
                )
            else:
                # Generic registration via a minimal concrete connector
                from app.hoc.cus.integrations.L6_drivers.connector_registry_driver import VectorConnector
                generic = VectorConnector(
                    connector_id=connector_id, tenant_id=tenant_id, name=name,
                    config=driver_config, vector_dimension=0,
                )
                generic.connector_type = driver_type
                base = self.registry.register(generic)

            if metadata:
                base.metadata = metadata

        capabilities = self._get_capabilities_for_type(connector_type)

        return ConnectorInfo(
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

    async def update_connector(
        self,
        connector_id: str,
        tenant_id: str,
        name: Optional[str] = None,
        endpoint: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[ConnectorInfo]:
        """Update a connector via L6 driver registry."""
        if not self.registry:
            return None

        c = self.registry.get(connector_id)
        if not c or c.tenant_id != tenant_id:
            return None

        if name:
            c.name = name
        if endpoint and c.config:
            c.config.endpoint = endpoint
        if metadata:
            c.metadata = metadata
        c.updated_at = datetime.now(timezone.utc)

        return ConnectorInfo(
            id=c.connector_id,
            name=c.name,
            connector_type=c.connector_type.value,
            status=c.status.value,
            capabilities=[cap.value for cap in c.capabilities],
            endpoint=c.config.endpoint if c.config else None,
            tenant_id=c.tenant_id,
            created_at=c.created_at,
            updated_at=c.updated_at,
            last_used_at=c.last_connected,
            config=c.config.to_dict() if c.config else {},
            metadata=c.metadata,
        )

    async def delete_connector(
        self,
        connector_id: str,
        tenant_id: str,
    ) -> bool:
        """Delete a connector via L6 driver registry."""
        if not self.registry:
            return False

        c = self.registry.get(connector_id)
        if not c or c.tenant_id != tenant_id:
            return False

        result = self.registry.delete(connector_id)
        if result:
            logger.info("facade.delete_connector", extra={"connector_id": connector_id})
        return result

    async def test_connector(
        self,
        connector_id: str,
        tenant_id: str,
    ) -> TestResult:
        """Test a connector connection via L6 driver registry."""
        import time

        if not self.registry:
            return TestResult(success=False, connector_id=connector_id, error="Registry not available")

        c = self.registry.get(connector_id)
        if not c or c.tenant_id != tenant_id:
            return TestResult(success=False, connector_id=connector_id, error="Connector not found")

        start_time = time.time()
        try:
            success = c.health_check()
            elapsed_ms = int((time.time() - start_time) * 1000)

            if success:
                c.record_connection()
                return TestResult(success=True, connector_id=connector_id, latency_ms=elapsed_ms, details={"status": "ok"})
            else:
                return TestResult(success=False, connector_id=connector_id, latency_ms=elapsed_ms, error="Health check failed")

        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            c.record_error(str(e))
            return TestResult(success=False, connector_id=connector_id, latency_ms=elapsed_ms, error=str(e))

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


def get_connectors_facade(session=None) -> ConnectorsFacade:
    """
    Get the connectors facade instance.

    Args:
        session: Optional database session from L4 handler.
                 Currently unused (L6 ConnectorRegistry is in-memory).
                 Accepted for forward-compatibility when DB persistence is added.

    Returns:
        ConnectorsFacade singleton instance.
    """
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = ConnectorsFacade(session=session)
    return _facade_instance
