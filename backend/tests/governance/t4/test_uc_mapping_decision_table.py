# Layer: L8 — Test
# AUDIENCE: INTERNAL
# Role: Validates Iteration-3 decision table integrity against canonical linkage doc and manifest
# Product: system-wide
# Temporal:
#   Trigger: CI / manual
#   Execution: sync
# Callers: pytest, CI
# Allowed Imports: stdlib, csv, pathlib
# Forbidden Imports: FastAPI, DB, ORM
# Reference: UC Codebase Elicitation Validation UAT — Workstream B2
# artifact_class: TEST

"""
Tests for HOC_CUS_UC_MATCH_ITERATION3_DECISION_TABLE_2026-02-15.csv

Validates that the Iteration-3 decision table is correctly reflected in the
canonical linkage doc (HOC_USECASE_CODE_LINKAGE.md) and the operation manifest.

Acceptance criteria:
  - Decision column contains only {ASSIGN, SPLIT, HOLD}.
  - Row counts per decision match expected totals (7 ASSIGN, 8 SPLIT, 15 HOLD).
  - ASSIGN rows have exactly one UC (no pipe characters).
  - SPLIT rows have at least 2 UCs (pipe-separated).
  - HOLD rows have empty assigned_uc.
  - All UC IDs fall within the UC-001..UC-040 range.
  - Linkage doc contains Iteration-3 ASSIGN Anchors for UC-002, UC-004, UC-006, UC-008.
"""

import csv
import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_USECASES_DIR = Path(__file__).resolve().parents[3] / "app" / "hoc" / "docs" / "architecture" / "usecases"
_CSV_PATH = _USECASES_DIR / "HOC_CUS_UC_MATCH_ITERATION3_DECISION_TABLE_2026-02-15.csv"
_LINKAGE_PATH = _USECASES_DIR / "HOC_USECASE_CODE_LINKAGE.md"

# ---------------------------------------------------------------------------
# Valid UC pattern: UC-001 through UC-040
# ---------------------------------------------------------------------------

_VALID_UC_PATTERN = re.compile(r"^UC-0(?:0[1-9]|[12]\d|3\d|40)$")


def _valid_uc_id(uc_id: str) -> bool:
    """Return True if uc_id matches UC-001..UC-040."""
    return bool(_VALID_UC_PATTERN.match(uc_id))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def decision_rows():
    """Load the decision table CSV and return a list of row dicts."""
    assert _CSV_PATH.exists(), f"Decision table CSV not found: {_CSV_PATH}"
    with open(_CSV_PATH, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) > 0, "Decision table CSV is empty"
    return rows


@pytest.fixture(scope="module")
def linkage_text():
    """Load the canonical linkage doc as a string."""
    assert _LINKAGE_PATH.exists(), f"Linkage doc not found: {_LINKAGE_PATH}"
    return _LINKAGE_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------


class TestDecisionTableStructure:
    """Structural integrity of the Iteration-3 decision table."""

    def test_total_row_count(self, decision_rows):
        """Decision table must have exactly 30 data rows (7 + 8 + 15)."""
        assert len(decision_rows) == 30, (
            f"Expected 30 rows, got {len(decision_rows)}"
        )

    def test_no_unknown_decisions(self, decision_rows):
        """Every row must have decision in {ASSIGN, SPLIT, HOLD}."""
        allowed = {"ASSIGN", "SPLIT", "HOLD"}
        for i, row in enumerate(decision_rows):
            decision = row["decision"]
            assert decision in allowed, (
                f"Row {i} has invalid decision '{decision}'; "
                f"allowed: {allowed}"
            )

    def test_assign_count(self, decision_rows):
        """Exactly 7 rows must have decision=ASSIGN."""
        assign_rows = [r for r in decision_rows if r["decision"] == "ASSIGN"]
        assert len(assign_rows) == 7, (
            f"Expected 7 ASSIGN rows, got {len(assign_rows)}"
        )

    def test_split_count(self, decision_rows):
        """Exactly 8 rows must have decision=SPLIT."""
        split_rows = [r for r in decision_rows if r["decision"] == "SPLIT"]
        assert len(split_rows) == 8, (
            f"Expected 8 SPLIT rows, got {len(split_rows)}"
        )

    def test_hold_count(self, decision_rows):
        """Exactly 15 rows must have decision=HOLD."""
        hold_rows = [r for r in decision_rows if r["decision"] == "HOLD"]
        assert len(hold_rows) == 15, (
            f"Expected 15 HOLD rows, got {len(hold_rows)}"
        )


