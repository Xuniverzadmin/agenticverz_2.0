#!/usr/bin/env python3
"""
Artifact Lookup Tool - Search and display codebase registry artifacts.

Usage:
    python scripts/ops/artifact_lookup.py <search_term>
    python scripts/ops/artifact_lookup.py --id <artifact_id>
    python scripts/ops/artifact_lookup.py --product ai-console
    python scripts/ops/artifact_lookup.py --type service
    python scripts/ops/artifact_lookup.py --authority mutate
    python scripts/ops/artifact_lookup.py --list

Examples:
    python scripts/ops/artifact_lookup.py KeysPage
    python scripts/ops/artifact_lookup.py --id AOS-FE-AIC-INT-002
    python scripts/ops/artifact_lookup.py --product ai-console --type page
    python scripts/ops/artifact_lookup.py --authority enforce
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. Install with: pip install pyyaml")
    sys.exit(1)

ARTIFACTS_DIR = (
    Path(__file__).parent.parent.parent / "docs" / "codebase-registry" / "artifacts"
)


def load_artifact(filepath: Path) -> Optional[dict]:
    """Load a single artifact YAML file."""
    try:
        with open(filepath) as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Warning: Failed to load {filepath.name}: {e}", file=sys.stderr)
        return None


def load_all_artifacts() -> list[dict]:
    """Load all artifacts from the registry."""
    artifacts = []
    if not ARTIFACTS_DIR.exists():
        print(f"ERROR: Artifacts directory not found: {ARTIFACTS_DIR}", file=sys.stderr)
        sys.exit(1)

    for filepath in sorted(ARTIFACTS_DIR.glob("*.yaml")):
        artifact = load_artifact(filepath)
        if artifact:
            artifact["_filepath"] = str(filepath)
            artifacts.append(artifact)

    return artifacts


def search_by_name(artifacts: list[dict], term: str) -> list[dict]:
    """Search artifacts by name (case-insensitive partial match)."""
    term_lower = term.lower()
    return [a for a in artifacts if term_lower in a.get("name", "").lower()]


def search_by_id(artifacts: list[dict], artifact_id: str) -> list[dict]:
    """Search artifacts by exact or partial artifact_id."""
    id_upper = artifact_id.upper()
    return [a for a in artifacts if id_upper in a.get("artifact_id", "").upper()]


def filter_by_product(artifacts: list[dict], product: str) -> list[dict]:
    """Filter artifacts by product."""
    return [
        a
        for a in artifacts
        if a.get("traceability", {}).get("product", "").lower() == product.lower()
    ]


def filter_by_type(artifacts: list[dict], artifact_type: str) -> list[dict]:
    """Filter artifacts by type."""
    return [a for a in artifacts if a.get("type", "").lower() == artifact_type.lower()]


def filter_by_authority(artifacts: list[dict], authority: str) -> list[dict]:
    """Filter artifacts by authority level."""
    return [
        a
        for a in artifacts
        if a.get("authority_level", "").lower() == authority.lower()
    ]


def format_artifact(artifact: dict, verbose: bool = False) -> str:
    """Format a single artifact for display."""
    lines = []

    artifact_id = artifact.get("artifact_id", "N/A")
    name = artifact.get("name", "N/A")
    artifact_type = artifact.get("type", "N/A")
    purpose = artifact.get("purpose", "N/A")
    authority = artifact.get("authority_level", "N/A")
    status = artifact.get("status", "N/A")

    # Header
    lines.append(f"{'─' * 60}")
    lines.append(f"  {artifact_id}")
    lines.append(f"{'─' * 60}")
    lines.append(f"  Name:      {name}")
    lines.append(f"  Type:      {artifact_type}")
    lines.append(f"  Status:    {status}")
    lines.append(f"  Authority: {authority}")
    lines.append(f"  Purpose:   {purpose}")

    # Traceability
    traceability = artifact.get("traceability", {})
    if traceability:
        product = traceability.get("product", "N/A")
        domain = traceability.get("domain", "N/A")
        order = traceability.get("order_depth", "N/A")
        lines.append(f"  Product:   {product}")
        lines.append(f"  Domain:    {domain}")
        lines.append(f"  Order:     {order}")

    if verbose:
        # Responsibility
        responsibility = artifact.get("responsibility", "")
        if responsibility:
            lines.append("  Responsibility:")
            for line in responsibility.strip().split("\n"):
                lines.append(f"    {line}")

        # Notes
        notes = artifact.get("notes", "")
        if notes:
            lines.append("  Notes:")
            for line in str(notes).strip().split("\n"):
                lines.append(f"    {line}")

        # File path
        filepath = artifact.get("_filepath", "")
        if filepath:
            lines.append(f"  File:      {filepath}")

    return "\n".join(lines)


def format_table(artifacts: list[dict]) -> str:
    """Format artifacts as a compact table."""
    if not artifacts:
        return "No artifacts found."

    lines = []
    lines.append(
        f"{'ID':<25} {'Name':<30} {'Type':<12} {'Authority':<10} {'Product':<15}"
    )
    lines.append("─" * 95)

    for a in artifacts:
        artifact_id = a.get("artifact_id", "N/A")[:24]
        name = a.get("name", "N/A")[:29]
        artifact_type = a.get("type", "N/A")[:11]
        authority = a.get("authority_level", "N/A")[:9]
        product = a.get("traceability", {}).get("product", "N/A")[:14]
        lines.append(
            f"{artifact_id:<25} {name:<30} {artifact_type:<12} {authority:<10} {product:<15}"
        )

    lines.append("─" * 95)
    lines.append(f"Total: {len(artifacts)} artifact(s)")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Search and display codebase registry artifacts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s KeysPage                    # Search by name
  %(prog)s --id AOS-FE-AIC-INT-002     # Search by artifact ID
  %(prog)s --product ai-console        # Filter by product
  %(prog)s --type service              # Filter by type
  %(prog)s --authority mutate          # Filter by authority level
  %(prog)s --list                      # List all artifacts
  %(prog)s --product ai-console -v     # Verbose output
        """,
    )

    parser.add_argument("search", nargs="?", help="Search term (matches artifact name)")
    parser.add_argument("--id", "-i", dest="artifact_id", help="Search by artifact ID")
    parser.add_argument(
        "--product",
        "-p",
        help="Filter by product (ai-console, system-wide, product-builder)",
    )
    parser.add_argument(
        "--type",
        "-t",
        dest="artifact_type",
        help="Filter by type (api-route, service, worker, page, etc.)",
    )
    parser.add_argument(
        "--authority",
        "-a",
        help="Filter by authority level (observe, advise, enforce, mutate)",
    )
    parser.add_argument("--list", "-l", action="store_true", help="List all artifacts")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed information"
    )
    parser.add_argument(
        "--table",
        action="store_true",
        help="Output as compact table (default for multiple results)",
    )

    args = parser.parse_args()

    # Require at least one search/filter option
    if not any(
        [
            args.search,
            args.artifact_id,
            args.product,
            args.artifact_type,
            args.authority,
            args.list,
        ]
    ):
        parser.print_help()
        sys.exit(1)

    # Load all artifacts
    artifacts = load_all_artifacts()
    results = artifacts

    # Apply filters
    if args.search:
        results = search_by_name(results, args.search)

    if args.artifact_id:
        results = search_by_id(results, args.artifact_id)

    if args.product:
        results = filter_by_product(results, args.product)

    if args.artifact_type:
        results = filter_by_type(results, args.artifact_type)

    if args.authority:
        results = filter_by_authority(results, args.authority)

    # Output results
    if not results:
        print("No artifacts found matching the criteria.")
        sys.exit(0)

    # Single result or verbose mode: show detailed view
    if len(results) == 1 or args.verbose:
        for artifact in results:
            print(format_artifact(artifact, verbose=args.verbose))
            print()
    else:
        # Multiple results: show table
        print(format_table(results))


if __name__ == "__main__":
    main()
