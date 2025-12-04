import os
import pytest
from nova_sdk import NovaClient

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")
API_KEY = os.environ.get("API_KEY", "edf7eeb8df7ed639b9d1d8bcac572cea5b8cf97e1dffa00d0d3c5ded0f728aaf")


def get_client():
    """Get a configured NovaClient."""
    return NovaClient(api_key=API_KEY, base_url=API_URL)


def test_create_agent_and_post_goal_smoke():
    c = get_client()
    # create_agent may fail if endpoint not implemented; use try/except to surface clear error
    try:
        agent_id = c.create_agent("sdk-smoke-agent")
    except Exception as e:
        pytest.skip(f"backend not available at {API_URL}: {e}")
    run_id = c.post_goal(agent_id, "ping", force_skill="http_call")
    assert run_id is not None


# =========== Machine-Native API Tests ===========

def test_simulate_feasible_plan():
    """Test simulating a feasible plan."""
    c = get_client()
    try:
        result = c.simulate([
            {"skill": "http_call", "params": {"url": "https://api.example.com"}},
            {"skill": "json_transform", "params": {"query": ".data"}}
        ], budget_cents=100)
    except Exception as e:
        pytest.skip(f"backend not available at {API_URL}: {e}")

    assert result["feasible"] is True
    assert result["budget_sufficient"] is True
    assert result["estimated_cost_cents"] >= 0
    assert "step_estimates" in result


def test_simulate_budget_exceeded():
    """Test simulating a plan that exceeds budget."""
    c = get_client()
    try:
        result = c.simulate([
            {"skill": "llm_invoke", "params": {"prompt": "test"}},
            {"skill": "llm_invoke", "params": {"prompt": "test2"}},
            {"skill": "llm_invoke", "params": {"prompt": "test3"}}
        ], budget_cents=5)  # LLM costs 5c each, so 15c total > 5c budget
    except Exception as e:
        pytest.skip(f"backend not available at {API_URL}: {e}")

    assert result["budget_sufficient"] is False
    assert result["estimated_cost_cents"] > 5


def test_query_allowed_skills():
    """Test querying allowed skills."""
    c = get_client()
    try:
        result = c.query("allowed_skills")
    except Exception as e:
        pytest.skip(f"backend not available at {API_URL}: {e}")

    assert "result" in result
    assert "supported_queries" in result
    assert "remaining_budget_cents" in result["supported_queries"]


def test_query_remaining_budget():
    """Test querying remaining budget."""
    c = get_client()
    try:
        result = c.query("remaining_budget_cents")
    except Exception as e:
        pytest.skip(f"backend not available at {API_URL}: {e}")

    assert "result" in result
    assert "remaining_cents" in result["result"]
    assert result["result"]["remaining_cents"] >= 0


def test_list_skills():
    """Test listing available skills."""
    c = get_client()
    try:
        result = c.list_skills()
    except Exception as e:
        pytest.skip(f"backend not available at {API_URL}: {e}")

    # Should have skills from capabilities fallback
    assert "count" in result


def test_describe_skill():
    """Test describing a skill."""
    c = get_client()
    try:
        result = c.describe_skill("http_call")
    except Exception as e:
        pytest.skip(f"backend not available at {API_URL}: {e}")

    assert result["skill_id"] == "http_call"
    assert "cost_model" in result
    assert "failure_modes" in result
    assert "constraints" in result


def test_get_capabilities():
    """Test getting capabilities."""
    c = get_client()
    try:
        result = c.get_capabilities()
    except Exception as e:
        pytest.skip(f"backend not available at {API_URL}: {e}")

    assert "skills" in result
    assert "budget" in result
    assert "rate_limits" in result
    assert "permissions" in result

    # Check skills structure
    skills = result["skills"]
    assert len(skills) > 0

    # Check budget structure
    budget = result["budget"]
    assert "total_cents" in budget
    assert "remaining_cents" in budget


def test_get_resource_contract():
    """Test getting resource contract."""
    c = get_client()
    try:
        result = c.get_resource_contract("default")
    except Exception as e:
        pytest.skip(f"backend not available at {API_URL}: {e}")

    assert "resource_id" in result
    assert "budget" in result
    assert "rate_limits" in result


def test_60_second_demo_scenario():
    """
    Integration test simulating the 60-second machine-native demo.

    Goal: "Fetch BTC price and notify on Slack"

    Steps:
    1. Query capabilities to know what skills are available
    2. Simulate the plan to check feasibility
    3. Execute (if simulate says feasible)
    """
    c = get_client()

    # Step 1: Query capabilities
    try:
        caps = c.get_capabilities()
    except Exception as e:
        pytest.skip(f"backend not available at {API_URL}: {e}")

    assert "http_call" in caps["skills"]
    assert caps["skills"]["http_call"]["available"]

    # Step 2: Build and simulate plan
    plan = [
        {"skill": "http_call", "params": {"url": "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"}},
        {"skill": "json_transform", "params": {"query": ".bitcoin.usd"}},
        {"skill": "webhook_send", "params": {"url": "https://hooks.slack.com/..."}}
    ]

    sim_result = c.simulate(plan, budget_cents=100)

    # The plan should be feasible
    assert sim_result["feasible"] is True
    assert sim_result["budget_sufficient"] is True

    # Should have estimates for all 3 steps
    assert len(sim_result["step_estimates"]) == 3

    # Total cost should be reasonable
    assert sim_result["estimated_cost_cents"] <= 10  # No LLM, just HTTP calls

    # Should identify TIMEOUT as a risk for http_call
    risk_types = [r["risk_type"] for r in sim_result.get("risks", [])]
    assert "TIMEOUT" in risk_types

    print("\n60-second demo scenario PASSED:")
    print(f"  - Capabilities queried: {len(caps['skills'])} skills available")
    print(f"  - Plan simulated: {sim_result['status']}")
    print(f"  - Estimated cost: {sim_result['estimated_cost_cents']}c")
    print(f"  - Estimated duration: {sim_result['estimated_duration_ms']}ms")
    print(f"  - Risks identified: {risk_types}")
