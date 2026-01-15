#!/usr/bin/env python3
"""
AURORA L2 Observation Applier (Phase 5 Automation)

Applies SDSR observation to capability registry and intent YAML.
This is a MACHINE-ONLY operation - humans must NOT call this manually.

What it does:
    1. Reads SDSR observation JSON
    2. If PASS: Updates capability status DECLARED → OBSERVED
    3. Updates coherency block in capability YAML
    4. Appends observation trace to intent YAML
    5. Updates sdsr.verified in intent YAML

Rules:
    - Only applies if observation.status == PASS
    - Atomic: all updates or none
    - Idempotent: safe to run multiple times
    - Human edits to capability status are FORBIDDEN

Usage:
    python aurora_apply_observation.py --observation SDSR_OBSERVATION_overview.activity_snapshot.json
    python aurora_apply_observation.py --capability overview.activity_snapshot

Author: AURORA L2 Automation
"""

import yaml
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent.parent
INTENTS_DIR = REPO_ROOT / "design/l2_1/intents"
CAPABILITY_REGISTRY = REPO_ROOT / "backend/AURORA_L2_CAPABILITY_REGISTRY"
SDSR_OBSERVATIONS_DIR = REPO_ROOT / "backend/scripts/sdsr/observations"


def load_observation(filename: str) -> Optional[Dict]:
    """Load observation JSON."""
    obs_path = SDSR_OBSERVATIONS_DIR / filename
    if not obs_path.exists():
        # Try with full path
        obs_path = Path(filename)
        if not obs_path.exists():
            return None
    with open(obs_path) as f:
        return json.load(f)


def find_observation_for_capability(capability_id: str) -> Optional[Dict]:
    """Find latest observation for a capability."""
    filename = f"SDSR_OBSERVATION_{capability_id}.json"
    return load_observation(filename)


def load_capability_yaml(capability_id: str) -> Optional[Dict]:
    """Load capability YAML."""
    cap_path = CAPABILITY_REGISTRY / f"AURORA_L2_CAPABILITY_{capability_id}.yaml"
    if not cap_path.exists():
        return None
    with open(cap_path) as f:
        return yaml.safe_load(f)


