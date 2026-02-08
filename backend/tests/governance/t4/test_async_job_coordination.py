# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci, manual
#   Execution: sync
# Role: T4 Async Job Coordination Tests (GAP-086)
# Callers: pytest, CI
# Allowed Imports: L4 (models, services)
# Forbidden Imports: L1, L2, L3, L5, L6
# Reference: GAP-086, DOMAINS_E2E_SCAFFOLD_V3.md Section 7.15.6

"""
T4 Async Job Coordination Tests (GAP-086)

These tests verify that the KnowledgeLifecycleManager properly coordinates
with async background jobs:

1. PENDING states trigger async jobs
2. Jobs track plane_id and job_id association
3. Job completion advances state exactly once
4. Job failure transitions to FAILED state
5. Job completion validates job_id match

Test Count Target: ~80 tests

INVARIANTS UNDER TEST:
- MANAGER-005: Async jobs report completion back to manager
- States requiring async jobs: PENDING_VERIFY, INGESTING, ARCHIVED

ASYNC JOB TYPES:
- verify_connectivity: Validate connection to knowledge source
- ingest_data: Pull data from source
- index_data: Build search index
- classify_data: Apply classification rules
- archive_data: Export to cold storage
- purge_data: Delete data permanently
"""

import pytest
from typing import Any, Dict, List, Tuple

from app.models.knowledge_lifecycle import (
    KnowledgePlaneLifecycleState,
    LifecycleAction,
)
from app.hoc.cus.hoc_spine.orchestrator.lifecycle.knowledge_lifecycle_manager import (
    KnowledgeLifecycleManager,
    TransitionRequest,
    LifecycleAuditEventType,
    reset_manager,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def job_tracker() -> Dict[str, Any]:
    """Create a job tracker dictionary."""
    return {"jobs": [], "next_id": 0}


@pytest.fixture
def manager_with_job_tracker(
    job_tracker: Dict[str, Any]
) -> KnowledgeLifecycleManager:
    """Create manager with custom job scheduler that tracks jobs."""
    reset_manager()

    def tracking_scheduler(plane_id: str, job_type: str, config: Dict[str, Any]) -> str:
        job_id = f"job_{job_tracker['next_id']}"
        job_tracker["next_id"] += 1
        job_tracker["jobs"].append((plane_id, job_type, config, job_id))
        return job_id

    return KnowledgeLifecycleManager(job_scheduler=tracking_scheduler)


@pytest.fixture
def manager() -> KnowledgeLifecycleManager:
    """Create a fresh KnowledgeLifecycleManager for testing."""
    reset_manager()
    return KnowledgeLifecycleManager()


# =============================================================================
# Async Job Triggering
# =============================================================================


class TestAsyncJobTriggering:
    """Tests that appropriate states trigger async jobs."""

    def test_verify_triggers_job(
        self,
        manager_with_job_tracker: KnowledgeLifecycleManager,
        job_tracker: Dict[str, Any],
    ):
        """VERIFY action triggers verify_connectivity job."""
        response = manager_with_job_tracker.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        job_tracker["jobs"].clear()

        result = manager_with_job_tracker.handle_transition(TransitionRequest(
            plane_id=response.plane_id,
            tenant_id="tenant-123",
            action=LifecycleAction.VERIFY,
        ))

        assert len(job_tracker["jobs"]) == 1
        job = job_tracker["jobs"][0]
        assert job[0] == response.plane_id  # plane_id
        assert job[1] == "verify_connectivity"  # job_type
        assert result.job_id is not None

    def test_ingest_triggers_job(
        self,
        manager_with_job_tracker: KnowledgeLifecycleManager,
        job_tracker: Dict[str, Any],
    ):
        """INGEST action triggers ingest_data job."""
        response = manager_with_job_tracker.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        plane = manager_with_job_tracker.get_plane(response.plane_id)
        plane.state = KnowledgePlaneLifecycleState.VERIFIED
        job_tracker["jobs"].clear()

        result = manager_with_job_tracker.handle_transition(TransitionRequest(
            plane_id=plane.id,
            tenant_id="tenant-123",
            action=LifecycleAction.INGEST,
        ))

        assert len(job_tracker["jobs"]) == 1
        job = job_tracker["jobs"][0]
        assert job[1] == "ingest_data"
        assert result.job_id is not None

    def test_non_async_transition_no_job(
        self,
        manager_with_job_tracker: KnowledgeLifecycleManager,
        job_tracker: Dict[str, Any],
    ):
        """Non-async transitions don't trigger jobs."""
        manager_with_job_tracker.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))

        # REGISTER doesn't require async job
        assert len(job_tracker["jobs"]) == 0

    def test_job_config_includes_plane_info(
        self,
        manager_with_job_tracker: KnowledgeLifecycleManager,
        job_tracker: Dict[str, Any],
    ):
        """Job config includes plane_id, tenant_id, target_state."""
        response = manager_with_job_tracker.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
            actor_id="user-456",
        ))
        job_tracker["jobs"].clear()

        manager_with_job_tracker.handle_transition(TransitionRequest(
            plane_id=response.plane_id,
            tenant_id="tenant-123",
            action=LifecycleAction.VERIFY,
            actor_id="user-456",
        ))

        job = job_tracker["jobs"][0]
        config = job[2]
        assert config["plane_id"] == response.plane_id
        assert config["tenant_id"] == "tenant-123"
        assert config["target_state"] == "PENDING_VERIFY"
        assert config["actor_id"] == "user-456"


