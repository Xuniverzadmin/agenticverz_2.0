#!/usr/bin/env python3
"""
AURORA L2 Trust Evaluator (Phase 5.5 — Stability Accrual Gate)

Evaluates whether a capability should be promoted from OBSERVED to TRUSTED.
TRUSTED is earned through repeated successful SDSR runs over time.

Rules:
    - OBSERVED → TRUSTED is machine-only (humans cannot promote)
    - Requires minimum N successful SDSR runs
    - Requires minimum pass rate over time window
    - Requires no consecutive failures above threshold
    - Requires invariant stability (same invariants passing)

Usage:
    python aurora_trust_evaluator.py --capability overview.activity_snapshot
    python aurora_trust_evaluator.py --all
    python aurora_trust_evaluator.py --capability overview.activity_snapshot --promote

Trust Policy (configurable):
    min_runs: 10
    min_pass_rate: 0.98
    max_consecutive_failures: 1
    time_window_days: 7
    invariant_stability_required: true

Author: AURORA L2 Automation
"""

import yaml
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent.parent
CAPABILITY_REGISTRY = REPO_ROOT / "backend/AURORA_L2_CAPABILITY_REGISTRY"
SDSR_OBSERVATIONS_DIR = REPO_ROOT / "backend/scripts/sdsr/observations"
TRUST_HISTORY_DIR = REPO_ROOT / "backend/scripts/sdsr/trust_history"
TRUST_POLICY_FILE = REPO_ROOT / "backend/aurora_l2/tools/trust_policy.yaml"

# Default trust policy
DEFAULT_TRUST_POLICY = {
    'min_runs': 10,
    'min_pass_rate': 0.98,
    'max_consecutive_failures': 1,
    'time_window_days': 7,
    'invariant_stability_required': True,
    'require_coherency_pass': True,
}


@dataclass
class TrustEvaluation:
    capability_id: str
    current_status: str
    eligible: bool
    reason: str
    metrics: Dict
    recommendation: str


def load_trust_policy() -> Dict:
    """Load trust policy from YAML or use defaults."""
    if TRUST_POLICY_FILE.exists():
        with open(TRUST_POLICY_FILE) as f:
            policy = yaml.safe_load(f)
            return {**DEFAULT_TRUST_POLICY, **policy}
    return DEFAULT_TRUST_POLICY


def save_trust_policy(policy: Dict):
    """Save trust policy to YAML."""
    TRUST_POLICY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRUST_POLICY_FILE, 'w') as f:
        yaml.dump(policy, f, default_flow_style=False)


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
# Updated By: aurora_trust_evaluator.py
#
# STATUS: {capability.get('status', 'UNKNOWN')}
#
"""

    with open(cap_path, 'w') as f:
        f.write(header)
        yaml.dump(capability, f, default_flow_style=False, sort_keys=False)


def load_observation_history(capability_id: str) -> List[Dict]:
    """Load all observations for a capability from history."""
    history = []

    # Load from trust history directory (accumulated observations)
    history_file = TRUST_HISTORY_DIR / f"{capability_id}_history.json"
    if history_file.exists():
        with open(history_file) as f:
            history = json.load(f)

    # Also check current observation
    current_obs_file = SDSR_OBSERVATIONS_DIR / f"SDSR_OBSERVATION_{capability_id}.json"
    if current_obs_file.exists():
        with open(current_obs_file) as f:
            current = json.load(f)
            # Add to history if not already there
            if not any(h.get('observation_id') == current.get('observation_id') for h in history):
                history.append(current)

    return history


def save_observation_history(capability_id: str, history: List[Dict]):
    """Save observation history."""
    TRUST_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    history_file = TRUST_HISTORY_DIR / f"{capability_id}_history.json"
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)


def append_observation_to_history(capability_id: str, observation: Dict):
    """Append a new observation to history."""
    history = load_observation_history(capability_id)

    # Check if already exists
    obs_id = observation.get('observation_id')
    if any(h.get('observation_id') == obs_id for h in history):
        return  # Already in history

    history.append(observation)
    save_observation_history(capability_id, history)


def filter_observations_by_window(
    observations: List[Dict],
    window_days: int
) -> List[Dict]:
    """Filter observations to only those within time window."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)

    filtered = []
    for obs in observations:
        obs_time_str = obs.get('observed_at')
        if obs_time_str:
            try:
                obs_time = datetime.fromisoformat(obs_time_str.replace('Z', '+00:00'))
                if obs_time >= cutoff:
                    filtered.append(obs)
            except ValueError:
                pass  # Skip malformed timestamps

    return filtered


