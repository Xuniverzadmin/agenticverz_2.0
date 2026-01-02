# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: test
#   Execution: sync
# Role: Infrastructure dependency declaration and checking for tests
# Callers: Test files via @requires_infra decorator
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-270 (Infrastructure State Governance)

"""
Infrastructure Dependency Helper for Tests

This module provides the `@requires_infra` decorator and related utilities
for declaring infrastructure dependencies in tests.

Usage:
    from tests.helpers.infra import requires_infra

    @requires_infra("Clerk")
    def test_rbac_enforcement():
        ...

All infrastructure items must be declared in docs/infra/INFRA_REGISTRY.md.
"""

import functools
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

import pytest


class InfraState(Enum):
    """Infrastructure availability states per INFRA_REGISTRY.md."""

    A = "Chosen (Conceptual)"  # Selected but not wired locally
    B = "Local Substitute"  # Stub/emulator available
    C = "Fully Wired"  # Required and available


class InfraBucket(Enum):
    """Skip bucket classification for State A infra."""

    B1 = "Production-Required, Locally Missing"  # Must be fixed
    B2 = "Optional / Future"  # Intentionally deferred


@dataclass
class InfraItem:
    """Infrastructure registry entry."""

    name: str
    purpose: str
    state: InfraState
    bucket: Optional[InfraBucket]
    local_strategy: str
    check_fn: Optional[Callable[[], bool]] = None


def _check_postgres() -> bool:
    """Check if PostgreSQL is available."""
    return bool(os.environ.get("DATABASE_URL"))


def _check_redis() -> bool:
    """Check if Redis is available."""
    try:
        import redis

        r = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
        r.ping()
        return True
    except Exception:
        return False


def _check_auth_backend() -> bool:
    """Check if auth backend is running and accepting requests."""
    try:
        import httpx

        response = httpx.get("http://localhost:8000/api/v1/runtime/capabilities", timeout=2.0)
        # 403 means auth is enforced but we don't have valid creds (infra exists)
        # 401 means auth backend exists but rejects us
        # 404 means endpoint doesn't exist (infra missing)
        return response.status_code not in (404, 502, 503)
    except Exception:
        return False


def _check_stub_auth() -> bool:
    """Check if RBAC stub is available (always True when module loads).

    The stub is a pure Python module with no external dependencies.
    If this module can be imported, the stub is available.
    """
    try:
        from app.auth.stub import AUTH_STUB_ENABLED, parse_stub_token

        # Verify stub is enabled and functional
        if not AUTH_STUB_ENABLED:
            return False

        # Verify basic parsing works
        claims = parse_stub_token("stub_admin_test")
        return claims is not None
    except Exception:
        return False


