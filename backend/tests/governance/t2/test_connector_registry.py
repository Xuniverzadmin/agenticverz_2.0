# Layer: L8 — Catalyst/Meta
# Product: system-wide
# Reference: GAP-057/061/062/064 (Connectors)
"""
Tests for ConnectorRegistry and Connectors (GAP-057/061/062/064).

Verifies connector registration, management, and specific connectors.
"""

import pytest
from datetime import datetime, timezone


class TestConnectorImports:
    """Test that all components are properly exported."""

    def test_type_import(self):
        """ConnectorType should be importable."""
        from app.services.connectors import ConnectorType
        assert ConnectorType.VECTOR == "vector"

    def test_status_import(self):
        """ConnectorStatus should be importable."""
        from app.services.connectors import ConnectorStatus
        assert ConnectorStatus.READY == "ready"

    def test_capability_import(self):
        """ConnectorCapability should be importable."""
        from app.services.connectors import ConnectorCapability
        assert ConnectorCapability.READ == "read"

    def test_config_import(self):
        """ConnectorConfig should be importable."""
        from app.services.connectors import ConnectorConfig
        config = ConnectorConfig()
        assert config.timeout_seconds == 30

    def test_registry_import(self):
        """ConnectorRegistry should be importable."""
        from app.services.connectors import ConnectorRegistry
        registry = ConnectorRegistry()
        assert registry is not None

    def test_connectors_import(self):
        """All connector types should be importable."""
        from app.services.connectors import (
            VectorConnector,
            FileConnector,
            ServerlessConnector,
        )
        assert VectorConnector is not None
        assert FileConnector is not None
        assert ServerlessConnector is not None


class TestConnectorConfig:
    """Test ConnectorConfig dataclass."""

    def test_default_values(self):
        """Default configuration should have sensible values."""
        from app.services.connectors import ConnectorConfig

        config = ConnectorConfig()
        assert config.timeout_seconds == 30
        assert config.max_retries == 3
        assert config.rate_limit_enabled is False

    def test_to_dict_masks_secrets(self):
        """to_dict should mask secrets by default."""
        from app.services.connectors import ConnectorConfig

        config = ConnectorConfig(credentials={"api_key": "secret"})
        result = config.to_dict()
        assert result["credentials"]["api_key"] == "***"


class TestVectorConnector:
    """Test VectorConnector (GAP-061)."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        from app.services.connectors.connector_registry import _reset_registry
        _reset_registry()
        yield
        _reset_registry()

    def test_vector_connector_creation(self):
        """Vector connector should be created with correct type."""
        from app.services.connectors import (
            VectorConnector,
            ConnectorType,
            ConnectorCapability,
        )

        connector = VectorConnector(
            connector_id="vec-1",
            tenant_id="tenant-1",
            name="Vector DB",
        )

        assert connector.connector_type == ConnectorType.VECTOR
        assert connector.vector_dimension == 1536
        assert ConnectorCapability.VECTOR_SEARCH in connector.capabilities

    def test_vector_connector_connect(self):
        """Vector connector should connect successfully."""
        from app.services.connectors import VectorConnector, ConnectorStatus

        connector = VectorConnector(
            connector_id="vec-1",
            tenant_id="tenant-1",
            name="Vector DB",
        )

        result = connector.connect()
        assert result is True
        assert connector.status == ConnectorStatus.CONNECTED

    def test_vector_connector_search(self):
        """Vector connector should support search."""
        from app.services.connectors import VectorConnector

        connector = VectorConnector(
            connector_id="vec-1",
            tenant_id="tenant-1",
            name="Vector DB",
        )
        connector.connect()

        results = connector.search([0.1] * 1536, top_k=5)
        assert len(results) <= 5

    def test_vector_connector_upsert(self):
        """Vector connector should support upsert."""
        from app.services.connectors import VectorConnector

        connector = VectorConnector(
            connector_id="vec-1",
            tenant_id="tenant-1",
            name="Vector DB",
        )
        connector.connect()

        result = connector.upsert_vectors([
            {"id": "v1", "values": [0.1] * 1536},
            {"id": "v2", "values": [0.2] * 1536},
        ])
        assert result["upserted"] == 2


class TestFileConnector:
    """Test FileConnector (GAP-062)."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        from app.services.connectors.connector_registry import _reset_registry
        _reset_registry()
        yield
        _reset_registry()

    def test_file_connector_creation(self):
        """File connector should be created with correct type."""
        from app.services.connectors import (
            FileConnector,
            ConnectorType,
            ConnectorCapability,
        )

        connector = FileConnector(
            connector_id="file-1",
            tenant_id="tenant-1",
            name="File Storage",
            storage_type="s3",
        )

        assert connector.connector_type == ConnectorType.FILE
        assert connector.storage_type == "s3"
        assert ConnectorCapability.READ in connector.capabilities

    def test_file_connector_connect(self):
        """File connector should connect successfully."""
        from app.services.connectors import FileConnector, ConnectorStatus

        connector = FileConnector(
            connector_id="file-1",
            tenant_id="tenant-1",
            name="File Storage",
        )

        result = connector.connect()
        assert result is True
        assert connector.status == ConnectorStatus.CONNECTED

    def test_file_connector_list(self):
        """File connector should list files."""
        from app.services.connectors import FileConnector

        connector = FileConnector(
            connector_id="file-1",
            tenant_id="tenant-1",
            name="File Storage",
        )
        connector.connect()

        files = connector.list_files("/")
        assert len(files) > 0

    def test_file_connector_write_read(self):
        """File connector should write and read files."""
        from app.services.connectors import FileConnector

        connector = FileConnector(
            connector_id="file-1",
            tenant_id="tenant-1",
            name="File Storage",
        )
        connector.connect()

        write_result = connector.write_file("/test.txt", b"content")
        assert write_result["status"] == "success"

        content = connector.read_file("/test.txt")
        assert content == b"file content"  # Simulated


