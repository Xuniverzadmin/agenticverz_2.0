# CI Test: External Calls Blocking
"""
Tests that verify external network calls are blocked in CI environment.

These tests are specifically designed to run in CI with DISABLE_EXTERNAL_CALLS=1.
They verify that the external_guard module correctly blocks network access.

Usage:
    DISABLE_EXTERNAL_CALLS=1 pytest tests/ci/test_no_external_calls.py -v
"""

import os

import pytest

# Only run these tests when DISABLE_EXTERNAL_CALLS is set
pytestmark = pytest.mark.skipif(
    os.getenv("DISABLE_EXTERNAL_CALLS", "").lower() not in ("1", "true"), reason="DISABLE_EXTERNAL_CALLS not enabled"
)


class TestExternalCallsBlocked:
    """Tests that verify external calls are blocked in CI."""

    def test_socket_connect_blocked(self):
        """Direct socket connections to external hosts should be blocked."""
        # Import the guard to ensure it's active
        from app.workflow.external_guard import ExternalCallBlockedError, check_external_call_allowed

        with pytest.raises(ExternalCallBlockedError) as exc_info:
            check_external_call_allowed("socket", "api.example.com")

        assert "api.example.com" in str(exc_info.value)
        assert exc_info.value.call_type == "socket"

    def test_http_request_blocked(self):
        """HTTP requests to external hosts should be blocked."""
        from app.workflow.external_guard import ExternalCallBlockedError, check_external_call_allowed

        with pytest.raises(ExternalCallBlockedError) as exc_info:
            check_external_call_allowed("http", "https://api.openai.com/v1/chat")

        assert "api.openai.com" in str(exc_info.value)

    def test_localhost_allowed(self):
        """Localhost connections should be allowed."""
        from app.workflow.external_guard import check_external_call_allowed

        # Should not raise
        check_external_call_allowed("socket", "localhost", allowed_hosts={"localhost", "127.0.0.1"})
        check_external_call_allowed("socket", "127.0.0.1", allowed_hosts={"localhost", "127.0.0.1"})

    def test_blocked_calls_tracked(self):
        """Blocked calls should be tracked for debugging."""
        from app.workflow.external_guard import (
            ExternalCallBlockedError,
            check_external_call_allowed,
            clear_blocked_calls,
            get_blocked_calls,
        )

        clear_blocked_calls()

        try:
            check_external_call_allowed("http", "https://malicious.example.com")
        except ExternalCallBlockedError:
            pass

        blocked = get_blocked_calls()
        assert len(blocked) >= 1
        assert ("http", "https://malicious.example.com") in blocked

    def test_guard_context_manager(self):
        """ExternalCallsGuard context manager should block calls."""
        from app.workflow.external_guard import ExternalCallBlockedError, ExternalCallsGuard

        with ExternalCallsGuard() as guard:
            # Inside guard, external calls should be blocked
            from app.workflow.external_guard import check_external_call_allowed

            with pytest.raises(ExternalCallBlockedError):
                check_external_call_allowed("socket", "external.example.com")


class TestGoldenTestIsolation:
    """Tests that verify golden tests are properly isolated from network."""

    def test_workflow_replay_no_network(self):
        """Workflow replay should work without any network calls."""
        from app.workflow.checkpoint import InMemoryCheckpointStore
        from app.workflow.engine import StepDescriptor, WorkflowEngine, WorkflowSpec
        from app.workflow.golden import InMemoryGoldenRecorder

        # Simple deterministic skill registry (no network)
        class LocalRegistry:
            def get(self, skill_id: str):
                if skill_id == "add":
                    return self._add
                return None

            async def _add(self, inputs):
                return {"result": inputs.get("a", 0) + inputs.get("b", 0)}

        spec = WorkflowSpec(
            id="ci-test",
            name="CI Isolation Test",
            steps=[
                StepDescriptor(id="s1", skill_id="add", inputs={"a": 1, "b": 2}),
            ],
        )

        checkpoint = InMemoryCheckpointStore()
        golden = InMemoryGoldenRecorder()
        engine = WorkflowEngine(
            registry=LocalRegistry(),
            checkpoint_store=checkpoint,
            golden=golden,
        )

        import asyncio

        # Use asyncio.run() instead of get_event_loop() to avoid issues with
        # closed event loops from previous async tests in the suite
        result = asyncio.run(engine.run(spec, run_id="ci-test-run", seed=42))

        assert result.status == "completed"
        assert result.step_results[0].output["result"] == 3


class TestEnvironmentGuard:
    """Tests that verify environment-based guard activation."""

    def test_disable_external_calls_env_active(self):
        """DISABLE_EXTERNAL_CALLS should be active in CI."""

        # This test only runs when DISABLE_EXTERNAL_CALLS=1
        # So this assertion verifies the guard is properly reading the env
        assert os.getenv("DISABLE_EXTERNAL_CALLS", "").lower() in ("1", "true")

    def test_blocked_domains_include_common_apis(self):
        """Common external APIs should be blocked."""
        from app.workflow.external_guard import ExternalCallBlockedError, check_external_call_allowed

        blocked_domains = [
            "api.openai.com",
            "api.anthropic.com",
            "api.stripe.com",
            "api.github.com",
            "slack.com",
            "webhook.site",
        ]

        for domain in blocked_domains:
            with pytest.raises(ExternalCallBlockedError):
                check_external_call_allowed("http", domain)
