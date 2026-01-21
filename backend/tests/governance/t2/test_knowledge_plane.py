# Layer: L8 — Catalyst/Meta
# Product: system-wide
# Reference: GAP-056 (KnowledgePlane model)
"""
Tests for KnowledgePlane model (GAP-056).

Verifies knowledge plane models and registry.
"""

import pytest
from datetime import datetime, timezone


class TestKnowledgePlaneImports:
    """Test that all components are properly exported."""

    def test_status_import(self):
        """KnowledgePlaneStatus should be importable."""
        from app.services.knowledge import KnowledgePlaneStatus
        assert KnowledgePlaneStatus.ACTIVE == "active"

    def test_node_type_import(self):
        """KnowledgeNodeType should be importable."""
        from app.services.knowledge import KnowledgeNodeType
        assert KnowledgeNodeType.DOCUMENT == "document"

    def test_node_import(self):
        """KnowledgeNode should be importable."""
        from app.services.knowledge import KnowledgeNode, KnowledgeNodeType
        node = KnowledgeNode(
            node_id="node-1",
            node_type=KnowledgeNodeType.DOCUMENT,
            content="Test content",
        )
        assert node.node_id == "node-1"

    def test_plane_import(self):
        """KnowledgePlane should be importable."""
        from app.services.knowledge import KnowledgePlane
        plane = KnowledgePlane(
            plane_id="plane-1",
            tenant_id="tenant-1",
            name="Test Plane",
        )
        assert plane.plane_id == "plane-1"

    def test_registry_import(self):
        """KnowledgePlaneRegistry should be importable."""
        from app.services.knowledge import KnowledgePlaneRegistry
        registry = KnowledgePlaneRegistry()
        assert registry is not None

    def test_error_import(self):
        """KnowledgePlaneError should be importable."""
        from app.services.knowledge import KnowledgePlaneError
        error = KnowledgePlaneError("test")
        assert str(error) == "test"


class TestKnowledgeNode:
    """Test KnowledgeNode dataclass."""

    def test_node_creation(self):
        """Node should be created with required fields."""
        from app.services.knowledge import KnowledgeNode, KnowledgeNodeType

        node = KnowledgeNode(
            node_id="node-1",
            node_type=KnowledgeNodeType.PARAGRAPH,
            content="Some text content",
        )

        assert node.node_id == "node-1"
        assert node.node_type == KnowledgeNodeType.PARAGRAPH
        assert node.content == "Some text content"

    def test_add_child(self):
        """Adding children should work correctly."""
        from app.services.knowledge import KnowledgeNode, KnowledgeNodeType

        node = KnowledgeNode(
            node_id="parent",
            node_type=KnowledgeNodeType.DOCUMENT,
            content="Doc",
        )

        node.add_child("child-1")
        assert "child-1" in node.child_ids

        node.add_child("child-1")  # Duplicate
        assert node.child_ids.count("child-1") == 1

    def test_add_related(self):
        """Adding related nodes should work correctly."""
        from app.services.knowledge import KnowledgeNode, KnowledgeNodeType

        node = KnowledgeNode(
            node_id="node-1",
            node_type=KnowledgeNodeType.CONCEPT,
            content="Concept",
        )

        node.add_related("related-1")
        assert "related-1" in node.related_ids

    def test_to_dict(self):
        """Node should serialize to dict."""
        from app.services.knowledge import KnowledgeNode, KnowledgeNodeType

        node = KnowledgeNode(
            node_id="node-1",
            node_type=KnowledgeNodeType.FACT,
            content="A fact",
            embedding=[0.1] * 10,
        )
        result = node.to_dict()

        assert result["node_id"] == "node-1"
        assert result["node_type"] == "fact"
        assert result["has_embedding"] is True


