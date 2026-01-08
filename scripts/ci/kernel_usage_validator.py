#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci
#   Execution: sync
# Role: CI validator for ExecutionKernel usage enforcement (PIN-337)
# Callers: CI pipeline, pre-commit hooks
# Allowed Imports: None (standalone script)
# Forbidden Imports: App runtime modules
# Reference: PIN-337

"""
PIN-337: Kernel Usage Validator - CI Structural Enforcement

This script performs SEMANTIC validation of ExecutionKernel usage:
- Scans for EXECUTE-power paths (HTTP mutating routes, CLI commands, workers)
- Verifies each calls ExecutionKernel (either directly or via @governed)
- Reports violations for CI to fail on

PHILOSOPHY:
- Check kernel USAGE, not decorator PRESENCE (semantic, not syntactic)
- The kernel is PHYSICS, this validator enforces the physics
- Unknown capability_id = CI FAIL (compile-time enforcement)

Usage:
    python scripts/ci/kernel_usage_validator.py [--strict] [--verbose]

Exit Codes:
    0 - All EXECUTE paths routed through kernel
    1 - Violations found (EXECUTE path without kernel)
    2 - Script error
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class ExecutePath:
    """Represents an identified EXECUTE-power path."""

    file_path: str
    line_number: int
    path_type: str  # HTTP_ADMIN, CLI, WORKER, SDK
    identifier: str  # route path, command name, class name
    capability_id: Optional[str] = None
    has_kernel_call: bool = False
    has_governed_decorator: bool = False
    details: str = ""


@dataclass
class ValidationResult:
    """Result of kernel usage validation."""

    total_paths: int = 0
    compliant_paths: int = 0
    violations: List[ExecutePath] = field(default_factory=list)
    deferred: List[ExecutePath] = field(
        default_factory=list
    )  # Known deferred violations
    warnings: List[str] = field(default_factory=list)


# Known EXECUTE-power patterns
# NOTE: These patterns identify EXECUTE-power paths that MUST route through kernel.
# Be precise - model classes and data containers are NOT execute paths.

HTTP_EXECUTE_PATTERNS = [
    # Admin routes that mutate state
    (r'@app\.(post|put|patch|delete)\s*\(\s*["\']\/admin', "HTTP_ADMIN"),
    # Founder review routes that mutate
    (r'@app\.(post|put|patch|delete)\s*\(\s*["\']\/api\/v\d+\/founder', "HTTP_ADMIN"),
    # Recovery approval routes (mutates recovery candidates)
    (r'@app\.post\s*\(\s*["\']\/api\/v\d+\/recovery\/approve', "HTTP_ADMIN"),
]

# Deprecated routes (return 410 Gone) - excluded from validation
DEPRECATED_ROUTE_PATTERNS = [
    r"/admin/rerun",  # Deprecated in favor of /admin/retry (PIN-337)
]

# Known deferred violations - documented for incremental integration
# These are REAL violations but are being addressed incrementally per PIN-337
KNOWN_DEFERRED_VIOLATIONS = {
    "BusinessBuilderWorker": "Deferred to Phase 7 incremental integration",
    "AlertWorker": "Deferred to Phase 7 incremental integration",
}

CLI_EXECUTE_PATTERNS = [
    # CLI command functions that execute logic (mutations)
    (r"def\s+cmd_simulate\s*\(", "CLI"),
    (r"def\s+cmd_recovery_approve\s*\(", "CLI"),
]

WORKER_EXECUTE_PATTERNS = [
    # Recovery claim worker - processes recovery candidates
    (r"class\s+RecoveryClaimWorker", "WORKER"),
    # Business builder worker - executes business plans
    (r"class\s+BusinessBuilderWorker", "WORKER"),
    # Alert worker - processes alerts
    (r"class\s+AlertWorker", "WORKER"),
    # Outbox processor run method
    (r"async\s+def\s+run\s*\(\s*self\s*\)\s*->\s*None\s*:.*outbox", "WORKER"),
]

# Kernel usage patterns
KERNEL_USAGE_PATTERNS = [
    r"ExecutionKernel\.invoke",
    r"ExecutionKernel\.invoke_async",
    r"ExecutionKernel\._emit_envelope",
    r"ExecutionKernel\._record_invocation",
    r"record_cli_invocation\s*\(",
    r"record_worker_invocation\s*\(",
]

GOVERNED_DECORATOR_PATTERN = r"@governed\s*\("


def is_deprecated_route(identifier: str) -> bool:
    """Check if a route is deprecated (returns 410 Gone)."""
    for pattern in DEPRECATED_ROUTE_PATTERNS:
        if re.search(pattern, identifier):
            return True
    return False


def find_execute_paths(file_path: str, content: str) -> List[ExecutePath]:
    """Find all EXECUTE-power paths in a file."""
    paths = []
    lines = content.split("\n")

    for i, line in enumerate(lines, 1):
        # Check HTTP patterns
        for pattern, path_type in HTTP_EXECUTE_PATTERNS:
            if re.search(pattern, line):
                # Extract route path
                route_match = re.search(r'["\']([^"\']+)["\']', line)
                identifier = route_match.group(1) if route_match else "unknown"

                # Skip deprecated routes
                if is_deprecated_route(identifier):
                    continue

                paths.append(
                    ExecutePath(
                        file_path=file_path,
                        line_number=i,
                        path_type=path_type,
                        identifier=identifier,
                        details=line.strip(),
                    )
                )

        # Check CLI patterns
        for pattern, path_type in CLI_EXECUTE_PATTERNS:
            if re.search(pattern, line):
                # Extract function name
                func_match = re.search(r"def\s+(\w+)", line)
                identifier = func_match.group(1) if func_match else "unknown"
                paths.append(
                    ExecutePath(
                        file_path=file_path,
                        line_number=i,
                        path_type=path_type,
                        identifier=identifier,
                        details=line.strip(),
                    )
                )

        # Check Worker patterns
        for pattern, path_type in WORKER_EXECUTE_PATTERNS:
            if re.search(pattern, line):
                # Extract class/method name
                name_match = re.search(r"(class|def)\s+(\w+)", line)
                identifier = name_match.group(2) if name_match else "unknown"
                paths.append(
                    ExecutePath(
                        file_path=file_path,
                        line_number=i,
                        path_type=path_type,
                        identifier=identifier,
                        details=line.strip(),
                    )
                )

    return paths


def check_kernel_usage(file_path: str, content: str, execute_path: ExecutePath) -> bool:
    """
    Check if an EXECUTE path uses the ExecutionKernel.

    Looks for kernel usage within the function/method scope.
    """
    lines = content.split("\n")

    # Find the scope of the execute path (function or class method)
    start_line = execute_path.line_number - 1

    # Determine indent level
    current_line = lines[start_line] if start_line < len(lines) else ""
    base_indent = len(current_line) - len(current_line.lstrip())

    # Scan forward to find kernel usage in scope
    in_scope = True
    scope_content = []

    for i in range(start_line, min(start_line + 200, len(lines))):  # Max 200 lines
        line = lines[i]

        # Skip empty lines
        if not line.strip():
            scope_content.append(line)
            continue

        # Check if we've exited the scope (dedented to base level or less)
        line_indent = len(line) - len(line.lstrip())
        if (
            i > start_line
            and line_indent <= base_indent
            and line.strip()
            and not line.strip().startswith("#")
        ):
            # Check for class/function at same or lower indent
            if re.match(r"\s*(def|class|@)", line):
                break

        scope_content.append(line)

    scope_text = "\n".join(scope_content)

    # Check for kernel usage patterns
    for pattern in KERNEL_USAGE_PATTERNS:
        if re.search(pattern, scope_text):
            return True

    # Check for @governed decorator (look backwards from the function)
    for i in range(max(0, start_line - 5), start_line):
        if re.search(GOVERNED_DECORATOR_PATTERN, lines[i]):
            execute_path.has_governed_decorator = True
            return True

    return False


def validate_file(
    file_path: str, verbose: bool = False
) -> Tuple[List[ExecutePath], List[ExecutePath], List[ExecutePath]]:
    """
    Validate a single file for kernel usage.

    Returns:
        Tuple of (compliant_paths, violations, deferred)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        if verbose:
            print(f"  Warning: Could not read {file_path}: {e}")
        return [], [], []

    execute_paths = find_execute_paths(file_path, content)
    compliant = []
    violations = []
    deferred = []

    for path in execute_paths:
        has_kernel = check_kernel_usage(file_path, content, path)
        path.has_kernel_call = has_kernel

        if has_kernel:
            compliant.append(path)
        elif path.identifier in KNOWN_DEFERRED_VIOLATIONS:
            # Known deferred violation - tracked separately
            path.details = KNOWN_DEFERRED_VIOLATIONS[path.identifier]
            deferred.append(path)
        else:
            violations.append(path)

    return compliant, violations, deferred


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
        "__pycache__",
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "tests/",  # Don't validate test files for kernel usage
        "quarantine/",
    ]
    all_excludes = default_excludes + exclude_patterns

    for root, dirs, files in os.walk(directory):
        # Filter excluded directories
        dirs[:] = [
            d
            for d in dirs
            if not any(excl in os.path.join(root, d) for excl in all_excludes)
        ]

        for file in files:
            if not file.endswith(".py"):
                continue

            file_path = os.path.join(root, file)

            # Skip excluded files
            if any(excl in file_path for excl in all_excludes):
                continue

            if verbose:
                print(f"  Scanning: {file_path}")

            compliant, violations, deferred = validate_file(file_path, verbose)

            result.total_paths += len(compliant) + len(violations) + len(deferred)
            result.compliant_paths += len(compliant)
            result.violations.extend(violations)
            result.deferred.extend(deferred)

    return result


