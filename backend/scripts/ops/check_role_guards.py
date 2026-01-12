#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: PIN-399 Phase-5 Role Guard CI Scanner
# Callers: CI pipeline, pre-commit hooks
# Allowed Imports: None (static analysis only)
# Forbidden Imports: L1, L2, L3, L4, L5, L6
# Reference: PIN-399 Phase-5 (Post-Onboarding Permissions & Roles)

"""
Phase-5 Role Guard CI Scanner

This script FAILS CI if any POST/PUT/PATCH/DELETE endpoint under /api/v1/*
does not have explicit role guard protection.

PIN-399 Phase-5 HARD RULES:
- ROLE-005: Role enforcement never mutates state
- All mutating endpoints MUST have require_role() or require_permission()
- Exceptions must be explicitly allowlisted with documented justification

USAGE
-----
    python scripts/ops/check_role_guards.py [--verbose] [--ci]

EXIT CODES
----------
    0 = All endpoints protected or allowlisted
    1 = Unprotected endpoints found
    2 = Script error

PHILOSOPHY
----------
This is a HARD GATE. Unprotected mutating endpoints are security vulnerabilities.
If an endpoint is public, it must be in the allowlist with documented justification.
"""

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Endpoint:
    """Represents an API endpoint."""

    file: Path
    line_num: int
    method: str  # POST, PUT, PATCH, DELETE
    path: str
    function_name: str
    has_role_guard: bool
    has_permission_guard: bool
    is_allowlisted: bool
    allowlist_reason: Optional[str] = None


@dataclass
class Violation:
    """An unprotected endpoint."""

    endpoint: Endpoint
    reason: str


# Endpoints that are explicitly allowed to be unguarded.
# Each entry MUST have a documented justification.
# Format: (router_file, path_pattern, method) -> reason
ALLOWLIST = {
    # Auth endpoints - authentication happens here, not before
    ("auth.py", "/auth/", "POST"): "Authentication endpoints - auth happens here",
    ("auth.py", "/auth/", "DELETE"): "Logout endpoint - no sensitive data mutation",
    # Health and metrics - monitoring endpoints
    ("health.py", "/health", "GET"): "Health check - public by design",
    ("health.py", "/health", "POST"): "Health ping - public by design",
    # Webhook endpoints - use signature validation instead
    ("webhooks.py", "/webhooks/", "POST"): "Webhook - uses HMAC signature validation",
    # C2 prediction endpoints - machine-to-machine, scoped by API key
    ("c2_prediction.py", "/c2/", "POST"): "C2 - machine context with scope auth",
    ("c2_prediction.py", "/c2/", "PUT"): "C2 - machine context with scope auth",
    # Founder endpoints - use verify_fops_token instead of require_role
    ("founder_onboarding.py", "/founder/", "POST"): "Founder-only - uses verify_fops_token",
}

# Patterns that indicate role protection
ROLE_GUARD_PATTERNS = [
    r"Depends\s*\(\s*require_role\s*\(",
    r"require_role\s*\(",
]

PERMISSION_GUARD_PATTERNS = [
    r"Depends\s*\(\s*require_permission\s*\(",
    r"require_permission\s*\(",
]

# Alternative auth patterns that are acceptable
ALTERNATIVE_AUTH_PATTERNS = [
    r"Depends\s*\(\s*verify_fops_token",  # Founder auth
    r"Depends\s*\(\s*verify_api_key",  # Machine auth (API key)
    r"Depends\s*\(\s*verify_webhook_signature",  # Webhook auth
]

# HTTP methods that mutate state
MUTATING_METHODS = {"post", "put", "patch", "delete"}

# Decorator patterns for router methods
ROUTER_DECORATOR_PATTERN = re.compile(
    r'@\s*router\s*\.\s*(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']'
)


def find_api_routers(root: Path, verbose: bool = False) -> list[Path]:
    """Find all API router files."""
    api_dir = root / "app" / "api"
    if not api_dir.exists():
        if verbose:
            print(f"  [WARN] API directory not found: {api_dir}")
        return []

    router_files = list(api_dir.glob("*.py"))
    # Also check subdirectories
    router_files.extend(api_dir.rglob("*.py"))

    # Filter out __init__.py and test files
    router_files = [
        f
        for f in router_files
        if f.name != "__init__.py" and not f.name.startswith("test_")
    ]

    return router_files


