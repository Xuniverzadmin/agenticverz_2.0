#!/usr/bin/env python3
"""
AURORA L2 Coherency Gate (Phase 3.5)

Validates consistency between:
  UI Plan → Intent YAML → Capability YAML → Backend Routes

This gate MUST pass before SDSR execution is allowed.
Failure blocks the pipeline - no workarounds.

Usage:
    python aurora_coherency_check.py --panel OVR-SUM-HL-O1
    python aurora_coherency_check.py --all
    python aurora_coherency_check.py --panel OVR-SUM-HL-O1 --update-capability

Invariants:
    COH-001: ui_plan.panel_id == intent.panel_id
    COH-002: ui_plan.intent_spec path exists
    COH-003: intent.capability.id == capability.capability_id
    COH-004: intent.assumed_endpoint == capability.assumption.endpoint (human consistency)
    COH-005: intent.assumed_method == capability.assumption.method (human consistency)
    COH-006: intent.metadata.domain == capability.domain (if declared)
    COH-007: capability.status in valid FSM states (ASSUMED → OBSERVED → TRUSTED)
    COH-008: intent.sdsr.verified → capability.status >= OBSERVED
    COH-009: assumed_endpoint exists in backend routes (reality check)
    COH-010: assumed_method matches backend route method (reality check)

Author: AURORA L2 Automation
"""

import yaml
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

# Paths (relative to repo root)
REPO_ROOT = Path(__file__).parent.parent.parent.parent
UI_PLAN = REPO_ROOT / "design/l2_1/ui_plan.yaml"
INTENTS_DIR = REPO_ROOT / "design/l2_1/intents"
CAPABILITY_REGISTRY = REPO_ROOT / "backend/AURORA_L2_CAPABILITY_REGISTRY"
BACKEND_API_DIR = REPO_ROOT / "backend/app/api"
ROUTES_CACHE = REPO_ROOT / "backend/aurora_l2/tools/.routes_cache.json"


class CheckStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    WARN = "WARN"


@dataclass
class CheckResult:
    invariant_id: str
    status: CheckStatus
    message: str
    details: Optional[Dict[str, Any]] = None


