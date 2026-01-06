# M11 E2E Workflow Test
# Tests a 5-step workflow using all M11 skills

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestM11FiveStepWorkflow:
    """
    E2E test for a 5-step workflow using M11 skills.

    Workflow:
    1. kv_store SET - Store workflow state
    2. voyage_embed - Generate embedding for a message
    3. slack_send - Send notification
    4. kv_store GET - Retrieve state
    5. email_send - Send completion email

    All skills run in stubbed mode for unit testing.
    """

    @pytest.fixture
    def workflow_run_id(self):
        """Generate unique workflow run ID."""
        return f"wf_m11_test_{int(datetime.now().timestamp())}"

    @pytest.fixture
    def kv_store_skill(self):
        """Create KV store skill in stubbed mode."""
        from app.skills.kv_store import KVStoreSkill

        return KVStoreSkill(allow_external=False)

    @pytest.fixture
    def voyage_embed_skill(self):
        """Create Voyage embed skill in stubbed mode."""
        from app.skills.voyage_embed import VoyageEmbedSkill

        return VoyageEmbedSkill(allow_external=False)

    @pytest.fixture
    def slack_send_skill(self):
        """Create Slack send skill in stubbed mode."""
        from app.skills.slack_send import SlackSendSkill

        return SlackSendSkill(allow_external=False)

    @pytest.fixture
    def email_send_skill(self):
        """Create Email send skill in stubbed mode."""
        from app.skills.email_send import EmailSendSkill

        return EmailSendSkill(allow_external=False)

    @pytest.mark.asyncio
    async def test_five_step_workflow_stubbed(
        self, workflow_run_id, kv_store_skill, voyage_embed_skill, slack_send_skill, email_send_skill
    ):
        """
        Execute full 5-step workflow in stubbed mode.

        This tests the skill execution flow and result structure.
        """
        results = []

        # Step 1: KV Store SET - Initialize workflow state
        step1_result = await kv_store_skill.execute(
            {
                "operation": "set",
                "namespace": workflow_run_id,
                "key": "status",
                "value": {"state": "started", "step": 1},
                "ttl_seconds": 3600,
                "idempotency_key": f"{workflow_run_id}_step1",
            }
        )
        results.append(("kv_store_set", step1_result))

        assert step1_result["skill"] == "kv_store"
        assert step1_result["status"] == "stubbed"
        assert step1_result["operation"] == "set"

        # Step 2: Voyage Embed - Generate embedding
        step2_result = await voyage_embed_skill.execute(
            {"input": f"Workflow {workflow_run_id} started successfully", "model": "voyage-3-lite"}
        )
        results.append(("voyage_embed", step2_result))

        assert step2_result["skill"] == "voyage_embed"
        assert step2_result["result"]["status"] == "stubbed"
        assert len(step2_result["result"]["embeddings"]) == 1
        # voyage-3-lite has 512 dimensions
        assert step2_result["result"]["dimensions"] == 512

        # Step 3: Slack Send - Notify channel
        step3_result = await slack_send_skill.execute(
            {
                "text": f"Workflow {workflow_run_id} started",
                "channel": "#aos-notifications",
                "idempotency_key": f"{workflow_run_id}_step3",
            }
        )
        results.append(("slack_send", step3_result))

        assert step3_result["skill"] == "slack_send"
        assert step3_result["result"]["status"] == "stubbed"
        assert step3_result["side_effects"]["slack_stubbed"] is True

        # Step 4: KV Store GET - Retrieve state
        step4_result = await kv_store_skill.execute({"operation": "get", "namespace": workflow_run_id, "key": "status"})
        results.append(("kv_store_get", step4_result))

        assert step4_result["skill"] == "kv_store"
        assert step4_result["status"] == "stubbed"
        assert step4_result["operation"] == "get"

        # Step 5: Email Send - Send completion email
        step5_result = await email_send_skill.execute(
            {
                "to": "admin@agenticverz.com",
                "subject": f"Workflow {workflow_run_id} Complete",
                "body": f"Workflow {workflow_run_id} has completed successfully.",
                "idempotency_key": f"{workflow_run_id}_step5",
            }
        )
        results.append(("email_send", step5_result))

        assert step5_result["skill"] == "email_send"
        assert step5_result["result"]["status"] == "stubbed"
        assert step5_result["side_effects"]["email_stubbed"] is True

        # Verify all 5 steps completed
        assert len(results) == 5

        # Verify duration captured for all steps
        for step_name, result in results:
            assert "duration" in result or "duration_seconds" in result, f"{step_name} missing duration"

        # Print summary
        print("\n=== M11 5-Step Workflow Summary ===")
        for step_name, result in results:
            duration = result.get("duration") or result.get("duration_seconds", 0)
            status = result.get("status") or result.get("result", {}).get("status", "unknown")
            print(f"  {step_name}: {status} ({duration:.3f}s)")

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_workflow_idempotency(self, mock_client_class, workflow_run_id):
        """Test that idempotency prevents duplicate side effects."""
        from app.skills.slack_send import SlackSendSkill

        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "ok"

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client

        slack_send_skill = SlackSendSkill(allow_external=True, webhook_url="https://hooks.slack.com/test")

        idempotency_key = f"{workflow_run_id}_idempotency_test"

        # First execution
        result1 = await slack_send_skill.execute({"text": "Test message", "idempotency_key": idempotency_key})

        # Second execution with same key
        result2 = await slack_send_skill.execute({"text": "Test message", "idempotency_key": idempotency_key})

        # First should be fresh execution
        assert result1["result"].get("from_cache") is not True

        # Second should be from cache
        assert result2["result"]["from_cache"] is True

    @pytest.mark.asyncio
    async def test_workflow_with_different_embedding_models(self, voyage_embed_skill):
        """Test different Voyage embedding models."""
        models = [
            ("voyage-3", 1024),
            ("voyage-3-lite", 512),
            ("voyage-code-3", 1024),
        ]

        for model, expected_dims in models:
            result = await voyage_embed_skill.execute({"input": "Test embedding", "model": model})

            assert result["result"]["dimensions"] == expected_dims, (
                f"Model {model} expected {expected_dims} dims, got {result['result']['dimensions']}"
            )

    @pytest.mark.asyncio
    async def test_workflow_kv_operations(self, kv_store_skill):
        """Test various KV operations in sequence."""
        namespace = "test_kv_ops"

        # SET
        set_result = await kv_store_skill.execute(
            {"operation": "set", "namespace": namespace, "key": "counter", "value": 0}
        )
        assert set_result["status"] == "stubbed"

        # GET
        get_result = await kv_store_skill.execute({"operation": "get", "namespace": namespace, "key": "counter"})
        assert get_result["status"] == "stubbed"

        # EXISTS
        exists_result = await kv_store_skill.execute({"operation": "exists", "namespace": namespace, "key": "counter"})
        assert exists_result["status"] == "stubbed"

        # TTL
        ttl_result = await kv_store_skill.execute({"operation": "ttl", "namespace": namespace, "key": "counter"})
        assert ttl_result["status"] == "stubbed"

        # DELETE
        delete_result = await kv_store_skill.execute({"operation": "delete", "namespace": namespace, "key": "counter"})
        assert delete_result["status"] == "stubbed"


