# M11 Skills Unit Tests
# Tests for kv_store, slack_send, webhook_send, voyage_embed

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ====================
# KV Store Skill Tests
# ====================


class TestKVStoreSkill:
    """Tests for KVStoreSkill."""

    @pytest.fixture
    def skill(self):
        """Create skill instance with stubbed mode."""
        from app.skills.kv_store import KVStoreSkill

        return KVStoreSkill(allow_external=False)

    @pytest.mark.asyncio
    async def test_stubbed_get(self, skill):
        """Test GET operation in stubbed mode."""
        result = await skill.execute({"operation": "get", "key": "test_key", "namespace": "test"})

        assert result["skill"] == "kv_store"
        assert result["status"] == "stubbed"

    @pytest.mark.asyncio
    async def test_stubbed_set(self, skill):
        """Test SET operation in stubbed mode."""
        result = await skill.execute(
            {"operation": "set", "key": "test_key", "value": {"foo": "bar"}, "namespace": "test"}
        )

        assert result["skill"] == "kv_store"
        assert result["status"] == "stubbed"

    @pytest.mark.asyncio
    async def test_key_construction(self, skill):
        """Test key prefix construction."""
        key = skill._make_key("my_namespace", "my_key")
        assert key == "aos:my_namespace:my_key"

    @pytest.mark.asyncio
    async def test_idempotency_key_construction(self, skill):
        """Test idempotency key construction."""
        key = skill._make_idempotency_key("idem_123")
        assert key == "aos:idem:idem_123"

    @pytest.mark.asyncio
    @patch("app.skills.kv_store.redis")
    async def test_real_get_operation(self, mock_redis):
        """Test real GET operation with mocked Redis."""
        from app.skills.kv_store import KVStoreSkill

        # Mock Redis client
        mock_client = AsyncMock()
        mock_client.get.return_value = '{"data": "test"}'
        mock_redis.from_url.return_value = mock_client

        skill = KVStoreSkill(allow_external=True)
        skill._client = mock_client

        result = await skill.execute({"operation": "get", "key": "test_key", "namespace": "test"})

        assert result["status"] == "ok"
        assert result["value"] == {"data": "test"}
        assert result["exists"] is True

    @pytest.mark.asyncio
    @patch("app.skills.kv_store.redis")
    async def test_real_set_operation(self, mock_redis):
        """Test real SET operation with mocked Redis."""
        from app.skills.kv_store import KVStoreSkill

        mock_client = AsyncMock()
        mock_client.set.return_value = True
        mock_redis.from_url.return_value = mock_client

        skill = KVStoreSkill(allow_external=True)
        skill._client = mock_client

        result = await skill.execute(
            {"operation": "set", "key": "test_key", "value": {"foo": "bar"}, "namespace": "test", "ttl_seconds": 3600}
        )

        assert result["status"] == "ok"
        assert result["value"] == {"foo": "bar"}
        mock_client.set.assert_called_once()


# ====================
# Slack Send Skill Tests
# ====================


class TestSlackSendSkill:
    """Tests for SlackSendSkill."""

    @pytest.fixture
    def skill(self):
        """Create skill instance with stubbed mode."""
        from app.skills.slack_send import SlackSendSkill

        return SlackSendSkill(allow_external=False)

    @pytest.mark.asyncio
    async def test_stubbed_send(self, skill):
        """Test send in stubbed mode."""
        result = await skill.execute({"text": "Hello, World!", "channel": "#test"})

        assert result["skill"] == "slack_send"
        assert result["result"]["status"] == "stubbed"
        assert result["side_effects"]["slack_stubbed"] is True

    @pytest.mark.asyncio
    async def test_missing_webhook_url(self):
        """Test error when webhook URL not configured."""
        from app.skills.slack_send import SlackSendSkill

        skill = SlackSendSkill(allow_external=True, webhook_url="")

        result = await skill.execute({"text": "Hello!"})

        assert result["result"]["status"] == "error"
        assert "configuration_error" in result["result"]["error"]

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_successful_send(self, mock_client_class):
        """Test successful Slack message send."""
        from app.skills.slack_send import SlackSendSkill

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "ok"

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client

        skill = SlackSendSkill(allow_external=True, webhook_url="https://hooks.slack.com/test")

        result = await skill.execute({"text": "Test message", "channel": "#test"})

        assert result["result"]["status"] == "ok"
        assert result["result"]["webhook_response"] == "ok"
        assert result["side_effects"]["slack_message_sent"] is True

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_idempotency_cache(self, mock_client_class):
        """Test idempotency caching with mocked backend."""
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

        skill = SlackSendSkill(allow_external=True, webhook_url="https://hooks.slack.com/test")

        # First call - should execute
        result1 = await skill.execute({"text": "Test", "idempotency_key": "test_123"})
        assert result1["result"]["status"] == "ok"
        assert result1["result"].get("from_cache") is not True

        # Second call with same key - should be from cache
        result2 = await skill.execute({"text": "Test", "idempotency_key": "test_123"})
        assert result2["result"].get("from_cache") is True