class CoherencyChecker:
    """
    Validates coherency across UI Plan, Intent, Capability, and Backend.
    """

    VALID_CAPABILITY_STATUSES = ["DECLARED", "ASSUMED", "OBSERVED", "TRUSTED", "DEPRECATED"]
    OBSERVED_OR_HIGHER = ["OBSERVED", "TRUSTED"]

    def __init__(self):
        self.ui_plan = None
        self.routes_cache = None
        self._load_ui_plan()
        self._load_routes_cache()

    def _load_ui_plan(self):
        """Load the UI plan YAML."""
        if UI_PLAN.exists():
            with open(UI_PLAN) as f:
                self.ui_plan = yaml.safe_load(f)
        else:
            self.ui_plan = None

    def _load_routes_cache(self):
        """Load cached backend routes or generate them.

        HARDENING: Empty or corrupt cache = hard fail, not silent regeneration.
        This prevents thrash loops when cache becomes invalid.
        """
        if ROUTES_CACHE.exists():
            # Guard: Check file is non-empty
            if ROUTES_CACHE.stat().st_size == 0:
                raise SystemExit(
                    f"COHERENCY BLOCKED: Routes cache is empty (0 bytes).\n"
                    f"File: {ROUTES_CACHE}\n"
                    f"Fix: Delete the file and re-run with --refresh-routes"
                )

            with open(ROUTES_CACHE) as f:
                try:
                    self.routes_cache = json.load(f)
                except json.JSONDecodeError as e:
                    raise SystemExit(
                        f"COHERENCY BLOCKED: Routes cache is corrupt.\n"
                        f"File: {ROUTES_CACHE}\n"
                        f"Error: {e}\n"
                        f"Fix: Delete the file and re-run with --refresh-routes"
                    )

            # Guard: Check cache has routes
            if not isinstance(self.routes_cache, dict) or len(self.routes_cache) == 0:
                raise SystemExit(
                    f"COHERENCY BLOCKED: Routes cache is empty dict.\n"
                    f"File: {ROUTES_CACHE}\n"
                    f"Fix: Re-run with --refresh-routes"
                )
        else:
            # Generate routes cache
            self.routes_cache = self._introspect_backend_routes()
            self._save_routes_cache()

    def _save_routes_cache(self):
        """Save routes cache to disk."""
        ROUTES_CACHE.parent.mkdir(parents=True, exist_ok=True)
        with open(ROUTES_CACHE, 'w') as f:
            json.dump(self.routes_cache, f, indent=2)

    def _introspect_backend_routes(self) -> Dict[str, List[str]]:
        """
        Introspect FastAPI routes from source files.
        Returns dict of {endpoint: [methods]}.
        """
        import re
        routes = {}

        # Pattern to match router decorators
        decorator_pattern = re.compile(
            r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']*)["\']',
            re.IGNORECASE
        )

        # Pattern to match router prefix in APIRouter()
        prefix_pattern = re.compile(
            r'router\s*=\s*APIRouter\s*\([^)]*prefix\s*=\s*["\']([^"\']*)["\']',
            re.IGNORECASE
        )

        # Known prefixes from main.py (hardcoded for reliability)
        known_prefixes = {
            'activity.py': '/api/v1/activity',
            'incidents.py': '/api/v1/incidents',
            'policy.py': '/api/v1/policies',
            'policy_proposals.py': '/api/v1/policy-proposals',
            'traces.py': '/api/v1/traces',
            'runtime.py': '/api/v1/runtime',
            'agents.py': '/api/v1/agents',
            'scenarios.py': '/api/v1/scenarios',
            'health.py': '',
            'ops.py': '/api/v1/ops',
            'feedback.py': '/api/v1/feedback',
            'tenants.py': '/api/v1',  # Fixed: router has prefix="/api/v1", not /api/v1/tenants
            'guard.py': '/api/v1/guard',
        }

        for api_file in BACKEND_API_DIR.glob("*.py"):
            if api_file.name.startswith('__'):
                continue

            try:
                content = api_file.read_text()

                # Get prefix
                prefix = known_prefixes.get(api_file.name, '')
                if not prefix:
                    prefix_match = prefix_pattern.search(content)
                    if prefix_match:
                        prefix = prefix_match.group(1)

                # Find all route decorators
                for match in decorator_pattern.finditer(content):
                    method = match.group(1).upper()
                    path = match.group(2)

                    # Build full endpoint
                    if path.startswith('/'):
                        endpoint = prefix + path
                    else:
                        endpoint = prefix + '/' + path if path else prefix

                    # Normalize
                    endpoint = endpoint.rstrip('/')
                    if not endpoint:
                        endpoint = '/'

                    if endpoint not in routes:
                        routes[endpoint] = []
                    if method not in routes[endpoint]:
                        routes[endpoint].append(method)

            except Exception as e:
                print(f"Warning: Could not parse {api_file}: {e}", file=sys.stderr)

        return routes

    def refresh_routes_cache(self):
        """Force refresh of routes cache."""
        self.routes_cache = self._introspect_backend_routes()
        self._save_routes_cache()

    def find_panel_in_ui_plan(self, panel_id: str) -> Optional[Dict]:
        """Find a panel entry in ui_plan.yaml."""
        if not self.ui_plan:
            return None

        for domain in self.ui_plan.get('domains', []):
            for subdomain in domain.get('subdomains', []):
                for topic in subdomain.get('topics', []):
                    for panel in topic.get('panels', []):
                        if panel.get('panel_id') == panel_id:
                            return {
                                'panel': panel,
                                'domain_id': domain.get('id'),
                                'subdomain_id': subdomain.get('id'),
                                'topic_id': topic.get('id'),
                            }
        return None

    def check_coherency(self, panel_id: str) -> List[CheckResult]:
        """
        Run all coherency checks for a panel.
        Returns list of CheckResult objects.
        """
        results = []

        # COH-001: Panel exists in ui_plan
        panel_entry = self.find_panel_in_ui_plan(panel_id)
        if not panel_entry:
            results.append(CheckResult(
                "COH-001", CheckStatus.FAIL,
                f"Panel {panel_id} not found in ui_plan.yaml"
            ))
            return results  # Can't continue without ui_plan entry

        results.append(CheckResult(
            "COH-001", CheckStatus.PASS,
            "Panel exists in ui_plan.yaml",
            {"domain": panel_entry['domain_id'], "subdomain": panel_entry['subdomain_id']}
        ))

        panel_data = panel_entry['panel']
        panel_state = panel_data.get('state', 'EMPTY')

        # EMPTY panels don't have intent YAMLs - skip coherency checks beyond COH-001
        if panel_state == 'EMPTY':
            results.append(CheckResult(
                "COH-002", CheckStatus.SKIP,
                f"Panel state is EMPTY - no intent YAML required yet",
                {"state": panel_state}
            ))
            return results  # Valid EMPTY panel, coherency OK for this state

        # COH-002: Intent spec path exists
        intent_spec = panel_data.get('intent_spec')
        if intent_spec:
            intent_path = REPO_ROOT / intent_spec
        else:
            # New naming convention with fallback to legacy
            intent_path = INTENTS_DIR / f"AURORA_L2_INTENT_{panel_id}.yaml"
            if not intent_path.exists():
                intent_path = INTENTS_DIR / f"{panel_id}.yaml"  # Legacy fallback

        if not intent_path.exists():
            results.append(CheckResult(
                "COH-002", CheckStatus.FAIL,
                f"Intent YAML not found: {intent_path.relative_to(REPO_ROOT)}"
            ))
            return results  # Can't continue without intent

        results.append(CheckResult(
            "COH-002", CheckStatus.PASS,
            f"Intent YAML exists: {intent_path.relative_to(REPO_ROOT)}"
        ))

        # Load intent YAML
        with open(intent_path) as f:
            intent = yaml.safe_load(f)

        # Verify panel_id matches
        if intent.get('panel_id') != panel_id:
            results.append(CheckResult(
                "COH-001", CheckStatus.FAIL,
                f"Intent panel_id mismatch: {intent.get('panel_id')} != {panel_id}"
            ))
            return results

        # Get capability reference
        capability_ref = intent.get('capability', {})
        capability_id = capability_ref.get('id')

        if not capability_id:
            results.append(CheckResult(
                "COH-003", CheckStatus.FAIL,
                "Intent has no capability.id defined"
            ))
            return results

        # COH-003: Capability YAML exists and ID matches
        capability_filename = f"AURORA_L2_CAPABILITY_{capability_id}.yaml"
        capability_path = CAPABILITY_REGISTRY / capability_filename

        if not capability_path.exists():
            results.append(CheckResult(
                "COH-003", CheckStatus.FAIL,
                f"Capability YAML not found: {capability_filename}",
                {"expected_path": str(capability_path.relative_to(REPO_ROOT))}
            ))
            return results

        # Load capability YAML
        with open(capability_path) as f:
            capability = yaml.safe_load(f)

        cap_id = capability.get('capability_id')
        if cap_id != capability_id:
            results.append(CheckResult(
                "COH-003", CheckStatus.FAIL,
                f"Capability ID mismatch: file has '{cap_id}', intent expects '{capability_id}'"
            ))
        else:
            results.append(CheckResult(
                "COH-003", CheckStatus.PASS,
                f"Capability ID matches: {capability_id}"
            ))

        # COH-004: Assumed endpoint consistency (human assumption should match across artifacts)
        intent_assumed_endpoint = capability_ref.get('assumed_endpoint')
        cap_assumption = capability.get('assumption', {})
        cap_assumed_endpoint = cap_assumption.get('endpoint')

        if intent_assumed_endpoint and cap_assumed_endpoint:
            if intent_assumed_endpoint != cap_assumed_endpoint:
                results.append(CheckResult(
                    "COH-004", CheckStatus.FAIL,
                    f"Assumed endpoint mismatch: intent='{intent_assumed_endpoint}', capability='{cap_assumed_endpoint}'"
                ))
            else:
                results.append(CheckResult(
                    "COH-004", CheckStatus.PASS,
                    f"Assumed endpoints consistent: {intent_assumed_endpoint}"
                ))
        elif intent_assumed_endpoint and not cap_assumed_endpoint:
            results.append(CheckResult(
                "COH-004", CheckStatus.WARN,
                f"Intent has assumed_endpoint '{intent_assumed_endpoint}' but capability assumption missing"
            ))
        else:
            results.append(CheckResult(
                "COH-004", CheckStatus.SKIP,
                "No assumed_endpoint declared in intent"
            ))

        # COH-005: Assumed method consistency
        intent_assumed_method = capability_ref.get('assumed_method')
        cap_assumed_method = cap_assumption.get('method')

        if intent_assumed_method and cap_assumed_method:
            if intent_assumed_method.upper() != cap_assumed_method.upper():
                results.append(CheckResult(
                    "COH-005", CheckStatus.FAIL,
                    f"Assumed method mismatch: intent='{intent_assumed_method}', capability='{cap_assumed_method}'"
                ))
            else:
                results.append(CheckResult(
                    "COH-005", CheckStatus.PASS,
                    f"Assumed methods consistent: {intent_assumed_method}"
                ))
        else:
            results.append(CheckResult(
                "COH-005", CheckStatus.SKIP,
                "Assumed method not declared in both intent and capability"
            ))

        # COH-006: Domain match
        intent_domain = intent.get('metadata', {}).get('domain')
        cap_domain = capability.get('domain')

        if intent_domain and cap_domain:
            if intent_domain != cap_domain:
                results.append(CheckResult(
                    "COH-006", CheckStatus.FAIL,
                    f"Domain mismatch: intent='{intent_domain}', capability='{cap_domain}'"
                ))
            else:
                results.append(CheckResult(
                    "COH-006", CheckStatus.PASS,
                    f"Domains match: {intent_domain}"
                ))
        else:
            results.append(CheckResult(
                "COH-006", CheckStatus.SKIP,
                "Domain not declared in capability"
            ))

        # COH-007: Valid capability status
        cap_status = capability.get('status')
        if cap_status not in self.VALID_CAPABILITY_STATUSES:
            results.append(CheckResult(
                "COH-007", CheckStatus.FAIL,
                f"Invalid capability status: '{cap_status}'",
                {"valid_statuses": self.VALID_CAPABILITY_STATUSES}
            ))
        else:
            results.append(CheckResult(
                "COH-007", CheckStatus.PASS,
                f"Capability status valid: {cap_status}"
            ))

        # COH-008: sdsr.verified implies OBSERVED or higher
        sdsr_verified = intent.get('sdsr', {}).get('verified', False)
        if sdsr_verified:
            if cap_status not in self.OBSERVED_OR_HIGHER:
                results.append(CheckResult(
                    "COH-008", CheckStatus.FAIL,
                    f"Intent says sdsr.verified=true but capability status='{cap_status}' (expected OBSERVED or TRUSTED)"
                ))
            else:
                results.append(CheckResult(
                    "COH-008", CheckStatus.PASS,
                    "SDSR verification status consistent"
                ))
        else:
            results.append(CheckResult(
                "COH-008", CheckStatus.SKIP,
                "SDSR not yet verified"
            ))

        # COH-009/010: Backend route exists with correct method (reality check)
        # Use assumed_endpoint from intent - this is what SDSR will test
        endpoint_to_check = intent_assumed_endpoint or cap_assumed_endpoint
        method_to_check = (intent_assumed_method or cap_assumed_method or 'GET').upper()

        if endpoint_to_check:
            # Check if endpoint exists
            if endpoint_to_check in self.routes_cache:
                results.append(CheckResult(
                    "COH-009", CheckStatus.PASS,
                    f"Backend route exists: {endpoint_to_check}"
                ))

                # Check method
                available_methods = self.routes_cache[endpoint_to_check]
                if method_to_check in available_methods:
                    results.append(CheckResult(
                        "COH-010", CheckStatus.PASS,
                        f"Route method matches: {method_to_check}"
                    ))
                else:
                    results.append(CheckResult(
                        "COH-010", CheckStatus.FAIL,
                        f"Method '{method_to_check}' not available for {endpoint_to_check}",
                        {"available_methods": available_methods}
                    ))
            else:
                # Try partial match (endpoint might have path params)
                partial_match = self._find_partial_route_match(endpoint_to_check)
                if partial_match:
                    results.append(CheckResult(
                        "COH-009", CheckStatus.WARN,
                        f"Partial route match found: {partial_match}",
                        {"requested": endpoint_to_check}
                    ))
                    results.append(CheckResult(
                        "COH-010", CheckStatus.SKIP,
                        "Skipped - using partial match"
                    ))
                else:
                    results.append(CheckResult(
                        "COH-009", CheckStatus.FAIL,
                        f"Backend route not found: {endpoint_to_check}",
                        {"available_routes_sample": list(self.routes_cache.keys())[:10]}
                    ))
                    results.append(CheckResult(
                        "COH-010", CheckStatus.SKIP,
                        "Skipped - route not found"
                    ))
        else:
            results.append(CheckResult(
                "COH-009", CheckStatus.SKIP,
                "No endpoint declared"
            ))
            results.append(CheckResult(
                "COH-010", CheckStatus.SKIP,
                "No endpoint declared"
            ))

        return results

    def _find_partial_route_match(self, endpoint: str) -> Optional[str]:
        """Find a route that might match with path parameters."""
        import re

        # Convert /api/v1/activity/summary to pattern
        # that would match /api/v1/activity/{something}
        parts = endpoint.split('/')

        for route in self.routes_cache.keys():
            route_parts = route.split('/')
            if len(route_parts) != len(parts):
                continue

            match = True
            for i, (ep, rp) in enumerate(zip(parts, route_parts)):
                if ep == rp:
                    continue
                if rp.startswith('{') and rp.endswith('}'):
                    continue  # Path parameter, consider it a match
                match = False
                break

            if match:
                return route

        return None

    def update_capability_coherency(self, panel_id: str, status: str) -> bool:
        """
        Update the coherency block in capability YAML after check.
        """
        panel_entry = self.find_panel_in_ui_plan(panel_id)
        if not panel_entry:
            return False

        intent_spec = panel_entry['panel'].get('intent_spec')
        if intent_spec:
            intent_path = REPO_ROOT / intent_spec
        else:
            # New naming convention with fallback to legacy
            intent_path = INTENTS_DIR / f"AURORA_L2_INTENT_{panel_id}.yaml"
            if not intent_path.exists():
                intent_path = INTENTS_DIR / f"{panel_id}.yaml"  # Legacy fallback

        if not intent_path.exists():
            return False

        with open(intent_path) as f:
            intent = yaml.safe_load(f)

        capability_id = intent.get('capability', {}).get('id')
        if not capability_id:
            return False

        capability_path = CAPABILITY_REGISTRY / f"AURORA_L2_CAPABILITY_{capability_id}.yaml"
        if not capability_path.exists():
            return False

        with open(capability_path) as f:
            capability = yaml.safe_load(f)

        # Update coherency block
        capability['coherency'] = {
            'last_checked': datetime.now(timezone.utc).isoformat(),
            'status': status,
            'checked_by': 'aurora_coherency_check.py',
        }

        # Write back
        with open(capability_path, 'w') as f:
            yaml.dump(capability, f, default_flow_style=False, sort_keys=False)

        return True