def calculate_metrics(observations: List[Dict]) -> Dict:
    """Calculate trust metrics from observations."""
    if not observations:
        return {
            'total_runs': 0,
            'pass_count': 0,
            'fail_count': 0,
            'pass_rate': 0.0,
            'max_consecutive_failures': 0,
            'invariant_sets': [],
            'coherency_failures': 0,
        }

    total = len(observations)
    passes = sum(1 for o in observations if o.get('status') == 'PASS')
    fails = total - passes

    # Calculate max consecutive failures
    max_consec = 0
    current_consec = 0
    for obs in sorted(observations, key=lambda x: x.get('observed_at', '')):
        if obs.get('status') != 'PASS':
            current_consec += 1
            max_consec = max(max_consec, current_consec)
        else:
            current_consec = 0

    # Track invariant sets (for stability check)
    invariant_sets = []
    for obs in observations:
        inv_results = obs.get('invariant_results', [])
        inv_ids = frozenset(r.get('id') for r in inv_results if r.get('status') == 'PASS')
        if inv_ids and inv_ids not in invariant_sets:
            invariant_sets.append(inv_ids)

    # Count coherency failures
    coherency_failures = sum(
        1 for o in observations
        if not o.get('coherency_verified', True)
    )

    return {
        'total_runs': total,
        'pass_count': passes,
        'fail_count': fails,
        'pass_rate': passes / total if total > 0 else 0.0,
        'max_consecutive_failures': max_consec,
        'invariant_sets_count': len(invariant_sets),
        'invariant_stable': len(invariant_sets) <= 1,
        'coherency_failures': coherency_failures,
    }


def evaluate_trust(capability_id: str, policy: Dict) -> TrustEvaluation:
    """Evaluate whether a capability is eligible for TRUSTED status."""
    capability = load_capability_yaml(capability_id)
    if not capability:
        return TrustEvaluation(
            capability_id=capability_id,
            current_status='UNKNOWN',
            eligible=False,
            reason="Capability YAML not found",
            metrics={},
            recommendation="Create capability first"
        )

    current_status = capability.get('status', 'UNKNOWN')

    # Already TRUSTED
    if current_status == 'TRUSTED':
        return TrustEvaluation(
            capability_id=capability_id,
            current_status=current_status,
            eligible=False,
            reason="Already TRUSTED",
            metrics={},
            recommendation="No action needed"
        )

    # Not yet OBSERVED
    if current_status not in ['OBSERVED', 'TRUSTED']:
        return TrustEvaluation(
            capability_id=capability_id,
            current_status=current_status,
            eligible=False,
            reason=f"Status is {current_status}, must be OBSERVED first",
            metrics={},
            recommendation="Complete SDSR verification first"
        )

    # Load observation history
    all_observations = load_observation_history(capability_id)
    window_observations = filter_observations_by_window(
        all_observations,
        policy['time_window_days']
    )

    metrics = calculate_metrics(window_observations)

    # Check each policy requirement
    failures = []

    if metrics['total_runs'] < policy['min_runs']:
        failures.append(
            f"Insufficient runs: {metrics['total_runs']} < {policy['min_runs']} required"
        )

    if metrics['pass_rate'] < policy['min_pass_rate']:
        failures.append(
            f"Pass rate too low: {metrics['pass_rate']:.2%} < {policy['min_pass_rate']:.0%} required"
        )

    if metrics['max_consecutive_failures'] > policy['max_consecutive_failures']:
        failures.append(
            f"Too many consecutive failures: {metrics['max_consecutive_failures']} > {policy['max_consecutive_failures']} allowed"
        )

    if policy['invariant_stability_required'] and not metrics.get('invariant_stable', True):
        failures.append(
            f"Invariant instability: {metrics['invariant_sets_count']} different invariant sets"
        )

    if policy['require_coherency_pass'] and metrics['coherency_failures'] > 0:
        failures.append(
            f"Coherency failures detected: {metrics['coherency_failures']}"
        )

    if failures:
        return TrustEvaluation(
            capability_id=capability_id,
            current_status=current_status,
            eligible=False,
            reason="; ".join(failures),
            metrics=metrics,
            recommendation="Continue SDSR runs to build trust"
        )

    return TrustEvaluation(
        capability_id=capability_id,
        current_status=current_status,
        eligible=True,
        reason="All trust policy requirements met",
        metrics=metrics,
        recommendation="Eligible for TRUSTED promotion"
    )