# ====================
# Webhook Send Skill Tests
# ====================


class TestWebhookSendSkill:
    """Tests for WebhookSendSkill."""

    @pytest.fixture
    def skill(self):
        """Create skill instance with stubbed mode."""
        from app.skills.webhook_send import WebhookSendSkill

        return WebhookSendSkill(allow_external=False, signing_secret="test_secret")

    @pytest.mark.asyncio
    async def test_stubbed_send(self, skill):
        """Test webhook send in stubbed mode."""
        result = await skill.execute({"url": "https://example.com/webhook", "payload": {"event": "test"}})

        assert result["skill"] == "webhook_send"
        assert result["result"]["status"] == "stubbed"
        assert result["result"]["signature_sent"] is True

    @pytest.mark.asyncio
    async def test_missing_url(self, skill):
        """Test error when URL not provided."""
        result = await skill.execute({"payload": {"event": "test"}})

        assert result["result"]["status"] == "error"
        assert "validation_error" in result["result"]["error"]

    def test_signature_generation(self):
        """Test HMAC signature generation."""
        from app.skills.webhook_send import sign_payload, verify_signature

        payload = b'{"event":"test"}'
        secret = "my_secret"
        timestamp = 1234567890

        signature = sign_payload(payload, secret, timestamp)

        assert signature.startswith("sha256=")
        assert verify_signature(payload, secret, timestamp, signature)

    def test_signature_verification_failure(self):
        """Test signature verification failure."""
        from app.skills.webhook_send import sign_payload, verify_signature

        payload = b'{"event":"test"}'
        secret = "my_secret"
        timestamp = 1234567890

        signature = sign_payload(payload, secret, timestamp)

        # Wrong secret should fail
        assert not verify_signature(payload, "wrong_secret", timestamp, signature)

        # Wrong timestamp should fail
        assert not verify_signature(payload, secret, timestamp + 1, signature)

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_successful_webhook_send(self, mock_client_class):
        """Test successful webhook send with signature."""
        from app.skills.webhook_send import WebhookSendSkill

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"received": true}'
        mock_response.headers = {"X-Request-ID": "req_123"}

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client

        skill = WebhookSendSkill(allow_external=True, signing_secret="test_secret")

        result = await skill.execute(
            {"url": "https://example.com/webhook", "payload": {"event": "test"}, "sign_payload": True}
        )

        assert result["result"]["status"] == "ok"
        assert result["result"]["status_code"] == 200
        assert result["result"]["signature_sent"] is True
        assert result["result"]["request_id"] == "req_123"


# ====================
# Voyage Embed Skill Tests
# ====================


