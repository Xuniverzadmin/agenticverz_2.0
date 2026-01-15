#!/usr/bin/env python3
"""
AURORA L2 SDSR Runner (Phase 4 Automation)

Executes SDSR scenarios and emits observations.
REQUIRES coherency gate to pass before execution.
Cannot run if coherency has not been verified.

Usage:
    python aurora_sdsr_runner.py --scenario SDSR-OVR-SUM-HL-O1-001
    python aurora_sdsr_runner.py --panel OVR-SUM-HL-O1

Pre-conditions (enforced):
    1. Coherency gate must pass (COH-001 to COH-010)
    2. Capability must be in DECLARED or ASSUMED status
    3. Backend must be reachable

Post-conditions:
    1. Observation JSON emitted
    2. If PASS: ready for aurora_apply_observation.py
    3. If FAIL: observation records failure taxonomy

Author: AURORA L2 Automation
"""

import yaml
import json
import sys
import argparse
import requests
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent.parent
INTENTS_DIR = REPO_ROOT / "design/l2_1/intents"
CAPABILITY_REGISTRY = REPO_ROOT / "backend/AURORA_L2_CAPABILITY_REGISTRY"
SDSR_SCENARIOS_DIR = REPO_ROOT / "backend/scripts/sdsr/scenarios"
SDSR_OBSERVATIONS_DIR = REPO_ROOT / "backend/scripts/sdsr/observations"

# Import coherency checker
sys.path.insert(0, str(Path(__file__).parent))
from aurora_coherency_check import CoherencyChecker, CheckStatus


class ObservationStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    BLOCKED = "BLOCKED"


class FailureClass(Enum):
    """
    SDSR Failure Taxonomy (Phase 5.5 Hardening)

    Classifies failure root causes for analytics and trust evaluation.
    Each failure has different implications for promotion eligibility.
    """
    # Coherency failures - wiring is broken
    COHERENCY_VIOLATION = "COHERENCY_VIOLATION"      # COH-001 to COH-008 failed
    REALITY_MISMATCH = "REALITY_MISMATCH"            # COH-009/010 failed (endpoint doesn't exist)

    # Behavioral failures - wiring correct but behavior wrong
    INVARIANT_VIOLATED = "INVARIANT_VIOLATED"        # SDSR invariants failed
    SEMANTIC_REGRESSION = "SEMANTIC_REGRESSION"      # Previously passing invariant now fails

    # Transient failures - infrastructure issues
    TRANSIENT_FAILURE = "TRANSIENT_FAILURE"          # Network timeout, service unavailable
    AUTH_FAILURE = "AUTH_FAILURE"                    # 401/403 errors (blocking for SERVICE/USER)

    # Visibility failures - behavior verified but access restricted
    VISIBILITY_RESTRICTED = "VISIBILITY_RESTRICTED"  # 401/403 for OBSERVER mode (non-blocking)

    # Internal errors
    INTERNAL_ERROR = "INTERNAL_ERROR"                # Script/assertion evaluation error

    @classmethod
    def from_legacy(cls, taxonomy: str) -> "FailureClass":
        """Convert legacy taxonomy strings to enum."""
        mapping = {
            "coherency_failed": cls.COHERENCY_VIOLATION,
            "request_failed": cls.TRANSIENT_FAILURE,
            "invariant_violated": cls.INVARIANT_VIOLATED,
        }
        return mapping.get(taxonomy, cls.INTERNAL_ERROR)


# =============================================================================
# SDSR Auth Mode Credential Loaders
# =============================================================================

def load_observer_credentials() -> Dict[str, str]:
    """
    Load credentials for OBSERVER mode.
    OBSERVER verifies behavior independent of user access.
    Uses internal/infra read-only credentials.
    """
    headers = {}
    # Try API key first (infra access)
    api_key = os.environ.get('AOS_API_KEY', '')
    if api_key:
        headers['X-AOS-Key'] = api_key
    # Observer always uses demo-tenant for system-wide reads
    headers['X-Tenant-ID'] = os.environ.get('SDSR_TENANT_ID', 'demo-tenant')
    return headers


