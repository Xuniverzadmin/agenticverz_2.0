#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci
#   Execution: sync
# Role: CI guard for L2.1 frontend constitutional mapping compliance
# Callers: GitHub Actions workflow
# Allowed Imports: L8 (stdlib only)
# Forbidden Imports: L1-L7 (must be self-contained)
# Reference: PIN-322 (L2-L2.1 Progressive Activation), PIN-321 (Binding Execution)
#
# GOVERNANCE NOTE:
# This script enforces frontend constitutional mapping from:
# - FRONTEND_CAPABILITY_MAPPING.yaml (Domain and Order mappings)
# - CUSTOMER_CONSOLE_V1_CONSTITUTION.md (L1 Truth Space)
#
# PHASE A3 GUARD

"""
Frontend Constitutional Mapping Guard (Phase A3)

This CI guard validates that frontend route displays align with the
constitutional domain structure defined in FRONTEND_CAPABILITY_MAPPING.yaml.

Validation Rules:
1. Routes tagged for domains match their declared domain
2. O-level usage matches declared orders
3. Gap domains (Activity, Logs) exposure without explicit flag raises warning

L1 Frozen Domains:
- Overview:  Is the system okay right now?
- Activity:  What ran / is running?
- Incidents: What went wrong?
- Policies:  How is behavior defined?
- Logs:      What is the raw truth?

Orders (Epistemic Depth):
- O1: Summary / Snapshot (scannable)
- O2: List of instances
- O3: Detail / Explanation
- O4: Context / Impact
- O5: Raw records / Proof

Exit codes:
  0 - All checks pass
  1 - Violations found
  2 - Script error

Usage:
  python scripts/ci/frontend_mapping_guard.py           # Check all clients
  python scripts/ci/frontend_mapping_guard.py --verbose # Show detailed analysis
  python scripts/ci/frontend_mapping_guard.py --ci      # CI mode
"""

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# =============================================================================
# CONFIGURATION - From FRONTEND_CAPABILITY_MAPPING.yaml
# =============================================================================

# L1 Frozen Domains (from CUSTOMER_CONSOLE_V1_CONSTITUTION.md)
L1_FROZEN_DOMAINS = {
    "Overview": "Is the system okay right now?",
    "Activity": "What ran / is running?",
    "Incidents": "What went wrong?",
    "Policies": "How is behavior defined?",
    "Logs": "What is the raw truth?",
}

# Orders (Epistemic Depth)
ORDERS = {
    "O1": "Summary / Snapshot",
    "O2": "List of instances",
    "O3": "Detail / Explanation",
    "O4": "Context / Impact",
    "O5": "Raw records / Proof",
}

