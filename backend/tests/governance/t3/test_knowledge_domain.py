# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Role: Test T3 knowledge domain governance requirements (GAP-036 to GAP-045)
# Reference: DOMAINS_E2E_SCAFFOLD_V3.md, GAP_IMPLEMENTATION_PLAN_V1.md

"""
T3-008: Knowledge Domain Feature Tests (GAP-036 to GAP-045)

Tests the knowledge domain features:
- GAP-036: Knowledge Asset Model (asset_type, visibility, auth_ref, status)
- GAP-037: Knowledge Plane Model (sensitivity, allowed_use, default_policy)
- GAP-038: Knowledge Onboarding Lifecycle (REGISTER → VERIFY → ... → GOVERN)
- GAP-039: Asset Verification Gate (credentials validation)
- GAP-040: Ingestion & Indexing Pipeline (chunking, PII detection)
- GAP-041: Plane Activation Gate (owner confirmation, default=DENY)
- GAP-042: Policy → Plane Binding (policies reference plane_id)
- GAP-043: Knowledge Plane Selection UI (API models)
- GAP-044: Public vs Private Knowledge Defaults
- GAP-045: Multi-Asset Single-Plane Aggregation

Key Principle:
> Knowledge assets require policy-aware governance from onboarding through retrieval.
"""

from datetime import datetime, timezone

import pytest

from app.hoc.cus.hoc_spine.orchestrator.lifecycle.drivers.knowledge_plane import (
    KnowledgeNode,
    KnowledgeNodeType,
    KnowledgePlane,
    KnowledgePlaneError,
    KnowledgePlaneRegistry,
    KnowledgePlaneStats,
    KnowledgePlaneStatus,
    _reset_registry,
    create_knowledge_plane,
    get_knowledge_plane,
    get_knowledge_plane_registry,
    list_knowledge_planes,
)


# ===========================================================================
# Test: Import Verification
# ===========================================================================


class TestKnowledgeDomainImports:
    """Verify all knowledge domain imports are accessible."""

    def test_knowledge_plane_import(self) -> None:
        """Test KnowledgePlane dataclass is importable."""
        assert KnowledgePlane is not None

    def test_knowledge_node_import(self) -> None:
        """Test KnowledgeNode dataclass is importable."""
        assert KnowledgeNode is not None

    def test_knowledge_plane_status_import(self) -> None:
        """Test KnowledgePlaneStatus enum is importable."""
        assert KnowledgePlaneStatus is not None

    def test_knowledge_node_type_import(self) -> None:
        """Test KnowledgeNodeType enum is importable."""
        assert KnowledgeNodeType is not None

    def test_knowledge_plane_registry_import(self) -> None:
        """Test KnowledgePlaneRegistry class is importable."""
        assert KnowledgePlaneRegistry is not None

    def test_knowledge_plane_error_import(self) -> None:
        """Test KnowledgePlaneError exception is importable."""
        assert KnowledgePlaneError is not None

    def test_knowledge_plane_stats_import(self) -> None:
        """Test KnowledgePlaneStats dataclass is importable."""
        assert KnowledgePlaneStats is not None


# ===========================================================================
# GAP-036: Knowledge Asset Model (Pattern Reference)
# ===========================================================================


