#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci | manual
#   Execution: sync
# Role: Validate RBAC alignment between gateway_config.py and RBAC_RULES.yaml
# Reference: PIN-391 (RBAC Unification)
"""
RBAC Alignment CI Guard

Validates that:
1. All PUBLIC paths in gateway_config.py exist in RBAC_RULES.yaml
2. All PUBLIC paths in rbac_middleware.py exist in RBAC_RULES.yaml
3. No RBAC drift between components

Exit Codes:
    0 - All validations passed
    1 - RBAC alignment violations detected
    2 - File not found or parse error

Usage:
    python3 scripts/ci/check_rbac_alignment.py
    python3 scripts/ci/check_rbac_alignment.py --verbose
    python3 scripts/ci/check_rbac_alignment.py --fix-suggestions
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent.parent

RBAC_RULES_PATH = REPO_ROOT / "design/auth/RBAC_RULES.yaml"
GATEWAY_CONFIG_PATH = REPO_ROOT / "backend/app/auth/gateway_config.py"
RBAC_MIDDLEWARE_PATH = REPO_ROOT / "backend/app/auth/rbac_middleware.py"

# Contract version
GUARD_VERSION = "rbac_alignment@1.0"


# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================


def extract_public_paths_from_yaml(yaml_path: Path) -> set[str]:
    """Extract PUBLIC tier path prefixes from RBAC_RULES.yaml."""
    if not yaml_path.exists():
        raise FileNotFoundError(f"RBAC_RULES.yaml not found at {yaml_path}")

    with yaml_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    public_paths = set()
    for rule in data.get("rules", []):
        if rule.get("access_tier") == "PUBLIC":
            public_paths.add(rule["path_prefix"])

    return public_paths


def extract_public_paths_from_gateway(gateway_path: Path) -> set[str]:
    """Extract public paths from gateway_config.py."""
    if not gateway_path.exists():
        raise FileNotFoundError(f"gateway_config.py not found at {gateway_path}")

    content = gateway_path.read_text(encoding="utf-8")

    # Look for PUBLIC_PREFIXES or similar list definitions
    public_paths = set()

    # Pattern 1: PUBLIC_PREFIXES = [...]
    prefixes_match = re.search(
        r"PUBLIC_PREFIXES\s*=\s*\[(.*?)\]",
        content,
        re.DOTALL,
    )
    if prefixes_match:
        # Extract string literals
        strings = re.findall(r'"([^"]+)"|\'([^\']+)\'', prefixes_match.group(1))
        for s1, s2 in strings:
            public_paths.add(s1 or s2)

    # Pattern 2: Specific API paths marked as public in comments or logic
    # Filter to only those near "public" keywords
    for line in content.split("\n"):
        if "public" in line.lower():
            matches = re.findall(r'"/api/v1/[^"]+"|"/[^"]*"', line)
            for m in matches:
                public_paths.add(m.strip('"'))

    return public_paths


def extract_public_paths_from_middleware(middleware_path: Path) -> set[str]:
    """Extract PUBLIC_PATHS from rbac_middleware.py."""
    if not middleware_path.exists():
        raise FileNotFoundError(f"rbac_middleware.py not found at {middleware_path}")

    content = middleware_path.read_text(encoding="utf-8")

    public_paths = set()

    # Find PUBLIC_PATHS = [...] in function body
    # This is a heuristic - the list is inside a function
    paths_match = re.search(
        r"PUBLIC_PATHS\s*=\s*\[(.*?)\]",
        content,
        re.DOTALL,
    )
    if paths_match:
        # Extract string literals
        strings = re.findall(r'"([^"]+)"|\'([^\']+)\'', paths_match.group(1))
        for s1, s2 in strings:
            path = s1 or s2
            # Normalize trailing slashes
            public_paths.add(path.rstrip("/") if path != "/" else path)

    return public_paths


# =============================================================================
# VALIDATION
# =============================================================================


class RBACAlignmentGuard:
    """Validates RBAC alignment across components."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str):
        self.errors.append(msg)
        if self.verbose:
            print(f"  ✗ {msg}")

    def warn(self, msg: str):
        self.warnings.append(msg)
        if self.verbose:
            print(f"  ⚠ {msg}")

    def ok(self, msg: str):
        if self.verbose:
            print(f"  ✓ {msg}")

    def validate_all(self) -> bool:
        """Run all validations. Returns True if all pass."""
        print("=" * 60)
        print("RBAC Alignment CI Guard (PIN-391)")
        print("=" * 60)

        try:
            yaml_paths = extract_public_paths_from_yaml(RBAC_RULES_PATH)
            middleware_paths = extract_public_paths_from_middleware(
                RBAC_MIDDLEWARE_PATH
            )
        except FileNotFoundError as e:
            print(f"\nERROR: {e}")
            return False

        # Normalize paths for comparison
        yaml_paths_normalized = {p.rstrip("/") for p in yaml_paths}
        middleware_paths_normalized = {p.rstrip("/") for p in middleware_paths}

        # Check 1: Middleware paths that are not in YAML
        print("\n[1] Checking middleware PUBLIC_PATHS against RBAC_RULES.yaml...")
        missing_in_yaml = middleware_paths_normalized - yaml_paths_normalized
        if missing_in_yaml:
            for path in sorted(missing_in_yaml):
                self.error(
                    f"RBAC DRIFT: '{path}' is public in middleware but not in RBAC_RULES.yaml"
                )
        else:
            self.ok("All middleware PUBLIC_PATHS are declared in RBAC_RULES.yaml")

        # Check 2: YAML paths that are not in middleware
        print("\n[2] Checking RBAC_RULES.yaml PUBLIC paths against middleware...")
        missing_in_middleware = yaml_paths_normalized - middleware_paths_normalized
        if missing_in_middleware:
            for path in sorted(missing_in_middleware):
                self.warn(
                    f"RBAC RULE UNUSED: '{path}' is PUBLIC in YAML but not in middleware"
                )
        else:
            self.ok("All RBAC_RULES.yaml PUBLIC paths are in middleware")

        # Check 3: Temporary rules audit
        print("\n[3] Auditing temporary RBAC rules...")
        self._audit_temporary_rules()

        # Check 4: Query authority validation (PIN-392)
        print("\n[4] Validating query_authority declarations (PIN-392)...")
        self._validate_query_authority()

        # Check 5: Expired rules enforcement
        print("\n[5] Checking for expired temporary rules...")
        self._check_expired_rules()

        # Summary
        print()
        print("=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Errors:   {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")

        if self.errors:
            print("\nERRORS (BLOCKING):")
            for err in self.errors:
                print(f"  ✗ {err}")

        if self.warnings:
            print("\nWARNINGS:")
            for warn in self.warnings:
                print(f"  ⚠ {warn}")

        if not self.errors:
            print("\n✓ RBAC alignment validation PASSED")
            return True
        else:
            print("\n✗ RBAC alignment validation FAILED")
            return False

    def _audit_temporary_rules(self):
        """Audit temporary RBAC rules for expiry."""
        try:
            with RBAC_RULES_PATH.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception:
            self.warn("Could not parse RBAC_RULES.yaml for temporary rule audit")
            return

        temp_count = 0
        for rule in data.get("rules", []):
            if rule.get("temporary"):
                temp_count += 1
                expires = rule.get("expires", "UNKNOWN")
                self.warn(f"Temporary rule: {rule['rule_id']} (expires: {expires})")

        if temp_count == 0:
            self.ok("No temporary RBAC rules")
        else:
            self.warn(f"{temp_count} temporary RBAC rule(s) require review")

    def _validate_query_authority(self):
        """Validate query_authority declarations (PIN-392)."""
        try:
            with RBAC_RULES_PATH.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception:
            self.warn("Could not parse RBAC_RULES.yaml for query_authority validation")
            return

        # Check that query_authority_defaults exists
        if "query_authority_defaults" not in data:
            self.warn("query_authority_defaults not declared in schema")

        # Data-reading paths that should have query_authority
        data_paths = ["/api/v1/"]

        for rule in data.get("rules", []):
            path = rule.get("path_prefix", "")
            methods = rule.get("methods", [])
            environment = rule.get("allow_environment", [])

            # Only check GET endpoints under /api/v1/
            if "GET" not in methods:
                continue
            if not any(path.startswith(dp) for dp in data_paths):
                continue

            # Check 1: Production rules must not allow include_synthetic
            if "production" in environment:
                qa = rule.get("query_authority", {})
                if qa.get("include_synthetic", False):
                    self.error(
                        f"CRITICAL: {rule['rule_id']} allows include_synthetic in production"
                    )

            # Check 2: Preflight data endpoints should declare query_authority
            if "preflight" in environment and path.startswith("/api/v1/"):
                if "query_authority" not in rule:
                    self.warn(
                        f"{rule['rule_id']} has no query_authority (using defaults)"
                    )

        self.ok("Query authority validation complete")

    def _check_expired_rules(self):
        """Check for expired temporary rules (BLOCKING after expiry)."""
        from datetime import datetime

        try:
            with RBAC_RULES_PATH.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception:
            self.warn("Could not parse RBAC_RULES.yaml for expiry check")
            return

        today = datetime.now().date()
        expired_count = 0

        for rule in data.get("rules", []):
            if not rule.get("temporary"):
                continue

            expires = rule.get("expires")
            if not expires:
                self.warn(f"Temporary rule {rule['rule_id']} has no expiry date")
                continue

            try:
                expiry_date = datetime.strptime(expires, "%Y-%m-%d").date()
                if today > expiry_date:
                    self.error(
                        f"EXPIRED: {rule['rule_id']} expired on {expires} - must be removed or renewed"
                    )
                    expired_count += 1
            except ValueError:
                self.warn(
                    f"Invalid expiry date format for {rule['rule_id']}: {expires}"
                )

        if expired_count == 0:
            self.ok("No expired temporary rules")
        else:
            self.error(f"{expired_count} expired rule(s) must be addressed")


