# Layer: L4 — Domain Engines
# Product: system-wide
# Role: Connector services for governed external access

"""
Connectors Package

Contains governed connectors for external data access:
- http_connector: Machine-controlled HTTP access (GAP-059)
- sql_gateway: Template-based SQL queries (GAP-060)
- mcp_connector: MCP tool invocation (GAP-063)
- connector_registry: Connector management (GAP-057)
- VectorConnector: Vector database connector (GAP-061)
- FileConnector: File storage connector (GAP-062)
- ServerlessConnector: Serverless function connector (GAP-064)

All connectors implement the Connector protocol from mediation layer.
"""

from app.services.connectors.http_connector import (
    HttpConnectorService,
    HttpConnectorConfig,
)
from app.services.connectors.sql_gateway import (
    SqlGatewayService,
    SqlGatewayConfig,
    QueryTemplate,
)
from app.services.connectors.mcp_connector import (
    McpConnectorService,
    McpConnectorConfig,
    McpToolDefinition,
)
from app.services.connectors.connector_registry import (
    BaseConnector,
    ConnectorCapability,
    ConnectorConfig,
    ConnectorError,
    ConnectorRegistry,
    ConnectorStatus,
    ConnectorType,
    FileConnector,
    ServerlessConnector,
    VectorConnector,
    get_connector,
    get_connector_registry,
    list_connectors,
    register_connector,
)

__all__ = [
    # HTTP Connector (GAP-059)
    "HttpConnectorService",
    "HttpConnectorConfig",
    # SQL Gateway (GAP-060)
    "SqlGatewayService",
    "SqlGatewayConfig",
    "QueryTemplate",
    # MCP Connector (GAP-063)
    "McpConnectorService",
    "McpConnectorConfig",
    "McpToolDefinition",
    # Connector Registry (GAP-057)
    "BaseConnector",
    "ConnectorCapability",
    "ConnectorConfig",
    "ConnectorError",
    "ConnectorRegistry",
    "ConnectorStatus",
    "ConnectorType",
    # Vector Connector (GAP-061)
    "VectorConnector",
    # File Connector (GAP-062)
    "FileConnector",
    # Serverless Connector (GAP-064)
    "ServerlessConnector",
    # Helper functions
    "get_connector",
    "get_connector_registry",
    "list_connectors",
    "register_connector",
]