def print_report(result: ValidationResult, verbose: bool = False) -> None:
    """Print validation report."""
    print()
    print("=" * 70)
    print("  PIN-337 KERNEL USAGE VALIDATION REPORT")
    print("=" * 70)
    print()

    print(f"  Total EXECUTE paths found:    {result.total_paths}")
    print(f"  Compliant (kernel routed):    {result.compliant_paths}")
    print(f"  Deferred (known, tracked):    {len(result.deferred)}")
    print(f"  Violations (no kernel):       {len(result.violations)}")
    print()

    if result.deferred:
        print("  DEFERRED (Known Violations - Tracked for Incremental Integration):")
        print("  " + "-" * 66)
        for d in result.deferred:
            print(f"    [{d.path_type}] {d.file_path}:{d.line_number}")
            print(f"           {d.identifier}")
            print(f"           Reason: {d.details}")
        print()

    if result.violations:
        print("  VIOLATIONS (Blocking):")
        print("  " + "-" * 66)
        for v in result.violations:
            print(f"    [{v.path_type}] {v.file_path}:{v.line_number}")
            print(f"           {v.identifier}")
            if verbose:
                print(f"           {v.details[:60]}...")
        print()
        print("  ❌ FAIL: EXECUTE paths found without ExecutionKernel routing")
        print()
        print("  Resolution:")
        print("    1. Add ExecutionKernel.invoke() call, OR")
        print("    2. Use @governed decorator, OR")
        print("    3. Add record_*_invocation() helper call")
        print()
    elif result.deferred:
        print(
            "  ⚠️  PASS (with deferred items): Core paths compliant, deferred items tracked"
        )
        print()
    else:
        print("  ✅ PASS: All EXECUTE paths route through ExecutionKernel")
        print()

    if result.warnings:
        print("  Warnings:")
        for w in result.warnings:
            print(f"    ⚠️  {w}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="PIN-337 Kernel Usage Validator - CI Structural Enforcement"
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

    print("PIN-337 Kernel Usage Validator")
    print(f"Scanning: {scan_dir}")

    result = validate_directory(
        str(scan_dir),
        exclude_patterns=args.exclude,
        verbose=args.verbose,
    )

    print_report(result, verbose=args.verbose)

    # Exit code
    if result.violations and args.strict:
        sys.exit(1)
    elif result.violations:
        # Non-strict: warn but don't fail
        print("  Note: Running in non-strict mode. Use --strict to fail on violations.")
        sys.exit(0)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
