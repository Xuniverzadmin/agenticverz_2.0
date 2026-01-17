#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: manual | CI
#   Execution: sync
# Role: Analyze slot pressure per topic — READ ONLY diagnostic
# Reference: PANEL_STRUCTURE_PIPELINE.md Phase 2

"""
Facet → Slot Pressure Analyzer (Phase 2 Tool 1)

Question it answers:
  "Which facets are competing for too few slots within a topic?"

This tool OBSERVES. It does not DECIDE.

Inputs:
  - design/l2_1/intents/*.yaml
  - design/l2_1/UI_TOPOLOGY_TEMPLATE.yaml

Output:
  - JSON report (stdout or file)
  - Optional Markdown summary

Guarantees:
  - No YAML writes
  - No pipeline blocking
  - Deterministic
  - Human-readable
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import yaml

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent
TOPOLOGY_PATH = REPO_ROOT / "design" / "l2_1" / "UI_TOPOLOGY_TEMPLATE.yaml"
INTENTS_DIR = REPO_ROOT / "design" / "l2_1" / "intents"

# Thresholds (configurable)
HIGH_PRESSURE_THRESHOLD = 0.90  # ≥90% utilization = HIGH pressure
MEDIUM_PRESSURE_THRESHOLD = 0.70  # ≥70% = MEDIUM
FACET_DOMINANCE_THRESHOLD = 0.60  # ≥60% of slots = dominant


def load_yaml(path: Path) -> Dict:
    """Load YAML file safely."""
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def load_topology() -> Dict[str, int]:
    """Load topology and extract panel_slots per topic.

    Returns:
        Dict mapping topic_id (DOMAIN.SUBDOMAIN.TOPIC) to panel_slots count
    """
    topology = load_yaml(TOPOLOGY_PATH)
    if not topology:
        print(f"ERROR: Topology not found at {TOPOLOGY_PATH}", file=sys.stderr)
        sys.exit(1)

    slots: Dict[str, int] = {}

    for domain in topology.get("domains", []):
        domain_id = domain.get("id", "")
        for subdomain in domain.get("subdomains", []):
            subdomain_id = subdomain.get("id", "")
            for topic in subdomain.get("topics", []):
                topic_id = topic.get("id", "")
                panel_slots = topic.get("panel_slots", 4)
                key = f"{domain_id}.{subdomain_id}.{topic_id}"
                slots[key] = panel_slots

    return slots


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


def analyze_slot_pressure(
    topology_slots: Dict[str, int],
    intents: List[Dict],
) -> List[Dict]:
    """Analyze slot pressure per topic.

    For each topic:
    1. Count panel_slots from topology
    2. Group panels by facet
    3. Compute utilization_ratio
    """
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
            })

    # Analyze each topic
    results = []

    for topic_id, slots in sorted(topology_slots.items()):
        panels = panels_by_topic.get(topic_id, [])
        total_panels = len(panels)

        # Group by facet
        facets: Dict[str, int] = defaultdict(int)
        for panel in panels:
            facet = panel.get("facet") or "_unassigned"
            facets[facet] += 1

        # Calculate pressure
        utilization_ratio = total_panels / slots if slots > 0 else 0

        if utilization_ratio >= HIGH_PRESSURE_THRESHOLD:
            slot_pressure = "HIGH"
        elif utilization_ratio >= MEDIUM_PRESSURE_THRESHOLD:
            slot_pressure = "MEDIUM"
        else:
            slot_pressure = "LOW"

        # Check for facet dominance
        dominant_facet = None
        if total_panels > 0:
            for facet, count in facets.items():
                if count / total_panels >= FACET_DOMINANCE_THRESHOLD:
                    dominant_facet = facet
                    break

        # Calculate available slots
        available_slots = max(0, slots - total_panels)

        result = {
            "topic_id": topic_id,
            "panel_slots": slots,
            "total_panels": total_panels,
            "available_slots": available_slots,
            "utilization_ratio": round(utilization_ratio, 2),
            "slot_pressure": slot_pressure,
            "facets": dict(facets) if facets else {},
            "dominant_facet": dominant_facet,
        }

        results.append(result)

    return results


def generate_summary(results: List[Dict]) -> Dict:
    """Generate summary statistics."""
    high_pressure = [r for r in results if r["slot_pressure"] == "HIGH"]
    medium_pressure = [r for r in results if r["slot_pressure"] == "MEDIUM"]
    low_pressure = [r for r in results if r["slot_pressure"] == "LOW"]
    dominant_topics = [r for r in results if r["dominant_facet"]]

    total_slots = sum(r["panel_slots"] for r in results)
    total_panels = sum(r["total_panels"] for r in results)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_topics": len(results),
        "total_slots": total_slots,
        "total_panels": total_panels,
        "overall_utilization": round(total_panels / total_slots, 2) if total_slots > 0 else 0,
        "pressure_distribution": {
            "HIGH": len(high_pressure),
            "MEDIUM": len(medium_pressure),
            "LOW": len(low_pressure),
        },
        "topics_with_dominant_facet": len(dominant_topics),
        "high_pressure_topics": [r["topic_id"] for r in high_pressure],
    }


def format_markdown(results: List[Dict], summary: Dict) -> str:
    """Format results as Markdown report."""
    lines = [
        "# Facet Slot Pressure Report",
        "",
        f"**Generated:** {summary['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Total topics: {summary['total_topics']}",
        f"- Total slots: {summary['total_slots']}",
        f"- Total panels: {summary['total_panels']}",
        f"- Overall utilization: {summary['overall_utilization'] * 100:.0f}%",
        "",
        "### Pressure Distribution",
        "",
        f"| Pressure | Count |",
        f"|----------|-------|",
        f"| HIGH (≥90%) | {summary['pressure_distribution']['HIGH']} |",
        f"| MEDIUM (≥70%) | {summary['pressure_distribution']['MEDIUM']} |",
        f"| LOW (<70%) | {summary['pressure_distribution']['LOW']} |",
        "",
    ]

    # High pressure topics
    high_pressure = [r for r in results if r["slot_pressure"] == "HIGH"]
    if high_pressure:
        lines.extend([
            "## High Pressure Topics",
            "",
            "These topics are at or near slot capacity:",
            "",
            "| Topic | Slots | Used | Available | Utilization | Dominant Facet |",
            "|-------|-------|------|-----------|-------------|----------------|",
        ])
        for r in high_pressure:
            dominant = r["dominant_facet"] or "-"
            lines.append(
                f"| {r['topic_id']} | {r['panel_slots']} | {r['total_panels']} | "
                f"{r['available_slots']} | {r['utilization_ratio'] * 100:.0f}% | {dominant} |"
            )
        lines.append("")

    # Facet distribution for high pressure topics
    if high_pressure:
        lines.extend([
            "### Facet Distribution (High Pressure Topics)",
            "",
        ])
        for r in high_pressure:
            lines.append(f"**{r['topic_id']}**")
            for facet, count in sorted(r["facets"].items(), key=lambda x: -x[1]):
                pct = count / r["total_panels"] * 100 if r["total_panels"] > 0 else 0
                lines.append(f"- {facet}: {count} panels ({pct:.0f}%)")
            lines.append("")

    # Topics with dominant facets
    dominant_topics = [r for r in results if r["dominant_facet"] and r["slot_pressure"] != "HIGH"]
    if dominant_topics:
        lines.extend([
            "## Topics with Dominant Facet (Not High Pressure)",
            "",
            "| Topic | Dominant Facet | Facet Share |",
            "|-------|----------------|-------------|",
        ])
        for r in dominant_topics:
            facet_count = r["facets"].get(r["dominant_facet"], 0)
            share = facet_count / r["total_panels"] * 100 if r["total_panels"] > 0 else 0
            lines.append(f"| {r['topic_id']} | {r['dominant_facet']} | {share:.0f}% |")
        lines.append("")

    lines.extend([
        "---",
        "",
        "*This report is observational. It does not modify any files or affect pipeline execution.*",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze facet slot pressure per topic (READ ONLY)"
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
        "--high-only",
        action="store_true",
        help="Only show high pressure topics",
    )
    args = parser.parse_args()

    # Load data
    topology_slots = load_topology()
    intents = load_intents()

    # Analyze
    results = analyze_slot_pressure(topology_slots, intents)

    # Filter if requested
    if args.high_only:
        results = [r for r in results if r["slot_pressure"] == "HIGH"]

    # Generate summary
    summary = generate_summary(results)

    # Format output
    if args.format == "json":
        output = json.dumps({"summary": summary, "topics": results}, indent=2)
    elif args.format == "markdown":
        output = format_markdown(results, summary)
    else:  # both
        json_output = json.dumps({"summary": summary, "topics": results}, indent=2)
        md_output = format_markdown(results, summary)
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
