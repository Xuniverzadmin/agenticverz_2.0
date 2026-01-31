#!/usr/bin/env python3
# Layer: L4 — Scripts/Ops
# AUDIENCE: FOUNDER
# Product: system-wide
# Role: Generate per-domain DOMAIN_CAPABILITY.md with operations, helpers, persistence, and non-features
# artifact_class: CODE

"""
HOC Domain Capability Doc Generator

Reads the classified FUNCTION_INVENTORY.csv (with intent + placement columns)
and generates a DOMAIN_CAPABILITY.md per domain.

Usage:
    python3 scripts/ops/hoc_capability_doc_generator.py
    python3 scripts/ops/hoc_capability_doc_generator.py --domain incidents
    python3 scripts/ops/hoc_capability_doc_generator.py --json
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = PROJECT_ROOT / "literature" / "hoc_domain" / "FUNCTION_INVENTORY.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "literature" / "hoc_domain"
DOMAIN_LOCKS_DIR = PROJECT_ROOT / "backend" / "app" / "hoc" / "cus" / "docs" / "domain-locks"

ALL_DOMAINS = [
    "account", "activity", "analytics", "api_keys", "apis",
    "controls", "docs", "incidents", "integrations", "logs",
    "overview", "policies",
]

# Domain purpose descriptions (brief)
DOMAIN_PURPOSES = {
    "account": "Manages customer account settings, organization profiles, team members, and account-level configuration. Provides the identity boundary for all other domains.",
    "activity": "Tracks and surfaces user and system activity streams. Provides audit trail and activity feeds for the customer console.",
    "analytics": "Aggregates operational metrics, trends, and insights across all customer domains. Powers dashboards, reports, and data exports.",
    "api_keys": "Manages API key lifecycle — creation, rotation, revocation, and usage tracking for machine-native access.",
    "apis": "API discovery and documentation for customer-facing endpoints. Manages API catalog and capability registry.",
    "controls": "Customer-configurable controls, feature flags, and operational knobs. Provides governance levers without code changes.",
    "docs": "Documentation management — internal and customer-facing docs, guides, and reference materials.",
    "incidents": "Incident lifecycle management — detection, classification, severity assessment, postmortem analysis, prevention rules, and recurrence tracking.",
    "integrations": "External system integrations — webhook management, third-party connectors, event routing, and integration health monitoring.",
    "logs": "Structured logging and log analysis — log ingestion, search, filtering, alerting, and retention management.",
    "overview": "Customer dashboard overview — aggregated health status, key metrics, and quick-access navigation across all domains.",
    "policies": "Policy engine — DSL-based policy definition, compilation, evaluation, versioning, and enforcement across all operations.",
}


# ---------------------------------------------------------------------------
# Domain Lock Parsing
# ---------------------------------------------------------------------------


def parse_domain_lock(domain: str) -> list[str]:
    """Extract non-feature declarations from DOMAIN_LOCK files."""
    lock_name = f"{domain.upper()}_DOMAIN_LOCK_FINAL.md"
    lock_path = DOMAIN_LOCKS_DIR / lock_name
    if not lock_path.exists():
        return []

    try:
        content = lock_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    # Look for explicit non-feature or exclusion sections
    non_features = []
    in_section = False
    for line in content.splitlines():
        if "non-feature" in line.lower() or "does not" in line.lower() or "excluded" in line.lower():
            in_section = True
            continue
        if in_section:
            if line.startswith("#") or line.startswith("---"):
                in_section = False
                continue
            stripped = line.strip().lstrip("- ")
            if stripped:
                non_features.append(stripped)

    return non_features


# ---------------------------------------------------------------------------
# Markdown Generation
# ---------------------------------------------------------------------------


def generate_capability_doc(
    domain: str,
    rows: list[dict[str, str]],
) -> str:
    """Generate DOMAIN_CAPABILITY.md content for a single domain."""
    lines = [
        f"# {domain.title()} — Domain Capability",
        "",
        f"**Domain:** {domain}  ",
        f"**Total functions:** {len(rows)}  ",
        f"**Generator:** `scripts/ops/hoc_capability_doc_generator.py`",
        "",
        "---",
        "",
    ]

    # Section 1: Domain Purpose
    lines.append("## 1. Domain Purpose")
    lines.append("")
    purpose = DOMAIN_PURPOSES.get(domain, f"The {domain} domain provides customer-facing functionality.")
    lines.append(purpose)
    lines.append("")

    # Group by intent
    by_intent: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        intent = r.get("intent", "Unclassified")
        by_intent[intent].append(r)

    # Section 2: Customer-Facing Operations
    lines.append("## 2. Customer-Facing Operations")
    lines.append("")

    operations = by_intent.get("Operation", [])
    if operations:
        lines.append("| Function | File | L4 Wired | Entry Point | Side Effects |")
        lines.append("|----------|------|----------|-------------|--------------|")
        for op in sorted(operations, key=lambda r: r.get("symbol", "")):
            symbol = op.get("symbol", "")
            file_name = op.get("file", "")
            called_by = op.get("called_by", "")
            placement = op.get("placement", "")
            side_effects = op.get("side_effects", "pure")

            wired = "Yes" if "L4:" in called_by else "No (gap)"
            entry = ""
            if "L2:" in called_by:
                # Extract L2 entry
                for part in called_by.split(" | "):
                    if part.startswith("L2:"):
                        entry = part
                        break
            elif "L4:" in called_by:
                for part in called_by.split(" | "):
                    if part.startswith("L4:"):
                        entry = part
                        break

            lines.append(f"| `{symbol}` | {file_name} | {wired} | {entry} | {side_effects} |")
        lines.append("")
    else:
        lines.append("_No operations classified for this domain._")
        lines.append("")

    # Section 3: Internal Functions (grouped by intent)
    lines.append("## 3. Internal Functions")
    lines.append("")

    # 3a: Policy/Decision
    decisions = by_intent.get("Policy/Decision", [])
    if decisions:
        lines.append("### Decisions")
        lines.append("")
        lines.append("| Function | File | Confidence |")
        lines.append("|----------|------|------------|")
        for fn in sorted(decisions, key=lambda r: r.get("symbol", "")):
            lines.append(f"| `{fn.get('symbol', '')}` | {fn.get('file', '')} | {fn.get('intent_confidence', '')} |")
        lines.append("")

    # 3b: Coordinator/Aggregator
    coordinators = by_intent.get("Coordinator/Aggregator", [])
    if coordinators:
        lines.append("### Coordinators")
        lines.append("")
        lines.append("| Function | File | Confidence |")
        lines.append("|----------|------|------------|")
        for fn in sorted(coordinators, key=lambda r: r.get("symbol", "")):
            lines.append(f"| `{fn.get('symbol', '')}` | {fn.get('file', '')} | {fn.get('intent_confidence', '')} |")
        lines.append("")

    # 3c: Internal Helpers
    helpers = by_intent.get("Internal Helper", [])
    if helpers:
        lines.append("### Helpers")
        lines.append("")
        lines.append(f"_{len(helpers)} internal helper functions._")
        lines.append("")
        # Group by file for compactness
        by_file: dict[str, list[str]] = defaultdict(list)
        for fn in helpers:
            by_file[fn.get("file", "")].append(fn.get("symbol", ""))
        for file_name in sorted(by_file):
            symbols = sorted(by_file[file_name])
            lines.append(f"- **{file_name}:** {', '.join(f'`{s}`' for s in symbols[:10])}")
            if len(symbols) > 10:
                lines.append(f"  _...and {len(symbols) - 10} more_")
        lines.append("")

    # 3d: Persistence
    persistence = by_intent.get("Persistence/Driver", [])
    if persistence:
        lines.append("### Persistence")
        lines.append("")
        lines.append("| Function | File | Side Effects |")
        lines.append("|----------|------|--------------|")
        for fn in sorted(persistence, key=lambda r: r.get("symbol", "")):
            lines.append(f"| `{fn.get('symbol', '')}` | {fn.get('file', '')} | {fn.get('side_effects', '')} |")
        lines.append("")

    # 3e: Unclassified
    unclassified = by_intent.get("Unclassified", [])
    if unclassified:
        lines.append("### Unclassified (needs review)")
        lines.append("")
        lines.append(f"_{len(unclassified)} functions need manual classification._")
        lines.append("")
        for fn in sorted(unclassified, key=lambda r: r.get("symbol", ""))[:20]:
            lines.append(f"- `{fn.get('symbol', '')}` ({fn.get('file', '')})")
        if len(unclassified) > 20:
            lines.append(f"- _...and {len(unclassified) - 20} more_")
        lines.append("")

    # Section 4: Explicit Non-Features
    lines.append("## 4. Explicit Non-Features")
    lines.append("")
    non_features = parse_domain_lock(domain)
    if non_features:
        for nf in non_features:
            lines.append(f"- {nf}")
    else:
        lines.append(f"_No explicit non-feature declarations found in {domain.upper()}_DOMAIN_LOCK_FINAL.md._")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run_generation(
    input_path: Path,
    output_dir: Path,
    domain_filter: str | None = None,
    as_json: bool = False,
) -> dict:
    """Generate capability docs for all domains."""
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        print("Run the inventory + classifier pipeline first.", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Group by domain
    by_domain: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        domain = r.get("domain", "")
        if domain_filter and domain != domain_filter:
            continue
        if domain == "_models":
            continue  # Skip L7 models — they don't get capability docs
        by_domain[domain].append(r)

    print(f"Loaded {len(rows)} records across {len(by_domain)} domains")

    results: dict[str, dict] = {}
    for domain in sorted(by_domain):
        domain_rows = by_domain[domain]
        md_content = generate_capability_doc(domain, domain_rows)

        domain_dir = output_dir / domain
        domain_dir.mkdir(parents=True, exist_ok=True)
        out_path = domain_dir / "DOMAIN_CAPABILITY.md"
        out_path.write_text(md_content, encoding="utf-8")

        results[domain] = {
            "total_functions": len(domain_rows),
            "output": str(out_path.relative_to(PROJECT_ROOT)),
        }
        print(f"  {domain}: {len(domain_rows)} functions → {out_path.relative_to(PROJECT_ROOT)}")

    if as_json:
        json.dump(results, sys.stdout, indent=2)
        print()

    print(f"\nGenerated {len(results)} DOMAIN_CAPABILITY.md files")
    return results


def main():
    parser = argparse.ArgumentParser(
        description="HOC Capability Doc Generator — per-domain DOMAIN_CAPABILITY.md"
    )
    parser.add_argument("--input", "-i", type=str,
                        help=f"Input CSV path (default: {DEFAULT_INPUT.relative_to(PROJECT_ROOT)})")
    parser.add_argument("--output-dir", type=str,
                        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR.relative_to(PROJECT_ROOT)})")
    parser.add_argument("--domain", type=str, help="Process only this domain")
    parser.add_argument("--json", action="store_true", help="Output JSON to stdout")
    args = parser.parse_args()

    input_path = Path(args.input) if args.input else DEFAULT_INPUT
    output_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIR

    print("=" * 60)
    print("HOC Domain Capability Doc Generator")
    print("=" * 60)
    print()

    run_generation(input_path, output_dir, domain_filter=args.domain, as_json=args.json)

    print()
    print("=" * 60)
    print("Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()
