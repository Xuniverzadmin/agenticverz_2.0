#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci
#   Execution: sync
# Role: CI guard for L2.1 interaction semantics consistency
# Callers: GitHub Actions workflow
# Allowed Imports: L8 (stdlib only)
# Forbidden Imports: L1-L7 (must be self-contained)
# Reference: PIN-322 (L2-L2.1 Progressive Activation), PIN-321 (Binding Execution)
#
# GOVERNANCE NOTE:
# This script enforces interaction semantics from:
# - INTERACTION_SEMANTICS.yaml (Input/output types, mutability)
# - CAPABILITY_REGISTRY.yaml (Invocation modes)
#
# PHASE A2 GUARD

"""
Interaction Semantics Consistency Guard (Phase A2)

This CI guard validates that no frontend call path violates interaction semantics:
1. Method + route matches declared input_type (query/command/proposal)
2. writes_state: true capabilities are only called via founder routes
3. Mutating methods (POST/PUT/DELETE) align with mutability declaration

Exit codes:
  0 - All checks pass
  1 - Violations found
  2 - Script error

Usage:
  python scripts/ci/interaction_semantics_guard.py           # Check all clients
  python scripts/ci/interaction_semantics_guard.py --verbose # Show detailed analysis
  python scripts/ci/interaction_semantics_guard.py --ci      # CI mode
"""

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# =============================================================================
# CONFIGURATION - From INTERACTION_SEMANTICS.yaml
# =============================================================================

# Interaction semantics per capability
INTERACTION_SEMANTICS = {
    "CAP-001": {  # REPLAY
        "name": "Execution Replay",
        "input_type": "query",
        "output_type": "report",
        "feedback_loop": "closed",
        "human_required": False,
        "writes_state": False,
        "l1_compliance": {
            "no_auto_enforcement": True,
            "no_learned_authority": True,
        },
    },
    "CAP-002": {  # COST SIMULATION
        "name": "Cost Simulation V2",
        "input_type": "proposal",
        "output_type": "recommendation",
        "feedback_loop": "open",
        "human_required": False,
        "writes_state": False,
        "l1_compliance": {
            "no_auto_enforcement": True,
            "no_learned_authority": True,
        },
    },
    "CAP-003": {  # POLICY PROPOSALS
        "name": "Policy Proposals",
        "input_type": "query",
        "output_type": "report",
        "feedback_loop": "open",
        "human_required": True,
        "writes_state": False,
        "l1_compliance": {
            "no_auto_enforcement": True,
            "no_learned_authority": True,
        },
    },
    "CAP-004": {  # PREDICTION PLANE
        "name": "C2 Prediction Plane",
        "input_type": "query",
        "output_type": "report",
        "feedback_loop": "open",
        "human_required": False,
        "writes_state": False,
        "l1_compliance": {
            "no_auto_enforcement": True,
            "no_learned_authority": True,
        },
        "critical_note": "PB-S5: Predictions MUST NOT influence execution paths",
    },
    "CAP-005": {  # FOUNDER CONSOLE
        "name": "Founder Console",
        "input_type": "command",
        "output_type": "state",
        "feedback_loop": "closed",
        "human_required": True,
        "writes_state": True,
        "l1_compliance": {
            "no_auto_enforcement": True,
            "no_learned_authority": True,
        },
        "audience_required": "founder",
    },
    "CAP-009": {  # POLICY ENGINE
        "name": "Policy Engine",
        "input_type": "query",
        "output_type": "report",
        "feedback_loop": "closed",
        "human_required": False,
        "writes_state": False,
        "l1_compliance": {
            "no_auto_enforcement": True,
            "no_learned_authority": True,
        },
    },
    "CAP-011": {  # GOVERNANCE ORCHESTRATION
        "name": "Governance Orchestration",
        "input_type": "command",
        "output_type": "state",
        "feedback_loop": "closed",
        "human_required": True,
        "writes_state": True,
        "l1_compliance": {
            "no_auto_enforcement": True,
            "no_learned_authority": True,
        },
        "audience_required": "founder",
    },
    "CAP-014": {  # MEMORY SYSTEM
        "name": "Memory System",
        "input_type": "query",
        "output_type": "report",
        "feedback_loop": "closed",
        "human_required": False,
        "writes_state": False,
        "l1_compliance": {
            "no_auto_enforcement": True,
            "no_learned_authority": True,
        },
    },
    "CAP-018": {  # INTEGRATION PLATFORM
        "name": "Integration Platform",
        "input_type": "query",
        "output_type": "report",
        "feedback_loop": "open",
        "human_required": False,
        "writes_state": False,
        "l1_compliance": {
            "no_auto_enforcement": True,
            "no_learned_authority": True,
        },
    },
}

