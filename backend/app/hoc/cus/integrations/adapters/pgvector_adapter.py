# capability_id: CAP-018
# Layer: L2 — Adapter
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: PGVector production adapter
# Callers: RetrievalMediator, IndexingExecutor
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2
# Reference: GAP-146 (PGVector Production Adapter)

"""
PGVector Production Adapter (GAP-146)

Provides integration with PostgreSQL pgvector extension:
- Native PostgreSQL integration
- HNSW and IVFFlat indexes
- SQL-based metadata filtering
- Production-ready with connection pooling
"""

import logging
import os
from typing import Any, Dict, List, Optional

from .base import (
    DeleteResult,
    IndexStats,
    QueryResult,
    UpsertResult,
    VectorRecord,
    VectorStoreAdapter,
)

logger = logging.getLogger(__name__)


class PGVectorAdapter(VectorStoreAdapter):
    """
    PGVector production adapter.

    Uses asyncpg for async PostgreSQL operations with pgvector extension.
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        table_name: str = "aos_vectors",
        dimension: int = 1536,
        index_type: str = "hnsw",  # hnsw or ivfflat
        **kwargs,
    ):
        self._database_url = database_url or os.getenv("PGVECTOR_DATABASE_URL") or os.getenv("DATABASE_URL")
        self._table_name = table_name
        self._dimension = dimension
        self._index_type = index_type
        self._pool = None

    async def connect(self) -> bool:
        """Connect to PostgreSQL and ensure pgvector is set up."""
        try:
            import asyncpg

            self._pool = await asyncpg.create_pool(
                dsn=self._database_url,
                min_size=2,
                max_size=10,
            )

            async with self._pool.acquire() as conn:
                # Ensure pgvector extension exists
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

                # Create table if not exists
                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self._table_name} (
                        id TEXT PRIMARY KEY,
                        embedding vector({self._dimension}),
                        text TEXT,
                        metadata JSONB DEFAULT '{{}}',
                        namespace TEXT DEFAULT '',
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)

                # Create index if not exists
                index_name = f"{self._table_name}_embedding_idx"
                if self._index_type == "hnsw":
                    await conn.execute(f"""
                        CREATE INDEX IF NOT EXISTS {index_name}
                        ON {self._table_name}
                        USING hnsw (embedding vector_cosine_ops)
                        WITH (m = 16, ef_construction = 64)
                    """)
                else:  # ivfflat
                    await conn.execute(f"""
                        CREATE INDEX IF NOT EXISTS {index_name}
                        ON {self._table_name}
                        USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = 100)
                    """)

                # Create namespace index
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS {self._table_name}_namespace_idx
                    ON {self._table_name} (namespace)
                """)

            logger.info(f"Connected to PGVector: {self._table_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to PGVector: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from PostgreSQL."""
        if self._pool:
            await self._pool.close()
            self._pool = None
        logger.info("Disconnected from PGVector")

    async def upsert(
        self,
        records: List[VectorRecord],
        namespace: Optional[str] = None,
    ) -> UpsertResult:
        """Upsert vectors to PGVector."""
        if not self._pool:
            raise RuntimeError("Not connected to PGVector")

        try:
            import json

            upserted_ids = []
            errors = []

            async with self._pool.acquire() as conn:
                for record in records:
                    try:
                        ns = namespace or record.namespace or ""
                        metadata_json = json.dumps(record.metadata)
                        vector_str = f"[{','.join(map(str, record.vector))}]"

                        await conn.execute(f"""
                            INSERT INTO {self._table_name} (id, embedding, text, metadata, namespace, updated_at)
                            VALUES ($1, $2::vector, $3, $4::jsonb, $5, NOW())
                            ON CONFLICT (id) DO UPDATE SET
                                embedding = EXCLUDED.embedding,
                                text = EXCLUDED.text,
                                metadata = EXCLUDED.metadata,
                                namespace = EXCLUDED.namespace,
                                updated_at = NOW()
                        """, record.id, vector_str, record.text or "", metadata_json, ns)

                        upserted_ids.append(record.id)
                    except Exception as e:
                        errors.append({"id": record.id, "error": str(e)})

            logger.info(f"Upserted {len(upserted_ids)} vectors to PGVector")
            return UpsertResult(
                upserted_count=len(upserted_ids),
                upserted_ids=upserted_ids,
                errors=errors,
            )

        except Exception as e:
            logger.error(f"PGVector upsert failed: {e}")
            return UpsertResult(
                upserted_count=0,
                errors=[{"error": str(e)}],
            )

    async def query(
        self,
        vector: List[float],
        top_k: int = 10,
        namespace: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None,
        include_vectors: bool = False,
        include_metadata: bool = True,
    ) -> List[QueryResult]:
        """Query PGVector for similar vectors."""
        if not self._pool:
            raise RuntimeError("Not connected to PGVector")

        try:
            vector_str = f"[{','.join(map(str, vector))}]"

            # Build query
            select_cols = ["id", "text"]
            if include_vectors:
                select_cols.append("embedding::text as vector_str")
            if include_metadata:
                select_cols.append("metadata")

            # Add distance calculation (cosine similarity)
            select_cols.append(f"1 - (embedding <=> '{vector_str}'::vector) as score")

            query = f"""
                SELECT {', '.join(select_cols)}
                FROM {self._table_name}
                WHERE 1=1
            """
            params = []
            param_idx = 1

            if namespace:
                query += f" AND namespace = ${param_idx}"
                params.append(namespace)
                param_idx += 1

            if filter:
                for key, value in filter.items():
                    if isinstance(value, str):
                        query += f" AND metadata->>'{key}' = ${param_idx}"
                    elif isinstance(value, (int, float)):
                        query += f" AND (metadata->>'{key}')::numeric = ${param_idx}"
                    elif isinstance(value, bool):
                        query += f" AND (metadata->>'{key}')::boolean = ${param_idx}"
                    params.append(value)
                    param_idx += 1

            query += f" ORDER BY embedding <=> '{vector_str}'::vector LIMIT {top_k}"

            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, *params)

            results = []
            for row in rows:
                result = QueryResult(
                    id=row["id"],
                    score=float(row["score"]),
                    text=row.get("text"),
                    metadata=dict(row["metadata"]) if include_metadata and "metadata" in row else {},
                )
                if include_vectors and "vector_str" in row:
                    # Parse vector string back to list
                    vec_str = row["vector_str"].strip("[]")
                    result.vector = [float(x) for x in vec_str.split(",")] if vec_str else None
                results.append(result)

            logger.debug(f"PGVector query returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"PGVector query failed: {e}")
            return []

    async def delete(
        self,
        ids: Optional[List[str]] = None,
        namespace: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None,
        delete_all: bool = False,
    ) -> DeleteResult:
        """Delete vectors from PGVector."""
        if not self._pool:
            raise RuntimeError("Not connected to PGVector")

        try:
            async with self._pool.acquire() as conn:
                if delete_all:
                    result = await conn.execute(f"DELETE FROM {self._table_name}")
                    count = int(result.split()[-1]) if result else -1
                    logger.info(f"Deleted all vectors from {self._table_name}")
                    return DeleteResult(deleted_count=count)

                if ids:
                    result = await conn.execute(
                        f"DELETE FROM {self._table_name} WHERE id = ANY($1)",
                        ids
                    )
                    count = int(result.split()[-1]) if result else 0
                    logger.info(f"Deleted {count} vectors from PGVector")
                    return DeleteResult(deleted_count=count, deleted_ids=ids[:count])

                if namespace or filter:
                    query = f"DELETE FROM {self._table_name} WHERE 1=1"
                    params = []
                    param_idx = 1

                    if namespace:
                        query += f" AND namespace = ${param_idx}"
                        params.append(namespace)
                        param_idx += 1

                    if filter:
                        for key, value in filter.items():
                            if isinstance(value, str):
                                query += f" AND metadata->>'{key}' = ${param_idx}"
                            elif isinstance(value, (int, float)):
                                query += f" AND (metadata->>'{key}')::numeric = ${param_idx}"
                            elif isinstance(value, bool):
                                query += f" AND (metadata->>'{key}')::boolean = ${param_idx}"
                            params.append(value)
                            param_idx += 1

                    result = await conn.execute(query, *params)
                    count = int(result.split()[-1]) if result else 0
                    logger.info(f"Deleted {count} vectors matching filter")
                    return DeleteResult(deleted_count=count)

            return DeleteResult(deleted_count=0)

        except Exception as e:
            logger.error(f"PGVector delete failed: {e}")
            return DeleteResult(deleted_count=0)

    async def get_stats(self, namespace: Optional[str] = None) -> IndexStats:
        """Get PGVector statistics."""
        if not self._pool:
            raise RuntimeError("Not connected to PGVector")

        try:
            async with self._pool.acquire() as conn:
                # Get total count
                if namespace:
                    total = await conn.fetchval(
                        f"SELECT COUNT(*) FROM {self._table_name} WHERE namespace = $1",
                        namespace
                    )
                else:
                    total = await conn.fetchval(f"SELECT COUNT(*) FROM {self._table_name}")

                # Get namespace counts
                namespace_rows = await conn.fetch(f"""
                    SELECT namespace, COUNT(*) as count
                    FROM {self._table_name}
                    GROUP BY namespace
                """)

                namespaces = {row["namespace"]: row["count"] for row in namespace_rows}

            return IndexStats(
                total_vectors=total or 0,
                dimension=self._dimension,
                namespaces=namespaces,
            )

        except Exception as e:
            logger.error(f"Failed to get PGVector stats: {e}")
            raise

    async def create_namespace(self, namespace: str) -> bool:
        """
        Create a namespace in PGVector.

        Note: PGVector uses a namespace column, no explicit creation needed.
        """
        logger.info(f"Namespace '{namespace}' available via column field")
        return True

    async def delete_namespace(self, namespace: str) -> bool:
        """Delete a namespace from PGVector."""
        result = await self.delete(namespace=namespace)
        return result.deleted_count > 0

    async def list_namespaces(self) -> List[str]:
        """List all namespaces in PGVector."""
        if not self._pool:
            raise RuntimeError("Not connected to PGVector")

        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(f"""
                    SELECT DISTINCT namespace
                    FROM {self._table_name}
                    WHERE namespace != ''
                    ORDER BY namespace
                """)

            return [row["namespace"] for row in rows]

        except Exception as e:
            logger.error(f"Failed to list namespaces: {e}")
            return []
