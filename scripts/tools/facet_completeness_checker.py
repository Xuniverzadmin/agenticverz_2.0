#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: manual | CI
#   Execution: sync
# Role: Check facet completeness (blind spot detection) — READ ONLY diagnostic
# Reference: PANEL_STRUCTURE_PIPELINE.md Phase 2

"""
Facet Completeness Checker (Phase 2 Tool 3)

Question it answers:
  "Which declared information needs are weakly represented or missing?"

This tool OBSERVES. It does not DECIDE.

Inputs:
  - design/l2_1/INTENT_LEDGER.md (facet declarations)
  - design/l2_1/intents/*.yaml

Logic:
  For each declared facet:
  1. Count panels assigned to facet
  2. Compare against:
     - facet_criticality
     - total panels in domain/topic

Rules (configurable):
  - HIGH criticality → expect ≥2 panels
  - MEDIUM → ≥1
  - LOW → informational only

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
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import yaml

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent
LEDGER_PATH = REPO_ROOT / "design" / "l2_1" / "INTENT_LEDGER.md"
INTENTS_DIR = REPO_ROOT / "design" / "l2_1" / "intents"

# Configurable thresholds
MINIMUM_PANELS = {
    "HIGH": 2,
    "MEDIUM": 1,
    "LOW": 0,  # informational only
}


@dataclass
class FacetDeclaration:
    """A facet as declared in the ledger."""
    facet_id: str
    purpose: str
    criticality: str
    domain: str
    expected_panels: List[str]


def parse_facets_from_ledger(path: Path) -> List[FacetDeclaration]:
    """Parse facet declarations from INTENT_LEDGER.md."""
    if not path.exists():
        print(f"ERROR: Ledger not found at {path}", file=sys.stderr)
        sys.exit(1)

    with open(path, "r") as f:
        content = f.read()

    facets = []

    # Split into sections and find Facets section
    sections = re.split(r"^## ", content, flags=re.MULTILINE)

    for section in sections:
        if section.startswith("Facets"):
            # Parse facet entries
            facet_blocks = re.split(r"^### Facet: ", section, flags=re.MULTILINE)

            for block in facet_blocks[1:]:  # Skip header
                lines = block.strip().split("\n")
                if not lines:
                    continue

                facet_id = lines[0].strip()
                fields = {}
                panels = []
                in_panels = False

                for line in lines[1:]:
                    line_stripped = line.strip()

                    if line_stripped.startswith("Panels:"):
                        in_panels = True
                        continue

                    if in_panels:
                        if line_stripped.startswith("- "):
                            # Extract panel_id
                            panel_match = re.match(r"^- ([A-Z0-9\-]+)", line_stripped)
                            if panel_match:
                                panels.append(panel_match.group(1))
                        elif ":" in line_stripped and not line_stripped.startswith("-"):
                            in_panels = False
                            field_match = re.match(r"^(\w+):\s*(.*)$", line_stripped)
                            if field_match:
                                key, value = field_match.groups()
                                fields[key.lower()] = value.strip()
                    else:
                        field_match = re.match(r"^(\w+):\s*(.*)$", line_stripped)
                        if field_match:
                            key, value = field_match.groups()
                            fields[key.lower()] = value.strip()

                facets.append(FacetDeclaration(
                    facet_id=facet_id,
                    purpose=fields.get("purpose", ""),
                    criticality=fields.get("criticality", "MEDIUM"),
                    domain=fields.get("domain", "UNKNOWN"),
                    expected_panels=panels,
                ))

    return facets


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


def check_completeness(
    facets: List[FacetDeclaration],
    intents: List[Dict],
) -> List[Dict]:
    """Check completeness of each declared facet."""
    # Build panel → facet mapping from intents
    panels_by_facet: Dict[str, List[str]] = defaultdict(list)
    all_panel_ids = set()

    for intent in intents:
        panel_id = intent.get("panel_id")
        if panel_id:
            all_panel_ids.add(panel_id)
            metadata = intent.get("metadata", {})
            facet = metadata.get("facet")
            if facet:
                panels_by_facet[facet].append(panel_id)

    # Check each declared facet
    results = []

    for facet in facets:
        # Actual panels assigned in intents
        actual_panels = panels_by_facet.get(facet.facet_id, [])
        panels_present = len(actual_panels)

        # Expected minimum based on criticality
        expected_minimum = MINIMUM_PANELS.get(facet.criticality, 1)

        # Check which expected panels are missing
        expected_set = set(facet.expected_panels)
        actual_set = set(actual_panels)
        missing_panels = expected_set - actual_set
        extra_panels = actual_set - expected_set

        # Determine status
        if panels_present == 0:
            status = "MISSING"
        elif panels_present < expected_minimum:
            status = "UNDERREPRESENTED"
        elif missing_panels:
            status = "INCOMPLETE"
        else:
            status = "ADEQUATE"

        # Coverage ratio
        if facet.expected_panels:
            coverage_ratio = len(actual_set & expected_set) / len(expected_set)
        else:
            coverage_ratio = 1.0 if panels_present > 0 else 0.0

        results.append({
            "facet_id": facet.facet_id,
            "purpose": facet.purpose,
            "criticality": facet.criticality,
            "domain": facet.domain,
            "expected_minimum": expected_minimum,
            "expected_panels": facet.expected_panels,
            "panels_present": panels_present,
            "actual_panels": actual_panels,
            "missing_panels": list(missing_panels),
            "extra_panels": list(extra_panels),
            "coverage_ratio": round(coverage_ratio, 2),
            "status": status,
        })

    # Sort by status severity
    status_order = {"MISSING": 0, "UNDERREPRESENTED": 1, "INCOMPLETE": 2, "ADEQUATE": 3}
    results.sort(key=lambda x: (status_order.get(x["status"], 99), -len(x["missing_panels"])))

    return results


def generate_summary(results: List[Dict]) -> Dict:
    """Generate summary statistics."""
    missing = [r for r in results if r["status"] == "MISSING"]
    underrepresented = [r for r in results if r["status"] == "UNDERREPRESENTED"]
    incomplete = [r for r in results if r["status"] == "INCOMPLETE"]
    adequate = [r for r in results if r["status"] == "ADEQUATE"]

    # Count by criticality
    high_crit = [r for r in results if r["criticality"] == "HIGH"]
    high_crit_issues = [r for r in high_crit if r["status"] in ("MISSING", "UNDERREPRESENTED")]

    total_expected = sum(len(r["expected_panels"]) for r in results)
    total_present = sum(r["panels_present"] for r in results)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_facets": len(results),
        "status_distribution": {
            "MISSING": len(missing),
            "UNDERREPRESENTED": len(underrepresented),
            "INCOMPLETE": len(incomplete),
            "ADEQUATE": len(adequate),
        },
        "high_criticality_facets": len(high_crit),
        "high_criticality_with_issues": len(high_crit_issues),
        "total_expected_panels": total_expected,
        "total_present_panels": total_present,
        "overall_coverage": round(total_present / total_expected, 2) if total_expected > 0 else 1.0,
        "thresholds_used": MINIMUM_PANELS,
    }


def format_markdown(results: List[Dict], summary: Dict) -> str:
    """Format results as Markdown report."""
    lines = [
        "# Facet Completeness Report",
        "",
        f"**Generated:** {summary['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Total facets declared: {summary['total_facets']}",
        f"- Overall coverage: {summary['overall_coverage'] * 100:.0f}%",
        f"- HIGH criticality facets: {summary['high_criticality_facets']}",
        f"- HIGH criticality with issues: {summary['high_criticality_with_issues']}",
        "",
        "### Status Distribution",
        "",
        "| Status | Count | Meaning |",
        "|--------|-------|---------|",
        f"| MISSING | {summary['status_distribution']['MISSING']} | No panels assigned |",
        f"| UNDERREPRESENTED | {summary['status_distribution']['UNDERREPRESENTED']} | Below minimum for criticality |",
        f"| INCOMPLETE | {summary['status_distribution']['INCOMPLETE']} | Missing expected panels |",
        f"| ADEQUATE | {summary['status_distribution']['ADEQUATE']} | Meets expectations |",
        "",
        "### Minimum Panel Thresholds",
        "",
        "| Criticality | Minimum Panels |",
        "|-------------|----------------|",
    ]
    for crit, minimum in MINIMUM_PANELS.items():
        lines.append(f"| {crit} | {minimum} |")
    lines.append("")

    # Issues section
    issues = [r for r in results if r["status"] != "ADEQUATE"]
    if issues:
        lines.extend([
            "## Facets Requiring Attention",
            "",
        ])

        # Group by status
        for status in ["MISSING", "UNDERREPRESENTED", "INCOMPLETE"]:
            status_issues = [r for r in issues if r["status"] == status]
            if status_issues:
                lines.extend([
                    f"### {status}",
                    "",
                    "| Facet | Criticality | Present | Expected | Gap |",
                    "|-------|-------------|---------|----------|-----|",
                ])
                for r in status_issues:
                    gap = r["expected_minimum"] - r["panels_present"]
                    lines.append(
                        f"| {r['facet_id']} | {r['criticality']} | "
                        f"{r['panels_present']} | {r['expected_minimum']} | {gap} |"
                    )
                lines.append("")

        # Details for missing/underrepresented
        critical_issues = [r for r in issues if r["criticality"] == "HIGH" and r["status"] in ("MISSING", "UNDERREPRESENTED")]
        if critical_issues:
            lines.extend([
                "### High Criticality Issues (Detail)",
                "",
            ])
            for r in critical_issues:
                lines.append(f"**{r['facet_id']}** ({r['status']})")
                lines.append(f"- Purpose: {r['purpose']}")
                lines.append(f"- Domain: {r['domain']}")
                lines.append(f"- Panels present: {r['panels_present']} (need {r['expected_minimum']})")
                if r['missing_panels']:
                    lines.append(f"- Missing: {', '.join(r['missing_panels'])}")
                lines.append("")

    # Adequate facets summary
    adequate = [r for r in results if r["status"] == "ADEQUATE"]
    if adequate:
        lines.extend([
            "## Adequate Facets",
            "",
            f"The following {len(adequate)} facets meet their coverage expectations:",
            "",
        ])
        for r in adequate:
            lines.append(f"- **{r['facet_id']}** ({r['criticality']}): {r['panels_present']} panels")
        lines.append("")

    lines.extend([
        "---",
        "",
        "*This report is observational. It does not modify any files or affect pipeline execution.*",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Check facet completeness (READ ONLY)"
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
        "--issues-only",
        action="store_true",
        help="Only show facets with issues",
    )
    parser.add_argument(
        "--high-min",
        type=int,
        default=MINIMUM_PANELS["HIGH"],
        help=f"Minimum panels for HIGH criticality (default: {MINIMUM_PANELS['HIGH']})",
    )
    parser.add_argument(
        "--medium-min",
        type=int,
        default=MINIMUM_PANELS["MEDIUM"],
        help=f"Minimum panels for MEDIUM criticality (default: {MINIMUM_PANELS['MEDIUM']})",
    )
    args = parser.parse_args()

    # Update thresholds if specified
    MINIMUM_PANELS["HIGH"] = args.high_min
    MINIMUM_PANELS["MEDIUM"] = args.medium_min

    # Load data
    facets = parse_facets_from_ledger(LEDGER_PATH)
    intents = load_intents()

    if not facets:
        print("No facets found in ledger. Is the Facets section present?", file=sys.stderr)
        sys.exit(0)

    # Analyze
    results = check_completeness(facets, intents)

    # Filter if requested
    if args.issues_only:
        results = [r for r in results if r["status"] != "ADEQUATE"]

    # Generate summary
    summary = generate_summary(results)

    # Format output
    if args.format == "json":
        output = json.dumps({"summary": summary, "facets": results}, indent=2)
    elif args.format == "markdown":
        output = format_markdown(results, summary)
    else:  # both
        json_output = json.dumps({"summary": summary, "facets": results}, indent=2)
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