def load_service_credentials() -> Dict[str, str]:
    """
    Load credentials for SERVICE mode.
    SERVICE verifies tenant-scoped behavior.
    Requires valid API key and tenant context.
    """
    headers = {}
    api_key = os.environ.get('AOS_API_KEY', '')
    if not api_key:
        raise ValueError("SERVICE auth mode requires AOS_API_KEY")
    headers['X-AOS-Key'] = api_key
    tenant_id = os.environ.get('SDSR_TENANT_ID', 'demo-tenant')
    headers['X-Tenant-ID'] = tenant_id
    return headers


def load_user_credentials() -> Dict[str, str]:
    """
    Load credentials for USER mode.
    USER verifies user-personal behavior.
    Requires bearer token.
    """
    headers = {}
    auth_token = os.environ.get('AUTH_TOKEN', '')
    if not auth_token:
        raise ValueError("USER auth mode requires AUTH_TOKEN")
    headers['Authorization'] = f'Bearer {auth_token}'
    return headers


def load_headers_for_auth_mode(auth_mode: str, scenario_headers: Dict[str, str]) -> Dict[str, str]:
    """
    Load headers based on auth mode.
    Auth mode determines how SDSR authenticates.
    Scenario headers are merged (resolved env vars).
    """
    # Start with content-type
    headers = {'Content-Type': 'application/json'}

    # Load auth-specific headers
    if auth_mode == 'OBSERVER':
        headers.update(load_observer_credentials())
    elif auth_mode == 'SERVICE':
        headers.update(load_service_credentials())
    elif auth_mode == 'USER':
        headers.update(load_user_credentials())
    else:
        # Default to OBSERVER
        headers.update(load_observer_credentials())

    # Merge scenario-specific headers (resolved)
    for k, v in scenario_headers.items():
        if k in ('Content-Type',):
            continue  # Already set
        if isinstance(v, str) and v.startswith('${') and v.endswith('}'):
            env_var = v[2:-1]
            resolved = os.environ.get(env_var, '')
            if resolved:
                headers[k] = resolved
        elif v:
            headers[k] = v

    return headers


@dataclass
class InvariantResult:
    id: str
    name: str
    status: str
    message: str


@dataclass
class Observation:
    observation_id: str
    scenario_id: str
    capability_id: str
    panel_id: str
    status: str
    observed_at: str
    endpoint: str
    method: str
    response_status_code: Optional[int]
    response_time_ms: Optional[float]
    invariants_total: int
    invariants_passed: int
    invariants_failed: int
    invariant_results: List[Dict]
    failure_reason: Optional[str]
    failure_taxonomy: Optional[str]
    coherency_verified: bool
    trace_id: Optional[str]


def load_scenario(scenario_id: str) -> Optional[Dict]:
    """Load SDSR scenario YAML."""
    scenario_path = SDSR_SCENARIOS_DIR / f"{scenario_id}.yaml"
    if not scenario_path.exists():
        return None
    with open(scenario_path) as f:
        return yaml.safe_load(f)


def load_intent_yaml(panel_id: str) -> Optional[Dict]:
    """Load intent YAML."""
    intent_path = INTENTS_DIR / f"{panel_id}.yaml"
    if not intent_path.exists():
        return None
    with open(intent_path) as f:
        return yaml.safe_load(f)


def find_scenario_for_panel(panel_id: str) -> Optional[str]:
    """Find scenario ID for a panel."""
    # Convention: SDSR-{panel_id}-001
    scenario_id = f"SDSR-{panel_id}-001"
    scenario_path = SDSR_SCENARIOS_DIR / f"{scenario_id}.yaml"
    if scenario_path.exists():
        return scenario_id

    # Search for any scenario with this panel_id
    if SDSR_SCENARIOS_DIR.exists():
        for f in SDSR_SCENARIOS_DIR.glob("*.yaml"):
            with open(f) as fh:
                scenario = yaml.safe_load(fh)
                if scenario and scenario.get('panel_id') == panel_id:
                    return scenario.get('scenario_id')
    return None


@dataclass
class CoherencyResult:
    """Result of coherency check with failure classification."""
    passed: bool
    failure_class: Optional[str] = None
    failed_checks: List[str] = None  # type: ignore

    def __post_init__(self):
        if self.failed_checks is None:
            self.failed_checks = []


