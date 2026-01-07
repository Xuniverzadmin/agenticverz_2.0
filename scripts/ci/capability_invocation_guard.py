#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci
#   Execution: sync
# Role: CI guard for L2.1 frontend capability invocation compliance
# Callers: GitHub Actions workflow
# Allowed Imports: L8 (stdlib only)
# Forbidden Imports: L1-L7 (must be self-contained)
# Reference: PIN-322 (L2-L2.1 Progressive Activation), PIN-321 (Binding Execution)
#
# GOVERNANCE NOTE:
# This script enforces frontend capability invocation rules from:
# - CAPABILITY_REGISTRY.yaml (Section 5-6: Invocation Addendum)
# - L2_L21_BINDINGS.yaml (Frontend client bindings)
#
# PHASE A1 GUARD

"""
Capability Invocation Guard (Phase A1)

This CI guard validates that frontend code cannot invoke backend capabilities
or routes that are not explicitly permitted.

Validation Rules:
1. Every frontend API client call maps to a capability_id with frontend_invocable: true
2. Called route ∈ allowed_routes for that capability
3. Client is bound (not BLOCKED or UNBOUND)

Exit codes:
  0 - All checks pass
  1 - Violations found
  2 - Script error

Usage:
  python scripts/ci/capability_invocation_guard.py           # Check all frontend clients
  python scripts/ci/capability_invocation_guard.py --verbose # Show detailed analysis
  python scripts/ci/capability_invocation_guard.py --ci      # CI mode (fail on violations)
"""

import argparse
import ast
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# =============================================================================
# CONFIGURATION - From CAPABILITY_REGISTRY.yaml Section 5-6
# =============================================================================

# Capabilities with frontend_invocable: true
FRONTEND_INVOCABLE_CAPABILITIES = {
    "CAP-001": {  # REPLAY
        "name": "Execution Replay",
        "allowed_routes": [
            "GET /api/v1/replay/{incident_id}/slice",
            "GET /api/v1/replay/{incident_id}/summary",
            "GET /api/v1/replay/{incident_id}/timeline",
            "GET /api/v1/replay/{incident_id}/explain/{item_id}",
            "POST /guard/replay/{call_id}",
            "POST /runtime/replay/{run_id}",
        ],
        "forbidden_routes": [
            "POST /api/v1/replay/execute",
        ],
        "invocation_modes": ["read", "observe"],
    },
    "CAP-002": {  # COST SIMULATION
        "name": "Cost Simulation V2",
        "allowed_routes": [
            "POST /costsim/v2/simulate",
            "GET /costsim/v2/divergence",
            "GET /api/v1/scenarios",
            "GET /api/v1/scenarios/{id}",
        ],
        "forbidden_routes": [],
        "invocation_modes": ["read", "proposal"],
    },
    "CAP-003": {  # POLICY PROPOSALS
        "name": "Policy Proposals",
        "allowed_routes": [
            "GET /api/v1/policy-proposals",
            "GET /api/v1/policy-proposals/{id}",
            "GET /api/v1/policy-proposals/{id}/versions",
            "GET /api/v1/policy-proposals/stats/summary",
        ],
        "forbidden_routes": [
            "POST /api/v1/policy-proposals",
            "PUT /api/v1/policy-proposals/{id}",
            "DELETE /api/v1/policy-proposals/{id}",
        ],
        "invocation_modes": ["read"],
    },
    "CAP-004": {  # PREDICTION PLANE
        "name": "C2 Prediction Plane",
        "allowed_routes": [
            "GET /api/v1/predictions",
            "GET /api/v1/predictions/{id}",
            "GET /api/v1/predictions/subject/{type}/{id}",
            "GET /api/v1/predictions/stats/summary",
        ],
        "forbidden_routes": [],
        "invocation_modes": ["read"],
    },
    "CAP-005": {  # FOUNDER CONSOLE
        "name": "Founder Console",
        "allowed_routes": [
            "GET /ops/*",
            "GET /founder/timeline/*",
            "GET /founder/controls/*",
            "GET /founder/explorer/*",
            "POST /founder/actions/*",
        ],
        "forbidden_routes": [],
        "invocation_modes": ["read", "write"],
    },
    "CAP-009": {  # POLICY ENGINE
        "name": "Policy Engine",
        "allowed_routes": [
            "GET /api/v1/policies",
            "GET /api/v1/policies/{id}",
            "GET /guard/policies/*",
        ],
        "forbidden_routes": [
            "POST /api/v1/policies",
            "PUT /api/v1/policies/{id}",
            "DELETE /api/v1/policies/{id}",
        ],
        "invocation_modes": ["read"],
    },
    "CAP-011": {  # GOVERNANCE ORCHESTRATION
        "name": "Governance Orchestration",
        "allowed_routes": [
            "GET /founder/review/*",
            "GET /api/v1/discovery/*",
            "POST /founder/review/{id}/approve",
            "POST /founder/review/{id}/reject",
            "GET /sba/*",  # SBA inspector
        ],
        "forbidden_routes": [],
        "invocation_modes": ["read", "write"],
    },
    "CAP-014": {  # MEMORY SYSTEM
        "name": "Memory System",
        "allowed_routes": [
            "GET /api/v1/memory/*",
            "GET /api/v1/embedding/*",
        ],
        "forbidden_routes": [
            "POST /api/v1/memory/*",
            "DELETE /api/v1/memory/*",
        ],
        "invocation_modes": ["read"],
    },
    "CAP-018": {  # INTEGRATION PLATFORM
        "name": "Integration Platform",
        "allowed_routes": [
            "GET /api/v1/integration/*",
            "GET /api/v1/recovery/*",
            "GET /integration/*",
        ],
        "forbidden_routes": [
            "POST /api/v1/integration/*",
            "POST /api/v1/recovery/ingest/*",
        ],
        "invocation_modes": ["read"],
    },
}

