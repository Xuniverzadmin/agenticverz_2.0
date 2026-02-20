# capability_id: CAP-018
# Layer: L2 — Adapter
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Base class for vector store adapters
# Callers: Vector store adapter implementations
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2
# Reference: GAP-144, GAP-145, GAP-146

"""
Vector Store Base Adapter

Provides abstract interface for vector store operations.
All vector store adapters must implement this interface.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class VectorRecord:
    """A single vector record."""

    id: str
    vector: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    text: Optional[str] = None
    namespace: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "vector": self.vector,
            "metadata": self.metadata,
            "text": self.text,
            "namespace": self.namespace,
        }


@dataclass
class QueryResult:
    """Result of a vector similarity query."""

    id: str
    score: float
    vector: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    text: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "score": self.score,
            "vector": self.vector,
            "metadata": self.metadata,
            "text": self.text,
        }


@dataclass
class UpsertResult:
    """Result of an upsert operation."""

    upserted_count: int
    upserted_ids: List[str] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


@dataclass
class DeleteResult:
    """Result of a delete operation."""

    deleted_count: int
    deleted_ids: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.deleted_count > 0


@dataclass
class IndexStats:
    """Statistics about a vector index."""

    total_vectors: int
    dimension: int
    index_fullness: Optional[float] = None
    namespaces: Optional[Dict[str, int]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_vectors": self.total_vectors,
            "dimension": self.dimension,
            "index_fullness": self.index_fullness,
            "namespaces": self.namespaces,
            "metadata": self.metadata,
        }


class VectorStoreAdapter(ABC):
    """
    Abstract base class for vector store adapters.

    All vector store implementations must implement these methods.
    """

    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to the vector store.

        Returns:
            True if connected successfully
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the vector store."""
        pass

    @abstractmethod
    async def upsert(
        self,
        records: List[VectorRecord],
        namespace: Optional[str] = None,
    ) -> UpsertResult:
        """
        Upsert vectors into the store.

        Args:
            records: List of vector records to upsert
            namespace: Optional namespace/collection

        Returns:
            UpsertResult
        """
        pass

    @abstractmethod
    async def query(
        self,
        vector: List[float],
        top_k: int = 10,
        namespace: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None,
        include_vectors: bool = False,
        include_metadata: bool = True,
    ) -> List[QueryResult]:
        """
        Query for similar vectors.

        Args:
            vector: Query vector
            top_k: Number of results to return
            namespace: Optional namespace/collection
            filter: Optional metadata filter
            include_vectors: Whether to include vectors in results
            include_metadata: Whether to include metadata in results

        Returns:
            List of QueryResult ordered by similarity
        """
        pass

    @abstractmethod
    async def delete(
        self,
        ids: Optional[List[str]] = None,
        namespace: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None,
        delete_all: bool = False,
    ) -> DeleteResult:
        """
        Delete vectors from the store.

        Args:
            ids: List of vector IDs to delete
            namespace: Optional namespace/collection
            filter: Optional metadata filter for deletion
            delete_all: Delete all vectors (use with caution)

        Returns:
            DeleteResult
        """
        pass

    @abstractmethod
    async def get_stats(self, namespace: Optional[str] = None) -> IndexStats:
        """
        Get index statistics.

        Args:
            namespace: Optional namespace/collection

        Returns:
            IndexStats
        """
        pass

    async def health_check(self) -> bool:
        """
        Check if the vector store is healthy.

        Returns:
            True if healthy
        """
        try:
            await self.get_stats()
            return True
        except Exception as e:
            logger.warning(f"Vector store health check failed: {e}")
            return False

    @abstractmethod
    async def create_namespace(self, namespace: str) -> bool:
        """
        Create a new namespace/collection.

        Args:
            namespace: Namespace name

        Returns:
            True if created
        """
        pass

    @abstractmethod
    async def delete_namespace(self, namespace: str) -> bool:
        """
        Delete a namespace/collection.

        Args:
            namespace: Namespace name

        Returns:
            True if deleted
        """
        pass

    @abstractmethod
    async def list_namespaces(self) -> List[str]:
        """
        List all namespaces/collections.

        Returns:
            List of namespace names
        """
        pass
