# capability_id: CAP-011
# Layer: L4 — hoc_spine Authority
# AUDIENCE: SHARED
# Role: Event schema contract — minimum required fields for authoritative events
# Product: system-wide
# Temporal:
#   Trigger: import
#   Execution: sync
# Callers: L4 handlers, L5 engines (event emitters)
# Allowed Imports: stdlib only
# Forbidden Imports: FastAPI, Starlette, DB, ORM
# Reference: GREEN_CLOSURE_PLAN_UC001_UC002 Phase 1
# artifact_class: CODE

"""
Event Schema Contract (UC-001 / UC-002)

Defines and enforces the minimum required fields for authoritative events
emitted by the HOC system. Any event written to the event store or published
to an event bus MUST pass this contract.

REQUIRED FIELDS:
    event_id        — UUID, globally unique per event
    event_type      — string, dot-separated domain event name
    tenant_id       — string, owning tenant
    project_id      — string, owning project (or "__system__" for system events)
    actor_type      — string, who triggered: "user", "system", "sdk", "founder"
    actor_id        — string, identifier of the actor
    decision_owner  — string, domain that owns the decision
    sequence_no     — int, monotonic within tenant+project scope
    schema_version  — string, semver of the event schema

This module contains NO framework imports — it is pure contract data + validation.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("nova.hoc.event_schema_contract")

# =============================================================================
# CONTRACT DEFINITION
# =============================================================================

REQUIRED_EVENT_FIELDS: dict[str, type] = {
    "event_id": str,
    "event_type": str,
    "tenant_id": str,
    "project_id": str,
    "actor_type": str,
    "actor_id": str,
    "decision_owner": str,
    "sequence_no": int,
    "schema_version": str,
}

VALID_ACTOR_TYPES = frozenset({"user", "system", "sdk", "founder"})

CURRENT_SCHEMA_VERSION = "1.0.0"


class EventSchemaViolation(Exception):
    """Raised when an event payload violates the minimum schema contract."""

    def __init__(self, missing: list[str], invalid: list[str]):
        self.missing = missing
        self.invalid = invalid
        parts = []
        if missing:
            parts.append(f"missing fields: {missing}")
        if invalid:
            parts.append(f"invalid fields: {invalid}")
        super().__init__(f"Event schema violation: {'; '.join(parts)}")


def validate_event_payload(payload: dict[str, Any]) -> None:
    """
    Validate an event payload against the minimum schema contract.

    Raises EventSchemaViolation if any required field is missing or has
    the wrong type. This is fail-closed: missing fields cause rejection,
    never silent pass-through.
    """
    missing: list[str] = []
    invalid: list[str] = []

    for field_name, field_type in REQUIRED_EVENT_FIELDS.items():
        value = payload.get(field_name)
        if value is None:
            missing.append(field_name)
        elif not isinstance(value, field_type):
            invalid.append(f"{field_name} (expected {field_type.__name__}, got {type(value).__name__})")

    # Validate actor_type value if present
    actor_type = payload.get("actor_type")
    if actor_type is not None and actor_type not in VALID_ACTOR_TYPES:
        invalid.append(f"actor_type (got '{actor_type}', valid: {sorted(VALID_ACTOR_TYPES)})")

    # Validate sequence_no is non-negative if present
    seq = payload.get("sequence_no")
    if isinstance(seq, int) and seq < 0:
        invalid.append(f"sequence_no (must be >= 0, got {seq})")

    if missing or invalid:
        logger.warning(
            "event_schema_violation",
            extra={
                "missing": missing,
                "invalid": invalid,
                "event_type": payload.get("event_type", "<unknown>"),
                "tenant_id": payload.get("tenant_id", "<unknown>"),
            },
        )
        raise EventSchemaViolation(missing=missing, invalid=invalid)


def is_valid_event_payload(payload: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Non-throwing variant: returns (valid, errors).
    Use when you need to check without raising.
    """
    try:
        validate_event_payload(payload)
        return True, []
    except EventSchemaViolation as e:
        errors = []
        if e.missing:
            errors.extend(f"missing: {f}" for f in e.missing)
        if e.invalid:
            errors.extend(f"invalid: {f}" for f in e.invalid)
        return False, errors


__all__ = [
    "REQUIRED_EVENT_FIELDS",
    "VALID_ACTOR_TYPES",
    "CURRENT_SCHEMA_VERSION",
    "EventSchemaViolation",
    "validate_event_payload",
    "is_valid_event_payload",
]
