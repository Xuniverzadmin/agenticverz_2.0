#!/usr/bin/env python3
"""
Auth Invariant Scanner — Mechanical Enforcement of AUTH_DESIGN.md

This scanner enforces the authentication design invariants.
It produces HARD FAILURES only. No warnings. No overrides.

If this scanner fails, the codebase contains invalid auth design.

Usage:
    python scripts/ops/auth_invariant_scanner.py [--ci]

Exit codes:
    0 = No violations
    1 = Violations found (blocks commit/merge)

Reference: docs/AUTH_DESIGN.md
"""

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

# =============================================================================
# CONFIGURATION
# =============================================================================

REPO_ROOT = Path(__file__).parent.parent.parent

# Directories to scan
SCAN_DIRS = [
    REPO_ROOT / "backend",
    REPO_ROOT / "website",
    REPO_ROOT / "scripts",
    REPO_ROOT / "docs",
]

# File extensions to scan
CODE_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".yaml", ".yml", ".md", ".sh", ".env"}

# Files/directories to skip
SKIP_PATTERNS = [
    "__pycache__",
    "node_modules",
    ".git",
    "dist",
    "build",
    ".venv",
    "venv",
    # The scanner itself and the design doc are exempt
    "auth_invariant_scanner.py",
    "AUTH_DESIGN.md",
    # Archive contains legacy docs intentionally preserved for history
    "docs/archive",
    "legacy-auth",
]

# =============================================================================
# VIOLATION DEFINITIONS
# =============================================================================

@dataclass
class Violation:
    """A detected invariant violation."""
    rule_id: str
    file: Path
    line: int
    content: str
    message: str


# Patterns that indicate violations
# Format: (rule_id, regex_pattern, message)
FORBIDDEN_PATTERNS = [
    # FORBIDDEN-001: CONSOLE_JWT_SECRET
    (
        "FORBIDDEN-001",
        r"CONSOLE_JWT_SECRET",
        "CONSOLE_JWT_SECRET is forbidden. Console JWT auth is not valid.",
    ),
    # FORBIDDEN-002: AuthSource.CONSOLE
    (
        "FORBIDDEN-002",
        r"AuthSource\.CONSOLE",
        "AuthSource.CONSOLE is forbidden. No console auth source exists.",
    ),
    # FORBIDDEN-003: HS256 for human auth (console JWT)
    # Note: HS256 for dev tokens in test helpers is acceptable
    # Only flags HS256 in console/human auth contexts
    (
        "FORBIDDEN-003",
        r"console.*HS256|human.*HS256|CONSOLE_JWT.*HS256|user.*jwt.*HS256",
        "HS256 JWT for human console auth is forbidden. Humans use Clerk (RS256).",
    ),
    # FORBIDDEN-004: permissions=["*"] for humans
    (
        "FORBIDDEN-004",
        r"permissions\s*=\s*\[\s*[\"']\*[\"']\s*\]",
        "Wildcard permissions for humans is forbidden. Permissions derive from roles.",
    ),
    # FORBIDDEN-005: Tenant fallback to "default"
    (
        "FORBIDDEN-005",
        r"(?:tenant_id|org_id).*(?:or|if.*else|\?\?).*[\"']default[\"']",
        "Tenant fallback to 'default' is forbidden. Missing tenant is a hard failure.",
    ),
    # FORBIDDEN-006: Issuer routing for agenticverz-console
    (
        "FORBIDDEN-006",
        r"[\"']agenticverz-console[\"']",
        "Console issuer routing is forbidden. Only Clerk issuers are valid.",
    ),
    # FORBIDDEN-007: stub_ AUTH token handling
    # Note: This pattern targets stub AUTH tokens specifically, not all stub_ prefixes.
    # Legitimate uses of stub_ include: golden file names, test message IDs, etc.
    # Auth stub tokens look like: stub_admin_tenant, stub_developer_tenant, etc.
    (
        "FORBIDDEN-007",
        r"stub_.*token|token.*startswith.*[\"']stub_[\"']|stub_(admin|developer|viewer|machine|user|operator)_",
        "Stub auth tokens are forbidden. No stub authentication exists.",
    ),
    # FORBIDDEN-008: AUTH_STUB_ENABLED
    (
        "FORBIDDEN-008",
        r"AUTH_STUB_ENABLED",
        "AUTH_STUB_ENABLED is forbidden. Stub authentication does not exist.",
    ),
    # FORBIDDEN-009: AUTH_CONSOLE_ENABLED
    (
        "FORBIDDEN-009",
        r"AUTH_CONSOLE_ENABLED",
        "AUTH_CONSOLE_ENABLED is forbidden. Console authentication does not exist.",
    ),
    # FORBIDDEN-010: Auth grace period for missing issuer
    # Note: Excludes "No grace" / "no fallback" (correct behavior)
    # Note: Excludes "webhook" grace period (different context - key rotation)
    (
        "FORBIDDEN-010",
        r"(?<!no\s)(?<!No\s)(?<!webhook\s)(?<!key\s)auth.*grace[_\s]*period|console.*grace[_\s]*period|issuer.*grace[_\s]*period|AUTH_CONSOLE_ALLOW_MISSING_ISS",
        "Auth grace period for missing issuer is forbidden. Unknown issuer is rejection.",
    ),
    # Additional: CONSOLE_TOKEN_ISSUER constant
    (
        "FORBIDDEN-006-B",
        r"CONSOLE_TOKEN_ISSUER",
        "CONSOLE_TOKEN_ISSUER constant is forbidden. Console auth does not exist.",
    ),
    # Additional: _authenticate_console function
    (
        "FORBIDDEN-002-B",
        r"_authenticate_console",
        "_authenticate_console function is forbidden. Console auth does not exist.",
    ),
    # Additional: AUTH_CONSOLE_ALLOW_MISSING_ISS
    (
        "FORBIDDEN-010-B",
        r"AUTH_CONSOLE_ALLOW_MISSING_ISS",
        "AUTH_CONSOLE_ALLOW_MISSING_ISS is forbidden. No grace period exists.",
    ),
    # Additional: record_console_grace_period
    (
        "FORBIDDEN-010-C",
        r"record_console_grace_period",
        "Console grace period metrics are forbidden. No grace period exists.",
    ),
    # Additional: DEV_LOGIN_PASSWORD (console auth path)
    (
        "FORBIDDEN-001-B",
        r"DEV_LOGIN_PASSWORD",
        "DEV_LOGIN_PASSWORD is forbidden. Password login issues console JWTs.",
    ),
    # Additional: parse_stub_token
    (
        "FORBIDDEN-007-B",
        r"parse_stub_token",
        "parse_stub_token is forbidden. Stub tokens do not exist.",
    ),
]


