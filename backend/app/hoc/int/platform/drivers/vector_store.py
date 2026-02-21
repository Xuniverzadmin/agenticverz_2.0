# capability_id: CAP-012
# Layer: L6 — Domain Driver
# AUDIENCE: INTERNAL
# Role: pgvector-backed memory store for semantic search.
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

import hashlib
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import text as sql_text

from app.db_async import async_session_context
from app.memory.embedding_metrics import (
    EMBEDDING_API_CALLS,
    EMBEDDING_API_LATENCY,
    EMBEDDING_ERRORS,
    VECTOR_FALLBACK_COUNT,
    VECTOR_QUERY_LATENCY,
    VECTOR_QUERY_RESULTS,
    VECTOR_SEARCH_ENABLED,
    VECTOR_SEARCH_FALLBACK,
    check_embedding_quota,
    increment_embedding_count,
)
from app.security.sanitize import sanitize_for_embedding

logger = logging.getLogger("nova.memory.vector_store")

# Embedding configuration
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")  # openai or voyage
EMBEDDING_BACKUP_PROVIDER = os.getenv("EMBEDDING_BACKUP_PROVIDER", "voyage")  # fallback provider
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
VOYAGE_MODEL = os.getenv("VOYAGE_MODEL", "voyage-3-lite")  # voyage-3, voyage-3-lite, voyage-code-3
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
EMBEDDING_FALLBACK_ENABLED = os.getenv("EMBEDDING_FALLBACK_ENABLED", "true").lower() == "true"


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""

    pass


async def get_embedding_openai(text: str) -> List[float]:
    """Get embedding from OpenAI API."""
    import time

    if not OPENAI_API_KEY:
        raise EmbeddingError("OPENAI_API_KEY not set")

    # Check quota before making API call
    if not check_embedding_quota():
        raise EmbeddingError("Daily embedding quota exceeded")

    start_time = time.perf_counter()

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
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

            latency = time.perf_counter() - start_time
            EMBEDDING_API_LATENCY.labels(provider="openai").observe(latency)

            if response.status_code == 429:
                EMBEDDING_ERRORS.labels(provider="openai", error_type="rate_limit").inc()
                raise EmbeddingError("OpenAI API rate limited")
            elif response.status_code == 401:
                EMBEDDING_ERRORS.labels(provider="openai", error_type="auth").inc()
                raise EmbeddingError("OpenAI API authentication failed")
            elif response.status_code != 200:
                EMBEDDING_ERRORS.labels(provider="openai", error_type="other").inc()
                raise EmbeddingError(f"OpenAI API error: {response.status_code} - {response.text}")

            # Increment quota counter on success
            increment_embedding_count()
            EMBEDDING_API_CALLS.labels(provider="openai", status="success").inc()

            data = response.json()
            return data["data"][0]["embedding"]

        except httpx.TimeoutException:
            EMBEDDING_ERRORS.labels(provider="openai", error_type="timeout").inc()
            raise EmbeddingError("OpenAI API timeout")


