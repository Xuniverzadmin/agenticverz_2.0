# Layer: L8 — Test
# AUDIENCE: INTERNAL
# Role: Tests for API key surface policy lock (read/write split)
# Product: system-wide
# Temporal:
#   Trigger: CI / manual
#   Execution: sync
# Callers: pytest, CI
# Allowed Imports: stdlib, onboarding_policy
# Forbidden Imports: FastAPI, DB, ORM
# Reference: GREEN_CLOSURE_PLAN_UC001_UC002 Phase 3
# artifact_class: TEST

"""
API Key Surface Policy Lock Tests (UC-002)

Proves:
1. /api-keys (read) and /tenant/api-keys (write) both resolve to IDENTITY_VERIFIED.
2. Read-only router does NOT trigger onboarding advancement.
3. Write router POST triggers onboarding advancement.
4. Policy split is intentional and route/gate drift causes test failure.
"""

from pathlib import Path

from app.hoc.cus.hoc_spine.authority.onboarding_policy import (
    ENDPOINT_STATE_REQUIREMENTS,
    get_required_state,
)
from app.hoc.cus.account.L5_schemas.onboarding_state import OnboardingState


BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent.parent


# =============================================================================
# GATE RESOLUTION TESTS
# =============================================================================


def test_api_keys_read_resolves_to_identity_verified():
    """/api-keys (read) requires IDENTITY_VERIFIED, not COMPLETE."""
    state = get_required_state("/api-keys")
    assert state == OnboardingState.IDENTITY_VERIFIED


def test_tenant_api_keys_write_resolves_to_identity_verified():
    """/tenant/api-keys (write) requires IDENTITY_VERIFIED, not COMPLETE."""
    state = get_required_state("/tenant/api-keys")
    assert state == OnboardingState.IDENTITY_VERIFIED


def test_tenant_api_keys_subpath_resolves_to_identity_verified():
    """/tenant/api-keys/{key_id} resolves via pattern to IDENTITY_VERIFIED."""
    state = get_required_state("/tenant/api-keys/some-key-id")
    assert state == OnboardingState.IDENTITY_VERIFIED


def test_api_keys_detail_resolves_to_identity_verified():
    """/api-keys/{key_id} resolves via pattern to IDENTITY_VERIFIED."""
    state = get_required_state("/api-keys/some-key-id")
    assert state == OnboardingState.IDENTITY_VERIFIED


def test_both_api_key_paths_in_endpoint_state_requirements():
    """Both /api-keys and /tenant/api-keys must exist in exact-match table."""
    assert "/api-keys" in ENDPOINT_STATE_REQUIREMENTS
    assert "/tenant/api-keys" in ENDPOINT_STATE_REQUIREMENTS


def test_api_key_paths_resolve_to_same_state():
    """Read and write API key paths must resolve to the same onboarding state."""
    read_state = get_required_state("/api-keys")
    write_state = get_required_state("/tenant/api-keys")
    assert read_state == write_state, (
        f"Gate drift: /api-keys={read_state}, /tenant/api-keys={write_state}"
    )


# =============================================================================
# ONBOARDING ADVANCEMENT BOUNDARY TESTS (static analysis)
# =============================================================================


def test_read_router_does_not_trigger_onboarding_advance():
    """
    aos_api_key.py (read-only router) must NOT reference
    _maybe_advance_to_api_key_created or async_advance_onboarding.
    Read operations do not imply onboarding progression.
    """
    read_router = (
        BACKEND_ROOT / "app" / "hoc" / "api" / "cus" / "api_keys" / "aos_api_key.py"
    )
    assert read_router.exists()
    source = read_router.read_text()

    assert "_maybe_advance_to_api_key_created" not in source, (
        "Read-only router must NOT trigger onboarding advancement"
    )
    assert "async_advance_onboarding" not in source, (
        "Read-only router must NOT import async_advance_onboarding"
    )


def test_write_router_triggers_onboarding_advance():
    """
    api_key_writes.py (write router) must reference
    _maybe_advance_to_api_key_created in the POST handler.
    """
    write_router = (
        BACKEND_ROOT / "app" / "hoc" / "api" / "cus" / "api_keys" / "api_key_writes.py"
    )
    assert write_router.exists()
    source = write_router.read_text()

    assert "_maybe_advance_to_api_key_created" in source, (
        "Write router must call _maybe_advance_to_api_key_created on POST"
    )


# =============================================================================
# POLICY INVARIANT COMMENT TESTS (structural)
# =============================================================================


def test_policy_invariant_comment_in_read_router():
    """Read router must contain the API KEY SURFACE POLICY INVARIANT comment."""
    read_router = (
        BACKEND_ROOT / "app" / "hoc" / "api" / "cus" / "api_keys" / "aos_api_key.py"
    )
    source = read_router.read_text()
    assert "API KEY SURFACE POLICY INVARIANT" in source


def test_policy_invariant_comment_in_write_router():
    """Write router must contain the API KEY SURFACE POLICY INVARIANT comment."""
    write_router = (
        BACKEND_ROOT / "app" / "hoc" / "api" / "cus" / "api_keys" / "api_key_writes.py"
    )
    source = write_router.read_text()
    assert "API KEY SURFACE POLICY INVARIANT" in source


def test_policy_invariant_comment_in_onboarding_policy():
    """Onboarding policy must contain the API KEY SURFACE POLICY comment."""
    policy = (
        BACKEND_ROOT
        / "app"
        / "hoc"
        / "cus"
        / "hoc_spine"
        / "authority"
        / "onboarding_policy.py"
    )
    source = policy.read_text()
    assert "API KEY SURFACE POLICY" in source