# =============================================================================
# SCANNER LOGIC
# =============================================================================


def should_skip(path: Path) -> bool:
    """Check if path should be skipped."""
    path_str = str(path)
    for pattern in SKIP_PATTERNS:
        if pattern in path_str:
            return True
    return False


def scan_file(file_path: Path) -> List[Violation]:
    """Scan a single file for violations."""
    violations = []

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return violations

    lines = content.splitlines()

    for line_num, line in enumerate(lines, start=1):
        for rule_id, pattern, message in FORBIDDEN_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                violations.append(Violation(
                    rule_id=rule_id,
                    file=file_path,
                    line=line_num,
                    content=line.strip()[:100],
                    message=message,
                ))

    return violations


def scan_directory(directory: Path) -> List[Violation]:
    """Recursively scan a directory for violations."""
    violations = []

    if not directory.exists():
        return violations

    for path in directory.rglob("*"):
        if path.is_file() and path.suffix in CODE_EXTENSIONS:
            if not should_skip(path):
                violations.extend(scan_file(path))

    return violations


def format_violation(v: Violation, repo_root: Path) -> str:
    """Format a violation for output."""
    rel_path = v.file.relative_to(repo_root) if v.file.is_relative_to(repo_root) else v.file
    return f"""
VIOLATION: {v.rule_id}
  File: {rel_path}:{v.line}
  Rule: {v.message}
  Code: {v.content}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Auth Invariant Scanner")
    parser.add_argument("--ci", action="store_true", help="CI mode (exit code only)")
    parser.add_argument("--files", nargs="*", help="Specific files to scan")
    args = parser.parse_args()

    print("=" * 70)
    print("AUTH INVARIANT SCANNER")
    print("Enforcing: docs/AUTH_DESIGN.md")
    print("=" * 70)

    all_violations: List[Violation] = []

    if args.files:
        # Scan specific files (for pre-commit)
        for file_path in args.files:
            path = Path(file_path)
            if path.exists() and path.suffix in CODE_EXTENSIONS:
                if not should_skip(path):
                    all_violations.extend(scan_file(path))
    else:
        # Scan all directories
        for scan_dir in SCAN_DIRS:
            all_violations.extend(scan_directory(scan_dir))

    # Report results
    if all_violations:
        print(f"\nFOUND {len(all_violations)} VIOLATION(S)\n")

        # Group by rule
        by_rule = {}
        for v in all_violations:
            if v.rule_id not in by_rule:
                by_rule[v.rule_id] = []
            by_rule[v.rule_id].append(v)

        for rule_id in sorted(by_rule.keys()):
            print(f"\n--- {rule_id} ({len(by_rule[rule_id])} occurrences) ---")
            for v in by_rule[rule_id]:
                print(format_violation(v, REPO_ROOT))

        print("=" * 70)
        print("SCANNER FAILED")
        print("The codebase violates AUTH_DESIGN.md invariants.")
        print("Delete the forbidden patterns before proceeding.")
        print("=" * 70)
        return 1
    else:
        print("\nNo violations found.")
        print("=" * 70)
        print("SCANNER PASSED")
        print("=" * 70)
        return 0


if __name__ == "__main__":
    sys.exit(main())