def extract_endpoints_from_file(file_path: Path, verbose: bool = False) -> list[Endpoint]:
    """Extract all HTTP endpoints from a router file."""
    endpoints = []

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        if verbose:
            print(f"  [ERROR] Could not read {file_path}: {e}")
        return []

    lines = content.split("\n")

    # Find all router decorators and their functions
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Look for router decorator
        match = ROUTER_DECORATOR_PATTERN.search(stripped)
        if match:
            method = match.group(1).upper()
            path = match.group(2)

            # Get the full decorator block (may span multiple lines)
            decorator_block = stripped
            paren_count = stripped.count("(") - stripped.count(")")
            j = i + 1
            while paren_count > 0 and j < len(lines):
                decorator_block += " " + lines[j].strip()
                paren_count += lines[j].count("(") - lines[j].count(")")
                j += 1

            # Find the function definition
            func_line_num = j
            while j < len(lines) and not lines[j].strip().startswith("async def ") and not lines[j].strip().startswith("def "):
                j += 1

            if j < len(lines):
                func_line = lines[j]
                func_match = re.search(r"(?:async\s+)?def\s+(\w+)", func_line)
                func_name = func_match.group(1) if func_match else "unknown"
                func_line_num = j + 1

                # Get the full function signature (may span multiple lines)
                func_sig = func_line
                paren_count = func_line.count("(") - func_line.count(")")
                k = j + 1
                while paren_count > 0 and k < len(lines):
                    func_sig += " " + lines[k].strip()
                    paren_count += lines[k].count("(") - lines[k].count(")")
                    k += 1

                # Check for guards in decorator block + function signature
                full_context = decorator_block + " " + func_sig

                has_role_guard = any(
                    re.search(pattern, full_context) for pattern in ROLE_GUARD_PATTERNS
                )
                has_permission_guard = any(
                    re.search(pattern, full_context)
                    for pattern in PERMISSION_GUARD_PATTERNS
                )
                has_alt_auth = any(
                    re.search(pattern, full_context)
                    for pattern in ALTERNATIVE_AUTH_PATTERNS
                )

                # Check allowlist
                is_allowlisted = False
                allowlist_reason = None
                file_name = file_path.name
                for (al_file, al_path, al_method), reason in ALLOWLIST.items():
                    if al_file == file_name and al_method == method:
                        if al_path in path or path.startswith(al_path.rstrip("/")):
                            is_allowlisted = True
                            allowlist_reason = reason
                            break

                endpoints.append(
                    Endpoint(
                        file=file_path,
                        line_num=func_line_num,
                        method=method,
                        path=path,
                        function_name=func_name,
                        has_role_guard=has_role_guard,
                        has_permission_guard=has_permission_guard or has_alt_auth,
                        is_allowlisted=is_allowlisted,
                        allowlist_reason=allowlist_reason,
                    )
                )

        i += 1

    return endpoints


def check_endpoint(endpoint: Endpoint) -> Optional[Violation]:
    """Check if an endpoint needs protection and has it."""
    # Only check mutating methods
    if endpoint.method.lower() not in MUTATING_METHODS:
        return None

    # Skip if allowlisted
    if endpoint.is_allowlisted:
        return None

    # Check if protected
    if endpoint.has_role_guard or endpoint.has_permission_guard:
        return None

    # Unprotected mutating endpoint!
    return Violation(
        endpoint=endpoint,
        reason="Mutating endpoint without role/permission guard",
    )


def scan_routers(root: Path, verbose: bool = False) -> tuple[list[Endpoint], list[Violation]]:
    """Scan all router files for unprotected endpoints."""
    all_endpoints = []
    violations = []

    router_files = find_api_routers(root, verbose)

    if verbose:
        print(f"Found {len(router_files)} router files")

    for file_path in router_files:
        if verbose:
            print(f"  Scanning: {file_path.name}")

        endpoints = extract_endpoints_from_file(file_path, verbose)
        all_endpoints.extend(endpoints)

        for endpoint in endpoints:
            violation = check_endpoint(endpoint)
            if violation:
                violations.append(violation)

    return all_endpoints, violations