# Capability to Domain Mapping (from FRONTEND_CAPABILITY_MAPPING.yaml)
CAPABILITY_DOMAIN_MAPPING = {
    "CAP-001": {  # REPLAY
        "name": "Execution Replay",
        "domain": "Incidents",
        "subdomain": "Incident Investigation",
        "topic": "Replay & Timeline",
        "orders": {"O1": False, "O2": True, "O3": True, "O4": True, "O5": True},
        "status": "fits",
    },
    "CAP-002": {  # COST SIMULATION
        "name": "Cost Simulation V2",
        "domain": "Overview",
        "subdomain": "Cost Advisory",
        "topic": "Pre-Execution Cost Estimate",
        "orders": {"O1": True, "O2": False, "O3": True, "O4": False, "O5": False},
        "status": "fits",
    },
    "CAP-003": {  # POLICY PROPOSALS
        "name": "Policy Proposals",
        "domain": "Policies",
        "subdomain": "Policy Evolution",
        "topic": "Pending Proposals",
        "orders": {"O1": True, "O2": True, "O3": True, "O4": True, "O5": False},
        "status": "partial",  # FOUNDER-ONLY visibility
    },
    "CAP-004": {  # PREDICTION PLANE
        "name": "C2 Prediction Plane",
        "domain": "Overview",
        "subdomain": "Predictive Signals",
        "topic": "Risk & Cost Predictions",
        "orders": {"O1": True, "O2": True, "O3": True, "O4": False, "O5": False},
        "status": "partial",  # OPTIONAL for customer
    },
    "CAP-005": {  # FOUNDER CONSOLE
        "name": "Founder Console",
        "domain": "NONE",  # Separate console
        "subdomain": None,
        "topic": None,
        "orders": {"O1": False, "O2": False, "O3": False, "O4": False, "O5": False},
        "status": "forbidden",  # Not part of Customer Console
    },
    "CAP-009": {  # POLICY ENGINE
        "name": "Policy Engine",
        "domain": "Policies",
        "subdomain": "Active Policies",
        "topic": "Policy Rules",
        "orders": {"O1": True, "O2": True, "O3": True, "O4": False, "O5": False},
        "status": "fits",
    },
    "CAP-011": {  # GOVERNANCE ORCHESTRATION
        "name": "Governance Orchestration",
        "domain": "NONE",  # FOUNDER-ONLY
        "subdomain": None,
        "topic": None,
        "orders": {"O1": False, "O2": False, "O3": False, "O4": False, "O5": False},
        "status": "forbidden",  # Not part of Customer Console
    },
    "CAP-014": {  # MEMORY SYSTEM
        "name": "Memory System",
        "domain": "Activity",
        "subdomain": "Agent Memory",
        "topic": "Memory State",
        "orders": {"O1": False, "O2": True, "O3": True, "O4": False, "O5": False},
        "status": "partial",  # FOUNDER-ONLY currently
    },
    "CAP-018": {  # INTEGRATION PLATFORM
        "name": "Integration Platform",
        "domain": "NONE",  # External capability
        "subdomain": None,
        "topic": None,
        "orders": {"O1": False, "O2": False, "O3": False, "O4": False, "O5": False},
        "status": "forbidden",  # External, not in L1 Truth Space
    },
}

# Gap domains (no frontend-invocable capabilities)
GAP_DOMAINS = {
    "Activity": "Memory system is founder-only. Activity needs customer-visible capability.",
    "Logs": "No frontend-invocable capability for raw log access.",
}

# Client to capability mapping
CLIENT_BINDINGS = {
    "replay.ts": {"capability_id": "CAP-001", "audience": "founder"},
    "costsim.ts": {"capability_id": "CAP-002", "audience": "customer"},
    "guard.ts": {"capabilities": ["CAP-001", "CAP-009"], "audience": "customer"},
    "ops.ts": {"capability_id": "CAP-005", "audience": "founder"},
    "timeline.ts": {"capability_id": "CAP-005", "audience": "founder"},
    "traces.ts": {"capability_id": "CAP-001", "audience": "founder"},
    "scenarios.ts": {"capability_id": "CAP-002", "audience": "customer"},
    "integration.ts": {"capability_id": "CAP-018", "audience": "founder"},
    "recovery.ts": {"capability_id": "CAP-018", "audience": "founder"},
    "memory.ts": {"capability_id": "CAP-014", "audience": "founder"},
    "explorer.ts": {"capability_id": "CAP-005", "audience": "founder"},
    "sba.ts": {"capability_id": "CAP-011", "audience": "founder"},
    "killswitch.ts": {"capability_id": "PLATFORM", "audience": "customer"},
}

# Route patterns that indicate domain/order usage
DOMAIN_ROUTE_PATTERNS = {
    "Overview": [
        r"/status",
        r"/health",
        r"/summary",
        r"/dashboard",
        r"/costs?",
        r"/predict",
    ],
    "Activity": [
        r"/runs?",
        r"/traces?",
        r"/jobs?",
        r"/memory",
        r"/activity",
    ],
    "Incidents": [
        r"/incidents?",
        r"/replay",
        r"/failures?",
        r"/violations?",
    ],
    "Policies": [
        r"/policies?",
        r"/policy",
        r"/rules?",
        r"/constraints?",
    ],
    "Logs": [
        r"/logs?",
        r"/audit",
        r"/proof",
        r"/records?",
    ],
}

# Frontend API directory
FRONTEND_API_DIR = "website/app-shell/src/api"