class TestKnowledgePlane:
    """Test KnowledgePlane dataclass."""

    def test_plane_creation(self):
        """Plane should be created with required fields."""
        from app.services.knowledge import (
            KnowledgePlane,
            KnowledgePlaneStatus,
        )

        plane = KnowledgePlane(
            plane_id="plane-1",
            tenant_id="tenant-1",
            name="Test Plane",
        )

        assert plane.plane_id == "plane-1"
        assert plane.status == KnowledgePlaneStatus.CREATING

    def test_add_node(self):
        """Adding nodes should work correctly."""
        from app.services.knowledge import (
            KnowledgePlane,
            KnowledgeNode,
            KnowledgeNodeType,
        )

        plane = KnowledgePlane(
            plane_id="plane-1",
            tenant_id="tenant-1",
            name="Test",
        )

        node = KnowledgeNode(
            node_id="node-1",
            node_type=KnowledgeNodeType.DOCUMENT,
            content="Doc",
        )

        plane.add_node(node)
        assert plane.node_count == 1
        assert plane.get_node("node-1") is not None

    def test_remove_node(self):
        """Removing nodes should work correctly."""
        from app.services.knowledge import (
            KnowledgePlane,
            KnowledgeNode,
            KnowledgeNodeType,
        )

        plane = KnowledgePlane(
            plane_id="plane-1",
            tenant_id="tenant-1",
            name="Test",
        )

        node = KnowledgeNode(
            node_id="node-1",
            node_type=KnowledgeNodeType.DOCUMENT,
            content="Doc",
        )

        plane.add_node(node)
        result = plane.remove_node("node-1")

        assert result is True
        assert plane.node_count == 0

    def test_add_source(self):
        """Adding sources should work correctly."""
        from app.services.knowledge import KnowledgePlane

        plane = KnowledgePlane(
            plane_id="plane-1",
            tenant_id="tenant-1",
            name="Test",
        )

        plane.add_source("source-1")
        assert "source-1" in plane.source_ids

    def test_status_lifecycle(self):
        """Status transitions should work correctly."""
        from app.services.knowledge import (
            KnowledgePlane,
            KnowledgePlaneStatus,
        )

        plane = KnowledgePlane(
            plane_id="plane-1",
            tenant_id="tenant-1",
            name="Test",
        )

        plane.activate()
        assert plane.status == KnowledgePlaneStatus.ACTIVE

        plane.start_indexing()
        assert plane.status == KnowledgePlaneStatus.INDEXING

        plane.finish_indexing(success=True)
        assert plane.status == KnowledgePlaneStatus.ACTIVE
        assert plane.last_indexed is not None

        plane.deactivate()
        assert plane.status == KnowledgePlaneStatus.INACTIVE

        plane.archive()
        assert plane.status == KnowledgePlaneStatus.ARCHIVED

    def test_error_handling(self):
        """Error recording should work correctly."""
        from app.services.knowledge import (
            KnowledgePlane,
            KnowledgePlaneStatus,
        )

        plane = KnowledgePlane(
            plane_id="plane-1",
            tenant_id="tenant-1",
            name="Test",
        )

        plane.record_error("Something failed")
        assert plane.status == KnowledgePlaneStatus.ERROR
        assert plane.last_error == "Something failed"

    def test_to_dict(self):
        """Plane should serialize to dict."""
        from app.services.knowledge import KnowledgePlane

        plane = KnowledgePlane(
            plane_id="plane-1",
            tenant_id="tenant-1",
            name="Test Plane",
            description="A test plane",
        )
        result = plane.to_dict()

        assert result["plane_id"] == "plane-1"
        assert result["name"] == "Test Plane"
        assert result["description"] == "A test plane"


