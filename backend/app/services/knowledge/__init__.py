# Layer: L4 — Domain Engines
# Product: system-wide
# Reference: GAP-056 (KnowledgePlane model)
"""
Knowledge Plane Services (GAP-056)

Provides models and services for knowledge plane management
including knowledge graphs, semantic indexing, and retrieval.

This module provides:
    - KnowledgePlane: Knowledge plane model
    - KnowledgeNode: Node in knowledge graph
    - KnowledgePlaneRegistry: Service for managing planes
    - Helper functions for quick access
"""

from app.services.knowledge.knowledge_plane import (
    KnowledgeNode,
    KnowledgeNodeType,
    KnowledgePlane,
    KnowledgePlaneError,
    KnowledgePlaneRegistry,
    KnowledgePlaneStatus,
    create_knowledge_plane,
    get_knowledge_plane,
    list_knowledge_planes,
)

__all__ = [
    "KnowledgeNode",
    "KnowledgeNodeType",
    "KnowledgePlane",
    "KnowledgePlaneError",
    "KnowledgePlaneRegistry",
    "KnowledgePlaneStatus",
    "create_knowledge_plane",
    "get_knowledge_plane",
    "list_knowledge_planes",
]
