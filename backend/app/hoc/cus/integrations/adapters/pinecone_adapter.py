# capability_id: CAP-018
# Layer: L2 — Adapter
# AUDIENCE: INTERNAL
# PHASE: W3
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Pinecone vector store adapter
# Callers: RetrievalMediator, IndexingExecutor
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2
# Reference: GAP-144 (Pinecone Vector Store Adapter)

"""
Pinecone Vector Store Adapter (GAP-144)

Provides integration with Pinecone vector database:
- Serverless and pod-based indexes
- Namespace support
- Metadata filtering
- Batch operations
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


class PineconeAdapter(VectorStoreAdapter):
    """
    Pinecone vector store adapter.

    Supports both serverless and pod-based Pinecone indexes.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        environment: Optional[str] = None,
        index_name: Optional[str] = None,
        dimension: int = 1536,  # OpenAI ada-002 default
        metric: str = "cosine",
        **kwargs,
    ):
        self._api_key = api_key or os.getenv("PINECONE_API_KEY")
        self._environment = environment or os.getenv("PINECONE_ENVIRONMENT")
        self._index_name = index_name or os.getenv("PINECONE_INDEX_NAME", "aos-vectors")
        self._dimension = dimension
        self._metric = metric
        self._index = None
        self._client = None

    async def connect(self) -> bool:
        """Connect to Pinecone."""
        try:
            from pinecone import Pinecone

            self._client = Pinecone(api_key=self._api_key)

            # Check if index exists
            existing_indexes = self._client.list_indexes()
            index_names = [idx.name for idx in existing_indexes]

            if self._index_name not in index_names:
                logger.info(f"Creating Pinecone index: {self._index_name}")
                self._client.create_index(
                    name=self._index_name,
                    dimension=self._dimension,
                    metric=self._metric,
                    spec={
                        "serverless": {
                            "cloud": "aws",
                            "region": self._environment or "us-east-1",
                        }
                    },
                )

            self._index = self._client.Index(self._index_name)
            logger.info(f"Connected to Pinecone index: {self._index_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Pinecone: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from Pinecone."""
        self._index = None
        self._client = None
        logger.info("Disconnected from Pinecone")

    async def upsert(
        self,
        records: List[VectorRecord],
        namespace: Optional[str] = None,
    ) -> UpsertResult:
        """Upsert vectors to Pinecone."""
        if not self._index:
            raise RuntimeError("Not connected to Pinecone")

        try:
            # Convert records to Pinecone format
            vectors = []
            for record in records:
                vector_data = {
                    "id": record.id,
                    "values": record.vector,
                }
                if record.metadata:
                    vector_data["metadata"] = record.metadata
                vectors.append(vector_data)

            # Batch upsert (Pinecone recommends batches of 100)
            batch_size = 100
            upserted_ids = []

            for i in range(0, len(vectors), batch_size):
                batch = vectors[i : i + batch_size]
                response = self._index.upsert(
                    vectors=batch,
                    namespace=namespace,
                )
                upserted_ids.extend([v["id"] for v in batch])

            logger.info(f"Upserted {len(upserted_ids)} vectors to Pinecone")
            return UpsertResult(
                upserted_count=len(upserted_ids),
                upserted_ids=upserted_ids,
            )

        except Exception as e:
            logger.error(f"Pinecone upsert failed: {e}")
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
        """Query Pinecone for similar vectors."""
        if not self._index:
            raise RuntimeError("Not connected to Pinecone")

        try:
            response = self._index.query(
                vector=vector,
                top_k=top_k,
                namespace=namespace,
                filter=filter,
                include_values=include_vectors,
                include_metadata=include_metadata,
            )

            results = []
            for match in response.matches:
                results.append(
                    QueryResult(
                        id=match.id,
                        score=match.score,
                        vector=match.values if include_vectors else None,
                        metadata=match.metadata or {},
                    )
                )

            logger.debug(f"Pinecone query returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Pinecone query failed: {e}")
            return []

    async def delete(
        self,
        ids: Optional[List[str]] = None,
        namespace: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None,
        delete_all: bool = False,
    ) -> DeleteResult:
        """Delete vectors from Pinecone."""
        if not self._index:
            raise RuntimeError("Not connected to Pinecone")

        try:
            if delete_all:
                self._index.delete(delete_all=True, namespace=namespace)
                logger.info(f"Deleted all vectors from namespace: {namespace}")
                return DeleteResult(deleted_count=-1)  # Unknown count

            if ids:
                self._index.delete(ids=ids, namespace=namespace)
                logger.info(f"Deleted {len(ids)} vectors from Pinecone")
                return DeleteResult(deleted_count=len(ids), deleted_ids=ids)

            if filter:
                self._index.delete(filter=filter, namespace=namespace)
                logger.info(f"Deleted vectors matching filter from Pinecone")
                return DeleteResult(deleted_count=-1)  # Unknown count

            return DeleteResult(deleted_count=0)

        except Exception as e:
            logger.error(f"Pinecone delete failed: {e}")
            return DeleteResult(deleted_count=0)

    async def get_stats(self, namespace: Optional[str] = None) -> IndexStats:
        """Get Pinecone index statistics."""
        if not self._index:
            raise RuntimeError("Not connected to Pinecone")

        try:
            stats = self._index.describe_index_stats()

            namespaces = {}
            if stats.namespaces:
                for ns_name, ns_stats in stats.namespaces.items():
                    namespaces[ns_name] = ns_stats.vector_count

            return IndexStats(
                total_vectors=stats.total_vector_count,
                dimension=stats.dimension,
                index_fullness=stats.index_fullness,
                namespaces=namespaces,
            )

        except Exception as e:
            logger.error(f"Failed to get Pinecone stats: {e}")
            raise

    async def create_namespace(self, namespace: str) -> bool:
        """
        Create a namespace in Pinecone.

        Note: Pinecone namespaces are created implicitly on first upsert.
        """
        # Pinecone namespaces are created automatically
        logger.info(f"Namespace '{namespace}' will be created on first upsert")
        return True

    async def delete_namespace(self, namespace: str) -> bool:
        """Delete a namespace from Pinecone."""
        if not self._index:
            raise RuntimeError("Not connected to Pinecone")

        try:
            self._index.delete(delete_all=True, namespace=namespace)
            logger.info(f"Deleted namespace: {namespace}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete namespace: {e}")
            return False

    async def list_namespaces(self) -> List[str]:
        """List all namespaces in Pinecone."""
        if not self._index:
            raise RuntimeError("Not connected to Pinecone")

        try:
            stats = self._index.describe_index_stats()
            namespaces = list(stats.namespaces.keys()) if stats.namespaces else []
            return namespaces

        except Exception as e:
            logger.error(f"Failed to list namespaces: {e}")
            return []