class TestKnowledgePlaneRegistry:
    """Test KnowledgePlaneRegistry."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        from app.services.knowledge.knowledge_plane import _reset_registry
        _reset_registry()
        yield
        _reset_registry()

    def test_registry_creation(self):
        """Registry should be created."""
        from app.services.knowledge import KnowledgePlaneRegistry

        registry = KnowledgePlaneRegistry()
        assert registry is not None

    def test_register_plane(self):
        """Registering a plane should store it."""
        from app.services.knowledge import (
            KnowledgePlaneRegistry,
            KnowledgePlaneStatus,
        )

        registry = KnowledgePlaneRegistry()
        plane = registry.register(
            tenant_id="tenant-1",
            name="Test Plane",
        )

        assert plane.plane_id is not None
        assert plane.status == KnowledgePlaneStatus.CREATING

    def test_get_plane(self):
        """Getting a plane by ID should work."""
        from app.services.knowledge import KnowledgePlaneRegistry

        registry = KnowledgePlaneRegistry()
        plane = registry.register(
            tenant_id="tenant-1",
            name="Test",
        )

        retrieved = registry.get(plane.plane_id)
        assert retrieved is not None
        assert retrieved.plane_id == plane.plane_id

    def test_get_by_name(self):
        """Getting a plane by name should work."""
        from app.services.knowledge import KnowledgePlaneRegistry

        registry = KnowledgePlaneRegistry()
        registry.register(
            tenant_id="tenant-1",
            name="Named Plane",
        )

        plane = registry.get_by_name("tenant-1", "Named Plane")
        assert plane is not None
        assert plane.name == "Named Plane"

    def test_list_by_tenant(self):
        """Planes should be filterable by tenant."""
        from app.services.knowledge import KnowledgePlaneRegistry

        registry = KnowledgePlaneRegistry()

        for i in range(3):
            registry.register(tenant_id="tenant-1", name=f"Plane {i}")
        registry.register(tenant_id="tenant-2", name="Other")

        planes = registry.list(tenant_id="tenant-1")
        assert len(planes) == 3

    def test_list_by_status(self):
        """Planes should be filterable by status."""
        from app.services.knowledge import (
            KnowledgePlaneRegistry,
            KnowledgePlaneStatus,
        )

        registry = KnowledgePlaneRegistry()

        plane1 = registry.register(tenant_id="tenant-1", name="Active")
        plane1.activate()

        registry.register(tenant_id="tenant-1", name="Creating")

        active = registry.list(status=KnowledgePlaneStatus.ACTIVE)
        creating = registry.list(status=KnowledgePlaneStatus.CREATING)

        assert len(active) == 1
        assert len(creating) == 1

    def test_delete_plane(self):
        """Deleting should remove plane."""
        from app.services.knowledge import KnowledgePlaneRegistry

        registry = KnowledgePlaneRegistry()
        plane = registry.register(
            tenant_id="tenant-1",
            name="To Delete",
        )

        result = registry.delete(plane.plane_id)
        assert result is True
        assert registry.get(plane.plane_id) is None

    def test_get_statistics(self):
        """Statistics should be collected correctly."""
        from app.services.knowledge import KnowledgePlaneRegistry

        registry = KnowledgePlaneRegistry()

        for i in range(3):
            registry.register(tenant_id="tenant-1", name=f"Plane {i}")

        stats = registry.get_statistics()
        assert stats.total_planes == 3

    def test_clear_tenant(self):
        """Clearing tenant should remove all planes."""
        from app.services.knowledge import KnowledgePlaneRegistry

        registry = KnowledgePlaneRegistry()

        for i in range(3):
            registry.register(tenant_id="tenant-1", name=f"Plane {i}")

        cleared = registry.clear_tenant("tenant-1")
        assert cleared == 3
        assert len(registry.list(tenant_id="tenant-1")) == 0


class TestHelperFunctions:
    """Test module-level helper functions."""

    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        from app.services.knowledge.knowledge_plane import _reset_registry
        _reset_registry()
        yield
        _reset_registry()

    def test_create_knowledge_plane(self):
        """create_knowledge_plane should use singleton."""
        from app.services.knowledge import create_knowledge_plane

        plane = create_knowledge_plane(
            tenant_id="tenant-1",
            name="Test",
        )
        assert plane.plane_id is not None

    def test_get_knowledge_plane(self):
        """get_knowledge_plane should use singleton."""
        from app.services.knowledge import (
            create_knowledge_plane,
            get_knowledge_plane,
        )

        plane = create_knowledge_plane(
            tenant_id="tenant-1",
            name="Test",
        )

        retrieved = get_knowledge_plane(plane.plane_id)
        assert retrieved is not None

    def test_list_knowledge_planes(self):
        """list_knowledge_planes should use singleton."""
        from app.services.knowledge import (
            create_knowledge_plane,
            list_knowledge_planes,
        )

        for i in range(3):
            create_knowledge_plane(
                tenant_id="tenant-1",
                name=f"Plane {i}",
            )

        planes = list_knowledge_planes(tenant_id="tenant-1")
        assert len(planes) == 3
