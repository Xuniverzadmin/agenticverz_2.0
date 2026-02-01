#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: GUARDRAIL: API-002 - Consistent Response Envelope
# artifact_class: CODE
"""
GUARDRAIL: API-002 - Consistent Response Envelope
Rule: All API responses must use standard envelope format.

This script validates that API endpoints use consistent response structures.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Standard envelope patterns (what we want)
STANDARD_ENVELOPE_PATTERNS = [
    r'ResponseEnvelope',
    r'StandardResponse',
    r'APIResponse',
    r'data=.*,\s*meta=',
    r'"data":\s*{',
    r'"success":\s*(true|false)',
    r'ListResponse',
    r'PaginatedResponse',
    r'ErrorResponse',
]

# Patterns indicating direct model return (should use envelope)
DIRECT_RETURN_PATTERNS = [
    # Returning a list directly
    (r'return\s+\[\s*\w+\s+for\s+', 'list comprehension'),
    # Returning a dict without envelope
    (r'return\s+\{[^}]*\}(?!\s*\))', 'raw dict'),
    # Returning model directly
    (r'return\s+\w+\s*$', 'direct model'),
]

# Exceptions (endpoints that can return non-envelope responses)
EXCEPTIONS = [
    r'health',
    r'metrics',
    r'ping',
    r'ready',
    r'alive',
    r'openapi',
    r'docs',
    r'schema',
]


def extract_route_handlers(content: str) -> List[Tuple[str, str, str]]:
    """Extract route handler functions."""
    handlers = []

    # Find route decorators and their functions
    pattern = r'@(?:router|app)\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\'].*?\).*?(?:async\s+)?def\s+(\w+)\s*\([^)]*\).*?(?=@(?:router|app)\.|(?:async\s+)?def\s+|\Z)'
    matches = re.finditer(pattern, content, re.DOTALL)

    for match in matches:
        method = match.group(1).upper()
        path = match.group(2)
        func_name = match.group(3)
        func_content = match.group(0)
        handlers.append((f"{method} {path}", func_name, func_content))

    return handlers


def is_exception_route(path: str) -> bool:
    """Check if route is an exception."""
    for exc in EXCEPTIONS:
        if re.search(exc, path, re.IGNORECASE):
            return True
    return False


def check_response_format(func_content: str) -> Tuple[bool, str]:
    """Check if function uses standard envelope."""
    # Check for standard envelope patterns
    for pattern in STANDARD_ENVELOPE_PATTERNS:
        if re.search(pattern, func_content, re.IGNORECASE):
            return True, ""

    # Check for direct returns (violations)
    for pattern, violation_type in DIRECT_RETURN_PATTERNS:
        if re.search(pattern, func_content, re.MULTILINE):
            return False, violation_type

    # If we can't determine, assume it's okay
    return True, ""


def check_file(file_path: Path) -> List[str]:
    """Check a file for response envelope violations."""
    violations = []

    with open(file_path, 'r') as f:
        content = f.read()

    handlers = extract_route_handlers(content)

    for route, func_name, func_content in handlers:
        # Skip exception routes
        if is_exception_route(route):
            continue

        uses_envelope, violation_type = check_response_format(func_content)

        if not uses_envelope:
            violations.append(
                f"Route: {route}\n"
                f"  Function: {func_name}\n"
                f"  File: {file_path.name}\n"
                f"  Issue: {violation_type}\n"
                f"  → Should use standard response envelope\n"
                f"  → Wrap in ResponseEnvelope(data=..., meta=...)"
            )

    return violations


def main():
    """Main entry point."""
    backend_path = Path(__file__).parent.parent.parent / "backend" / "app"

    print("API-002: Response Envelope Consistency Check")
    print("=" * 50)

    all_violations = []
    files_checked = 0

    # Check API routes
    api_path = backend_path / "api"
    if api_path.exists():
        for py_file in api_path.glob("*.py"):
            # Skip __init__.py
            if py_file.name == '__init__.py':
                continue

            files_checked += 1
            violations = check_file(py_file)
            all_violations.extend(violations)

    print(f"Files checked: {files_checked}")
    print(f"Violations found: {len(all_violations)}")
    print()

    if all_violations:
        print("VIOLATIONS:")
        print("-" * 50)
        for v in all_violations:
            print(v)
            print()

        print("\nAll API responses should use standard envelope!")
        print("\nStandard format:")
        print("  {")
        print('    "success": true,')
        print('    "data": { ... },')
        print('    "meta": {')
        print('      "timestamp": "...",')
        print('      "request_id": "..."')
        print("    }")
        print("  }")
        print()
        print("Benefits:")
        print("  - Consistent error handling")
        print("  - Metadata for debugging")
        print("  - Pagination support")
        print("  - Client SDK simplicity")
        sys.exit(1)
    else:
        print("✓ All API endpoints use standard response envelopes")
        sys.exit(0)


if __name__ == "__main__":
    main()