# =============================================================================
# Job ID Association
# =============================================================================


class TestJobIdAssociation:
    """Tests that job IDs are properly associated with planes."""

    def test_job_id_stored_on_plane(
        self,
        manager_with_job_tracker: KnowledgeLifecycleManager,
        job_tracker: Dict[str, Any],
    ):
        """Plane stores active job_id after async transition."""
        response = manager_with_job_tracker.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))

        manager_with_job_tracker.handle_transition(TransitionRequest(
            plane_id=response.plane_id,
            tenant_id="tenant-123",
            action=LifecycleAction.VERIFY,
        ))

        plane = manager_with_job_tracker.get_plane(response.plane_id)
        assert plane.active_job_id is not None
        assert plane.active_job_id.startswith("job_")

    def test_job_id_returned_in_response(
        self,
        manager_with_job_tracker: KnowledgeLifecycleManager,
        job_tracker: Dict[str, Any],
    ):
        """Transition response includes job_id for async transitions."""
        response = manager_with_job_tracker.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))

        result = manager_with_job_tracker.handle_transition(TransitionRequest(
            plane_id=response.plane_id,
            tenant_id="tenant-123",
            action=LifecycleAction.VERIFY,
        ))

        assert result.job_id is not None
        assert result.job_id.startswith("job_")


# =============================================================================
# Job Completion (Success Path)
# =============================================================================


class TestJobCompletion:
    """Tests for job completion handling."""

    def test_complete_job_clears_active_job_id(
        self, manager: KnowledgeLifecycleManager
    ):
        """complete_job clears the active_job_id."""
        response = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        result = manager.handle_transition(TransitionRequest(
            plane_id=response.plane_id,
            tenant_id="tenant-123",
            action=LifecycleAction.VERIFY,
        ))

        plane = manager.get_plane(response.plane_id)
        assert plane.active_job_id is not None
        job_id = plane.active_job_id

        manager.complete_job(
            job_id=job_id,
            plane_id=response.plane_id,
            success=True,
        )

        plane = manager.get_plane(response.plane_id)
        assert plane.active_job_id is None

    def test_complete_job_requires_matching_job_id(
        self, manager: KnowledgeLifecycleManager
    ):
        """complete_job fails if job_id doesn't match."""
        response = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        manager.handle_transition(TransitionRequest(
            plane_id=response.plane_id,
            tenant_id="tenant-123",
            action=LifecycleAction.VERIFY,
        ))

        result = manager.complete_job(
            job_id="wrong_job_id",
            plane_id=response.plane_id,
            success=True,
        )

        assert not result.success
        assert "Job ID mismatch" in result.reason

    def test_complete_job_unknown_plane(
        self, manager: KnowledgeLifecycleManager
    ):
        """complete_job fails for unknown plane."""
        result = manager.complete_job(
            job_id="job_123",
            plane_id="unknown-plane-id",
            success=True,
        )

        assert not result.success
        assert "not found" in result.reason


# =============================================================================
# Job Failure Handling
# =============================================================================