class TestGAP036KnowledgeAssetModel:
    """
    GAP-036: Knowledge Asset Model

    CURRENT: KnowledgeNode exists for in-graph nodes
    REQUIRED: KnowledgeAsset model with asset_type, visibility, auth_ref, status

    Note: The system has KnowledgeNode for graph nodes but not a separate
    KnowledgeAsset model for external source registration.
    """

    def test_knowledge_node_has_source_tracking(self) -> None:
        """KnowledgeNode tracks source origin."""
        node = KnowledgeNode(
            node_id="node-001",
            node_type=KnowledgeNodeType.DOCUMENT,
            content="Test content",
            source_id="source-001",
            source_type="s3",
        )
        assert node.source_id == "source-001"
        assert node.source_type == "s3"

    def test_knowledge_node_has_metadata(self) -> None:
        """KnowledgeNode supports metadata storage."""
        node = KnowledgeNode(
            node_id="node-001",
            node_type=KnowledgeNodeType.DOCUMENT,
            content="Test content",
            metadata={
                "visibility": "private",
                "auth_ref": "cred-001",
                "asset_type": "s3",
            },
        )
        assert node.metadata["visibility"] == "private"
        assert node.metadata["auth_ref"] == "cred-001"
        assert node.metadata["asset_type"] == "s3"

    def test_knowledge_node_types_cover_asset_types(self) -> None:
        """KnowledgeNodeType enum covers document types."""
        assert KnowledgeNodeType.DOCUMENT is not None
        assert KnowledgeNodeType.SECTION is not None
        assert KnowledgeNodeType.PARAGRAPH is not None
        assert KnowledgeNodeType.ENTITY is not None
        assert KnowledgeNodeType.CONCEPT is not None
        assert KnowledgeNodeType.FACT is not None

    def test_knowledge_plane_has_source_ids(self) -> None:
        """KnowledgePlane tracks source assets."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
        )
        plane.add_source("s3://bucket/path")
        plane.add_source("postgres://db/table")
        assert len(plane.source_ids) == 2


# ===========================================================================
# GAP-037: Knowledge Plane Model (Policy-Aware)
# ===========================================================================


class TestGAP037KnowledgePlaneModel:
    """
    GAP-037: Knowledge Plane Model

    CURRENT: KnowledgePlane has basic fields
    REQUIRED: Policy-aware abstraction with sensitivity, allowed_use, default_policy

    Note: The plane model exists but doesn't have explicit policy bindings.
    Policy awareness can be added via metadata or extension.
    """

    def test_knowledge_plane_has_tenant_isolation(self) -> None:
        """KnowledgePlane has tenant_id for isolation."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
        )
        assert plane.tenant_id == "tenant-001"

    def test_knowledge_plane_has_tags(self) -> None:
        """KnowledgePlane supports tags for categorization."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
            tags=["sensitive", "internal", "hr-data"],
        )
        assert "sensitive" in plane.tags
        assert "internal" in plane.tags

    def test_knowledge_plane_has_metadata_for_policy(self) -> None:
        """KnowledgePlane metadata can store policy references."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
            metadata={
                "sensitivity": "confidential",
                "allowed_use": ["retrieval", "qa"],
                "default_policy": "POL-001",
            },
        )
        assert plane.metadata["sensitivity"] == "confidential"
        assert "retrieval" in plane.metadata["allowed_use"]
        assert plane.metadata["default_policy"] == "POL-001"

    def test_knowledge_plane_has_embedding_config(self) -> None:
        """KnowledgePlane has embedding configuration."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
        )
        assert plane.embedding_model == "text-embedding-ada-002"
        assert plane.embedding_dimension == 1536


# ===========================================================================
# GAP-038: Knowledge Onboarding Lifecycle
# ===========================================================================


class TestGAP038OnboardingLifecycle:
    """
    GAP-038: Knowledge Onboarding Lifecycle

    CURRENT: Plane has status lifecycle (CREATING → ACTIVE → etc.)
    REQUIRED: Full pipeline: REGISTER → VERIFY → INGEST → INDEX → CLASSIFY → ACTIVATE → GOVERN

    Note: Current lifecycle covers most states via KnowledgePlaneStatus.
    """

    def test_status_creating(self) -> None:
        """CREATING status exists (equivalent to REGISTER)."""
        assert KnowledgePlaneStatus.CREATING.value == "creating"

    def test_status_indexing(self) -> None:
        """INDEXING status exists (covers INGEST/INDEX)."""
        assert KnowledgePlaneStatus.INDEXING.value == "indexing"

    def test_status_active(self) -> None:
        """ACTIVE status exists (equivalent to ACTIVATE)."""
        assert KnowledgePlaneStatus.ACTIVE.value == "active"

    def test_status_updating(self) -> None:
        """UPDATING status exists for re-indexing."""
        assert KnowledgePlaneStatus.UPDATING.value == "updating"

    def test_status_inactive(self) -> None:
        """INACTIVE status exists for temporary disable."""
        assert KnowledgePlaneStatus.INACTIVE.value == "inactive"

    def test_status_error(self) -> None:
        """ERROR status exists for failure states."""
        assert KnowledgePlaneStatus.ERROR.value == "error"

    def test_status_archived(self) -> None:
        """ARCHIVED status exists for end-of-life."""
        assert KnowledgePlaneStatus.ARCHIVED.value == "archived"

    def test_lifecycle_creating_to_active(self) -> None:
        """Plane can transition from CREATING to ACTIVE."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
        )
        assert plane.status == KnowledgePlaneStatus.CREATING
        plane.activate()
        assert plane.status == KnowledgePlaneStatus.ACTIVE

    def test_lifecycle_active_to_indexing(self) -> None:
        """Plane can transition from ACTIVE to INDEXING."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
        )
        plane.activate()
        plane.start_indexing()
        assert plane.status == KnowledgePlaneStatus.INDEXING

    def test_lifecycle_indexing_success(self) -> None:
        """Plane transitions to ACTIVE after successful indexing."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
        )
        plane.start_indexing()
        plane.finish_indexing(success=True)
        assert plane.status == KnowledgePlaneStatus.ACTIVE
        assert plane.last_indexed is not None

    def test_lifecycle_indexing_failure(self) -> None:
        """Plane transitions to ERROR after failed indexing."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
        )
        plane.start_indexing()
        plane.finish_indexing(success=False, error="Connection timeout")
        assert plane.status == KnowledgePlaneStatus.ERROR
        assert plane.last_error == "Connection timeout"

    def test_lifecycle_deactivation(self) -> None:
        """Plane can be deactivated."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
        )
        plane.activate()
        plane.deactivate()
        assert plane.status == KnowledgePlaneStatus.INACTIVE

    def test_lifecycle_archival(self) -> None:
        """Plane can be archived."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
        )
        plane.archive()
        assert plane.status == KnowledgePlaneStatus.ARCHIVED


# ===========================================================================
# GAP-039: Asset Verification Gate
# ===========================================================================


class TestGAP039AssetVerification:
    """
    GAP-039: Asset Verification Gate

    CURRENT: No explicit verification gate
    REQUIRED: Validate credentials, test read-only access before ingestion

    Note: The error recording mechanism exists for failed verification.
    Verification logic would be added in the onboarding service.
    """

    def test_plane_can_record_error(self) -> None:
        """Plane can record verification errors."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
        )
        plane.record_error("Invalid credentials for S3 bucket")
        assert plane.status == KnowledgePlaneStatus.ERROR
        assert "Invalid credentials" in plane.last_error

    def test_plane_error_has_timestamp(self) -> None:
        """Error recording updates timestamp."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
        )
        initial_updated = plane.updated_at
        plane.record_error("Verification failed")
        assert plane.updated_at >= initial_updated

    def test_plane_error_exception_has_context(self) -> None:
        """KnowledgePlaneError carries context."""
        error = KnowledgePlaneError(
            message="Access denied to vector DB",
            plane_id="plane-001",
        )
        assert error.plane_id == "plane-001"
        assert "Access denied" in error.message

    def test_plane_error_serializable(self) -> None:
        """KnowledgePlaneError can be serialized."""
        error = KnowledgePlaneError(
            message="Invalid API key",
            plane_id="plane-001",
        )
        error_dict = error.to_dict()
        assert error_dict["error"] == "Invalid API key"
        assert error_dict["plane_id"] == "plane-001"


# ===========================================================================
# GAP-040: Ingestion & Indexing Pipeline
# ===========================================================================


class TestGAP040IngestionPipeline:
    """
    GAP-040: Ingestion & Indexing Pipeline

    CURRENT: Basic node storage in memory
    REQUIRED: Chunking, PII detection, content hashing, external source indexing

    Note: Node model supports content storage. Hashing and PII detection
    would be added as preprocessing steps.
    """

    def test_node_can_store_content_hash(self) -> None:
        """KnowledgeNode can store content hash via metadata."""
        node = KnowledgeNode(
            node_id="node-001",
            node_type=KnowledgeNodeType.PARAGRAPH,
            content="Some text",
            metadata={
                "content_hash": "sha256:abc123...",
            },
        )
        assert "content_hash" in node.metadata

    def test_node_can_store_embedding(self) -> None:
        """KnowledgeNode can store embedding vectors."""
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        node = KnowledgeNode(
            node_id="node-001",
            node_type=KnowledgeNodeType.PARAGRAPH,
            content="Some text",
            embedding=embedding,
        )
        assert node.embedding is not None
        assert len(node.embedding) == 5

    def test_node_to_dict_indicates_embedding(self) -> None:
        """Serialized node indicates if embedding exists."""
        node = KnowledgeNode(
            node_id="node-001",
            node_type=KnowledgeNodeType.PARAGRAPH,
            content="Some text",
            embedding=[0.1] * 1536,
        )
        node_dict = node.to_dict()
        assert node_dict["has_embedding"] is True

    def test_plane_tracks_document_count(self) -> None:
        """Plane tracks document count for indexing progress."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
        )
        plane.document_count = 100
        assert plane.document_count == 100

    def test_plane_tracks_last_indexed(self) -> None:
        """Plane tracks last indexing timestamp."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
        )
        plane.start_indexing()
        plane.finish_indexing(success=True)
        assert plane.last_indexed is not None


# ===========================================================================
# GAP-041: Plane Activation Gate
# ===========================================================================


class TestGAP041ActivationGate:
    """
    GAP-041: Plane Activation Gate

    CURRENT: Activate method exists
    REQUIRED: Owner confirmation, default=DENY, audit log on activation

    Note: The activation transition exists. Owner confirmation and
    audit logging would be added at the service layer.
    """

    def test_plane_starts_inactive(self) -> None:
        """New plane starts in CREATING status (not active)."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
        )
        assert plane.status == KnowledgePlaneStatus.CREATING
        assert plane.status != KnowledgePlaneStatus.ACTIVE

    def test_activation_clears_error(self) -> None:
        """Activating a plane clears any previous error."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
        )
        plane.record_error("Previous error")
        plane.activate()
        assert plane.last_error is None

    def test_activation_updates_timestamp(self) -> None:
        """Activation updates the updated_at timestamp."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
        )
        initial = plane.updated_at
        plane.activate()
        assert plane.updated_at >= initial

    def test_deactivation_available(self) -> None:
        """Plane can be deactivated after activation."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
        )
        plane.activate()
        plane.deactivate()
        assert plane.status == KnowledgePlaneStatus.INACTIVE


# ===========================================================================
# GAP-042: Policy → Plane Binding
# ===========================================================================


class TestGAP042PolicyPlaneBinding:
    """
    GAP-042: Policy → Plane Binding

    CURRENT: MonitorConfig has allowed_rag_sources (string list)
    REQUIRED: Policies reference KnowledgePlane.plane_id

    Note: Binding can be implemented via metadata or a dedicated field.
    """

    def test_plane_has_unique_id(self) -> None:
        """KnowledgePlane has unique plane_id for reference."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
        )
        assert plane.plane_id == "plane-001"

    def test_plane_can_store_policy_reference(self) -> None:
        """Plane metadata can store policy reference."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
            metadata={
                "bound_policies": ["POL-001", "POL-002"],
            },
        )
        assert "POL-001" in plane.metadata["bound_policies"]

    def test_registry_lookup_by_id(self) -> None:
        """Registry can look up plane by ID for policy validation."""
        registry = KnowledgePlaneRegistry()
        plane = registry.register(
            tenant_id="tenant-001",
            name="Test Plane",
            plane_id="plane-binding-test",
        )
        retrieved = registry.get("plane-binding-test")
        assert retrieved is not None
        assert retrieved.plane_id == "plane-binding-test"


# ===========================================================================
# GAP-043: Knowledge Plane Selection UI (API Models)
# ===========================================================================


class TestGAP043PlaneSelectionUI:
    """
    GAP-043: Knowledge Plane Selection UI

    CURRENT: Plane and registry models exist
    REQUIRED: Asset onboarding wizard, plane management UI

    Note: The backend models support UI integration via to_dict methods.
    """

    def test_plane_serializable(self) -> None:
        """KnowledgePlane can be serialized for API response."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
            description="A test plane for UI",
        )
        plane_dict = plane.to_dict()
        assert "plane_id" in plane_dict
        assert "name" in plane_dict
        assert "description" in plane_dict
        assert "status" in plane_dict

    def test_node_serializable(self) -> None:
        """KnowledgeNode can be serialized for API response."""
        node = KnowledgeNode(
            node_id="node-001",
            node_type=KnowledgeNodeType.DOCUMENT,
            content="Test content",
        )
        node_dict = node.to_dict()
        assert "node_id" in node_dict
        assert "node_type" in node_dict
        assert "content" in node_dict

    def test_stats_serializable(self) -> None:
        """KnowledgePlaneStats can be serialized for dashboard."""
        stats = KnowledgePlaneStats(
            total_planes=10,
            active_planes=7,
            indexing_planes=2,
            error_planes=1,
            total_nodes=5000,
            total_documents=200,
        )
        stats_dict = stats.to_dict()
        assert stats_dict["total_planes"] == 10
        assert stats_dict["active_planes"] == 7

    def test_error_serializable(self) -> None:
        """KnowledgePlaneError can be serialized for error display."""
        error = KnowledgePlaneError(
            message="Failed to connect",
            plane_id="plane-001",
        )
        error_dict = error.to_dict()
        assert "error" in error_dict
        assert "plane_id" in error_dict


