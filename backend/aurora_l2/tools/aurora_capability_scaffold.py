#!/usr/bin/env python3
"""
AURORA L2 Capability Scaffolder (Phase 3 Automation)

Generates capability YAML from approved intent.
Creates capability in DECLARED status (claim without proof).
SDSR verification will move DECLARED → OBSERVED.

Usage:
    python aurora_capability_scaffold.py --panel OVR-SUM-HL-O2
    python aurora_capability_scaffold.py --capability overview.metric_snapshot --panel OVR-SUM-HL-O2

Rules:
    - Capability created in DECLARED status
    - Humans must NOT manually change status
    - DECLARED → OBSERVED happens via SDSR automation
    - CI blocks manual status edits

Author: AURORA L2 Automation
"""

import yaml
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent.parent
INTENTS_DIR = REPO_ROOT / "design/l2_1/intents"
INTENT_REGISTRY = REPO_ROOT / "design/l2_1/AURORA_L2_INTENT_REGISTRY.yaml"
CAPABILITY_REGISTRY = REPO_ROOT / "backend/AURORA_L2_CAPABILITY_REGISTRY"


def load_intent_yaml(panel_id: str) -> Optional[Dict]:
    """Load intent YAML for a panel (new naming convention with legacy fallback)."""
    # Try new naming convention first
    intent_path = INTENTS_DIR / f"AURORA_L2_INTENT_{panel_id}.yaml"
    if not intent_path.exists():
        # Fall back to legacy naming
        intent_path = INTENTS_DIR / f"{panel_id}.yaml"
    if not intent_path.exists():
        return None
    with open(intent_path) as f:
        return yaml.safe_load(f)


def load_intent_registry() -> Dict:
    """Load intent registry."""
    if INTENT_REGISTRY.exists():
        with open(INTENT_REGISTRY) as f:
            return yaml.safe_load(f) or {}
    return {}


def scaffold_capability(
    capability_id: str,
    panel_id: str,
    domain: str,
    endpoint: Optional[str] = None,
    method: str = "GET",
) -> Dict:
    """Generate capability YAML structure."""
    now = datetime.now(timezone.utc)

    capability = {
        'capability_id': capability_id,
        'status': 'DECLARED',
        'source_panels': [panel_id],
        'domain': domain,
        'endpoint': endpoint,
        'method': method,
        'metadata': {
            'generated_by': 'aurora_capability_scaffold.py',
            'generated_on': now.strftime('%Y-%m-%d'),
            'declared_by': 'AURORA_AUTOMATION',
            'declared_on': now.strftime('%Y-%m-%d'),
        },
        'coherency': {
            'last_checked': None,
            'status': 'UNVERIFIED',
            'checked_by': None,
        },
        'observation': {
            'scenario_id': None,
            'observed_at': None,
            'trace_id': None,
            'invariants_passed': None,
        },
        'acceptance_criteria': [
            'Endpoint exists and responds',
            'Response schema matches contract',
            'Auth works correctly',
            'Data is real (not mock)',
        ],
    }

    return capability


def write_capability_yaml(capability_id: str, capability: Dict, force: bool = False) -> Path:
    """Write capability YAML to registry."""
    CAPABILITY_REGISTRY.mkdir(parents=True, exist_ok=True)
    filename = f"AURORA_L2_CAPABILITY_{capability_id}.yaml"
    capability_path = CAPABILITY_REGISTRY / filename

    if capability_path.exists() and not force:
        raise FileExistsError(f"Capability YAML already exists: {capability_path}")

    header = f"""# AURORA L2 Capability Registry Entry
# Capability: {capability_id}
# Generated: {datetime.now(timezone.utc).isoformat()}
# Generator: aurora_capability_scaffold.py
#
# STATUS LIFECYCLE (Machine-Owned):
#   DECLARED → ASSUMED → OBSERVED → TRUSTED
#
# RULES:
#   - Status transitions are MACHINE-ONLY
#   - Humans must NOT edit status field
#   - DECLARED → OBSERVED requires SDSR verification
#   - CI blocks manual status changes
#
"""

    with open(capability_path, 'w') as f:
        f.write(header)
        yaml.dump(capability, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    return capability_path


def main():
    parser = argparse.ArgumentParser(
        description="AURORA L2 Capability Scaffolder - Generates capability YAML"
    )
    parser.add_argument("--panel", required=True, help="Panel ID (must have approved intent)")
    parser.add_argument("--capability", help="Override capability ID (otherwise from intent)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing capability")
    parser.add_argument("--dry-run", action="store_true", help="Print without writing")
    args = parser.parse_args()

    # Load intent
    intent = load_intent_yaml(args.panel)
    if not intent:
        print(f"ERROR: Intent YAML not found for {args.panel}", file=sys.stderr)
        return 1

    # Check registry status
    registry = load_intent_registry()
    if args.panel in registry:
        status = registry[args.panel].get('status')
        if status != 'APPROVED':
            print(f"WARNING: Intent status is {status}, not APPROVED", file=sys.stderr)
            print("Capability scaffolding typically requires APPROVED intent", file=sys.stderr)
            print("Continue anyway? This capability won't be used until intent is approved.")

    # Extract capability info from intent
    capability_ref = intent.get('capability', {})
    capability_id = args.capability or capability_ref.get('id')

    if not capability_id or capability_id.startswith('[TODO'):
        print(f"ERROR: No valid capability ID. Set in intent YAML or use --capability", file=sys.stderr)
        return 1

    endpoint = capability_ref.get('endpoint')
    if endpoint and endpoint.startswith('[TODO'):
        endpoint = None

    method = capability_ref.get('method', 'GET')
    domain = intent.get('metadata', {}).get('domain', 'UNKNOWN')

    # Check if capability already exists
    capability_path = CAPABILITY_REGISTRY / f"AURORA_L2_CAPABILITY_{capability_id}.yaml"
    if capability_path.exists() and not args.force and not args.dry_run:
        print(f"ERROR: Capability YAML already exists: {capability_path}", file=sys.stderr)
        print("Use --force to overwrite", file=sys.stderr)
        return 1

    # Generate scaffold
    capability = scaffold_capability(
        capability_id=capability_id,
        panel_id=args.panel,
        domain=domain,
        endpoint=endpoint,
        method=method,
    )

    if args.dry_run:
        print(f"# DRY RUN - Would write to: {capability_path.relative_to(REPO_ROOT)}")
        print("=" * 70)
        print(yaml.dump(capability, default_flow_style=False, sort_keys=False))
        return 0

    # Write file
    try:
        output_path = write_capability_yaml(capability_id, capability, force=args.force)
        print(f"✅ Created capability YAML: {output_path.relative_to(REPO_ROOT)}")
        print(f"   Capability ID: {capability_id}")
        print(f"   Status: DECLARED")
        print()
        print("Next steps:")
        print(f"  1. Run coherency check: python aurora_coherency_check.py --panel {args.panel}")
        print(f"  2. Generate SDSR scenario: python aurora_sdsr_synth.py --panel {args.panel}")
        print(f"  3. Run SDSR: python aurora_sdsr_runner.py --panel {args.panel}")
        return 0
    except FileExistsError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