def print_endpoint_summary(endpoints: list[Endpoint], verbose: bool = False) -> None:
    """Print summary of all scanned endpoints."""
    mutating = [e for e in endpoints if e.method.lower() in MUTATING_METHODS]
    protected = [e for e in mutating if e.has_role_guard or e.has_permission_guard]
    allowlisted = [e for e in mutating if e.is_allowlisted and not (e.has_role_guard or e.has_permission_guard)]

    print(f"\nEndpoint Summary:")
    print(f"  Total endpoints scanned: {len(endpoints)}")
    print(f"  Mutating endpoints (POST/PUT/PATCH/DELETE): {len(mutating)}")
    print(f"  Protected by role/permission guard: {len(protected)}")
    print(f"  Allowlisted (documented exceptions): {len(allowlisted)}")

    if verbose and allowlisted:
        print(f"\n  Allowlisted endpoints:")
        for e in allowlisted:
            print(f"    - {e.method} {e.path} ({e.file.name}:{e.line_num})")
            print(f"      Reason: {e.allowlist_reason}")


def print_violation(v: Violation) -> None:
    """Print a single violation."""
    e = v.endpoint
    print(f"\n{'=' * 70}")
    print(f"UNPROTECTED ENDPOINT: {e.method} {e.path}")
    print(f"{'=' * 70}")
    print(f"File: {e.file}:{e.line_num}")
    print(f"Function: {e.function_name}")
    print(f"\nReason: {v.reason}")
    print(f"\nFix: Add role guard to the endpoint:")
    print(f"    from app.auth.role_guard import require_role")
    print(f"    from app.auth.tenant_roles import TenantRole")
    print(f"")
    print(f"    @router.{e.method.lower()}(\"{e.path}\")")
    print(f"    async def {e.function_name}(")
    print(f"        ...,")
    print(f"        role: TenantRole = Depends(require_role(TenantRole.MEMBER)),")
    print(f"    ):")
    print(f"")
    print(f"Or add to ALLOWLIST in scripts/ops/check_role_guards.py with justification.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check for unprotected mutating API endpoints (PIN-399 Phase-5)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output",
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode - strict output format",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to backend directory (default: current directory)",
    )

    args = parser.parse_args()

    # Determine root path
    root = Path(args.path)
    if not root.exists():
        print(f"ERROR: Path does not exist: {root}")
        return 2

    # If we're in backend, use it directly
    if (root / "app" / "api").exists():
        pass
    elif (root / "backend" / "app" / "api").exists():
        root = root / "backend"
    else:
        print(f"ERROR: Could not find app/api directory in: {root}")
        return 2

    print(f"PIN-399 Phase-5 Role Guard Scanner")
    print(f"Scanning: {root}/app/api/")
    print()

    endpoints, violations = scan_routers(root, args.verbose)

    print_endpoint_summary(endpoints, args.verbose)

    if violations:
        print(f"\n{'#' * 70}")
        print(f"# UNPROTECTED ENDPOINTS FOUND: {len(violations)}")
        print(f"{'#' * 70}")

        for v in violations:
            print_violation(v)

        print(f"\n{'=' * 70}")
        print("SUMMARY")
        print(f"{'=' * 70}")
        print(f"Total violations: {len(violations)}")
        print()
        print("PIN-399 Phase-5 HARD RULES:")
        print("- All POST/PUT/PATCH/DELETE endpoints MUST have role guards")
        print("- Use: Depends(require_role(TenantRole.MEMBER, ...))")
        print("- Or add to ALLOWLIST with documented justification")
        print()
        print("Reference: PIN-399 Phase-5 (Post-Onboarding Permissions & Roles)")

        return 1

    print(f"\n{'=' * 70}")
    print("✅ All mutating endpoints are protected or allowlisted")
    print(f"{'=' * 70}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