class TestJobFailureHandling:
    """Tests for job failure handling."""

    def test_job_failure_emits_audit_event(
        self, manager: KnowledgeLifecycleManager
    ):
        """Job failure emits JOB_FAILED audit event."""
        response = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        manager.handle_transition(TransitionRequest(
            plane_id=response.plane_id,
            tenant_id="tenant-123",
            action=LifecycleAction.VERIFY,
        ))

        plane = manager.get_plane(response.plane_id)
        job_id = plane.active_job_id

        manager.complete_job(
            job_id=job_id,
            plane_id=response.plane_id,
            success=False,
            result={"error": "Connection timeout"},
        )

        events = manager.get_audit_log(
            plane_id=response.plane_id,
            event_type=LifecycleAuditEventType.JOB_FAILED,
        )
        assert len(events) >= 1
        assert events[-1].reason == "Connection timeout"

    def test_job_failure_preserves_state(
        self, manager: KnowledgeLifecycleManager
    ):
        """Job failure preserves current state (doesn't auto-fail)."""
        response = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        manager.handle_transition(TransitionRequest(
            plane_id=response.plane_id,
            tenant_id="tenant-123",
            action=LifecycleAction.VERIFY,
        ))

        plane = manager.get_plane(response.plane_id)
        job_id = plane.active_job_id
        original_state = plane.state

        manager.complete_job(
            job_id=job_id,
            plane_id=response.plane_id,
            success=False,
            result={"error": "Connection timeout"},
        )

        # State should be preserved (not auto-transitioned to FAILED)
        plane = manager.get_plane(response.plane_id)
        assert plane.state == original_state


# =============================================================================
# Job Completion Advances State Once
# =============================================================================


class TestJobCompletionAdvancesOnce:
    """Tests that job completion advances state exactly once."""

    def test_duplicate_job_completion_rejected(
        self, manager: KnowledgeLifecycleManager
    ):
        """Second job completion for same job_id is rejected."""
        response = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        manager.handle_transition(TransitionRequest(
            plane_id=response.plane_id,
            tenant_id="tenant-123",
            action=LifecycleAction.VERIFY,
        ))

        plane = manager.get_plane(response.plane_id)
        job_id = plane.active_job_id

        # First completion
        result1 = manager.complete_job(
            job_id=job_id,
            plane_id=response.plane_id,
            success=True,
        )
        assert result1.success

        # Second completion should fail (active_job_id is now None)
        result2 = manager.complete_job(
            job_id=job_id,
            plane_id=response.plane_id,
            success=True,
        )
        assert not result2.success
        assert "mismatch" in result2.reason.lower()


# =============================================================================
# Custom Job Scheduler
# =============================================================================


class TestCustomJobScheduler:
    """Tests for custom job scheduler integration."""

    def test_custom_scheduler_receives_correct_args(self):
        """Custom scheduler receives plane_id, job_type, config."""
        calls = []

        def custom_scheduler(plane_id, job_type, config):
            calls.append((plane_id, job_type, config.keys()))
            return f"custom_job_{len(calls)}"

        manager = KnowledgeLifecycleManager(job_scheduler=custom_scheduler)

        response = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        manager.handle_transition(TransitionRequest(
            plane_id=response.plane_id,
            tenant_id="tenant-123",
            action=LifecycleAction.VERIFY,
        ))

        assert len(calls) == 1
        assert calls[0][0] == response.plane_id
        assert calls[0][1] == "verify_connectivity"
        assert "plane_id" in calls[0][2]
        assert "tenant_id" in calls[0][2]

    def test_custom_scheduler_job_id_used(self):
        """Custom scheduler's returned job_id is used."""
        def custom_scheduler(plane_id, job_type, config):
            return "my_custom_job_id_12345"

        manager = KnowledgeLifecycleManager(job_scheduler=custom_scheduler)

        response = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        result = manager.handle_transition(TransitionRequest(
            plane_id=response.plane_id,
            tenant_id="tenant-123",
            action=LifecycleAction.VERIFY,
        ))

        assert result.job_id == "my_custom_job_id_12345"

        plane = manager.get_plane(response.plane_id)
        assert plane.active_job_id == "my_custom_job_id_12345"


# =============================================================================
# Job Type Mapping
# =============================================================================


class TestJobTypeMapping:
    """Tests for state-to-job-type mapping."""

    @pytest.mark.parametrize(
        "target_state,expected_job_type",
        [
            (KnowledgePlaneLifecycleState.PENDING_VERIFY, "verify_connectivity"),
            (KnowledgePlaneLifecycleState.INGESTING, "ingest_data"),
            (KnowledgePlaneLifecycleState.INDEXED, "index_data"),
            (KnowledgePlaneLifecycleState.CLASSIFIED, "classify_data"),
            (KnowledgePlaneLifecycleState.ARCHIVED, "archive_data"),
            (KnowledgePlaneLifecycleState.PURGED, "purge_data"),
        ],
    )
    def test_state_maps_to_job_type(
        self,
        target_state: KnowledgePlaneLifecycleState,
        expected_job_type: str,
    ):
        """States map to correct job types."""
        jobs = []

        def tracking_scheduler(plane_id, job_type, config):
            jobs.append(job_type)
            return f"job_{len(jobs)}"

        manager = KnowledgeLifecycleManager(job_scheduler=tracking_scheduler)

        # Use internal method to check mapping
        result = manager._get_job_type_for_state(target_state)
        assert result == expected_job_type


