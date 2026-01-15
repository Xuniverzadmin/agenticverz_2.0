#!/usr/bin/env python3
"""
AURORA L2 SDSR Scenario Synthesizer (Phase 4 Automation)

Generates SDSR scenario YAML from intent and capability.
Scenario defines what to inject and what to expect.
Human may optionally refine invariants.

Usage:
    python aurora_sdsr_synth.py --panel OVR-SUM-HL-O2
    python aurora_sdsr_synth.py --panel OVR-SUM-HL-O2 --invariants strict

What gets generated:
    - scenario_id (derived from panel_id)
    - inject block (API call definition)
    - expect block (response shape assertions)
    - invariants (default set from capability type)

Human may optionally:
    - Add domain-specific invariants
    - Tighten response expectations
    - Add custom checks

Author: AURORA L2 Automation
"""

import yaml
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional, List

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent.parent
INTENTS_DIR = REPO_ROOT / "design/l2_1/intents"
CAPABILITY_REGISTRY = REPO_ROOT / "backend/AURORA_L2_CAPABILITY_REGISTRY"
SDSR_SCENARIOS_DIR = REPO_ROOT / "backend/scripts/sdsr/scenarios"


def load_intent_yaml(panel_id: str) -> Optional[Dict]:
    """Load intent YAML for a panel."""
    intent_path = INTENTS_DIR / f"{panel_id}.yaml"
    if not intent_path.exists():
        return None
    with open(intent_path) as f:
        return yaml.safe_load(f)


def load_capability_yaml(capability_id: str) -> Optional[Dict]:
    """Load capability YAML."""
    cap_path = CAPABILITY_REGISTRY / f"AURORA_L2_CAPABILITY_{capability_id}.yaml"
    if not cap_path.exists():
        return None
    with open(cap_path) as f:
        return yaml.safe_load(f)


def generate_scenario_id(panel_id: str) -> str:
    """Generate scenario ID from panel ID."""
    # OVR-SUM-HL-O1 → SDSR-OVR-SUM-HL-O1-001
    return f"SDSR-{panel_id}-001"


def generate_default_invariants(panel_class: str, has_provenance: bool = False) -> List[Dict]:
    """Generate default invariants based on panel type."""
    invariants = [
        {
            'id': 'INV-001',
            'name': 'response_shape',
            'description': 'Response has expected top-level structure',
            'assertion': 'response is dict and response is not empty',
        },
        {
            'id': 'INV-002',
            'name': 'status_code',
            'description': 'API returns 200 OK',
            'assertion': 'status_code == 200',
        },
        {
            'id': 'INV-003',
            'name': 'auth_works',
            'description': 'Authenticated request succeeds',
            'assertion': 'status_code != 401 and status_code != 403',
        },
    ]

    if panel_class == 'interpretation':
        invariants.append({
            'id': 'INV-004',
            'name': 'provenance_present',
            'description': 'Interpretation panel has provenance metadata',
            'assertion': '"provenance" in response',
        })
        invariants.append({
            'id': 'INV-005',
            'name': 'aggregation_type_present',
            'description': 'Provenance includes aggregation type',
            'assertion': '"aggregation" in response.get("provenance", {})',
        })

    return invariants


def scaffold_scenario(
    panel_id: str,
    capability_id: str,
    endpoint: str,
    method: str,
    panel_class: str,
    domain: str,
    auth_mode: str = 'OBSERVER',
) -> Dict:
    """Generate SDSR scenario YAML structure."""
    scenario_id = generate_scenario_id(panel_id)
    invariants = generate_default_invariants(panel_class)

    # Headers based on auth mode - SDSR runner will resolve credentials
    headers = {'Content-Type': 'application/json'}
    if auth_mode == 'USER':
        headers['Authorization'] = 'Bearer ${AUTH_TOKEN}'
    elif auth_mode == 'SERVICE':
        headers['X-AOS-Key'] = '${AOS_API_KEY}'
        headers['X-Tenant-ID'] = '${SDSR_TENANT_ID}'
    # OBSERVER mode: runner will inject observer credentials

    scenario = {
        'scenario_id': scenario_id,
        'version': '1.0.0',
        'name': f"Observe {panel_id} capability",
        'description': f"SDSR verification scenario for {capability_id}",
        'capability': capability_id,
        'panel_id': panel_id,
        'domain': domain,
        'auth': {
            'mode': auth_mode,  # OBSERVER | SERVICE | USER
        },
        'metadata': {
            'generated_by': 'aurora_sdsr_synth.py',
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'panel_class': panel_class,
        },
        'inject': {
            'type': 'api_call',
            'endpoint': endpoint,
            'method': method,
            'headers': headers,
            'params': {
                'window': '24h',  # Default for summary endpoints
            },
        },
        'expect': {
            'status_code': 200,
            'response_type': 'json',
            'response_shape': {
                '_note': 'Define expected response structure here',
            },
        },
        'invariants': invariants,
        'cleanup': {
            'required': False,
            'note': 'Read-only observation, no cleanup needed',
        },
        'on_success': {
            'update_capability_status': 'OBSERVED',
            'emit_observation': True,
        },
        'on_failure': {
            'update_capability_status': None,
            'emit_observation': True,
            'failure_taxonomy': {
                'endpoint_missing': 'Backend route does not exist',
                'auth_failed': 'Authentication/authorization issue',
                'schema_mismatch': 'Response shape does not match contract',
                'invariant_violated': 'One or more invariants failed',
            },
        },
    }

    return scenario


