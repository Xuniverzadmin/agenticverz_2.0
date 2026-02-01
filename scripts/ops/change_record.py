#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Change Record Helper - Create and manage code change records.
# artifact_class: CODE
"""
Change Record Helper - Create and manage code change records.

Usage:
    python scripts/ops/change_record.py create --purpose "Why this change" --type bugfix --artifacts AOS-FE-AIC-INT-002
    python scripts/ops/change_record.py list
    python scripts/ops/change_record.py show CHANGE-2025-0001
    python scripts/ops/change_record.py next

Examples:
    # Create a bugfix change record
    python scripts/ops/change_record.py create \
        --purpose "Fix API key validation error" \
        --type bugfix \
        --artifacts AOS-BE-API-INT-001 \
        --risk low \
        --behavior-change no

    # Create a refactor change record
    python scripts/ops/change_record.py create \
        --purpose "Refactor incident aggregation for performance" \
        --type refactor \
        --artifacts AOS-BE-SVC-INC-001 AOS-BE-API-INC-001 \
        --risk medium \
        --interface-change no

    # Create a RENAME change record (HIGH-RISK)
    # Note: For renames, the tool auto-enforces:
    #   - risk_level >= medium
    #   - interface_change = yes
    #   - backward_compatibility = no
    #   - manual_verification = required
    python scripts/ops/change_record.py create \
        --purpose "Rename cost_detector.py to cost_anomaly_detector.py for clarity" \
        --type rename \
        --artifacts AOS-BE-SVC-CAD-001 \
        --files-renamed "backend/app/services/cost_detector.py:backend/app/services/cost_anomaly_detector.py"

    # List all change records
    python scripts/ops/change_record.py list

    # Show specific change record
    python scripts/ops/change_record.py show CHANGE-2025-0001
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. Install with: pip install pyyaml")
    sys.exit(1)

CHANGES_DIR = (
    Path(__file__).parent.parent.parent / "docs" / "codebase-registry" / "changes"
)
ARTIFACTS_DIR = (
    Path(__file__).parent.parent.parent / "docs" / "codebase-registry" / "artifacts"
)

VALID_CHANGE_TYPES = [
    "bugfix",
    "refactor",
    "behavior_change",
    "performance",
    "security",
    "cleanup",
    "test_only",
    "documentation",
    "feature",
    "deprecation",
    "rename",  # File/artifact rename (HIGH-RISK)
]

VALID_RISK_LEVELS = ["low", "medium", "high"]
VALID_YES_NO = ["yes", "no"]
VALID_AUTHORITY_CHANGE = ["none", "increased", "reduced"]
VALID_VERIFICATION = ["required", "not_required"]


def get_next_change_id() -> str:
    """Get the next available change ID."""
    year = datetime.now().year

    if not CHANGES_DIR.exists():
        CHANGES_DIR.mkdir(parents=True, exist_ok=True)
        return f"CHANGE-{year}-0001"

    existing = list(CHANGES_DIR.glob(f"CHANGE-{year}-*.yaml"))
    if not existing:
        return f"CHANGE-{year}-0001"

    # Extract numbers and find max
    numbers = []
    for f in existing:
        try:
            num = int(f.stem.split("-")[-1])
            numbers.append(num)
        except ValueError:
            continue

    next_num = max(numbers) + 1 if numbers else 1
    return f"CHANGE-{year}-{next_num:04d}"


def validate_artifacts(artifact_ids: list[str]) -> tuple[bool, list[str]]:
    """Validate that artifact IDs exist in the registry."""
    missing = []
    for aid in artifact_ids:
        # Search for artifact file
        matches = list(ARTIFACTS_DIR.glob(f"{aid}.yaml"))
        if not matches:
            missing.append(aid)
    return len(missing) == 0, missing


def create_change_record(
    purpose: str,
    change_type: str,
    artifacts: list[str],
    author: str = "pair",
    risk_level: str = "low",
    authority_change: str = "none",
    behavior_change: str = "no",
    interface_change: str = "no",
    data_change: str = "no",
    backward_compat: str = "yes",
    tests_added: str = "no",
    tests_modified: str = "no",
    manual_verification: str = "not_required",
    files_added: list[str] = None,
    files_removed: list[str] = None,
    files_renamed: list[tuple[str, str]] = None,  # List of (from, to) tuples
    related_pins: list[str] = None,
    notes: str = None,
) -> tuple[str, str]:
    """Create a new change record."""

    # Validate inputs
    if change_type not in VALID_CHANGE_TYPES:
        return None, f"Invalid change_type: {change_type}. Valid: {VALID_CHANGE_TYPES}"

    if risk_level not in VALID_RISK_LEVELS:
        return None, f"Invalid risk_level: {risk_level}. Valid: {VALID_RISK_LEVELS}"

    if authority_change not in VALID_AUTHORITY_CHANGE:
        return (
            None,
            f"Invalid authority_change: {authority_change}. Valid: {VALID_AUTHORITY_CHANGE}",
        )

    for field, value in [
        ("behavior_change", behavior_change),
        ("interface_change", interface_change),
        ("data_change", data_change),
        ("backward_compatibility", backward_compat),
        ("tests_added", tests_added),
        ("tests_modified", tests_modified),
    ]:
        if value not in VALID_YES_NO:
            return None, f"Invalid {field}: {value}. Valid: {VALID_YES_NO}"

    if manual_verification not in VALID_VERIFICATION:
        return (
            None,
            f"Invalid manual_verification: {manual_verification}. Valid: {VALID_VERIFICATION}",
        )

    # Validate artifacts exist
    valid, missing = validate_artifacts(artifacts)
    if not valid:
        return None, f"Artifact IDs not found in registry: {missing}"

    # Get next ID
    change_id = get_next_change_id()
    date = datetime.now().strftime("%Y-%m-%d")

    # Build record
    record = {
        "change_id": change_id,
        "date": date,
        "author": author,
        "change_type": change_type,
        "purpose": purpose,
        "scope": {
            "artifacts_modified": artifacts,
        },
        "impact": {
            "authority_change": authority_change,
            "behavior_change": behavior_change,
            "interface_change": interface_change,
            "data_change": data_change,
        },
        "risk_level": risk_level,
        "backward_compatibility": backward_compat,
        "validation": {
            "tests_added": tests_added,
            "tests_modified": tests_modified,
            "manual_verification": manual_verification,
        },
    }

    # Optional fields
    if files_added:
        record["scope"]["files_added"] = files_added
    if files_removed:
        record["scope"]["files_removed"] = files_removed
    if files_renamed:
        # Convert tuples to {from, to} dicts
        record["scope"]["files_renamed"] = [
            {"from": fr, "to": to} for fr, to in files_renamed
        ]
    if related_pins:
        record["related_pins"] = related_pins
    if notes:
        record["notes"] = notes

    # Ensure directory exists
    CHANGES_DIR.mkdir(parents=True, exist_ok=True)

    # Write file
    filepath = CHANGES_DIR / f"{change_id}.yaml"

    # Create YAML content with header
    header = f"""# Code Change Record