# ===========================================================================
# GAP-044: Public vs Private Knowledge Defaults
# ===========================================================================


class TestGAP044VisibilityDefaults:
    """
    GAP-044: Public vs Private Knowledge Defaults

    CURRENT: No explicit visibility field
    REQUIRED: Public=allow by default, Private=deny by default

    Note: Visibility can be stored in metadata or tags.
    """

    def test_plane_can_have_visibility_tag(self) -> None:
        """Plane can use tags for visibility."""
        public_plane = KnowledgePlane(
            plane_id="plane-public",
            tenant_id="tenant-001",
            name="Public Knowledge",
            tags=["public"],
        )
        private_plane = KnowledgePlane(
            plane_id="plane-private",
            tenant_id="tenant-001",
            name="Private Knowledge",
            tags=["private", "restricted"],
        )
        assert "public" in public_plane.tags
        assert "private" in private_plane.tags

    def test_plane_can_have_visibility_metadata(self) -> None:
        """Plane can use metadata for visibility."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
            metadata={
                "visibility": "private",
                "default_access": "deny",
            },
        )
        assert plane.metadata["visibility"] == "private"
        assert plane.metadata["default_access"] == "deny"

    def test_node_can_inherit_visibility(self) -> None:
        """Node can store visibility from source."""
        node = KnowledgeNode(
            node_id="node-001",
            node_type=KnowledgeNodeType.DOCUMENT,
            content="Sensitive data",
            metadata={
                "visibility": "private",
                "source_visibility": "inherited",
            },
        )
        assert node.metadata["visibility"] == "private"


# ===========================================================================
# GAP-045: Multi-Asset Single-Plane Aggregation
# ===========================================================================


class TestGAP045MultiAssetAggregation:
    """
    GAP-045: Multi-Asset Single-Plane Aggregation

    CURRENT: Plane has source_ids list
    REQUIRED: Single plane can aggregate multiple assets

    Note: The source_ids field already supports this pattern.
    """

    @pytest.fixture(autouse=True)
    def reset_registry(self) -> None:
        """Reset registry before each test."""
        _reset_registry()
        yield
        _reset_registry()

    def test_plane_can_have_multiple_sources(self) -> None:
        """Plane can aggregate multiple source assets."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Multi-Source Plane",
        )
        plane.add_source("s3://bucket1/docs")
        plane.add_source("s3://bucket2/reports")
        plane.add_source("postgres://db/knowledge")
        assert len(plane.source_ids) == 3

    def test_plane_source_deduplication(self) -> None:
        """Adding duplicate source is idempotent."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
        )
        plane.add_source("s3://bucket/path")
        plane.add_source("s3://bucket/path")  # Duplicate
        assert len(plane.source_ids) == 1

    def test_plane_source_removal(self) -> None:
        """Source can be removed from plane."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
        )
        plane.add_source("s3://bucket1")
        plane.add_source("s3://bucket2")
        result = plane.remove_source("s3://bucket1")
        assert result is True
        assert len(plane.source_ids) == 1
        assert "s3://bucket2" in plane.source_ids

    def test_nodes_can_track_source(self) -> None:
        """Nodes can track which source they came from."""
        node1 = KnowledgeNode(
            node_id="node-001",
            node_type=KnowledgeNodeType.DOCUMENT,
            content="From S3",
            source_id="s3://bucket/doc1",
        )
        node2 = KnowledgeNode(
            node_id="node-002",
            node_type=KnowledgeNodeType.DOCUMENT,
            content="From Postgres",
            source_id="postgres://db/table/row1",
        )
        assert node1.source_id != node2.source_id


