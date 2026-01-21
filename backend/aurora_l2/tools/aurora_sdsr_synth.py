#!/usr/bin/env python3
"""
AURORA L2 SDSR Scenario Synthesizer (Phase 4 Automation)

Generates SDSR scenario YAML from intent and capability.
Scenario defines what to inject and what to expect.

ARCHITECTURE (3-Layer Model):
    L0 — Transport (synth-owned)     → Endpoint reachable, auth works, response exists
    L1 — Domain (domain-owned)       → policy_context, EvidenceMetadata, etc.
    L2 — Capability (optional)       → Specific business rules

DOMAIN AUTHORITY:
    - Synth ATTACHES invariants, does not INVENT them
    - Domain invariants loaded from backend/sdsr/invariants/
    - Invariant IDs stored in YAML, executed at runtime

Usage:
    python aurora_sdsr_synth.py --panel OVR-SUM-HL-O2
    python aurora_sdsr_synth.py --panel OVR-SUM-HL-O2 --required-only

What gets generated:
    - scenario_id (derived from panel_id)
    - inject block (API call with domain-specific params)
    - expect block (response shape assertions)
    - invariants (L0 transport + L1 domain, by ID reference)

Author: AURORA L2 Automation
Reference: PIN-370, SDSR Layered Architecture
"""

import yaml
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional, List

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent.parent
BACKEND_ROOT = REPO_ROOT / "backend"
INTENTS_DIR = REPO_ROOT / "design/l2_1/intents"
CAPABILITY_REGISTRY = REPO_ROOT / "backend/AURORA_L2_CAPABILITY_REGISTRY"
SDSR_SCENARIOS_DIR = REPO_ROOT / "backend/scripts/sdsr/scenarios"

# Add backend to path for invariant imports
sys.path.insert(0, str(BACKEND_ROOT))

# Import domain invariant loader
try:
    from sdsr.invariants import (
        load_domain_invariants,
        get_invariant_ids_for_domain,
        get_default_params,
        get_transport_invariant_ids,
    )
    INVARIANTS_AVAILABLE = True
except ImportError as e:
    print(f"WARNING: Could not import domain invariants: {e}", file=sys.stderr)
    print("Falling back to legacy invariant generation", file=sys.stderr)
    INVARIANTS_AVAILABLE = False


def load_intent_yaml(panel_id: str) -> Optional[Dict]:
    """Load intent YAML for a panel."""
    # Try AURORA_L2_INTENT_{panel_id}.yaml naming convention first
    intent_path = INTENTS_DIR / f"AURORA_L2_INTENT_{panel_id}.yaml"
    if not intent_path.exists():
        # Fallback to {panel_id}.yaml for legacy files
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


def generate_invariant_ids(
    domain: str,
    panel_class: str,
    required_only: bool = False,
) -> List[str]:
    """
    Generate list of invariant IDs for a scenario.

    NEW ARCHITECTURE:
    - Invariant IDs are stored in YAML (not full definitions)
    - Invariants are executed at runtime by the runner
    - Domain invariants loaded from backend/sdsr/invariants/

    Args:
        domain: Domain name (ACTIVITY, LOGS, INCIDENTS, POLICIES)
        panel_class: Panel class (execution, interpretation, evidence)
        required_only: If True, only include required invariants

    Returns:
        List of invariant IDs to include in the scenario
    """
    if INVARIANTS_AVAILABLE:
        # NEW: Use domain invariant loader
        invariant_ids = []

        # Add L0 transport invariants
        invariant_ids.extend(get_transport_invariant_ids())

        # Add L1 domain invariants
        try:
            domain_ids = get_invariant_ids_for_domain(domain)
            invariant_ids.extend(domain_ids)
        except ValueError:
            # Unknown domain - use transport only
            print(f"WARNING: Unknown domain '{domain}', using transport invariants only", file=sys.stderr)

        return invariant_ids
    else:
        # LEGACY: Fall back to old behavior
        return generate_legacy_invariant_ids(panel_class)


def generate_legacy_invariant_ids(panel_class: str) -> List[str]:
    """
    LEGACY: Generate default invariant IDs based on panel type.

    DEPRECATED: Use generate_invariant_ids() with domain invariants instead.
    This is kept for backwards compatibility when invariants module not available.

    Note: These IDs are placeholders - the actual invariant definitions
    must be provided by the runner at execution time.
    """
    # Basic L0-equivalent invariant IDs (legacy naming)
    invariant_ids = [
        'INV-LEGACY-001',  # response_shape
        'INV-LEGACY-002',  # status_code
        'INV-LEGACY-003',  # auth_works
    ]

    if panel_class == 'interpretation':
        invariant_ids.extend([
            'INV-LEGACY-004',  # provenance_present
            'INV-LEGACY-005',  # aggregation_type_present
        ])

    return invariant_ids


def get_domain_default_params(domain: str, subdomain: str, topic: str) -> Dict:
    """
    Get domain-specific default query parameters.

    NEW ARCHITECTURE:
    - Params are domain-owned, not hardcoded in synth
    - Loaded from backend/sdsr/invariants/<domain>.py

    Args:
        domain: Domain name (ACTIVITY, LOGS, INCIDENTS, POLICIES)
        subdomain: Subdomain (e.g., LLM_RUNS, RECORDS, EVENTS)
        topic: Topic (e.g., LIVE, COMPLETED, ACTIVE)

    Returns:
        Dict of query parameters
    """
    if INVARIANTS_AVAILABLE:
        try:
            return get_default_params(domain, subdomain, topic)
        except Exception:
            pass

    # LEGACY: Return empty dict (no hardcoded params)
    return {}


def scaffold_scenario(
    panel_id: str,
    capability_id: str,
    endpoint: str,
    method: str,
    panel_class: str,
    domain: str,
    auth_mode: str = 'OBSERVER',
    subdomain: str = '',
    topic: str = '',
) -> Dict:
    """Generate SDSR scenario YAML structure."""
    scenario_id = generate_scenario_id(panel_id)

    # NEW: Get invariant IDs (not full definitions)
    # Invariants are executed at runtime by the runner
    invariant_ids = generate_invariant_ids(domain, panel_class)

    # NEW: Get domain-specific default params
    domain_params = get_domain_default_params(domain, subdomain, topic)

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
            # NEW: Use domain-specific params, not hardcoded defaults
            'params': domain_params if domain_params else {'window': '24h'},
        },
        'expect': {
            'status_code': 200,
            'response_type': 'json',
            'response_shape': {
                '_note': 'Define expected response structure here',
            },
        },
        # NEW: Store invariant IDs only (not full definitions)
        # Invariants are executed at runtime by looking up IDs in the registry
        'invariant_ids': invariant_ids,
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

    # Check both 'endpoint' and 'assumed_endpoint' (AURORA naming convention)
    endpoint = capability_ref.get('endpoint') or capability_ref.get('assumed_endpoint')
    if not endpoint or endpoint.startswith('[TODO'):
        print(f"ERROR: No valid endpoint in intent", file=sys.stderr)
        return 1

    # Check both 'method' and 'assumed_method' (AURORA naming convention)
    method = capability_ref.get('method') or capability_ref.get('assumed_method', 'GET')
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
        print(f"   Invariants: {len(scenario['invariant_ids'])}")
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
