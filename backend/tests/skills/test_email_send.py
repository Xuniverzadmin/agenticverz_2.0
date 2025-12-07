# tests/skills/test_email_send.py
"""
Tests for Email Send Skill (Resend)

Tests stubbed behavior, validation, error handling, and API integration.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

# Path setup
_backend = Path(__file__).parent.parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))


class TestEmailSendSkillStubbed:
    """Test email_send skill in stubbed mode (no external calls)."""

    @pytest.fixture
    def stubbed_skill(self):
        """Create skill with external calls disabled."""
        from app.skills.email_send import EmailSendSkill
        return EmailSendSkill(allow_external=False)

    @pytest.mark.asyncio
    async def test_stubbed_returns_stub_response(self, stubbed_skill):
        """When allow_external=False, returns stubbed response."""
        params = {
            "to": "user@example.com",
            "subject": "Test Subject",
            "body": "Test body content",
        }
        result = await stubbed_skill.execute(params)

        assert result["skill"] == "email_send"
        assert result["skill_version"] == "1.0.0"
        assert result["result"]["status"] == "stubbed"
        assert "stub_" in result["result"]["message_id"]
        assert result["result"]["recipients"] == ["user@example.com"]
        assert result["result"]["accepted"] == 1
        assert result["result"]["rejected"] == 0
        assert result["side_effects"]["email_stubbed"] is True

    @pytest.mark.asyncio
    async def test_stubbed_multiple_recipients(self, stubbed_skill):
        """Stubbed mode handles multiple recipients correctly."""
        params = {
            "to": ["user1@example.com", "user2@example.com"],
            "subject": "Test",
            "body": "Body",
            "cc": "cc@example.com",
            "bcc": ["bcc1@example.com", "bcc2@example.com"],
        }
        result = await stubbed_skill.execute(params)

        assert result["result"]["status"] == "stubbed"
        assert len(result["result"]["recipients"]) == 5
        assert result["result"]["accepted"] == 5


class TestEmailSendSkillValidation:
    """Test input validation."""

    @pytest.fixture
    def skill(self):
        """Create skill with external calls enabled but fake API key for validation tests."""
        from app.skills.email_send import EmailSendSkill
        return EmailSendSkill(allow_external=True, api_key="test_key")

    @pytest.mark.asyncio
    async def test_missing_recipients_error(self, skill):
        """Missing recipients returns validation error."""
        params = {
            "to": [],
            "subject": "Test",
            "body": "Body",
        }
        result = await skill.execute(params)

        assert result["result"]["status"] == "error"
        assert result["result"]["error"] == "validation_error"
        assert "No recipients" in result["result"]["message"]

    @pytest.mark.asyncio
    async def test_missing_subject_error(self, skill):
        """Missing subject returns validation error."""
        params = {
            "to": "user@example.com",
            "subject": "",
            "body": "Body",
        }
        result = await skill.execute(params)

        assert result["result"]["status"] == "error"
        assert result["result"]["error"] == "validation_error"
        assert "Subject is required" in result["result"]["message"]


class TestEmailSendSkillConfiguration:
    """Test skill configuration."""

    def test_api_key_from_env(self):
        """API key can be loaded from environment."""
        with patch.dict('os.environ', {'RESEND_API_KEY': 'env_key_123'}):
            # Force re-import to pick up env var
            import importlib
            import app.skills.email_send as email_module
            importlib.reload(email_module)
            skill = email_module.EmailSendSkill()
            assert skill.api_key == "env_key_123"

    def test_api_key_from_constructor(self):
        """API key from constructor takes precedence."""
        from app.skills.email_send import EmailSendSkill
        skill = EmailSendSkill(api_key="constructor_key")
        assert skill.api_key == "constructor_key"

    def test_from_address_default(self):
        """Default from address is set."""
        from app.skills.email_send import EmailSendSkill
        skill = EmailSendSkill()
        assert "agenticverz.com" in skill.from_address

    def test_from_address_from_constructor(self):
        """From address can be overridden."""
        from app.skills.email_send import EmailSendSkill
        skill = EmailSendSkill(from_address="custom@example.com")
        assert skill.from_address == "custom@example.com"


class TestEmailSendSkillApiIntegration:
    """Test API integration with mocked httpx."""

    @pytest.fixture
    def skill(self):
        """Create skill with test API key."""
        from app.skills.email_send import EmailSendSkill
        return EmailSendSkill(allow_external=True, api_key="test_api_key")

    @pytest.mark.asyncio
    async def test_successful_send(self, skill):
        """Successful email send returns message_id."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "msg_123abc"}

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            params = {
                "to": "user@example.com",
                "subject": "Test Subject",
                "body": "Test body",
            }
            result = await skill.execute(params)

            assert result["result"]["status"] == "ok"
            assert result["result"]["message_id"] == "msg_123abc"
            assert result["result"]["accepted"] == 1
            assert result["side_effects"]["email_sent"] is True
            assert result["side_effects"]["provider"] == "resend"

    @pytest.mark.asyncio
    async def test_api_error_response(self, skill):
        """API error returns error status."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"error": "Invalid email address"}'

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            params = {
                "to": "invalid-email",
                "subject": "Test",
                "body": "Body",
            }
            result = await skill.execute(params)

            assert result["result"]["status"] == "error"
            assert result["result"]["error"] == "api_error"
            assert "400" in result["result"]["message"]
            assert result["result"]["rejected"] == 1

    @pytest.mark.asyncio
    async def test_timeout_error(self, skill):
        """Timeout returns timeout status."""
        import httpx

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.side_effect = httpx.TimeoutException("Request timed out")
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            params = {
                "to": "user@example.com",
                "subject": "Test",
                "body": "Body",
            }
            result = await skill.execute(params)

            assert result["result"]["status"] == "timeout"
            assert "timed out" in result["result"]["message"]

    @pytest.mark.asyncio
    async def test_network_error(self, skill):
        """Network error returns error status."""
        import httpx

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.side_effect = httpx.ConnectError("Connection refused")
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            params = {
                "to": "user@example.com",
                "subject": "Test",
                "body": "Body",
            }
            result = await skill.execute(params)

            assert result["result"]["status"] == "error"
            assert result["result"]["error"] == "network_error"


class TestEmailSendSkillHtmlSupport:
    """Test HTML email support."""

    @pytest.fixture
    def skill(self):
        """Create skill with test API key."""
        from app.skills.email_send import EmailSendSkill
        return EmailSendSkill(allow_external=True, api_key="test_api_key")

    @pytest.mark.asyncio
    async def test_html_body_in_payload(self, skill):
        """HTML flag sends body as html field."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "msg_html"}

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            params = {
                "to": "user@example.com",
                "subject": "HTML Test",
                "body": "<h1>Hello</h1><p>World</p>",
                "html": True,
            }
            result = await skill.execute(params)

            # Check that the post was called with html field
            call_args = mock_instance.post.call_args
            payload = call_args.kwargs.get('json') or call_args[1].get('json')
            assert "html" in payload
            assert payload["html"] == "<h1>Hello</h1><p>World</p>"
            assert "text" not in payload

    @pytest.mark.asyncio
    async def test_plain_text_body_in_payload(self, skill):
        """Non-HTML sends body as text field."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "msg_text"}

        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            params = {
                "to": "user@example.com",
                "subject": "Text Test",
                "body": "Plain text content",
                "html": False,
            }
            result = await skill.execute(params)

            call_args = mock_instance.post.call_args
            payload = call_args.kwargs.get('json') or call_args[1].get('json')
            assert "text" in payload
            assert payload["text"] == "Plain text content"
            assert "html" not in payload


class TestEmailSendSkillRegistry:
    """Test skill registration."""

    def test_skill_is_registered(self):
        """email_send skill is registered in the registry."""
        from app.skills import load_skill, skill_exists

        # Load the skill module to trigger registration
        load_skill("EmailSendSkill")

        assert skill_exists("email_send")

    def test_skill_has_correct_metadata(self):
        """Skill has correct metadata in registry."""
        from app.skills import load_skill, get_skill_entry

        load_skill("EmailSendSkill")
        entry = get_skill_entry("email_send")

        assert entry is not None
        assert entry.name == "email_send"
        assert entry.version == "1.0.0"
        assert "email" in entry.tags
        assert "communication" in entry.tags

    def test_skill_input_schema_available(self):
        """Input schema is available for validation."""
        from app.skills import load_skill, get_skill_entry

        load_skill("EmailSendSkill")
        entry = get_skill_entry("email_send")

        assert entry.input_schema is not None
        schema = entry.input_schema.model_json_schema()
        assert "to" in schema["properties"]
        assert "subject" in schema["properties"]
        assert "body" in schema["properties"]


class TestEmailSendSchemas:
    """Test Pydantic schemas."""

    def test_input_schema_normalizes_string_to(self):
        """String 'to' field is normalized to list."""
        from app.schemas.skill import EmailSendInput

        input_data = EmailSendInput(
            to="single@example.com",
            subject="Test",
            body="Body",
        )
        assert input_data.to == ["single@example.com"]

    def test_input_schema_accepts_list_to(self):
        """List 'to' field is accepted."""
        from app.schemas.skill import EmailSendInput

        input_data = EmailSendInput(
            to=["user1@example.com", "user2@example.com"],
            subject="Test",
            body="Body",
        )
        assert input_data.to == ["user1@example.com", "user2@example.com"]

    def test_input_schema_normalizes_cc_bcc(self):
        """CC and BCC are normalized to lists."""
        from app.schemas.skill import EmailSendInput

        input_data = EmailSendInput(
            to="user@example.com",
            subject="Test",
            body="Body",
            cc="cc@example.com",
            bcc="bcc@example.com",
        )
        assert input_data.cc == ["cc@example.com"]
        assert input_data.bcc == ["bcc@example.com"]

    def test_input_schema_optional_fields(self):
        """Optional fields default to None."""
        from app.schemas.skill import EmailSendInput

        input_data = EmailSendInput(
            to="user@example.com",
            subject="Test",
            body="Body",
        )
        assert input_data.from_address is None
        assert input_data.reply_to is None
        assert input_data.cc is None
        assert input_data.bcc is None
        assert input_data.tags is None
        assert input_data.html is False
