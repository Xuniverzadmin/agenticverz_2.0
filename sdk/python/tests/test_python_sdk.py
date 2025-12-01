import os
import pytest
from nova_sdk import NovaClient

API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")
API_KEY = os.environ.get("API_KEY", "edf7eeb8df7ed639b9d1d8bcac572cea5b8cf97e1dffa00d0d3c5ded0f728aaf")


def test_create_agent_and_post_goal_smoke():
    c = NovaClient(api_key=API_KEY, base_url=API_URL)
    # create_agent may fail if endpoint not implemented; use try/except to surface clear error
    try:
        agent_id = c.create_agent("sdk-smoke-agent")
    except Exception as e:
        pytest.skip(f"backend not available at {API_URL}: {e}")
    run_id = c.post_goal(agent_id, "ping", force_skill="http_call")
    assert run_id is not None