# ===========================================================================
# Test: Registry Operations
# ===========================================================================


class TestKnowledgePlaneRegistryOperations:
    """Test KnowledgePlaneRegistry for plane management."""

    @pytest.fixture(autouse=True)
    def reset_registry(self) -> None:
        """Reset registry before each test."""
        _reset_registry()
        yield
        _reset_registry()

    def test_registry_register(self) -> None:
        """Registry can register a new plane."""
        registry = KnowledgePlaneRegistry()
        plane = registry.register(
            tenant_id="tenant-001",
            name="Test Plane",
            description="A test plane",
        )
        assert plane.plane_id is not None
        assert plane.tenant_id == "tenant-001"
        assert plane.name == "Test Plane"

    def test_registry_get_by_id(self) -> None:
        """Registry can retrieve plane by ID."""
        registry = KnowledgePlaneRegistry()
        plane = registry.register(
            tenant_id="tenant-001",
            name="Test Plane",
        )
        retrieved = registry.get(plane.plane_id)
        assert retrieved is not None
        assert retrieved.name == "Test Plane"

    def test_registry_get_by_name(self) -> None:
        """Registry can retrieve plane by name within tenant."""
        registry = KnowledgePlaneRegistry()
        registry.register(
            tenant_id="tenant-001",
            name="Named Plane",
        )
        plane = registry.get_by_name("tenant-001", "Named Plane")
        assert plane is not None
        assert plane.name == "Named Plane"

    def test_registry_list_by_tenant(self) -> None:
        """Registry can list planes filtered by tenant."""
        registry = KnowledgePlaneRegistry()
        registry.register(tenant_id="tenant-001", name="Plane A")
        registry.register(tenant_id="tenant-001", name="Plane B")
        registry.register(tenant_id="tenant-002", name="Other")
        planes = registry.list(tenant_id="tenant-001")
        assert len(planes) == 2

    def test_registry_list_by_status(self) -> None:
        """Registry can list planes filtered by status."""
        registry = KnowledgePlaneRegistry()
        plane1 = registry.register(tenant_id="tenant-001", name="Active")
        plane1.activate()
        registry.register(tenant_id="tenant-001", name="Creating")
        active_planes = registry.list(status=KnowledgePlaneStatus.ACTIVE)
        assert len(active_planes) == 1

    def test_registry_delete(self) -> None:
        """Registry can delete a plane."""
        registry = KnowledgePlaneRegistry()
        plane = registry.register(
            tenant_id="tenant-001",
            name="To Delete",
        )
        result = registry.delete(plane.plane_id)
        assert result is True
        assert registry.get(plane.plane_id) is None

    def test_registry_statistics(self) -> None:
        """Registry can compute statistics."""
        registry = KnowledgePlaneRegistry()
        plane1 = registry.register(tenant_id="tenant-001", name="Active")
        plane1.activate()
        registry.register(tenant_id="tenant-001", name="Creating")
        plane3 = registry.register(tenant_id="tenant-001", name="Indexing")
        plane3.start_indexing()
        stats = registry.get_statistics(tenant_id="tenant-001")
        assert stats.total_planes == 3
        assert stats.active_planes == 1
        assert stats.indexing_planes == 1

    def test_registry_clear_tenant(self) -> None:
        """Registry can clear all planes for a tenant."""
        registry = KnowledgePlaneRegistry()
        for i in range(5):
            registry.register(tenant_id="tenant-001", name=f"Plane {i}")
        registry.register(tenant_id="tenant-002", name="Other")
        cleared = registry.clear_tenant("tenant-001")
        assert cleared == 5
        assert len(registry.list(tenant_id="tenant-001")) == 0
        assert len(registry.list(tenant_id="tenant-002")) == 1