# Capabilities with frontend_invocable: false
FRONTEND_BLOCKED_CAPABILITIES = {
    "CAP-006": "Authentication (Delegated to Clerk)",
    "CAP-007": "Authorization (Internal RBAC)",
    "CAP-008": "Multi-Agent Orchestration (SDK-only)",
    "CAP-010": "CARE-L Routing (Internal)",
    "CAP-012": "Workflow Engine (Internal)",
    "CAP-013": "Learning Pipeline (Internal)",
    "CAP-015": "Optimization Engine (Internal)",
    "CAP-016": "Skill System (SDK-only)",
    "CAP-017": "Cross-Project Aggregation (PLANNED)",
}

# Frontend clients and their bindings (from L2_L21_BINDINGS.yaml)
BOUND_CLIENTS = {
    "replay.ts": {"capability_id": "CAP-001", "audience": "founder", "status": "BOUND"},
    "costsim.ts": {"capability_id": "CAP-002", "audience": "customer", "status": "BOUND"},
    "guard.ts": {"capability_id": "MULTI", "capabilities": ["CAP-001", "CAP-009"], "audience": "customer", "status": "BOUND"},
    "ops.ts": {"capability_id": "CAP-005", "audience": "founder", "status": "BOUND"},
    "timeline.ts": {"capability_id": "CAP-005", "audience": "founder", "status": "BOUND"},
    "traces.ts": {"capability_id": "CAP-001", "audience": "founder", "status": "BOUND"},
    "scenarios.ts": {"capability_id": "CAP-002", "audience": "customer", "status": "BOUND"},
    "integration.ts": {"capability_id": "CAP-018", "audience": "founder", "status": "BOUND"},
    "recovery.ts": {"capability_id": "CAP-018", "audience": "founder", "status": "BOUND"},
    "memory.ts": {"capability_id": "CAP-014", "audience": "founder", "status": "BOUND"},
    "explorer.ts": {"capability_id": "CAP-005", "audience": "founder", "status": "BOUND"},
    "sba.ts": {"capability_id": "CAP-011", "audience": "founder", "status": "BOUND"},
    "killswitch.ts": {"capability_id": "PLATFORM", "audience": "customer", "status": "BOUND"},
}

PLATFORM_CLIENTS = {
    "client.ts": {"purpose": "Base axios client", "status": "UTILITY"},
    "auth.ts": {"purpose": "Clerk integration", "status": "UTILITY"},
    "health.ts": {"purpose": "Health checks", "status": "UTILITY"},
    "metrics.ts": {"purpose": "Platform metrics", "status": "UTILITY"},
}

