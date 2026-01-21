# Layer: L8 — Catalyst/Meta
# Product: system-wide
# Reference: GAP-055 (CustomerDataSource model)
"""
Tests for CustomerDataSource model (GAP-055).

Verifies customer data source models and registry including
configuration, status management, and access control.
"""

import pytest
from datetime import datetime, timezone


class TestDataSourceImports:
    """Test that all components are properly exported."""

    def test_type_import(self):
        """DataSourceType should be importable from package."""
        from app.services.datasources import DataSourceType
        assert DataSourceType.DATABASE == "database"

    def test_status_import(self):
        """DataSourceStatus should be importable from package."""
        from app.services.datasources import DataSourceStatus
        assert DataSourceStatus.ACTIVE == "active"

    def test_config_import(self):
        """DataSourceConfig should be importable from package."""
        from app.services.datasources import DataSourceConfig
        config = DataSourceConfig()
        assert config.pool_size == 5

    def test_datasource_import(self):
        """CustomerDataSource should be importable from package."""
        from app.services.datasources import (
            CustomerDataSource,
            DataSourceType,
            DataSourceConfig,
        )
        source = CustomerDataSource(
            source_id="src-1",
            tenant_id="tenant-1",
            name="Test Source",
            source_type=DataSourceType.DATABASE,
        )
        assert source.source_id == "src-1"

    def test_registry_import(self):
        """DataSourceRegistry should be importable from package."""
        from app.services.datasources import DataSourceRegistry
        registry = DataSourceRegistry()
        assert registry is not None

    def test_error_import(self):
        """DataSourceError should be importable from package."""
        from app.services.datasources import DataSourceError
        error = DataSourceError("test error")
        assert str(error) == "test error"

    def test_helper_functions_import(self):
        """Helper functions should be importable from package."""
        from app.services.datasources import (
            create_datasource,
            get_datasource,
            list_datasources,
            get_datasource_registry,
        )
        assert callable(create_datasource)
        assert callable(get_datasource)
        assert callable(list_datasources)
        assert callable(get_datasource_registry)


class TestDataSourceTypeEnum:
    """Test DataSourceType enum."""

    def test_all_types_defined(self):
        """All data source types should be defined."""
        from app.services.datasources import DataSourceType

        assert hasattr(DataSourceType, "DATABASE")
        assert hasattr(DataSourceType, "DOCUMENT")
        assert hasattr(DataSourceType, "FILE")
        assert hasattr(DataSourceType, "VECTOR")
        assert hasattr(DataSourceType, "API")
        assert hasattr(DataSourceType, "STREAM")
        assert hasattr(DataSourceType, "CUSTOM")

    def test_type_string_values(self):
        """Type values should be lowercase strings."""
        from app.services.datasources import DataSourceType

        assert DataSourceType.DATABASE.value == "database"
        assert DataSourceType.VECTOR.value == "vector"
        assert DataSourceType.API.value == "api"


class TestDataSourceStatusEnum:
    """Test DataSourceStatus enum."""

    def test_all_statuses_defined(self):
        """All statuses should be defined."""
        from app.services.datasources import DataSourceStatus

        assert hasattr(DataSourceStatus, "PENDING")
        assert hasattr(DataSourceStatus, "CONFIGURING")
        assert hasattr(DataSourceStatus, "ACTIVE")
        assert hasattr(DataSourceStatus, "INACTIVE")
        assert hasattr(DataSourceStatus, "ERROR")
        assert hasattr(DataSourceStatus, "DEPRECATED")