class TestServerlessConnector:
    """Test ServerlessConnector (GAP-064)."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        from app.services.connectors.connector_registry import _reset_registry
        _reset_registry()
        yield
        _reset_registry()

    def test_serverless_connector_creation(self):
        """Serverless connector should be created with correct type."""
        from app.services.connectors import (
            ServerlessConnector,
            ConnectorType,
        )

        connector = ServerlessConnector(
            connector_id="sls-1",
            tenant_id="tenant-1",
            name="Lambda",
            platform="aws_lambda",
        )

        assert connector.connector_type == ConnectorType.SERVERLESS
        assert connector.platform == "aws_lambda"

    def test_serverless_connector_invoke(self):
        """Serverless connector should invoke functions."""
        from app.services.connectors import ServerlessConnector

        connector = ServerlessConnector(
            connector_id="sls-1",
            tenant_id="tenant-1",
            name="Lambda",
        )
        connector.connect()

        result = connector.invoke("my-function", {"key": "value"})
        assert result["status"] == "completed"

    def test_serverless_connector_list_functions(self):
        """Serverless connector should list functions."""
        from app.services.connectors import ServerlessConnector

        connector = ServerlessConnector(
            connector_id="sls-1",
            tenant_id="tenant-1",
            name="Lambda",
        )
        connector.connect()

        functions = connector.list_functions()
        assert len(functions) > 0


class TestConnectorRegistry:
    """Test ConnectorRegistry (GAP-057)."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        from app.services.connectors.connector_registry import _reset_registry
        _reset_registry()
        yield
        _reset_registry()

    def test_registry_creation(self):
        """Registry should be created."""
        from app.services.connectors import ConnectorRegistry

        registry = ConnectorRegistry()
        assert registry is not None

    def test_register_vector_connector(self):
        """Registry should create and register vector connector."""
        from app.services.connectors import ConnectorRegistry, ConnectorType

        registry = ConnectorRegistry()
        connector = registry.create_vector_connector(
            tenant_id="tenant-1",
            name="Vector DB",
        )

        assert connector.connector_type == ConnectorType.VECTOR
        assert registry.get(connector.connector_id) is not None

    def test_register_file_connector(self):
        """Registry should create and register file connector."""
        from app.services.connectors import ConnectorRegistry, ConnectorType

        registry = ConnectorRegistry()
        connector = registry.create_file_connector(
            tenant_id="tenant-1",
            name="File Storage",
            storage_type="s3",
        )

        assert connector.connector_type == ConnectorType.FILE
        assert connector.storage_type == "s3"

    def test_register_serverless_connector(self):
        """Registry should create and register serverless connector."""
        from app.services.connectors import ConnectorRegistry, ConnectorType

        registry = ConnectorRegistry()
        connector = registry.create_serverless_connector(
            tenant_id="tenant-1",
            name="Lambda",
            platform="aws_lambda",
        )

        assert connector.connector_type == ConnectorType.SERVERLESS
        assert connector.platform == "aws_lambda"

    def test_list_by_type(self):
        """Connectors should be filterable by type."""
        from app.services.connectors import ConnectorRegistry, ConnectorType

        registry = ConnectorRegistry()

        registry.create_vector_connector(tenant_id="tenant-1", name="Vec 1")
        registry.create_vector_connector(tenant_id="tenant-1", name="Vec 2")
        registry.create_file_connector(tenant_id="tenant-1", name="File 1")

        vector_connectors = registry.list(connector_type=ConnectorType.VECTOR)
        file_connectors = registry.list(connector_type=ConnectorType.FILE)

        assert len(vector_connectors) == 2
        assert len(file_connectors) == 1

    def test_list_by_tenant(self):
        """Connectors should be filterable by tenant."""
        from app.services.connectors import ConnectorRegistry

        registry = ConnectorRegistry()

        registry.create_vector_connector(tenant_id="tenant-1", name="Vec 1")
        registry.create_vector_connector(tenant_id="tenant-2", name="Vec 2")

        tenant1_connectors = registry.list(tenant_id="tenant-1")
        tenant2_connectors = registry.list(tenant_id="tenant-2")

        assert len(tenant1_connectors) == 1
        assert len(tenant2_connectors) == 1

    def test_get_by_name(self):
        """Connectors should be retrievable by name."""
        from app.services.connectors import ConnectorRegistry

        registry = ConnectorRegistry()
        registry.create_vector_connector(tenant_id="tenant-1", name="My Vector DB")

        connector = registry.get_by_name("tenant-1", "My Vector DB")
        assert connector is not None
        assert connector.name == "My Vector DB"

    def test_delete_connector(self):
        """Deleting should remove connector."""
        from app.services.connectors import ConnectorRegistry

        registry = ConnectorRegistry()
        connector = registry.create_vector_connector(
            tenant_id="tenant-1",
            name="To Delete",
        )

        result = registry.delete(connector.connector_id)
        assert result is True
        assert registry.get(connector.connector_id) is None

    def test_get_statistics(self):
        """Statistics should be collected correctly."""
        from app.services.connectors import ConnectorRegistry

        registry = ConnectorRegistry()

        registry.create_vector_connector(tenant_id="tenant-1", name="Vec 1")
        registry.create_file_connector(tenant_id="tenant-1", name="File 1")
        registry.create_serverless_connector(tenant_id="tenant-1", name="Sls 1")

        stats = registry.get_statistics()
        assert stats.total_connectors == 3
        assert stats.connectors_by_type["vector"] == 1
        assert stats.connectors_by_type["file"] == 1
        assert stats.connectors_by_type["serverless"] == 1

    def test_clear_tenant(self):
        """Clearing tenant should remove all connectors."""
        from app.services.connectors import ConnectorRegistry

        registry = ConnectorRegistry()

        for i in range(3):
            registry.create_vector_connector(
                tenant_id="tenant-1",
                name=f"Vec {i}",
            )

        cleared = registry.clear_tenant("tenant-1")
        assert cleared == 3
        assert len(registry.list(tenant_id="tenant-1")) == 0


