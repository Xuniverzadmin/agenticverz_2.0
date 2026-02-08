# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Role: T4 Onboarding Stage Tests (GAP-071 to GAP-077)
# Reference: GAP_IMPLEMENTATION_PLAN_V1.md Step 2

"""
T4 Onboarding Stage Tests

Tests for the "dumb plugin" onboarding stage handlers.

These tests verify that:
1. Stage handlers only return success/failure (they don't manage state)
2. Stage handlers validate their inputs correctly
3. Stage handlers don't emit events or check policies
4. Stage handlers can execute from their designated states

Test Categories:
- RegisterHandler tests (GAP-071)
- VerifyHandler tests (GAP-072)
- IngestHandler tests (GAP-073)
- IndexHandler tests (GAP-074)
- ClassifyHandler tests (GAP-075)
- ActivateHandler tests (GAP-076)
- GovernHandler tests (GAP-077)
- StageRegistry tests
"""

import pytest

from app.models.knowledge_lifecycle import KnowledgePlaneLifecycleState
from app.hoc.cus.hoc_spine.orchestrator.lifecycle.stages import (
    StageContext,
    StageResult,
    StageRegistry,
    RegisterHandler,
    VerifyHandler,
    IngestHandler,
    IndexHandler,
    ClassifyHandler,
    ActivateHandler,
    GovernHandler,
    StageStatus,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def register_handler() -> RegisterHandler:
    """Create a RegisterHandler instance."""
    return RegisterHandler()


@pytest.fixture
def verify_handler() -> VerifyHandler:
    """Create a VerifyHandler instance."""
    return VerifyHandler()


@pytest.fixture
def ingest_handler() -> IngestHandler:
    """Create an IngestHandler instance."""
    return IngestHandler()


@pytest.fixture
def index_handler() -> IndexHandler:
    """Create an IndexHandler instance."""
    return IndexHandler()


@pytest.fixture
def classify_handler() -> ClassifyHandler:
    """Create a ClassifyHandler instance."""
    return ClassifyHandler()


@pytest.fixture
def activate_handler() -> ActivateHandler:
    """Create an ActivateHandler instance."""
    return ActivateHandler()


@pytest.fixture
def govern_handler() -> GovernHandler:
    """Create a GovernHandler instance."""
    return GovernHandler()


@pytest.fixture
def stage_registry() -> StageRegistry:
    """Create a StageRegistry with default handlers."""
    return StageRegistry.create_default()


def make_context(
    plane_id: str = "kp_test",
    tenant_id: str = "tenant-123",
    current_state: KnowledgePlaneLifecycleState = KnowledgePlaneLifecycleState.DRAFT,
    target_state: KnowledgePlaneLifecycleState = KnowledgePlaneLifecycleState.PENDING_VERIFY,
    **kwargs
) -> StageContext:
    """Helper to create StageContext."""
    return StageContext(
        plane_id=plane_id,
        tenant_id=tenant_id,
        current_state=current_state,
        target_state=target_state,
        **kwargs,
    )


# =============================================================================
# RegisterHandler Tests (GAP-071)
# =============================================================================


class TestRegisterHandler:
    """Tests for RegisterHandler (GAP-071)."""

    async def test_register_returns_stage_result(self, register_handler: RegisterHandler):
        """Register returns StageResult, not state changes."""
        context = make_context(
            config={"name": "Test Plane", "source_type": "s3"},
        )
        result = await register_handler.execute(context)

        assert isinstance(result, StageResult)
        assert result.status == StageStatus.SUCCESS

    async def test_register_validates_tenant_id(self, register_handler: RegisterHandler):
        """Register requires tenant_id."""
        context = make_context(
            tenant_id="",  # Empty tenant
            config={"name": "Test Plane"},
        )
        error = await register_handler.validate(context)
        assert error is not None
        assert "tenant_id" in error.lower()

    async def test_register_validates_config(self, register_handler: RegisterHandler):
        """Register requires config with name or source_type."""
        context = make_context(config={})  # Empty config
        error = await register_handler.validate(context)
        assert error is not None
        assert "name" in error.lower() or "source_type" in error.lower()

    async def test_register_returns_registration_data(self, register_handler: RegisterHandler):
        """Register returns registration data in result."""
        context = make_context(
            config={"name": "My Knowledge Plane", "source_type": "database"},
            actor_id="user-123",
        )
        result = await register_handler.execute(context)

        assert result.success
        assert "registration_data" in result.data
        assert result.data["registration_data"]["name"] == "My Knowledge Plane"
        assert result.data["registration_data"]["source_type"] == "database"

    async def test_register_generates_name_if_missing(self, register_handler: RegisterHandler):
        """Register generates name if not provided."""
        context = make_context(
            plane_id="kp_abc123",
            config={"source_type": "s3"},
        )
        result = await register_handler.execute(context)

        assert result.success
        assert "kp_abc123" in result.data["registration_data"]["name"]

    async def test_register_stage_name(self, register_handler: RegisterHandler):
        """Register has correct stage name."""
        assert register_handler.stage_name == "register"


# =============================================================================
# VerifyHandler Tests (GAP-072)
# =============================================================================


class TestVerifyHandler:
    """Tests for VerifyHandler (GAP-072)."""

    async def test_verify_returns_stage_result(self, verify_handler: VerifyHandler):
        """Verify returns StageResult, not state changes."""
        context = make_context(
            current_state=KnowledgePlaneLifecycleState.DRAFT,
            config={"source_type": "s3"},
        )
        result = await verify_handler.execute(context)

        assert isinstance(result, StageResult)
        assert result.status == StageStatus.SUCCESS

    async def test_verify_handles_draft_state(self, verify_handler: VerifyHandler):
        """Verify handles DRAFT state."""
        assert KnowledgePlaneLifecycleState.DRAFT in verify_handler.handles_states

    async def test_verify_validates_config_exists(self, verify_handler: VerifyHandler):
        """Verify requires configuration."""
        context = make_context(config=None)
        error = await verify_handler.validate(context)
        assert error is not None
        assert "configuration" in error.lower()

    async def test_verify_returns_verification_data(self, verify_handler: VerifyHandler):
        """Verify returns verification data in result."""
        context = make_context(
            current_state=KnowledgePlaneLifecycleState.DRAFT,
            config={"source_type": "database"},
        )
        result = await verify_handler.execute(context)

        assert result.success
        assert "verified_at" in result.data
        assert "source_type" in result.data

    async def test_verify_reports_connection_latency(self, verify_handler: VerifyHandler):
        """Verify reports connection latency."""
        context = make_context(
            current_state=KnowledgePlaneLifecycleState.DRAFT,
            config={"source_type": "s3"},
        )
        result = await verify_handler.execute(context)

        assert result.success
        assert "connection_latency_ms" in result.data
        assert result.data["connection_latency_ms"] >= 0

    async def test_verify_rejects_wrong_state(self, verify_handler: VerifyHandler):
        """Verify rejects execution from wrong state."""
        context = make_context(
            current_state=KnowledgePlaneLifecycleState.ACTIVE,  # Wrong state
            config={"source_type": "s3"},
        )
        error = await verify_handler.validate(context)
        assert error is not None
        assert "DRAFT" in error

    async def test_verify_stage_name(self, verify_handler: VerifyHandler):
        """Verify has correct stage name."""
        assert verify_handler.stage_name == "verify"


# =============================================================================
# IngestHandler Tests (GAP-073)
# =============================================================================


class TestIngestHandler:
    """Tests for IngestHandler (GAP-073)."""

    async def test_ingest_returns_stage_result(self, ingest_handler: IngestHandler):
        """Ingest returns StageResult, not state changes."""
        context = make_context(
            current_state=KnowledgePlaneLifecycleState.VERIFIED,
            config={"source_type": "s3"},
        )
        result = await ingest_handler.execute(context)

        assert isinstance(result, StageResult)
        assert result.status == StageStatus.SUCCESS

    async def test_ingest_handles_verified_state(self, ingest_handler: IngestHandler):
        """Ingest handles VERIFIED state."""
        assert KnowledgePlaneLifecycleState.VERIFIED in ingest_handler.handles_states

    async def test_ingest_returns_record_count(self, ingest_handler: IngestHandler):
        """Ingest returns record count."""
        context = make_context(
            current_state=KnowledgePlaneLifecycleState.VERIFIED,
            config={"source_type": "database"},
        )
        result = await ingest_handler.execute(context)

        assert result.success
        assert "records_ingested" in result.data
        assert result.data["records_ingested"] > 0

    async def test_ingest_returns_bytes_processed(self, ingest_handler: IngestHandler):
        """Ingest returns bytes processed."""
        context = make_context(
            current_state=KnowledgePlaneLifecycleState.VERIFIED,
            config={"source_type": "s3"},
        )
        result = await ingest_handler.execute(context)

        assert result.success
        assert "bytes_processed" in result.data
        assert result.data["bytes_processed"] > 0

    async def test_ingest_stage_name(self, ingest_handler: IngestHandler):
        """Ingest has correct stage name."""
        assert ingest_handler.stage_name == "ingest"


# =============================================================================
# IndexHandler Tests (GAP-074)
# =============================================================================


class TestIndexHandler:
    """Tests for IndexHandler (GAP-074)."""

    async def test_index_returns_stage_result(self, index_handler: IndexHandler):
        """Index returns StageResult, not state changes."""
        context = make_context(
            current_state=KnowledgePlaneLifecycleState.INGESTING,
        )
        result = await index_handler.execute(context)

        assert isinstance(result, StageResult)
        assert result.status == StageStatus.SUCCESS

    async def test_index_handles_ingesting_state(self, index_handler: IndexHandler):
        """Index handles INGESTING state."""
        assert KnowledgePlaneLifecycleState.INGESTING in index_handler.handles_states

    async def test_index_returns_vector_count(self, index_handler: IndexHandler):
        """Index returns vector count."""
        context = make_context(
            current_state=KnowledgePlaneLifecycleState.INGESTING,
        )
        result = await index_handler.execute(context)

        assert result.success
        assert "vectors_created" in result.data
        assert result.data["vectors_created"] > 0

    async def test_index_returns_index_size(self, index_handler: IndexHandler):
        """Index returns index size."""
        context = make_context(
            current_state=KnowledgePlaneLifecycleState.INGESTING,
        )
        result = await index_handler.execute(context)

        assert result.success
        assert "index_size_bytes" in result.data
        assert result.data["index_size_bytes"] > 0

    async def test_index_stage_name(self, index_handler: IndexHandler):
        """Index has correct stage name."""
        assert index_handler.stage_name == "index"


# =============================================================================
# ClassifyHandler Tests (GAP-075)
# =============================================================================


class TestClassifyHandler:
    """Tests for ClassifyHandler (GAP-075)."""

    async def test_classify_returns_stage_result(self, classify_handler: ClassifyHandler):
        """Classify returns StageResult, not state changes."""
        context = make_context(
            current_state=KnowledgePlaneLifecycleState.INDEXED,
        )
        result = await classify_handler.execute(context)

        assert isinstance(result, StageResult)
        assert result.status == StageStatus.SUCCESS

    async def test_classify_handles_indexed_state(self, classify_handler: ClassifyHandler):
        """Classify handles INDEXED state."""
        assert KnowledgePlaneLifecycleState.INDEXED in classify_handler.handles_states

    async def test_classify_returns_sensitivity_level(self, classify_handler: ClassifyHandler):
        """Classify returns sensitivity level."""
        context = make_context(
            current_state=KnowledgePlaneLifecycleState.INDEXED,
        )
        result = await classify_handler.execute(context)

        assert result.success
        assert "sensitivity_level" in result.data
        assert result.data["sensitivity_level"] in ["public", "internal", "confidential", "restricted"]

    async def test_classify_returns_pii_detection(self, classify_handler: ClassifyHandler):
        """Classify returns PII detection result."""
        context = make_context(
            current_state=KnowledgePlaneLifecycleState.INDEXED,
        )
        result = await classify_handler.execute(context)

        assert result.success
        assert "pii_detected" in result.data
        assert isinstance(result.data["pii_detected"], bool)

    async def test_classify_returns_content_categories(self, classify_handler: ClassifyHandler):
        """Classify returns content categories."""
        context = make_context(
            current_state=KnowledgePlaneLifecycleState.INDEXED,
        )
        result = await classify_handler.execute(context)

        assert result.success
        assert "content_categories" in result.data
        assert isinstance(result.data["content_categories"], list)

    async def test_classify_stage_name(self, classify_handler: ClassifyHandler):
        """Classify has correct stage name."""
        assert classify_handler.stage_name == "classify"


# =============================================================================
# ActivateHandler Tests (GAP-076)
# =============================================================================


class TestActivateHandler:
    """Tests for ActivateHandler (GAP-076)."""

    async def test_activate_returns_stage_result(self, activate_handler: ActivateHandler):
        """Activate returns StageResult, not state changes."""
        context = make_context(
            current_state=KnowledgePlaneLifecycleState.PENDING_ACTIVATE,
        )
        result = await activate_handler.execute(context)

        assert isinstance(result, StageResult)
        assert result.status == StageStatus.SUCCESS

    async def test_activate_handles_pending_activate_state(self, activate_handler: ActivateHandler):
        """Activate handles PENDING_ACTIVATE state."""
        assert KnowledgePlaneLifecycleState.PENDING_ACTIVATE in activate_handler.handles_states

    async def test_activate_returns_endpoint(self, activate_handler: ActivateHandler):
        """Activate returns query endpoint."""
        context = make_context(
            plane_id="kp_test123",
            current_state=KnowledgePlaneLifecycleState.PENDING_ACTIVATE,
        )
        result = await activate_handler.execute(context)

        assert result.success
        assert "endpoint" in result.data
        assert "kp_test123" in result.data["endpoint"]

    async def test_activate_returns_access_controls(self, activate_handler: ActivateHandler):
        """Activate returns access controls."""
        context = make_context(
            current_state=KnowledgePlaneLifecycleState.PENDING_ACTIVATE,
        )
        result = await activate_handler.execute(context)

        assert result.success
        assert "access_controls" in result.data
        assert "rate_limit" in result.data["access_controls"]

    async def test_activate_stage_name(self, activate_handler: ActivateHandler):
        """Activate has correct stage name."""
        assert activate_handler.stage_name == "activate"


# =============================================================================
# GovernHandler Tests (GAP-077)
# =============================================================================


class TestGovernHandler:
    """Tests for GovernHandler (GAP-077)."""

    async def test_govern_returns_stage_result(self, govern_handler: GovernHandler):
        """Govern returns StageResult, not state changes."""
        context = make_context(
            current_state=KnowledgePlaneLifecycleState.ACTIVE,
        )
        result = await govern_handler.execute(context)

        assert isinstance(result, StageResult)
        assert result.status == StageStatus.SUCCESS

    async def test_govern_handles_active_state(self, govern_handler: GovernHandler):
        """Govern handles ACTIVE state."""
        assert KnowledgePlaneLifecycleState.ACTIVE in govern_handler.handles_states

    async def test_govern_returns_evidence_hash(self, govern_handler: GovernHandler):
        """Govern returns evidence hash."""
        context = make_context(
            current_state=KnowledgePlaneLifecycleState.ACTIVE,
            actor_id="user-123",
        )
        result = await govern_handler.execute(context)

        assert result.success
        assert "evidence_hash" in result.data
        assert len(result.data["evidence_hash"]) == 16  # SHA256 truncated to 16 chars

    async def test_govern_evidence_varies_by_context(self, govern_handler: GovernHandler):
        """Govern generates different evidence for different contexts."""
        context1 = make_context(
            current_state=KnowledgePlaneLifecycleState.ACTIVE,
            actor_id="user-123",
        )
        context2 = make_context(
            current_state=KnowledgePlaneLifecycleState.ACTIVE,
            actor_id="user-456",  # Different actor
        )

        result1 = await govern_handler.execute(context1)
        result2 = await govern_handler.execute(context2)

        assert result1.success
        assert result2.success
        assert result1.data["evidence_hash"] != result2.data["evidence_hash"]

    async def test_govern_stage_name(self, govern_handler: GovernHandler):
        """Govern has correct stage name."""
        assert govern_handler.stage_name == "govern"


# =============================================================================
# StageRegistry Tests
# =============================================================================


class TestStageRegistry:
    """Tests for StageRegistry."""

    def test_registry_has_verify_handler(self, stage_registry: StageRegistry):
        """Registry has handler for DRAFT state (verify)."""
        handler = stage_registry.get_handler(KnowledgePlaneLifecycleState.DRAFT)
        assert handler is not None
        assert handler.stage_name == "verify"

    def test_registry_has_ingest_handler(self, stage_registry: StageRegistry):
        """Registry has handler for VERIFIED state (ingest)."""
        handler = stage_registry.get_handler(KnowledgePlaneLifecycleState.VERIFIED)
        assert handler is not None
        assert handler.stage_name == "ingest"

    def test_registry_has_index_handler(self, stage_registry: StageRegistry):
        """Registry has handler for INGESTING state (index)."""
        handler = stage_registry.get_handler(KnowledgePlaneLifecycleState.INGESTING)
        assert handler is not None
        assert handler.stage_name == "index"

    def test_registry_has_classify_handler(self, stage_registry: StageRegistry):
        """Registry has handler for INDEXED state (classify)."""
        handler = stage_registry.get_handler(KnowledgePlaneLifecycleState.INDEXED)
        assert handler is not None
        assert handler.stage_name == "classify"

    def test_registry_has_activate_handler(self, stage_registry: StageRegistry):
        """Registry has handler for PENDING_ACTIVATE state (activate)."""
        handler = stage_registry.get_handler(KnowledgePlaneLifecycleState.PENDING_ACTIVATE)
        assert handler is not None
        assert handler.stage_name == "activate"

    def test_registry_has_handler_for_active_state(self, stage_registry: StageRegistry):
        """Registry has handler for ACTIVE state."""
        handler = stage_registry.get_handler(KnowledgePlaneLifecycleState.ACTIVE)
        assert handler is not None
        # Note: Both GovernHandler and DeregisterHandler handle ACTIVE state.
        # The last registered handler (DeregisterHandler) wins.
        # This is expected behavior - in practice, the orchestrator
        # selects handlers based on the action being performed.
        assert handler.stage_name in ("govern", "deregister")

    def test_registry_no_handler_for_terminal_states(self, stage_registry: StageRegistry):
        """Registry has no handler for terminal states."""
        assert stage_registry.get_handler(KnowledgePlaneLifecycleState.PURGED) is None
        assert stage_registry.get_handler(KnowledgePlaneLifecycleState.FAILED) is None

    def test_registry_has_handler_check(self, stage_registry: StageRegistry):
        """Registry has_handler returns correct boolean."""
        assert stage_registry.has_handler(KnowledgePlaneLifecycleState.DRAFT)
        assert not stage_registry.has_handler(KnowledgePlaneLifecycleState.PURGED)


# =============================================================================
# StageResult Tests
# =============================================================================


class TestStageResult:
    """Tests for StageResult helper methods."""

    def test_ok_creates_success_result(self):
        """StageResult.ok creates success result."""
        result = StageResult.ok(message="Done", foo="bar")

        assert result.success
        assert result.status == StageStatus.SUCCESS
        assert result.message == "Done"
        assert result.data["foo"] == "bar"

    def test_fail_creates_failure_result(self):
        """StageResult.fail creates failure result."""
        result = StageResult.fail(
            message="Oops",
            error_code="ERR001",
            detail="More info",
        )

        assert not result.success
        assert result.status == StageStatus.FAILURE
        assert result.message == "Oops"
        assert result.error_code == "ERR001"
        assert result.error_details["detail"] == "More info"

    def test_pending_creates_async_result(self):
        """StageResult.pending creates async result."""
        result = StageResult.pending(job_id="job_123", message="In progress")

        assert result.is_async
        assert result.status == StageStatus.PENDING
        assert result.job_id == "job_123"
        assert result.message == "In progress"

    def test_skipped_creates_skipped_result(self):
        """StageResult.skipped creates skipped result."""
        result = StageResult.skipped(reason="Already done")

        assert not result.success
        assert result.status == StageStatus.SKIPPED
        assert result.message == "Already done"


# =============================================================================
# Integration Tests
# =============================================================================


class TestStageHandlerContract:
    """Tests verifying stage handlers follow the 'dumb plugin' contract."""

    async def test_handlers_dont_return_state_changes(self, stage_registry: StageRegistry):
        """Handlers return StageResult, not state changes."""
        for state in [
            KnowledgePlaneLifecycleState.DRAFT,
            KnowledgePlaneLifecycleState.VERIFIED,
            KnowledgePlaneLifecycleState.INGESTING,
            KnowledgePlaneLifecycleState.INDEXED,
            KnowledgePlaneLifecycleState.PENDING_ACTIVATE,
            KnowledgePlaneLifecycleState.ACTIVE,
        ]:
            handler = stage_registry.get_handler(state)
            if handler:
                context = make_context(current_state=state, config={"source_type": "test"})
                result = await handler.execute(context)

                assert isinstance(result, StageResult)
                assert not hasattr(result, "new_state")
                assert not hasattr(result, "state_change")

    async def test_handlers_have_stage_name(self, stage_registry: StageRegistry):
        """All handlers have a stage name."""
        for state in KnowledgePlaneLifecycleState:
            handler = stage_registry.get_handler(state)
            if handler:
                assert handler.stage_name is not None
                assert len(handler.stage_name) > 0

    async def test_handlers_have_handles_states(self, stage_registry: StageRegistry):
        """All handlers declare their states."""
        for state in KnowledgePlaneLifecycleState:
            handler = stage_registry.get_handler(state)
            if handler:
                assert handler.handles_states is not None
                assert isinstance(handler.handles_states, tuple)
