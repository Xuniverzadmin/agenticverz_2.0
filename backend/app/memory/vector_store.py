# Vector Memory Store with pgvector
"""
pgvector-backed memory store for semantic search.

Features:
- Embeddings via OpenAI or Anthropic (Voyage)
- HNSW index for fast approximate nearest neighbor search
- Hybrid search (vector + keyword fallback)
- Async support

Usage:
    from app.memory.vector_store import get_vector_memory_store

    store = get_vector_memory_store()

    # Store with auto-embedding
    memory_id = await store.store(
        agent_id="agent-123",
        text="Important information about the project",
    )

    # Semantic search
    results = await store.search(
        agent_id="agent-123",
        query="project details",
        limit=5,
    )
"""

import os
import logging
import hashlib
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

import httpx
from sqlalchemy import text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_async import AsyncSessionLocal, async_session_context
from app.memory.embedding_metrics import (
    VECTOR_SEARCH_ENABLED,
    VECTOR_SEARCH_FALLBACK,
    VECTOR_QUERY_LATENCY,
    VECTOR_QUERY_RESULTS,
    VECTOR_FALLBACK_COUNT,
    EMBEDDING_API_CALLS,
    EMBEDDING_API_LATENCY,
    EMBEDDING_ERRORS,
    check_embedding_quota,
    increment_embedding_count,
)

logger = logging.getLogger("nova.memory.vector_store")

# Embedding configuration
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")  # openai or anthropic
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""
    pass


async def get_embedding_openai(text: str) -> List[float]:
    """Get embedding from OpenAI API."""
    if not OPENAI_API_KEY:
        raise EmbeddingError("OPENAI_API_KEY not set")

    # Check quota before making API call
    if not check_embedding_quota():
        raise EmbeddingError("Daily embedding quota exceeded")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": EMBEDDING_MODEL,
                "input": text[:8000],  # Truncate to avoid token limits
            },
        )

        if response.status_code != 200:
            raise EmbeddingError(f"OpenAI API error: {response.status_code} - {response.text}")

        # Increment quota counter on success
        increment_embedding_count()

        data = response.json()
        return data["data"][0]["embedding"]


async def get_embedding_anthropic(text: str) -> List[float]:
    """Get embedding from Anthropic Voyage API."""
    if not ANTHROPIC_API_KEY:
        raise EmbeddingError("ANTHROPIC_API_KEY not set")

    # Anthropic uses Voyage for embeddings
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.voyageai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {os.getenv('VOYAGE_API_KEY', '')}",
                "Content-Type": "application/json",
            },
            json={
                "model": "voyage-2",
                "input": text[:8000],
            },
        )

        if response.status_code != 200:
            raise EmbeddingError(f"Voyage API error: {response.status_code}")

        data = response.json()
        return data["data"][0]["embedding"]


async def get_embedding(text: str) -> List[float]:
    """Get embedding using configured provider."""
    if EMBEDDING_PROVIDER == "anthropic":
        return await get_embedding_anthropic(text)
    else:
        return await get_embedding_openai(text)


