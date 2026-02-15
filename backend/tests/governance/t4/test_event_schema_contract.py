# Layer: L8 — Test
# AUDIENCE: INTERNAL
# Role: Tests for event schema contract — valid/invalid payload validation
# Product: system-wide
# Temporal:
#   Trigger: CI / manual
#   Execution: sync
# Callers: pytest, CI
# Allowed Imports: stdlib, event_schema_contract
# Forbidden Imports: FastAPI, DB, ORM
# Reference: GREEN_CLOSURE_PLAN_UC001_UC002 Phase 1
# artifact_class: TEST

"""
Tests for event_schema_contract — proves valid payloads pass and invalid
payloads fail with structured rejection (EventSchemaViolation).

Acceptance criteria (Phase 1):
  - Missing required field causes structured rejection (no silent pass-through).
  - Tests prove valid payload passes and invalid payload fails.
"""

import uuid

from app.hoc.cus.hoc_spine.authority.event_schema_contract import (
    CURRENT_SCHEMA_VERSION,
    REQUIRED_EVENT_FIELDS,
    VALID_ACTOR_TYPES,
    EventSchemaViolation,
    is_valid_event_payload,
    validate_event_payload,
)


def _make_valid_payload(**overrides):
    """Construct a valid event payload, optionally overriding fields."""
    base = {
        "event_id": str(uuid.uuid4()),
        "event_type": "test.event.created",
        "tenant_id": "tenant-001",
        "project_id": "project-001",
        "actor_type": "system",
        "actor_id": "test-harness",
        "decision_owner": "test_domain",
        "sequence_no": 1,
        "schema_version": CURRENT_SCHEMA_VERSION,
    }
    base.update(overrides)
    return base


# =============================================================================
# POSITIVE TESTS
# =============================================================================


def test_valid_payload_passes():
    """Valid payload must pass without exception."""
    payload = _make_valid_payload()
    validate_event_payload(payload)  # Should not raise


def test_all_valid_actor_types_accepted():
    """All values in VALID_ACTOR_TYPES pass validation."""
    for actor in VALID_ACTOR_TYPES:
        payload = _make_valid_payload(actor_type=actor)
        validate_event_payload(payload)  # Should not raise


def test_is_valid_event_payload_true():
    """Non-throwing variant returns (True, []) for valid payload."""
    payload = _make_valid_payload()
    valid, errors = is_valid_event_payload(payload)
    assert valid is True
    assert errors == []


def test_zero_sequence_no_accepted():
    """sequence_no = 0 is valid (boundary)."""
    payload = _make_valid_payload(sequence_no=0)
    validate_event_payload(payload)  # Should not raise


# =============================================================================
# NEGATIVE TESTS — MISSING FIELDS
# =============================================================================


def test_missing_single_field_raises():
    """Missing one required field causes EventSchemaViolation."""
    for field_name in REQUIRED_EVENT_FIELDS:
        payload = _make_valid_payload()
        del payload[field_name]
        try:
            validate_event_payload(payload)
            assert False, f"Expected EventSchemaViolation for missing '{field_name}'"
        except EventSchemaViolation as e:
            assert field_name in e.missing


def test_missing_multiple_fields_raises():
    """Missing multiple fields lists all missing."""
    payload = _make_valid_payload()
    del payload["event_id"]
    del payload["tenant_id"]
    del payload["sequence_no"]
    try:
        validate_event_payload(payload)
        assert False, "Expected EventSchemaViolation"
    except EventSchemaViolation as e:
        assert "event_id" in e.missing
        assert "tenant_id" in e.missing
        assert "sequence_no" in e.missing


def test_none_field_value_treated_as_missing():
    """Field present but None is treated as missing."""
    payload = _make_valid_payload(event_id=None)
    try:
        validate_event_payload(payload)
        assert False, "Expected EventSchemaViolation"
    except EventSchemaViolation as e:
        assert "event_id" in e.missing


def test_is_valid_event_payload_false_missing():
    """Non-throwing variant returns (False, errors) for missing field."""
    payload = _make_valid_payload()
    del payload["event_id"]
    valid, errors = is_valid_event_payload(payload)
    assert valid is False
    assert len(errors) >= 1
    assert any("event_id" in e for e in errors)


# =============================================================================
# NEGATIVE TESTS — WRONG TYPES
# =============================================================================


def test_wrong_type_string_for_int_raises():
    """String for sequence_no (expected int) causes violation."""
    payload = _make_valid_payload(sequence_no="not_an_int")
    try:
        validate_event_payload(payload)
        assert False, "Expected EventSchemaViolation"
    except EventSchemaViolation as e:
        assert len(e.invalid) >= 1
        assert any("sequence_no" in item for item in e.invalid)


def test_wrong_type_int_for_string_raises():
    """Int for event_type (expected str) causes violation."""
    payload = _make_valid_payload(event_type=42)
    try:
        validate_event_payload(payload)
        assert False, "Expected EventSchemaViolation"
    except EventSchemaViolation as e:
        assert len(e.invalid) >= 1
        assert any("event_type" in item for item in e.invalid)


# =============================================================================
# NEGATIVE TESTS — INVALID VALUES
# =============================================================================


def test_invalid_actor_type_raises():
    """actor_type not in VALID_ACTOR_TYPES causes violation."""
    payload = _make_valid_payload(actor_type="hacker")
    try:
        validate_event_payload(payload)
        assert False, "Expected EventSchemaViolation"
    except EventSchemaViolation as e:
        assert any("actor_type" in item for item in e.invalid)


def test_negative_sequence_no_raises():
    """sequence_no < 0 causes violation."""
    payload = _make_valid_payload(sequence_no=-1)
    try:
        validate_event_payload(payload)
        assert False, "Expected EventSchemaViolation"
    except EventSchemaViolation as e:
        assert any("sequence_no" in item for item in e.invalid)