class TestVoyageEmbedSkill:
    """Tests for VoyageEmbedSkill."""

    @pytest.fixture
    def skill(self):
        """Create skill instance with stubbed mode."""
        from app.skills.voyage_embed import VoyageEmbedSkill

        return VoyageEmbedSkill(allow_external=False)

    @pytest.mark.asyncio
    async def test_stubbed_embed(self, skill):
        """Test embedding generation in stubbed mode."""
        result = await skill.execute({"input": "Hello, world!", "model": "voyage-3"})

        assert result["skill"] == "voyage_embed"
        assert result["result"]["status"] == "stubbed"
        assert len(result["result"]["embeddings"]) == 1
        assert len(result["result"]["embeddings"][0]) == 1024  # voyage-3 dimensions

    @pytest.mark.asyncio
    async def test_stubbed_batch_embed(self, skill):
        """Test batch embedding generation in stubbed mode."""
        result = await skill.execute({"input": ["Hello", "World", "Test"], "model": "voyage-3-lite"})

        assert result["result"]["status"] == "stubbed"
        assert len(result["result"]["embeddings"]) == 3
        assert len(result["result"]["embeddings"][0]) == 512  # voyage-3-lite dimensions

    @pytest.mark.asyncio
    async def test_deterministic_stub_embeddings(self, skill):
        """Test that stub embeddings are deterministic."""
        result1 = await skill.execute({"input": "Test text", "model": "voyage-3"})

        result2 = await skill.execute({"input": "Test text", "model": "voyage-3"})

        # Same input should produce same stub embedding
        assert result1["result"]["embeddings"] == result2["result"]["embeddings"]

    @pytest.mark.asyncio
    async def test_empty_input_error(self, skill):
        """Test error on empty input."""
        result = await skill.execute({"input": "", "model": "voyage-3"})

        assert result["result"]["status"] == "error"
        assert "validation_error" in result["result"]["error"]

    @pytest.mark.asyncio
    async def test_missing_api_key(self):
        """Test error when API key not configured."""
        from app.skills.voyage_embed import VoyageEmbedSkill

        skill = VoyageEmbedSkill(allow_external=True, api_key="")

        result = await skill.execute({"input": "Test"})

        assert result["result"]["status"] == "error"
        assert "configuration_error" in result["result"]["error"]

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_successful_embed(self, mock_client_class):
        """Test successful embedding generation."""
        from app.skills.voyage_embed import VoyageEmbedSkill

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"embedding": [0.1, 0.2, 0.3] * 341 + [0.1]}  # 1024 dims
            ],
            "model": "voyage-3",
            "usage": {"total_tokens": 5},
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client

        skill = VoyageEmbedSkill(allow_external=True, api_key="test_key")

        result = await skill.execute({"input": "Test text", "model": "voyage-3"})

        assert result["result"]["status"] == "ok"
        assert len(result["result"]["embeddings"]) == 1
        assert result["result"]["model"] == "voyage-3"
        assert result["result"]["usage"]["total_tokens"] == 5


# ====================
# Integration Tests
# ====================


class TestSkillRegistry:
    """Test skills are properly registered."""

    def test_m11_skills_registered(self):
        """Test all M11 skills are in the registry."""
        from app.skills import list_skills, load_all_skills

        load_all_skills()
        skills = list_skills()
        skill_names = [s["name"] for s in skills]

        assert "kv_store" in skill_names
        assert "slack_send" in skill_names
        assert "webhook_send" in skill_names
        assert "voyage_embed" in skill_names
        assert "email_send" in skill_names

    def test_skill_manifest(self):
        """Test skill manifest generation."""
        from app.skills import get_skill_manifest, load_all_skills

        load_all_skills()
        manifest = get_skill_manifest()

        # Find kv_store in manifest
        kv_manifest = next((s for s in manifest if s["name"] == "kv_store"), None)
        assert kv_manifest is not None
        assert "input_schema" in kv_manifest
        assert kv_manifest["version"] == "1.0.0"


# ====================
# Input Schema Tests
# ====================


class TestInputSchemas:
    """Test input schema validation."""

    def test_kv_store_input_validation(self):
        """Test KVStoreInput validation."""
        from app.schemas.skill import KVOperation, KVStoreInput

        # Valid input
        input_data = KVStoreInput(operation=KVOperation.SET, key="test_key", value={"foo": "bar"}, namespace="test")
        assert input_data.operation == KVOperation.SET
        assert input_data.key == "test_key"

    def test_slack_send_input_validation(self):
        """Test SlackSendInput validation."""
        from app.schemas.skill import SlackSendInput

        input_data = SlackSendInput(text="Hello!", channel="#test")
        assert input_data.text == "Hello!"
        assert input_data.channel == "#test"

    def test_webhook_send_input_validation(self):
        """Test WebhookSendInput validation."""
        from app.schemas.skill import WebhookSendInput

        input_data = WebhookSendInput(url="https://example.com/webhook", payload={"event": "test"})
        assert input_data.url == "https://example.com/webhook"
        assert input_data.sign_payload is True  # Default

    def test_voyage_embed_input_validation(self):
        """Test VoyageEmbedInput validation."""
        from app.schemas.skill import VoyageEmbedInput, VoyageModel

        input_data = VoyageEmbedInput(input="Test text", model=VoyageModel.VOYAGE_3)
        assert input_data.input == "Test text"
        assert input_data.model == VoyageModel.VOYAGE_3