class TestDataSourceConfig:
    """Test DataSourceConfig dataclass."""

    def test_default_values(self):
        """Default configuration should have sensible values."""
        from app.services.datasources import DataSourceConfig

        config = DataSourceConfig()

        assert config.connection_string is None
        assert config.pool_size == 5
        assert config.pool_timeout == 30
        assert config.max_retries == 3
        assert config.ssl_enabled is False

    def test_custom_values(self):
        """Configuration should accept custom values."""
        from app.services.datasources import DataSourceConfig

        config = DataSourceConfig(
            host="localhost",
            port=5432,
            username="user",
            password="secret",
            database="mydb",
        )

        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "mydb"

    def test_to_dict_masks_secrets(self):
        """to_dict should mask secrets by default."""
        from app.services.datasources import DataSourceConfig

        config = DataSourceConfig(
            password="secret123",
            api_key="key456",
        )
        result = config.to_dict()

        assert result["password"] == "***"
        assert result["api_key"] == "***"

    def test_to_dict_includes_secrets(self):
        """to_dict should include secrets when requested."""
        from app.services.datasources import DataSourceConfig

        config = DataSourceConfig(
            password="secret123",
            api_key="key456",
        )
        result = config.to_dict(include_secrets=True)

        assert result["password"] == "secret123"
        assert result["api_key"] == "key456"

    def test_get_connection_url_from_string(self):
        """get_connection_url should return connection_string if set."""
        from app.services.datasources import DataSourceConfig

        config = DataSourceConfig(
            connection_string="postgresql://user:pass@host:5432/db",
        )

        assert config.get_connection_url() == "postgresql://user:pass@host:5432/db"

    def test_get_connection_url_from_components(self):
        """get_connection_url should build URL from components."""
        from app.services.datasources import DataSourceConfig

        config = DataSourceConfig(
            host="localhost",
            port=5432,
            username="user",
            password="pass",
            database="mydb",
        )

        url = config.get_connection_url()
        assert url == "user:pass@localhost:5432/mydb"


class TestCustomerDataSource:
    """Test CustomerDataSource dataclass."""

    def test_source_creation(self):
        """Source should be created with required fields."""
        from app.services.datasources import (
            CustomerDataSource,
            DataSourceType,
            DataSourceStatus,
        )

        source = CustomerDataSource(
            source_id="src-1",
            tenant_id="tenant-1",
            name="Test Source",
            source_type=DataSourceType.DATABASE,
        )

        assert source.source_id == "src-1"
        assert source.tenant_id == "tenant-1"
        assert source.name == "Test Source"
        assert source.source_type == DataSourceType.DATABASE
        assert source.status == DataSourceStatus.PENDING

    def test_record_connection(self):
        """Recording connection should update stats."""
        from app.services.datasources import (
            CustomerDataSource,
            DataSourceType,
        )

        source = CustomerDataSource(
            source_id="src-1",
            tenant_id="tenant-1",
            name="Test",
            source_type=DataSourceType.DATABASE,
        )

        source.record_connection()

        assert source.connection_count == 1
        assert source.last_connected is not None

    def test_record_error(self):
        """Recording error should update status and stats."""
        from app.services.datasources import (
            CustomerDataSource,
            DataSourceType,
            DataSourceStatus,
        )

        source = CustomerDataSource(
            source_id="src-1",
            tenant_id="tenant-1",
            name="Test",
            source_type=DataSourceType.DATABASE,
        )

        source.record_error("Connection refused")

        assert source.error_count == 1
        assert source.last_error == "Connection refused"
        assert source.status == DataSourceStatus.ERROR

    def test_activate(self):
        """Activating should update status."""
        from app.services.datasources import (
            CustomerDataSource,
            DataSourceType,
            DataSourceStatus,
        )

        source = CustomerDataSource(
            source_id="src-1",
            tenant_id="tenant-1",
            name="Test",
            source_type=DataSourceType.DATABASE,
        )
        source.status = DataSourceStatus.ERROR
        source.last_error = "Previous error"

        source.activate()

        assert source.status == DataSourceStatus.ACTIVE
        assert source.last_error is None

    def test_deactivate(self):
        """Deactivating should update status."""
        from app.services.datasources import (
            CustomerDataSource,
            DataSourceType,
            DataSourceStatus,
        )

        source = CustomerDataSource(
            source_id="src-1",
            tenant_id="tenant-1",
            name="Test",
            source_type=DataSourceType.DATABASE,
        )
        source.status = DataSourceStatus.ACTIVE

        source.deactivate()

        assert source.status == DataSourceStatus.INACTIVE

    def test_deprecate(self):
        """Deprecating should update status."""
        from app.services.datasources import (
            CustomerDataSource,
            DataSourceType,
            DataSourceStatus,
        )

        source = CustomerDataSource(
            source_id="src-1",
            tenant_id="tenant-1",
            name="Test",
            source_type=DataSourceType.DATABASE,
        )

        source.deprecate()

        assert source.status == DataSourceStatus.DEPRECATED

    def test_update_config(self):
        """Updating config should set configuring status."""
        from app.services.datasources import (
            CustomerDataSource,
            DataSourceType,
            DataSourceConfig,
            DataSourceStatus,
        )

        source = CustomerDataSource(
            source_id="src-1",
            tenant_id="tenant-1",
            name="Test",
            source_type=DataSourceType.DATABASE,
        )

        new_config = DataSourceConfig(host="newhost")
        source.update_config(new_config)

        assert source.config.host == "newhost"
        assert source.status == DataSourceStatus.CONFIGURING

    def test_tags(self):
        """Tags should be manageable."""
        from app.services.datasources import (
            CustomerDataSource,
            DataSourceType,
        )

        source = CustomerDataSource(
            source_id="src-1",
            tenant_id="tenant-1",
            name="Test",
            source_type=DataSourceType.DATABASE,
        )

        source.add_tag("production")
        assert "production" in source.tags

        source.add_tag("production")  # Duplicate
        assert source.tags.count("production") == 1

        source.remove_tag("production")
        assert "production" not in source.tags

    def test_access_control(self):
        """Access control should work correctly."""
        from app.services.datasources import (
            CustomerDataSource,
            DataSourceType,
        )

        source = CustomerDataSource(
            source_id="src-1",
            tenant_id="tenant-1",
            name="Test",
            source_type=DataSourceType.DATABASE,
        )

        # Empty access_roles means everyone has access
        assert source.has_access("admin") is True

        source.grant_access("admin")
        assert "admin" in source.access_roles
        assert source.has_access("admin") is True
        assert source.has_access("viewer") is False

        source.revoke_access("admin")
        assert "admin" not in source.access_roles

    def test_to_dict(self):
        """Source should serialize to dict."""
        from app.services.datasources import (
            CustomerDataSource,
            DataSourceType,
        )

        source = CustomerDataSource(
            source_id="src-1",
            tenant_id="tenant-1",
            name="Test Source",
            source_type=DataSourceType.DATABASE,
            description="A test source",
        )
        result = source.to_dict()

        assert result["source_id"] == "src-1"
        assert result["tenant_id"] == "tenant-1"
        assert result["name"] == "Test Source"
        assert result["source_type"] == "database"
        assert result["description"] == "A test source"