async def get_embedding_voyage(text: str) -> List[float]:
    """
    Get embedding from Voyage AI API.

    Voyage AI (https://www.voyageai.com/) provides high-quality embeddings
    optimized for retrieval tasks.

    Models:
    - voyage-3: Best quality, 1024 dimensions
    - voyage-3-lite: Faster, 512 dimensions
    - voyage-code-3: Optimized for code
    """
    import time

    if not VOYAGE_API_KEY:
        raise EmbeddingError("VOYAGE_API_KEY not set")

    # Check quota before making API call
    if not check_embedding_quota():
        raise EmbeddingError("Daily embedding quota exceeded")

    start_time = time.perf_counter()

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                "https://api.voyageai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {VOYAGE_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": VOYAGE_MODEL,
                    "input": text[:8000],  # Truncate to avoid token limits
                    "input_type": "document",
                },
            )

            latency = time.perf_counter() - start_time
            EMBEDDING_API_LATENCY.labels(provider="voyage").observe(latency)

            if response.status_code == 429:
                EMBEDDING_ERRORS.labels(provider="voyage", error_type="rate_limit").inc()
                raise EmbeddingError("Voyage API rate limited")
            elif response.status_code == 401:
                EMBEDDING_ERRORS.labels(provider="voyage", error_type="auth").inc()
                raise EmbeddingError("Voyage API authentication failed")
            elif response.status_code != 200:
                EMBEDDING_ERRORS.labels(provider="voyage", error_type="other").inc()
                raise EmbeddingError(f"Voyage API error: {response.status_code} - {response.text}")

            # Increment quota counter on success
            increment_embedding_count()
            EMBEDDING_API_CALLS.labels(provider="voyage", status="success").inc()

            data = response.json()
            return data["data"][0]["embedding"]

        except httpx.TimeoutException:
            EMBEDDING_ERRORS.labels(provider="voyage", error_type="timeout").inc()
            raise EmbeddingError("Voyage API timeout")