class TestAssignDecisionRules:
    """ASSIGN rows must have exactly one canonical UC with no pipe characters."""

    def test_assign_rows_have_single_uc(self, decision_rows):
        """ASSIGN rows must have exactly one UC (no pipe separator)."""
        assign_rows = [r for r in decision_rows if r["decision"] == "ASSIGN"]
        for row in assign_rows:
            assigned = row["assigned_uc"].strip()
            assert "|" not in assigned, (
                f"ASSIGN row '{row['script_path']}' has pipe in assigned_uc: "
                f"'{assigned}' — ASSIGN must map to exactly one UC"
            )
            assert assigned != "", (
                f"ASSIGN row '{row['script_path']}' has empty assigned_uc"
            )

    def test_assign_rows_known_ucs(self, decision_rows):
        """ASSIGN rows must map to known UC IDs: UC-002, UC-004, UC-006, UC-008."""
        expected_ucs = {"UC-002", "UC-004", "UC-006", "UC-008"}
        assign_rows = [r for r in decision_rows if r["decision"] == "ASSIGN"]
        actual_ucs = {r["assigned_uc"].strip() for r in assign_rows}
        assert actual_ucs == expected_ucs, (
            f"ASSIGN UC set mismatch: expected {expected_ucs}, got {actual_ucs}"
        )

    def test_assign_uc_ids_within_valid_range(self, decision_rows):
        """All assigned UC IDs in ASSIGN rows must be within UC-001..UC-040."""
        assign_rows = [r for r in decision_rows if r["decision"] == "ASSIGN"]
        for row in assign_rows:
            uc_id = row["assigned_uc"].strip()
            assert _valid_uc_id(uc_id), (
                f"ASSIGN row '{row['script_path']}' has out-of-range UC: '{uc_id}'"
            )


class TestSplitDecisionRules:
    """SPLIT rows must have at least 2 pipe-separated UCs."""

    def test_split_rows_have_multiple_ucs(self, decision_rows):
        """SPLIT rows must contain at least 2 UCs separated by pipe."""
        split_rows = [r for r in decision_rows if r["decision"] == "SPLIT"]
        for row in split_rows:
            assigned = row["assigned_uc"].strip()
            parts = assigned.split("|")
            assert len(parts) >= 2, (
                f"SPLIT row '{row['script_path']}' has fewer than 2 UCs: "
                f"'{assigned}'"
            )

    def test_split_uc_ids_within_valid_range(self, decision_rows):
        """All UC IDs in SPLIT rows must be within UC-001..UC-040."""
        split_rows = [r for r in decision_rows if r["decision"] == "SPLIT"]
        for row in split_rows:
            parts = row["assigned_uc"].strip().split("|")
            for uc_id in parts:
                uc_id = uc_id.strip()
                assert _valid_uc_id(uc_id), (
                    f"SPLIT row '{row['script_path']}' has out-of-range UC: "
                    f"'{uc_id}' in '{row['assigned_uc']}'"
                )


class TestHoldDecisionRules:
    """HOLD rows must have an empty assigned_uc."""

    def test_hold_rows_have_empty_assigned_uc(self, decision_rows):
        """HOLD rows must not assign any UC."""
        hold_rows = [r for r in decision_rows if r["decision"] == "HOLD"]
        for row in hold_rows:
            assigned = row["assigned_uc"].strip()
            assert assigned == "", (
                f"HOLD row '{row['script_path']}' has non-empty assigned_uc: "
                f"'{assigned}' — HOLD rows must leave assigned_uc empty"
            )


class TestAllUcIdsInRange:
    """All UC IDs across all decision types must be within UC-001..UC-040."""

    def test_all_assigned_ucs_in_range(self, decision_rows):
        """Every non-empty assigned_uc value must contain only valid UC IDs."""
        for row in decision_rows:
            assigned = row["assigned_uc"].strip()
            if not assigned:
                continue
            parts = assigned.split("|")
            for uc_id in parts:
                uc_id = uc_id.strip()
                assert _valid_uc_id(uc_id), (
                    f"Row '{row['script_path']}' (decision={row['decision']}) "
                    f"has out-of-range UC: '{uc_id}'"
                )


class TestLinkageDocIterationAnchors:
    """Canonical linkage doc must contain Iteration-3 ASSIGN Anchors for anchored UCs."""

    @pytest.mark.parametrize("uc_id", ["UC-002", "UC-004", "UC-006", "UC-008"])
    def test_linkage_contains_iteration3_assign_anchor(self, linkage_text, uc_id):
        """HOC_USECASE_CODE_LINKAGE.md must have an 'Iteration-3 ASSIGN Anchors'
        section under the given UC."""
        # The anchors appear under the UC's section heading.  We verify that
        # after the UC heading line, the text "Iteration-3 ASSIGN Anchors"
        # appears before the next UC heading.
        uc_heading_pattern = re.compile(
            rf"^## {re.escape(uc_id)}:",
            re.MULTILINE,
        )
        heading_match = uc_heading_pattern.search(linkage_text)
        assert heading_match is not None, (
            f"Linkage doc has no section heading for {uc_id}"
        )

        # Find the next UC heading after this one
        next_heading = re.search(
            r"^## UC-\d{3}:",
            linkage_text[heading_match.end():],
            re.MULTILINE,
        )
        if next_heading:
            section_text = linkage_text[heading_match.end():heading_match.end() + next_heading.start()]
        else:
            section_text = linkage_text[heading_match.end():]

        assert "Iteration-3 ASSIGN Anchors" in section_text, (
            f"Linkage doc section for {uc_id} does not contain "
            f"'Iteration-3 ASSIGN Anchors'"
        )
