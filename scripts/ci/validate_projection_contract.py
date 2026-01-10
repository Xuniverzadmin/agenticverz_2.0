#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci | manual
#   Execution: sync
# Role: Validate UI projection contract for CI enforcement
# Reference: PIN-387 (Canonical Projection Design)
"""
UI Projection Contract Validator

Validates that the canonical projection file conforms to all contract requirements
established in the AURORA_L2 canonical design (Phases 0-4).

Exit Codes:
    0 - All validations passed
    1 - Contract violations detected
    2 - File not found or invalid JSON

Usage:
    python3 scripts/ci/validate_projection_contract.py
    python3 scripts/ci/validate_projection_contract.py --verbose
    python3 scripts/ci/validate_projection_contract.py --path /custom/path/ui_projection_lock.json
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
PUBLIC_PROJECTION_PATH = REPO_ROOT / "website/app-shell/public/projection/ui_projection_lock.json"

# Contract version this validator enforces
CONTRACT_VERSION = "ui_projection@2.0"

# =============================================================================
# VALIDATION RULES
# =============================================================================

class ContractValidator:
    """Validates projection against canonical contract."""

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
        print("UI Projection Contract Validator")
        print("=" * 60)

        self._validate_meta()
        self._validate_statistics()
        self._validate_contract_block()
        self._validate_domains()
        self._validate_panels()
        self._validate_ordering()
        self._validate_content_blocks()
        self._validate_binding_metadata()
        self._validate_sdsr_traces()

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
            print("\n✓ All contract validations PASSED")
            return True
        else:
            print("\n✗ Contract validation FAILED")
            return False

    def _validate_meta(self):
        """Validate _meta block (Phase 1.1)."""
        print("\n[1] Validating _meta block...")

        meta = self.projection.get("_meta")
        if not meta:
            self.error("Missing _meta block")
            return

        required_fields = [
            "type", "generator", "generator_version", "db_authority",
            "contract_version", "processing_stage", "frozen", "editable"
        ]

        for field in required_fields:
            if field not in meta:
                self.error(f"_meta missing required field: {field}")
            else:
                self.ok(f"_meta.{field} present")

        # Validate specific values
        if meta.get("type") != "ui_projection_lock":
            self.error(f"_meta.type must be 'ui_projection_lock', got: {meta.get('type')}")

        if meta.get("frozen") is not True:
            self.error("_meta.frozen must be true")

        if meta.get("editable") is not False:
            self.error("_meta.editable must be false")

        # DB_AUTHORITY enforcement (Phase 0)
        db_authority = meta.get("db_authority")
        if not db_authority:
            self.error("_meta.db_authority not declared (Phase 0 violation)")
        elif db_authority not in ("neon", "local"):
            self.error(f"_meta.db_authority must be 'neon' or 'local', got: {db_authority}")
        else:
            self.ok(f"_meta.db_authority: {db_authority}")

    def _validate_statistics(self):
        """Validate _statistics block (Phase 1.1 + Phase 4)."""
        print("\n[2] Validating _statistics block...")

        stats = self.projection.get("_statistics")
        if not stats:
            self.error("Missing _statistics block")
            return

        required_fields = [
            "domain_count", "panel_count", "control_count",
            "bound_panels", "draft_panels", "info_panels", "unbound_panels",
            # Phase 4 additions
            "sdsr_trace_count", "panels_with_traces", "unique_scenario_count"
        ]

        for field in required_fields:
            if field not in stats:
                self.error(f"_statistics missing required field: {field}")
            else:
                self.ok(f"_statistics.{field}: {stats[field]}")

        # Cross-validate panel counts
        total_binding = (
            stats.get("bound_panels", 0) +
            stats.get("draft_panels", 0) +
            stats.get("info_panels", 0) +
            stats.get("unbound_panels", 0)
        )
        if total_binding != stats.get("panel_count", 0):
            self.error(f"Binding status counts ({total_binding}) don't sum to panel_count ({stats.get('panel_count')})")

    def _validate_contract_block(self):
        """Validate _contract block (All phases)."""
        print("\n[3] Validating _contract block...")

        contract = self.projection.get("_contract")
        if not contract:
            self.error("Missing _contract block")
            return

        required_true_fields = [
            "renderer_must_consume_only_this_file",
            "no_optional_fields",
            "explicit_ordering_everywhere",
            "all_controls_have_type",
            "all_panels_have_render_mode",
            "all_items_have_visibility",
            "binding_status_required",
            "panel_display_order_required",      # Phase 2
            "topic_display_order_required",      # Phase 2
            "content_blocks_required",           # Phase 3
            "binding_metadata_on_bound_panels",  # Phase 4
            "sdsr_trace_provenance",             # Phase 4
            "ui_must_not_infer",
        ]

        for field in required_true_fields:
            value = contract.get(field)
            if value is not True:
                self.error(f"_contract.{field} must be true, got: {value}")
            else:
                self.ok(f"_contract.{field}: true")

        # Validate ordering semantic
        if contract.get("ordering_semantic") != "numeric_only":
            self.error(f"_contract.ordering_semantic must be 'numeric_only'")

    def _validate_domains(self):
        """Validate domains array structure."""
        print("\n[4] Validating domains structure...")

        domains = self.projection.get("domains")
        if not domains:
            self.error("Missing domains array")
            return

        if not isinstance(domains, list):
            self.error("domains must be an array")
            return

        self.ok(f"Found {len(domains)} domains")

        for i, domain in enumerate(domains):
            if not domain.get("domain"):
                self.error(f"domains[{i}] missing 'domain' name")
            if "order" not in domain:
                self.error(f"domains[{i}] missing 'order'")
            if not domain.get("panels"):
                self.warn(f"domains[{i}] ({domain.get('domain', 'unknown')}) has no panels")

    def _validate_panels(self):
        """Validate all panels have required fields."""
        print("\n[5] Validating panel structure...")

        required_panel_fields = [
            "panel_id", "panel_name", "order", "render_mode", "visibility",
            "enabled", "controls", "control_count", "topic", "topic_id",
            "subdomain", "permissions", "route", "view_type", "binding_status",
            "review_status", "content_blocks",  # Phase 3
            "panel_display_order", "topic_display_order",  # Phase 2
        ]

        total_panels = 0
        panels_missing_fields = 0

        for domain in self.projection.get("domains", []):
            for panel in domain.get("panels", []):
                total_panels += 1
                panel_id = panel.get("panel_id", f"unknown-{total_panels}")

                missing = [f for f in required_panel_fields if f not in panel]
                if missing:
                    panels_missing_fields += 1
                    self.error(f"Panel {panel_id} missing fields: {', '.join(missing)}")

        if panels_missing_fields == 0:
            self.ok(f"All {total_panels} panels have required fields")
        else:
            self.error(f"{panels_missing_fields}/{total_panels} panels missing required fields")

    def _validate_ordering(self):
        """Validate panel_display_order and topic_display_order (Phase 2)."""
        print("\n[6] Validating ordering (Phase 2)...")

        panel_orders = []
        panels_without_order = 0

        for domain in self.projection.get("domains", []):
            for panel in domain.get("panels", []):
                pdo = panel.get("panel_display_order")
                tdo = panel.get("topic_display_order")

                if not isinstance(pdo, int):
                    panels_without_order += 1
                    self.error(f"Panel {panel.get('panel_id')} has non-integer panel_display_order: {pdo}")
                else:
                    panel_orders.append(pdo)

                if not isinstance(tdo, int):
                    self.error(f"Panel {panel.get('panel_id')} has non-integer topic_display_order: {tdo}")

        # Check for duplicate panel_display_order
        if len(panel_orders) != len(set(panel_orders)):
            self.error("Duplicate panel_display_order values detected")
        else:
            self.ok("All panel_display_order values are unique")

        # Check for sequential ordering (0 to N-1)
        if panel_orders:
            expected = set(range(len(panel_orders)))
            actual = set(panel_orders)
            if expected != actual:
                self.warn(f"panel_display_order not strictly sequential (expected 0-{len(panel_orders)-1})")
            else:
                self.ok(f"panel_display_order is sequential (0-{len(panel_orders)-1})")

    def _validate_content_blocks(self):
        """Validate content_blocks structure (Phase 3)."""
        print("\n[7] Validating content_blocks (Phase 3)...")

        panels_with_blocks = 0
        panels_without_blocks = 0
        block_type_counts: dict[str, int] = {}

        for domain in self.projection.get("domains", []):
            for panel in domain.get("panels", []):
                blocks = panel.get("content_blocks", [])

                if not blocks:
                    panels_without_blocks += 1
                    self.error(f"Panel {panel.get('panel_id')} has no content_blocks")
                    continue

                panels_with_blocks += 1

                # Check required block types
                block_types = [b.get("type") for b in blocks]
                for required_type in ["HEADER", "DATA", "FOOTER"]:
                    if required_type not in block_types:
                        self.error(f"Panel {panel.get('panel_id')} missing {required_type} block")

                # Count block types
                for bt in block_types:
                    block_type_counts[bt] = block_type_counts.get(bt, 0) + 1

                # Validate each block has required fields
                for block in blocks:
                    if "type" not in block:
                        self.error(f"Panel {panel.get('panel_id')} has block without type")
                    if "order" not in block:
                        self.error(f"Panel {panel.get('panel_id')} has block without order")
                    if "visibility" not in block:
                        self.error(f"Panel {panel.get('panel_id')} has block without visibility")

        if panels_without_blocks == 0:
            self.ok(f"All {panels_with_blocks} panels have content_blocks")

        self.ok(f"Block types: {block_type_counts}")

    def _validate_binding_metadata(self):
        """Validate binding_metadata on BOUND panels (Phase 4)."""
        print("\n[8] Validating binding_metadata (Phase 4)...")

        bound_panels = 0
        bound_with_metadata = 0

        for domain in self.projection.get("domains", []):
            for panel in domain.get("panels", []):
                if panel.get("binding_status") == "BOUND":
                    bound_panels += 1
                    metadata = panel.get("binding_metadata")

                    if not metadata:
                        self.error(f"BOUND panel {panel.get('panel_id')} missing binding_metadata")
                        continue

                    bound_with_metadata += 1

                    # Check required metadata fields
                    required = ["scenario_ids", "observed_at", "capability_ids", "trace_count", "observed_effects"]
                    for field in required:
                        if field not in metadata:
                            self.error(f"Panel {panel.get('panel_id')} binding_metadata missing: {field}")

        if bound_panels == 0:
            self.warn("No BOUND panels found")
        elif bound_with_metadata == bound_panels:
            self.ok(f"All {bound_panels} BOUND panels have binding_metadata")
        else:
            self.error(f"{bound_with_metadata}/{bound_panels} BOUND panels have binding_metadata")

    def _validate_sdsr_traces(self):
        """Validate SDSR trace statistics (Phase 4)."""
        print("\n[9] Validating SDSR trace provenance (Phase 4)...")

        stats = self.projection.get("_statistics", {})

        # Count actual traces from panels
        actual_trace_count = 0
        actual_panels_with_traces = 0
        actual_scenarios: set[str] = set()

        for domain in self.projection.get("domains", []):
            for panel in domain.get("panels", []):
                metadata = panel.get("binding_metadata")
                if metadata and metadata.get("trace_count", 0) > 0:
                    actual_trace_count += metadata["trace_count"]
                    actual_panels_with_traces += 1
                    for sid in metadata.get("scenario_ids", []):
                        actual_scenarios.add(sid)

        # Cross-validate with statistics
        if stats.get("sdsr_trace_count") != actual_trace_count:
            self.error(f"_statistics.sdsr_trace_count ({stats.get('sdsr_trace_count')}) != actual ({actual_trace_count})")
        else:
            self.ok(f"sdsr_trace_count matches: {actual_trace_count}")

        if stats.get("panels_with_traces") != actual_panels_with_traces:
            self.error(f"_statistics.panels_with_traces ({stats.get('panels_with_traces')}) != actual ({actual_panels_with_traces})")
        else:
            self.ok(f"panels_with_traces matches: {actual_panels_with_traces}")

        if stats.get("unique_scenario_count") != len(actual_scenarios):
            self.error(f"_statistics.unique_scenario_count ({stats.get('unique_scenario_count')}) != actual ({len(actual_scenarios)})")
        else:
            self.ok(f"unique_scenario_count matches: {len(actual_scenarios)}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Validate UI projection contract for CI enforcement",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contract Requirements Validated:
  Phase 0: DB_AUTHORITY enforcement
  Phase 1: Canonical schema (_meta, _statistics, _contract)
  Phase 2: panel_display_order, topic_display_order
  Phase 3: content_blocks structure
  Phase 4: SDSR trace finalization and binding_metadata

Exit Codes:
  0 - All validations passed
  1 - Contract violations detected
  2 - File not found or invalid JSON
        """
    )

    parser.add_argument(
        "--path",
        type=Path,
        default=DEFAULT_PROJECTION_PATH,
        help=f"Path to projection file (default: {DEFAULT_PROJECTION_PATH})",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed validation output",
    )
    parser.add_argument(
        "--check-public",
        action="store_true",
        help="Also validate public/projection copy matches canonical",
    )

    args = parser.parse_args()

    # Load projection
    if not args.path.exists():
        print(f"ERROR: Projection file not found: {args.path}")
        sys.exit(2)

    try:
        projection = json.loads(args.path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in projection file: {e}")
        sys.exit(2)

    # Validate
    validator = ContractValidator(projection, verbose=args.verbose)
    passed = validator.validate_all()

    # Optionally check public copy
    if args.check_public and PUBLIC_PROJECTION_PATH.exists():
        print()
        print("=" * 60)
        print("Checking public projection copy...")
        print("=" * 60)

        try:
            public_projection = json.loads(PUBLIC_PROJECTION_PATH.read_text(encoding="utf-8"))
            if projection == public_projection:
                print("✓ Public projection matches canonical")
            else:
                print("✗ Public projection differs from canonical")
                passed = False
        except Exception as e:
            print(f"✗ Failed to compare public projection: {e}")
            passed = False

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