def print_results(panel_id: str, results: List[CheckResult], verbose: bool = False):
    """Print coherency check results."""
    print(f"\nCOHERENCY CHECK: {panel_id}")
    print("=" * 70)

    for r in results:
        if r.status == CheckStatus.PASS:
            icon = "✅"
        elif r.status == CheckStatus.FAIL:
            icon = "❌"
        elif r.status == CheckStatus.WARN:
            icon = "⚠️"
        else:
            icon = "⏭️"

        print(f"  {r.invariant_id}  {icon} {r.status.value:4}  {r.message}")

        if verbose and r.details:
            for k, v in r.details.items():
                print(f"           └─ {k}: {v}")


def get_all_panel_ids() -> List[str]:
    """Get all panel IDs from ui_plan.yaml."""
    if not UI_PLAN.exists():
        return []

    with open(UI_PLAN) as f:
        ui_plan = yaml.safe_load(f)

    panel_ids = []
    for domain in ui_plan.get('domains', []):
        for subdomain in domain.get('subdomains', []):
            for topic in subdomain.get('topics', []):
                for panel in topic.get('panels', []):
                    panel_ids.append(panel.get('panel_id'))

    return panel_ids


def main():
    parser = argparse.ArgumentParser(
        description="AURORA L2 Coherency Gate - Validates UI/Intent/Capability/Backend consistency"
    )
    parser.add_argument("--panel", help="Panel ID to check")
    parser.add_argument("--all", action="store_true", help="Check all panels in ui_plan")
    parser.add_argument("--refresh-routes", action="store_true", help="Refresh backend routes cache")
    parser.add_argument("--update-capability", action="store_true",
                        help="Update capability YAML with coherency status")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    checker = CoherencyChecker()

    if args.refresh_routes:
        print("Refreshing backend routes cache...")
        checker.refresh_routes_cache()
        print(f"Cached {len(checker.routes_cache)} routes to {ROUTES_CACHE}")
        if not args.panel and not args.all:
            return 0

    if not args.panel and not args.all:
        parser.print_help()
        return 1

    panels_to_check = []
    if args.all:
        panels_to_check = get_all_panel_ids()
    else:
        panels_to_check = [args.panel]

    all_results = {}
    total_failures = 0

    for panel_id in panels_to_check:
        results = checker.check_coherency(panel_id)
        all_results[panel_id] = results

        failures = [r for r in results if r.status == CheckStatus.FAIL]
        total_failures += len(failures)

        if not args.json:
            print_results(panel_id, results, args.verbose)

            if failures:
                print(f"\n❌ COHERENCY GATE FAILED: {len(failures)} violations")
            else:
                print(f"\n✅ COHERENCY GATE PASSED")

        if args.update_capability and not failures:
            if checker.update_capability_coherency(panel_id, "PASSED"):
                print(f"   Updated capability coherency status for {panel_id}")

    if args.json:
        output = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_panels": len(panels_to_check),
            "total_failures": total_failures,
            "results": {
                panel_id: [
                    {
                        "invariant": r.invariant_id,
                        "status": r.status.value,
                        "message": r.message,
                        "details": r.details
                    }
                    for r in results
                ]
                for panel_id, results in all_results.items()
            }
        }
        print(json.dumps(output, indent=2))

    return 1 if total_failures > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
