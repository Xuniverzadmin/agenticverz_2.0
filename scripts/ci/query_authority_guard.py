#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci | manual
#   Execution: sync
# Role: Validate query_authority on all panels in UI projection
# Reference: PIN-390 (Four-Console Query Authority Model)
"""
Query Authority CI Guard

Validates that every panel in the UI projection has a valid `query_authority`
field conforming to the four-console authority model (PIN-390).

Core Invariants:
    1. Every panel MUST have query_authority
    2. query_authority.level MUST be valid enum
    3. query_authority.allow_in MUST have customer and founder
    4. SYNTHETIC is NEVER allowed in production
    5. INTERNAL is never projection-exposed
    6. Founder ≠ god mode (still has restrictions)

Exit Codes:
    0 - All validations passed
    1 - Query authority violations detected
    2 - File not found or invalid JSON

Usage:
    python3 scripts/ci/query_authority_guard.py
    python3 scripts/ci/query_authority_guard.py --verbose
    python3 scripts/ci/query_authority_guard.py --path /custom/path/ui_projection_lock.json
"""

import argparse
import json
import sys
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent.parent
DEFAULT_PROJECTION_PATH = REPO_ROOT / "design/l2_1/ui_contract/ui_projection_lock.json"
SCHEMA_PATH = REPO_ROOT / "docs/schemas/query_authority_schema.json"

# Contract version this guard enforces
GUARD_VERSION = "query_authority@1.0"

# Valid authority levels (from schema)
VALID_LEVELS = {"USER", "SYSTEM", "SYNTHETIC", "INTERNAL"}

# Valid failure modes (from schema)
VALID_FAILURE_MODES = {"HIDE", "DISABLE", "EXPLAIN"}


# =============================================================================
# FOUR-CONSOLE AUTHORITY MATRIX (PIN-390)
# =============================================================================

# Hardcoded matrix - this is LAW, not configuration
AUTHORITY_MATRIX = {
    "customer": {
        "preflight": {
            "USER": True,
            "SYSTEM": False,
            "SYNTHETIC": False,
            "INTERNAL": False,
        },
        "production": {
            "USER": True,
            "SYSTEM": False,
            "SYNTHETIC": False,
            "INTERNAL": False,
        },
    },
    "founder": {
        "preflight": {
            "USER": True,
            "SYSTEM": True,
            "SYNTHETIC": True,
            "INTERNAL": False,
        },
        "production": {
            "USER": True,
            "SYSTEM": True,
            "SYNTHETIC": False,
            "INTERNAL": False,
        },
    },
}

# Fail-closed default (when authority is unknown)
FAIL_CLOSED_DEFAULT = {
    "level": "SYSTEM",
    "requires": {"permissions": ["UNKNOWN"]},
    "allow_in": {
        "customer": {"preflight": False, "production": False},
        "founder": {"preflight": False, "production": False},
    },
    "failure_mode": "HIDE",
}


# =============================================================================
# VALIDATION RULES
# =============================================================================