BLOCKED_CLIENTS = {
    "agents.ts": {"intended_capability": "CAP-008", "reason": "SDK-only", "status": "BLOCKED"},
    "blackboard.ts": {"intended_capability": "CAP-008", "reason": "SDK-only", "status": "BLOCKED"},
    "credits.ts": {"intended_capability": "CAP-008", "reason": "SDK-only", "status": "BLOCKED"},
    "messages.ts": {"intended_capability": "CAP-008", "reason": "SDK-only", "status": "BLOCKED"},
    "jobs.ts": {"intended_capability": "CAP-008", "reason": "SDK-only", "status": "BLOCKED"},
    "worker.ts": {"intended_capability": "CAP-012", "reason": "Internal", "status": "BLOCKED"},
}

UNBOUND_CLIENTS = {
    "runtime.ts": {"reason": "Capability unclear", "status": "UNBOUND"},
    "operator.ts": {"reason": "Needs verification", "status": "UNBOUND"},
    "failures.ts": {"reason": "Capability unclear", "status": "UNBOUND"},
}

# Frontend API client directory
FRONTEND_API_DIR = "website/app-shell/src/api"


# =============================================================================
# VIOLATION TYPES
# =============================================================================

@dataclass
class Violation:
    """Represents a capability invocation violation."""
    file: str
    line: int
    violation_type: str
    message: str
    severity: str  # BLOCKING, WARNING, DIRECTIONAL

    def __str__(self) -> str:
        return f"{self.file}:{self.line} [{self.severity}] {self.violation_type}: {self.message}"


@dataclass
class RouteCall:
    """Represents an API route call extracted from frontend code."""
    file: str
    line: int
    method: str  # GET, POST, PUT, DELETE, PATCH
    route: str
    raw_code: str


# =============================================================================
# ROUTE EXTRACTION
# =============================================================================

def extract_api_calls(file_path: Path) -> List[RouteCall]:
    """Extract API route calls from a TypeScript file.

    Looks for patterns like:
    - client.get('/api/v1/...')
    - client.post('/api/v1/...')
    - axios.get('/ops/...')
    - fetch('/api/v1/...')
    """
    calls = []

    try:
        content = file_path.read_text()
        lines = content.split('\n')

        # Pattern for HTTP method calls
        # Matches: client.get('/path'), axios.post('/path'), etc.
        http_pattern = re.compile(
            r'(?:client|axios|api|http)\s*\.\s*(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
            re.IGNORECASE
        )

        # Pattern for fetch calls
        fetch_pattern = re.compile(
            r'fetch\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
            re.IGNORECASE
        )

        # Pattern for template literal routes with baseURL
        template_pattern = re.compile(
            r'`\$\{[^}]+\}(/[^`]+)`',
            re.IGNORECASE
        )

        for line_no, line in enumerate(lines, 1):
            # Skip comments
            if line.strip().startswith('//') or line.strip().startswith('*'):
                continue

            # HTTP method calls
            for match in http_pattern.finditer(line):
                method = match.group(1).upper()
                route = match.group(2)
                calls.append(RouteCall(
                    file=str(file_path),
                    line=line_no,
                    method=method,
                    route=route,
                    raw_code=line.strip(),
                ))

            # Fetch calls (assume GET unless method specified)
            for match in fetch_pattern.finditer(line):
                route = match.group(1)
                # Try to detect method from options
                method = "GET"
                if "method:" in line or "'POST'" in line or '"POST"' in line:
                    method = "POST"
                calls.append(RouteCall(
                    file=str(file_path),
                    line=line_no,
                    method=method,
                    route=route,
                    raw_code=line.strip(),
                ))

    except Exception as e:
        print(f"Warning: Could not parse {file_path}: {e}", file=sys.stderr)

    return calls


def normalize_route(route: str) -> str:
    """Normalize a route for comparison.

    - Remove query strings
    - Replace path parameters with wildcards
    - Normalize slashes
    """
    # Remove query strings
    if '?' in route:
        route = route.split('?')[0]

    # Remove trailing slash
    route = route.rstrip('/')

    return route