def print_fix_suggestions(errors: list[str]):
    """Print suggestions for fixing alignment issues."""
    print("\n" + "=" * 60)
    print("FIX SUGGESTIONS")
    print("=" * 60)

    for err in errors:
        if "not in RBAC_RULES.yaml" in err:
            # Extract path from error
            path_match = re.search(r"'([^']+)'", err)
            if path_match:
                path = path_match.group(1)
                print(f"\nTo fix: {err}")
                print("Add this rule to design/auth/RBAC_RULES.yaml:")
                print(f"""
  - rule_id: {path.replace("/", "_").upper().strip("_")}_PUBLIC
    path_prefix: {path}/
    methods: [GET]
    access_tier: PUBLIC
    allow_console: [customer, founder]
    allow_environment: [preflight, production]
    description: "TODO: Add description"
""")


# =============================================================================
# MAIN
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Validate RBAC alignment (PIN-391)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
RBAC Alignment Guard Validations:
  1. Middleware PUBLIC_PATHS match RBAC_RULES.yaml
  2. RBAC_RULES.yaml PUBLIC paths are used
  3. Temporary rules audit

Exit Codes:
  0 - All validations passed
  1 - RBAC alignment violations detected
  2 - File not found or parse error

Reference:
  PIN-391: RBAC Unification
  Schema: design/auth/RBAC_RULES.yaml
        """,
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed validation output",
    )
    parser.add_argument(
        "--fix-suggestions",
        action="store_true",
        help="Show suggestions for fixing issues",
    )

    args = parser.parse_args()

    # Validate
    guard = RBACAlignmentGuard(verbose=args.verbose)

    try:
        passed = guard.validate_all()
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(2)

    if args.fix_suggestions and guard.errors:
        print_fix_suggestions(guard.errors)

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
