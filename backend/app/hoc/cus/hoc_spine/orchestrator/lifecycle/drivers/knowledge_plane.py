# capability_id: CAP-012
# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none (dataclass definitions)
#   Writes: none
# Role: KnowledgePlane domain models and registry (pure dataclass definitions)
# Callers: lifecycle engines, drivers
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L6 (no DB), sqlalchemy
# Reference: PIN-470, GAP-056 (KnowledgePlane model)
# NOTE: Reclassified L6→L5 (2026-01-24) - Pure dataclass definitions, no DB imports
"""
KnowledgePlane - Knowledge plane models and registry.

Provides knowledge graph abstraction for:
- Knowledge organization
- Semantic relationships
- Multi-source integration
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
import uuid


class KnowledgePlaneStatus(str, Enum):
    """Status of a knowledge plane."""

    CREATING = "creating"       # Being created
    INDEXING = "indexing"       # Indexing content
    ACTIVE = "active"           # Ready for use
    UPDATING = "updating"       # Being updated
    INACTIVE = "inactive"       # Temporarily disabled
    ERROR = "error"             # In error state
    ARCHIVED = "archived"       # Archived


class KnowledgeNodeType(str, Enum):
    """Types of knowledge nodes."""

    DOCUMENT = "document"       # Full document
    SECTION = "section"         # Document section
    PARAGRAPH = "paragraph"     # Text paragraph
    ENTITY = "entity"           # Named entity
    CONCEPT = "concept"         # Abstract concept
    FACT = "fact"               # Factual statement
    RELATION = "relation"       # Relationship between nodes


@dataclass
class KnowledgeNode:
    """A node in the knowledge graph."""

    node_id: str
    node_type: KnowledgeNodeType
    content: str

    # Embedding
    embedding: Optional[list[float]] = None

    # Metadata
    source_id: Optional[str] = None
    source_type: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    # Relationships
    parent_id: Optional[str] = None
    child_ids: list[str] = field(default_factory=list)
    related_ids: list[str] = field(default_factory=list)

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_child(self, child_id: str) -> None:
        """Add a child node reference."""
        if child_id not in self.child_ids:
            self.child_ids.append(child_id)
            self.updated_at = datetime.now(timezone.utc)

    def add_related(self, node_id: str) -> None:
        """Add a related node reference."""
        if node_id not in self.related_ids:
            self.related_ids.append(node_id)
            self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "content": self.content,
            "has_embedding": self.embedding is not None,
            "source_id": self.source_id,
            "source_type": self.source_type,
            "metadata": self.metadata,
            "parent_id": self.parent_id,
            "child_ids": self.child_ids,
            "related_ids": self.related_ids,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class KnowledgePlane:
    """
    Representation of a knowledge plane.

    A knowledge plane is a tenant-specific knowledge graph
    that organizes and indexes content from multiple sources.
    """

    plane_id: str
    tenant_id: str
    name: str

    # Status
    status: KnowledgePlaneStatus = KnowledgePlaneStatus.CREATING

    # Configuration
    description: Optional[str] = None
    embedding_model: str = "text-embedding-ada-002"
    embedding_dimension: int = 1536

    # Content
    nodes: dict[str, KnowledgeNode] = field(default_factory=dict)
    source_ids: list[str] = field(default_factory=list)

    # Statistics
    node_count: int = 0
    document_count: int = 0
    last_indexed: Optional[datetime] = None
    last_error: Optional[str] = None

    # Metadata
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_node(self, node: KnowledgeNode) -> None:
        """Add a node to the plane."""
        self.nodes[node.node_id] = node
        self.node_count = len(self.nodes)
        self.updated_at = datetime.now(timezone.utc)

    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def remove_node(self, node_id: str) -> bool:
        """Remove a node from the plane."""
        if node_id in self.nodes:
            del self.nodes[node_id]
            self.node_count = len(self.nodes)
            self.updated_at = datetime.now(timezone.utc)
            return True
        return False

    def add_source(self, source_id: str) -> None:
        """Add a source to the plane."""
        if source_id not in self.source_ids:
            self.source_ids.append(source_id)
            self.updated_at = datetime.now(timezone.utc)

    def remove_source(self, source_id: str) -> bool:
        """Remove a source from the plane."""
        if source_id in self.source_ids:
            self.source_ids.remove(source_id)
            self.updated_at = datetime.now(timezone.utc)
            return True
        return False

    def activate(self, now: Optional[datetime] = None) -> None:
        """Activate the plane."""
        now = now or datetime.now(timezone.utc)
        self.status = KnowledgePlaneStatus.ACTIVE
        self.last_error = None
        self.updated_at = now

    def deactivate(self, now: Optional[datetime] = None) -> None:
        """Deactivate the plane."""
        now = now or datetime.now(timezone.utc)
        self.status = KnowledgePlaneStatus.INACTIVE
        self.updated_at = now

    def start_indexing(self, now: Optional[datetime] = None) -> None:
        """Start indexing the plane."""
        now = now or datetime.now(timezone.utc)
        self.status = KnowledgePlaneStatus.INDEXING
        self.updated_at = now

    def finish_indexing(
        self,
        success: bool,
        error: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> None:
        """Finish indexing the plane."""
        now = now or datetime.now(timezone.utc)
        if success:
            self.status = KnowledgePlaneStatus.ACTIVE
            self.last_indexed = now
            self.last_error = None
        else:
            self.status = KnowledgePlaneStatus.ERROR
            self.last_error = error
        self.updated_at = now

    def archive(self, now: Optional[datetime] = None) -> None:
        """Archive the plane."""
        now = now or datetime.now(timezone.utc)
        self.status = KnowledgePlaneStatus.ARCHIVED
        self.updated_at = now

    def record_error(self, error: str, now: Optional[datetime] = None) -> None:
        """Record an error."""
        now = now or datetime.now(timezone.utc)
        self.last_error = error
        self.status = KnowledgePlaneStatus.ERROR
        self.updated_at = now

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "plane_id": self.plane_id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "status": self.status.value,
            "description": self.description,
            "embedding_model": self.embedding_model,
            "embedding_dimension": self.embedding_dimension,
            "node_count": self.node_count,
            "document_count": self.document_count,
            "source_ids": self.source_ids,
            "last_indexed": (
                self.last_indexed.isoformat() if self.last_indexed else None
            ),
            "last_error": self.last_error,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class KnowledgePlaneError(Exception):
    """Exception for knowledge plane errors."""

    def __init__(
        self,
        message: str,
        plane_id: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.plane_id = plane_id

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "error": self.message,
            "plane_id": self.plane_id,
        }


@dataclass
class KnowledgePlaneStats:
    """Statistics for knowledge planes."""

    total_planes: int = 0
    active_planes: int = 0
    indexing_planes: int = 0
    error_planes: int = 0

    # Totals
    total_nodes: int = 0
    total_documents: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_planes": self.total_planes,
            "active_planes": self.active_planes,
            "indexing_planes": self.indexing_planes,
            "error_planes": self.error_planes,
            "total_nodes": self.total_nodes,
            "total_documents": self.total_documents,
        }


class KnowledgePlaneRegistry:
    """
    Registry for managing knowledge planes.

    Features:
    - Plane registration and lookup
    - Node management
    - Status tracking
    - Tenant isolation
    """

    def __init__(self):
        """Initialize the registry."""
        self._planes: dict[str, KnowledgePlane] = {}
        self._tenant_planes: dict[str, set[str]] = {}

    def register(
        self,
        tenant_id: str,
        name: str,
        description: Optional[str] = None,
        embedding_model: str = "text-embedding-ada-002",
        plane_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> KnowledgePlane:
        """Register a new knowledge plane."""
        plane_id = plane_id or str(uuid.uuid4())

        plane = KnowledgePlane(
            plane_id=plane_id,
            tenant_id=tenant_id,
            name=name,
            description=description,
            embedding_model=embedding_model,
            tags=tags or [],
        )

        self._planes[plane_id] = plane

        # Track by tenant
        if tenant_id not in self._tenant_planes:
            self._tenant_planes[tenant_id] = set()
        self._tenant_planes[tenant_id].add(plane_id)

        return plane

    def get(self, plane_id: str) -> Optional[KnowledgePlane]:
        """Get a plane by ID."""
        return self._planes.get(plane_id)

    def get_by_name(
        self,
        tenant_id: str,
        name: str,
    ) -> Optional[KnowledgePlane]:
        """Get a plane by name within a tenant."""
        for plane in self._planes.values():
            if plane.tenant_id == tenant_id and plane.name == name:
                return plane
        return None

    def list(
        self,
        tenant_id: Optional[str] = None,
        status: Optional[KnowledgePlaneStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[KnowledgePlane]:
        """List planes with optional filters."""
        planes = list(self._planes.values())

        if tenant_id:
            planes = [p for p in planes if p.tenant_id == tenant_id]

        if status:
            planes = [p for p in planes if p.status == status]

        planes.sort(key=lambda p: p.name)

        return planes[offset:offset + limit]

    def delete(self, plane_id: str) -> bool:
        """Delete a plane."""
        plane = self._planes.get(plane_id)
        if not plane:
            return False

        del self._planes[plane_id]

        # Remove from tenant tracking
        if plane.tenant_id in self._tenant_planes:
            self._tenant_planes[plane.tenant_id].discard(plane_id)

        return True

    def get_statistics(
        self,
        tenant_id: Optional[str] = None,
    ) -> KnowledgePlaneStats:
        """Get registry statistics."""
        stats = KnowledgePlaneStats()

        for plane in self._planes.values():
            if tenant_id and plane.tenant_id != tenant_id:
                continue

            stats.total_planes += 1
            stats.total_nodes += plane.node_count
            stats.total_documents += plane.document_count

            if plane.status == KnowledgePlaneStatus.ACTIVE:
                stats.active_planes += 1
            elif plane.status == KnowledgePlaneStatus.INDEXING:
                stats.indexing_planes += 1
            elif plane.status == KnowledgePlaneStatus.ERROR:
                stats.error_planes += 1

        return stats

    def clear_tenant(self, tenant_id: str) -> int:
        """Clear all planes for a tenant."""
        plane_ids = list(self._tenant_planes.get(tenant_id, set()))
        for plane_id in plane_ids:
            self.delete(plane_id)
        return len(plane_ids)

    def reset(self) -> None:
        """Reset all state (for testing)."""
        self._planes.clear()
        self._tenant_planes.clear()


# Module-level singleton
_registry: Optional[KnowledgePlaneRegistry] = None


def get_knowledge_plane_registry() -> KnowledgePlaneRegistry:
    """Get the singleton registry instance."""
    global _registry
    if _registry is None:
        _registry = KnowledgePlaneRegistry()
    return _registry


def _reset_registry() -> None:
    """Reset the singleton (for testing)."""
    global _registry
    if _registry:
        _registry.reset()
    _registry = None


# Helper functions
def create_knowledge_plane(
    tenant_id: str,
    name: str,
    description: Optional[str] = None,
) -> KnowledgePlane:
    """Create a new knowledge plane using the singleton registry."""
    registry = get_knowledge_plane_registry()
    return registry.register(
        tenant_id=tenant_id,
        name=name,
        description=description,
    )


def get_knowledge_plane(plane_id: str) -> Optional[KnowledgePlane]:
    """Get a knowledge plane by ID using the singleton registry."""
    registry = get_knowledge_plane_registry()
    return registry.get(plane_id)


def list_knowledge_planes(
    tenant_id: Optional[str] = None,
) -> list[KnowledgePlane]:
    """List knowledge planes using the singleton registry."""
    registry = get_knowledge_plane_registry()
    return registry.list(tenant_id=tenant_id)