# Created: {date}
# Schema: change-schema-v1.yaml

"""

    with open(filepath, "w") as f:
        f.write(header)
        yaml.dump(
            record, f, default_flow_style=False, sort_keys=False, allow_unicode=True
        )

    return change_id, str(filepath)


def list_changes() -> list[dict]:
    """List all change records."""
    if not CHANGES_DIR.exists():
        return []

    changes = []
    for filepath in sorted(CHANGES_DIR.glob("CHANGE-*.yaml"), reverse=True):
        try:
            with open(filepath) as f:
                record = yaml.safe_load(f)
                if record:
                    record["_filepath"] = str(filepath)
                    changes.append(record)
        except Exception as e:
            print(f"Warning: Failed to load {filepath.name}: {e}", file=sys.stderr)

    return changes


def show_change(change_id: str) -> dict:
    """Show a specific change record."""
    # Normalize ID
    if not change_id.startswith("CHANGE-"):
        change_id = f"CHANGE-{change_id}"

    filepath = CHANGES_DIR / f"{change_id}.yaml"
    if not filepath.exists():
        # Try partial match
        matches = list(CHANGES_DIR.glob(f"*{change_id}*.yaml"))
        if matches:
            filepath = matches[0]
        else:
            return None

    try:
        with open(filepath) as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def format_change_table(changes: list[dict]) -> str:
    """Format changes as a table."""
    if not changes:
        return "No change records found."

    lines = []
    lines.append(f"{'ID':<20} {'Date':<12} {'Type':<15} {'Risk':<8} {'Purpose':<40}")
    lines.append("-" * 100)

    for c in changes:
        cid = c.get("change_id", "N/A")[:19]
        date = c.get("date", "N/A")[:11]
        ctype = c.get("change_type", "N/A")[:14]
        risk = c.get("risk_level", "N/A")[:7]
        purpose = c.get("purpose", "N/A")[:39]
        lines.append(f"{cid:<20} {date:<12} {ctype:<15} {risk:<8} {purpose:<40}")

    lines.append("-" * 100)
    lines.append(f"Total: {len(changes)} change record(s)")

    return "\n".join(lines)


def format_change_detail(record: dict) -> str:
    """Format a single change record for display."""
    if not record:
        return "Change record not found."

    lines = []
    lines.append("=" * 60)
    lines.append(f"  {record.get('change_id', 'N/A')}")
    lines.append("=" * 60)
    lines.append(f"  Date:     {record.get('date', 'N/A')}")
    lines.append(f"  Author:   {record.get('author', 'N/A')}")
    lines.append(f"  Type:     {record.get('change_type', 'N/A')}")
    lines.append(f"  Risk:     {record.get('risk_level', 'N/A')}")
    lines.append(f"  Purpose:  {record.get('purpose', 'N/A')}")

    # Scope
    scope = record.get("scope", {})
    artifacts = scope.get("artifacts_modified", [])
    lines.append(f"  Artifacts: {', '.join(artifacts) if artifacts else 'None'}")

    if scope.get("files_added"):
        lines.append(f"  Files Added: {', '.join(scope['files_added'])}")
    if scope.get("files_removed"):
        lines.append(f"  Files Removed: {', '.join(scope['files_removed'])}")
    if scope.get("files_renamed"):
        lines.append("  Files Renamed:")
        for rename in scope["files_renamed"]:
            lines.append(f"    {rename.get('from', '?')} -> {rename.get('to', '?')}")

    # Impact
    impact = record.get("impact", {})
    lines.append("  Impact:")
    lines.append(f"    Authority Change: {impact.get('authority_change', 'N/A')}")
    lines.append(f"    Behavior Change:  {impact.get('behavior_change', 'N/A')}")
    lines.append(f"    Interface Change: {impact.get('interface_change', 'N/A')}")
    lines.append(f"    Data Change:      {impact.get('data_change', 'N/A')}")

    lines.append(
        f"  Backward Compatible: {record.get('backward_compatibility', 'N/A')}"
    )

    # Validation
    validation = record.get("validation", {})
    lines.append("  Validation:")
    lines.append(f"    Tests Added:    {validation.get('tests_added', 'N/A')}")
    lines.append(f"    Tests Modified: {validation.get('tests_modified', 'N/A')}")
    lines.append(
        f"    Manual Verification: {validation.get('manual_verification', 'N/A')}"
    )

    # Optional
    if record.get("related_pins"):
        lines.append(f"  Related PINs: {', '.join(record['related_pins'])}")
    if record.get("notes"):
        lines.append(f"  Notes: {record['notes']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Create and manage code change records.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s next                     # Show next change ID
  %(prog)s list                     # List all change records
  %(prog)s show CHANGE-2025-0001    # Show specific record
  %(prog)s create --purpose "Fix bug" --type bugfix --artifacts AOS-BE-API-INT-001
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # next command
    next_parser = subparsers.add_parser("next", help="Show next available change ID")

    # list command
    list_parser = subparsers.add_parser("list", help="List all change records")
    list_parser.add_argument("--type", dest="filter_type", help="Filter by change type")
    list_parser.add_argument("--risk", dest="filter_risk", help="Filter by risk level")

    # show command
    show_parser = subparsers.add_parser("show", help="Show a specific change record")
    show_parser.add_argument("change_id", help="Change ID (e.g., CHANGE-2025-0001)")

    # create command
    create_parser = subparsers.add_parser("create", help="Create a new change record")
    create_parser.add_argument(
        "--purpose", "-p", required=True, help="Purpose of the change"
    )
    create_parser.add_argument(
        "--type",
        "-t",
        dest="change_type",
        required=True,
        choices=VALID_CHANGE_TYPES,
        help="Type of change",
    )
    create_parser.add_argument(
        "--artifacts",
        "-a",
        nargs="+",
        required=True,
        help="Artifact IDs being modified",
    )
    create_parser.add_argument(
        "--author",
        default="pair",
        choices=["human", "claude", "pair"],
        help="Author (default: pair)",
    )
    create_parser.add_argument(
        "--risk",
        default="low",
        choices=VALID_RISK_LEVELS,
        help="Risk level (default: low)",
    )
    create_parser.add_argument(
        "--authority-change",
        default="none",
        choices=VALID_AUTHORITY_CHANGE,
        help="Authority change (default: none)",
    )
    create_parser.add_argument(
        "--behavior-change",
        default="no",
        choices=VALID_YES_NO,
        help="Behavior change (default: no)",
    )
    create_parser.add_argument(
        "--interface-change",
        default="no",
        choices=VALID_YES_NO,
        help="Interface change (default: no)",
    )
    create_parser.add_argument(
        "--data-change",
        default="no",
        choices=VALID_YES_NO,
        help="Data change (default: no)",
    )
    create_parser.add_argument(
        "--backward-compat",
        default="yes",
        choices=VALID_YES_NO,
        help="Backward compatible (default: yes)",
    )
    create_parser.add_argument(
        "--tests-added",
        default="no",
        choices=VALID_YES_NO,
        help="Tests added (default: no)",
    )
    create_parser.add_argument(
        "--tests-modified",
        default="no",
        choices=VALID_YES_NO,
        help="Tests modified (default: no)",
    )
    create_parser.add_argument(
        "--manual-verification",
        default="not_required",
        choices=VALID_VERIFICATION,
        help="Manual verification (default: not_required)",
    )
    create_parser.add_argument("--files-added", nargs="*", help="Files being added")
    create_parser.add_argument("--files-removed", nargs="*", help="Files being removed")
    create_parser.add_argument(
        "--files-renamed",
        nargs="*",
        metavar="FROM:TO",
        help="Files being renamed (format: old_path:new_path)",
    )
    create_parser.add_argument("--related-pins", nargs="*", help="Related PIN numbers")
    create_parser.add_argument("--notes", help="Additional notes")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "next":
        next_id = get_next_change_id()
        print(f"Next change ID: {next_id}")

    elif args.command == "list":
        changes = list_changes()

        # Apply filters
        if args.filter_type:
            changes = [c for c in changes if c.get("change_type") == args.filter_type]
        if args.filter_risk:
            changes = [c for c in changes if c.get("risk_level") == args.filter_risk]

        print(format_change_table(changes))

    elif args.command == "show":
        record = show_change(args.change_id)
        print(format_change_detail(record))

    elif args.command == "create":
        # Parse files_renamed (format: old_path:new_path)
        files_renamed = None
        if args.files_renamed:
            files_renamed = []
            for entry in args.files_renamed:
                if ":" not in entry:
                    print(
                        f"ERROR: Invalid rename format '{entry}'. Use 'old_path:new_path'",
                        file=sys.stderr,
                    )
                    sys.exit(1)
                parts = entry.split(":", 1)
                files_renamed.append((parts[0], parts[1]))

        # For rename change type, enforce high-risk defaults
        if args.change_type == "rename":
            if args.risk == "low":
                print(
                    "WARNING: Renames are HIGH-RISK. Setting risk_level to 'medium' (minimum)."
                )
                args.risk = "medium"
            if args.interface_change == "no":
                print(
                    "WARNING: Renames change import paths. Setting interface_change to 'yes'."
                )
                args.interface_change = "yes"
            if args.backward_compat == "yes":
                print(
                    "WARNING: Renames break old imports. Setting backward_compatibility to 'no'."
                )
                args.backward_compat = "no"
            if args.manual_verification == "not_required":
                print(
                    "WARNING: Renames require caller verification. Setting manual_verification to 'required'."
                )
                args.manual_verification = "required"

        change_id, result = create_change_record(
            purpose=args.purpose,
            change_type=args.change_type,
            artifacts=args.artifacts,
            author=args.author,
            risk_level=args.risk,
            authority_change=args.authority_change,
            behavior_change=args.behavior_change,
            interface_change=args.interface_change,
            data_change=args.data_change,
            backward_compat=args.backward_compat,
            tests_added=args.tests_added,
            tests_modified=args.tests_modified,
            manual_verification=args.manual_verification,
            files_added=args.files_added,
            files_removed=args.files_removed,
            files_renamed=files_renamed,
            related_pins=args.related_pins,
            notes=args.notes,
        )

        if change_id:
            print(f"Created change record: {change_id}")
            print(f"File: {result}")
        else:
            print(f"ERROR: {result}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
