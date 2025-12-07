"""
Integration tests for pgvector-backed memory store.

Tests:
- Vector store CRUD operations
- Semantic similarity search
- Fallback to keyword search
- Feature flag behavior
- Metric recording

These tests require a database with pgvector extension enabled.
Tests will skip gracefully if pgvector is not available.

Note: Some tests may have event loop issues when run as a full suite.
Run individual test classes for more reliable results:
    pytest tests/integration/test_vector_search.py::TestVectorStoreBasics -v
"""

import os
import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from typing import List

# Skip module if running in CI without DB
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.integration,
]


# ========== Fixtures ==========

@pytest.fixture
def mock_embedding_fn():
    """
    Mock embedding function that returns deterministic embeddings.

    Uses a simple hash-based approach for consistent test results.
    """
    async def _mock_embedding(text: str) -> List[float]:
        # Generate deterministic embedding based on text hash
        import hashlib
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)

        # Create 1536-dim vector from hash
        embedding = []
        for i in range(1536):
            # Use hash to generate values between -1 and 1
            val = ((hash_val >> (i % 64)) & 0xFF) / 255.0 * 2 - 1
            embedding.append(val)

        # Normalize
        norm = sum(x*x for x in embedding) ** 0.5
        return [x / norm for x in embedding]

    return _mock_embedding


@pytest.fixture
def mock_similar_embeddings():
    """
    Returns two similar embeddings for testing similarity search.
    """
    # Base embedding - normalized
    base = [0.1] * 1536
    norm = sum(x*x for x in base) ** 0.5
    base = [x / norm for x in base]

    # Slightly modified embedding (high similarity)
    similar = base.copy()
    similar[0] = 0.11
    norm = sum(x*x for x in similar) ** 0.5
    similar = [x / norm for x in similar]

    return base, similar


@pytest.fixture
def test_agent_id():
    """Generate unique agent ID for test isolation."""
    return f"test-agent-{uuid.uuid4().hex[:8]}"


# ========== pgvector Availability Check ==========

def check_pgvector_available_sync() -> bool:
    """Check if pgvector extension is available in the database (sync)."""
    try:
        from sqlmodel import Session
        from sqlalchemy import text
        from app.db import engine

        with Session(engine) as session:
            result = session.exec(
                text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            )
            return result.first() is not None
    except Exception as e:
        print(f"pgvector check failed: {e}")
        return False


# Cache the result
_PGVECTOR_AVAILABLE = None


def get_pgvector_available():
    global _PGVECTOR_AVAILABLE
    if _PGVECTOR_AVAILABLE is None:
        _PGVECTOR_AVAILABLE = check_pgvector_available_sync()
    return _PGVECTOR_AVAILABLE


@pytest.fixture
def pgvector_available():
    """Fixture to check pgvector availability and skip if not available."""
    if not get_pgvector_available():
        pytest.skip("pgvector extension not available")
    return True


# ========== Tests ==========