class TestDataSourceError:
    """Test DataSourceError exception."""

    def test_error_creation(self):
        """Error should be created with message."""
        from app.services.datasources import DataSourceError, DataSourceType

        error = DataSourceError(
            message="Connection failed",
            source_id="src-1",
            source_type=DataSourceType.DATABASE,
        )

        assert str(error) == "Connection failed"
        assert error.source_id == "src-1"
        assert error.source_type == DataSourceType.DATABASE

    def test_error_to_dict(self):
        """Error should serialize to dict."""
        from app.services.datasources import DataSourceError, DataSourceType

        error = DataSourceError(
            message="Timeout",
            source_id="src-1",
            source_type=DataSourceType.API,
        )
        result = error.to_dict()

        assert result["error"] == "Timeout"
        assert result["source_id"] == "src-1"
        assert result["source_type"] == "api"


class TestDataSourceRegistry:
    """Test DataSourceRegistry core functionality."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        from app.services.datasources.datasource_model import _reset_registry
        _reset_registry()
        yield
        _reset_registry()

    def test_registry_creation(self):
        """Registry should be created."""
        from app.services.datasources import DataSourceRegistry

        registry = DataSourceRegistry()
        assert registry is not None

    def test_register_source(self):
        """Registering a source should store it."""
        from app.services.datasources import (
            DataSourceRegistry,
            DataSourceType,
            DataSourceStatus,
        )

        registry = DataSourceRegistry()

        source = registry.register(
            tenant_id="tenant-1",
            name="My Database",
            source_type=DataSourceType.DATABASE,
        )

        assert source.source_id is not None
        assert source.tenant_id == "tenant-1"
        assert source.name == "My Database"
        assert source.status == DataSourceStatus.PENDING

    def test_get_source(self):
        """Getting a source by ID should work."""
        from app.services.datasources import (
            DataSourceRegistry,
            DataSourceType,
        )

        registry = DataSourceRegistry()
        source = registry.register(
            tenant_id="tenant-1",
            name="Test",
            source_type=DataSourceType.DATABASE,
        )

        retrieved = registry.get(source.source_id)
        assert retrieved is not None
        assert retrieved.source_id == source.source_id

    def test_get_source_not_found(self):
        """Getting non-existent source should return None."""
        from app.services.datasources import DataSourceRegistry

        registry = DataSourceRegistry()
        retrieved = registry.get("nonexistent")
        assert retrieved is None

    def test_get_by_name(self):
        """Getting a source by name should work."""
        from app.services.datasources import (
            DataSourceRegistry,
            DataSourceType,
        )

        registry = DataSourceRegistry()
        registry.register(
            tenant_id="tenant-1",
            name="Production DB",
            source_type=DataSourceType.DATABASE,
        )

        source = registry.get_by_name("tenant-1", "Production DB")
        assert source is not None
        assert source.name == "Production DB"


class TestDataSourceRegistryFiltering:
    """Test source filtering and listing."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        from app.services.datasources.datasource_model import _reset_registry
        _reset_registry()
        yield
        _reset_registry()

    def test_list_by_tenant(self):
        """Sources should be filterable by tenant."""
        from app.services.datasources import (
            DataSourceRegistry,
            DataSourceType,
        )

        registry = DataSourceRegistry()

        for i in range(3):
            registry.register(
                tenant_id="tenant-1",
                name=f"Source {i}",
                source_type=DataSourceType.DATABASE,
            )

        registry.register(
            tenant_id="tenant-2",
            name="Other",
            source_type=DataSourceType.DATABASE,
        )

        sources = registry.list(tenant_id="tenant-1")
        assert len(sources) == 3

    def test_list_by_type(self):
        """Sources should be filterable by type."""
        from app.services.datasources import (
            DataSourceRegistry,
            DataSourceType,
        )

        registry = DataSourceRegistry()

        registry.register(
            tenant_id="tenant-1",
            name="DB 1",
            source_type=DataSourceType.DATABASE,
        )
        registry.register(
            tenant_id="tenant-1",
            name="API 1",
            source_type=DataSourceType.API,
        )

        db_sources = registry.list(source_type=DataSourceType.DATABASE)
        api_sources = registry.list(source_type=DataSourceType.API)

        assert len(db_sources) == 1
        assert len(api_sources) == 1

    def test_list_by_status(self):
        """Sources should be filterable by status."""
        from app.services.datasources import (
            DataSourceRegistry,
            DataSourceType,
            DataSourceStatus,
        )

        registry = DataSourceRegistry()

        source1 = registry.register(
            tenant_id="tenant-1",
            name="Active",
            source_type=DataSourceType.DATABASE,
        )
        registry.activate(source1.source_id)

        registry.register(
            tenant_id="tenant-1",
            name="Pending",
            source_type=DataSourceType.DATABASE,
        )

        active = registry.list(status=DataSourceStatus.ACTIVE)
        pending = registry.list(status=DataSourceStatus.PENDING)

        assert len(active) == 1
        assert len(pending) == 1

    def test_list_by_tag(self):
        """Sources should be filterable by tag."""
        from app.services.datasources import (
            DataSourceRegistry,
            DataSourceType,
        )

        registry = DataSourceRegistry()

        source1 = registry.register(
            tenant_id="tenant-1",
            name="Production",
            source_type=DataSourceType.DATABASE,
            tags=["production", "critical"],
        )

        registry.register(
            tenant_id="tenant-1",
            name="Development",
            source_type=DataSourceType.DATABASE,
            tags=["development"],
        )

        prod_sources = registry.list(tag="production")
        assert len(prod_sources) == 1
        assert prod_sources[0].name == "Production"


