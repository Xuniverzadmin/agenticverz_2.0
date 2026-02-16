# Layer: TEST
# AUDIENCE: INTERNAL
# Role: Business invariants runtime test suite — positive/negative cases
# Reference: BA-05 Business Assurance Guardrails
# artifact_class: TEST

"""
Business Invariants Runtime Tests (BA-05)

Tests the business invariant registry, structural checks, and exception model
defined in app.hoc.cus.hoc_spine.authority.business_invariants.

Coverage:
  - Registry population and field completeness
  - Severity value validation
  - check_invariant return contract (tuple[bool, str])
  - check_invariant unknown-id error handling
  - check_all_for_operation return contract
  - Positive/negative domain-specific invariant checks
  - BusinessInvariantViolation exception raisability
"""

import pytest

from app.hoc.cus.hoc_spine.authority.business_invariants import (
    BUSINESS_INVARIANTS,
    BusinessInvariantViolation,
    Invariant,
    check_all_for_operation,
    check_invariant,
)


# =============================================================================
# REGISTRY STRUCTURE TESTS
# =============================================================================


def test_invariant_registry_not_empty():
    """BUSINESS_INVARIANTS has >= 10 entries."""
    assert len(BUSINESS_INVARIANTS) >= 10, (
        f"Expected at least 10 invariants, got {len(BUSINESS_INVARIANTS)}"
    )


def test_all_invariants_have_required_fields():
    """Each Invariant has invariant_id, operation, severity,
    condition_description, and remediation."""
    required_fields = [
        "invariant_id",
        "operation",
        "severity",
        "condition_description",
        "remediation",
    ]
    for inv_id, invariant in BUSINESS_INVARIANTS.items():
        assert isinstance(invariant, Invariant), (
            f"{inv_id} is not an Invariant instance"
        )
        for field in required_fields:
            value = getattr(invariant, field, None)
            assert value is not None and value != "", (
                f"Invariant {inv_id} missing or empty field: {field}"
            )


def test_severity_values_valid():
    """Severity is one of CRITICAL, HIGH, MEDIUM."""
    valid_severities = {"CRITICAL", "HIGH", "MEDIUM"}
    for inv_id, invariant in BUSINESS_INVARIANTS.items():
        assert invariant.severity in valid_severities, (
            f"Invariant {inv_id} has invalid severity '{invariant.severity}'; "
            f"expected one of {valid_severities}"
        )


# =============================================================================
# check_invariant RETURN CONTRACT
# =============================================================================


def test_check_invariant_returns_tuple():
    """check_invariant returns (bool, str) for a known invariant."""
    # Use the first registered invariant
    first_id = next(iter(BUSINESS_INVARIANTS))
    result = check_invariant(first_id, {})
    assert isinstance(result, tuple), (
        f"Expected tuple, got {type(result).__name__}"
    )
    assert len(result) == 2, f"Expected 2-element tuple, got {len(result)}"
    passed, message = result
    assert isinstance(passed, bool), (
        f"First element should be bool, got {type(passed).__name__}"
    )
    assert isinstance(message, str), (
        f"Second element should be str, got {type(message).__name__}"
    )


def test_check_invariant_unknown_id_returns_false():
    """Unknown invariant_id raises ValueError (fail-closed)."""
    with pytest.raises(ValueError, match="Unknown invariant_id"):
        check_invariant("NONEXISTENT-999", {})


# =============================================================================
# check_all_for_operation RETURN CONTRACT
# =============================================================================


def test_check_all_for_operation_returns_list():
    """check_all_for_operation returns a list of tuples."""
    # Pick a real operation from the registry
    first_invariant = next(iter(BUSINESS_INVARIANTS.values()))
    operation = first_invariant.operation
    results = check_all_for_operation(operation, {})
    assert isinstance(results, list), (
        f"Expected list, got {type(results).__name__}"
    )
    for item in results:
        assert isinstance(item, tuple), (
            f"Each result should be a tuple, got {type(item).__name__}"
        )
        assert len(item) == 3, (
            f"Each result tuple should have 3 elements "
            f"(invariant_id, passed, message), got {len(item)}"
        )


def test_check_all_for_unknown_operation_returns_empty():
    """Unknown operation returns empty list (no invariants guard it)."""
    results = check_all_for_operation("nonexistent.operation.xyz", {})
    assert isinstance(results, list)
    assert len(results) == 0, (
        f"Expected empty list for unknown operation, got {len(results)} results"
    )


# =============================================================================
# DOMAIN-SPECIFIC POSITIVE / NEGATIVE TESTS
# =============================================================================


def test_tenant_create_invariant_passes_with_valid_context():
    """Context with org_id (via tenant_id) passes BI-TENANT-001 (project.create)."""
    # BI-TENANT-001 guards "project.create" — requires tenant_id
    passed, message = check_invariant("BI-TENANT-001", {
        "tenant_id": "tenant-abc-123",
        "tenant_status": "ACTIVE",
    })
    assert passed is True, f"Expected pass, got fail: {message}"
    assert message == "ok"


def test_tenant_create_invariant_fails_without_org_id():
    """Context without tenant_id (org_id proxy) fails BI-TENANT-001."""
    passed, message = check_invariant("BI-TENANT-001", {})
    assert passed is False, "Expected failure when tenant_id is missing"
    assert "tenant_id" in message.lower(), (
        f"Failure message should mention tenant_id, got: {message}"
    )


def test_threshold_invariant_fails_with_negative():
    """Negative threshold fails BI-CTRL-001 (control.set_threshold)."""
    passed, message = check_invariant("BI-CTRL-001", {
        "threshold": -5.0,
    })
    assert passed is False, "Expected failure for negative threshold"
    assert "negative" in message.lower() or "non-negative" in message.lower() or "-5" in message, (
        f"Failure message should reference the negative value, got: {message}"
    )


def test_threshold_invariant_passes_with_positive():
    """Positive threshold passes BI-CTRL-001."""
    passed, message = check_invariant("BI-CTRL-001", {
        "threshold": 42.0,
    })
    assert passed is True, f"Expected pass for positive threshold, got fail: {message}"
    assert message == "ok"


def test_incident_resolve_fails_when_already_resolved():
    """Context with current_status=RESOLVED and target=ACTIVE fails BI-INCIDENT-001."""
    passed, message = check_invariant("BI-INCIDENT-001", {
        "current_status": "RESOLVED",
        "target_status": "ACTIVE",
    })
    assert passed is False, "Expected failure for RESOLVED->ACTIVE transition"
    assert "resolved" in message.lower() or "reopen" in message.lower(), (
        f"Failure message should mention RESOLVED or reopen, got: {message}"
    )


# =============================================================================
# EXCEPTION MODEL
# =============================================================================


def test_business_invariant_violation_exception():
    """BusinessInvariantViolation is raiseable with proper fields."""
    exc = BusinessInvariantViolation(
        invariant_id="BI-TEST-001",
        operation="test.operation",
        severity="CRITICAL",
        message="test invariant violated",
    )
    assert exc.invariant_id == "BI-TEST-001"
    assert exc.operation == "test.operation"
    assert exc.severity == "CRITICAL"
    assert exc.message == "test invariant violated"
    assert "BI-TEST-001" in str(exc)
    assert "CRITICAL" in str(exc)
    assert "test.operation" in str(exc)

    # Verify it is raiseable
    with pytest.raises(BusinessInvariantViolation):
        raise exc