class TestM11WorkflowWithMockedBackends:
    """
    E2E tests with mocked external backends.

    These tests verify the full execution path with real skill logic
    but mocked external services.
    """

    @pytest.mark.asyncio
    @patch("app.skills.kv_store.redis")
    @patch("httpx.AsyncClient")
    async def test_workflow_with_mocked_backends(self, mock_httpx_client, mock_redis):
        """Test workflow with mocked Redis and HTTP clients."""
        from app.skills.email_send import EmailSendSkill
        from app.skills.kv_store import KVStoreSkill
        from app.skills.slack_send import SlackSendSkill
        from app.skills.voyage_embed import VoyageEmbedSkill

        workflow_run_id = "wf_mocked_test"

        # Mock Redis client
        mock_redis_client = AsyncMock()
        mock_redis_client.get.return_value = '{"state": "started"}'
        mock_redis_client.set.return_value = True
        mock_redis.from_url.return_value = mock_redis_client

        # Mock HTTP responses
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "ok"
        mock_response.json.return_value = {
            "data": [{"embedding": [0.1] * 1024}],
            "model": "voyage-3",
            "usage": {"total_tokens": 10},
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.request.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_httpx_client.return_value = mock_client

        # Create skills
        kv_skill = KVStoreSkill(allow_external=True)
        kv_skill._client = mock_redis_client

        slack_skill = SlackSendSkill(allow_external=True, webhook_url="https://hooks.slack.com/test")

        voyage_skill = VoyageEmbedSkill(allow_external=True, api_key="test_key")

        email_skill = EmailSendSkill(allow_external=True, api_key="test_resend_key")

        # Execute workflow
        # Step 1: KV SET
        step1 = await kv_skill.execute(
            {"operation": "set", "namespace": workflow_run_id, "key": "status", "value": {"state": "started"}}
        )
        assert step1["status"] == "ok"

        # Step 2: Voyage Embed
        step2 = await voyage_skill.execute({"input": "Test embedding", "model": "voyage-3"})
        assert step2["result"]["status"] == "ok"

        # Step 3: Slack Send
        step3 = await slack_skill.execute({"text": "Workflow started"})
        assert step3["result"]["status"] == "ok"

        # Step 4: KV GET
        step4 = await kv_skill.execute({"operation": "get", "namespace": workflow_run_id, "key": "status"})
        assert step4["status"] == "ok"
        assert step4["value"] == {"state": "started"}


class TestM11WorkflowJSON:
    """Test workflow execution from JSON specification."""

    @pytest.fixture
    def workflow_spec(self):
        """Example 5-step workflow specification from PIN-059."""
        return {
            "workflow_run_id": "wf_m11_test_001",
            "steps": [
                {
                    "id": "s1",
                    "skill": "kv_store",
                    "params": {
                        "operation": "set",
                        "namespace": "wf_m11_test_001",
                        "key": "status",
                        "value": {"state": "started"},
                    },
                },
                {
                    "id": "s2",
                    "skill": "voyage_embed",
                    "params": {"input": "Workflow started successfully", "model": "voyage-3-lite"},
                },
                {
                    "id": "s3",
                    "skill": "slack_send",
                    "params": {"text": "Workflow wf_m11_test_001 started", "idempotency_key": "wf_m11_test_001_s3"},
                },
                {
                    "id": "s4",
                    "skill": "kv_store",
                    "params": {"operation": "get", "namespace": "wf_m11_test_001", "key": "status"},
                },
                {
                    "id": "s5",
                    "skill": "email_send",
                    "params": {
                        "to": "admin@agenticverz.com",
                        "subject": "Workflow Complete",
                        "body": "Done",
                        "idempotency_key": "wf_m11_test_001_s5",
                    },
                },
            ],
        }

    @pytest.mark.asyncio
    async def test_execute_workflow_spec(self, workflow_spec):
        """Execute workflow from JSON specification."""
        from app.skills import load_all_skills

        # Load all skills to register them
        load_all_skills()

        # Map skill names to classes
        skill_map = {
            "kv_store": ("KVStoreSkill", {"allow_external": False}),
            "voyage_embed": ("VoyageEmbedSkill", {"allow_external": False}),
            "slack_send": ("SlackSendSkill", {"allow_external": False}),
            "email_send": ("EmailSendSkill", {"allow_external": False}),
        }

        results = []

        for step in workflow_spec["steps"]:
            skill_name = step["skill"]
            params = step["params"]

            # Create skill instance
            skill_class_name, config = skill_map.get(skill_name, (None, {}))

            if skill_class_name:
                from app.skills import load_skill

                skill_class = load_skill(skill_class_name)
                skill = skill_class(**config)

                # Execute step
                result = await skill.execute(params)
                results.append({"step_id": step["id"], "skill": skill_name, "result": result})

        # Verify all steps executed
        assert len(results) == 5

        # Verify step IDs
        step_ids = [r["step_id"] for r in results]
        assert step_ids == ["s1", "s2", "s3", "s4", "s5"]

        print("\n=== Workflow Spec Execution Results ===")
        for r in results:
            status = r["result"].get("status") or r["result"].get("result", {}).get("status")
            print(f"  {r['step_id']} ({r['skill']}): {status}")
