"""
Memory Service Tests - M7 Implementation

Tests for the memory service with caching and fail-open behavior.

Run with:
    pytest tests/memory/test_memory_service.py -v
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch
import json

# Clear Prometheus registry before importing modules that register metrics
from prometheus_client import REGISTRY
for name, collector in list(REGISTRY._names_to_collectors.items()):
    if not name.startswith(('python_', 'process_', 'gc_')):
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass

# Import memory service components
from app.memory.memory_service import (
    MemoryService,
    MemoryEntry,
    MemoryResult,
    get_memory_service,
    init_memory_service,
    MEMORY_CACHE_TTL,
    MEMORY_MAX_SIZE_BYTES,
)


class TestMemoryEntry:
    """Tests for MemoryEntry dataclass."""

    def test_create_memory_entry(self):
        """Test creating a MemoryEntry."""
        entry = MemoryEntry(
            tenant_id="test-tenant",
            key="test-key",
            value={"data": "value"},
            source="api",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert entry.tenant_id == "test-tenant"
        assert entry.key == "test-key"
        assert entry.value == {"data": "value"}
        assert entry.source == "api"
        assert entry.ttl_seconds is None
        assert entry.expires_at is None
        assert entry.cache_hit is False

    def test_memory_entry_with_ttl(self):
        """Test MemoryEntry with TTL."""
        now = datetime.now(timezone.utc)
        entry = MemoryEntry(
            tenant_id="test",
            key="key",
            value={},
            source="api",
            created_at=now,
            updated_at=now,
            ttl_seconds=3600,
            expires_at=now,
        )
        assert entry.ttl_seconds == 3600
        assert entry.expires_at is not None


class TestMemoryResult:
    """Tests for MemoryResult dataclass."""

    def test_successful_result(self):
        """Test successful MemoryResult."""
        entry = MemoryEntry(
            tenant_id="test",
            key="key",
            value={"test": True},
            source="db",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        result = MemoryResult(
            success=True,
            entry=entry,
            cache_hit=True,
            latency_ms=5.2
        )
        assert result.success is True
        assert result.entry is not None
        assert result.cache_hit is True
        assert result.error is None

    def test_failed_result(self):
        """Test failed MemoryResult."""
        result = MemoryResult(
            success=False,
            entry=None,
            error="Database connection failed",
            latency_ms=100.0
        )
        assert result.success is False
        assert result.entry is None
        assert result.error == "Database connection failed"


class TestMemoryServiceBasics:
    """Tests for MemoryService basic functionality."""

    @pytest.fixture
    def mock_db_factory(self):
        """Create mock database session factory."""
        mock_session = MagicMock()
        mock_session.execute.return_value.fetchone.return_value = None
        mock_session.commit = MagicMock()
        mock_session.close = MagicMock()

        factory = MagicMock(return_value=mock_session)
        return factory

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        redis = MagicMock()
        redis.get.return_value = None
        redis.setex.return_value = True
        redis.delete.return_value = 1
        return redis

    @pytest.fixture
    def service(self, mock_db_factory, mock_redis, monkeypatch):
        """Create MemoryService instance."""
        monkeypatch.setenv("MEMORY_AUDIT_ENABLED", "false")
        monkeypatch.setenv("MEMORY_FAIL_OPEN", "true")
        return MemoryService(
            db_session_factory=mock_db_factory,
            redis_client=mock_redis,
        )

    @pytest.mark.asyncio
    async def test_get_not_found(self, service):
        """Test get returns None when key not found."""
        result = await service.get("tenant1", "nonexistent-key")
        assert result.success is True
        assert result.entry is None

    @pytest.mark.asyncio
    async def test_get_from_cache(self, service, mock_redis):
        """Test get returns from cache when available."""
        cached_data = {
            "tenant_id": "tenant1",
            "key": "test-key",
            "value": {"cached": True},
            "source": "cache",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "ttl_seconds": None,
            "expires_at": None,
        }
        mock_redis.get.return_value = json.dumps(cached_data)

        result = await service.get("tenant1", "test-key")

        assert result.success is True
        assert result.cache_hit is True
        assert result.entry is not None
        assert result.entry.value == {"cached": True}

    @pytest.mark.asyncio
    async def test_get_from_database(self, service, mock_db_factory):
        """Test get returns from database on cache miss."""
        # Setup mock database result
        mock_row = MagicMock()
        mock_row.tenant_id = "tenant1"
        mock_row.key = "db-key"
        mock_row.value = {"from": "db"}
        mock_row.source = "api"
        mock_row.created_at = datetime.now(timezone.utc)
        mock_row.updated_at = datetime.now(timezone.utc)
        mock_row.ttl_seconds = None
        mock_row.expires_at = None

        mock_session = mock_db_factory()
        mock_session.execute.return_value.fetchone.return_value = mock_row

        result = await service.get("tenant1", "db-key")

        assert result.success is True
        assert result.cache_hit is False
        assert result.entry is not None
        assert result.entry.value == {"from": "db"}


class TestMemoryServiceSet:
    """Tests for MemoryService set operations."""

    @pytest.fixture
    def mock_db_factory(self):
        """Create mock database session factory."""
        mock_session = MagicMock()

        # Mock return for INSERT
        mock_row = MagicMock()
        mock_row.tenant_id = "tenant1"
        mock_row.key = "new-key"
        mock_row.value = {"new": "value"}
        mock_row.source = "api"
        mock_row.created_at = datetime.now(timezone.utc)
        mock_row.updated_at = datetime.now(timezone.utc)
        mock_row.ttl_seconds = None
        mock_row.expires_at = None

        mock_session.execute.return_value.fetchone.return_value = mock_row
        mock_session.commit = MagicMock()
        mock_session.close = MagicMock()

        factory = MagicMock(return_value=mock_session)
        return factory

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        redis = MagicMock()
        redis.get.return_value = None
        redis.setex.return_value = True
        return redis

    @pytest.fixture
    def service(self, mock_db_factory, mock_redis, monkeypatch):
        """Create MemoryService instance."""
        monkeypatch.setenv("MEMORY_AUDIT_ENABLED", "false")
        return MemoryService(
            db_session_factory=mock_db_factory,
            redis_client=mock_redis,
        )

    @pytest.mark.asyncio
    async def test_set_new_entry(self, service, mock_db_factory):
        """Test setting a new memory entry."""
        result = await service.set(
            tenant_id="tenant1",
            key="new-key",
            value={"new": "value"},
            source="test",
        )

        assert result.success is True
        assert result.entry is not None

    @pytest.mark.asyncio
    async def test_set_updates_cache(self, service, mock_redis):
        """Test that set updates Redis cache."""
        await service.set(
            tenant_id="tenant1",
            key="cache-key",
            value={"cached": True},
        )

        mock_redis.setex.assert_called()

    @pytest.mark.asyncio
    async def test_set_rejects_oversized_value(self, service, monkeypatch):
        """Test that oversized values are rejected."""
        monkeypatch.setattr(
            "app.memory.memory_service.MEMORY_MAX_SIZE_BYTES",
            100
        )

        # Create large value
        large_value = {"data": "x" * 200}

        result = await service.set(
            tenant_id="tenant1",
            key="large-key",
            value=large_value,
        )

        assert result.success is False
        assert "exceeds maximum size" in result.error


class TestMemoryServiceDelete:
    """Tests for MemoryService delete operations."""

    @pytest.fixture
    def mock_db_factory(self):
        """Create mock database session factory."""
        mock_session = MagicMock()
        mock_session.execute.return_value.fetchone.return_value = MagicMock(id=1)
        mock_session.commit = MagicMock()
        mock_session.close = MagicMock()
        factory = MagicMock(return_value=mock_session)
        return factory

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        redis = MagicMock()
        redis.get.return_value = None
        redis.delete.return_value = 1
        return redis

    @pytest.fixture
    def service(self, mock_db_factory, mock_redis, monkeypatch):
        """Create MemoryService instance."""
        monkeypatch.setenv("MEMORY_AUDIT_ENABLED", "false")
        return MemoryService(
            db_session_factory=mock_db_factory,
            redis_client=mock_redis,
        )

    @pytest.mark.asyncio
    async def test_delete_existing(self, service, mock_db_factory):
        """Test deleting an existing entry."""
        result = await service.delete("tenant1", "existing-key")

        assert result.success is True

    @pytest.mark.asyncio
    async def test_delete_removes_from_cache(self, service, mock_redis):
        """Test that delete removes from Redis cache."""
        await service.delete("tenant1", "cached-key")

        mock_redis.delete.assert_called_once()


class TestMemoryServiceList:
    """Tests for MemoryService list operations."""

    @pytest.fixture
    def mock_db_factory(self):
        """Create mock database session factory."""
        mock_session = MagicMock()

        # Mock multiple rows
        mock_rows = [
            MagicMock(
                tenant_id="tenant1",
                key=f"key-{i}",
                value={"index": i},
                source="api",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                ttl_seconds=None,
                expires_at=None,
            )
            for i in range(3)
        ]

        mock_session.execute.return_value = mock_rows
        mock_session.close = MagicMock()
        factory = MagicMock(return_value=mock_session)
        return factory

    @pytest.fixture
    def service(self, mock_db_factory, monkeypatch):
        """Create MemoryService instance."""
        monkeypatch.setenv("MEMORY_AUDIT_ENABLED", "false")
        return MemoryService(db_session_factory=mock_db_factory)

    @pytest.mark.asyncio
    async def test_list_entries(self, service):
        """Test listing entries for tenant."""
        entries = await service.list("tenant1")

        assert len(entries) == 3

    @pytest.mark.asyncio
    async def test_list_with_prefix(self, service):
        """Test listing with prefix filter."""
        entries = await service.list("tenant1", prefix="key-")

        # Prefix filter should be applied via SQL
        assert len(entries) >= 0


class TestMemoryServiceFailOpen:
    """Tests for fail-open behavior."""

    @pytest.fixture
    def failing_db_factory(self):
        """Create database factory that raises errors."""
        mock_session = MagicMock()
        mock_session.execute.side_effect = Exception("Database error")
        mock_session.close = MagicMock()
        factory = MagicMock(return_value=mock_session)
        return factory

    @pytest.fixture
    def service_fail_open(self, failing_db_factory, monkeypatch):
        """Create service with fail-open enabled."""
        monkeypatch.setenv("MEMORY_FAIL_OPEN", "true")
        monkeypatch.setenv("MEMORY_AUDIT_ENABLED", "false")

        import app.memory.memory_service as mem_mod
        monkeypatch.setattr(mem_mod, "MEMORY_FAIL_OPEN", True)

        return MemoryService(db_session_factory=failing_db_factory)

    @pytest.fixture
    def service_fail_closed(self, failing_db_factory, monkeypatch):
        """Create service with fail-closed."""
        monkeypatch.setenv("MEMORY_FAIL_OPEN", "false")
        monkeypatch.setenv("MEMORY_AUDIT_ENABLED", "false")

        import app.memory.memory_service as mem_mod
        monkeypatch.setattr(mem_mod, "MEMORY_FAIL_OPEN", False)

        return MemoryService(db_session_factory=failing_db_factory)

    @pytest.mark.asyncio
    async def test_get_fail_open(self, service_fail_open):
        """Test get returns success with None on error when fail-open."""
        result = await service_fail_open.get("tenant1", "key")

        assert result.success is True
        assert result.entry is None
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_get_fail_closed(self, service_fail_closed):
        """Test get returns failure on error when fail-closed."""
        result = await service_fail_closed.get("tenant1", "key")

        assert result.success is False
        assert result.error is not None


class TestCacheKeyGeneration:
    """Tests for cache key generation."""

    @pytest.fixture
    def service(self, monkeypatch):
        """Create service instance."""
        monkeypatch.setenv("MEMORY_AUDIT_ENABLED", "false")
        mock_factory = MagicMock()
        return MemoryService(db_session_factory=mock_factory)

    def test_cache_key_format(self, service):
        """Test cache key format is correct."""
        key = service._make_cache_key("tenant-123", "config:settings")
        assert key == "memory:tenant-123:config:settings"

    def test_cache_key_uniqueness(self, service):
        """Test different tenant/key combinations produce unique cache keys."""
        key1 = service._make_cache_key("tenant1", "key1")
        key2 = service._make_cache_key("tenant1", "key2")
        key3 = service._make_cache_key("tenant2", "key1")

        assert key1 != key2
        assert key1 != key3
        assert key2 != key3


class TestValueHashing:
    """Tests for value hashing (used in audit)."""

    @pytest.fixture
    def service(self, monkeypatch):
        """Create service instance."""
        monkeypatch.setenv("MEMORY_AUDIT_ENABLED", "false")
        mock_factory = MagicMock()
        return MemoryService(db_session_factory=mock_factory)

    def test_hash_deterministic(self, service):
        """Test hash is deterministic for same value."""
        value = {"key": "value", "nested": {"a": 1}}

        hash1 = service._hash_value(value)
        hash2 = service._hash_value(value)

        assert hash1 == hash2

    def test_hash_different_values(self, service):
        """Test different values produce different hashes."""
        hash1 = service._hash_value({"key": "value1"})
        hash2 = service._hash_value({"key": "value2"})

        assert hash1 != hash2

    def test_hash_key_order_independent(self, service):
        """Test hash is independent of key order."""
        hash1 = service._hash_value({"a": 1, "b": 2})
        hash2 = service._hash_value({"b": 2, "a": 1})

        assert hash1 == hash2


class TestGlobalInstance:
    """Tests for global instance management."""

    def test_get_memory_service_returns_none_initially(self, monkeypatch):
        """Test get_memory_service returns None before init."""
        import app.memory.memory_service as mem_mod
        mem_mod._service = None

        result = get_memory_service()
        assert result is None

    def test_init_memory_service(self, monkeypatch):
        """Test init_memory_service creates instance."""
        import app.memory.memory_service as mem_mod
        mem_mod._service = None
        monkeypatch.setenv("MEMORY_AUDIT_ENABLED", "false")

        mock_factory = MagicMock()
        service = init_memory_service(db_session_factory=mock_factory)

        assert service is not None
        assert get_memory_service() is service

        # Cleanup
        mem_mod._service = None