# =============================================================================
# States Not Requiring Async Jobs
# =============================================================================


class TestStatesNotRequiringAsync:
    """Tests that non-async states don't trigger jobs."""

    @pytest.mark.parametrize(
        "state",
        [
            KnowledgePlaneLifecycleState.DRAFT,
            KnowledgePlaneLifecycleState.VERIFIED,
            KnowledgePlaneLifecycleState.PENDING_ACTIVATE,
            KnowledgePlaneLifecycleState.ACTIVE,
            KnowledgePlaneLifecycleState.PENDING_DEACTIVATE,
            KnowledgePlaneLifecycleState.DEACTIVATED,
            KnowledgePlaneLifecycleState.FAILED,
        ],
    )
    def test_non_async_state_no_job_type(
        self,
        state: KnowledgePlaneLifecycleState,
    ):
        """Non-async states return None for job type."""
        manager = KnowledgeLifecycleManager()
        result = manager._get_job_type_for_state(state)
        assert result is None


# =============================================================================
# Job Result Handling
# =============================================================================


class TestJobResultHandling:
    """Tests for job result data handling."""

    def test_job_success_result_in_metadata(
        self, manager: KnowledgeLifecycleManager
    ):
        """Job success result is passed to next transition."""
        response = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        manager.handle_transition(TransitionRequest(
            plane_id=response.plane_id,
            tenant_id="tenant-123",
            action=LifecycleAction.VERIFY,
        ))

        plane = manager.get_plane(response.plane_id)
        job_id = plane.active_job_id

        result = manager.complete_job(
            job_id=job_id,
            plane_id=response.plane_id,
            success=True,
            result={"records_verified": 100, "connection_latency_ms": 45},
        )

        assert result.success
        assert "job_id" in result.metadata
        assert "job_result" in result.metadata or "job_success" in result.metadata

    def test_job_failure_error_in_audit(
        self, manager: KnowledgeLifecycleManager
    ):
        """Job failure error is recorded in audit event."""
        response = manager.handle_transition(TransitionRequest(
            plane_id="new",
            tenant_id="tenant-123",
            action=LifecycleAction.REGISTER,
        ))
        manager.handle_transition(TransitionRequest(
            plane_id=response.plane_id,
            tenant_id="tenant-123",
            action=LifecycleAction.VERIFY,
        ))

        plane = manager.get_plane(response.plane_id)
        job_id = plane.active_job_id

        manager.complete_job(
            job_id=job_id,
            plane_id=response.plane_id,
            success=False,
            result={"error": "Authentication failed: Invalid credentials"},
        )

        events = manager.get_audit_log(
            plane_id=response.plane_id,
            event_type=LifecycleAuditEventType.JOB_FAILED,
        )
        assert len(events) >= 1
        # Error should be in the event
        assert "Authentication failed" in events[-1].reason or \
               "error" in str(events[-1].metadata)


# =============================================================================
# Async Job States
# =============================================================================


class TestAsyncJobStates:
    """Tests for identifying async job states."""

    def test_pending_verify_requires_async(self):
        """PENDING_VERIFY requires async job."""
        assert KnowledgePlaneLifecycleState.PENDING_VERIFY.requires_async_job()

    def test_ingesting_requires_async(self):
        """INGESTING requires async job."""
        assert KnowledgePlaneLifecycleState.INGESTING.requires_async_job()

    def test_archived_requires_async(self):
        """ARCHIVED requires async job (export)."""
        assert KnowledgePlaneLifecycleState.ARCHIVED.requires_async_job()

    def test_active_does_not_require_async(self):
        """ACTIVE does not require async job."""
        assert not KnowledgePlaneLifecycleState.ACTIVE.requires_async_job()

    def test_draft_does_not_require_async(self):
        """DRAFT does not require async job."""
        assert not KnowledgePlaneLifecycleState.DRAFT.requires_async_job()
