#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Role: Runtime/API boundary enforcement
# Reference: docs/architecture/contracts/RUNTIME_VS_API.md

"""
Runtime/API Boundary Check

Detects violations:
- API endpoints directly accessing runtime schema fields
- Missing adapters for domain responses
- Direct field access patterns that should use adapters
"""

import ast
import re
import sys
from pathlib import Path
from typing import NamedTuple


class Violation(NamedTuple):
    file: str
    line: int
    code: str
    rule: str
    message: str


# Runtime schema field patterns that should go through adapters
RUNTIME_FIELD_PATTERNS = [
    # HeadroomInfo fields
    r"\.headroom\.tokens\b",
    r"\.headroom\.runs\b",
    r"\.headroom\.cost_cents\b",
    # Common runtime patterns
    r"\.decision\.value\b",
    r"\.status\.value\b",
]

# Files that are allowed to access runtime fields directly
ALLOWED_FILES = [
    "_adapters/",
    "services/",
    "schemas/",
    "models/",
    "tests/",
]


def is_in_api_layer(file_path: Path, backend_path: Path) -> bool:
    """Check if file is in the API layer (L2)."""
    rel_path = str(file_path.relative_to(backend_path))
    return rel_path.startswith("app/api/") and not any(a in rel_path for a in ALLOWED_FILES)


def check_direct_runtime_access(backend_path: Path) -> list[Violation]:
    """Check for direct runtime field access in API layer."""
    violations = []
    api_path = backend_path / "app" / "api"

    if not api_path.exists():
        return violations

    for py_file in api_path.rglob("*.py"):
        # Skip adapters and __init__ files
        rel_path = str(py_file.relative_to(backend_path))
        if any(a in rel_path for a in ALLOWED_FILES):
            continue

        try:
            content = py_file.read_text()
            lines = content.split("\n")
        except (UnicodeDecodeError, IOError):
            continue

        for line_num, line in enumerate(lines, 1):
            for pattern in RUNTIME_FIELD_PATTERNS:
                if re.search(pattern, line):
                    # Extract the relevant code snippet
                    code_snippet = line.strip()[:60]
                    if len(line.strip()) > 60:
                        code_snippet += "..."

                    violations.append(Violation(
                        file=rel_path,
                        line=line_num,
                        code=code_snippet,
                        rule="RAB-001",
                        message="Direct runtime field access in API layer. Use adapter."
                    ))

    return violations


def check_missing_adapters(backend_path: Path) -> list[Violation]:
    """Check for domains that have API endpoints but no adapters."""
    violations = []
    api_path = backend_path / "app" / "api"
    adapters_path = api_path / "_adapters"

    if not api_path.exists():
        return violations

    # Find all domain directories in api/
    domain_dirs = [
        d for d in api_path.iterdir()
        if d.is_dir() and not d.name.startswith("_") and d.name != "debug"
    ]

    for domain_dir in domain_dirs:
        # Check if this domain has any endpoints that return complex objects
        has_complex_responses = False

        for py_file in domain_dir.glob("*.py"):
            content = py_file.read_text()
            # Look for response models or dict returns
            if re.search(r"response_model\s*=", content) or re.search(r"return\s*\{", content):
                has_complex_responses = True
                break

        if has_complex_responses:
            # Check for corresponding adapter
            adapter_file = adapters_path / f"{domain_dir.name}.py"
            if not adapter_file.exists():
                violations.append(Violation(
                    file=f"app/api/{domain_dir.name}/",
                    line=0,
                    code="",
                    rule="RAB-002",
                    message=f"Domain '{domain_dir.name}' has endpoints but no adapter. "
                           f"Create app/api/_adapters/{domain_dir.name}.py"
                ))

    return violations


def check_response_construction(backend_path: Path) -> list[Violation]:
    """Check for inline response construction that should use adapters."""
    violations = []
    api_path = backend_path / "app" / "api"

    if not api_path.exists():
        return violations

    # Pattern for inline dict construction with field mapping
    inline_mapping_pattern = re.compile(
        r'"(\w+_remaining|\w+_current)":\s*\w+\.\w+\.(\w+)'
    )

    for py_file in api_path.rglob("*.py"):
        rel_path = str(py_file.relative_to(backend_path))
        if any(a in rel_path for a in ALLOWED_FILES):
            continue

        try:
            content = py_file.read_text()
            lines = content.split("\n")
        except (UnicodeDecodeError, IOError):
            continue

        for line_num, line in enumerate(lines, 1):
            match = inline_mapping_pattern.search(line)
            if match:
                violations.append(Violation(
                    file=rel_path,
                    line=line_num,
                    code=line.strip()[:60],
                    rule="RAB-003",
                    message="Inline field mapping in API endpoint. Move to adapter."
                ))

    return violations


def main():
    backend_path = Path(__file__).parent.parent.parent / "backend"

    if not backend_path.exists():
        print(f"Backend path not found: {backend_path}")
        sys.exit(1)

    print("RUNTIME/API BOUNDARY CHECK")
    print("=" * 60)

    all_violations = []

    # Run checks
    print("\n▶ Checking for direct runtime field access...")
    access_violations = check_direct_runtime_access(backend_path)
    all_violations.extend(access_violations)
    print(f"  Found {len(access_violations)} violations")

    print("\n▶ Checking for missing adapters...")
    adapter_violations = check_missing_adapters(backend_path)
    all_violations.extend(adapter_violations)
    print(f"  Found {len(adapter_violations)} violations")

    print("\n▶ Checking for inline response construction...")
    response_violations = check_response_construction(backend_path)
    all_violations.extend(response_violations)
    print(f"  Found {len(response_violations)} violations")

    print("\n" + "=" * 60)

    if not all_violations:
        print("✓ RUNTIME/API BOUNDARY CHECK: PASSED")
        print("  - Direct runtime access: 0 violations")
        print("  - Missing adapters: 0 violations")
        print("  - Inline construction: 0 violations")
        sys.exit(0)
    else:
        print("✗ RUNTIME/API BOUNDARY CHECK: FAILED")
        print(f"\nTotal violations: {len(all_violations)}\n")

        for i, v in enumerate(all_violations, 1):
            print(f"Violation {i}:")
            print(f"  File: {v.file}:{v.line}" if v.line else f"  File: {v.file}")
            if v.code:
                print(f"  Code: {v.code}")
            print(f"  Rule: {v.rule}")
            print(f"  Message: {v.message}")
            print()

        print("Fix: Create adapter in app/api/_adapters/{domain}.py")
        print("Reference: docs/architecture/contracts/RUNTIME_VS_API.md")
        sys.exit(1)


if __name__ == "__main__":
    main()