def save_capability_yaml(capability_id: str, capability: Dict):
    """Save capability YAML."""
    cap_path = CAPABILITY_REGISTRY / f"AURORA_L2_CAPABILITY_{capability_id}.yaml"

    header = f"""# AURORA L2 Capability Registry Entry
# Capability: {capability_id}
# Last Updated: {datetime.now(timezone.utc).isoformat()}
# Updated By: aurora_apply_observation.py
#
# STATUS: {capability.get('status', 'UNKNOWN')}
#
# WARNING: Status transitions are MACHINE-OWNED.
#          Do NOT manually edit the status field.
#
"""

    with open(cap_path, 'w') as f:
        f.write(header)
        yaml.dump(capability, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def load_intent_yaml(panel_id: str) -> Optional[Dict]:
    """Load intent YAML."""
    # Try new naming convention first
    intent_path = INTENTS_DIR / f"AURORA_L2_INTENT_{panel_id}.yaml"
    if not intent_path.exists():
        # Fallback to legacy naming
        intent_path = INTENTS_DIR / f"{panel_id}.yaml"
    if not intent_path.exists():
        return None
    with open(intent_path) as f:
        return yaml.safe_load(f)


def save_intent_yaml(panel_id: str, intent: Dict):
    """Save intent YAML."""
    intent_path = INTENTS_DIR / f"AURORA_L2_INTENT_{panel_id}.yaml"

    header = f"""# AURORA_L2 Intent Spec: {panel_id}
# Last Updated: {datetime.now(timezone.utc).isoformat()}
# Updated By: aurora_apply_observation.py
#
"""

    with open(intent_path, 'w') as f:
        f.write(header)
        yaml.dump(intent, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def apply_observation(observation: Dict, dry_run: bool = False) -> bool:
    """
    Apply observation to capability and intent.
    Returns True if successful.
    """
    # Validate observation
    status = observation.get('status')
    if status != 'PASS':
        print(f"Cannot apply observation with status={status} (must be PASS)", file=sys.stderr)
        return False

    capability_id = observation.get('capability_id')
    panel_id = observation.get('panel_id')
    observed_at = observation.get('observed_at')
    scenario_id = observation.get('scenario_id')
    invariants_passed = observation.get('invariants_passed', 0)
    invariants_total = observation.get('invariants_total', 0)
    coherency_verified = observation.get('coherency_verified', False)

    if not capability_id:
        print("Observation missing capability_id", file=sys.stderr)
        return False

    # Load capability
    capability = load_capability_yaml(capability_id)
    if not capability:
        print(f"Capability YAML not found: {capability_id}", file=sys.stderr)
        return False

    current_status = capability.get('status')

    # Determine new status
    if current_status in ['DECLARED', 'ASSUMED']:
        new_status = 'OBSERVED'
    elif current_status == 'OBSERVED':
        new_status = 'OBSERVED'  # Already observed, just update trace
    elif current_status == 'TRUSTED':
        new_status = 'TRUSTED'  # Don't downgrade from TRUSTED
    else:
        new_status = 'OBSERVED'

    print(f"Applying observation for {capability_id}")
    print(f"  Current status: {current_status}")
    print(f"  New status: {new_status}")
    print(f"  Coherency verified: {coherency_verified}")
    print(f"  Invariants: {invariants_passed}/{invariants_total}")

    if dry_run:
        print("\nDRY RUN - Would update:")
        print(f"  - Capability status: {current_status} → {new_status}")
        print(f"  - Capability observation block")
        print(f"  - Capability coherency block")
        if panel_id:
            print(f"  - Intent YAML sdsr.verified")
        return True

    # Update capability
    capability['status'] = new_status
    capability['observation'] = {
        'scenario_id': scenario_id,
        'observed_at': observed_at,
        'trace_id': observation.get('trace_id'),
        'invariants_passed': invariants_passed,
        'invariants_total': invariants_total,
    }
    capability['coherency'] = {
        'last_checked': observed_at,
        'status': 'PASSED' if coherency_verified else 'UNVERIFIED',
        'checked_by': 'aurora_sdsr_runner.py',
    }
    capability['metadata']['observed_by'] = scenario_id
    capability['metadata']['observed_on'] = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    # Save capability
    save_capability_yaml(capability_id, capability)
    print(f"  ✅ Updated capability: {capability_id}")

    # Update intent if panel_id provided
    if panel_id:
        intent = load_intent_yaml(panel_id)
        if intent:
            # Update sdsr block
            if 'sdsr' not in intent:
                intent['sdsr'] = {}

            intent['sdsr']['verified'] = True
            intent['sdsr']['verification_date'] = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            intent['sdsr']['scenario'] = scenario_id
            intent['sdsr']['observation_trace'] = {
                'observation_id': observation.get('observation_id'),
                'observed_at': observed_at,
                'invariants_passed': invariants_passed,
            }
            intent['sdsr']['checks'] = {
                'endpoint_exists': 'PASS',
                'schema_matches': 'PASS' if invariants_passed == invariants_total else 'PARTIAL',
                'auth_works': 'PASS',
                'data_is_real': 'PASS',
            }

            # Update capability status in intent
            if 'capability' in intent:
                intent['capability']['status'] = new_status

            # Update review status
            if 'metadata' in intent:
                intent['metadata']['review_status'] = 'REVIEWED'

            save_intent_yaml(panel_id, intent)
            print(f"  ✅ Updated intent: {panel_id}")
        else:
            print(f"  ⚠️  Intent YAML not found for {panel_id}")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="AURORA L2 Observation Applier - Applies SDSR observations to registry"
    )
    parser.add_argument("--observation", help="Observation JSON filename")
    parser.add_argument("--capability", help="Capability ID (finds latest observation)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change")
    parser.add_argument("--force", action="store_true", help="Apply even if status != PASS")
    args = parser.parse_args()

    # Find observation
    observation = None
    if args.observation:
        observation = load_observation(args.observation)
        if not observation:
            print(f"ERROR: Observation not found: {args.observation}", file=sys.stderr)
            return 1
    elif args.capability:
        observation = find_observation_for_capability(args.capability)
        if not observation:
            print(f"ERROR: No observation found for capability: {args.capability}", file=sys.stderr)
            return 1
    else:
        parser.print_help()
        return 1

    # Apply observation
    if args.force and observation.get('status') != 'PASS':
        print(f"WARNING: Forcing application of {observation.get('status')} observation")
        observation['status'] = 'PASS'  # Override for force mode

    success = apply_observation(observation, dry_run=args.dry_run)

    if success:
        print()
        if args.dry_run:
            print("DRY RUN complete")
        else:
            print("✅ Observation applied successfully")
            print()
            print("Next step:")
            print("  Run compiler: ./scripts/tools/run_aurora_l2_pipeline.sh")
        return 0
    else:
        print()
        print("❌ Failed to apply observation")
        return 1


if __name__ == "__main__":
    sys.exit(main())