class TestDataSourceRegistryOperations:
    """Test source operations."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        from app.services.datasources.datasource_model import _reset_registry
        _reset_registry()
        yield
        _reset_registry()

    def test_update_source(self):
        """Updating a source should work."""
        from app.services.datasources import (
            DataSourceRegistry,
            DataSourceType,
        )

        registry = DataSourceRegistry()
        source = registry.register(
            tenant_id="tenant-1",
            name="Original",
            source_type=DataSourceType.DATABASE,
        )

        registry.update(source.source_id, name="Updated", description="New desc")

        assert source.name == "Updated"
        assert source.description == "New desc"

    def test_activate_source(self):
        """Activating a source should update status."""
        from app.services.datasources import (
            DataSourceRegistry,
            DataSourceType,
            DataSourceStatus,
        )

        registry = DataSourceRegistry()
        source = registry.register(
            tenant_id="tenant-1",
            name="Test",
            source_type=DataSourceType.DATABASE,
        )

        registry.activate(source.source_id)
        assert source.status == DataSourceStatus.ACTIVE

    def test_deactivate_source(self):
        """Deactivating a source should update status."""
        from app.services.datasources import (
            DataSourceRegistry,
            DataSourceType,
            DataSourceStatus,
        )

        registry = DataSourceRegistry()
        source = registry.register(
            tenant_id="tenant-1",
            name="Test",
            source_type=DataSourceType.DATABASE,
        )
        registry.activate(source.source_id)

        registry.deactivate(source.source_id)
        assert source.status == DataSourceStatus.INACTIVE

    def test_delete_source(self):
        """Deleting a source should remove it."""
        from app.services.datasources import (
            DataSourceRegistry,
            DataSourceType,
        )

        registry = DataSourceRegistry()
        source = registry.register(
            tenant_id="tenant-1",
            name="Test",
            source_type=DataSourceType.DATABASE,
        )

        result = registry.delete(source.source_id)
        assert result is True
        assert registry.get(source.source_id) is None


class TestDataSourceRegistryStatistics:
    """Test statistics gathering."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        from app.services.datasources.datasource_model import _reset_registry
        _reset_registry()
        yield
        _reset_registry()

    def test_get_statistics(self):
        """Statistics should be collected correctly."""
        from app.services.datasources import (
            DataSourceRegistry,
            DataSourceType,
        )

        registry = DataSourceRegistry()

        for i in range(5):
            registry.register(
                tenant_id="tenant-1",
                name=f"Source {i}",
                source_type=DataSourceType.DATABASE,
            )

        stats = registry.get_statistics()
        assert stats.total_sources == 5
        assert stats.pending_sources == 5

    def test_get_statistics_by_tenant(self):
        """Statistics should filter by tenant."""
        from app.services.datasources import (
            DataSourceRegistry,
            DataSourceType,
        )

        registry = DataSourceRegistry()

        for i in range(3):
            registry.register(
                tenant_id="tenant-1",
                name=f"Source {i}",
                source_type=DataSourceType.DATABASE,
            )

        registry.register(
            tenant_id="tenant-2",
            name="Other",
            source_type=DataSourceType.DATABASE,
        )

        stats = registry.get_statistics(tenant_id="tenant-1")
        assert stats.total_sources == 3

    def test_clear_tenant(self):
        """Clearing tenant should remove all sources."""
        from app.services.datasources import (
            DataSourceRegistry,
            DataSourceType,
        )

        registry = DataSourceRegistry()

        for i in range(5):
            registry.register(
                tenant_id="tenant-1",
                name=f"Source {i}",
                source_type=DataSourceType.DATABASE,
            )

        cleared = registry.clear_tenant("tenant-1")
        assert cleared == 5

        sources = registry.list(tenant_id="tenant-1")
        assert len(sources) == 0


