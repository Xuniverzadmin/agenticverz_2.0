#!/usr/bin/env python3
# Layer: L4 — Scripts/Ops
# AUDIENCE: FOUNDER
# Product: system-wide
# Role: Extract customer-facing features by grouping operations across domains into user-intent features
# artifact_class: CODE

"""
HOC Feature Extractor

Groups Operations from the classified inventory by base noun across domains
to identify customer-facing features. A feature = one or more Operations +
one user intent.

Usage:
    python3 scripts/ops/hoc_feature_extractor.py
    python3 scripts/ops/hoc_feature_extractor.py --domain incidents
    python3 scripts/ops/hoc_feature_extractor.py --json
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
DEFAULT_OUTPUT = PROJECT_ROOT / "literature" / "hoc_domain" / "CUSTOMER_FEATURES.md"

# Verb groups that map to user intents
VERB_INTENT_MAP = {
    "create": "Create",
    "add": "Create",
    "generate": "Create",
    "get": "Read",
    "read": "Read",
    "list": "Read",
    "fetch": "Read",
    "find": "Read",
    "search": "Read",
    "query": "Read",
    "count": "Read",
    "update": "Update",
    "modify": "Update",
    "edit": "Update",
    "patch": "Update",
    "delete": "Delete",
    "remove": "Delete",
    "revoke": "Delete",
    "export": "Export",
    "aggregate": "Analyze",
    "compute": "Analyze",
    "calculate": "Analyze",
    "analyze": "Analyze",
    "evaluate": "Evaluate",
    "validate": "Evaluate",
    "check": "Evaluate",
    "enforce": "Enforce",
    "detect": "Detect",
    "classify": "Classify",
    "resolve": "Resolve",
    "recover": "Recover",
    "prevent": "Prevent",
    "format": "Transform",
    "transform": "Transform",
    "process": "Process",
    "handle": "Process",
}


# ---------------------------------------------------------------------------
# Feature Extraction
# ---------------------------------------------------------------------------


def extract_noun(symbol: str) -> str | None:
    """Extract the base noun from a function name."""
    fn_name = symbol.split(".")[-1] if "." in symbol else symbol
    if fn_name.startswith("_"):
        return None

    parts = fn_name.split("_")
    if len(parts) < 2:
        return None

    verb = parts[0]
    if verb not in VERB_INTENT_MAP:
        return None

    noun = "_".join(parts[1:])
    # Normalize
    if noun.endswith("ies"):
        noun = noun[:-3] + "y"
    elif noun.endswith("s") and not noun.endswith("ss"):
        noun = noun[:-1]

    return noun


def extract_verb(symbol: str) -> str | None:
    """Extract the verb from a function name."""
    fn_name = symbol.split(".")[-1] if "." in symbol else symbol
    parts = fn_name.split("_")
    if parts and parts[0] in VERB_INTENT_MAP:
        return parts[0]
    return None


def build_features(rows: list[dict[str, str]]) -> list[dict]:
    """
    Build features by grouping operations by base noun.
    A feature = one noun + multiple verb operations.
    """
    # Filter to operations only
    operations = [r for r in rows if r.get("intent") == "Operation"]

    # Group by noun
    by_noun: dict[str, list[dict[str, str]]] = defaultdict(list)
    for op in operations:
        noun = extract_noun(op.get("symbol", ""))
        if noun:
            by_noun[noun].append(op)

    features = []
    for noun in sorted(by_noun):
        ops = by_noun[noun]
        domains = sorted(set(op.get("domain", "") for op in ops))
        verbs = sorted(set(extract_verb(op.get("symbol", "")) or "" for op in ops))
        intents = sorted(set(VERB_INTENT_MAP.get(v, "?") for v in verbs if v))

        # Wiring health
        total = len(ops)
        wired = sum(1 for op in ops if "L4:" in op.get("called_by", ""))
        gaps = sum(1 for op in ops if "L2:" in op.get("called_by", "") and "L4:" not in op.get("called_by", ""))
        orphans = sum(1 for op in ops if not op.get("called_by", ""))

        features.append({
            "feature_noun": noun,
            "user_intents": intents,
            "domains": domains,
            "operations": [op.get("symbol", "") for op in ops],
            "operation_count": total,
            "wired": wired,
            "gaps": gaps,
            "orphans": orphans,
            "health": "healthy" if gaps == 0 and orphans == 0 else ("degraded" if gaps > 0 else "orphaned"),
        })

    # Sort by operation count descending
    features.sort(key=lambda f: -f["operation_count"])
    return features


# ---------------------------------------------------------------------------
# Markdown Generation
# ---------------------------------------------------------------------------


def generate_features_markdown(features: list[dict], domain_filter: str | None = None) -> str:
    """Generate CUSTOMER_FEATURES.md."""
    scope = f" ({domain_filter})" if domain_filter else ""
    total_ops = sum(f["operation_count"] for f in features)
    healthy = sum(1 for f in features if f["health"] == "healthy")
    degraded = sum(1 for f in features if f["health"] == "degraded")
    orphaned_count = sum(1 for f in features if f["health"] == "orphaned")

    lines = [
        f"# Customer Features{scope}",
        "",
        f"**Total features:** {len(features)}  ",
        f"**Total operations:** {total_ops}  ",
        f"**Health:** {healthy} healthy, {degraded} degraded, {orphaned_count} orphaned  ",
        f"**Generator:** `scripts/ops/hoc_feature_extractor.py`",
        "",
        "---",
        "",
        "## Feature Matrix",
        "",
        "| Feature | Intents | Domains | Ops | Wired | Gaps | Health |",
        "|---------|---------|---------|-----|-------|------|--------|",
    ]

    for f in features:
        intents = ", ".join(f["user_intents"])
        domains = ", ".join(f["domains"])
        health_icon = {"healthy": "OK", "degraded": "GAP", "orphaned": "ORPHAN"}[f["health"]]
        lines.append(
            f"| {f['feature_noun']} | {intents} | {domains} | {f['operation_count']} "
            f"| {f['wired']} | {f['gaps']} | {health_icon} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")

    # Detailed feature descriptions
    lines.append("## Feature Details")
    lines.append("")

    for f in features:
        lines.append(f"### {f['feature_noun']}")
        lines.append("")
        lines.append(f"**Domains:** {', '.join(f['domains'])}  ")
        lines.append(f"**User intents:** {', '.join(f['user_intents'])}  ")
        lines.append(f"**Health:** {f['health']}  ")
        lines.append("")
        lines.append("**Operations:**")
        for op in sorted(f["operations"]):
            lines.append(f"- `{op}`")
        lines.append("")

    # Wiring health summary
    lines.append("---")
    lines.append("")
    lines.append("## Wiring Health Summary")
    lines.append("")

    gap_features = [f for f in features if f["health"] == "degraded"]
    if gap_features:
        lines.append("### Features with L2→L5 Gaps")
        lines.append("")
        for f in gap_features:
            lines.append(f"- **{f['feature_noun']}** ({f['gaps']} gaps across {', '.join(f['domains'])})")
        lines.append("")
    else:
        lines.append("_All features are properly wired through L4._")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run_extraction(
    input_path: Path,
    output_path: Path,
    domain_filter: str | None = None,
    as_json: bool = False,
) -> dict:
    """Run feature extraction."""
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        print("Run the full pipeline first.", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if domain_filter:
        rows = [r for r in rows if r.get("domain") == domain_filter]

    # Check intent column
    if rows and "intent" not in rows[0]:
        print("ERROR: Input CSV missing 'intent' column. Run classifier first.", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(rows)} function records")

    features = build_features(rows)
    print(f"Extracted {len(features)} features")

    if as_json:
        result = {
            "total_features": len(features),
            "features": features,
        }
        json.dump(result, sys.stdout, indent=2)
        print()
        return result

    # Write markdown
    md_content = generate_features_markdown(features, domain_filter)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md_content, encoding="utf-8")

    print(f"\nMarkdown written: {output_path}")
    print(f"  Features: {len(features)}")

    # Summary
    healthy = sum(1 for f in features if f["health"] == "healthy")
    degraded = sum(1 for f in features if f["health"] == "degraded")
    print(f"  Healthy: {healthy}, Degraded: {degraded}")

    return {"total_features": len(features)}


def main():
    parser = argparse.ArgumentParser(
        description="HOC Feature Extractor — group operations into customer features"
    )
    parser.add_argument("--input", "-i", type=str,
                        help=f"Input CSV path (default: {DEFAULT_INPUT.relative_to(PROJECT_ROOT)})")
    parser.add_argument("--output", "-o", type=str,
                        help=f"Output markdown path (default: {DEFAULT_OUTPUT.relative_to(PROJECT_ROOT)})")
    parser.add_argument("--domain", type=str, help="Process only this domain")
    parser.add_argument("--json", action="store_true", help="Output JSON to stdout")
    args = parser.parse_args()

    input_path = Path(args.input) if args.input else DEFAULT_INPUT
    output_path = Path(args.output) if args.output else DEFAULT_OUTPUT

    print("=" * 60)
    print("HOC Feature Extractor")
    print("=" * 60)
    print()

    run_extraction(input_path, output_path, domain_filter=args.domain, as_json=args.json)

    print()
    print("=" * 60)
    print("Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()
