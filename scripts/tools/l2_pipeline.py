#!/usr/bin/env python3
"""
================================================================================
DEPRECATED — DO NOT USE
================================================================================

This script is part of the LEGACY L2.1 CSV-based pipeline.
It has been replaced by the AURORA L2 SDSR-driven pipeline.

REPLACEMENT: scripts/tools/run_aurora_l2_pipeline.sh
REFERENCE: design/l2_1/AURORA_L2.md, PIN-370, PIN-379

The new pipeline uses:
- Intent YAMLs (design/l2_1/intents/*.yaml) instead of CSV
- SDSR-driven capability observation
- backend/aurora_l2/compiler.py for projection generation

This file is preserved for historical reference only.
================================================================================
"""
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Status: DEPRECATED (2026-01-14)
# Replacement: scripts/tools/run_aurora_l2_pipeline.sh
# Reference: PIN-349 (UI Contract Generation) - SUPERSEDED by PIN-370
"""
L2 Pipeline — Governed Supertable → UI Contract Pipeline

DEPRECATED: This script is no longer used.
Use run_aurora_l2_pipeline.sh instead.

This script provided a governed workflow for:
1. GENERATE: Create new supertable versions (fast, no approval)
2. LIST: Show all versions with approval status
3. PROMOTE: Human approves a version → regenerates UI contract
4. STATUS: Check current approved version

GOVERNANCE RULES (HISTORICAL):
- Multiple XLSX versions can be generated for distillation
- Only ONE version can be approved at a time
- UI contract is ONLY regenerated on explicit promotion
- Promotion requires human action (not automatic)
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = Path(__file__).parent.parent.parent
DESIGN_DIR = BASE_DIR / "design" / "l2_1" / "supertable"
MANIFEST_FILE = DESIGN_DIR / "l2_supertable_manifest.json"

INTENT_CSV = DESIGN_DIR / "L2_1_UI_INTENT_SUPERTABLE.csv"
CAPABILITIES_CSV = (
    BASE_DIR
    / "design"
    / "l2_1"
    / "elicitation"
    / "capability_intelligence_all_domains.csv"
)

EXPANDER_SCRIPT = BASE_DIR / "scripts" / "tools" / "l2_cap_expander.py"
CONTRACT_SCRIPT = BASE_DIR / "scripts" / "tools" / "ui_contract_generator.py"

CONTRACT_OUTPUT = (
    BASE_DIR / "website" / "app-shell" / "src" / "contracts" / "ui_contract.v1.json"
)
SUMMARY_OUTPUT = (
    BASE_DIR / "design" / "l2_1" / "ui_contract" / "ui_contract_v1_summary.md"
)


# =============================================================================
# MANIFEST MANAGEMENT
# =============================================================================


def load_manifest() -> dict:
    """Load the version manifest."""
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE) as f:
            return json.load(f)
    return {"approved_version": None, "versions": {}, "last_updated": None}


def save_manifest(manifest: dict) -> None:
    """Save the version manifest."""
    manifest["last_updated"] = datetime.now(timezone.utc).isoformat()
    DESIGN_DIR.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=2)


# =============================================================================
# COMMANDS
# =============================================================================


def cmd_generate(version: str) -> int:
    """Generate a new supertable version."""
    manifest = load_manifest()

    # Validate version format
    if not version.startswith("v"):
        version = f"v{version}"

    output_file = DESIGN_DIR / f"l2_supertable_{version}_cap_expanded.xlsx"

    print("=" * 60)
    print(f"GENERATING: {version}")
    print("=" * 60)

    # Run the expander script
    cmd = [
        sys.executable,
        str(EXPANDER_SCRIPT),
        "--intent",
        str(INTENT_CSV),
        "--capabilities",
        str(CAPABILITIES_CSV),
        "--output",
        str(output_file),
    ]

    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print(f"\n❌ Generation failed for {version}")
        return 1

    # Update manifest
    manifest["versions"][version] = {
        "file": str(output_file.relative_to(BASE_DIR)),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "CANDIDATE",
    }
    save_manifest(manifest)

    print(f"\n✅ Generated: {output_file.name}")
    print("   Status: CANDIDATE (not yet approved)")
    print(f"\n   To promote: python3 {Path(__file__).name} promote {version}")

    return 0


def cmd_list() -> int:
    """List all versions with status."""
    manifest = load_manifest()

    print("=" * 60)
    print("L2 SUPERTABLE VERSIONS")
    print("=" * 60)

    if not manifest["versions"]:
        print("\n  No versions generated yet.")
        print(f"  Run: python3 {Path(__file__).name} generate v4")
        return 0

    approved = manifest.get("approved_version")

    print(f"\n{'Version':<10} {'Status':<15} {'Generated':<25} {'File'}")
    print("-" * 80)

    for version, info in sorted(manifest["versions"].items()):
        status = "✅ APPROVED" if version == approved else "⏳ CANDIDATE"
        generated = info.get("generated_at", "unknown")[:19]
        filename = Path(info.get("file", "")).name
        print(f"{version:<10} {status:<15} {generated:<25} {filename}")

    print("-" * 80)
    print(f"\nApproved version: {approved or 'NONE'}")

    return 0


def cmd_promote(version: str) -> int:
    """Promote a version and regenerate UI contract."""
    manifest = load_manifest()

    # Validate version format
    if not version.startswith("v"):
        version = f"v{version}"

    if version not in manifest["versions"]:
        print(f"❌ Version {version} not found.")
        print(f"   Available: {list(manifest['versions'].keys())}")
        return 1

    version_info = manifest["versions"][version]
    xlsx_file = BASE_DIR / version_info["file"]

    if not xlsx_file.exists():
        print(f"❌ File not found: {xlsx_file}")
        return 1

    print("=" * 60)
    print(f"PROMOTING: {version}")
    print("=" * 60)
    print(f"\n  Source: {xlsx_file.name}")
    print(f"  Target: {CONTRACT_OUTPUT.name}")

    # Confirmation
    print(f"\n⚠️  This will regenerate the UI contract from {version}.")
    confirm = input("   Proceed? [y/N]: ").strip().lower()

    if confirm != "y":
        print("\n❌ Promotion cancelled.")
        return 1

    # Run the contract generator
    cmd = [
        sys.executable,
        str(CONTRACT_SCRIPT),
        "--input",
        str(xlsx_file),
        "--output-json",
        str(CONTRACT_OUTPUT),
        "--output-summary",
        str(SUMMARY_OUTPUT),
    ]

    print("\n  Generating UI contract...")
    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print("\n❌ Contract generation failed")
        return 1

    # Update manifest
    old_approved = manifest.get("approved_version")
    if old_approved and old_approved in manifest["versions"]:
        manifest["versions"][old_approved]["status"] = "SUPERSEDED"

    manifest["approved_version"] = version
    manifest["versions"][version]["status"] = "APPROVED"
    manifest["versions"][version]["promoted_at"] = datetime.now(
        timezone.utc
    ).isoformat()
    save_manifest(manifest)

    print("\n" + "=" * 60)
    print("✅ PROMOTION COMPLETE")
    print("=" * 60)
    print(f"   Approved version: {version}")
    print(f"   UI Contract: {CONTRACT_OUTPUT.relative_to(BASE_DIR)}")
    print(f"   Summary: {SUMMARY_OUTPUT.relative_to(BASE_DIR)}")

    return 0


def cmd_status() -> int:
    """Show current approval status."""
    manifest = load_manifest()

    print("=" * 60)
    print("L2 PIPELINE STATUS")
    print("=" * 60)

    approved = manifest.get("approved_version")

    if approved:
        info = manifest["versions"].get(approved, {})
        print(f"\n  Approved Version: {approved}")
        print(f"  Promoted At:      {info.get('promoted_at', 'unknown')[:19]}")
        print(f"  Source File:      {info.get('file', 'unknown')}")

        # Check if UI contract exists and matches
        if CONTRACT_OUTPUT.exists():
            with open(CONTRACT_OUTPUT) as f:
                contract = json.load(f)
            contract_source = contract.get("generated_from", "")
            print(f"\n  UI Contract Source: {contract_source}")

            expected_source = f"l2_supertable_{approved}_cap_expanded.xlsx"
            if contract_source == expected_source:
                print("  ✅ UI contract is IN SYNC with approved version")
            else:
                print("  ⚠️  UI contract may be OUT OF SYNC")
                print(f"      Expected: {expected_source}")
        else:
            print("\n  ⚠️  UI contract file not found")
    else:
        print("\n  No version approved yet.")
        print(f"\n  Run: python3 {Path(__file__).name} list")
        print(f"       python3 {Path(__file__).name} promote <version>")

    print(f"\n  Total versions: {len(manifest.get('versions', {}))}")
    print(f"  Last updated:   {manifest.get('last_updated', 'never')[:19]}")

    return 0


def cmd_demote() -> int:
    """Remove approval (UI contract becomes stale)."""
    manifest = load_manifest()

    approved = manifest.get("approved_version")
    if not approved:
        print("No version is currently approved.")
        return 0

    print(f"⚠️  This will remove approval from {approved}.")
    print("    The UI contract will become STALE.")
    confirm = input("   Proceed? [y/N]: ").strip().lower()

    if confirm != "y":
        print("Cancelled.")
        return 1

    manifest["versions"][approved]["status"] = "DEMOTED"
    manifest["approved_version"] = None
    save_manifest(manifest)

    print(f"✅ Demoted {approved}. No version is now approved.")
    return 0


# =============================================================================
# MAIN
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="L2 Pipeline — Governed Supertable → UI Contract",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 l2_pipeline.py generate v4      # Create new version
  python3 l2_pipeline.py list             # Show all versions
  python3 l2_pipeline.py promote v4       # Approve and generate contract
  python3 l2_pipeline.py status           # Check current state
  python3 l2_pipeline.py demote           # Remove approval
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # generate
    gen_parser = subparsers.add_parser(
        "generate", help="Generate new supertable version"
    )
    gen_parser.add_argument("version", help="Version tag (e.g., v4, v5)")

    # list
    subparsers.add_parser("list", help="List all versions")

    # promote
    promote_parser = subparsers.add_parser(
        "promote", help="Promote version to approved"
    )
    promote_parser.add_argument("version", help="Version to promote")

    # status
    subparsers.add_parser("status", help="Show current approval status")

    # demote
    subparsers.add_parser("demote", help="Remove approval from current version")

    args = parser.parse_args()

    if args.command == "generate":
        return cmd_generate(args.version)
    elif args.command == "list":
        return cmd_list()
    elif args.command == "promote":
        return cmd_promote(args.version)
    elif args.command == "status":
        return cmd_status()
    elif args.command == "demote":
        return cmd_demote()
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
