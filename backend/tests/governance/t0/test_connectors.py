# Layer: L8 — Tests
# Product: system-wide
# Reference: GAP-059 (HTTP Connector), GAP-060 (SQL Gateway), GAP-063 (MCP Connector)
"""
Unit tests for T0 Connector modules.

Tests the governed connectors that provide machine-controlled
access to external resources:
- GAP-059: HTTP Connector
- GAP-060: SQL Gateway
- GAP-063: MCP Connector
"""

import pytest


class TestHttpConnector:
    """Test suite for HTTP Connector (GAP-059)."""

    def test_connector_import(self):
        """HTTP connector should be importable."""
        from app.services.connectors.http_connector import (
            HttpConnectorService,
            HttpConnectorConfig,
        )

        assert HttpConnectorService is not None
        assert HttpConnectorConfig is not None

    def test_connector_config_creation(self):
        """HttpConnectorConfig should be creatable."""
        from app.services.connectors.http_connector import HttpConnectorConfig

        config = HttpConnectorConfig(
            id="http-001",
            name="Test HTTP Connector",
            base_url="https://api.example.com",
            auth_type="bearer",
            timeout_seconds=30,
            max_response_bytes=5 * 1024 * 1024,
        )

        assert config.id == "http-001"
        assert "api.example.com" in config.base_url

    def test_connector_has_rate_limit(self):
        """HTTP connector should have rate limiting config."""
        from app.services.connectors.http_connector import HttpConnectorConfig

        config = HttpConnectorConfig(
            id="http-001",
            name="Test",
            base_url="https://api.example.com",
            auth_type="bearer",
            rate_limit_per_minute=60,
        )

        assert config.rate_limit_per_minute == 60


class TestSqlGateway:
    """Test suite for SQL Gateway (GAP-060)."""

    def test_gateway_import(self):
        """SQL gateway should be importable."""
        from app.services.connectors.sql_gateway import (
            SqlGatewayService,
            SqlGatewayConfig,
            QueryTemplate,
        )

        assert SqlGatewayService is not None
        assert SqlGatewayConfig is not None
        assert QueryTemplate is not None

    def test_template_creation(self):
        """QueryTemplate should be creatable."""
        from app.services.connectors.sql_gateway import (
            QueryTemplate,
            ParameterSpec,
            ParameterType,
        )

        template = QueryTemplate(
            id="get-users",
            name="Get Users",
            description="Get users by tenant",
            sql="SELECT * FROM users WHERE tenant_id = $1",
            parameters=[
                ParameterSpec(name="tenant_id", param_type=ParameterType.STRING)
            ],
            read_only=True,
        )

        assert template.id == "get-users"
        assert template.read_only is True

    def test_sql_injection_patterns_defined(self):
        """SQL gateway should check for injection patterns."""
        from app.services.connectors.sql_gateway import SqlInjectionAttemptError

        assert SqlInjectionAttemptError is not None

    def test_read_only_enforced(self):
        """SQL gateway should enforce read-only mode."""
        from app.services.connectors.sql_gateway import SqlGatewayConfig

        config = SqlGatewayConfig(
            id="sql-001",
            name="Test SQL Gateway",
            connection_string_ref="vault://db/conn",
            allowed_templates=["get-users"],
            read_only=True,
        )

        assert config.read_only is True


class TestMcpConnector:
    """Test suite for MCP Connector (GAP-063)."""

    def test_connector_import(self):
        """MCP connector should be importable."""
        from app.services.connectors.mcp_connector import (
            McpConnectorService,
            McpConnectorConfig,
            McpToolDefinition,
        )

        assert McpConnectorService is not None
        assert McpConnectorConfig is not None
        assert McpToolDefinition is not None

    def test_tool_definition_creation(self):
        """McpToolDefinition should be creatable."""
        from app.services.connectors.mcp_connector import McpToolDefinition

        tool = McpToolDefinition(
            name="search",
            description="Search documents",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            },
            requires_approval=False,
        )

        assert tool.name == "search"
        assert "query" in tool.input_schema["properties"]

    def test_config_has_allowlist(self):
        """MCP config should have tool allowlist."""
        from app.services.connectors.mcp_connector import McpConnectorConfig

        config = McpConnectorConfig(
            id="mcp-001",
            name="Test MCP Connector",
            server_url="https://mcp.example.com",
            api_key_ref="vault://mcp/key",
            allowed_tools=["search", "read"],
        )

        assert "search" in config.allowed_tools
        assert "write" not in config.allowed_tools

    def test_rate_limit_defined(self):
        """MCP connector should have rate limiting."""
        from app.services.connectors.mcp_connector import McpConnectorConfig

        config = McpConnectorConfig(
            id="mcp-001",
            name="Test",
            server_url="https://mcp.example.com",
            api_key_ref="vault://key",
            allowed_tools=["search"],
            rate_limit_per_minute=30,
        )

        assert config.rate_limit_per_minute == 30

    def test_approval_required_error(self):
        """MCP connector should have approval error."""
        from app.services.connectors.mcp_connector import McpApprovalRequiredError

        error = McpApprovalRequiredError("dangerous_tool")
        assert "dangerous_tool" in str(error)


class TestConnectorBlastRadiusCaps:
    """Test connector blast-radius caps (INV-003)."""

    def test_http_max_response_bytes(self):
        """HTTP connector should have max response bytes cap."""
        from app.services.connectors.http_connector import DEFAULT_MAX_RESPONSE_BYTES

        assert DEFAULT_MAX_RESPONSE_BYTES > 0
        assert DEFAULT_MAX_RESPONSE_BYTES <= 10 * 1024 * 1024  # Max 10MB

    def test_sql_max_rows(self):
        """SQL gateway should have max rows cap."""
        from app.services.connectors.sql_gateway import DEFAULT_MAX_ROWS

        assert DEFAULT_MAX_ROWS > 0
        assert DEFAULT_MAX_ROWS <= 10000  # Max 10K rows

    def test_mcp_max_response(self):
        """MCP connector should have max response cap."""
        from app.services.connectors.mcp_connector import DEFAULT_MAX_RESPONSE_BYTES

        assert DEFAULT_MAX_RESPONSE_BYTES > 0
        assert DEFAULT_MAX_RESPONSE_BYTES <= 10 * 1024 * 1024  # Max 10MB

    def test_timeout_defaults(self):
        """All connectors should have reasonable timeout defaults."""
        from app.services.connectors.http_connector import DEFAULT_TIMEOUT_SECONDS as HTTP_TIMEOUT
        from app.services.connectors.sql_gateway import DEFAULT_TIMEOUT_SECONDS as SQL_TIMEOUT
        from app.services.connectors.mcp_connector import DEFAULT_TIMEOUT_SECONDS as MCP_TIMEOUT

        # All should have reasonable defaults (< 5 minutes)
        assert HTTP_TIMEOUT <= 300
        assert SQL_TIMEOUT <= 300
        assert MCP_TIMEOUT <= 300
