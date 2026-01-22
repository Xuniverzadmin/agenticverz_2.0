#!/usr/bin/env python3
"""
Audience Guard - CI enforcement for audience classification.

This script validates import boundaries between different AUDIENCE classifications:
- CUSTOMER code cannot import FOUNDER code
- CUSTOMER code should not directly import INTERNAL (prefer through facades)
- Validates that files have AUDIENCE and PURPOSE/Role headers

Reference: AUDIENCE_REGISTRY.yaml
"""

import argparse
import ast
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


# =============================================================================
# Configuration
# =============================================================================

AUDIENCE_PATTERN = re.compile(r"^#\s*AUDIENCE:\s*(CUSTOMER|FOUNDER|INTERNAL|SHARED)\s*$", re.MULTILINE)
PURPOSE_PATTERN = re.compile(r"^#\s*Role:\s*(.+)$", re.MULTILINE)

# Import rules: from_audience -> cannot import -> [to_audiences]
FORBIDDEN_IMPORTS = {
    "CUSTOMER": ["FOUNDER"],
    "FOUNDER": [],  # Founder can import anything
    "INTERNAL": [],  # Internal can import anything
    "SHARED": [],  # Shared can import anything
}

# Directories to scan
SCAN_DIRS = [
    "app/api",
    "app/services",
    "app/adapters",
    "app/worker",
    "app/core",
]

# Files/directories to skip
SKIP_PATTERNS = [
    "__pycache__",
    ".pytest_cache",
    "*.pyc",
    "tests/",
]


@dataclass
class FileInfo:
    """Information about a Python file."""
    path: Path
    audience: Optional[str]
    purpose: Optional[str]
    imports: List[str]
    module_name: str


@dataclass
class Violation:
    """An audience import violation."""
    file_path: str
    line_number: int
    from_audience: str
    to_audience: str
    imported_module: str
    message: str


# =============================================================================
# File Parsing
# =============================================================================


def extract_audience_from_file(file_path: Path) -> Tuple[Optional[str], Optional[str]]:
    """Extract AUDIENCE and PURPOSE/Role from file header."""
    try:
        content = file_path.read_text(encoding="utf-8")
        # Only look in first 50 lines for performance
        header = "\n".join(content.split("\n")[:50])

        audience_match = AUDIENCE_PATTERN.search(header)
        purpose_match = PURPOSE_PATTERN.search(header)

        audience = audience_match.group(1) if audience_match else None
        purpose = purpose_match.group(1).strip() if purpose_match else None

        return audience, purpose
    except Exception:
        return None, None


def extract_imports_from_file(file_path: Path) -> List[Tuple[str, int]]:
    """Extract import statements and their line numbers."""
    imports = []
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append((alias.name, node.lineno))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append((node.module, node.lineno))
    except SyntaxError:
        pass  # Skip files with syntax errors
    except Exception:
        pass

    return imports


def path_to_module(file_path: Path, base_dir: Path) -> str:
    """Convert file path to Python module name."""
    relative = file_path.relative_to(base_dir)
    parts = list(relative.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    elif parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]
    return ".".join(parts)


# =============================================================================
# Build File Index
# =============================================================================


def should_skip(path: Path) -> bool:
    """Check if path should be skipped."""
    path_str = str(path)
    for pattern in SKIP_PATTERNS:
        if pattern.endswith("/"):
            if f"/{pattern}" in path_str or path_str.startswith(pattern):
                return True
        elif pattern.startswith("*."):
            if path_str.endswith(pattern[1:]):
                return True
        elif pattern in path_str:
            return True
    return False


def build_file_index(base_dir: Path) -> Dict[str, FileInfo]:
    """Build an index of all Python files with their audience."""
    index: Dict[str, FileInfo] = {}

    for scan_dir in SCAN_DIRS:
        dir_path = base_dir / scan_dir
        if not dir_path.exists():
            continue

        for py_file in dir_path.rglob("*.py"):
            if should_skip(py_file):
                continue

            audience, purpose = extract_audience_from_file(py_file)
            imports = extract_imports_from_file(py_file)
            module_name = path_to_module(py_file, base_dir)

            index[module_name] = FileInfo(
                path=py_file,
                audience=audience,
                purpose=purpose,
                imports=[imp[0] for imp in imports],
                module_name=module_name,
            )

    return index


def get_audience_for_module(module: str, index: Dict[str, FileInfo]) -> Optional[str]:
    """Get audience for a module, checking parent packages if needed."""
    # Direct match
    if module in index:
        return index[module].audience

    # Check parent packages
    parts = module.split(".")
    for i in range(len(parts) - 1, 0, -1):
        parent = ".".join(parts[:i])
        if parent in index:
            return index[parent].audience

    return None


# =============================================================================
# Validation
# =============================================================================