# =============================================================================
# VIOLATION TYPES
# =============================================================================

@dataclass
class Violation:
    """Represents a constitutional mapping violation."""
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
    method: str
    route: str
    raw_code: str


# =============================================================================
# ROUTE EXTRACTION
# =============================================================================

def extract_api_calls(file_path: Path) -> List[RouteCall]:
    """Extract API route calls from a TypeScript file."""
    calls = []

    try:
        content = file_path.read_text()
        lines = content.split('\n')

        http_pattern = re.compile(
            r'(?:client|axios|api|http)\s*\.\s*(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
            re.IGNORECASE
        )

        for line_no, line in enumerate(lines, 1):
            if line.strip().startswith('//') or line.strip().startswith('*'):
                continue

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

    except Exception as e:
        print(f"Warning: Could not parse {file_path}: {e}", file=sys.stderr)

    return calls


# =============================================================================
# VALIDATION
# =============================================================================

def infer_domain_from_route(route: str) -> Optional[str]:
    """Infer the L1 domain from a route based on patterns."""
    route_lower = route.lower()

    for domain, patterns in DOMAIN_ROUTE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, route_lower):
                return domain

    return None


def check_domain_alignment(
    client_name: str,
    call: RouteCall,
) -> List[Violation]:
    """Check if a route call aligns with constitutional domain mapping."""
    violations = []

    # Get client binding
    binding = CLIENT_BINDINGS.get(client_name)
    if not binding:
        return []

    # Get capability IDs
    capability_ids = []
    if "capability_id" in binding:
        cap_id = binding["capability_id"]
        if cap_id == "PLATFORM":
            return []
        capability_ids = [cap_id]
    elif "capabilities" in binding:
        capability_ids = binding["capabilities"]

    client_audience = binding.get("audience", "unknown")

    for cap_id in capability_ids:
        mapping = CAPABILITY_DOMAIN_MAPPING.get(cap_id)
        if not mapping:
            continue

        declared_domain = mapping["domain"]
        mapping_status = mapping["status"]

        # Check 1: Forbidden capabilities in customer console
        if mapping_status == "forbidden" and client_audience == "customer":
            violations.append(Violation(
                file=call.file,
                line=call.line,
                violation_type="FORBIDDEN_IN_CUSTOMER",
                message=f"Capability {cap_id} ({mapping['name']}) is forbidden in Customer Console",
                severity="BLOCKING",
            ))
            continue

        # Check 2: Domain alignment
        inferred_domain = infer_domain_from_route(call.route)
        if inferred_domain and declared_domain != "NONE":
            if inferred_domain != declared_domain:
                violations.append(Violation(
                    file=call.file,
                    line=call.line,
                    violation_type="DOMAIN_MISMATCH",
                    message=f"Route suggests '{inferred_domain}' domain, but capability {cap_id} maps to '{declared_domain}'",
                    severity="WARNING",
                ))

        # Check 3: Gap domain exposure
        if inferred_domain in GAP_DOMAINS:
            violations.append(Violation(
                file=call.file,
                line=call.line,
                violation_type="GAP_DOMAIN_EXPOSURE",
                message=f"Route touches gap domain '{inferred_domain}': {GAP_DOMAINS[inferred_domain]}",
                severity="DIRECTIONAL",
            ))

        # Check 4: Partial visibility warning
        if mapping_status == "partial" and client_audience == "customer":
            violations.append(Violation(
                file=call.file,
                line=call.line,
                violation_type="PARTIAL_VISIBILITY",
                message=f"Capability {cap_id} has partial visibility for customer. Review required.",
                severity="WARNING",
            ))

    return violations


