#!/usr/bin/env python3
"""
SDSR Status Report

Generates a comprehensive report of SDSR system status including:
- Capability status by domain (OBSERVED/DECLARED/ASSUMED/DEFERRED)
- Panels with missing capability bindings
- Scenarios in old vs new format
- Promotion guard readiness

Usage:
    python backend/scripts/sdsr/report_status.py
    python backend/scripts/sdsr/report_status.py --domain ACTIVITY
    python backend/scripts/sdsr/report_status.py --json

Author: AURORA L2 Automation
Reference: PIN-370
"""

import argparse
import json
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

import yaml

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent.parent
INTENTS_DIR = REPO_ROOT / "design/l2_1/intents"
CAPABILITY_REGISTRY = REPO_ROOT / "backend/AURORA_L2_CAPABILITY_REGISTRY"
SDSR_SCENARIOS_DIR = REPO_ROOT / "backend/scripts/sdsr/scenarios"
INVARIANTS_DIR = REPO_ROOT / "backend/sdsr/invariants"


@dataclass
class DomainStats:
    """Statistics for a domain."""
    domain: str
    observed: int = 0
    declared: int = 0
    assumed: int = 0
    deferred: int = 0
    total: int = 0
    panels: List[str] = field(default_factory=list)

    @property
    def ready_pct(self) -> float:
        """Percentage of capabilities that are OBSERVED."""
        if self.total == 0:
            return 0.0
        return (self.observed / self.total) * 100


@dataclass
class ScenarioStats:
    """Scenario format statistics."""
    new_format: int = 0
    old_format: int = 0
    old_format_files: List[str] = field(default_factory=list)


def load_yaml(path: Path) -> Optional[Dict]:
    """Load YAML file safely."""
    if not path.exists():
        return None
    with open(path) as f:
        return yaml.safe_load(f)


def get_domain_stats() -> Dict[str, DomainStats]:
    """Get capability status by domain from intent YAMLs."""
    stats: Dict[str, DomainStats] = {}

    for f in sorted(INTENTS_DIR.glob("AURORA_L2_INTENT_*.yaml")):
        data = load_yaml(f)
        if not data:
            continue

        domain = data.get('metadata', {}).get('domain', 'UNKNOWN')
        status = data.get('capability', {}).get('status', 'UNKNOWN').upper()
        panel_id = data.get('panel_id', f.stem)

        if domain not in stats:
            stats[domain] = DomainStats(domain=domain)

        stats[domain].total += 1
        stats[domain].panels.append(panel_id)

        if status == 'OBSERVED':
            stats[domain].observed += 1
        elif status == 'DECLARED':
            stats[domain].declared += 1
        elif status == 'ASSUMED':
            stats[domain].assumed += 1
        elif status == 'DEFERRED':
            stats[domain].deferred += 1

    return stats


def get_scenario_stats() -> ScenarioStats:
    """Get scenario format statistics."""
    stats = ScenarioStats()

    for f in sorted(SDSR_SCENARIOS_DIR.glob("SDSR-*.yaml")):
        content = f.read_text()
        if "invariant_ids:" in content:
            stats.new_format += 1
        elif "invariants:" in content:
            stats.old_format += 1
            stats.old_format_files.append(f.name)

    return stats


def get_missing_capabilities() -> List[str]:
    """Find panels with null endpoints that aren't DEFERRED."""
    missing = []

    for f in sorted(INTENTS_DIR.glob("AURORA_L2_INTENT_*.yaml")):
        data = load_yaml(f)
        if not data:
            continue

        endpoint = data.get('capability', {}).get('assumed_endpoint')
        status = data.get('capability', {}).get('status', '').upper()
        panel_id = data.get('panel_id', f.stem)

        if (endpoint is None or endpoint == 'null') and status != 'DEFERRED':
            missing.append(panel_id)

    return missing


def get_invariant_counts() -> Dict[str, int]:
    """Get invariant counts by domain."""
    import re
    counts = {}

    # Count from invariant files
    domain_files = {
        'L0_TRANSPORT': 'transport.py',
        'ACTIVITY': 'activity.py',
        'LOGS': 'logs.py',
        'INCIDENTS': 'incidents.py',
        'POLICIES': 'policies.py',
    }

    for domain, fname in domain_files.items():
        fpath = INVARIANTS_DIR / fname
        if fpath.exists():
            content = fpath.read_text()
            # Count "id": patterns (invariant definitions)
            matches = re.findall(r'"id":', content)
            counts[domain] = len(matches)
        else:
            counts[domain] = 0

    return counts