def _check_prometheus() -> bool:
    """Check if Prometheus is available."""
    try:
        import httpx

        response = httpx.get("http://localhost:9090/-/healthy", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


# ============================================================================
# INFRA REGISTRY — Single source of truth
# ============================================================================
# This must match docs/infra/INFRA_REGISTRY.md
# Changes here require human approval

INFRA_REGISTRY: dict[str, InfraItem] = {
    "PostgreSQL": InfraItem(
        name="PostgreSQL",
        purpose="Primary DB",
        state=InfraState.C,
        bucket=None,
        local_strategy="Local DB (5433)",
        check_fn=_check_postgres,
    ),
    "Redis": InfraItem(
        name="Redis",
        purpose="Queue/Cache",
        state=InfraState.B,
        bucket=None,
        local_strategy="Local Redis (6379)",
        check_fn=_check_redis,
    ),
    "Clerk": InfraItem(
        name="Clerk",
        purpose="RBAC/Auth",
        state=InfraState.B,  # Promoted A→B via stub (PIN-272)
        bucket=None,  # No longer in Bucket B1
        local_strategy="Stub (app/auth/stub.py)",
        check_fn=_check_stub_auth,  # Use stub check, not backend check
    ),
    "Prometheus": InfraItem(
        name="Prometheus",
        purpose="Metrics",
        state=InfraState.A,
        bucket=InfraBucket.B2,
        local_strategy="None",
        check_fn=_check_prometheus,
    ),
    "Alertmanager": InfraItem(
        name="Alertmanager",
        purpose="Alerts",
        state=InfraState.A,
        bucket=InfraBucket.B2,
        local_strategy="None",
        check_fn=None,
    ),
    "Grafana": InfraItem(
        name="Grafana",
        purpose="Dashboards",
        state=InfraState.A,
        bucket=InfraBucket.B2,
        local_strategy="None",
        check_fn=None,
    ),
    "AgentsSchema": InfraItem(
        name="AgentsSchema",
        purpose="M12 internal",
        state=InfraState.A,
        bucket=InfraBucket.B2,
        local_strategy="None",
        check_fn=None,
    ),
    "LLMAPIs": InfraItem(
        name="LLMAPIs",
        purpose="External inference",
        state=InfraState.A,
        bucket=InfraBucket.B2,
        local_strategy="Mocked",
        check_fn=None,
    ),
    "Neon": InfraItem(
        name="Neon",
        purpose="Cloud Postgres",
        state=InfraState.A,
        bucket=InfraBucket.B2,
        local_strategy="Local fallback",
        check_fn=None,
    ),
    "Backend": InfraItem(
        name="Backend",
        purpose="Running API server",
        state=InfraState.B,
        bucket=None,
        local_strategy="Docker compose",
        check_fn=_check_auth_backend,  # Reuse auth check
    ),
}


def get_infra(name: str) -> InfraItem:
    """Get infrastructure item by name.

    Raises:
        ValueError: If infra name is not in registry
    """
    if name not in INFRA_REGISTRY:
        raise ValueError(
            f"Infrastructure '{name}' not found in INFRA_REGISTRY. "
            f"Available: {list(INFRA_REGISTRY.keys())}. "
            f"Add to docs/infra/INFRA_REGISTRY.md first."
        )
    return INFRA_REGISTRY[name]


def check_infra_available(name: str) -> bool:
    """Check if infrastructure is available.

    For State A: Always returns False (conceptual only)
    For State B/C: Runs check function if available
    """
    infra = get_infra(name)

    if infra.state == InfraState.A:
        return False

    if infra.check_fn is not None:
        return infra.check_fn()

    # Default: assume available for State B/C without check_fn
    return True


def get_infra_skip_reason(name: str) -> str:
    """Get skip reason for unavailable infrastructure."""
    infra = get_infra(name)

    if infra.state == InfraState.A:
        bucket_str = f" (Bucket {infra.bucket.name})" if infra.bucket else ""
        return (
            f"Infrastructure '{name}' is State A (Conceptual){bucket_str}. "
            f"Local strategy: {infra.local_strategy}. "
            f"See docs/infra/INFRA_REGISTRY.md"
        )

    return f"Infrastructure '{name}' is not available locally."


def requires_infra(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to mark tests that require specific infrastructure.

    Usage:
        @requires_infra("Clerk")
        def test_rbac_enforcement():
            ...

    Behavior:
        - State A: Always skips with Bucket B reason
        - State B/C: Runs check function, skips if unavailable
        - State C required but unavailable: Fails (not skips)

    Args:
        name: Infrastructure name from INFRA_REGISTRY

    Returns:
        Decorator function
    """
    infra = get_infra(name)  # Validates name exists

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not check_infra_available(name):
                if infra.state == InfraState.C:
                    # State C is required — fail, don't skip
                    pytest.fail(
                        f"Required infrastructure '{name}' (State C) is unavailable. "
                        f"This is a CI/environment failure, not a test issue."
                    )
                else:
                    pytest.skip(get_infra_skip_reason(name))

            return fn(*args, **kwargs)

        return wrapper

    return decorator


# ============================================================================
# PYTEST MARKERS
# ============================================================================
# These can be used as pytest markers for filtering

requires_postgres = requires_infra("PostgreSQL")
requires_redis = requires_infra("Redis")
requires_auth = requires_infra("Clerk")
requires_prometheus = requires_infra("Prometheus")
requires_agents_schema = requires_infra("AgentsSchema")


# ============================================================================
# REGISTRY VALIDATION
# ============================================================================


def validate_registry() -> list[str]:
    """Validate that INFRA_REGISTRY matches INFRA_REGISTRY.md.

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    for name, infra in INFRA_REGISTRY.items():
        # State A must have bucket
        if infra.state == InfraState.A and infra.bucket is None:
            errors.append(f"{name}: State A requires bucket classification (B1 or B2)")

        # State C must not have bucket
        if infra.state == InfraState.C and infra.bucket is not None:
            errors.append(f"{name}: State C should not have bucket classification")

        # State B/C should have check function
        if infra.state in (InfraState.B, InfraState.C) and infra.check_fn is None:
            # Warning, not error — some infra is assumed available
            pass

    return errors


if __name__ == "__main__":
    # Self-test
    print("INFRA_REGISTRY validation:")
    errors = validate_registry()
    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
    else:
        print("  All entries valid")

    print("\nRegistry contents:")
    for name, infra in INFRA_REGISTRY.items():
        bucket_str = f" [{infra.bucket.name}]" if infra.bucket else ""
        print(f"  {name}: State {infra.state.name}{bucket_str}")
