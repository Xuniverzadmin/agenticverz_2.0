# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: test
#   Execution: sync
# Role: FOPS token generation for tests
# Callers: test fixtures
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: PIN-398 (Founder Auth Architecture)

"""
FOPS Token Test Fixtures

Provides utilities for generating valid FOPS tokens in tests.
These are REAL tokens that go through the gateway - no mocking.

USAGE:
    @pytest.fixture
    def founder_headers():
        token = make_fops_token(
            sub="founder-test",
            reason="test-suite",
            secret=settings.AOS_FOPS_SECRET,
        )
        return {"Authorization": f"Bearer {token}"}

HARD RULES:
- Tests MUST use real FOPS tokens
- Tests MUST go through gateway
- Tests MUST NOT mock auth contexts
- If a test can't pass with a real token, DELETE the test
"""

import os
from datetime import datetime, timedelta, timezone

import jwt

# Default test secret (only for testing, never production)
DEFAULT_TEST_SECRET = "test-fops-secret-for-testing-only"


def make_fops_token(
    *,
    sub: str,
    reason: str,
    secret: str | None = None,
    expires_in_seconds: int = 3600,
) -> str:
    """
    Generate a valid FOPS token for testing.

    Args:
        sub: Founder identifier (e.g., "founder-test")
        reason: Required reason for access (audit trail)
        secret: FOPS secret for signing (defaults to test secret)
        expires_in_seconds: Token lifetime (default 1 hour)

    Returns:
        Signed JWT string

    Example:
        token = make_fops_token(
            sub="founder-1",
            reason="emergency-unblock",
            secret=os.getenv("AOS_FOPS_SECRET"),
        )
    """
    if secret is None:
        secret = os.getenv("AOS_FOPS_SECRET", DEFAULT_TEST_SECRET)

    now = datetime.now(timezone.utc)
    payload = {
        "iss": "agenticverz-fops",
        "sub": sub,
        "reason": reason,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_in_seconds)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def get_founder_headers(
    *,
    sub: str = "founder-test",
    reason: str = "test-suite",
    secret: str | None = None,
) -> dict:
    """
    Get Authorization headers with a valid FOPS token.

    Convenience function for tests.

    Args:
        sub: Founder identifier
        reason: Required reason for access
        secret: FOPS secret (defaults to env var or test secret)

    Returns:
        Dict with Authorization header
    """
    token = make_fops_token(sub=sub, reason=reason, secret=secret)
    return {"Authorization": f"Bearer {token}"}