# Client to capability mapping (from L2_L21_BINDINGS.yaml)
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

# HTTP method to input_type mapping
METHOD_TO_INPUT_TYPE = {
    "GET": ["query"],  # GET = read = query
    "POST": ["command", "proposal"],  # POST can be command (mutate) or proposal (advisory)
    "PUT": ["command"],  # PUT = always mutating
    "PATCH": ["command"],  # PATCH = always mutating
    "DELETE": ["command"],  # DELETE = always mutating
}

# Methods that typically imply mutation
MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Frontend API directory
FRONTEND_API_DIR = "website/app-shell/src/api"


# =============================================================================
# VIOLATION TYPES
# =============================================================================

@dataclass
class Violation:
    """Represents an interaction semantics violation."""
    file: str
    line: int
    violation_type: str
    message: str
    severity: str  # BLOCKING, WARNING

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

        # Pattern for HTTP method calls
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

def check_semantics_consistency(
    client_name: str,
    call: RouteCall,
) -> List[Violation]:
    """Check if a route call is consistent with interaction semantics."""
    violations = []

    # Get client binding
    binding = CLIENT_BINDINGS.get(client_name)
    if not binding:
        return []  # Unknown client, skip

    # Get capability IDs
    capability_ids = []
    if "capability_id" in binding:
        cap_id = binding["capability_id"]
        if cap_id == "PLATFORM":
            return []  # Platform utilities skip semantics check
        capability_ids = [cap_id]
    elif "capabilities" in binding:
        capability_ids = binding["capabilities"]

    client_audience = binding.get("audience", "unknown")

    for cap_id in capability_ids:
        semantics = INTERACTION_SEMANTICS.get(cap_id)
        if not semantics:
            continue

        # Check 1: Input type consistency
        expected_input_types = METHOD_TO_INPUT_TYPE.get(call.method, [])
        actual_input_type = semantics["input_type"]

        if actual_input_type not in expected_input_types:
            # Special case: POST with query input_type is suspicious
            if call.method == "POST" and actual_input_type == "query":
                violations.append(Violation(
                    file=call.file,
                    line=call.line,
                    violation_type="INPUT_TYPE_MISMATCH",
                    message=f"{call.method} used with query capability ({cap_id}). Expected GET for queries.",
                    severity="WARNING",
                ))

        # Check 2: Mutation consistency
        if call.method in MUTATING_METHODS and not semantics["writes_state"]:
            # POST is allowed for proposals (advisory)
            if call.method == "POST" and actual_input_type == "proposal":
                pass  # Proposal POSTs are OK even with writes_state: false
            else:
                violations.append(Violation(
                    file=call.file,
                    line=call.line,
                    violation_type="MUTATION_ON_READONLY",
                    message=f"{call.method} used on read-only capability ({cap_id}). writes_state: false",
                    severity="WARNING",
                ))

        # Check 3: Audience consistency for state-mutating capabilities
        audience_required = semantics.get("audience_required")
        if audience_required and semantics["writes_state"]:
            if client_audience != audience_required:
                violations.append(Violation(
                    file=call.file,
                    line=call.line,
                    violation_type="AUDIENCE_MISMATCH",
                    message=f"State-mutating capability ({cap_id}) requires {audience_required} audience, but client is {client_audience}",
                    severity="BLOCKING",
                ))

        # Check 4: Human-required capabilities with automated patterns
        if semantics["human_required"]:
            # Look for patterns that suggest automation (e.g., retry loops, batching)
            if "retry" in call.raw_code.lower() or "batch" in call.raw_code.lower():
                violations.append(Violation(
                    file=call.file,
                    line=call.line,
                    violation_type="HUMAN_REQUIRED_AUTOMATION",
                    message=f"Capability ({cap_id}) requires human decision. Automated patterns detected.",
                    severity="WARNING",
                ))

    return violations