def validate_imports(index: Dict[str, FileInfo]) -> List[Violation]:
    """Validate all imports against audience rules."""
    violations = []

    for module_name, file_info in index.items():
        if not file_info.audience:
            continue  # Skip files without audience header

        forbidden = FORBIDDEN_IMPORTS.get(file_info.audience, [])
        if not forbidden:
            continue  # This audience has no restrictions

        # Check each import
        imports_with_lines = extract_imports_from_file(file_info.path)
        for imported_module, line_no in imports_with_lines:
            # Skip external imports
            if not imported_module.startswith("app."):
                continue

            imported_audience = get_audience_for_module(imported_module, index)
            if imported_audience and imported_audience in forbidden:
                violations.append(Violation(
                    file_path=str(file_info.path),
                    line_number=line_no,
                    from_audience=file_info.audience,
                    to_audience=imported_audience,
                    imported_module=imported_module,
                    message=f"{file_info.audience} code cannot import {imported_audience} module",
                ))

    return violations


def check_missing_headers(index: Dict[str, FileInfo], strict: bool = False) -> List[str]:
    """Find files missing AUDIENCE headers."""
    missing = []

    for module_name, file_info in index.items():
        if file_info.audience is None:
            # Only report if strict mode or file has other headers (partially classified)
            content = file_info.path.read_text(encoding="utf-8")
            has_layer_header = "# Layer:" in content[:1000]

            if strict or has_layer_header:
                missing.append(str(file_info.path))

    return missing


# =============================================================================
# Reporting
# =============================================================================


def print_violations(violations: List[Violation]) -> None:
    """Print violations in a readable format."""
    if not violations:
        print("✓ No audience import violations found")
        return

    print(f"\n✗ Found {len(violations)} audience import violation(s):\n")

    for v in violations:
        print(f"  {v.file_path}:{v.line_number}")
        print(f"    → {v.message}")
        print(f"    Import: {v.imported_module}")
        print()


def print_missing_headers(missing: List[str], strict: bool) -> None:
    """Print files missing headers."""
    if not missing:
        print("✓ All scanned files have AUDIENCE headers")
        return

    severity = "Warning" if not strict else "Error"
    print(f"\n{severity}: {len(missing)} file(s) missing AUDIENCE header:\n")

    for path in missing[:20]:  # Limit output
        print(f"  - {path}")

    if len(missing) > 20:
        print(f"  ... and {len(missing) - 20} more")


def print_summary(index: Dict[str, FileInfo]) -> None:
    """Print summary statistics."""
    audiences = {"CUSTOMER": 0, "FOUNDER": 0, "INTERNAL": 0, "SHARED": 0, "NONE": 0}
    purpose_stats = {"HAS_PURPOSE": 0, "MISSING_PURPOSE": 0}

    for file_info in index.values():
        audience = file_info.audience or "NONE"
        audiences[audience] = audiences.get(audience, 0) + 1
        if file_info.purpose:
            purpose_stats["HAS_PURPOSE"] += 1
        else:
            purpose_stats["MISSING_PURPOSE"] += 1

    print("\n=== Audience Distribution ===")
    for aud, count in sorted(audiences.items()):
        if count > 0:
            print(f"  {aud}: {count}")

    print("\n=== Purpose/Role Coverage ===")
    print(f"  Has Role header: {purpose_stats['HAS_PURPOSE']}")
    print(f"  Missing Role header: {purpose_stats['MISSING_PURPOSE']}")


# =============================================================================
# Main
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Validate audience import boundaries for CI enforcement"
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="Run in CI mode (exit with non-zero on violations)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode: fail if any files are missing AUDIENCE headers",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print summary statistics",
    )
    parser.add_argument(
        "--base-dir",
        default=".",
        help="Base directory to scan (default: current directory)",
    )

    args = parser.parse_args()
    base_dir = Path(args.base_dir).resolve()

    # Ensure we're in the right directory
    if not (base_dir / "app").exists():
        print(f"Error: {base_dir}/app not found. Run from backend directory.")
        sys.exit(1)

    print(f"Scanning {base_dir}...\n")

    # Build index
    index = build_file_index(base_dir)
    print(f"Indexed {len(index)} Python files")

    # Validate imports
    violations = validate_imports(index)
    print_violations(violations)

    # Check missing headers
    missing = check_missing_headers(index, strict=args.strict)
    print_missing_headers(missing, strict=args.strict)

    # Summary
    if args.summary:
        print_summary(index)

    # Exit status for CI
    if args.ci:
        has_violations = len(violations) > 0
        has_missing = args.strict and len(missing) > 0

        if has_violations or has_missing:
            print("\n✗ CI CHECK FAILED")
            sys.exit(1)
        else:
            print("\n✓ CI CHECK PASSED")
            sys.exit(0)


if __name__ == "__main__":
    main()