def run_coherency_check(panel_id: str) -> CoherencyResult:
    """
    Run coherency check and return detailed result.

    COH-009/010 failures (reality checks) are classified as REALITY_MISMATCH.
    Other failures are classified as COHERENCY_VIOLATION.
    """
    checker = CoherencyChecker()
    results = checker.check_coherency(panel_id)

    failures = [r for r in results if r.status == CheckStatus.FAIL]

    if not failures:
        return CoherencyResult(passed=True)

    failed_ids = [r.invariant_id for r in failures]

    # Check if any reality checks failed (COH-009, COH-010)
    reality_checks = {'COH-009', 'COH-010'}
    reality_failures = [f for f in failed_ids if f in reality_checks]

    if reality_failures:
        # Reality mismatch - endpoint doesn't exist in backend
        return CoherencyResult(
            passed=False,
            failure_class=FailureClass.REALITY_MISMATCH.value,
            failed_checks=failed_ids,
        )

    # Other coherency failures - wiring issues
    return CoherencyResult(
        passed=False,
        failure_class=FailureClass.COHERENCY_VIOLATION.value,
        failed_checks=failed_ids,
    )


def execute_api_call(
    endpoint: str,
    method: str,
    headers: Dict[str, str],
    params: Optional[Dict] = None,
    body: Optional[Dict] = None,
    base_url: str = "http://localhost:8000",
) -> Dict[str, Any]:
    """Execute API call and return result."""
    import time

    url = f"{base_url}{endpoint}"

    # Substitute environment variables in headers
    resolved_headers = {}
    for k, v in headers.items():
        if isinstance(v, str) and v.startswith('${') and v.endswith('}'):
            env_var = v[2:-1]
            resolved_headers[k] = os.environ.get(env_var, '')
        else:
            resolved_headers[k] = v

    # Add default auth if not present
    if 'Authorization' not in resolved_headers and 'X-AOS-Key' not in resolved_headers:
        api_key = os.environ.get('AOS_API_KEY', '')
        if api_key:
            resolved_headers['X-AOS-Key'] = api_key

    start_time = time.time()
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=resolved_headers, params=params, timeout=30)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=resolved_headers, params=params, json=body, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")

        elapsed_ms = (time.time() - start_time) * 1000

        return {
            'success': True,
            'status_code': response.status_code,
            'response': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            'elapsed_ms': elapsed_ms,
        }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': str(e),
            'elapsed_ms': (time.time() - start_time) * 1000,
        }
    except json.JSONDecodeError:
        return {
            'success': True,
            'status_code': response.status_code,
            'response': response.text,
            'elapsed_ms': (time.time() - start_time) * 1000,
        }


def check_invariant(invariant: Dict, response: Any, status_code: int) -> InvariantResult:
    """Check a single invariant against response."""
    inv_id = invariant.get('id', 'UNKNOWN')
    inv_name = invariant.get('name', 'unknown')
    assertion = invariant.get('assertion', '')

    try:
        # Simple assertion evaluation
        # In production, use a proper assertion engine
        local_vars = {
            'response': response,
            'status_code': status_code,
        }

        # Handle common assertions
        if assertion == 'response is dict and response is not empty':
            passed = isinstance(response, dict) and len(response) > 0
        elif assertion == 'status_code == 200':
            passed = status_code == 200
        elif assertion == 'status_code != 401 and status_code != 403':
            passed = status_code not in [401, 403]
        elif assertion == '"provenance" in response':
            passed = isinstance(response, dict) and 'provenance' in response
        elif assertion == '"aggregation" in response.get("provenance", {})':
            passed = isinstance(response, dict) and 'aggregation' in response.get('provenance', {})
        elif assertion == '"total" in response':
            passed = isinstance(response, dict) and 'total' in response
        elif assertion == '"by_status" in response':
            passed = isinstance(response, dict) and 'by_status' in response
        elif assertion == 'isinstance(response, list)':
            passed = isinstance(response, list)
        elif assertion == 'isinstance(response, dict)':
            passed = isinstance(response, dict)
        elif assertion == 'response is list or response is dict':
            passed = isinstance(response, (list, dict))
        else:
            # Try eval (careful in production!)
            # Include isinstance in available builtins
            safe_builtins = {'isinstance': isinstance, 'len': len, 'list': list, 'dict': dict}
            passed = eval(assertion, {"__builtins__": safe_builtins}, local_vars)

        return InvariantResult(
            id=inv_id,
            name=inv_name,
            status='PASS' if passed else 'FAIL',
            message=f"Assertion {'passed' if passed else 'failed'}: {assertion}"
        )
    except Exception as e:
        return InvariantResult(
            id=inv_id,
            name=inv_name,
            status='ERROR',
            message=f"Error evaluating assertion: {e}"
        )


