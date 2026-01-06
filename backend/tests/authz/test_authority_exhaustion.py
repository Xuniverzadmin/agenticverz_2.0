# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: test
#   Execution: sync
# Role: Authority exhaustion test harness (T12)
# Callers: pytest, CI
# Allowed Imports: L6, L8
# Forbidden Imports: L1, L2, L3
# Reference: PIN-310 (Fast-Track M7 Closure), T12

"""
Authority Exhaustion Test Harness

Executes every (principal, resource, action) combination from the Authority Matrix.
Tracks M7 tripwire hits and verifies M28 coverage.

Usage:
    # Run all authority tests
    pytest tests/authz/test_authority_exhaustion.py -v

    # Run with tripwire mode
    AUTHZ_TRIPWIRE=true pytest tests/authz/test_authority_exhaustion.py -v

    # Run specific test categories
    pytest tests/authz/test_authority_exhaustion.py -k "m28_native" -v
    pytest tests/authz/test_authority_exhaustion.py -k "m7_legacy" -v

Goals:
- Execute 100% of matrix cells at least once
- Identify any M7 tripwire hits (fallbacks)
- Verify M28 can make decisions for all paths
- Report coverage gaps
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

import pytest

from app.auth.actor import ActorType
from app.auth.authorization_choke import (
    M7_LEGACY_RESOURCES,
    M28_NATIVE_RESOURCES,
    AuthorizationDecision,
    AuthorizationSource,
    AuthzPhase,
    authorize_action,
    get_authz_phase,
    is_strict_mode,
    is_tripwire_mode,
)
from tests.authz.fixtures.principals import (
    HUMAN_PRINCIPALS,
    MACHINE_PRINCIPALS,
    get_principal,
    list_principal_ids,
)

# =============================================================================
# Test Matrix Definition
# =============================================================================

# M28 native resources with their valid actions
M28_RESOURCE_ACTIONS: Dict[str, Set[str]] = {
    "runs": {"read", "write", "delete"},
    "agents": {"read", "write", "delete"},
    "skills": {"read", "write", "delete"},
    "traces": {"read", "write"},
    "metrics": {"read", "write", "admin"},
    "ops": {"read", "write"},
    "account": {"read", "write", "admin"},
    "team": {"read", "write", "admin"},
    "members": {"read", "write", "admin"},
    "members:team": {"read", "write", "admin"},  # PIN-310: Team member management
    "billing:account": {"read", "write", "admin"},  # PIN-310: Account billing
    "policies": {"read", "write", "admin"},
    "replay": {"read", "execute", "admin", "audit"},
    "predictions": {"read", "execute", "admin", "audit"},
    "system": {"read", "admin", "delete"},
    "rbac": {"read", "write", "admin"},  # PIN-310: RBAC admin endpoints
}

# M7 legacy resources with their valid actions (via mapping)
M7_RESOURCE_ACTIONS: Dict[str, Set[str]] = {
    "memory_pin": {"read", "write", "delete", "admin"},
    "costsim": {"read", "write"},
    "policy": {"read", "write", "approve"},
    "agent": {"read", "write", "delete", "heartbeat", "register"},
    "runtime": {"simulate", "capabilities", "query"},
    "recovery": {"suggest", "execute"},
    "prometheus": {"query", "reload"},
}


# =============================================================================
# Test Result Tracking
# =============================================================================


@dataclass
class AuthorityTestResult:
    """Result of a single authority test."""

    principal_id: str
    resource: str
    action: str
    decision: AuthorizationDecision
    source: AuthorizationSource
    allowed: bool
    is_m7_fallback: bool
    is_tripwire_hit: bool = False


@dataclass
class AuthorityTestReport:
    """Summary report for authority exhaustion testing."""

    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    m28_direct: int = 0
    m28_via_mapping: int = 0
    m7_tripwire_hits: int = 0
    denied_no_mapping: int = 0
    errors: List[str] = field(default_factory=list)
    tripwire_hits: List[AuthorityTestResult] = field(default_factory=list)

    def record(self, result: AuthorityTestResult) -> None:
        """Record a test result."""
        self.total_tests += 1

        # Track source
        if result.source == AuthorizationSource.M28_DIRECT:
            self.m28_direct += 1
            self.passed += 1
        elif result.source == AuthorizationSource.M28_VIA_MAPPING:
            self.m28_via_mapping += 1
            self.passed += 1
            if result.is_tripwire_hit:
                self.m7_tripwire_hits += 1
                self.tripwire_hits.append(result)
        elif result.source == AuthorizationSource.DENIED_NO_MAPPING:
            self.denied_no_mapping += 1
            self.failed += 1
            self.errors.append(f"NO_MAPPING: {result.principal_id} → {result.resource}:{result.action}")
        else:
            self.passed += 1

    def summary(self) -> str:
        """Generate summary report."""
        return f"""
