#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Role: Validates incident-to-guardrail linkage — every incident must map to invariant + test
# artifact_class: CODE

"""
Incident Guardrail Linkage Checker (BA-27)

Reads the INCIDENT_GUARDRAIL_TEMPLATE.md file, parses the "Current Guardrails"
table, and validates that:

1. Each invariant_id maps to a known business invariant (via alias or direct match).
2. Each test_file path exists on disk.

Exit codes:
  0 = all guardrails linked correctly
  1 = one or more guardrails have broken linkage
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

BACKEND_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_PATH = (
    BACKEND_ROOT
    / "app"
    / "hoc"
    / "docs"
    / "architecture"
    / "usecases"
    / "INCIDENT_GUARDRAIL_TEMPLATE.md"
)

# ---------------------------------------------------------------------------
# Invariant alias map
# ---------------------------------------------------------------------------
# The guardrail template uses short-form invariant IDs (INV-XXX-NNN) while
# the canonical BUSINESS_INVARIANTS registry uses BI-XXX-NNN.  This map
# resolves aliases so the linkage check succeeds for both forms.

_INVARIANT_ALIAS: dict[str, str] = {
    "INV-TENANT-001": "BI-TENANT-001",
    "INV-INC-001": "BI-INCIDENT-001",
    "INV-CTRL-001": "BI-CTRL-001",
}


def _load_business_invariants() -> set[str]:
    """Return the set of known invariant IDs from the canonical registry."""
    try:
        from app.hoc.cus.hoc_spine.authority.business_invariants import (
            BUSINESS_INVARIANTS,
        )

        return set(BUSINESS_INVARIANTS.keys())
    except ImportError:
        # Fallback: parse the file directly to extract invariant IDs
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


def _resolve_invariant_id(raw_id: str) -> str:
    """Resolve an alias invariant ID to the canonical form."""
    return _INVARIANT_ALIAS.get(raw_id, raw_id)


# ---------------------------------------------------------------------------
# Table parser
# ---------------------------------------------------------------------------

_TABLE_ROW_RE = re.compile(
    r"\|\s*(?P<incident>[^|]+?)\s*"
    r"\|\s*(?P<invariant>[^|]+?)\s*"
    r"\|\s*(?P<test>[^|]+?)\s*"
    r"\|\s*(?P<status>[^|]+?)\s*\|"
)


def parse_guardrail_table(template_text: str) -> list[dict[str, str]]:
    """
    Parse the 'Current Guardrails' markdown table from the template.

    Returns a list of dicts with keys: incident, invariant, test, status.
    Skips header and separator rows.
    """
    entries: list[dict[str, str]] = []
    in_table = False

    for line in template_text.splitlines():
        stripped = line.strip()

        # Detect table start by header row
        if "Incident" in stripped and "Invariant" in stripped and "Test" in stripped:
            in_table = True
            continue

        if not in_table:
            continue

        # Skip separator rows (e.g., |---|---|---|---|)
        if stripped.startswith("|") and set(stripped.replace("|", "").strip()) <= {"-", " "}:
            continue

        # Stop parsing at the next markdown section or blank line
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


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------


def _test_file_exists(test_ref: str) -> bool:
    """
    Check that the test file referenced in a guardrail entry exists.

    test_ref may be in the form "test_foo.py::test_bar" — we only check
    the file part.  The file is resolved relative to the tests/ directory
    in the backend root.
    """
    file_part = test_ref.split("::")[0].strip()

    # Search common test directories
    candidates = [
        BACKEND_ROOT / "tests" / "governance" / "t5" / file_part,
        BACKEND_ROOT / "tests" / "governance" / "t4" / file_part,
        BACKEND_ROOT / "tests" / file_part,
    ]

    return any(p.exists() for p in candidates)


def validate_guardrails(
    entries: list[dict[str, str]],
    known_invariants: set[str],
    strict: bool = False,
) -> tuple[int, int, list[str]]:
    """
    Validate each guardrail entry.

    Returns:
        (linked_count, unlinked_count, messages)
    """
    linked = 0
    unlinked = 0
    messages: list[str] = []

    for entry in entries:
        incident_id = entry["incident"]
        raw_invariant = entry["invariant"]
        test_ref = entry["test"]
        status = entry["status"]

        # Skip RETIRED entries unless strict
        if status == "RETIRED" and not strict:
            messages.append(f"[SKIP] {incident_id} — status RETIRED (skipped in non-strict mode)")
            continue

        missing: list[str] = []

        # Check invariant linkage
        canonical_id = _resolve_invariant_id(raw_invariant)
        if canonical_id not in known_invariants:
            missing.append(f"invariant '{raw_invariant}' (resolved: '{canonical_id}') not in BUSINESS_INVARIANTS")

        # Check test file existence
        if not _test_file_exists(test_ref):
            missing.append(f"test file '{test_ref}' not found on disk")

        if missing:
            unlinked += 1
            detail = "; ".join(missing)
            messages.append(f"[FAIL] {incident_id} — missing: {detail}")
        else:
            linked += 1
            messages.append(f"[PASS] {incident_id} — linked to {raw_invariant}, test exists")

    return linked, unlinked, messages


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate incident-to-guardrail linkage (BA-27)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict mode: include RETIRED entries, fail on any issue",
    )
    parser.add_argument(
        "--template",
        type=str,
        default=str(TEMPLATE_PATH),
        help="Path to INCIDENT_GUARDRAIL_TEMPLATE.md",
    )
    args = parser.parse_args()

    template_path = Path(args.template)
    if not template_path.exists():
        print(f"[FAIL] Template not found: {template_path}")
        return 1

    template_text = template_path.read_text()
    entries = parse_guardrail_table(template_text)

    if not entries:
        print("[FAIL] No guardrail entries found in 'Current Guardrails' table")
        return 1

    known_invariants = _load_business_invariants()
    if not known_invariants:
        print("[FAIL] Could not load BUSINESS_INVARIANTS — 0 invariants found")
        return 1

    linked, unlinked, messages = validate_guardrails(entries, known_invariants, strict=args.strict)

    # Print results
    print("=" * 60)
    print("Incident Guardrail Linkage Check (BA-27)")
    print("=" * 60)
    for msg in messages:
        print(msg)
    print("-" * 60)
    print(f"Total incidents: {linked + unlinked}")
    print(f"Linked:          {linked}")
    print(f"Unlinked:        {unlinked}")
    print("=" * 60)

    if unlinked > 0:
        print("RESULT: FAIL — unlinked incidents detected")
        return 1

    print("RESULT: PASS — all incidents linked to invariant + test")
    return 0


if __name__ == "__main__":
    sys.exit(main())