class QueryAuthorityGuard:
    """Validates query_authority on all panels."""

    def __init__(self, projection: dict, verbose: bool = False):
        self.projection = projection
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
        print("Query Authority CI Guard (PIN-390)")
        print("=" * 60)

        self._validate_contract_declaration()
        self._validate_all_panels_have_authority()
        self._validate_authority_schema()
        self._validate_hard_invariants()
        self._validate_matrix_compliance()
        self._emit_authority_summary()

        # Summary
        print()
        print("=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Errors:   {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")

        if self.errors:
            print("\nERRORS:")
            for err in self.errors:
                print(f"  ✗ {err}")

        if self.warnings:
            print("\nWARNINGS:")
            for warn in self.warnings:
                print(f"  ⚠ {warn}")

        if not self.errors:
            print("\n✓ All query authority validations PASSED")
            return True
        else:
            print("\n✗ Query authority validation FAILED")
            return False

    def _validate_contract_declaration(self):
        """Check that _contract declares query_authority requirement."""
        print("\n[1] Validating contract declaration...")

        contract = self.projection.get("_contract", {})

        # Check if query_authority is declared in contract
        if "query_authority_required" not in contract:
            self.warn(
                "_contract does not declare query_authority_required - adding enforcement"
            )
        elif contract.get("query_authority_required") is not True:
            self.error("_contract.query_authority_required must be true")
        else:
            self.ok("_contract.query_authority_required: true")

    def _validate_all_panels_have_authority(self):
        """Ensure every panel has query_authority field."""
        print("\n[2] Validating panel query_authority presence...")

        panels_with_authority = 0
        panels_without_authority = 0
        total_panels = 0

        for domain in self.projection.get("domains", []):
            for panel in domain.get("panels", []):
                total_panels += 1
                panel_id = panel.get("panel_id", f"unknown-{total_panels}")

                if "query_authority" not in panel:
                    panels_without_authority += 1
                    self.error(f"Panel {panel_id} missing query_authority (INVALID)")
                else:
                    panels_with_authority += 1

        if panels_without_authority == 0:
            self.ok(f"All {total_panels} panels have query_authority")
        else:
            self.error(
                f"{panels_without_authority}/{total_panels} panels missing query_authority"
            )

    def _validate_authority_schema(self):
        """Validate each query_authority conforms to schema."""
        print("\n[3] Validating query_authority schema compliance...")

        valid_count = 0
        invalid_count = 0

        for domain in self.projection.get("domains", []):
            for panel in domain.get("panels", []):
                panel_id = panel.get("panel_id", "unknown")
                qa = panel.get("query_authority")

                if not qa:
                    continue  # Already reported in previous check

                errors = self._validate_single_authority(qa, panel_id)
                if errors:
                    invalid_count += 1
                    for err in errors:
                        self.error(err)
                else:
                    valid_count += 1

        if invalid_count == 0:
            self.ok(f"All {valid_count} query_authority blocks are schema-valid")
        else:
            self.error(f"{invalid_count} panels have invalid query_authority schema")

    def _validate_single_authority(self, qa: dict, panel_id: str) -> list[str]:
        """Validate a single query_authority block. Returns list of errors."""
        errors = []

        # Required fields
        required = ["level", "requires", "allow_in", "failure_mode"]
        for field in required:
            if field not in qa:
                errors.append(
                    f"Panel {panel_id}: query_authority missing required field '{field}'"
                )

        # Validate level enum
        level = qa.get("level")
        if level and level not in VALID_LEVELS:
            errors.append(
                f"Panel {panel_id}: invalid level '{level}', must be one of {VALID_LEVELS}"
            )

        # Validate failure_mode enum
        fm = qa.get("failure_mode")
        if fm and fm not in VALID_FAILURE_MODES:
            errors.append(
                f"Panel {panel_id}: invalid failure_mode '{fm}', must be one of {VALID_FAILURE_MODES}"
            )

        # Validate requires.permissions
        requires = qa.get("requires", {})
        if not requires.get("permissions"):
            errors.append(
                f"Panel {panel_id}: query_authority.requires.permissions must be non-empty"
            )

        # Validate allow_in structure
        allow_in = qa.get("allow_in", {})
        for console in ["customer", "founder"]:
            if console not in allow_in:
                errors.append(
                    f"Panel {panel_id}: query_authority.allow_in missing '{console}'"
                )
            else:
                console_cfg = allow_in[console]
                for env in ["preflight", "production"]:
                    if env not in console_cfg:
                        errors.append(
                            f"Panel {panel_id}: allow_in.{console} missing '{env}'"
                        )
                    elif not isinstance(console_cfg.get(env), bool):
                        errors.append(
                            f"Panel {panel_id}: allow_in.{console}.{env} must be boolean"
                        )

        return errors

    def _validate_hard_invariants(self):
        """Validate the three hard invariants from PIN-390."""
        print("\n[4] Validating hard invariants...")

        # INVARIANT 1: SYNTHETIC is NEVER allowed in production
        # INVARIANT 2: INTERNAL is never projection-exposed
        # INVARIANT 3: Founder ≠ god mode (checked via matrix compliance)

        synthetic_in_prod = []
        internal_exposed = []

        for domain in self.projection.get("domains", []):
            for panel in domain.get("panels", []):
                panel_id = panel.get("panel_id", "unknown")
                qa = panel.get("query_authority", {})
                level = qa.get("level")
                allow_in = qa.get("allow_in", {})

                # Check SYNTHETIC in production
                if level == "SYNTHETIC":
                    for console in ["customer", "founder"]:
                        if allow_in.get(console, {}).get("production") is True:
                            synthetic_in_prod.append(panel_id)

                # Check INTERNAL exposed
                if level == "INTERNAL":
                    # INTERNAL should never be in projection at all
                    # But if it is, it must be fully hidden
                    any_allowed = False
                    for console in ["customer", "founder"]:
                        for env in ["preflight", "production"]:
                            if allow_in.get(console, {}).get(env) is True:
                                any_allowed = True
                    if any_allowed:
                        internal_exposed.append(panel_id)

        # Report invariant violations
        if synthetic_in_prod:
            for pid in synthetic_in_prod:
                self.error(f"HARD INVARIANT VIOLATION: SYNTHETIC in production - {pid}")
        else:
            self.ok("Invariant 1: No SYNTHETIC in production")

        if internal_exposed:
            for pid in internal_exposed:
                self.error(
                    f"HARD INVARIANT VIOLATION: INTERNAL projection-exposed - {pid}"
                )
        else:
            self.ok("Invariant 2: No INTERNAL projection-exposed")

    def _validate_matrix_compliance(self):
        """Validate allow_in values match the authority matrix."""
        print("\n[5] Validating authority matrix compliance...")

        matrix_violations = []

        for domain in self.projection.get("domains", []):
            for panel in domain.get("panels", []):
                panel_id = panel.get("panel_id", "unknown")
                qa = panel.get("query_authority", {})
                level = qa.get("level")
                allow_in = qa.get("allow_in", {})

                if not level or level not in VALID_LEVELS:
                    continue  # Already reported

                # Check each console/env combination
                for console in ["customer", "founder"]:
                    for env in ["preflight", "production"]:
                        declared = allow_in.get(console, {}).get(env)
                        expected_allowed = (
                            AUTHORITY_MATRIX.get(console, {})
                            .get(env, {})
                            .get(level, False)
                        )

                        # If declared as allowed but matrix says no
                        if declared is True and not expected_allowed:
                            matrix_violations.append(
                                f"Panel {panel_id}: {level} cannot be allowed in {console}/{env} per matrix"
                            )

        if matrix_violations:
            for v in matrix_violations:
                self.error(f"MATRIX VIOLATION: {v}")
        else:
            self.ok("All panels comply with four-console authority matrix")

    def _emit_authority_summary(self):
        """Emit summary statistics about authority usage."""
        print("\n[6] Authority usage summary...")

        level_counts: dict[str, int] = {}
        failure_mode_counts: dict[str, int] = {}

        for domain in self.projection.get("domains", []):
            for panel in domain.get("panels", []):
                qa = panel.get("query_authority", {})

                level = qa.get("level")
                if level:
                    level_counts[level] = level_counts.get(level, 0) + 1

                fm = qa.get("failure_mode")
                if fm:
                    failure_mode_counts[fm] = failure_mode_counts.get(fm, 0) + 1

        print(f"  Authority levels: {level_counts}")
        print(f"  Failure modes: {failure_mode_counts}")


