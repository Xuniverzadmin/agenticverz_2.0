# Layer: L4 — Governance Test
# AUDIENCE: INTERNAL
# Role: Regression guard for stagetest route prefix policy
# artifact_class: TEST
"""
Tests for stagetest route prefix guard.

Ensures:
1. The guard script runs cleanly.
2. No /api/v1/stagetest references exist in the codebase.
3. Canonical /hoc/api/stagetest references are present.
"""

import subprocess
import sys
import os

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def test_guard_script_exits_zero():
    """Guard script exits 0 (no forbidden references)."""
    result = subprocess.run(
        [sys.executable, "scripts/verification/stagetest_route_prefix_guard.py"],
        capture_output=True, text=True, cwd=BACKEND_DIR,
    )
    assert result.returncode == 0, f"Guard failed:\n{result.stdout}\n{result.stderr}"


def test_guard_reports_zero_forbidden():
    """Guard output includes 'Forbidden references: 0'."""
    result = subprocess.run(
        [sys.executable, "scripts/verification/stagetest_route_prefix_guard.py"],
        capture_output=True, text=True, cwd=BACKEND_DIR,
    )
    assert "Forbidden references: 0" in result.stdout


def test_guard_finds_canonical_references():
    """Guard detects canonical /hoc/api/stagetest references."""
    result = subprocess.run(
        [sys.executable, "scripts/verification/stagetest_route_prefix_guard.py"],
        capture_output=True, text=True, cwd=BACKEND_DIR,
    )
    # After implementation, canonical count should be > 0
    for line in result.stdout.splitlines():
        if "Canonical references:" in line:
            count = int(line.split(":")[1].strip())
            assert count > 0, "Expected canonical /hoc/api/stagetest references in codebase"
            break
    else:
        raise AssertionError("Canonical references line not found in guard output")
