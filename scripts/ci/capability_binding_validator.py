#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci
#   Execution: sync
# Role: CI validator for capability binding enforcement (PIN-337)
# Callers: CI pipeline, pre-commit hooks
# Allowed Imports: None (standalone script)
# Forbidden Imports: App runtime modules
# Reference: PIN-337

"""
PIN-337: Capability Binding Validator - CI Compile-Time Enforcement

This script validates that all capability_id references in code are:
1. Known capabilities from the registry
2. Not "unknown" or placeholder strings
3. Bound to registered capabilities

PHILOSOPHY:
- Unknown capability_id = CI FAIL (compile-time, not runtime)
- Capability MUST pre-exist before code references it
- "Unknown" string is invalid

Usage:
    python scripts/ci/capability_binding_validator.py [--strict] [--verbose]

Exit Codes:
    0 - All capability bindings valid
    1 - Invalid capability bindings found
    2 - Script error
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set, Tuple

# Known capability IDs (must match ExecutionKernel._KNOWN_CAPABILITIES)
# Source of truth: app/governance/kernel.py
KNOWN_CAPABILITIES: Set[str] = {
    # FIRST_CLASS (CAP-001 to CAP-021)
    "CAP-001", "CAP-002", "CAP-003", "CAP-004", "CAP-005",
    "CAP-006", "CAP-007", "CAP-008", "CAP-009", "CAP-010",
    "CAP-011", "CAP-012", "CAP-013", "CAP-014", "CAP-015",
    "CAP-016", "CAP-017", "CAP-018", "CAP-019", "CAP-020",
    "CAP-021",
    # SUBSTRATE (SUB-001 to SUB-020)
    "SUB-001", "SUB-002", "SUB-003", "SUB-004", "SUB-005",
    "SUB-006", "SUB-007", "SUB-008", "SUB-009", "SUB-010",
    "SUB-011", "SUB-012", "SUB-013", "SUB-014", "SUB-015",
    "SUB-016", "SUB-017", "SUB-018", "SUB-019", "SUB-020",
}

# Patterns to find capability_id references
CAPABILITY_PATTERNS = [
    # capability_id="CAP-XXX" or capability_id='CAP-XXX'
    r'capability_id\s*=\s*["\']([^"\']+)["\']',
    # "capability_id": "CAP-XXX"
    r'"capability_id"\s*:\s*["\']([^"\']+)["\']',
    # CapabilityId.CAP_NNN or CapabilityId.SUB_NNN (enum references)
    r'CapabilityId\.(CAP_\d+|SUB_\d+)',
]

# Invalid capability values (placeholders, unknowns)
INVALID_CAPABILITY_VALUES = {
    "unknown",
    "UNKNOWN",
    "none",
    "None",
    "null",
    "placeholder",
    "TODO",
    "FIXME",
    "TBD",
}


@dataclass
class CapabilityBinding:
    """A capability binding found in code."""
    file_path: str
    line_number: int
    capability_id: str
    context: str  # Line content


@dataclass
class ValidationResult:
    """Result of capability binding validation."""
    total_bindings: int = 0
    valid_bindings: int = 0
    invalid_bindings: List[CapabilityBinding] = field(default_factory=list)
    unknown_bindings: List[CapabilityBinding] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def find_capability_bindings(file_path: str, content: str) -> List[CapabilityBinding]:
    """Find all capability_id bindings in a file."""
    bindings = []
    lines = content.split('\n')

    for i, line in enumerate(lines, 1):
        for pattern in CAPABILITY_PATTERNS:
            for match in re.finditer(pattern, line):
                cap_id = match.group(1)
                bindings.append(CapabilityBinding(
                    file_path=file_path,
                    line_number=i,
                    capability_id=cap_id,
                    context=line.strip()[:80],
                ))

    return bindings


def normalize_capability_id(cap_id: str) -> str:
    """
    Normalize capability ID format.

    Converts underscore format (CAP_020) to hyphen format (CAP-020).
    """
    # Replace underscore with hyphen for comparison
    return cap_id.replace("_", "-")


def validate_binding(binding: CapabilityBinding) -> Tuple[bool, str]:
    """
    Validate a single capability binding.

    Returns:
        (is_valid, reason)
    """
    cap_id = binding.capability_id
    normalized = normalize_capability_id(cap_id)

    # Check for invalid placeholder values
    if cap_id.lower() in {v.lower() for v in INVALID_CAPABILITY_VALUES}:
        return False, f"Placeholder value: {cap_id}"

    # Check if it's a known capability (normalize underscore to hyphen)
    if normalized not in KNOWN_CAPABILITIES:
        # Allow CAP-XXX or SUB-XXX format with unknown number (for flexibility)
        if re.match(r'^(CAP|SUB)[-_]\d{3}$', cap_id):
            return False, f"Unknown capability: {cap_id}"
        else:
            return False, f"Invalid format: {cap_id}"

    return True, "Valid"


def validate_file(file_path: str, verbose: bool = False) -> Tuple[List[CapabilityBinding], List[CapabilityBinding], List[CapabilityBinding]]:
    """
    Validate all capability bindings in a file.

    Returns:
        Tuple of (valid_bindings, invalid_bindings, unknown_bindings)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        if verbose:
            print(f"  Warning: Could not read {file_path}: {e}")
        return [], [], []

    bindings = find_capability_bindings(file_path, content)
    valid = []
    invalid = []
    unknown = []

    for binding in bindings:
        is_valid, reason = validate_binding(binding)
        if is_valid:
            valid.append(binding)
        elif "Unknown capability" in reason:
            unknown.append(binding)
        else:
            invalid.append(binding)

    return valid, invalid, unknown