def write_scenario_yaml(scenario_id: str, scenario: Dict, force: bool = False) -> Path:
    """Write scenario YAML to file."""
    SDSR_SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)
    scenario_path = SDSR_SCENARIOS_DIR / f"{scenario_id}.yaml"

    if scenario_path.exists() and not force:
        raise FileExistsError(f"Scenario YAML already exists: {scenario_path}")

    header = f"""# SDSR Verification Scenario
# Scenario: {scenario_id}
# Generated: {datetime.now(timezone.utc).isoformat()}
# Generator: aurora_sdsr_synth.py
#
# PURPOSE:
#   This scenario verifies the capability by:
#   1. Injecting an API call (cause)
#   2. Observing the response (effect)
#   3. Checking invariants (verification)
#
# EXECUTION:
#   python aurora_sdsr_runner.py --scenario {scenario_id}
#
# HUMAN MAY OPTIONALLY:
#   - Add domain-specific invariants
#   - Tighten response expectations
#   - Add custom checks
#
"""

    with open(scenario_path, 'w') as f:
        f.write(header)
        yaml.dump(scenario, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    return scenario_path


def main():
    parser = argparse.ArgumentParser(
        description="AURORA L2 SDSR Scenario Synthesizer - Generates verification scenarios"
    )
    parser.add_argument("--panel", required=True, help="Panel ID")
    parser.add_argument("--force", action="store_true", help="Overwrite existing scenario")
    parser.add_argument("--dry-run", action="store_true", help="Print without writing")
    args = parser.parse_args()

    # Load intent
    intent = load_intent_yaml(args.panel)
    if not intent:
        print(f"ERROR: Intent YAML not found for {args.panel}", file=sys.stderr)
        return 1

    # Extract capability info
    capability_ref = intent.get('capability', {})
    capability_id = capability_ref.get('id')

    if not capability_id or capability_id.startswith('[TODO'):
        print(f"ERROR: No valid capability ID in intent", file=sys.stderr)
        return 1

    endpoint = capability_ref.get('endpoint')
    if not endpoint or endpoint.startswith('[TODO'):
        print(f"ERROR: No valid endpoint in intent", file=sys.stderr)
        return 1

    method = capability_ref.get('method', 'GET')
    panel_class = intent.get('panel_class', 'execution')
    domain = intent.get('metadata', {}).get('domain', 'UNKNOWN')

    # Get auth mode from intent (default OBSERVER)
    sdsr_config = intent.get('sdsr', {})
    auth_mode = sdsr_config.get('auth_mode', 'OBSERVER')
    if auth_mode not in ('OBSERVER', 'SERVICE', 'USER'):
        print(f"WARNING: Unknown auth_mode '{auth_mode}', defaulting to OBSERVER", file=sys.stderr)
        auth_mode = 'OBSERVER'

    # Check capability exists
    capability = load_capability_yaml(capability_id)
    if not capability:
        print(f"WARNING: Capability YAML not found for {capability_id}", file=sys.stderr)
        print("Run aurora_capability_scaffold.py first", file=sys.stderr)

    scenario_id = generate_scenario_id(args.panel)

    # Check if scenario exists
    scenario_path = SDSR_SCENARIOS_DIR / f"{scenario_id}.yaml"
    if scenario_path.exists() and not args.force and not args.dry_run:
        print(f"ERROR: Scenario YAML already exists: {scenario_path}", file=sys.stderr)
        print("Use --force to overwrite", file=sys.stderr)
        return 1

    # Generate scenario
    scenario = scaffold_scenario(
        panel_id=args.panel,
        capability_id=capability_id,
        endpoint=endpoint,
        method=method,
        panel_class=panel_class,
        domain=domain,
        auth_mode=auth_mode,
    )

    if args.dry_run:
        print(f"# DRY RUN - Would write to: {scenario_path.relative_to(REPO_ROOT)}")
        print("=" * 70)
        print(yaml.dump(scenario, default_flow_style=False, sort_keys=False))
        return 0

    # Write file
    try:
        output_path = write_scenario_yaml(scenario_id, scenario, force=args.force)
        print(f"✅ Created SDSR scenario: {output_path.relative_to(REPO_ROOT)}")
        print(f"   Scenario ID: {scenario_id}")
        print(f"   Capability: {capability_id}")
        print(f"   Endpoint: {endpoint}")
        print(f"   Invariants: {len(scenario['invariants'])}")
        print()
        print("Next steps:")
        print(f"  1. (Optional) Edit scenario to add custom invariants")
        print(f"  2. Run coherency check: python aurora_coherency_check.py --panel {args.panel}")
        print(f"  3. Execute SDSR: python aurora_sdsr_runner.py --scenario {scenario_id}")
        return 0
    except FileExistsError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