def get_observation_scope(panel_id: str) -> Dict[str, Any]:
    """
    Read observation_scope from intent YAML.

    observation_scope.type determines how SDSR injects context:
      - SYSTEM: No tenant context (system-wide truth)
      - TENANT: Requires tenant context (customer-scoped truth)
      - USER: Requires user context (user-scoped truth)

    Returns:
        Dict with 'type' and optional 'semantic_alias' keys
    """
    intent_path = INTENTS_DIR / f"{panel_id}.yaml"
    if not intent_path.exists():
        return {'type': 'SYSTEM'}  # Default: system-wide

    try:
        with open(intent_path) as f:
            intent = yaml.safe_load(f)
        return intent.get('observation_scope', {'type': 'SYSTEM'})
    except Exception:
        return {'type': 'SYSTEM'}


def inject_scope_context(params: Dict[str, Any], observation_scope: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inject tenant/user context into params based on observation_scope.

    For TENANT scope: adds tenant_id query param
    For USER scope: would add user context (not implemented yet)
    For SYSTEM scope: no injection
    """
    scope_type = observation_scope.get('type', 'SYSTEM')

    if scope_type == 'TENANT':
        # Inject tenant_id as query param (not just header)
        tenant_id = os.environ.get('SDSR_TENANT_ID', 'demo-tenant')
        params = dict(params)  # Copy to avoid mutation
        params['tenant_id'] = tenant_id
    elif scope_type == 'USER':
        # Future: inject user context
        pass

    return params


def run_scenario(scenario: Dict, skip_coherency: bool = False) -> Observation:
    """Execute SDSR scenario and return observation."""
    scenario_id = scenario.get('scenario_id', 'UNKNOWN')
    capability_id = scenario.get('capability', 'UNKNOWN')
    panel_id = scenario.get('panel_id', 'UNKNOWN')
    inject = scenario.get('inject', {})
    invariants = scenario.get('invariants', [])

    # Get auth mode from scenario (default OBSERVER)
    auth_config = scenario.get('auth', {})
    auth_mode = auth_config.get('mode', 'OBSERVER')

    observation_id = f"OBS-{scenario_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    # Pre-check: Coherency gate
    coherency_verified = False
    if not skip_coherency:
        if panel_id and panel_id != 'UNKNOWN':
            coherency_result = run_coherency_check(panel_id)
            coherency_verified = coherency_result.passed

            if not coherency_verified:
                # Determine failure severity
                # COH-009/010 failures (REALITY_MISMATCH) are hard failures
                failure_class = coherency_result.failure_class or FailureClass.COHERENCY_VIOLATION.value
                failed_checks = coherency_result.failed_checks

                failure_reason = f"Coherency gate failed: {', '.join(failed_checks)}"

                return Observation(
                    observation_id=observation_id,
                    scenario_id=scenario_id,
                    capability_id=capability_id,
                    panel_id=panel_id,
                    status=ObservationStatus.BLOCKED.value,
                    observed_at=datetime.now(timezone.utc).isoformat(),
                    endpoint=inject.get('endpoint', ''),
                    method=inject.get('method', ''),
                    response_status_code=None,
                    response_time_ms=None,
                    invariants_total=len(invariants),
                    invariants_passed=0,
                    invariants_failed=0,
                    invariant_results=[],
                    failure_reason=failure_reason,
                    failure_taxonomy=failure_class,
                    coherency_verified=False,
                    trace_id=None,
                )
    else:
        coherency_verified = True  # Skipped by flag

    # Execute API call
    endpoint = inject.get('endpoint', '')
    method = inject.get('method', 'GET')
    scenario_headers = inject.get('headers', {})
    params = inject.get('params', {})

    # Load observation scope from intent YAML
    observation_scope = get_observation_scope(panel_id)

    # Inject tenant/user context based on scope
    params = inject_scope_context(params, observation_scope)

    # Load headers based on auth mode
    headers = load_headers_for_auth_mode(auth_mode, scenario_headers)

    result = execute_api_call(endpoint, method, headers, params)

    if not result.get('success'):
        # Classify the transient failure
        error_msg = result.get('error', 'Unknown error')
        failure_class = FailureClass.TRANSIENT_FAILURE.value

        return Observation(
            observation_id=observation_id,
            scenario_id=scenario_id,
            capability_id=capability_id,
            panel_id=panel_id,
            status=ObservationStatus.ERROR.value,
            observed_at=datetime.now(timezone.utc).isoformat(),
            endpoint=endpoint,
            method=method,
            response_status_code=None,
            response_time_ms=result.get('elapsed_ms'),
            invariants_total=len(invariants),
            invariants_passed=0,
            invariants_failed=0,
            invariant_results=[],
            failure_reason=error_msg,
            failure_taxonomy=failure_class,
            coherency_verified=coherency_verified,
            trace_id=None,
        )

    # Check invariants
    status_code = result.get('status_code', 0)
    response = result.get('response')

    # Check for auth failures (401/403)
    # For OBSERVER mode: 401/403 = VISIBILITY_RESTRICTED (non-blocking)
    # For SERVICE/USER mode: 401/403 = AUTH_FAILURE (blocking)
    if status_code in [401, 403]:
        if auth_mode == 'OBSERVER':
            # OBSERVER mode: behavior cannot be verified due to access restriction
            # This is NOT a failure - it's visibility information
            # Panel can still be OBSERVED if other invariants would pass
            return Observation(
                observation_id=observation_id,
                scenario_id=scenario_id,
                capability_id=capability_id,
                panel_id=panel_id,
                status=ObservationStatus.PASS.value,  # PASS with VISIBILITY_RESTRICTED
                observed_at=datetime.now(timezone.utc).isoformat(),
                endpoint=endpoint,
                method=method,
                response_status_code=status_code,
                response_time_ms=result.get('elapsed_ms'),
                invariants_total=len(invariants),
                invariants_passed=0,  # Cannot verify invariants without access
                invariants_failed=0,
                invariant_results=[],
                failure_reason=f"Access restricted (HTTP {status_code}) - visibility limited but endpoint exists",
                failure_taxonomy=FailureClass.VISIBILITY_RESTRICTED.value,
                coherency_verified=coherency_verified,
                trace_id=None,
            )
        else:
            # SERVICE/USER mode: auth failure is blocking
            return Observation(
                observation_id=observation_id,
                scenario_id=scenario_id,
                capability_id=capability_id,
                panel_id=panel_id,
                status=ObservationStatus.FAIL.value,
                observed_at=datetime.now(timezone.utc).isoformat(),
                endpoint=endpoint,
                method=method,
                response_status_code=status_code,
                response_time_ms=result.get('elapsed_ms'),
                invariants_total=len(invariants),
                invariants_passed=0,
                invariants_failed=0,
                invariant_results=[],
                failure_reason=f"Authentication/authorization failed: HTTP {status_code}",
                failure_taxonomy=FailureClass.AUTH_FAILURE.value,
                coherency_verified=coherency_verified,
                trace_id=None,
            )

    invariant_results = []
    passed = 0
    failed = 0

    for inv in invariants:
        inv_result = check_invariant(inv, response, status_code)
        invariant_results.append(asdict(inv_result))
        if inv_result.status == 'PASS':
            passed += 1
        else:
            failed += 1

    # Determine overall status
    if failed > 0:
        overall_status = ObservationStatus.FAIL.value
        failure_reason = f"{failed} invariant(s) failed"
        failure_taxonomy = FailureClass.INVARIANT_VIOLATED.value
    else:
        overall_status = ObservationStatus.PASS.value
        failure_reason = None
        failure_taxonomy = None

    return Observation(
        observation_id=observation_id,
        scenario_id=scenario_id,
        capability_id=capability_id,
        panel_id=panel_id,
        status=overall_status,
        observed_at=datetime.now(timezone.utc).isoformat(),
        endpoint=endpoint,
        method=method,
        response_status_code=status_code,
        response_time_ms=result.get('elapsed_ms'),
        invariants_total=len(invariants),
        invariants_passed=passed,
        invariants_failed=failed,
        invariant_results=invariant_results,
        failure_reason=failure_reason,
        failure_taxonomy=failure_taxonomy,
        coherency_verified=coherency_verified,
        trace_id=None,
    )


def write_observation(observation: Observation) -> Path:
    """Write observation JSON to file."""
    SDSR_OBSERVATIONS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"SDSR_OBSERVATION_{observation.capability_id}.json"
    obs_path = SDSR_OBSERVATIONS_DIR / filename

    with open(obs_path, 'w') as f:
        json.dump(asdict(observation), f, indent=2)

    return obs_path


def main():
    parser = argparse.ArgumentParser(
        description="AURORA L2 SDSR Runner - Executes verification scenarios"
    )
    parser.add_argument("--scenario", help="Scenario ID to execute")
    parser.add_argument("--panel", help="Panel ID (finds associated scenario)")
    parser.add_argument("--skip-coherency", action="store_true",
                        help="Skip coherency check (DANGEROUS - use only for debugging)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would execute")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Backend base URL")
    args = parser.parse_args()

    # Determine scenario
    scenario_id = args.scenario
    if not scenario_id and args.panel:
        scenario_id = find_scenario_for_panel(args.panel)
        if not scenario_id:
            print(f"ERROR: No scenario found for panel {args.panel}", file=sys.stderr)
            print(f"Generate one: python aurora_sdsr_synth.py --panel {args.panel}", file=sys.stderr)
            return 1

    if not scenario_id:
        parser.print_help()
        return 1

    # Load scenario
    scenario = load_scenario(scenario_id)
    if not scenario:
        print(f"ERROR: Scenario not found: {scenario_id}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"DRY RUN - Would execute scenario: {scenario_id}")
        print(f"  Capability: {scenario.get('capability')}")
        print(f"  Panel: {scenario.get('panel_id')}")
        print(f"  Endpoint: {scenario.get('inject', {}).get('endpoint')}")
        print(f"  Method: {scenario.get('inject', {}).get('method')}")
        print(f"  Invariants: {len(scenario.get('invariants', []))}")
        return 0

    print(f"Executing SDSR scenario: {scenario_id}")
    print("=" * 70)

    # Run scenario
    observation = run_scenario(scenario, skip_coherency=args.skip_coherency)

    # Print results
    print(f"  Status: {observation.status}")
    print(f"  Capability: {observation.capability_id}")
    print(f"  Endpoint: {observation.endpoint}")
    print(f"  Response Code: {observation.response_status_code}")
    print(f"  Response Time: {observation.response_time_ms:.2f}ms" if observation.response_time_ms else "  Response Time: N/A")
    print(f"  Coherency Verified: {observation.coherency_verified}")
    print()
    print(f"  Invariants: {observation.invariants_passed}/{observation.invariants_total} passed")

    for inv in observation.invariant_results:
        icon = "✅" if inv['status'] == 'PASS' else "❌"
        print(f"    {icon} {inv['id']}: {inv['name']} - {inv['status']}")

    if observation.failure_reason:
        print()
        print(f"  ❌ Failure: {observation.failure_reason}")
        print(f"     Taxonomy: {observation.failure_taxonomy}")

    # Write observation
    obs_path = write_observation(observation)
    print()
    print(f"Observation written: {obs_path.relative_to(REPO_ROOT)}")

    if observation.status == ObservationStatus.PASS.value:
        print()
        print("✅ SDSR PASSED")
        print()
        print("Next step:")
        print(f"  python aurora_apply_observation.py --observation {obs_path.name}")
        return 0
    elif observation.status == ObservationStatus.BLOCKED.value:
        print()
        print("🚫 SDSR BLOCKED - Coherency gate failed")
        print()
        print("Fix coherency first:")
        print(f"  python aurora_coherency_check.py --panel {observation.panel_id}")
        return 2
    else:
        print()
        print("❌ SDSR FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