# ===========================================================================
# Test: Helper Functions
# ===========================================================================


class TestKnowledgePlaneHelpers:
    """Test module-level helper functions."""

    @pytest.fixture(autouse=True)
    def reset_registry(self) -> None:
        """Reset registry before each test."""
        _reset_registry()
        yield
        _reset_registry()

    def test_create_knowledge_plane_function(self) -> None:
        """create_knowledge_plane uses singleton registry."""
        plane = create_knowledge_plane(
            tenant_id="tenant-001",
            name="Test",
        )
        assert plane.plane_id is not None

    def test_get_knowledge_plane_function(self) -> None:
        """get_knowledge_plane uses singleton registry."""
        plane = create_knowledge_plane(
            tenant_id="tenant-001",
            name="Test",
        )
        retrieved = get_knowledge_plane(plane.plane_id)
        assert retrieved is not None
        assert retrieved.plane_id == plane.plane_id

    def test_list_knowledge_planes_function(self) -> None:
        """list_knowledge_planes uses singleton registry."""
        for i in range(3):
            create_knowledge_plane(
                tenant_id="tenant-001",
                name=f"Plane {i}",
            )
        planes = list_knowledge_planes(tenant_id="tenant-001")
        assert len(planes) == 3

    def test_get_knowledge_plane_registry_singleton(self) -> None:
        """get_knowledge_plane_registry returns singleton."""
        registry1 = get_knowledge_plane_registry()
        registry2 = get_knowledge_plane_registry()
        assert registry1 is registry2