# =============================================================================
# MAIN
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Validate query_authority on all panels (PIN-390)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Query Authority Guard Validations:
  1. Contract declaration - query_authority_required in _contract
  2. Presence check - every panel has query_authority
  3. Schema compliance - all fields valid per schema
  4. Hard invariants - SYNTHETIC/INTERNAL rules
  5. Matrix compliance - allow_in matches four-console matrix

Exit Codes:
  0 - All validations passed
  1 - Query authority violations detected
  2 - File not found or invalid JSON

Reference:
  PIN-390: Four-Console Query Authority Model
  Schema: docs/schemas/query_authority_schema.json
  Governance: docs/governance/QUERY_AUTHORITY_MODEL.md
        """,
    )

    parser.add_argument(
        "--path",
        type=Path,
        default=DEFAULT_PROJECTION_PATH,
        help=f"Path to projection file (default: {DEFAULT_PROJECTION_PATH})",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed validation output",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )

    args = parser.parse_args()

    # Check if projection exists
    if not args.path.exists():
        print(f"ERROR: Projection file not found: {args.path}")
        print()
        print("This guard requires the UI projection file to exist.")
        print("Run the L2 pipeline first:")
        print("  ./scripts/tools/run_l2_pipeline.sh")
        sys.exit(2)

    # Load projection
    try:
        projection = json.loads(args.path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in projection file: {e}")
        sys.exit(2)

    # Validate
    guard = QueryAuthorityGuard(projection, verbose=args.verbose)
    passed = guard.validate_all()

    # Strict mode: warnings are errors
    if args.strict and guard.warnings:
        print(f"\n--strict mode: {len(guard.warnings)} warnings treated as errors")
        passed = False

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
