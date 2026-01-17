#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: manual | CI
#   Execution: sync
# Role: Detect overlapping panels within topics — READ ONLY diagnostic
# Reference: PANEL_STRUCTURE_PIPELINE.md Phase 2

"""
Facet Overlap Detector (Phase 2 Tool 2)

Question it answers:
  "Are multiple panels saying the same thing under different names?"

This tool OBSERVES. It does not DECIDE.

Inputs:
  - design/l2_1/intents/*.yaml

Logic:
  For every pair of panels within the same topic:
  1. Compute signal overlap:
     overlap_ratio = |intersection(signals)| / |union(signals)|
  2. Group overlaps by facet combination

Threshold:
  - Flag if overlap_ratio >= 0.70

Output:
  - JSON report (stdout or file)
  - Optional Markdown summary

Guarantees:
  - No judgment (only facts)
  - No auto-fix
  - Pure diagnostics
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import yaml

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent
INTENTS_DIR = REPO_ROOT / "design" / "l2_1" / "intents"

# Thresholds (configurable)
OVERLAP_THRESHOLD = 0.70  # ≥70% overlap = flagged
HIGH_OVERLAP_THRESHOLD = 0.85  # ≥85% = high overlap


def load_intents() -> List[Dict]:
    """Load all intent YAMLs."""
    intents = []

    if not INTENTS_DIR.exists():
        return intents

    for yaml_file in sorted(INTENTS_DIR.glob("AURORA_L2_INTENT_*.yaml")):
        try:
            with open(yaml_file, "r") as f:
                intent = yaml.safe_load(f)
                if intent:
                    intents.append(intent)
        except Exception as e:
            print(f"WARNING: Failed to load {yaml_file}: {e}", file=sys.stderr)

    return intents


def extract_signals(intent: Dict) -> Set[str]:
    """Extract signal indicators from an intent.

    Signals are derived from:
    - capability id
    - panel_class
    - data permissions
    - control flags
    - notes keywords (if present)
    """
    signals = set()

    # Capability
    capability = intent.get("capability")
    if capability and isinstance(capability, dict):
        cap_id = capability.get("id")
        if cap_id:
            signals.add(f"cap:{cap_id}")
            # Also add capability domain parts
            parts = cap_id.split(".")
            for part in parts:
                signals.add(f"cap_part:{part}")

    # Panel class
    panel_class = intent.get("panel_class")
    if panel_class:
        signals.add(f"class:{panel_class}")

    # Data permissions
    data = intent.get("data", {})
    for key, value in data.items():
        if value:
            signals.add(f"data:{key}")

    # Controls
    controls = intent.get("controls", {})
    for key, value in controls.items():
        if value:
            signals.add(f"control:{key}")

    # Notes keywords (simple extraction)
    notes = intent.get("notes", "")
    if notes:
        # Extract key terms (lowercase, significant words)
        words = notes.lower().split()
        keywords = {"error", "failure", "incident", "policy", "trace", "log",
                    "summary", "detail", "list", "status", "health", "cost",
                    "budget", "execution", "run", "agent", "violation"}
        for word in words:
            clean_word = "".join(c for c in word if c.isalnum())
            if clean_word in keywords:
                signals.add(f"keyword:{clean_word}")

    return signals


def compute_overlap(signals_a: Set[str], signals_b: Set[str]) -> float:
    """Compute overlap ratio between two signal sets.

    overlap_ratio = |intersection| / |union|
    """
    if not signals_a and not signals_b:
        return 0.0

    intersection = signals_a & signals_b
    union = signals_a | signals_b

    if not union:
        return 0.0

    return len(intersection) / len(union)


def detect_overlaps(intents: List[Dict], threshold: float = 0.70) -> List[Dict]:
    """Detect overlapping panels within the same topic."""
    # Group panels by topic
    panels_by_topic: Dict[str, List[Dict]] = defaultdict(list)

    for intent in intents:
        metadata = intent.get("metadata", {})
        topic_id = metadata.get("topic_id")
        if topic_id:
            panels_by_topic[topic_id].append({
                "panel_id": intent.get("panel_id"),
                "facet": metadata.get("facet"),
                "facet_criticality": metadata.get("facet_criticality"),
                "signals": extract_signals(intent),
                "panel_class": intent.get("panel_class"),
            })

    # Find overlaps
    overlaps = []

    for topic_id, panels in panels_by_topic.items():
        if len(panels) < 2:
            continue

        # Compare all pairs
        for panel_a, panel_b in combinations(panels, 2):
            overlap_ratio = compute_overlap(
                panel_a["signals"],
                panel_b["signals"]
            )

            if overlap_ratio >= threshold:
                # Determine overlap level
                if overlap_ratio >= HIGH_OVERLAP_THRESHOLD:
                    overlap_level = "HIGH"
                else:
                    overlap_level = "MEDIUM"

                # Find shared signals
                shared = panel_a["signals"] & panel_b["signals"]

                overlaps.append({
                    "topic_id": topic_id,
                    "panel_a": panel_a["panel_id"],
                    "panel_b": panel_b["panel_id"],
                    "facet_a": panel_a["facet"],
                    "facet_b": panel_b["facet"],
                    "class_a": panel_a["panel_class"],
                    "class_b": panel_b["panel_class"],
                    "overlap_ratio": round(overlap_ratio, 2),
                    "overlap_level": overlap_level,
                    "shared_signals": sorted(list(shared)),
                    "same_facet": panel_a["facet"] == panel_b["facet"],
                    "suggestion": _suggest_action(
                        overlap_ratio,
                        panel_a["facet"] == panel_b["facet"],
                        panel_a["panel_class"],
                        panel_b["panel_class"],
                    ),
                })

    # Sort by overlap ratio descending
    overlaps.sort(key=lambda x: -x["overlap_ratio"])

    return overlaps


def _suggest_action(
    overlap_ratio: float,
    same_facet: bool,
    class_a: str,
    class_b: str,
) -> str:
    """Generate a suggestion based on overlap characteristics.

    This is purely informational — not prescriptive.
    """
    if overlap_ratio >= HIGH_OVERLAP_THRESHOLD:
        if same_facet:
            return "High overlap within same facet — review for consolidation"
        else:
            return "High overlap across facets — verify semantic distinction"
    else:
        if same_facet and class_a == class_b:
            return "Consider if panels serve distinct user needs"
        else:
            return "Overlap detected — verify intentional differentiation"


def generate_summary(overlaps: List[Dict], total_panels: int, threshold: float = 0.70) -> Dict:
    """Generate summary statistics."""
    high_overlaps = [o for o in overlaps if o["overlap_level"] == "HIGH"]
    same_facet = [o for o in overlaps if o["same_facet"]]
    cross_facet = [o for o in overlaps if not o["same_facet"]]

    # Group by topic
    topics_with_overlap = set(o["topic_id"] for o in overlaps)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_panels_analyzed": total_panels,
        "total_overlaps_detected": len(overlaps),
        "high_overlaps": len(high_overlaps),
        "medium_overlaps": len(overlaps) - len(high_overlaps),
        "same_facet_overlaps": len(same_facet),
        "cross_facet_overlaps": len(cross_facet),
        "topics_with_overlap": len(topics_with_overlap),
        "threshold_used": threshold,
    }


def format_markdown(overlaps: List[Dict], summary: Dict) -> str:
    """Format results as Markdown report."""
    lines = [
        "# Facet Overlap Detection Report",
        "",
        f"**Generated:** {summary['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Panels analyzed: {summary['total_panels_analyzed']}",
        f"- Overlap threshold: {summary['threshold_used'] * 100:.0f}%",
        f"- Total overlaps detected: {summary['total_overlaps_detected']}",
        f"- High overlaps (≥{HIGH_OVERLAP_THRESHOLD * 100:.0f}%): {summary['high_overlaps']}",
        f"- Topics with overlap: {summary['topics_with_overlap']}",
        "",
        "### Overlap Distribution",
        "",
        f"| Type | Count |",
        f"|------|-------|",
        f"| Same facet | {summary['same_facet_overlaps']} |",
        f"| Cross facet | {summary['cross_facet_overlaps']} |",
        "",
    ]

    if not overlaps:
        lines.extend([
            "## No Overlaps Detected",
            "",
            "No panel pairs exceeded the overlap threshold.",
        ])
    else:
        # High overlaps
        high_overlaps = [o for o in overlaps if o["overlap_level"] == "HIGH"]
        if high_overlaps:
            lines.extend([
                "## High Overlap Pairs",
                "",
                "| Panel A | Panel B | Overlap | Same Facet | Suggestion |",
                "|---------|---------|---------|------------|------------|",
            ])
            for o in high_overlaps:
                same = "Yes" if o["same_facet"] else "No"
                lines.append(
                    f"| {o['panel_a']} | {o['panel_b']} | "
                    f"{o['overlap_ratio'] * 100:.0f}% | {same} | {o['suggestion']} |"
                )
            lines.append("")

        # Details for high overlaps
        if high_overlaps:
            lines.extend([
                "### Shared Signals (High Overlap)",
                "",
            ])
            for o in high_overlaps[:5]:  # Limit to top 5
                lines.append(f"**{o['panel_a']} ↔ {o['panel_b']}**")
                lines.append(f"- Topic: {o['topic_id']}")
                lines.append(f"- Facets: {o['facet_a'] or 'none'} / {o['facet_b'] or 'none'}")
                lines.append(f"- Shared: {', '.join(o['shared_signals'][:10])}")
                if len(o['shared_signals']) > 10:
                    lines.append(f"  ... and {len(o['shared_signals']) - 10} more")
                lines.append("")

        # Medium overlaps summary
        medium_overlaps = [o for o in overlaps if o["overlap_level"] == "MEDIUM"]
        if medium_overlaps:
            lines.extend([
                "## Medium Overlap Pairs",
                "",
                "| Panel A | Panel B | Overlap | Topic |",
                "|---------|---------|---------|-------|",
            ])
            for o in medium_overlaps[:10]:  # Limit display
                lines.append(
                    f"| {o['panel_a']} | {o['panel_b']} | "
                    f"{o['overlap_ratio'] * 100:.0f}% | {o['topic_id']} |"
                )
            if len(medium_overlaps) > 10:
                lines.append(f"| ... | ... | ... | ({len(medium_overlaps) - 10} more) |")
            lines.append("")

    lines.extend([
        "---",
        "",
        "*This report is observational. It does not modify any files or affect pipeline execution.*",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Detect overlapping panels within topics (READ ONLY)"
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "both"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.70,
        help="Overlap threshold (default: 0.70)",
    )
    parser.add_argument(
        "--high-only",
        action="store_true",
        help="Only show high overlap pairs",
    )
    args = parser.parse_args()

    # Use threshold from args
    threshold = args.threshold

    # Load data
    intents = load_intents()

    # Analyze
    overlaps = detect_overlaps(intents, threshold)

    # Filter if requested
    if args.high_only:
        overlaps = [o for o in overlaps if o["overlap_level"] == "HIGH"]

    # Generate summary
    summary = generate_summary(overlaps, len(intents), threshold)

    # Format output
    if args.format == "json":
        output = json.dumps({"summary": summary, "overlaps": overlaps}, indent=2)
    elif args.format == "markdown":
        output = format_markdown(overlaps, summary)
    else:  # both
        json_output = json.dumps({"summary": summary, "overlaps": overlaps}, indent=2)
        md_output = format_markdown(overlaps, summary)
        output = f"# JSON Output\n\n```json\n{json_output}\n```\n\n{md_output}"

    # Write output
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Report written to: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
