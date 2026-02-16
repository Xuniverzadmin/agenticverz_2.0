# Layer: TEST
# AUDIENCE: INTERNAL
# Role: Governance test — incident guardrail linkage enforcement
# artifact_class: TEST

"""
Incident Guardrail Linkage Tests (BA-28)

Validates that the INCIDENT_GUARDRAIL_TEMPLATE.md exists, has the correct
structure, and that every guardrail entry maps to a real invariant and a
real test file.  Also verifies that the check_incident_guardrail_linkage.py
script exits zero.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path constants — all relative to backend root
# ---------------------------------------------------------------------------

BACKEND_ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_PATH = (
    BACKEND_ROOT
    / "app"
    / "hoc"
    / "docs"
    / "architecture"
    / "usecases"
    / "INCIDENT_GUARDRAIL_TEMPLATE.md"
)
CHECKER_SCRIPT = (
    BACKEND_ROOT
    / "scripts"
    / "verification"
    / "check_incident_guardrail_linkage.py"
)

# ---------------------------------------------------------------------------
# Invariant alias map (mirrors the checker script)
# ---------------------------------------------------------------------------

_INVARIANT_ALIAS: dict[str, str] = {
    "INV-TENANT-001": "BI-TENANT-001",
    "INV-INC-001": "BI-INCIDENT-001",
    "INV-CTRL-001": "BI-CTRL-001",
}

# ---------------------------------------------------------------------------
# Table parser (duplicated from checker to keep test self-contained)
# ---------------------------------------------------------------------------

_TABLE_ROW_RE = re.compile(
    r"\|\s*(?P<incident>[^|]+?)\s*"
    r"\|\s*(?P<invariant>[^|]+?)\s*"
    r"\|\s*(?P<test>[^|]+?)\s*"
    r"\|\s*(?P<status>[^|]+?)\s*\|"
)


def _parse_guardrail_table(text: str) -> list[dict[str, str]]:
    """Parse the Current Guardrails markdown table."""
    entries: list[dict[str, str]] = []
    in_table = False

    for line in text.splitlines():
        stripped = line.strip()

        if "Incident" in stripped and "Invariant" in stripped and "Test" in stripped:
            in_table = True
            continue

        if not in_table:
            continue

        if stripped.startswith("|") and set(stripped.replace("|", "").strip()) <= {"-", " "}:
            continue

        if stripped.startswith("#") or stripped == "":
            if entries:
                break
            continue

        match = _TABLE_ROW_RE.match(stripped)
        if match:
            entries.append(
                {
                    "incident": match.group("incident").strip(),
                    "invariant": match.group("invariant").strip(),
                    "test": match.group("test").strip(),
                    "status": match.group("status").strip(),
                }
            )

    return entries


def _resolve_invariant_id(raw_id: str) -> str:
    """Resolve an alias invariant ID to the canonical form."""
    return _INVARIANT_ALIAS.get(raw_id, raw_id)


def _load_business_invariant_ids() -> set[str]:
    """Load the set of known invariant IDs from business_invariants.py."""
    try:
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BUSINESS_INVARIANTS,
        )

        return set(BUSINESS_INVARIANTS.keys())
    except ImportError:
        bi_path = (
            BACKEND_ROOT
            / "app"
            / "hoc"
            / "cus"
            / "hoc_spine"
            / "authority"
            / "business_invariants.py"
        )
        if not bi_path.exists():
            return set()
        content = bi_path.read_text()
        return set(re.findall(r'"(BI-[A-Z]+-\d+)"', content))


def _test_file_exists(test_ref: str) -> bool:
    """Check that the test file referenced in a guardrail entry exists on disk."""
    file_part = test_ref.split("::")[0].strip()
    candidates = [
        BACKEND_ROOT / "tests" / "governance" / "t5" / file_part,
        BACKEND_ROOT / "tests" / "governance" / "t4" / file_part,
        BACKEND_ROOT / "tests" / file_part,
    ]
    return any(p.exists() for p in candidates)


# =============================================================================
# TESTS
# =============================================================================


def test_guardrail_template_exists():
    """BA-28-T1: INCIDENT_GUARDRAIL_TEMPLATE.md exists on disk."""
    assert TEMPLATE_PATH.exists(), (
        f"INCIDENT_GUARDRAIL_TEMPLATE.md not found at {TEMPLATE_PATH}"
    )


def test_guardrail_template_has_required_fields_section():
    """BA-28-T2: Template contains a 'Required Fields' section."""
    content = TEMPLATE_PATH.read_text()
    assert "## Required Fields" in content, (
        "INCIDENT_GUARDRAIL_TEMPLATE.md is missing the '## Required Fields' section"
    )


def test_guardrail_registry_has_entries():
    """BA-28-T3: The 'Current Guardrails' table has at least 1 entry."""
    content = TEMPLATE_PATH.read_text()
    entries = _parse_guardrail_table(content)
    assert len(entries) >= 1, (
        f"Expected >= 1 guardrail entry in 'Current Guardrails' table, found {len(entries)}"
    )


def test_baseline_guardrails_reference_valid_invariants():
    """BA-28-T4: Each invariant_id in the guardrail table maps to a real invariant."""
    content = TEMPLATE_PATH.read_text()
    entries = _parse_guardrail_table(content)
    known = _load_business_invariant_ids()

    assert len(known) > 0, "Could not load any business invariants — check import path"

    failures: list[str] = []
    for entry in entries:
        raw_id = entry["invariant"]
        canonical = _resolve_invariant_id(raw_id)
        if canonical not in known:
            failures.append(
                f"{entry['incident']}: invariant '{raw_id}' "
                f"(resolved: '{canonical}') not in BUSINESS_INVARIANTS"
            )

    assert not failures, (
        f"Guardrail entries reference unknown invariants:\n"
        + "\n".join(f"  - {f}" for f in failures)
    )


def test_baseline_guardrails_reference_valid_tests():
    """BA-28-T5: Each test_file path in the guardrail table exists on disk."""
    content = TEMPLATE_PATH.read_text()
    entries = _parse_guardrail_table(content)

    failures: list[str] = []
    for entry in entries:
        test_ref = entry["test"]
        if not _test_file_exists(test_ref):
            failures.append(
                f"{entry['incident']}: test file '{test_ref}' not found on disk"
            )

    assert not failures, (
        f"Guardrail entries reference missing test files:\n"
        + "\n".join(f"  - {f}" for f in failures)
    )


def test_linkage_checker_exits_zero():
    """BA-28-T6: check_incident_guardrail_linkage.py exits 0 (all linked)."""
    assert CHECKER_SCRIPT.exists(), (
        f"Checker script not found at {CHECKER_SCRIPT}"
    )

    result = subprocess.run(
        [sys.executable, str(CHECKER_SCRIPT), "--strict"],
        capture_output=True,
        text=True,
        cwd=str(BACKEND_ROOT),
        env={**__import__("os").environ, "PYTHONPATH": str(BACKEND_ROOT)},
        timeout=30,
    )

    assert result.returncode == 0, (
        f"check_incident_guardrail_linkage.py --strict exited {result.returncode}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def test_no_orphan_incidents():
    """BA-28-T7: Every incident has BOTH an invariant and a test linkage (no orphans)."""
    content = TEMPLATE_PATH.read_text()
    entries = _parse_guardrail_table(content)
    known = _load_business_invariant_ids()

    orphans: list[str] = []
    for entry in entries:
        incident_id = entry["incident"]
        raw_invariant = entry["invariant"]
        test_ref = entry["test"]

        has_invariant = _resolve_invariant_id(raw_invariant) in known
        has_test = _test_file_exists(test_ref)

        if not has_invariant or not has_test:
            missing_parts: list[str] = []
            if not has_invariant:
                missing_parts.append("invariant")
            if not has_test:
                missing_parts.append("test")
            orphans.append(f"{incident_id}: missing {', '.join(missing_parts)}")

    assert not orphans, (
        f"Orphan incidents found (missing invariant and/or test linkage):\n"
        + "\n".join(f"  - {o}" for o in orphans)
    )