# ===========================================================================
# Test: Knowledge Node Operations
# ===========================================================================


class TestKnowledgeNodeOperations:
    """Test KnowledgeNode dataclass operations."""

    def test_node_creation(self) -> None:
        """Node can be created with required fields."""
        node = KnowledgeNode(
            node_id="node-001",
            node_type=KnowledgeNodeType.DOCUMENT,
            content="Test content",
        )
        assert node.node_id == "node-001"
        assert node.node_type == KnowledgeNodeType.DOCUMENT

    def test_node_add_child(self) -> None:
        """Node can add child references."""
        node = KnowledgeNode(
            node_id="parent",
            node_type=KnowledgeNodeType.DOCUMENT,
            content="Parent doc",
        )
        node.add_child("child-001")
        node.add_child("child-002")
        assert len(node.child_ids) == 2

    def test_node_add_child_deduplication(self) -> None:
        """Adding duplicate child is idempotent."""
        node = KnowledgeNode(
            node_id="parent",
            node_type=KnowledgeNodeType.DOCUMENT,
            content="Parent doc",
        )
        node.add_child("child-001")
        node.add_child("child-001")
        assert len(node.child_ids) == 1

    def test_node_add_related(self) -> None:
        """Node can add related references."""
        node = KnowledgeNode(
            node_id="node-001",
            node_type=KnowledgeNodeType.CONCEPT,
            content="Concept",
        )
        node.add_related("node-002")
        assert "node-002" in node.related_ids

    def test_node_types_complete(self) -> None:
        """All KnowledgeNodeType values are accessible."""
        types = [
            KnowledgeNodeType.DOCUMENT,
            KnowledgeNodeType.SECTION,
            KnowledgeNodeType.PARAGRAPH,
            KnowledgeNodeType.ENTITY,
            KnowledgeNodeType.CONCEPT,
            KnowledgeNodeType.FACT,
            KnowledgeNodeType.RELATION,
        ]
        assert len(types) == 7