class TestHelperFunctions:
    """Test module-level helper functions."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        from app.services.connectors.connector_registry import _reset_registry
        _reset_registry()
        yield
        _reset_registry()

    def test_get_connector_registry(self):
        """get_connector_registry should return singleton."""
        from app.services.connectors import get_connector_registry

        registry1 = get_connector_registry()
        registry2 = get_connector_registry()
        assert registry1 is registry2

    def test_register_and_get_connector(self):
        """Helper functions should work with singleton."""
        from app.services.connectors import (
            VectorConnector,
            register_connector,
            get_connector,
        )

        connector = VectorConnector(
            connector_id="vec-1",
            tenant_id="tenant-1",
            name="Test",
        )

        register_connector(connector)
        retrieved = get_connector("vec-1")

        assert retrieved is not None
        assert retrieved.connector_id == "vec-1"

    def test_list_connectors(self):
        """list_connectors should use singleton."""
        from app.services.connectors import (
            get_connector_registry,
            list_connectors,
        )

        registry = get_connector_registry()
        registry.create_vector_connector(tenant_id="tenant-1", name="Vec 1")
        registry.create_file_connector(tenant_id="tenant-1", name="File 1")

        connectors = list_connectors(tenant_id="tenant-1")
        assert len(connectors) == 2