def compute_text_hash(text: str) -> str:
    """Compute hash of text for deduplication."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


class VectorMemoryStore:
    """
    pgvector-backed memory store with semantic search.

    Uses HNSW index for fast approximate nearest neighbor queries.
    """

    def __init__(self, embedding_fn=None):
        """
        Initialize vector store.

        Args:
            embedding_fn: Optional custom embedding function
        """
        self._embedding_fn = embedding_fn or get_embedding
        logger.info(f"VectorMemoryStore initialized (provider={EMBEDDING_PROVIDER})")

    async def store(
        self,
        agent_id: str,
        text: str,
        memory_type: str = "general",
        meta: Optional[Dict[str, Any]] = None,
        generate_embedding: bool = True,
    ) -> str:
        """
        Store a memory with optional embedding.

        Args:
            agent_id: Agent identifier
            text: Memory text content
            memory_type: Type classification
            meta: Additional metadata
            generate_embedding: Whether to generate embedding (default True)

        Returns:
            Memory ID
        """
        import json
        import uuid

        memory_id = str(uuid.uuid4())
        meta_json = json.dumps(meta) if meta else None

        # Generate embedding
        embedding = None
        if generate_embedding and text.strip():
            try:
                embedding = await self._embedding_fn(text)
                logger.debug(f"Generated embedding for memory {memory_id[:8]}")
            except EmbeddingError as e:
                logger.warning(f"Embedding generation failed: {e}")
                # Continue without embedding - will use keyword search

        async with async_session_context() as session:
            if embedding:
                # Insert with embedding
                await session.execute(
                    sql_text("""
                        INSERT INTO memories (id, agent_id, memory_type, text, meta, embedding, created_at)
                        VALUES (:id, :agent_id, :memory_type, :text, :meta, CAST(:embedding AS vector), :created_at)
                    """),
                    {
                        "id": memory_id,
                        "agent_id": agent_id,
                        "memory_type": memory_type,
                        "text": text,
                        "meta": meta_json,
                        "embedding": f"[{','.join(str(x) for x in embedding)}]",
                        "created_at": datetime.utcnow(),
                    }
                )
            else:
                # Insert without embedding
                await session.execute(
                    sql_text("""
                        INSERT INTO memories (id, agent_id, memory_type, text, meta, created_at)
                        VALUES (:id, :agent_id, :memory_type, :text, :meta, :created_at)
                    """),
                    {
                        "id": memory_id,
                        "agent_id": agent_id,
                        "memory_type": memory_type,
                        "text": text,
                        "meta": meta_json,
                        "created_at": datetime.utcnow(),
                    }
                )

            await session.commit()

        logger.debug(
            "memory_stored",
            extra={
                "memory_id": memory_id,
                "agent_id": agent_id,
                "has_embedding": embedding is not None,
            }
        )

        return memory_id

    async def search(
        self,
        agent_id: str,
        query: str,
        limit: int = 10,
        similarity_threshold: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for memories.

        Uses vector similarity when embeddings are available,
        falls back to keyword search otherwise.

        Args:
            agent_id: Agent to search memories for
            query: Search query
            limit: Maximum results
            similarity_threshold: Minimum cosine similarity (0-1)

        Returns:
            List of matching memories with similarity scores
        """
        import json
        import time

        # Feature flag check - skip vector search if disabled
        if not VECTOR_SEARCH_ENABLED:
            logger.debug("Vector search disabled via feature flag, using keyword search")
            VECTOR_FALLBACK_COUNT.labels(reason="disabled").inc()
            return await self._keyword_search(agent_id, query, limit)

        start_time = time.perf_counter()

        # Generate query embedding
        try:
            query_embedding = await self._embedding_fn(query)
        except EmbeddingError as e:
            logger.warning(f"Query embedding failed, using keyword search: {e}")
            VECTOR_FALLBACK_COUNT.labels(reason="no_embedding").inc()
            if VECTOR_SEARCH_FALLBACK:
                return await self._keyword_search(agent_id, query, limit)
            return []

        async with async_session_context() as session:
            # Vector similarity search using cosine distance
            # 1 - cosine_distance = cosine_similarity
            result = await session.execute(
                sql_text("""
                    SELECT
                        id,
                        agent_id,
                        memory_type,
                        text,
                        meta,
                        created_at,
                        1 - (embedding <=> CAST(:query_embedding AS vector)) as similarity
                    FROM memories
                    WHERE agent_id = :agent_id
                        AND embedding IS NOT NULL
                        AND 1 - (embedding <=> CAST(:query_embedding AS vector)) >= :threshold
                    ORDER BY embedding <=> CAST(:query_embedding AS vector)
                    LIMIT :limit
                """),
                {
                    "agent_id": agent_id,
                    "query_embedding": f"[{','.join(str(x) for x in query_embedding)}]",
                    "threshold": similarity_threshold,
                    "limit": limit,
                }
            )

            rows = result.fetchall()

            # Track query latency
            latency = time.perf_counter() - start_time
            VECTOR_QUERY_LATENCY.observe(latency)

            if not rows:
                # Fall back to keyword search if no vector matches
                logger.debug("No vector matches, falling back to keyword search")
                VECTOR_FALLBACK_COUNT.labels(reason="below_threshold").inc()
                if VECTOR_SEARCH_FALLBACK:
                    return await self._keyword_search(agent_id, query, limit)
                return []

            # Track results count
            VECTOR_QUERY_RESULTS.observe(len(rows))

            return [
                {
                    "id": row.id,
                    "agent_id": row.agent_id,
                    "memory_type": row.memory_type,
                    "text": row.text,
                    "meta": json.loads(row.meta) if row.meta else None,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "similarity": float(row.similarity),
                }
                for row in rows
            ]

    async def _keyword_search(
        self,
        agent_id: str,
        query: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        """Fallback keyword search using ILIKE."""
        import json

        async with async_session_context() as session:
            result = await session.execute(
                sql_text("""
                    SELECT id, agent_id, memory_type, text, meta, created_at
                    FROM memories
                    WHERE agent_id = :agent_id
                        AND text ILIKE :pattern
                    ORDER BY created_at DESC
                    LIMIT :limit
                """),
                {
                    "agent_id": agent_id,
                    "pattern": f"%{query}%",
                    "limit": limit,
                }
            )

            rows = result.fetchall()

            return [
                {
                    "id": row.id,
                    "agent_id": row.agent_id,
                    "memory_type": row.memory_type,
                    "text": row.text,
                    "meta": json.loads(row.meta) if row.meta else None,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "similarity": 0.0,  # No similarity score for keyword search
                }
                for row in rows
            ]

    async def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get a memory by ID."""
        import json

        async with async_session_context() as session:
            result = await session.execute(
                sql_text("""
                    SELECT id, agent_id, memory_type, text, meta, created_at
                    FROM memories
                    WHERE id = :id
                """),
                {"id": memory_id}
            )

            row = result.fetchone()
            if not row:
                return None

            return {
                "id": row.id,
                "agent_id": row.agent_id,
                "memory_type": row.memory_type,
                "text": row.text,
                "meta": json.loads(row.meta) if row.meta else None,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }

    async def list_by_agent(
        self,
        agent_id: str,
        memory_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List memories for an agent."""
        import json

        async with async_session_context() as session:
            if memory_type:
                result = await session.execute(
                    sql_text("""
                        SELECT id, agent_id, memory_type, text, meta, created_at
                        FROM memories
                        WHERE agent_id = :agent_id AND memory_type = :memory_type
                        ORDER BY created_at DESC
                        LIMIT :limit OFFSET :offset
                    """),
                    {
                        "agent_id": agent_id,
                        "memory_type": memory_type,
                        "limit": limit,
                        "offset": offset,
                    }
                )
            else:
                result = await session.execute(
                    sql_text("""
                        SELECT id, agent_id, memory_type, text, meta, created_at
                        FROM memories
                        WHERE agent_id = :agent_id
                        ORDER BY created_at DESC
                        LIMIT :limit OFFSET :offset
                    """),
                    {
                        "agent_id": agent_id,
                        "limit": limit,
                        "offset": offset,
                    }
                )

            rows = result.fetchall()

            return [
                {
                    "id": row.id,
                    "agent_id": row.agent_id,
                    "memory_type": row.memory_type,
                    "text": row.text,
                    "meta": json.loads(row.meta) if row.meta else None,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in rows
            ]

    async def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        async with async_session_context() as session:
            result = await session.execute(
                sql_text("DELETE FROM memories WHERE id = :id RETURNING id"),
                {"id": memory_id}
            )
            deleted = result.fetchone() is not None
            await session.commit()
            return deleted

    async def backfill_embeddings(
        self,
        agent_id: Optional[str] = None,
        batch_size: int = 100,
    ) -> Dict[str, int]:
        """
        Backfill embeddings for existing memories.

        Args:
            agent_id: Optionally limit to specific agent
            batch_size: Number of records per batch

        Returns:
            Stats dict with processed, success, failed counts
        """
        stats = {"processed": 0, "success": 0, "failed": 0}

        async with async_session_context() as session:
            # Get memories without embeddings
            if agent_id:
                result = await session.execute(
                    sql_text("""
                        SELECT id, text FROM memories
                        WHERE agent_id = :agent_id AND embedding IS NULL
                        LIMIT :limit
                    """),
                    {"agent_id": agent_id, "limit": batch_size}
                )
            else:
                result = await session.execute(
                    sql_text("""
                        SELECT id, text FROM memories
                        WHERE embedding IS NULL
                        LIMIT :limit
                    """),
                    {"limit": batch_size}
                )

            rows = result.fetchall()

            for row in rows:
                stats["processed"] += 1
                try:
                    if row.text and row.text.strip():
                        embedding = await self._embedding_fn(row.text)
                        await session.execute(
                            sql_text("""
                                UPDATE memories
                                SET embedding = CAST(:embedding AS vector)
                                WHERE id = :id
                            """),
                            {
                                "id": row.id,
                                "embedding": f"[{','.join(str(x) for x in embedding)}]",
                            }
                        )
                        stats["success"] += 1
                except Exception as e:
                    logger.warning(f"Failed to backfill embedding for {row.id}: {e}")
                    stats["failed"] += 1

            await session.commit()

        logger.info(f"Backfill complete: {stats}")
        return stats


# Singleton instance
_vector_store: Optional[VectorMemoryStore] = None


def get_vector_memory_store() -> VectorMemoryStore:
    """Get the singleton vector memory store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorMemoryStore()
    return _vector_store