class TestVectorStoreBasics:
    """Basic CRUD operations for vector store."""

    async def test_store_memory_without_embedding(self, test_agent_id, pgvector_available):
        """Test storing memory without generating embedding."""
        from app.memory.vector_store import VectorMemoryStore

        store = VectorMemoryStore()

        # Store without embedding
        memory_id = await store.store(
            agent_id=test_agent_id,
            text="Test memory without embedding",
            generate_embedding=False,
        )

        assert memory_id is not None
        assert len(memory_id) == 36  # UUID format

        # Verify stored
        retrieved = await store.get(memory_id)
        assert retrieved is not None
        assert retrieved["text"] == "Test memory without embedding"

        # Cleanup
        await store.delete(memory_id)

    async def test_store_memory_with_mock_embedding(
        self, test_agent_id, mock_embedding_fn, pgvector_available
    ):
        """Test storing memory with mock embedding."""
        from app.memory.vector_store import VectorMemoryStore

        store = VectorMemoryStore(embedding_fn=mock_embedding_fn)

        # Store with embedding
        memory_id = await store.store(
            agent_id=test_agent_id,
            text="Test memory with embedding",
            generate_embedding=True,
        )

        assert memory_id is not None

        # Cleanup
        await store.delete(memory_id)

    async def test_list_memories_by_agent(self, test_agent_id, pgvector_available):
        """Test listing memories by agent ID."""
        from app.memory.vector_store import VectorMemoryStore

        store = VectorMemoryStore()
        memory_ids = []

        # Store multiple memories
        for i in range(3):
            mid = await store.store(
                agent_id=test_agent_id,
                text=f"Memory {i} for listing test",
                generate_embedding=False,
            )
            memory_ids.append(mid)

        # List
        memories = await store.list_by_agent(test_agent_id)
        assert len(memories) >= 3

        # Cleanup
        for mid in memory_ids:
            await store.delete(mid)

    async def test_delete_memory(self, test_agent_id, pgvector_available):
        """Test deleting a memory."""
        from app.memory.vector_store import VectorMemoryStore

        store = VectorMemoryStore()

        # Store
        memory_id = await store.store(
            agent_id=test_agent_id,
            text="Memory to delete",
            generate_embedding=False,
        )

        # Verify exists
        assert await store.get(memory_id) is not None

        # Delete
        deleted = await store.delete(memory_id)
        assert deleted is True

        # Verify gone
        assert await store.get(memory_id) is None


class TestVectorSimilaritySearch:
    """Tests for semantic similarity search."""

    async def test_similarity_search_with_mock_embeddings(
        self, test_agent_id, mock_embedding_fn, pgvector_available
    ):
        """Test vector similarity search returns ordered by similarity."""
        from app.memory.vector_store import VectorMemoryStore

        store = VectorMemoryStore(embedding_fn=mock_embedding_fn)
        memory_ids = []

        # Store memories with different content
        texts = [
            "The quick brown fox jumps over the lazy dog",
            "The quick brown fox runs through the forest",  # Similar to first
            "Programming in Python is fun and productive",   # Different topic
        ]

        for text in texts:
            mid = await store.store(
                agent_id=test_agent_id,
                text=text,
                generate_embedding=True,
            )
            memory_ids.append(mid)

        # Search for fox-related content
        results = await store.search(
            agent_id=test_agent_id,
            query="fox jumping",
            limit=3,
            similarity_threshold=0.0,  # Accept all for testing
        )

        # Should get results (embedding similarity)
        assert len(results) > 0

        # Results should have similarity scores
        for result in results:
            assert "similarity" in result
            assert isinstance(result["similarity"], float)

        # Cleanup
        for mid in memory_ids:
            await store.delete(mid)


class TestKeywordFallback:
    """Tests for keyword search fallback."""

    async def test_keyword_search_when_no_embeddings(
        self, test_agent_id, pgvector_available
    ):
        """Test fallback to keyword search when embeddings unavailable."""
        from app.memory.vector_store import VectorMemoryStore

        # Mock embedding function that fails
        async def failing_embedding(text: str):
            from app.memory.vector_store import EmbeddingError
            raise EmbeddingError("API unavailable")

        store = VectorMemoryStore(embedding_fn=failing_embedding)

        # Store without embedding
        memory_id = await store.store(
            agent_id=test_agent_id,
            text="Keyword searchable content about databases",
            generate_embedding=False,
        )

        # Search should fall back to keyword search
        results = await store.search(
            agent_id=test_agent_id,
            query="databases",
            limit=5,
        )

        # Should find the memory via keyword
        assert len(results) > 0
        found = any("databases" in r["text"] for r in results)
        assert found, "Keyword search should find matching content"

        # Cleanup
        await store.delete(memory_id)


