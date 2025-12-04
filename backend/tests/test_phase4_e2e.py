"""
Phase 4 End-to-End Tests

Tests for:
1. Multi-step plan execution (HTTP → LLM → transform)
2. Plan safety validation
3. Budget deduction
4. New skills (json_transform, postgres_query)

Run with: pytest tests/test_phase4_e2e.py -v

For server-based tests (requires docker compose up):
    pytest tests/test_phase4_e2e.py -v -m e2e
"""
import json
import os
import uuid

import pytest

# Custom markers for test categorization
pytestmark = pytest.mark.e2e

# Set environment before imports
os.environ.setdefault("DATABASE_URL", "postgresql://nova:novapass@localhost:5433/nova_aos")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("AOS_API_KEY", "test-e2e-key")


class TestPlanInspector:
    """Tests for plan safety validation."""

    def test_valid_plan_passes(self):
        """A simple valid plan passes inspection."""
        from app.utils.plan_inspector import validate_plan

        plan = {
            "plan_id": "test-1",
            "steps": [
                {
                    "step_id": "s1",
                    "skill": "http_call",
                    "params": {"url": "https://api.example.com/data", "method": "GET"}
                }
            ],
            "metadata": {}
        }
        result = validate_plan(plan)
        assert result.valid

    def test_forbidden_domain_rejected(self):
        """Plans targeting internal IPs are rejected."""
        from app.utils.plan_inspector import validate_plan

        plan = {
            "plan_id": "test-2",
            "steps": [
                {
                    "step_id": "s1",
                    "skill": "http_call",
                    "params": {"url": "http://169.254.169.254/metadata", "method": "GET"}
                }
            ]
        }
        result = validate_plan(plan)
        assert not result.valid
        assert any("forbidden" in e.message.lower() for e in result.errors)

    def test_localhost_rejected(self):
        """Plans targeting localhost are rejected."""
        from app.utils.plan_inspector import validate_plan

        plan = {
            "plan_id": "test-3",
            "steps": [
                {
                    "step_id": "s1",
                    "skill": "http_call",
                    "params": {"url": "http://localhost:8080/admin", "method": "GET"}
                }
            ]
        }
        result = validate_plan(plan)
        assert not result.valid

    def test_too_many_steps_rejected(self):
        """Plans with excessive steps are rejected."""
        from app.utils.plan_inspector import validate_plan

        plan = {
            "plan_id": "test-4",
            "steps": [{"step_id": f"s{i}", "skill": "http_call", "params": {}} for i in range(30)]
        }
        result = validate_plan(plan)
        assert not result.valid
        assert any("steps" in e.message.lower() and "maximum" in e.message.lower() for e in result.errors)

    def test_unknown_skill_rejected(self):
        """Plans with unknown skills are rejected."""
        from app.utils.plan_inspector import validate_plan

        plan = {
            "plan_id": "test-5",
            "steps": [
                {
                    "step_id": "s1",
                    "skill": "exec_shell",  # Not allowed
                    "params": {"command": "rm -rf /"}
                }
            ]
        }
        result = validate_plan(plan)
        assert not result.valid
        assert any("unknown_skill" in e.code.lower() for e in result.errors)

    def test_budget_check_in_validation(self):
        """Plans exceeding budget are rejected."""
        from app.utils.plan_inspector import validate_plan

        plan = {
            "plan_id": "test-6",
            "steps": [{"step_id": "s1", "skill": "http_call", "params": {}}],
            "metadata": {"estimated_cost_cents": 500}  # 5 dollars
        }
        # With a budget of only 100 cents
        result = validate_plan(plan, agent_budget_cents=100)
        assert not result.valid
        assert any("budget" in e.message.lower() for e in result.errors)