def print_report(stats: Dict[str, DomainStats], scenarios: ScenarioStats,
                 missing: List[str], invariants: Dict[str, int],
                 domain_filter: Optional[str] = None):
    """Print formatted report."""
    print("=" * 70)
    print("SDSR STATUS REPORT")
    print(f"Generated: {datetime.now().isoformat()}")
    print("=" * 70)
    print()

    # Domain summary
    print("CAPABILITY STATUS BY DOMAIN")
    print("-" * 70)
    print(f"{'Domain':<15} {'OBSERVED':>10} {'DECLARED':>10} {'ASSUMED':>10} {'DEFERRED':>10} {'Ready%':>8}")
    print("-" * 70)

    total_observed = 0
    total_declared = 0
    total_assumed = 0
    total_deferred = 0
    total_all = 0

    for domain, s in sorted(stats.items()):
        if domain_filter and domain != domain_filter:
            continue
        print(f"{domain:<15} {s.observed:>10} {s.declared:>10} {s.assumed:>10} {s.deferred:>10} {s.ready_pct:>7.1f}%")
        total_observed += s.observed
        total_declared += s.declared
        total_assumed += s.assumed
        total_deferred += s.deferred
        total_all += s.total

    print("-" * 70)
    total_pct = (total_observed / total_all * 100) if total_all > 0 else 0
    print(f"{'TOTAL':<15} {total_observed:>10} {total_declared:>10} {total_assumed:>10} {total_deferred:>10} {total_pct:>7.1f}%")
    print()

    # Invariant counts
    print("INVARIANT COUNTS BY DOMAIN")
    print("-" * 40)
    for domain, count in sorted(invariants.items()):
        print(f"  {domain}: {count} invariants")
    print()

    # Scenario format
    print("SCENARIO FORMAT STATUS")
    print("-" * 40)
    print(f"  New format (invariant_ids): {scenarios.new_format}")
    print(f"  Old format (invariants):    {scenarios.old_format}")
    if scenarios.old_format > 0:
        print(f"  Migration needed:           {scenarios.old_format} files")
    print()

    # Missing capabilities
    if missing:
        print("PANELS NEEDING CAPABILITY BINDING")
        print("-" * 40)
        for panel in missing:
            print(f"  - {panel}")
        print()

    # Promotion readiness
    print("PROMOTION GUARD READINESS")
    print("-" * 40)
    for domain, s in sorted(stats.items()):
        if domain_filter and domain != domain_filter:
            continue
        l1_count = invariants.get(domain, 0)
        if s.observed > 0 and l1_count > 0:
            print(f"  {domain}: READY (L0=8, L1={l1_count})")
        elif l1_count > 0:
            print(f"  {domain}: PARTIAL (L1={l1_count}, no OBSERVED capabilities)")
        else:
            print(f"  {domain}: NOT READY (no L1 invariants)")
    print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Total panels: {total_all}")
    print(f"  OBSERVED (verified): {total_observed} ({total_pct:.1f}%)")
    print(f"  DECLARED (ready to verify): {total_declared}")
    print(f"  ASSUMED (need endpoints): {total_assumed}")
    print(f"  DEFERRED (no backend): {total_deferred}")
    print(f"  Missing capability bindings: {len(missing)}")
    print(f"  Scenarios needing migration: {scenarios.old_format}")
    print()


def output_json(stats: Dict[str, DomainStats], scenarios: ScenarioStats,
                missing: List[str], invariants: Dict[str, int]):
    """Output as JSON."""
    data = {
        "generated": datetime.now().isoformat(),
        "domains": {
            domain: {
                "observed": s.observed,
                "declared": s.declared,
                "assumed": s.assumed,
                "deferred": s.deferred,
                "total": s.total,
                "ready_pct": round(s.ready_pct, 1),
            }
            for domain, s in stats.items()
        },
        "scenarios": {
            "new_format": scenarios.new_format,
            "old_format": scenarios.old_format,
            "old_format_files": scenarios.old_format_files,
        },
        "missing_capabilities": missing,
        "invariants": invariants,
    }
    print(json.dumps(data, indent=2))


def main():
    parser = argparse.ArgumentParser(description="SDSR Status Report")
    parser.add_argument("--domain", help="Filter by domain")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    # Gather data
    domain_stats = get_domain_stats()
    scenario_stats = get_scenario_stats()
    missing = get_missing_capabilities()
    invariants = get_invariant_counts()

    # Output
    if args.json:
        output_json(domain_stats, scenario_stats, missing, invariants)
    else:
        print_report(domain_stats, scenario_stats, missing, invariants, args.domain)

    return 0


if __name__ == "__main__":
    sys.exit(main())
