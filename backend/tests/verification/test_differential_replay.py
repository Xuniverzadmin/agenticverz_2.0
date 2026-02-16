# Layer: TEST
# AUDIENCE: INTERNAL
# Role: Tests for differential replay verifier — schema validation, fixture loading, runner exit codes
# artifact_class: TEST

"""
Differential Replay Tests (BA-16)

Validates:
    1. Golden no-drift fixture is valid against the replay contract schema
    2. Golden deny-case fixture is valid against the replay contract schema
    3. Replay runner returns exit 0 on golden fixtures
    4. replay_contract_schema.json is valid JSON
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
_FIXTURES_DIR = _BACKEND_ROOT / "tests" / "fixtures" / "replay"
_SCHEMA_PATH = _BACKEND_ROOT / "scripts" / "verification" / "replay_contract_schema.json"
_REPLAY_SCRIPT = _BACKEND_ROOT / "scripts" / "verification" / "uc_differential_replay.py"

_GOLDEN_NO_DRIFT = _FIXTURES_DIR / "golden_no_drift.json"
_GOLDEN_DENY_CASE = _FIXTURES_DIR / "golden_deny_case.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_OUTCOMES = {"ALLOW", "DENY", "DEFERRED"}
_VALID_ACTOR_TYPES = {"user", "system", "sdk", "founder"}
_VALID_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
_REQUIRED_TOP_LEVEL = {"replay_id", "operation", "input_context", "expected_decision"}


def _load_json(path: Path) -> dict:
    """Load and parse a JSON file."""
    with open(path, "r") as f:
        return json.load(f)


def _validate_fixture_schema(data: dict) -> list[str]:
    """
    Validate a replay fixture dict against the contract schema.
    Returns a list of error strings (empty = valid).
    """
    errors: list[str] = []

    # Top-level required fields
    for field in _REQUIRED_TOP_LEVEL:
        if field not in data:
            errors.append(f"missing required field: {field}")

    if errors:
        return errors

    # replay_id
    if not isinstance(data["replay_id"], str) or not data["replay_id"]:
        errors.append("replay_id must be a non-empty string")

    # operation
    if not isinstance(data["operation"], str) or not data["operation"]:
        errors.append("operation must be a non-empty string")

    # input_context
    ctx = data["input_context"]
    if not isinstance(ctx, dict):
        errors.append("input_context must be an object")
    else:
        if "tenant_id" not in ctx:
            errors.append("input_context.tenant_id is required")
        elif not isinstance(ctx["tenant_id"], str):
            errors.append("input_context.tenant_id must be a string")

        if "actor_type" in ctx and ctx["actor_type"] not in _VALID_ACTOR_TYPES:
            errors.append(
                f"input_context.actor_type invalid: '{ctx['actor_type']}'"
            )

    # expected_decision
    decision = data["expected_decision"]
    if not isinstance(decision, dict):
        errors.append("expected_decision must be an object")
    else:
        if "outcome" not in decision:
            errors.append("expected_decision.outcome is required")
        elif decision["outcome"] not in _VALID_OUTCOMES:
            errors.append(
                f"expected_decision.outcome invalid: '{decision['outcome']}'"
            )

        if "invariants_checked" in decision:
            if not isinstance(decision["invariants_checked"], list):
                errors.append("expected_decision.invariants_checked must be an array")
            else:
                for item in decision["invariants_checked"]:
                    if not isinstance(item, str):
                        errors.append(
                            f"expected_decision.invariants_checked items must be strings, "
                            f"got {type(item).__name__}"
                        )

    # metadata (optional)
    if "metadata" in data:
        meta = data["metadata"]
        if not isinstance(meta, dict):
            errors.append("metadata must be an object")
        else:
            if "severity" in meta and meta["severity"] not in _VALID_SEVERITIES:
                errors.append(
                    f"metadata.severity invalid: '{meta['severity']}'"
                )

    return errors


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDifferentialReplay:
    """BA-16: Differential replay fixture and runner tests."""

    def test_golden_no_drift_fixture_is_valid(self) -> None:
        """Load golden_no_drift.json and validate all schema fields."""
        assert _GOLDEN_NO_DRIFT.exists(), (
            f"Golden no-drift fixture not found: {_GOLDEN_NO_DRIFT}"
        )

        data = _load_json(_GOLDEN_NO_DRIFT)
        errors = _validate_fixture_schema(data)

        assert errors == [], (
            f"golden_no_drift.json has schema errors: {errors}"
        )

        # Additional structural assertions
        assert data["replay_id"] == "REPLAY-001"
        assert data["operation"] == "tenant.create"
        assert data["input_context"]["tenant_id"] == "t-golden-001"
        assert data["input_context"]["actor_type"] == "founder"
        assert data["expected_decision"]["outcome"] == "ALLOW"
        assert isinstance(data["expected_decision"]["invariants_checked"], list)
        assert data["metadata"]["severity"] == "HIGH"
        assert data["metadata"]["baseline_commit"] == "golden"

    def test_golden_deny_case_fixture_is_valid(self) -> None:
        """Load golden_deny_case.json and validate all schema fields."""
        assert _GOLDEN_DENY_CASE.exists(), (
            f"Golden deny-case fixture not found: {_GOLDEN_DENY_CASE}"
        )

        data = _load_json(_GOLDEN_DENY_CASE)
        errors = _validate_fixture_schema(data)

        assert errors == [], (
            f"golden_deny_case.json has schema errors: {errors}"
        )

        # Additional structural assertions
        assert data["replay_id"] == "REPLAY-002"
        assert data["operation"] == "incident.resolve"
        assert data["input_context"]["tenant_id"] == "t-golden-002"
        assert data["input_context"]["actor_type"] == "user"
        assert data["expected_decision"]["outcome"] == "DENY"
        assert "resolve" in data["expected_decision"]["reason"].lower()
        assert isinstance(data["expected_decision"]["invariants_checked"], list)
        assert data["metadata"]["severity"] == "MEDIUM"
        assert data["metadata"]["baseline_commit"] == "golden"

    def test_replay_runner_returns_zero_on_golden(self) -> None:
        """Run the replay script via subprocess on fixtures dir, assert exit 0."""
        assert _REPLAY_SCRIPT.exists(), (
            f"Replay script not found: {_REPLAY_SCRIPT}"
        )
        assert _FIXTURES_DIR.exists(), (
            f"Fixtures dir not found: {_FIXTURES_DIR}"
        )

        result = subprocess.run(
            [
                sys.executable,
                str(_REPLAY_SCRIPT),
                "--input",
                str(_FIXTURES_DIR),
            ],
            capture_output=True,
            text=True,
            cwd=str(_BACKEND_ROOT),
            env={**os.environ, "PYTHONPATH": str(_BACKEND_ROOT)},
            timeout=30,
        )

        # Print output for debugging if test fails
        if result.returncode != 0:
            print(f"STDOUT:\n{result.stdout}")
            print(f"STDERR:\n{result.stderr}")

        assert result.returncode == 0, (
            f"Replay runner exited with code {result.returncode}. "
            f"Expected 0 (no drifts).\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )

        # Verify output contains expected report markers
        assert "DIFFERENTIAL REPLAY REPORT" in result.stdout
        assert "REPLAY-001" in result.stdout
        assert "REPLAY-002" in result.stdout
        assert "DRIFT:   0" in result.stdout

    def test_replay_schema_file_is_valid_json(self) -> None:
        """Load replay_contract_schema.json and assert it is valid JSON."""
        assert _SCHEMA_PATH.exists(), (
            f"Schema file not found: {_SCHEMA_PATH}"
        )

        data = _load_json(_SCHEMA_PATH)

        # Verify it's a JSON Schema document
        assert isinstance(data, dict), "Schema must be a JSON object"
        assert "$schema" in data, "Schema must have $schema key"
        assert "properties" in data, "Schema must have properties key"
        assert "required" in data, "Schema must have required key"
        assert data["type"] == "object", "Schema type must be 'object'"
        assert data["title"] == "Replay Contract Schema"

        # Verify required fields are declared
        required = data["required"]
        assert "replay_id" in required
        assert "operation" in required
        assert "input_context" in required
        assert "expected_decision" in required

        # Verify properties structure
        props = data["properties"]
        assert "replay_id" in props
        assert "operation" in props
        assert "input_context" in props
        assert "expected_decision" in props
        assert "metadata" in props
