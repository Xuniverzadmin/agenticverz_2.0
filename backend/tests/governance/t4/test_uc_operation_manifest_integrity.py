# Layer: L8 — Test
# AUDIENCE: INTERNAL
# Role: Validates UC operation manifest JSON integrity — field presence, decision counts, handler existence
# Product: system-wide
# Temporal:
#   Trigger: CI / manual
#   Execution: sync
# Callers: pytest, CI
# Allowed Imports: stdlib, json, pathlib
# Forbidden Imports: FastAPI, DB, ORM
# Reference: UC Codebase Elicitation Validation UAT — Workstream B2
# artifact_class: TEST

"""
Tests for UC_OPERATION_MANIFEST_2026-02-15.json

Validates the operation manifest produced by Iteration-3 decision table
materialisation. Ensures structural correctness, field completeness, decision
type consistency, handler file existence, and HOLD/ASSIGN invariants.

Acceptance criteria:
  - Manifest is a list with exactly 44 entries.
  - Every entry has all required fields.
  - Decision type counts: 7 ASSIGN, 22 SPLIT, 15 HOLD.
  - All uc_ids are valid (UC-001..UC-040 or literal "HOLD").
  - ASSIGN entries have non-empty test_refs.
  - Every non-null handler_file exists on disk.
  - HOLD entries have a hold_status field.
  - No HOLD entry has a non-HOLD uc_id.
  - ASSIGN uc_id distribution matches expected: {UC-002: 3, UC-004: 1, UC-006: 2, UC-008: 1}.
"""

import json
import re
from collections import Counter
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_BACKEND_ROOT = Path(__file__).resolve().parents[3]
_USECASES_DIR = _BACKEND_ROOT / "app" / "hoc" / "docs" / "architecture" / "usecases"
_MANIFEST_PATH = _USECASES_DIR / "UC_OPERATION_MANIFEST_2026-02-15.json"

# ---------------------------------------------------------------------------
# Valid UC pattern: UC-001 through UC-040, or the literal "HOLD"
# ---------------------------------------------------------------------------

_VALID_UC_PATTERN = re.compile(r"^UC-0(?:0[1-9]|[12]\d|3\d|40)$")

_REQUIRED_FIELDS = {
    "uc_id",
    "operation_name",
    "handler_file",
    "engine_or_driver_files",
    "decision_type",
}


def _valid_uc_or_hold(uc_id: str) -> bool:
    """Return True if uc_id is UC-001..UC-040 or literal 'HOLD'."""
    if uc_id == "HOLD":
        return True
    return bool(_VALID_UC_PATTERN.match(uc_id))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def manifest():
    """Load the operation manifest JSON and return the list of entries."""
    assert _MANIFEST_PATH.exists(), f"Manifest not found: {_MANIFEST_PATH}"
    with open(_MANIFEST_PATH) as f:
        data = json.load(f)
    assert isinstance(data, list), "Manifest root must be a JSON array"
    return data


# ---------------------------------------------------------------------------
# Test class: Structural integrity
# ---------------------------------------------------------------------------


class TestManifestStructure:
    """Basic structural checks on the operation manifest."""

    def test_manifest_is_list(self, manifest):
        """Manifest must be a JSON array."""
        assert isinstance(manifest, list)

    def test_manifest_entry_count(self, manifest):
        """Manifest must contain exactly 44 entries."""
        assert len(manifest) == 44, (
            f"Expected 44 entries, got {len(manifest)}"
        )

    def test_every_entry_has_required_fields(self, manifest):
        """Every entry must have uc_id, operation_name, handler_file,
        engine_or_driver_files, and decision_type."""
        for i, entry in enumerate(manifest):
            missing = _REQUIRED_FIELDS - set(entry.keys())
            assert not missing, (
                f"Entry {i} ('{entry.get('operation_name', '?')}') "
                f"is missing required fields: {missing}"
            )


# ---------------------------------------------------------------------------
# Test class: Decision type counts
# ---------------------------------------------------------------------------


class TestDecisionTypeCounts:
    """Decision type distribution in the manifest."""

    def test_assign_count(self, manifest):
        """Exactly 7 entries must have decision_type=ASSIGN."""
        count = sum(1 for e in manifest if e["decision_type"] == "ASSIGN")
        assert count == 7, f"Expected 7 ASSIGN entries, got {count}"

    def test_split_count(self, manifest):
        """Exactly 22 entries must have decision_type=SPLIT."""
        count = sum(1 for e in manifest if e["decision_type"] == "SPLIT")
        assert count == 22, f"Expected 22 SPLIT entries, got {count}"

    def test_hold_count(self, manifest):
        """Exactly 15 entries must have decision_type=HOLD."""
        count = sum(1 for e in manifest if e["decision_type"] == "HOLD")
        assert count == 15, f"Expected 15 HOLD entries, got {count}"

    def test_no_unknown_decision_types(self, manifest):
        """No entry may have a decision_type outside {ASSIGN, SPLIT, HOLD}."""
        allowed = {"ASSIGN", "SPLIT", "HOLD"}
        for i, entry in enumerate(manifest):
            dt = entry["decision_type"]
            assert dt in allowed, (
                f"Entry {i} ('{entry.get('operation_name', '?')}') "
                f"has unknown decision_type: '{dt}'"
            )


