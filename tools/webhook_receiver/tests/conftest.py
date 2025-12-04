# tools/webhook_receiver/tests/conftest.py
"""
Pytest configuration for webhook receiver tests.
"""

import os
import sys

import pytest

# Add app directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture(scope="session")
def event_loop_policy():
    """Use default event loop policy."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture
def redis_url():
    """Get Redis URL for testing."""
    return os.getenv("REDIS_TEST_URL", "redis://localhost:6379/1")


@pytest.fixture
def rate_limit_rpm():
    """Default rate limit for tests."""
    return 10


@pytest.fixture
def rate_limit_window():
    """Default rate limit window for tests."""
    return 5