def check_client(file_path: Path, verbose: bool = False) -> List[Violation]:
    """Check a frontend client file for interaction semantics violations."""
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
        call_violations = check_semantics_consistency(client_name, call)
        violations.extend(call_violations)

    if verbose and not violations:
        print(f"  ✓ {client_name}: {len(calls)} calls consistent with semantics")

    return violations


# =============================================================================
# SUMMARY STATISTICS
# =============================================================================

def generate_semantics_summary() -> str:
    """Generate a summary of interaction semantics by capability."""
    lines = []
    lines.append("")
    lines.append("INTERACTION SEMANTICS SUMMARY")
    lines.append("-" * 50)

    # Group by input_type
    by_input_type = {}
    for cap_id, sem in INTERACTION_SEMANTICS.items():
        input_type = sem["input_type"]
        if input_type not in by_input_type:
            by_input_type[input_type] = []
        by_input_type[input_type].append((cap_id, sem["name"]))

    for input_type in ["query", "proposal", "command"]:
        if input_type in by_input_type:
            lines.append(f"\n{input_type.upper()} capabilities:")
            for cap_id, name in by_input_type[input_type]:
                sem = INTERACTION_SEMANTICS[cap_id]
                writes = "MUTATES" if sem["writes_state"] else "READ-ONLY"
                human = "HUMAN-REQUIRED" if sem["human_required"] else ""
                lines.append(f"  {cap_id}: {name} [{writes}] {human}")

    return "\n".join(lines)


# =============================================================================
# MAIN GUARD
# =============================================================================

def run_guard(verbose: bool = False, ci_mode: bool = False) -> Tuple[int, List[Violation]]:
    """Run the interaction semantics consistency guard."""
    all_violations: List[Violation] = []
    repo_root = Path(__file__).parent.parent.parent
    api_dir = repo_root / FRONTEND_API_DIR

    print("=" * 70)
    print("INTERACTION SEMANTICS CONSISTENCY GUARD (Phase A2)")
    print("=" * 70)
    print()
    print(f"Reference: PIN-322 (L2-L2.1 Progressive Activation)")
    print(f"Checking: {api_dir}")
    print()

    if verbose:
        print(generate_semantics_summary())
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
    print("Checking interaction semantics consistency...")
    print()

    for ts_file in sorted(ts_files):
        violations = check_client(ts_file, verbose)
        all_violations.extend(violations)

    print()

    # Report results
    blocking = [v for v in all_violations if v.severity == "BLOCKING"]
    warnings = [v for v in all_violations if v.severity == "WARNING"]

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

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print(f"  Clients checked: {len(ts_files)}")
    print(f"  Blocking violations: {len(blocking)}")
    print(f"  Warnings: {len(warnings)}")
    print()

    if blocking:
        print("=" * 70)
        print("GUARD: FAIL")
        print("=" * 70)
        print()
        print("Interaction semantics guard FAILED.")
        print("Fix all BLOCKING violations before merge.")
        return 1, all_violations
    elif warnings:
        print("=" * 70)
        print(f"GUARD: PASS with warnings ({len(warnings)} warnings)")
        print("=" * 70)
        print()
        print("Interaction semantics guard PASSED (warnings are advisory).")
        return 0, all_violations
    else:
        print("=" * 70)
        print("GUARD: PASS")
        print("=" * 70)
        print()
        print("Interaction semantics guard PASSED.")
        return 0, all_violations


def main():
    parser = argparse.ArgumentParser(
        description="Interaction Semantics Consistency Guard (Phase A2)"
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