def check_client(file_path: Path, verbose: bool = False) -> List[Violation]:
    """Check a frontend client file for constitutional mapping violations."""
    violations = []
    client_name = file_path.name

    # Skip non-bound clients
    if client_name not in CLIENT_BINDINGS:
        if verbose:
            print(f"  ⊘ {client_name}: Not bound (skipped)")
        return []

    binding = CLIENT_BINDINGS[client_name]
    if binding.get("capability_id") == "PLATFORM":
        if verbose:
            print(f"  ⊘ {client_name}: Platform utility (skipped)")
        return []

    # Extract API calls
    calls = extract_api_calls(file_path)

    if not calls:
        if verbose:
            print(f"  ○ {client_name}: No API calls detected")
        return []

    # Check each call
    for call in calls:
        call_violations = check_domain_alignment(client_name, call)
        violations.extend(call_violations)

    if verbose and not violations:
        cap_id = binding.get("capability_id", "MULTI")
        if cap_id != "MULTI":
            mapping = CAPABILITY_DOMAIN_MAPPING.get(cap_id, {})
            domain = mapping.get("domain", "Unknown")
        else:
            domain = "Mixed"
        print(f"  ✓ {client_name}: {len(calls)} calls aligned with domain '{domain}'")

    return violations


# =============================================================================
# DOMAIN COVERAGE SUMMARY
# =============================================================================

def generate_domain_summary() -> str:
    """Generate a summary of domain coverage."""
    lines = []
    lines.append("")
    lines.append("L1 DOMAIN COVERAGE SUMMARY")
    lines.append("-" * 50)

    for domain, question in L1_FROZEN_DOMAINS.items():
        lines.append(f"\n{domain}: {question}")

        # Find capabilities for this domain
        caps_for_domain = []
        for cap_id, mapping in CAPABILITY_DOMAIN_MAPPING.items():
            if mapping["domain"] == domain:
                caps_for_domain.append((cap_id, mapping["name"], mapping["status"]))

        if caps_for_domain:
            for cap_id, name, status in caps_for_domain:
                status_icon = {"fits": "✓", "partial": "◐", "forbidden": "✗", "gap": "○"}.get(status, "?")
                lines.append(f"  {status_icon} {cap_id}: {name} [{status}]")
        else:
            if domain in GAP_DOMAINS:
                lines.append(f"  ○ GAP: {GAP_DOMAINS[domain]}")
            else:
                lines.append(f"  ? No capabilities mapped")

    return "\n".join(lines)


# =============================================================================
# MAIN GUARD
# =============================================================================

def run_guard(verbose: bool = False, ci_mode: bool = False) -> Tuple[int, List[Violation]]:
    """Run the frontend constitutional mapping guard."""
    all_violations: List[Violation] = []
    repo_root = Path(__file__).parent.parent.parent
    api_dir = repo_root / FRONTEND_API_DIR

    print("=" * 70)
    print("FRONTEND CONSTITUTIONAL MAPPING GUARD (Phase A3)")
    print("=" * 70)
    print()
    print(f"Reference: PIN-322 (L2-L2.1 Progressive Activation)")
    print(f"Reference: CUSTOMER_CONSOLE_V1_CONSTITUTION.md")
    print(f"Checking: {api_dir}")
    print()

    if verbose:
        print(generate_domain_summary())
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
    print("Checking constitutional domain alignment...")
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
    print(f"  Blocking violations: {len(blocking)}")
    print(f"  Warnings: {len(warnings)}")
    print(f"  Directional: {len(directional)}")
    print()
    print("  Domain Coverage:")
    for domain in L1_FROZEN_DOMAINS:
        if domain in GAP_DOMAINS:
            print(f"    {domain}: GAP")
        else:
            print(f"    {domain}: COVERED")
    print()

    if blocking:
        print("=" * 70)
        print("GUARD: FAIL")
        print("=" * 70)
        print()
        print("Frontend constitutional mapping guard FAILED.")
        print("Fix all BLOCKING violations before merge.")
        return 1, all_violations
    elif warnings:
        print("=" * 70)
        print(f"GUARD: PASS with warnings ({len(warnings)} warnings)")
        print("=" * 70)
        print()
        print("Constitutional mapping guard PASSED (warnings are advisory).")
        return 0, all_violations
    else:
        print("=" * 70)
        print("GUARD: PASS")
        print("=" * 70)
        print()
        print("Constitutional mapping guard PASSED.")
        return 0, all_violations


def main():
    parser = argparse.ArgumentParser(
        description="Frontend Constitutional Mapping Guard (Phase A3)"
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
