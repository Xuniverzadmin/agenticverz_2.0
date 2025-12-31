#!/usr/bin/env python3
"""
Architecture Incident Logger

Logs architecture violations to an append-only incident log.
Triggered by: intent_validator.py, temporal_detector.py, LIT/BIT failures.

Usage:
    # Log an incident
    python scripts/ops/architecture_incident_logger.py log \
        --code TV-001 \
        --file backend/app/api/runs.py \
        --layer L2 \
        --summary "Sync layer importing async worker"

    # View recent incidents
    python scripts/ops/architecture_incident_logger.py view --last 10

    # Generate report
    python scripts/ops/architecture_incident_logger.py report

Reference: PIN-246 (Architecture Governance Implementation)
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Incident log location
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
INCIDENT_LOG = LOG_DIR / "architecture_incidents.log"


def ensure_log_dir():
    """Ensure log directory exists."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def log_incident(
    code: str,
    file: str,
    layer: Optional[str] = None,
    author: Optional[str] = None,
    summary: Optional[str] = None,
    source: Optional[str] = None,
) -> dict:
    """
    Log an architecture incident.

    Args:
        code: Violation code (TV-001, INTENT-001, LAYER-003, BIT-FAIL, LIT-FAIL)
        file: File path where violation occurred
        layer: Layer classification if known
        author: Author if known (from git blame or session)
        summary: Human-readable summary
        source: Tool that detected the violation

    Returns:
        The incident record
    """
    ensure_log_dir()

    # Generate incident ID
    timestamp = datetime.utcnow()
    incident_id = f"ARCH-{timestamp.strftime('%Y%m%d-%H%M%S')}-{code}"

    # Build incident record
    incident = {
        "incident_id": incident_id,
        "timestamp": timestamp.isoformat() + "Z",
        "violation_code": code,
        "file": file,
        "layer": layer or "unknown",
        "author": author or "unknown",
        "summary": summary or "",
        "source": source or "manual",
    }

    # Append to log (one JSON object per line)
    with open(INCIDENT_LOG, "a") as f:
        f.write(json.dumps(incident) + "\n")

    return incident


def view_incidents(last_n: int = 10) -> list:
    """View recent incidents."""
    if not INCIDENT_LOG.exists():
        return []

    incidents = []
    with open(INCIDENT_LOG, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    incidents.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    return incidents[-last_n:] if last_n > 0 else incidents


def generate_report() -> dict:
    """Generate incident report with statistics."""
    incidents = view_incidents(last_n=0)  # Get all

    if not incidents:
        return {
            "total": 0,
            "by_code": {},
            "by_layer": {},
            "by_tier": {},
            "recent": [],
        }

    # Tier mapping
    tier_map = {
        # Tier A: Structural violations
        "TV-001": "A", "TV-002": "A", "TV-003": "A",
        "TV-004": "A", "TV-005": "A", "TV-006": "A",
        "INTENT-001": "A", "INTENT-002": "A", "INTENT-003": "A",
        "LAYER-001": "A", "LAYER-002": "A", "LAYER-003": "A",
        # Tier B: Integration violations
        "LIT-FAIL": "B", "BIT-FAIL": "B",
        # Tier C: Governance friction
        "FALSE-POS": "C", "HEURISTIC": "C",
    }

    by_code = {}
    by_layer = {}
    by_tier = {"A": 0, "B": 0, "C": 0, "unknown": 0}

    for inc in incidents:
        code = inc.get("violation_code", "unknown")
        layer = inc.get("layer", "unknown")
        tier = tier_map.get(code, "unknown")

        by_code[code] = by_code.get(code, 0) + 1
        by_layer[layer] = by_layer.get(layer, 0) + 1
        by_tier[tier] = by_tier.get(tier, 0) + 1

    return {
        "total": len(incidents),
        "by_code": by_code,
        "by_layer": by_layer,
        "by_tier": by_tier,
        "recent": incidents[-5:],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Architecture Incident Logger",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Log command
    log_parser = subparsers.add_parser("log", help="Log an incident")
    log_parser.add_argument("--code", required=True, help="Violation code (e.g., TV-001)")
    log_parser.add_argument("--file", required=True, help="File path")
    log_parser.add_argument("--layer", help="Layer classification")
    log_parser.add_argument("--author", help="Author")
    log_parser.add_argument("--summary", help="Summary description")
    log_parser.add_argument("--source", help="Detection source tool")

    # View command
    view_parser = subparsers.add_parser("view", help="View recent incidents")
    view_parser.add_argument("--last", type=int, default=10, help="Number of incidents")
    view_parser.add_argument("--json", action="store_true", help="JSON output")

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate report")
    report_parser.add_argument("--json", action="store_true", help="JSON output")

    args = parser.parse_args()

    if args.command == "log":
        incident = log_incident(
            code=args.code,
            file=args.file,
            layer=args.layer,
            author=args.author,
            summary=args.summary,
            source=args.source,
        )
        print(f"Logged: {incident['incident_id']}")
        print(json.dumps(incident, indent=2))

    elif args.command == "view":
        incidents = view_incidents(args.last)
        if not incidents:
            print("No incidents recorded.")
            return

        if args.json:
            print(json.dumps(incidents, indent=2))
        else:
            for inc in incidents:
                print(f"[{inc['timestamp']}] {inc['violation_code']} - {inc['file']}")
                if inc.get('summary'):
                    print(f"  {inc['summary']}")

    elif args.command == "report":
        report = generate_report()

        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print("=" * 60)
            print("ARCHITECTURE INCIDENT REPORT")
            print("=" * 60)
            print(f"\nTotal Incidents: {report['total']}")

            print("\nBy Tier:")
            print(f"  A (Structural):   {report['by_tier'].get('A', 0)}")
            print(f"  B (Integration):  {report['by_tier'].get('B', 0)}")
            print(f"  C (Friction):     {report['by_tier'].get('C', 0)}")

            print("\nBy Code:")
            for code, count in sorted(report['by_code'].items(), key=lambda x: -x[1]):
                print(f"  {code}: {count}")

            print("\nBy Layer:")
            for layer, count in sorted(report['by_layer'].items(), key=lambda x: -x[1]):
                print(f"  {layer}: {count}")

            if report['recent']:
                print("\nRecent Incidents:")
                for inc in report['recent']:
                    print(f"  [{inc['timestamp'][:10]}] {inc['violation_code']} - {inc['file']}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