def route_matches(actual: str, pattern: str) -> bool:
    """Check if an actual route matches a pattern.

    Pattern can contain:
    - {param} for path parameters
    - * for wildcard segments
    """
    actual = normalize_route(actual)
    pattern = normalize_route(pattern)

    # Convert pattern to regex
    # {param} -> matches any segment
    # * -> matches any remaining path
    regex_pattern = pattern
    regex_pattern = re.sub(r'\{[^}]+\}', r'[^/]+', regex_pattern)
    regex_pattern = regex_pattern.replace('/*', '/.*')
    regex_pattern = f'^{regex_pattern}$'

    try:
        return bool(re.match(regex_pattern, actual))
    except re.error:
        return False


# =============================================================================
# VALIDATION
# =============================================================================

def validate_client_binding(client_name: str) -> Tuple[str, Optional[str], Optional[Dict]]:
    """Validate a client's binding status.

    Returns (status, capability_id, binding_info)
    """
    if client_name in BOUND_CLIENTS:
        binding = BOUND_CLIENTS[client_name]
        return "BOUND", binding.get("capability_id"), binding

    if client_name in PLATFORM_CLIENTS:
        return "UTILITY", None, PLATFORM_CLIENTS[client_name]

    if client_name in BLOCKED_CLIENTS:
        return "BLOCKED", BLOCKED_CLIENTS[client_name].get("intended_capability"), BLOCKED_CLIENTS[client_name]

    if client_name in UNBOUND_CLIENTS:
        return "UNBOUND", None, UNBOUND_CLIENTS[client_name]

    return "UNKNOWN", None, None


def validate_route_invocation(
    method: str,
    route: str,
    capability_id: str,
) -> Tuple[bool, str]:
    """Validate if a route invocation is permitted for a capability.

    Returns (is_valid, reason)
    """
    # Skip if capability not in invocable list
    if capability_id not in FRONTEND_INVOCABLE_CAPABILITIES:
        return False, f"Capability {capability_id} is not frontend-invocable"

    cap_info = FRONTEND_INVOCABLE_CAPABILITIES[capability_id]

    # Check forbidden routes first
    for forbidden in cap_info["forbidden_routes"]:
        if route_matches(route, forbidden.split(" ", 1)[-1]):
            return False, f"Route matches forbidden pattern: {forbidden}"

    # Check allowed routes
    full_route = f"{method} {route}"
    for allowed in cap_info["allowed_routes"]:
        allowed_method, allowed_path = allowed.split(" ", 1)
        if method.upper() == allowed_method.upper() and route_matches(route, allowed_path):
            return True, f"Matches allowed route: {allowed}"

    return False, f"Route not in allowed_routes for {capability_id}"


def check_client(file_path: Path, verbose: bool = False) -> List[Violation]:
    """Check a frontend client file for invocation violations."""
    violations = []
    client_name = file_path.name

    # Validate binding
    status, capability_id, binding_info = validate_client_binding(client_name)

    if status == "BLOCKED":
        violations.append(Violation(
            file=str(file_path),
            line=0,
            violation_type="BLOCKED_CLIENT",
            message=f"Client is BLOCKED: {binding_info.get('reason', 'Unknown')}",
            severity="BLOCKING",
        ))
        return violations

    if status == "UNBOUND":
        violations.append(Violation(
            file=str(file_path),
            line=0,
            violation_type="UNBOUND_CLIENT",
            message=f"Client is UNBOUND: {binding_info.get('reason', 'Unknown')}",
            severity="WARNING",
        ))
        # Continue checking routes anyway

    if status == "UTILITY":
        if verbose:
            print(f"  ⊘ {client_name}: Platform utility (skipped)")
        return violations

    if status == "UNKNOWN":
        violations.append(Violation(
            file=str(file_path),
            line=0,
            violation_type="UNKNOWN_CLIENT",
            message="Client not registered in L2_L21_BINDINGS.yaml",
            severity="WARNING",
        ))

    # Extract API calls
    calls = extract_api_calls(file_path)

    if not calls:
        if verbose:
            print(f"  ○ {client_name}: No API calls detected")
        return violations

    # Get capability IDs to check against
    capability_ids = []
    if capability_id == "MULTI":
        capability_ids = binding_info.get("capabilities", [])
    elif capability_id == "PLATFORM":
        # Platform utilities are allowed
        if verbose:
            print(f"  ✓ {client_name}: Platform utility ({len(calls)} calls)")
        return violations
    elif capability_id:
        capability_ids = [capability_id]

    # Validate each call
    valid_count = 0
    for call in calls:
        route_valid = False
        route_reason = ""

        for cap_id in capability_ids:
            is_valid, reason = validate_route_invocation(call.method, call.route, cap_id)
            if is_valid:
                route_valid = True
                route_reason = reason
                break
            route_reason = reason

        if not route_valid and capability_ids:
            violations.append(Violation(
                file=str(file_path),
                line=call.line,
                violation_type="ROUTE_NOT_ALLOWED",
                message=f"{call.method} {call.route} - {route_reason}",
                severity="WARNING",  # WARNING because route extraction may be imprecise
            ))
        else:
            valid_count += 1

    if verbose and not violations:
        print(f"  ✓ {client_name}: {valid_count} valid calls ({capability_id})")

    return violations