class TestJsonTransformSkill:
    """Tests for json_transform skill."""

    def test_simple_path_extraction(self):
        """Can extract values using dot paths."""
        from app.skills.json_transform import transform_json

        payload = {"data": {"user": {"name": "Alice", "age": 30}}}
        mapping = {"user_name": "data.user.name", "user_age": "data.user.age"}

        result, errors = transform_json(payload, mapping)
        assert result["user_name"] == "Alice"
        assert result["user_age"] == 30
        assert len(errors) == 0

    def test_array_indexing(self):
        """Can extract values from arrays."""
        from app.skills.json_transform import transform_json

        payload = {"items": [{"id": 1}, {"id": 2}, {"id": 3}]}
        mapping = {
            "first_id": "items[0].id",
            "last_id": "items[-1].id"
        }

        result, errors = transform_json(payload, mapping)
        assert result["first_id"] == 1
        assert result["last_id"] == 3

    def test_missing_path_returns_default(self):
        """Missing paths use default values."""
        from app.skills.json_transform import transform_json

        payload = {"data": {}}
        mapping = {"name": "data.user.name"}
        defaults = {"name": "Unknown"}

        result, errors = transform_json(payload, mapping, defaults)
        assert result["name"] == "Unknown"
        # When default is used, no error is reported (value is available)
        # Only missing paths without defaults generate errors

    def test_nested_extraction(self):
        """Can handle deeply nested structures."""
        from app.skills.json_transform import transform_json

        payload = {
            "response": {
                "data": {
                    "results": [
                        {"meta": {"score": 95}}
                    ]
                }
            }
        }
        mapping = {"score": "response.data.results[0].meta.score"}

        result, errors = transform_json(payload, mapping)
        assert result["score"] == 95

    @pytest.mark.asyncio
    async def test_skill_execution(self):
        """Full skill execution works."""
        from app.skills.json_transform import JsonTransformSkill

        skill = JsonTransformSkill()
        result = await skill.execute({
            "payload": {"data": {"items": [1, 2, 3]}},
            "mapping": {"items": "data.items", "first": "data.items[0]"}
        })

        assert result["result"]["status"] == "ok"
        assert result["result"]["result"]["items"] == [1, 2, 3]
        assert result["result"]["result"]["first"] == 1


class TestPostgresQuerySkill:
    """Tests for postgres_query skill."""

    def test_readonly_blocks_insert(self):
        """Read-only mode blocks INSERT statements."""
        from app.skills.postgres_query import is_read_only_query

        assert is_read_only_query("SELECT * FROM users") is True
        assert is_read_only_query("INSERT INTO users VALUES (1)") is False
        assert is_read_only_query("UPDATE users SET name = 'x'") is False
        assert is_read_only_query("DELETE FROM users") is False

    def test_cte_query_allowed(self):
        """WITH...SELECT queries are allowed."""
        from app.skills.postgres_query import is_read_only_query

        query = "WITH recent AS (SELECT * FROM logs) SELECT * FROM recent"
        assert is_read_only_query(query) is True

    def test_explain_allowed(self):
        """EXPLAIN queries are allowed."""
        from app.skills.postgres_query import is_read_only_query

        assert is_read_only_query("EXPLAIN SELECT * FROM users") is True

    def test_forbidden_patterns_blocked(self):
        """Forbidden SQL patterns are blocked by validator."""
        from app.skills.postgres_query import PostgresQueryInput
        from pydantic import ValidationError

        dangerous_queries = [
            "DROP TABLE users",
            "TRUNCATE users",
            "ALTER TABLE users ADD COLUMN x",
            "CREATE TABLE hack (id int)",
        ]

        for query in dangerous_queries:
            with pytest.raises(ValidationError):
                PostgresQueryInput(query=query)