class TestHelperFunctions:
    """Test module-level helper functions."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        from app.services.datasources.datasource_model import _reset_registry
        _reset_registry()
        yield
        _reset_registry()

    def test_create_datasource_helper(self):
        """create_datasource should use singleton."""
        from app.services.datasources import (
            create_datasource,
            DataSourceType,
        )

        source = create_datasource(
            tenant_id="tenant-1",
            name="Test",
            source_type=DataSourceType.DATABASE,
        )

        assert source.source_id is not None

    def test_get_datasource_helper(self):
        """get_datasource should use singleton."""
        from app.services.datasources import (
            create_datasource,
            get_datasource,
            DataSourceType,
        )

        source = create_datasource(
            tenant_id="tenant-1",
            name="Test",
            source_type=DataSourceType.DATABASE,
        )

        retrieved = get_datasource(source.source_id)
        assert retrieved is not None
        assert retrieved.source_id == source.source_id

    def test_list_datasources_helper(self):
        """list_datasources should use singleton."""
        from app.services.datasources import (
            create_datasource,
            list_datasources,
            DataSourceType,
        )

        for i in range(3):
            create_datasource(
                tenant_id="tenant-1",
                name=f"Source {i}",
                source_type=DataSourceType.DATABASE,
            )

        sources = list_datasources(tenant_id="tenant-1")
        assert len(sources) == 3

    def test_get_datasource_registry_helper(self):
        """get_datasource_registry should return singleton."""
        from app.services.datasources import get_datasource_registry

        registry1 = get_datasource_registry()
        registry2 = get_datasource_registry()

        assert registry1 is registry2


class TestDataSourceUseCases:
    """Test real-world use cases."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        from app.services.datasources.datasource_model import _reset_registry
        _reset_registry()
        yield
        _reset_registry()

    def test_database_source_lifecycle(self):
        """Simulate a database source lifecycle."""
        from app.services.datasources import (
            DataSourceRegistry,
            DataSourceType,
            DataSourceConfig,
            DataSourceStatus,
        )

        registry = DataSourceRegistry()

        # Register
        source = registry.register(
            tenant_id="tenant-1",
            name="Production DB",
            source_type=DataSourceType.DATABASE,
            description="Main production database",
            tags=["production", "critical"],
        )

        assert source.status == DataSourceStatus.PENDING

        # Configure
        config = DataSourceConfig(
            host="db.example.com",
            port=5432,
            username="app_user",
            password="secret",
            database="production",
            ssl_enabled=True,
        )
        source.update_config(config)
        assert source.status == DataSourceStatus.CONFIGURING

        # Activate
        source.activate()
        assert source.status == DataSourceStatus.ACTIVE

        # Record usage
        source.record_connection()
        assert source.connection_count == 1

        # Handle error
        source.record_error("Connection timeout")
        assert source.status == DataSourceStatus.ERROR

        # Recover
        source.activate()
        assert source.status == DataSourceStatus.ACTIVE

    def test_multi_type_registry(self):
        """Simulate registry with multiple source types."""
        from app.services.datasources import (
            DataSourceRegistry,
            DataSourceType,
        )

        registry = DataSourceRegistry()

        # Register various types
        registry.register(
            tenant_id="tenant-1",
            name="Main DB",
            source_type=DataSourceType.DATABASE,
        )
        registry.register(
            tenant_id="tenant-1",
            name="Document Store",
            source_type=DataSourceType.DOCUMENT,
        )
        registry.register(
            tenant_id="tenant-1",
            name="File Storage",
            source_type=DataSourceType.FILE,
        )
        registry.register(
            tenant_id="tenant-1",
            name="Vector DB",
            source_type=DataSourceType.VECTOR,
        )
        registry.register(
            tenant_id="tenant-1",
            name="External API",
            source_type=DataSourceType.API,
        )

        stats = registry.get_statistics()
        assert stats.total_sources == 5
        assert stats.sources_by_type["database"] == 1
        assert stats.sources_by_type["vector"] == 1

    def test_tenant_isolation(self):
        """Data sources should be isolated by tenant."""
        from app.services.datasources import (
            DataSourceRegistry,
            DataSourceType,
        )

        registry = DataSourceRegistry()

        for i in range(3):
            registry.register(
                tenant_id="tenant-1",
                name=f"Source {i}",
                source_type=DataSourceType.DATABASE,
            )

        for i in range(2):
            registry.register(
                tenant_id="tenant-2",
                name=f"Source {i}",
                source_type=DataSourceType.DATABASE,
            )

        tenant1_sources = registry.list(tenant_id="tenant-1")
        tenant2_sources = registry.list(tenant_id="tenant-2")

        assert len(tenant1_sources) == 3
        assert len(tenant2_sources) == 2

        # Clear tenant 1
        registry.clear_tenant("tenant-1")

        tenant1_sources = registry.list(tenant_id="tenant-1")
        tenant2_sources = registry.list(tenant_id="tenant-2")

        assert len(tenant1_sources) == 0
        assert len(tenant2_sources) == 2  # Unaffected