def validate_directory(
    directory: str,
    exclude_patterns: Optional[List[str]] = None,
    verbose: bool = False,
) -> ValidationResult:
    """
    Validate all Python files in a directory tree.
    """
    result = ValidationResult()
    exclude_patterns = exclude_patterns or []

    # Default exclusions
    default_excludes = [
        '__pycache__',
        '.git',
        'node_modules',
        '.venv',
        'venv',
        'quarantine/',
    ]
    all_excludes = default_excludes + exclude_patterns

    for root, dirs, files in os.walk(directory):
        # Filter excluded directories
        dirs[:] = [d for d in dirs if not any(excl in os.path.join(root, d) for excl in all_excludes)]

        for file in files:
            if not file.endswith('.py'):
                continue

            file_path = os.path.join(root, file)

            # Skip excluded files
            if any(excl in file_path for excl in all_excludes):
                continue

            if verbose:
                print(f"  Scanning: {file_path}")

            valid, invalid, unknown = validate_file(file_path, verbose)

            result.total_bindings += len(valid) + len(invalid) + len(unknown)
            result.valid_bindings += len(valid)
            result.invalid_bindings.extend(invalid)
            result.unknown_bindings.extend(unknown)

    return result


def print_report(result: ValidationResult, verbose: bool = False) -> None:
    """Print validation report."""
    print()
    print("=" * 70)
    print("  PIN-337 CAPABILITY BINDING VALIDATION REPORT")
    print("=" * 70)
    print()

    print(f"  Total capability bindings found:   {result.total_bindings}")
    print(f"  Valid bindings:                    {result.valid_bindings}")
    print(f"  Unknown capability IDs:            {len(result.unknown_bindings)}")
    print(f"  Invalid bindings:                  {len(result.invalid_bindings)}")
    print()

    if result.unknown_bindings:
        print("  UNKNOWN CAPABILITIES (CI FAIL):")
        print("  " + "-" * 66)
        for b in result.unknown_bindings:
            print(f"    {b.file_path}:{b.line_number}")
            print(f"           capability_id={b.capability_id}")
            if verbose:
                print(f"           {b.context}")
        print()
        print("  Resolution:")
        print("    1. Register the capability in CAPABILITY_REGISTRY_UNIFIED.yaml")
        print("    2. Update kernel._KNOWN_CAPABILITIES")
        print("    3. Use an existing capability ID")
        print()

    if result.invalid_bindings:
        print("  INVALID BINDINGS (CI FAIL):")
        print("  " + "-" * 66)
        for b in result.invalid_bindings:
            print(f"    {b.file_path}:{b.line_number}")
            print(f"           capability_id={b.capability_id}")
            if verbose:
                print(f"           {b.context}")
        print()
        print("  Resolution:")
        print("    Replace placeholder values with valid capability IDs")
        print()

    if result.unknown_bindings or result.invalid_bindings:
        print("  ❌ FAIL: Invalid capability bindings found")
        print()
    else:
        print("  ✅ PASS: All capability bindings are valid")
        print()

    if result.warnings:
        print("  Warnings:")
        for w in result.warnings:
            print(f"    ⚠️  {w}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="PIN-337 Capability Binding Validator - CI Compile-Time Enforcement"
    )
    parser.add_argument(
        "--directory",
        "-d",
        default="backend/app",
        help="Directory to scan (default: backend/app)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode: exit 1 on any violation",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Additional patterns to exclude",
    )

    args = parser.parse_args()

    # Determine base directory
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent.parent
    scan_dir = repo_root / args.directory

    if not scan_dir.exists():
        print(f"Error: Directory not found: {scan_dir}")
        sys.exit(2)

    print(f"PIN-337 Capability Binding Validator")
    print(f"Scanning: {scan_dir}")

    result = validate_directory(
        str(scan_dir),
        exclude_patterns=args.exclude,
        verbose=args.verbose,
    )

    print_report(result, verbose=args.verbose)

    # Exit code
    if (result.unknown_bindings or result.invalid_bindings) and args.strict:
        sys.exit(1)
    elif result.unknown_bindings or result.invalid_bindings:
        print("  Note: Running in non-strict mode. Use --strict to fail on violations.")
        sys.exit(0)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
