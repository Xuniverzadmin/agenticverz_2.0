# Layer: L3 — Boundary Adapters
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Weaviate vector store adapter
# Callers: RetrievalMediator, IndexingExecutor
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2
# Reference: GAP-145 (Weaviate Vector Store Adapter)

"""
Weaviate Vector Store Adapter (GAP-145)

Provides integration with Weaviate vector database:
- Schema-based collections
- Hybrid search (vector + keyword)
- GraphQL queries
- Multi-tenancy support
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


class WeaviateAdapter(VectorStoreAdapter):
    """
    Weaviate vector store adapter.

    Supports both Weaviate Cloud Services (WCS) and self-hosted instances.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        collection_name: str = "AosVectors",
        dimension: int = 1536,
        **kwargs,
    ):
        self._url = url or os.getenv("WEAVIATE_URL", "http://localhost:8080")
        self._api_key = api_key or os.getenv("WEAVIATE_API_KEY")
        self._collection_name = collection_name
        self._dimension = dimension
        self._client = None

    async def connect(self) -> bool:
        """Connect to Weaviate."""
        try:
            import weaviate
            from weaviate.auth import AuthApiKey

            auth_config = AuthApiKey(api_key=self._api_key) if self._api_key else None

            self._client = weaviate.Client(
                url=self._url,
                auth_client_secret=auth_config,
            )

            # Check if collection exists, create if not
            if not self._client.schema.exists(self._collection_name):
                logger.info(f"Creating Weaviate collection: {self._collection_name}")
                self._create_collection()

            logger.info(f"Connected to Weaviate: {self._url}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {e}")
            return False

    def _create_collection(self) -> None:
        """Create the vector collection schema."""
        schema = {
            "class": self._collection_name,
            "vectorizer": "none",  # We provide vectors directly
            "properties": [
                {
                    "name": "text",
                    "dataType": ["text"],
                    "description": "The text content",
                },
                {
                    "name": "metadata",
                    "dataType": ["object"],
                    "description": "Additional metadata",
                    "nestedProperties": [],  # Flexible schema
                },
                {
                    "name": "namespace",
                    "dataType": ["text"],
                    "description": "Namespace for organization",
                },
            ],
        }
        self._client.schema.create_class(schema)

    async def disconnect(self) -> None:
        """Disconnect from Weaviate."""
        self._client = None
        logger.info("Disconnected from Weaviate")

    async def upsert(
        self,
        records: List[VectorRecord],
        namespace: Optional[str] = None,
    ) -> UpsertResult:
        """Upsert vectors to Weaviate."""
        if not self._client:
            raise RuntimeError("Not connected to Weaviate")

        try:
            upserted_ids = []
            errors = []

            with self._client.batch as batch:
                batch.batch_size = 100

                for record in records:
                    properties = {
                        "text": record.text or "",
                        "metadata": record.metadata,
                        "namespace": namespace or record.namespace or "",
                    }

                    try:
                        batch.add_data_object(
                            data_object=properties,
                            class_name=self._collection_name,
                            uuid=record.id,
                            vector=record.vector,
                        )
                        upserted_ids.append(record.id)
                    except Exception as e:
                        errors.append({"id": record.id, "error": str(e)})

            logger.info(f"Upserted {len(upserted_ids)} vectors to Weaviate")
            return UpsertResult(
                upserted_count=len(upserted_ids),
                upserted_ids=upserted_ids,
                errors=errors,
            )

        except Exception as e:
            logger.error(f"Weaviate upsert failed: {e}")
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
        """Query Weaviate for similar vectors."""
        if not self._client:
            raise RuntimeError("Not connected to Weaviate")

        try:
            query = (
                self._client.query
                .get(self._collection_name, ["text", "metadata", "namespace"])
                .with_near_vector({"vector": vector})
                .with_limit(top_k)
                .with_additional(["id", "distance"])
            )

            # Add namespace filter if specified
            if namespace:
                where_filter = {
                    "path": ["namespace"],
                    "operator": "Equal",
                    "valueText": namespace,
                }
                if filter:
                    where_filter = {
                        "operator": "And",
                        "operands": [where_filter, self._build_filter(filter)],
                    }
                query = query.with_where(where_filter)
            elif filter:
                query = query.with_where(self._build_filter(filter))

            if include_vectors:
                query = query.with_additional(["id", "distance", "vector"])

            response = query.do()

            results = []
            if response and "data" in response and "Get" in response["data"]:
                items = response["data"]["Get"].get(self._collection_name, [])
                for item in items:
                    additional = item.get("_additional", {})
                    results.append(
                        QueryResult(
                            id=additional.get("id", ""),
                            score=1.0 - additional.get("distance", 0),  # Convert distance to similarity
                            vector=additional.get("vector") if include_vectors else None,
                            metadata=item.get("metadata", {}) if include_metadata else {},
                            text=item.get("text"),
                        )
                    )

            logger.debug(f"Weaviate query returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Weaviate query failed: {e}")
            return []

    def _build_filter(self, filter: Dict[str, Any]) -> Dict[str, Any]:
        """Build Weaviate where filter from dict."""
        # Simple key-value filter conversion
        operands = []
        for key, value in filter.items():
            if isinstance(value, str):
                operands.append({
                    "path": [f"metadata.{key}"],
                    "operator": "Equal",
                    "valueText": value,
                })
            elif isinstance(value, (int, float)):
                operands.append({
                    "path": [f"metadata.{key}"],
                    "operator": "Equal",
                    "valueNumber": value,
                })
            elif isinstance(value, bool):
                operands.append({
                    "path": [f"metadata.{key}"],
                    "operator": "Equal",
                    "valueBoolean": value,
                })

        if len(operands) == 1:
            return operands[0]
        return {"operator": "And", "operands": operands}

    async def delete(
        self,
        ids: Optional[List[str]] = None,
        namespace: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None,
        delete_all: bool = False,
    ) -> DeleteResult:
        """Delete vectors from Weaviate."""
        if not self._client:
            raise RuntimeError("Not connected to Weaviate")

        try:
            deleted_count = 0

            if delete_all:
                # Delete entire collection and recreate
                self._client.schema.delete_class(self._collection_name)
                self._create_collection()
                logger.info(f"Deleted all vectors from collection: {self._collection_name}")
                return DeleteResult(deleted_count=-1)

            if ids:
                for obj_id in ids:
                    try:
                        self._client.data_object.delete(
                            uuid=obj_id,
                            class_name=self._collection_name,
                        )
                        deleted_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to delete {obj_id}: {e}")

                logger.info(f"Deleted {deleted_count} vectors from Weaviate")
                return DeleteResult(deleted_count=deleted_count, deleted_ids=ids[:deleted_count])

            if namespace or filter:
                where_filter = None
                if namespace:
                    where_filter = {
                        "path": ["namespace"],
                        "operator": "Equal",
                        "valueText": namespace,
                    }
                if filter:
                    if where_filter:
                        where_filter = {
                            "operator": "And",
                            "operands": [where_filter, self._build_filter(filter)],
                        }
                    else:
                        where_filter = self._build_filter(filter)

                result = self._client.batch.delete_objects(
                    class_name=self._collection_name,
                    where=where_filter,
                )
                deleted_count = result.get("results", {}).get("successful", 0)
                logger.info(f"Deleted {deleted_count} vectors matching filter")
                return DeleteResult(deleted_count=deleted_count)

            return DeleteResult(deleted_count=0)

        except Exception as e:
            logger.error(f"Weaviate delete failed: {e}")
            return DeleteResult(deleted_count=0)

    async def get_stats(self, namespace: Optional[str] = None) -> IndexStats:
        """Get Weaviate collection statistics."""
        if not self._client:
            raise RuntimeError("Not connected to Weaviate")

        try:
            # Get aggregate count
            query = (
                self._client.query
                .aggregate(self._collection_name)
                .with_meta_count()
            )

            if namespace:
                query = query.with_where({
                    "path": ["namespace"],
                    "operator": "Equal",
                    "valueText": namespace,
                })

            response = query.do()

            total = 0
            if response and "data" in response and "Aggregate" in response["data"]:
                agg = response["data"]["Aggregate"].get(self._collection_name, [{}])[0]
                total = agg.get("meta", {}).get("count", 0)

            return IndexStats(
                total_vectors=total,
                dimension=self._dimension,
            )

        except Exception as e:
            logger.error(f"Failed to get Weaviate stats: {e}")
            raise

    async def create_namespace(self, namespace: str) -> bool:
        """
        Create a namespace in Weaviate.

        Note: Weaviate uses the namespace property field, no explicit creation needed.
        """
        logger.info(f"Namespace '{namespace}' available via property field")
        return True

    async def delete_namespace(self, namespace: str) -> bool:
        """Delete a namespace from Weaviate."""
        result = await self.delete(namespace=namespace)
        return result.deleted_count > 0

    async def list_namespaces(self) -> List[str]:
        """List all namespaces in Weaviate."""
        if not self._client:
            raise RuntimeError("Not connected to Weaviate")

        try:
            # Query for distinct namespace values
            query = (
                self._client.query
                .aggregate(self._collection_name)
                .with_group_by_filter(["namespace"])
                .with_fields("groupedBy { value }")
            )

            response = query.do()

            namespaces = []
            if response and "data" in response and "Aggregate" in response["data"]:
                groups = response["data"]["Aggregate"].get(self._collection_name, [])
                for group in groups:
                    if "groupedBy" in group and "value" in group["groupedBy"]:
                        namespaces.append(group["groupedBy"]["value"])

            return namespaces

        except Exception as e:
            logger.error(f"Failed to list namespaces: {e}")
            return []