# ---------------------------------------------------------------------------
# Test class: UC ID validity
# ---------------------------------------------------------------------------


class TestUcIdValidity:
    """All uc_id values must be valid UC identifiers or 'HOLD'."""

    def test_all_uc_ids_valid(self, manifest):
        """Every uc_id must be UC-001..UC-040 or 'HOLD'."""
        for i, entry in enumerate(manifest):
            uc_id = entry["uc_id"]
            assert _valid_uc_or_hold(uc_id), (
                f"Entry {i} ('{entry.get('operation_name', '?')}') "
                f"has invalid uc_id: '{uc_id}'"
            )


# ---------------------------------------------------------------------------
# Test class: ASSIGN invariants
# ---------------------------------------------------------------------------


class TestAssignInvariants:
    """ASSIGN entries must have non-empty test_refs and expected UC distribution."""

    def test_assign_entries_have_nonempty_test_refs(self, manifest):
        """ASSIGN entries must have a non-empty test_refs list."""
        assign_entries = [e for e in manifest if e["decision_type"] == "ASSIGN"]
        for entry in assign_entries:
            test_refs = entry.get("test_refs", [])
            assert isinstance(test_refs, list) and len(test_refs) > 0, (
                f"ASSIGN entry '{entry['operation_name']}' (uc_id={entry['uc_id']}) "
                f"has empty or missing test_refs"
            )

    def test_assign_uc_distribution(self, manifest):
        """ASSIGN entries must map to exactly:
        UC-002: 3 entries, UC-004: 1, UC-006: 2, UC-008: 1."""
        expected = {"UC-002": 3, "UC-004": 1, "UC-006": 2, "UC-008": 1}
        assign_entries = [e for e in manifest if e["decision_type"] == "ASSIGN"]
        actual = dict(Counter(e["uc_id"] for e in assign_entries))
        assert actual == expected, (
            f"ASSIGN UC distribution mismatch:\n"
            f"  expected: {expected}\n"
            f"  actual:   {actual}"
        )


# ---------------------------------------------------------------------------
# Test class: Handler file existence
# ---------------------------------------------------------------------------


class TestHandlerFileExistence:
    """Every non-null handler_file must exist on disk."""

    def test_handler_files_exist(self, manifest):
        """handler_file must exist on disk when not null."""
        missing = []
        for entry in manifest:
            hf = entry.get("handler_file")
            if hf is None:
                # Null handler_file is allowed for HOLD entries
                continue
            full_path = _BACKEND_ROOT / hf
            if not full_path.exists():
                missing.append(
                    f"{entry['uc_id']}:{entry['operation_name']} -> {hf}"
                )
        assert not missing, (
            f"{len(missing)} handler files missing from disk:\n"
            + "\n".join(f"  {m}" for m in missing)
        )


# ---------------------------------------------------------------------------
# Test class: HOLD invariants
# ---------------------------------------------------------------------------


class TestHoldInvariants:
    """HOLD entries must have hold_status and must use uc_id='HOLD'."""

    def test_hold_entries_have_hold_status(self, manifest):
        """Every HOLD entry must include a hold_status field."""
        hold_entries = [e for e in manifest if e["decision_type"] == "HOLD"]
        for entry in hold_entries:
            assert "hold_status" in entry, (
                f"HOLD entry '{entry['operation_name']}' is missing hold_status"
            )
            assert entry["hold_status"], (
                f"HOLD entry '{entry['operation_name']}' has empty hold_status"
            )

    def test_no_hold_entry_has_non_hold_uc_id(self, manifest):
        """HOLD entries must have uc_id='HOLD', not a real UC ID.
        This prevents force-fitting unresolved operations into canonical UCs."""
        hold_entries = [e for e in manifest if e["decision_type"] == "HOLD"]
        violations = []
        for entry in hold_entries:
            if entry["uc_id"] != "HOLD":
                violations.append(
                    f"  {entry['operation_name']}: uc_id='{entry['uc_id']}'"
                )
        assert not violations, (
            f"{len(violations)} HOLD entries have non-HOLD uc_id "
            f"(prevents force-fitting):\n" + "\n".join(violations)
        )