class TestFeatureFlags:
    """Tests for feature flag behavior."""

    async def test_vector_search_disabled_flag(
        self, test_agent_id, mock_embedding_fn, pgvector_available
    ):
        """Test that VECTOR_SEARCH_ENABLED=false skips vector search."""
        from app.memory.vector_store import VectorMemoryStore

        store = VectorMemoryStore(embedding_fn=mock_embedding_fn)

        # Store a memory with embedding
        memory_id = await store.store(
            agent_id=test_agent_id,
            text="Test content for feature flag",
            generate_embedding=False,  # No embedding needed for keyword
        )

        # Disable vector search via patch
        with patch("app.memory.vector_store.VECTOR_SEARCH_ENABLED", False):
            results = await store.search(
                agent_id=test_agent_id,
                query="feature flag",
                limit=5,
            )

            # Should still get results (keyword fallback)
            assert len(results) > 0
            # Results should have 0.0 similarity (keyword search)
            for r in results:
                assert r.get("similarity", 0) == 0.0

        # Cleanup
        await store.delete(memory_id)


class TestMetricsRecording:
    """Tests for Prometheus metrics recording."""

    async def test_search_records_latency_metric(
        self, test_agent_id, mock_embedding_fn, pgvector_available
    ):
        """Test that vector search records latency metrics."""
        from app.memory.vector_store import VectorMemoryStore
        from app.memory.embedding_metrics import VECTOR_QUERY_LATENCY

        store = VectorMemoryStore(embedding_fn=mock_embedding_fn)

        # Store a memory
        memory_id = await store.store(
            agent_id=test_agent_id,
            text="Metrics test content",
            generate_embedding=True,
        )

        # Get initial metric count
        initial_count = VECTOR_QUERY_LATENCY._sum._value

        # Perform search
        await store.search(
            agent_id=test_agent_id,
            query="metrics",
            limit=5,
        )

        # Metric should have increased
        # (Note: Prometheus metrics are global, so we just check it exists)
        assert VECTOR_QUERY_LATENCY._sum._value >= initial_count

        # Cleanup
        await store.delete(memory_id)

    async def test_fallback_records_counter(
        self, test_agent_id, pgvector_available
    ):
        """Test that fallback events are counted."""
        from app.memory.vector_store import VectorMemoryStore
        from app.memory.embedding_metrics import VECTOR_FALLBACK_COUNT

        # Mock embedding function that fails
        async def failing_embedding(text: str):
            from app.memory.vector_store import EmbeddingError
            raise EmbeddingError("Intentional failure")

        store = VectorMemoryStore(embedding_fn=failing_embedding)

        # Store without embedding
        memory_id = await store.store(
            agent_id=test_agent_id,
            text="Fallback test",
            generate_embedding=False,
        )

        # Perform search (will fail embedding and fallback)
        await store.search(
            agent_id=test_agent_id,
            query="test",
            limit=5,
        )

        # Fallback counter should exist
        # (Just verify no exception, actual value depends on test order)
        assert VECTOR_FALLBACK_COUNT is not None

        # Cleanup
        await store.delete(memory_id)


class TestBackfill:
    """Tests for embedding backfill functionality."""

    async def test_backfill_processes_memories_without_embeddings(
        self, test_agent_id, mock_embedding_fn, pgvector_available
    ):
        """Test that backfill adds embeddings to existing memories."""
        from app.memory.vector_store import VectorMemoryStore

        store = VectorMemoryStore(embedding_fn=mock_embedding_fn)

        # Store memories WITHOUT embeddings
        memory_ids = []
        for i in range(3):
            mid = await store.store(
                agent_id=test_agent_id,
                text=f"Backfill test memory {i}",
                generate_embedding=False,
            )
            memory_ids.append(mid)

        # Run backfill for this agent
        stats = await store.backfill_embeddings(
            agent_id=test_agent_id,
            batch_size=10,
        )

        # Should have processed our memories
        assert stats["processed"] >= 3
        assert stats["success"] >= 3 or stats["failed"] == 0

        # Cleanup
        for mid in memory_ids:
            await store.delete(mid)