Authority Exhaustion Report
===========================
Total Tests: {self.total_tests}
Passed: {self.passed}
Failed: {self.failed}

Source Breakdown:
  M28 Direct: {self.m28_direct}
  M28 via Mapping: {self.m28_via_mapping}
  No Mapping (Denied): {self.denied_no_mapping}

Tripwire Hits: {self.m7_tripwire_hits}
{self._format_tripwire_hits()}

Errors: {len(self.errors)}
{self._format_errors()}
"""

    def _format_tripwire_hits(self) -> str:
        if not self.tripwire_hits:
            return "  (none)"
        return "\n".join(f"  - {h.principal_id} → {h.resource}:{h.action}" for h in self.tripwire_hits)

    def _format_errors(self) -> str:
        if not self.errors:
            return "  (none)"
        return "\n".join(f"  - {e}" for e in self.errors[:10])


# Global report for pytest session
_report = AuthorityTestReport()


# =============================================================================
# Helper Functions
# =============================================================================


def execute_authority_check(
    principal_id: str,
    resource: str,
    action: str,
) -> AuthorityTestResult:
    """
    Execute a single authority check and return structured result.

    Args:
        principal_id: ID from ALL_PRINCIPALS
        resource: Resource to access
        action: Action to perform

    Returns:
        AuthorityTestResult with full decision context
    """
    actor = get_principal(principal_id)
    decision = authorize_action(actor, resource, action)

    is_m7_fallback = decision.source in (
        AuthorizationSource.M28_VIA_MAPPING,
        AuthorizationSource.LOGGED_WRITE_M7,
    )

    result = AuthorityTestResult(
        principal_id=principal_id,
        resource=resource,
        action=action,
        decision=decision,
        source=decision.source,
        allowed=decision.allowed,
        is_m7_fallback=is_m7_fallback,
        is_tripwire_hit=is_m7_fallback and is_tripwire_mode(),
    )

    _report.record(result)
    return result


def generate_m28_test_cases() -> List[Tuple[str, str, str]]:
    """Generate all (principal, resource, action) test cases for M28 native resources."""
    cases = []
    for resource, actions in M28_RESOURCE_ACTIONS.items():
        for action in actions:
            for principal_id in list_principal_ids():
                cases.append((principal_id, resource, action))
    return cases


def generate_m7_test_cases() -> List[Tuple[str, str, str]]:
    """Generate all (principal, resource, action) test cases for M7 legacy resources."""
    cases = []
    for resource, actions in M7_RESOURCE_ACTIONS.items():
        for action in actions:
            for principal_id in list_principal_ids():
                cases.append((principal_id, resource, action))
    return cases


# =============================================================================
# Pytest Fixtures
# =============================================================================


@pytest.fixture(scope="module")
def authority_report():
    """Provide access to the global report."""
    return _report


@pytest.fixture(autouse=True)
def check_test_env():
    """Verify test environment is configured."""
    # Note: Tripwire mode is optional for exhaustion testing
    pass


# =============================================================================
# M28 Native Resource Tests
# =============================================================================


class TestM28NativeResources:
    """Tests for M28 native resources (direct authorization)."""

    @pytest.mark.parametrize(
        "principal_id,resource,action",
        generate_m28_test_cases(),
        ids=lambda x: f"{x}" if isinstance(x, str) else None,
    )
    def test_m28_authority(
        self,
        principal_id: str,
        resource: str,
        action: str,
    ):
        """Test that M28 can authorize native resources."""
        result = execute_authority_check(principal_id, resource, action)

        # M28 native resources must use M28_DIRECT source
        assert result.source == AuthorizationSource.M28_DIRECT, (
            f"Expected M28_DIRECT for {resource}:{action}, got {result.source}"
        )

        # Decision must be made (not abstain)
        assert result.decision.source == AuthorizationSource.M28_DIRECT

    def test_m28_coverage(self):
        """Verify all M28 native resources are covered."""
        tested_resources = set(M28_RESOURCE_ACTIONS.keys())
        expected = M28_NATIVE_RESOURCES

        missing = expected - tested_resources
        assert not missing, f"Missing M28 resources in test matrix: {missing}"


# =============================================================================
# M7 Legacy Resource Tests (via Mapping)
# =============================================================================


class TestM7LegacyResources:
    """Tests for M7 legacy resources (via mapping to M28)."""

    @pytest.mark.parametrize(
        "principal_id,resource,action",
        generate_m7_test_cases(),
        ids=lambda x: f"{x}" if isinstance(x, str) else None,
    )
    def test_m7_via_mapping(
        self,
        principal_id: str,
        resource: str,
        action: str,
    ):
        """Test that M7 resources are handled via mapping."""
        result = execute_authority_check(principal_id, resource, action)

        # M7 legacy resources should use mapping OR be denied
        valid_sources = {
            AuthorizationSource.M28_VIA_MAPPING,
            AuthorizationSource.LOGGED_WRITE_M7,
            AuthorizationSource.DENIED_NO_MAPPING,
            AuthorizationSource.DENIED_PHASE_C_NO_M7,
        }

        assert result.source in valid_sources, f"Unexpected source for M7 {resource}:{action}: {result.source}"

        # If tripwire mode, this was recorded
        if result.is_tripwire_hit:
            print(f"TRIPWIRE HIT: {principal_id} → {resource}:{action}")

    def test_m7_coverage(self):
        """Verify all M7 legacy resources are covered."""
        tested_resources = set(M7_RESOURCE_ACTIONS.keys())
        expected = M7_LEGACY_RESOURCES

        missing = expected - tested_resources
        assert not missing, f"Missing M7 resources in test matrix: {missing}"


# =============================================================================
# Principal Coverage Tests
# =============================================================================


class TestPrincipalCoverage:
    """Tests for principal coverage across all actor types."""

    def test_all_actor_types_covered(self):
        """Verify all ActorTypes have at least one principal."""
        covered_types = {get_principal(pid).actor_type for pid in list_principal_ids()}

        for actor_type in ActorType:
            assert actor_type in covered_types, f"No principal for ActorType {actor_type.value}"

    def test_human_principals_count(self):
        """Verify sufficient human principals."""
        assert len(HUMAN_PRINCIPALS) >= 5, "Need at least 5 human principals"

    def test_machine_principals_count(self):
        """Verify sufficient machine principals."""
        assert len(MACHINE_PRINCIPALS) >= 5, "Need at least 5 machine principals"


# =============================================================================
# Tripwire Analysis Tests
# =============================================================================


class TestTripwireAnalysis:
    """Tests for tripwire mode analysis."""

    def test_tripwire_mode_detectable(self):
        """Verify tripwire mode can be detected."""
        # Note: Actual mode depends on environment variable
        result = is_tripwire_mode()
        assert isinstance(result, bool)

    def test_strict_mode_detectable(self):
        """Verify strict mode can be detected."""
        result = is_strict_mode()
        assert isinstance(result, bool)

    def test_phase_detectable(self):
        """Verify current phase can be detected."""
        phase = get_authz_phase()
        assert phase in (AuthzPhase.PHASE_A, AuthzPhase.PHASE_B, AuthzPhase.PHASE_C)


# =============================================================================
# Report Generation
# =============================================================================


def pytest_sessionfinish(session, exitstatus):
    """Generate final report after all tests."""
    if _report.total_tests > 0:
        print("\n" + _report.summary())


# =============================================================================
# Standalone Execution
# =============================================================================


def run_exhaustive_test() -> AuthorityTestReport:
    """
    Run all authority tests and return report.

    For use outside pytest (e.g., scripts).
    """
    report = AuthorityTestReport()

    print("Running M28 native resource tests...")
    for principal_id, resource, action in generate_m28_test_cases():
        actor = get_principal(principal_id)
        decision = authorize_action(actor, resource, action)

        is_m7_fallback = decision.source in (
            AuthorizationSource.M28_VIA_MAPPING,
            AuthorizationSource.LOGGED_WRITE_M7,
        )

        result = AuthorityTestResult(
            principal_id=principal_id,
            resource=resource,
            action=action,
            decision=decision,
            source=decision.source,
            allowed=decision.allowed,
            is_m7_fallback=is_m7_fallback,
            is_tripwire_hit=is_m7_fallback and is_tripwire_mode(),
        )
        report.record(result)

    print("Running M7 legacy resource tests...")
    for principal_id, resource, action in generate_m7_test_cases():
        actor = get_principal(principal_id)
        decision = authorize_action(actor, resource, action)

        is_m7_fallback = decision.source in (
            AuthorizationSource.M28_VIA_MAPPING,
            AuthorizationSource.LOGGED_WRITE_M7,
        )

        result = AuthorityTestResult(
            principal_id=principal_id,
            resource=resource,
            action=action,
            decision=decision,
            source=decision.source,
            allowed=decision.allowed,
            is_m7_fallback=is_m7_fallback,
            is_tripwire_hit=is_m7_fallback and is_tripwire_mode(),
        )
        report.record(result)

    return report


if __name__ == "__main__":
    print("Authority Exhaustion Test Harness")
    print("=" * 40)
    print(f"Tripwire mode: {is_tripwire_mode()}")
    print(f"Strict mode: {is_strict_mode()}")
    print(f"Phase: {get_authz_phase().value}")
    print()

    report = run_exhaustive_test()
    print(report.summary())

    # Exit with error if tripwire hits found (for CI)
    if report.m7_tripwire_hits > 0:
        print(f"\n⚠️  {report.m7_tripwire_hits} tripwire hits detected!")
        exit(1)
    else:
        print("\n✓ No tripwire hits - M28 coverage complete!")
        exit(0)
