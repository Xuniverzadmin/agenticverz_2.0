"""
M0 Schema Validation Tests

Tests for the core JSON schemas defined in M0:
- StructuredOutcome
- SkillMetadata
- ResourceContract
- AgentProfile

Uses jsonschema for validation to ensure cross-language compatibility.
"""

import pytest
import jsonschema
from datetime import datetime, timezone

from app.schemas import (
    get_structured_outcome_schema,
    get_skill_metadata_schema,
    get_resource_contract_schema,
    get_agent_profile_schema,
)


# =============================================================================
# StructuredOutcome Tests
# =============================================================================

class TestStructuredOutcome:
    """Tests for StructuredOutcome schema validation."""

    @pytest.fixture
    def schema(self):
        return get_structured_outcome_schema()

    def test_minimal_success_outcome(self, schema):
        """Test minimal valid success outcome."""
        obj = {
            "status": "success",
            "code": "OK",
            "message": "Operation completed successfully",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cost_cents": 0,
            "latency_ms": 5
        }
        jsonschema.validate(obj, schema)

    def test_minimal_failure_outcome(self, schema):
        """Test minimal valid failure outcome."""
        obj = {
            "status": "failure",
            "code": "ERR_HTTP_TIMEOUT",
            "message": "Request timed out after 5000ms",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cost_cents": 0,
            "latency_ms": 5000
        }
        jsonschema.validate(obj, schema)

    def test_full_outcome_with_all_fields(self, schema):
        """Test outcome with all optional fields."""
        obj = {
            "run_id": "run_abc123",
            "step_id": "step_001",
            "status": "success",
            "code": "OK_HTTP_CALL",
            "message": "HTTP call succeeded",
            "details": {
                "response_status": 200,
                "response_body": {"data": "test"}
            },
            "cost_cents": 5,
            "latency_ms": 150,
            "retryable": False,
            "side_effects": [
                {"type": "http_request", "url": "https://api.example.com"}
            ],
            "metadata": {
                "skill_id": "http_call",
                "skill_version": "1.0.0"
            },
            "observability": {
                "trace_id": "trace_xyz",
                "span_id": "span_123",
                "backend_retries": 0
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        jsonschema.validate(obj, schema)

    def test_partial_status(self, schema):
        """Test partial status is valid."""
        obj = {
            "status": "partial",
            "code": "OK_PARTIAL",
            "message": "Partial results returned",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cost_cents": 10,
            "latency_ms": 200
        }
        jsonschema.validate(obj, schema)

    def test_skipped_status(self, schema):
        """Test skipped status is valid."""
        obj = {
            "status": "skipped",
            "code": "SKIP_DUPLICATE",
            "message": "Step skipped - already executed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cost_cents": 0,
            "latency_ms": 0
        }
        jsonschema.validate(obj, schema)

    def test_invalid_status_rejected(self, schema):
        """Test invalid status is rejected."""
        obj = {
            "status": "invalid_status",
            "code": "OK",
            "message": "test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cost_cents": 0,
            "latency_ms": 0
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(obj, schema)

    def test_missing_required_field_rejected(self, schema):
        """Test missing required field is rejected."""
        obj = {
            "status": "success",
            "code": "OK",
            # missing message, timestamp, cost_cents, latency_ms
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(obj, schema)

    def test_invalid_code_pattern_rejected(self, schema):
        """Test invalid code pattern is rejected."""
        obj = {
            "status": "success",
            "code": "invalid code with spaces",
            "message": "test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cost_cents": 0,
            "latency_ms": 0
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(obj, schema)

    def test_negative_cost_rejected(self, schema):
        """Test negative cost is rejected."""
        obj = {
            "status": "success",
            "code": "OK",
            "message": "test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cost_cents": -1,
            "latency_ms": 0
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(obj, schema)

    def test_additional_properties_rejected(self, schema):
        """Test additional properties are rejected."""
        obj = {
            "status": "success",
            "code": "OK",
            "message": "test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cost_cents": 0,
            "latency_ms": 0,
            "unknown_field": "should fail"
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(obj, schema)


# =============================================================================
# SkillMetadata Tests
# =============================================================================

class TestSkillMetadata:
    """Tests for SkillMetadata schema validation."""

    @pytest.fixture
    def schema(self):
        return get_skill_metadata_schema()

    def test_minimal_skill_metadata(self, schema):
        """Test minimal valid skill metadata."""
        obj = {
            "skill_id": "http_call.v1",
            "name": "HTTP Call",
            "version": "1.0.0",
            "input_schema": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"]
            },
            "output_schema": {"type": "object"},
            "timeout_ms": 5000,
            "cost_estimate_cents": 5
        }
        jsonschema.validate(obj, schema)

    def test_full_skill_metadata(self, schema):
        """Test skill metadata with all optional fields."""
        obj = {
            "skill_id": "llm_invoke.claude",
            "name": "LLM Invoke (Claude)",
            "version": "1.2.0-beta.1",
            "description": "Invoke Claude LLM for text generation",
            "input_schema": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "max_tokens": {"type": "integer"}
                },
                "required": ["prompt"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "tokens_used": {"type": "integer"}
                }
            },
            "timeout_ms": 30000,
            "retry_policy": {
                "max_attempts": 3,
                "backoff_ms": 1000,
                "retry_on": ["ERR_LLM_RATE_LIMIT", "ERR_LLM_API_ERROR"]
            },
            "permissions": ["llm_invoke", "external_api"],
            "cost_estimate_cents": 50,
            "side_effects": ["llm_call"],
            "tags": ["llm", "claude", "text-generation"],
            "owner": "platform-team",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        jsonschema.validate(obj, schema)

    def test_invalid_skill_id_pattern(self, schema):
        """Test invalid skill_id pattern is rejected."""
        obj = {
            "skill_id": "Invalid Skill ID",  # uppercase and spaces
            "name": "Test",
            "version": "1.0.0",
            "input_schema": {},
            "output_schema": {},
            "timeout_ms": 1000,
            "cost_estimate_cents": 0
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(obj, schema)

    def test_invalid_version_pattern(self, schema):
        """Test invalid version pattern is rejected."""
        obj = {
            "skill_id": "test",
            "name": "Test",
            "version": "v1",  # not semver
            "input_schema": {},
            "output_schema": {},
            "timeout_ms": 1000,
            "cost_estimate_cents": 0
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(obj, schema)

    def test_valid_semver_with_prerelease(self, schema):
        """Test valid semver with prerelease tag."""
        obj = {
            "skill_id": "test",
            "name": "Test",
            "version": "2.0.0-alpha.1",
            "input_schema": {},
            "output_schema": {},
            "timeout_ms": 1000,
            "cost_estimate_cents": 0
        }
        jsonschema.validate(obj, schema)


# =============================================================================
# ResourceContract Tests
# =============================================================================

class TestResourceContract:
    """Tests for ResourceContract schema validation."""

    @pytest.fixture
    def schema(self):
        return get_resource_contract_schema()

    def test_minimal_resource_contract(self, schema):
        """Test minimal valid resource contract."""
        obj = {
            "contract_id": "contract_001",
            "principal": "agent_abc",
            "budget_cents": 10000,
            "period": "30d",
            "allowed_operations": ["http_call", "llm_invoke"]
        }
        jsonschema.validate(obj, schema)

    def test_full_resource_contract(self, schema):
        """Test resource contract with all optional fields."""
        obj = {
            "contract_id": "contract_001",
            "principal": "tenant_xyz",
            "currency": "USD",
            "budget_cents": 100000,
            "period": "24h",
            "quotas": {
                "llm_invoke": {
                    "limit": 1000,
                    "window": "1h",
                    "per": "agent"
                },
                "http_call": {
                    "limit": 10000
                }
            },
            "allowed_operations": ["http_call", "llm_invoke", "json_transform"],
            "cost_model": {
                "llm_invoke": {"base_cost_cents": 10, "per_token_cents": 0.001}
            },
            "policy": {
                "max_tokens_per_day": 100000,
                "disallowed_skills": ["email_send"]
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": "2025-12-31T23:59:59Z"
        }
        jsonschema.validate(obj, schema)

    def test_valid_period_formats(self, schema):
        """Test various valid period formats."""
        for period in ["30d", "24h", "60m", "1d", "720h"]:
            obj = {
                "contract_id": "test",
                "principal": "agent",
                "budget_cents": 1000,
                "period": period,
                "allowed_operations": ["http_call"]
            }
            jsonschema.validate(obj, schema)

    def test_invalid_period_format(self, schema):
        """Test invalid period format is rejected."""
        obj = {
            "contract_id": "test",
            "principal": "agent",
            "budget_cents": 1000,
            "period": "1 month",  # invalid format
            "allowed_operations": ["http_call"]
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(obj, schema)

    def test_null_expires_at_allowed(self, schema):
        """Test null expires_at is allowed."""
        obj = {
            "contract_id": "test",
            "principal": "agent",
            "budget_cents": 1000,
            "period": "30d",
            "allowed_operations": ["http_call"],
            "expires_at": None
        }
        jsonschema.validate(obj, schema)


# =============================================================================
# AgentProfile Tests
# =============================================================================

class TestAgentProfile:
    """Tests for AgentProfile schema validation."""

    @pytest.fixture
    def schema(self):
        return get_agent_profile_schema()

    def test_minimal_agent_profile(self, schema):
        """Test minimal valid agent profile."""
        obj = {
            "agent_id": "agent_001",
            "name": "Test Agent",
            "planner": {
                "name": "claude"
            },
            "default_resource_contract_id": "contract_001"
        }
        jsonschema.validate(obj, schema)

    def test_full_agent_profile(self, schema):
        """Test agent profile with all optional fields."""
        obj = {
            "agent_id": "agent_001",
            "name": "Production Agent",
            "description": "Agent for handling customer requests",
            "planner": {
                "name": "claude",
                "version": "claude-sonnet-4-20250514"
            },
            "default_resource_contract_id": "contract_001",
            "permissions": ["http_call", "llm_invoke", "email_send"],
            "memory_policy": {
                "enabled": True,
                "retriever": "postgres",
                "max_tokens": 4000,
                "recency_weight": 0.7
            },
            "safety": {
                "disallowed_side_effects": ["email_send_bulk"],
                "max_external_calls_per_run": 50
            },
            "defaults": {
                "timeout_ms": 30000,
                "preferred_model": "claude-sonnet-4-20250514"
            },
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        jsonschema.validate(obj, schema)

    def test_planner_requires_name(self, schema):
        """Test planner object requires name field."""
        obj = {
            "agent_id": "agent_001",
            "name": "Test",
            "planner": {
                "version": "1.0.0"  # missing name
            },
            "default_resource_contract_id": "contract_001"
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(obj, schema)

    def test_memory_policy_no_additional_properties(self, schema):
        """Test memory_policy rejects additional properties."""
        obj = {
            "agent_id": "agent_001",
            "name": "Test",
            "planner": {"name": "claude"},
            "default_resource_contract_id": "contract_001",
            "memory_policy": {
                "enabled": True,
                "unknown_field": "should fail"
            }
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(obj, schema)


# =============================================================================
# Schema Loading Tests
# =============================================================================

class TestSchemaLoading:
    """Tests for schema loading functions."""

    def test_all_schemas_load_successfully(self):
        """Test all schemas can be loaded."""
        schemas = [
            get_structured_outcome_schema(),
            get_skill_metadata_schema(),
            get_resource_contract_schema(),
            get_agent_profile_schema(),
        ]
        for schema in schemas:
            assert "$schema" in schema
            assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
            assert "title" in schema
            assert "type" in schema

    def test_schemas_have_required_fields(self):
        """Test all schemas define required fields."""
        schemas = {
            "StructuredOutcome": get_structured_outcome_schema(),
            "SkillMetadata": get_skill_metadata_schema(),
            "ResourceContract": get_resource_contract_schema(),
            "AgentProfile": get_agent_profile_schema(),
        }
        for name, schema in schemas.items():
            assert "required" in schema, f"{name} should have required fields"
            assert len(schema["required"]) > 0, f"{name} should have at least one required field"

    def test_schemas_disallow_additional_properties(self):
        """Test all schemas disallow additional properties."""
        schemas = {
            "StructuredOutcome": get_structured_outcome_schema(),
            "SkillMetadata": get_skill_metadata_schema(),
            "ResourceContract": get_resource_contract_schema(),
            "AgentProfile": get_agent_profile_schema(),
        }
        for name, schema in schemas.items():
            assert schema.get("additionalProperties") is False, \
                f"{name} should disallow additional properties"