def promote_to_trusted(capability_id: str) -> bool:
    """Promote a capability from OBSERVED to TRUSTED."""
    capability = load_capability_yaml(capability_id)
    if not capability:
        return False

    if capability.get('status') != 'OBSERVED':
        print(f"Cannot promote: status is {capability.get('status')}, not OBSERVED")
        return False

    # Update status
    capability['status'] = 'TRUSTED'
    capability['trust'] = {
        'promoted_at': datetime.now(timezone.utc).isoformat(),
        'promoted_by': 'aurora_trust_evaluator.py',
        'policy_version': '1.0',
    }

    save_capability_yaml(capability_id, capability)
    return True


def get_all_observed_capabilities() -> List[str]:
    """Get all capabilities with OBSERVED status."""
    capabilities = []
    for cap_file in CAPABILITY_REGISTRY.glob("AURORA_L2_CAPABILITY_*.yaml"):
        with open(cap_file) as f:
            cap = yaml.safe_load(f)
            if cap and cap.get('status') == 'OBSERVED':
                capabilities.append(cap.get('capability_id'))
    return capabilities


def print_evaluation(eval_result: TrustEvaluation, verbose: bool = False):
    """Print trust evaluation result."""
    print(f"\nTrust Evaluation: {eval_result.capability_id}")
    print("=" * 60)
    print(f"  Current Status:  {eval_result.current_status}")
    print(f"  Eligible:        {'✅ YES' if eval_result.eligible else '❌ NO'}")
    print(f"  Reason:          {eval_result.reason}")
    print(f"  Recommendation:  {eval_result.recommendation}")

    if verbose and eval_result.metrics:
        print()
        print("  Metrics:")
        for k, v in eval_result.metrics.items():
            if isinstance(v, float):
                print(f"    {k}: {v:.2%}" if 'rate' in k else f"    {k}: {v:.2f}")
            else:
                print(f"    {k}: {v}")


def main():
    parser = argparse.ArgumentParser(
        description="AURORA L2 Trust Evaluator - Evaluates OBSERVED → TRUSTED promotion"
    )
    parser.add_argument("--capability", help="Capability ID to evaluate")
    parser.add_argument("--all", action="store_true", help="Evaluate all OBSERVED capabilities")
    parser.add_argument("--promote", action="store_true",
                        help="Promote eligible capability to TRUSTED")
    parser.add_argument("--show-policy", action="store_true", help="Show current trust policy")
    parser.add_argument("--set-policy", help="Set policy value (key=value)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    policy = load_trust_policy()

    if args.show_policy:
        print("Trust Policy:")
        print("=" * 40)
        for k, v in policy.items():
            print(f"  {k}: {v}")
        return 0

    if args.set_policy:
        key, value = args.set_policy.split('=')
        # Try to parse as int, float, or bool
        try:
            value = int(value)
        except ValueError:
            try:
                value = float(value)
            except ValueError:
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'

        policy[key] = value
        save_trust_policy(policy)
        print(f"Updated policy: {key} = {value}")
        return 0

    capabilities_to_check = []
    if args.all:
        capabilities_to_check = get_all_observed_capabilities()
        if not capabilities_to_check:
            print("No OBSERVED capabilities found")
            return 0
    elif args.capability:
        capabilities_to_check = [args.capability]
    else:
        parser.print_help()
        return 1

    promoted = 0
    eligible = 0

    for cap_id in capabilities_to_check:
        eval_result = evaluate_trust(cap_id, policy)
        print_evaluation(eval_result, args.verbose)

        if eval_result.eligible:
            eligible += 1
            if args.promote:
                if promote_to_trusted(cap_id):
                    print(f"\n  ✅ PROMOTED: {cap_id} → TRUSTED")
                    promoted += 1
                else:
                    print(f"\n  ❌ Failed to promote {cap_id}")

    if args.all:
        print()
        print("=" * 60)
        print(f"Summary: {eligible}/{len(capabilities_to_check)} eligible for TRUSTED")
        if args.promote:
            print(f"Promoted: {promoted}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