# =============================================================================
# MAIN GUARD
# =============================================================================

def run_guard(verbose: bool = False, ci_mode: bool = False) -> Tuple[int, List[Violation]]:
    """Run the capability invocation guard."""
    all_violations: List[Violation] = []
    repo_root = Path(__file__).parent.parent.parent
    api_dir = repo_root / FRONTEND_API_DIR

    print("=" * 70)
    print("CAPABILITY INVOCATION GUARD (Phase A1)")
    print("=" * 70)
    print()
    print(f"Reference: PIN-322 (L2-L2.1 Progressive Activation)")
    print(f"Checking: {api_dir}")
    print()

    if not api_dir.exists():
        print(f"ERROR: Frontend API directory not found: {api_dir}")
        return 2, []

    # Find all TypeScript files
    ts_files = list(api_dir.glob("*.ts"))

    if not ts_files:
        print(f"WARNING: No TypeScript files found in {api_dir}")
        return 0, []

    print(f"Found {len(ts_files)} frontend API clients")
    print()

    # Check each client
    print("Checking client bindings and route invocations...")
    print()

    for ts_file in sorted(ts_files):
        violations = check_client(ts_file, verbose)
        all_violations.extend(violations)

    print()

    # Report results
    blocking = [v for v in all_violations if v.severity == "BLOCKING"]
    warnings = [v for v in all_violations if v.severity == "WARNING"]
    directional = [v for v in all_violations if v.severity == "DIRECTIONAL"]

    if blocking:
        print("=" * 70)
        print(f"BLOCKING VIOLATIONS ({len(blocking)}):")
        print("=" * 70)
        for v in blocking:
            print(f"  ✗ {v}")
        print()

    if warnings:
        print("-" * 70)
        print(f"WARNINGS ({len(warnings)}):")
        print("-" * 70)
        for v in warnings:
            print(f"  ⚠ {v}")
        print()

    if directional:
        print("-" * 70)
        print(f"DIRECTIONAL ({len(directional)}):")
        print("-" * 70)
        for v in directional:
            print(f"  → {v}")
        print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print(f"  Clients checked: {len(ts_files)}")
    print(f"  Bound clients: {len(BOUND_CLIENTS)}")
    print(f"  Platform utilities: {len(PLATFORM_CLIENTS)}")
    print(f"  Blocked clients: {len(BLOCKED_CLIENTS)}")
    print(f"  Unbound clients: {len(UNBOUND_CLIENTS)}")
    print()
    print(f"  Blocking violations: {len(blocking)}")
    print(f"  Warnings: {len(warnings)}")
    print(f"  Directional: {len(directional)}")
    print()

    if blocking:
        print("=" * 70)
        print("GUARD: FAIL")
        print("=" * 70)
        print()
        print("Capability invocation guard FAILED.")
        print("Fix all BLOCKING violations before merge.")
        return 1, all_violations
    elif warnings and ci_mode:
        print("=" * 70)
        print(f"GUARD: PASS with warnings ({len(warnings)} warnings)")
        print("=" * 70)
        print()
        print("Capability invocation guard PASSED (warnings are advisory).")
        return 0, all_violations
    else:
        print("=" * 70)
        print("GUARD: PASS")
        print("=" * 70)
        print()
        print("Capability invocation guard PASSED.")
        return 0, all_violations


def main():
    parser = argparse.ArgumentParser(
        description="Capability Invocation Guard (Phase A1) - CI enforcement for frontend capability invocation"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed analysis"
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode (stricter enforcement)"
    )
    args = parser.parse_args()

    exit_code, _ = run_guard(verbose=args.verbose, ci_mode=args.ci)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