class TestBudgetDeduction:
    """Tests for budget tracking and deduction."""

    def test_cost_calculation(self):
        """LLM cost calculation is accurate."""
        from app.worker.runner import calculate_llm_cost_cents

        # 539 input, 170 output tokens (from our real test)
        # Sonnet 4: $3/1M input, $15/1M output
        # Input: 539 / 1M * 300 cents = 0.0001617 cents
        # Output: 170 / 1M * 1500 cents = 0.000255 cents
        # Total: ~0.0004167 cents → rounds to 1 cent minimum

        cost = calculate_llm_cost_cents("claude-sonnet-4-20250514", 539, 170)
        assert cost == 1  # Minimum 1 cent

        # Larger usage
        cost = calculate_llm_cost_cents("claude-sonnet-4-20250514", 100000, 50000)
        # Input: 100000 / 1M * 300 = 30 cents
        # Output: 50000 / 1M * 1500 = 75 cents
        # Total: 105 cents
        assert cost == 105

    def test_budget_deduction_function_exists(self):
        """Budget deduction functions are available."""
        from app.utils.budget_tracker import (
            deduct_budget,
            record_cost,
            check_budget,
            get_budget_tracker,
        )

        tracker = get_budget_tracker()
        assert tracker is not None


class TestMultiStepExecution:
    """Tests for multi-step plan execution."""

    @pytest.fixture
    def api_key(self):
        return os.environ.get("AOS_API_KEY", "edf7eeb8df7ed639b9d1d8bcac572cea5b8cf97e1dffa00d0d3c5ded0f728aaf")

    @pytest.fixture
    def test_agent(self, api_key):
        """Create a test agent."""
        import httpx

        response = httpx.post(
            "http://localhost:8000/agents",
            headers={
                "X-AOS-Key": api_key,
                "Content-Type": "application/json"
            },
            json={"name": f"e2e-test-{uuid.uuid4().hex[:8]}"}
        )
        assert response.status_code == 201
        return response.json()["agent_id"]

    @pytest.mark.skipif(
        not os.environ.get("RUN_E2E_TESTS"),
        reason="Requires running server - set RUN_E2E_TESTS=1 with docker compose up"
    )
    def test_http_skill_execution(self, api_key, test_agent):
        """HTTP skill executes correctly."""
        import httpx
        import time

        # Submit goal
        response = httpx.post(
            f"http://localhost:8000/agents/{test_agent}/goals",
            headers={
                "X-AOS-Key": api_key,
                "Content-Type": "application/json"
            },
            json={"goal": "Fetch a random quote from https://zenquotes.io/api/random"}
        )
        assert response.status_code == 202
        run_id = response.json()["run_id"]

        # Poll for completion (max 30 seconds)
        max_wait = 30
        poll_interval = 2
        elapsed = 0
        data = None

        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval

            response = httpx.get(
                f"http://localhost:8000/agents/{test_agent}/runs/{run_id}",
                headers={"X-AOS-Key": api_key}
            )
            assert response.status_code == 200
            data = response.json()

            if data["status"] in ("succeeded", "failed"):
                break

        assert data is not None
        assert data["status"] in ("succeeded", "failed"), f"Run still {data['status']} after {max_wait}s"

        # Verify plan was generated (if succeeded)
        if data["status"] == "succeeded":
            assert data.get("plan") is not None
            assert len(data.get("tool_calls", [])) > 0

    @pytest.mark.skipif(
        not os.environ.get("RUN_E2E_TESTS"),
        reason="Skills require running server - set RUN_E2E_TESTS=1 with docker compose up"
    )
    def test_skills_registered(self, api_key):
        """New skills are registered."""
        import httpx

        response = httpx.get(
            "http://localhost:8000/skills",
            headers={"X-AOS-Key": api_key}
        )
        assert response.status_code == 200
        data = response.json()

        skill_names = [s["name"] for s in data["skills"]]
        assert "json_transform" in skill_names
        assert "postgres_query" in skill_names


class TestSkillRegistry:
    """Tests for skill registration."""

    def test_all_skills_registered(self):
        """All expected skills are registered."""
        from app.skills import list_skills, load_all_skills
        load_all_skills()

        skills = list_skills()
        skill_names = [s["name"] for s in skills]

        expected = ["http_call", "calendar_write", "llm_invoke", "json_transform", "postgres_query"]
        for name in expected:
            assert name in skill_names, f"Skill {name} not registered"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
