# Layer: TEST
# AUDIENCE: INTERNAL
# Role: Runtime spec contract enforcement tests
# artifact_class: TEST

"""
Operation Spec Enforcement Tests (BA-08)

Validates the OPERATION_SPEC_REGISTRY_V1.md at test time:
  - File existence
  - Minimum operation count
  - Field completeness (preconditions, postconditions, forbidden_states)
  - No duplicate operation names
  - Domain coverage
  - Forbidden state actionability
  - Static checker script exits zero

Uses pathlib.Path to construct paths relative to the test file location.
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

_TEST_DIR = Path(__file__).resolve().parent
_BACKEND_ROOT = _TEST_DIR.parent.parent.parent  # tests/governance/t5 -> backend/
_REGISTRY_PATH = (
    _BACKEND_ROOT
    / "app"
    / "hoc"
    / "docs"
    / "architecture"
    / "usecases"
    / "OPERATION_SPEC_REGISTRY_V1.md"
)
_CHECKER_SCRIPT = (
    _BACKEND_ROOT / "scripts" / "verification" / "check_operation_specs.py"
)


# ---------------------------------------------------------------------------
# Helpers — lightweight YAML-block parser (mirrors check_operation_specs.py)
# ---------------------------------------------------------------------------


def _extract_yaml_blocks(content: str) -> list[str]:
    """Extract YAML code blocks from markdown content."""
    pattern = r"```yaml\s*\n(.*?)```"
    return re.findall(pattern, content, re.DOTALL)


def _parse_yaml_block(block: str) -> dict[str, Any]:
    """Parse a YAML-like code block into a dict."""
    spec: dict[str, Any] = {}
    current_key: str | None = None

    for line in block.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("- ") and current_key:
            value = stripped[2:].strip().strip('"').strip("'")
            if current_key not in spec:
                spec[current_key] = []
            if isinstance(spec[current_key], list):
                spec[current_key].append(value)
            continue

        if ":" in stripped:
            colon_idx = stripped.index(":")
            key = stripped[:colon_idx].strip()
            value = stripped[colon_idx + 1:].strip().strip('"').strip("'")
            if value:
                spec[key] = value
            else:
                spec[key] = []
            current_key = key

    return spec


def _load_specs() -> list[dict[str, Any]]:
    """Load all operation specs from the registry markdown file."""
    content = _REGISTRY_PATH.read_text(encoding="utf-8")
    yaml_blocks = _extract_yaml_blocks(content)
    specs = []
    for block in yaml_blocks:
        spec = _parse_yaml_block(block)
        if "spec_id" in spec or "operation_name" in spec:
            specs.append(spec)
    return specs


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def specs() -> list[dict[str, Any]]:
    """Load specs once per module."""
    return _load_specs()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_spec_registry_file_exists():
    """Assert OPERATION_SPEC_REGISTRY_V1.md exists."""
    assert _REGISTRY_PATH.is_file(), (
        f"Spec registry file not found at: {_REGISTRY_PATH}"
    )


def test_spec_registry_has_operations(specs: list[dict[str, Any]]):
    """Parse file, assert >= 15 operations defined."""
    assert len(specs) >= 15, (
        f"Expected at least 15 operation specs, found {len(specs)}"
    )


def test_each_spec_has_preconditions(specs: list[dict[str, Any]]):
    """Every operation has at least one precondition."""
    for spec in specs:
        op = spec.get("operation_name", spec.get("spec_id", "<unknown>"))
        preconditions = spec.get("preconditions", [])
        assert isinstance(preconditions, list) and len(preconditions) >= 1, (
            f"Spec '{op}' must have at least 1 precondition, "
            f"found {len(preconditions) if isinstance(preconditions, list) else 0}"
        )


def test_each_spec_has_postconditions(specs: list[dict[str, Any]]):
    """Every operation has at least one postcondition."""
    for spec in specs:
        op = spec.get("operation_name", spec.get("spec_id", "<unknown>"))
        postconditions = spec.get("postconditions", [])
        assert isinstance(postconditions, list) and len(postconditions) >= 1, (
            f"Spec '{op}' must have at least 1 postcondition, "
            f"found {len(postconditions) if isinstance(postconditions, list) else 0}"
        )


def test_each_spec_has_forbidden_states(specs: list[dict[str, Any]]):
    """Every operation has at least one forbidden state."""
    for spec in specs:
        op = spec.get("operation_name", spec.get("spec_id", "<unknown>"))
        forbidden = spec.get("forbidden_states", [])
        assert isinstance(forbidden, list) and len(forbidden) >= 1, (
            f"Spec '{op}' must have at least 1 forbidden state, "
            f"found {len(forbidden) if isinstance(forbidden, list) else 0}"
        )


def test_no_duplicate_operation_names(specs: list[dict[str, Any]]):
    """No two specs share the same operation_name."""
    seen: dict[str, int] = {}
    duplicates: list[str] = []
    for spec in specs:
        op = spec.get("operation_name", "")
        if not op:
            continue
        if op in seen:
            duplicates.append(op)
        seen[op] = seen.get(op, 0) + 1

    assert len(duplicates) == 0, (
        f"Duplicate operation_name(s) found: {duplicates}"
    )


def test_spec_checker_exits_zero():
    """Run check_operation_specs.py via subprocess, assert exit 0."""
    assert _CHECKER_SCRIPT.is_file(), (
        f"Checker script not found at: {_CHECKER_SCRIPT}"
    )
    result = subprocess.run(
        [sys.executable, str(_CHECKER_SCRIPT)],
        capture_output=True,
        text=True,
        cwd=str(_BACKEND_ROOT),
        env={**__import__("os").environ, "PYTHONPATH": str(_BACKEND_ROOT)},
        timeout=30,
    )
    assert result.returncode == 0, (
        f"check_operation_specs.py exited with code {result.returncode}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def test_all_domains_represented(specs: list[dict[str, Any]]):
    """At least 5 distinct domains in specs."""
    domains = {spec.get("domain", "").lower() for spec in specs if spec.get("domain")}
    assert len(domains) >= 5, (
        f"Expected at least 5 distinct domains, found {len(domains)}: {sorted(domains)}"
    )


def test_forbidden_states_are_actionable(specs: list[dict[str, Any]]):
    """Each forbidden state is a non-empty string."""
    for spec in specs:
        op = spec.get("operation_name", spec.get("spec_id", "<unknown>"))
        forbidden = spec.get("forbidden_states", [])
        if not isinstance(forbidden, list):
            continue
        for i, state in enumerate(forbidden):
            assert isinstance(state, str) and state.strip() != "", (
                f"Spec '{op}' forbidden_states[{i}] is empty or not a string"
            )
