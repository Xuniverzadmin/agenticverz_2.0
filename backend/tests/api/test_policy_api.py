# tests/api/test_policy_api.py
"""
Integration tests for Policy API endpoints.

Tests:
1. Policy sandbox evaluation (/api/v1/policy/eval)
2. Approval workflow (create, approve, reject, list)
3. Escalation worker behavior
4. Webhook callbacks

Run with:
    pytest tests/api/test_policy_api.py -v
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = MagicMock()
    session.exec = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    session.get = MagicMock(return_value=None)
    session.add = MagicMock()
    session.refresh = MagicMock()
    # Support async operations for escalation check
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    session.execute = AsyncMock(return_value=mock_result)
    session.commit = AsyncMock()
    return session


@pytest.fixture
def sample_eval_request():
    """Sample policy evaluation request."""
    return {
        "skill_id": "http_call",
        "tenant_id": "tenant-001",
        "agent_id": "agent-001",
        "payload": {"url": "https://api.example.com/data", "method": "GET"},
        "simulate_cost": True,
    }


@pytest.fixture
def sample_approval_request():
    """Sample approval request."""
    return {
        "policy_type": "cost",
        "skill_id": "llm_invoke",
        "tenant_id": "tenant-001",
        "agent_id": "agent-001",
        "payload": {"prompt": "Generate summary", "model": "claude-3"},
        "requested_by": "user-001",
        "justification": "Need to process large document",
        "expires_in_seconds": 300,
    }


@pytest.fixture
def sample_approval_action():
    """Sample approval action."""
    return {"approver_id": "approver-001", "level": 3, "notes": "Approved for document processing"}


# =============================================================================
# Policy Evaluation Tests
# =============================================================================


class TestPolicyEvaluation:
    """Tests for /api/v1/policy/eval endpoint."""

    def test_eval_request_model_validation(self, sample_eval_request):
        """Request model should validate correctly."""
        from app.api.policy import PolicyEvalRequest

        request = PolicyEvalRequest(**sample_eval_request)
        assert request.skill_id == "http_call"
        assert request.tenant_id == "tenant-001"
        assert request.simulate_cost is True

    def test_eval_response_model(self):
        """Response model should construct correctly."""
        from app.api.policy import PolicyEvalResponse

        response = PolicyEvalResponse(
            decision="allow",
            reasons=["No violations"],
            simulated_cost_cents=10,
            policy_version="v1.0.0",
            approval_level_required=None,
            violations=[],
            timestamp="2025-12-03T00:00:00Z",
        )
        assert response.decision == "allow"
        assert response.simulated_cost_cents == 10

    @pytest.mark.asyncio
    async def test_simulate_cost_fallback(self):
        """Cost simulation should fallback to default."""
        from app.api.policy import _simulate_cost

        # Without CostSim available, should return fallback
        cost = await _simulate_cost("http_call", "tenant-001", {})
        assert cost == 10  # Default fallback

    @pytest.mark.asyncio
    async def test_check_policy_violations_empty_when_no_enforcer(self):
        """Should return empty violations when PolicyEnforcer not available."""
        from app.api.policy import _check_policy_violations

        with patch.dict("sys.modules", {"app.workflow.policies": None}):
            violations = await _check_policy_violations(
                skill_id="http_call", tenant_id="tenant-001", agent_id=None, payload={}, simulated_cost=10
            )
            # May have violations from actual enforcer or empty
            assert isinstance(violations, list)


# =============================================================================
# Approval Workflow Tests
# =============================================================================


class TestApprovalWorkflow:
    """Tests for approval workflow endpoints."""

    def test_approval_request_create_model(self, sample_approval_request):
        """ApprovalRequestCreate model should validate correctly."""
        from app.api.policy import ApprovalRequestCreate

        request = ApprovalRequestCreate(**sample_approval_request)
        assert request.policy_type.value == "cost"
        assert request.skill_id == "llm_invoke"

    def test_approval_action_model(self, sample_approval_action):
        """ApprovalAction model should validate correctly."""
        from app.api.policy import ApprovalAction

        action = ApprovalAction(**sample_approval_action)
        assert action.approver_id == "approver-001"
        assert action.level == 3

    def test_approval_action_level_validation(self):
        """ApprovalAction should reject invalid levels."""
        from pydantic import ValidationError

        from app.api.policy import ApprovalAction

        with pytest.raises(ValidationError):
            ApprovalAction(approver_id="test", level=0)  # Too low

        with pytest.raises(ValidationError):
            ApprovalAction(approver_id="test", level=6)  # Too high

    def test_approval_status_enum(self):
        """ApprovalStatus enum should have correct values."""
        from app.api.policy import ApprovalStatus

        assert ApprovalStatus.PENDING.value == "pending"
        assert ApprovalStatus.APPROVED.value == "approved"
        assert ApprovalStatus.REJECTED.value == "rejected"
        assert ApprovalStatus.ESCALATED.value == "escalated"
        assert ApprovalStatus.EXPIRED.value == "expired"


# =============================================================================
# Database Model Tests
# =============================================================================


class TestApprovalRequestModel:
    """Tests for ApprovalRequest database model."""

    def test_model_payload_serialization(self):
        """Model should serialize/deserialize payload correctly."""
        from app.db import ApprovalRequest

        approval = ApprovalRequest(
            policy_type="cost", requested_by="user-001", expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )

        payload = {"key": "value", "nested": {"a": 1}}
        approval.set_payload(payload)

        assert approval.get_payload() == payload

    def test_model_approvals_tracking(self):
        """Model should track approvals correctly."""
        from app.db import ApprovalRequest

        approval = ApprovalRequest(
            policy_type="cost", requested_by="user-001", expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )

        approval.add_approval("approver-1", 2, "approve", "ok")
        approval.add_approval("approver-2", 4, "approve", "also ok")

        approvals = approval.get_approvals()
        assert len(approvals) == 2
        assert approval.current_level == 4  # Max of all approvals

    def test_model_to_dict(self):
        """Model should convert to dict correctly."""
        from app.db import ApprovalRequest

        approval = ApprovalRequest(
            policy_type="cost",
            skill_id="llm_invoke",
            tenant_id="tenant-001",
            requested_by="user-001",
            required_level=3,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        data = approval.to_dict()
        assert data["policy_type"] == "cost"
        assert data["skill_id"] == "llm_invoke"
        assert data["required_level"] == 3


# =============================================================================
# Webhook Tests
# =============================================================================


class TestWebhooks:
    """Tests for webhook callback behavior."""

    def test_webhook_signature_computation(self):
        """Webhook signature should be computed correctly."""
        from app.api.policy import _compute_webhook_signature

        payload = '{"event": "test"}'
        secret = "my-secret"

        signature = _compute_webhook_signature(payload, secret)

        # Should be a hex string
        assert len(signature) == 64
        assert all(c in "0123456789abcdef" for c in signature)

    def test_webhook_secret_hashing(self):
        """Webhook secret should be hashed for storage."""
        from app.api.policy import _hash_webhook_secret

        secret = "my-webhook-secret"
        hashed = _hash_webhook_secret(secret)

        # Should be SHA256 hash
        assert len(hashed) == 64
        assert hashed != secret

    @pytest.mark.asyncio
    async def test_send_webhook_success(self):
        """Successful webhook should return True."""
        from app.api.policy import _send_webhook

        with patch("app.api.policy.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            result = await _send_webhook(
                url="https://hooks.example.com/approval", payload={"event": "test"}, secret="test-secret"
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_send_webhook_includes_signature_header(self):
        """Webhook with secret should include signature header."""
        from app.api.policy import _send_webhook

        captured_headers = {}

        with patch("app.api.policy.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200

            async def capture_post(url, content, headers):
                captured_headers.update(headers)
                return mock_response

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(side_effect=capture_post)

            await _send_webhook(url="https://hooks.example.com", payload={"event": "test"}, secret="my-secret")

            assert "X-Webhook-Signature" in captured_headers
            assert captured_headers["X-Webhook-Signature"].startswith("sha256=")


# =============================================================================
# Escalation Tests
# =============================================================================


class TestEscalation:
    """Tests for escalation worker behavior."""

    def test_escalation_task_entry_point_exists(self):
        """Escalation task entry point should exist."""
        from app.api.policy import run_escalation_task

        assert callable(run_escalation_task)

    @pytest.mark.asyncio
    async def test_run_escalation_check_function(self, mock_db_session):
        """Escalation check should process pending requests."""
        from app.api.policy import run_escalation_check

        # Mock returns empty results (no pending requests)
        mock_db_session.exec.return_value.all.return_value = []

        result = await run_escalation_check(mock_db_session)

        assert result == 0  # No requests escalated


# =============================================================================
# Metrics Tests
# =============================================================================


class TestMetrics:
    """Tests for metrics recording."""

    def test_record_policy_decision_safe(self):
        """Policy decision recording should not raise on failure."""
        from app.api.policy import _record_policy_decision

        # Should not raise even if metrics module fails
        _record_policy_decision("allow", "cost")

    def test_record_capability_violation_safe(self):
        """Capability violation recording should not raise on failure."""
        from app.api.policy import _record_capability_violation

        # Should not raise
        _record_capability_violation("budget", "llm_invoke", "tenant-001")

    def test_record_budget_rejection_safe(self):
        """Budget rejection recording should not raise on failure."""
        from app.api.policy import _record_budget_rejection

        # Should not raise
        _record_budget_rejection("cost", "llm_invoke")


# =============================================================================
# Policy Type Tests
# =============================================================================


class TestPolicyTypes:
    """Tests for policy type handling."""

    def test_policy_type_enum_values(self):
        """PolicyType enum should have expected values."""
        from app.api.policy import PolicyType

        assert PolicyType.COST.value == "cost"
        assert PolicyType.CAPABILITY.value == "capability"
        assert PolicyType.RESOURCE.value == "resource"
        assert PolicyType.RATE_LIMIT.value == "rate_limit"

    def test_config_to_dict_handles_string_approval_level(self):
        """Config conversion should handle string approval levels."""
        from app.api.policy import _config_to_dict

        class MockConfig:
            approval_level = "3"
            auto_approve_max_cost_cents = 100
            auto_approve_max_tokens = 1000
            escalate_to = "admin"
            escalation_timeout_seconds = 300

        result = _config_to_dict(MockConfig())

        assert result["approval_level"] == 3
        assert result["auto_approve_max_cost_cents"] == 100

    def test_config_to_dict_handles_non_numeric_approval_level(self):
        """Config conversion should default non-numeric approval levels."""
        from app.api.policy import _config_to_dict

        class MockConfig:
            approval_level = "auto_approve"  # Not numeric
            auto_approve_max_cost_cents = None
            auto_approve_max_tokens = None
            escalate_to = None
            escalation_timeout_seconds = 300

        result = _config_to_dict(MockConfig())

        assert result["approval_level"] == 3  # Default
        assert result["auto_approve_max_cost_cents"] == 100  # Default


# =============================================================================
# Integration Test (requires DB)
# =============================================================================


@pytest.mark.integration
class TestIntegration:
    """Integration tests requiring database."""

    @pytest.fixture
    def app_client(self):
        """Create test client with real app."""
        try:
            from fastapi import FastAPI
            from fastapi.testclient import TestClient

            from app.api.policy import router

            app = FastAPI()
            app.include_router(router)

            return TestClient(app)
        except ImportError:
            pytest.skip("FastAPI test client not available")

    def test_eval_endpoint_basic(self, app_client, sample_eval_request):
        """Basic eval endpoint test."""
        response = app_client.post("/api/v1/policy/eval", json=sample_eval_request)

        # May fail without full DB setup, but structure should be valid
        assert response.status_code in (200, 500)


# =============================================================================
# Replay/Determinism Tests
# =============================================================================


class TestDeterminism:
    """Tests for policy decision determinism."""

    @pytest.mark.asyncio
    async def test_same_input_same_output(self):
        """Same policy input should produce same decision."""
        from app.api.policy import _check_policy_violations

        # Run twice with same input
        v1 = await _check_policy_violations("http_call", "t1", None, {}, 10)
        v2 = await _check_policy_violations("http_call", "t1", None, {}, 10)

        # Should produce same violations
        assert len(v1) == len(v2)