async def get_embedding(text: str, allow_fallback: bool = True, use_cache: bool = True) -> List[float]:
    """
    Get embedding using configured provider with automatic fallback and caching.

    Args:
        text: Text to embed
        allow_fallback: Whether to try backup provider on failure
        use_cache: Whether to use cache layer

    Returns:
        Embedding vector

    Raises:
        EmbeddingError: If all providers fail
    """
    from app.memory.embedding_cache import get_embedding_cache

    # Check cache first
    if use_cache:
        cache = get_embedding_cache()
        model = EMBEDDING_MODEL if EMBEDDING_PROVIDER == "openai" else VOYAGE_MODEL
        cached = await cache.get(text, model=model, provider=EMBEDDING_PROVIDER)
        if cached is not None:
            return cached

    providers = [EMBEDDING_PROVIDER]
    if EMBEDDING_FALLBACK_ENABLED and allow_fallback and EMBEDDING_BACKUP_PROVIDER:
        providers.append(EMBEDDING_BACKUP_PROVIDER)

    last_error = None

    for provider in providers:
        try:
            if provider == "voyage":
                embedding = await get_embedding_voyage(text)
            else:  # default to openai
                embedding = await get_embedding_openai(text)

            # Cache the result
            if use_cache:
                model = VOYAGE_MODEL if provider == "voyage" else EMBEDDING_MODEL
                await cache.set(text, embedding, model=model)

            return embedding

        except EmbeddingError as e:
            last_error = e
            if provider == EMBEDDING_PROVIDER and len(providers) > 1:
                logger.warning(f"Primary provider {provider} failed ({e}), trying backup {EMBEDDING_BACKUP_PROVIDER}")
                continue
            raise

    # Should not reach here, but just in case
    raise last_error or EmbeddingError("No embedding providers available")


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

        # Generate embedding with sanitization (PIN-052)
        embedding = None
        if generate_embedding and text.strip():
            try:
                # Sanitize text before embedding to prevent secret leakage
                sanitized_text = sanitize_for_embedding(text)
                embedding = await self._embedding_fn(sanitized_text)
                logger.debug(f"Generated embedding for memory {memory_id[:8]}")
            except EmbeddingError as e:
                logger.warning(f"Embedding generation failed: {e}")
                # Continue without embedding - will use keyword search

        async with async_session_context() as session:
            if embedding:
                # Insert with embedding
                await session.execute(
                    sql_text(
                        """
                        INSERT INTO memories (id, agent_id, memory_type, text, meta, embedding, created_at)
                        VALUES (:id, :agent_id, :memory_type, :text, :meta, CAST(:embedding AS vector), :created_at)
                    """
                    ),
                    {
                        "id": memory_id,
                        "agent_id": agent_id,
                        "memory_type": memory_type,
                        "text": text,
                        "meta": meta_json,
                        "embedding": f"[{','.join(str(x) for x in embedding)}]",
                        "created_at": datetime.utcnow(),
                    },
                )
            else:
                # Insert without embedding
                await session.execute(
                    sql_text(
                        """
                        INSERT INTO memories (id, agent_id, memory_type, text, meta, created_at)
                        VALUES (:id, :agent_id, :memory_type, :text, :meta, :created_at)
                    """
                    ),
                    {
                        "id": memory_id,
                        "agent_id": agent_id,
                        "memory_type": memory_type,
                        "text": text,
                        "meta": meta_json,
                        "created_at": datetime.utcnow(),
                    },
                )

            await session.commit()

        logger.debug(
            "memory_stored",
            extra={
                "memory_id": memory_id,
                "agent_id": agent_id,
                "has_embedding": embedding is not None,
            },
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

        # Generate query embedding (sanitize query for consistency - PIN-052)
        try:
            sanitized_query = sanitize_for_embedding(query)
            query_embedding = await self._embedding_fn(sanitized_query)
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
                sql_text(
                    """
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
                """
                ),
                {
                    "agent_id": agent_id,
                    "query_embedding": f"[{','.join(str(x) for x in query_embedding)}]",
                    "threshold": similarity_threshold,
                    "limit": limit,
                },
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
                sql_text(
                    """
                    SELECT id, agent_id, memory_type, text, meta, created_at
                    FROM memories
                    WHERE agent_id = :agent_id
                        AND text ILIKE :pattern
                    ORDER BY created_at DESC
                    LIMIT :limit
                """
                ),
                {
                    "agent_id": agent_id,
                    "pattern": f"%{query}%",
                    "limit": limit,
                },
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
                sql_text(
                    """
                    SELECT id, agent_id, memory_type, text, meta, created_at
                    FROM memories
                    WHERE id = :id
                """
                ),
                {"id": memory_id},
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
                    sql_text(
                        """
                        SELECT id, agent_id, memory_type, text, meta, created_at
                        FROM memories
                        WHERE agent_id = :agent_id AND memory_type = :memory_type
                        ORDER BY created_at DESC
                        LIMIT :limit OFFSET :offset
                    """
                    ),
                    {
                        "agent_id": agent_id,
                        "memory_type": memory_type,
                        "limit": limit,
                        "offset": offset,
                    },
                )
            else:
                result = await session.execute(
                    sql_text(
                        """
                        SELECT id, agent_id, memory_type, text, meta, created_at
                        FROM memories
                        WHERE agent_id = :agent_id
                        ORDER BY created_at DESC
                        LIMIT :limit OFFSET :offset
                    """
                    ),
                    {
                        "agent_id": agent_id,
                        "limit": limit,
                        "offset": offset,
                    },
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
                sql_text("DELETE FROM memories WHERE id = :id RETURNING id"), {"id": memory_id}
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
                    sql_text(
                        """
                        SELECT id, text FROM memories
                        WHERE agent_id = :agent_id AND embedding IS NULL
                        LIMIT :limit
                    """
                    ),
                    {"agent_id": agent_id, "limit": batch_size},
                )
            else:
                result = await session.execute(
                    sql_text(
                        """
                        SELECT id, text FROM memories
                        WHERE embedding IS NULL
                        LIMIT :limit
                    """
                    ),
                    {"limit": batch_size},
                )

            rows = result.fetchall()

            for row in rows:
                stats["processed"] += 1
                try:
                    if row.text and row.text.strip():
                        embedding = await self._embedding_fn(row.text)
                        await session.execute(
                            sql_text(
                                """
                                UPDATE memories
                                SET embedding = CAST(:embedding AS vector)
                                WHERE id = :id
                            """
                            ),
                            {
                                "id": row.id,
                                "embedding": f"[{','.join(str(x) for x in embedding)}]",
                            },
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
