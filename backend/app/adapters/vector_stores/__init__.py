# Layer: L3 — Boundary Adapters
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Vector store adapters for embedding storage and similarity search
# Callers: RetrievalMediator, IndexingExecutor
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2
# Reference: GAP-144, GAP-145, GAP-146 (Vector Store Adapters)

"""
Vector Store Adapters (GAP-144, GAP-145, GAP-146)

Provides adapters for vector databases:
- Pinecone (GAP-144)
- Weaviate (GAP-145)
- PGVector (GAP-146)

Features:
- Unified interface for vector operations
- Batch upsert/query support
- Metadata filtering
- Namespace/collection management
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import VectorStoreAdapter
    from .pinecone_adapter import PineconeAdapter
    from .weaviate_adapter import WeaviateAdapter
    from .pgvector_adapter import PGVectorAdapter

__all__ = [
    "VectorStoreAdapter",
    "PineconeAdapter",
    "WeaviateAdapter",
    "PGVectorAdapter",
    "get_vector_store_adapter",
    "VectorStoreType",
]


from enum import Enum


class VectorStoreType(str, Enum):
    """Supported vector store types."""
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"
    PGVECTOR = "pgvector"


def get_vector_store_adapter(
    store_type: VectorStoreType,
    **config,
):
    """
    Factory function to get a vector store adapter.

    Args:
        store_type: Type of vector store
        **config: Store-specific configuration

    Returns:
        VectorStoreAdapter instance
    """
    if store_type == VectorStoreType.PINECONE:
        from .pinecone_adapter import PineconeAdapter
        return PineconeAdapter(**config)
    elif store_type == VectorStoreType.WEAVIATE:
        from .weaviate_adapter import WeaviateAdapter
        return WeaviateAdapter(**config)
    elif store_type == VectorStoreType.PGVECTOR:
        from .pgvector_adapter import PGVectorAdapter
        return PGVectorAdapter(**config)
    else:
        raise ValueError(f"Unsupported vector store type: {store_type}")