# ===========================================================================
# Test: Plane Node Management
# ===========================================================================


class TestPlaneNodeManagement:
    """Test node management within planes."""

    def test_plane_add_node(self) -> None:
        """Plane can add nodes."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
        )
        node = KnowledgeNode(
            node_id="node-001",
            node_type=KnowledgeNodeType.DOCUMENT,
            content="Test doc",
        )
        plane.add_node(node)
        assert plane.node_count == 1

    def test_plane_get_node(self) -> None:
        """Plane can retrieve node by ID."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
        )
        node = KnowledgeNode(
            node_id="node-001",
            node_type=KnowledgeNodeType.DOCUMENT,
            content="Test doc",
        )
        plane.add_node(node)
        retrieved = plane.get_node("node-001")
        assert retrieved is not None
        assert retrieved.content == "Test doc"

    def test_plane_remove_node(self) -> None:
        """Plane can remove nodes."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
        )
        node = KnowledgeNode(
            node_id="node-001",
            node_type=KnowledgeNodeType.DOCUMENT,
            content="Test doc",
        )
        plane.add_node(node)
        result = plane.remove_node("node-001")
        assert result is True
        assert plane.node_count == 0
        assert plane.get_node("node-001") is None

    def test_plane_node_count_accuracy(self) -> None:
        """Plane accurately tracks node count."""
        plane = KnowledgePlane(
            plane_id="plane-001",
            tenant_id="tenant-001",
            name="Test Plane",
        )
        for i in range(10):
            node = KnowledgeNode(
                node_id=f"node-{i}",
                node_type=KnowledgeNodeType.PARAGRAPH,
                content=f"Paragraph {i}",
            )
            plane.add_node(node)
        assert plane.node_count == 10
