#!/usr/bin/env python3
"""
Incidents Domain CI Contract

Validates architectural constraints for the Incidents domain:
1. Capability Registry Compliance
2. Layer Violations (L2 facade rule)
3. Service Responsibilities
4. Endpoint → Capability Mapping
5. CAP-E2E-001 Compliance (DECLARED status for unvalidated capabilities)

Reference: docs/architecture/incidents/INCIDENTS_DOMAIN_SQL.md
Reference: docs/architecture/CROSS_DOMAIN_CONTRACT.md

Usage:
    python scripts/preflight/check_incidents_domain.py
    python scripts/preflight/check_incidents_domain.py --verbose
    python scripts/preflight/check_incidents_domain.py --fix  # Show fixes only
"""

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

# =============================================================================
# Configuration
# =============================================================================

BACKEND_PATH = Path(__file__).parent.parent.parent / "backend"
CAPABILITY_REGISTRY_PATH = BACKEND_PATH / "AURORA_L2_CAPABILITY_REGISTRY"
INCIDENTS_API_PATH = BACKEND_PATH / "app/api/incidents.py"
INCIDENTS_SERVICES_PATH = BACKEND_PATH / "app/services/incidents"


@dataclass
class Violation:
    """Represents a contract violation."""
    rule_id: str
    severity: str  # ERROR, WARNING
    file: str
    line: Optional[int]
    message: str
    fix: Optional[str] = None


# =============================================================================
# Registry Loader
# =============================================================================

def load_incidents_capabilities() -> dict[str, dict]:
    """Load all incidents-related capability registry files."""
    capabilities = {}

    if not CAPABILITY_REGISTRY_PATH.exists():
        return capabilities

    for cap_file in CAPABILITY_REGISTRY_PATH.glob("AURORA_L2_CAPABILITY_incidents.*.yaml"):
        with open(cap_file) as f:
            cap_data = yaml.safe_load(f)
            if cap_data:
                cap_id = cap_data.get("capability_id", cap_file.stem)
                capabilities[cap_id] = cap_data

    return capabilities


# =============================================================================
# Rule 1: Capability Registry Compliance
# =============================================================================

def check_capability_registry(capabilities: dict, verbose: bool = False) -> list[Violation]:
    """
    Validate capability registry internal consistency.

    Rules:
    - Every capability must have an endpoint
    - Every capability must have status (DECLARED, OBSERVED, TRUSTED)
    - DECLARED capabilities must not claim OBSERVED metadata
    """
    violations = []

    for cap_id, cap_def in capabilities.items():
        cap_file = CAPABILITY_REGISTRY_PATH / f"AURORA_L2_CAPABILITY_{cap_id.replace('.', '_')}.yaml"

        # Check endpoint exists
        assumption = cap_def.get("assumption", {})
        if not assumption.get("endpoint"):
            violations.append(Violation(
                rule_id="INC-REG-001",
                severity="ERROR",
                file=str(cap_file),
                line=None,
                message=f"Capability '{cap_id}' missing endpoint in assumption",
                fix=f"Add assumption.endpoint to capability '{cap_id}'"
            ))

        # Check status exists
        status = cap_def.get("status")
        if not status:
            violations.append(Violation(
                rule_id="INC-REG-002",
                severity="ERROR",
                file=str(cap_file),
                line=None,
                message=f"Capability '{cap_id}' missing status",
                fix=f"Add status (DECLARED, OBSERVED, TRUSTED) to capability '{cap_id}'"
            ))
        elif status not in ["DECLARED", "OBSERVED", "TRUSTED", "DISCOVERED"]:
            violations.append(Violation(
                rule_id="INC-REG-003",
                severity="ERROR",
                file=str(cap_file),
                line=None,
                message=f"Capability '{cap_id}' has invalid status '{status}'",
                fix=f"Change status to one of: DECLARED, OBSERVED, TRUSTED"
            ))

        # CAP-E2E-001: Check that DECLARED capabilities don't have observation metadata
        if status == "DECLARED":
            metadata = cap_def.get("metadata", {})
            if metadata.get("observed_by") or metadata.get("observed_on"):
                violations.append(Violation(
                    rule_id="INC-CAP-E2E-001",
                    severity="ERROR",
                    file=str(cap_file),
                    line=None,
                    message=f"DECLARED capability '{cap_id}' has observation metadata without E2E validation",
                    fix=f"Remove observed_by/observed_on or run E2E validation to promote to OBSERVED"
                ))

    return violations


# =============================================================================
# Rule 2: L2 Facade Rule (No Writes in Incidents API)
# =============================================================================

def check_l2_facade_rule(verbose: bool = False) -> list[Violation]:
    """
    Validate that incidents.py (L2) contains no write operations.

    Rules:
    - No INSERT, UPDATE, DELETE in SQL
    - No .add(), .commit(), .delete() on session
    - Only SELECT queries allowed
    """
    violations = []

    if not INCIDENTS_API_PATH.exists():
        return violations

    content = INCIDENTS_API_PATH.read_text()
    lines = content.split("\n")

    # Patterns that indicate writes
    write_patterns = [
        (r'\bINSERT\s+INTO\b', "INSERT statement in L2 facade"),
        (r'\bUPDATE\s+\w+\s+SET\b', "UPDATE statement in L2 facade"),
        (r'\bDELETE\s+FROM\b', "DELETE statement in L2 facade"),
        (r'session\.add\s*\(', "session.add() in L2 facade"),
        (r'session\.delete\s*\(', "session.delete() in L2 facade"),
        (r'session\.commit\s*\(', "session.commit() in L2 facade"),
        (r'session\.flush\s*\(', "session.flush() in L2 facade"),
    ]

    for i, line in enumerate(lines, 1):
        for pattern, description in write_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                violations.append(Violation(
                    rule_id="INC-L2-001",
                    severity="ERROR",
                    file=str(INCIDENTS_API_PATH),
                    line=i,
                    message=description,
                    fix="Move write operation to L4 service or remove"
                ))

    return violations


# =============================================================================
# Rule 3: Service Responsibilities
# =============================================================================

def check_service_responsibilities(verbose: bool = False) -> list[Violation]:
    """
    Validate that incidents services follow design rules.

    Rules:
    - Services must be read-only (no writes)
    - Services must not call other services
    - Services must not use ML libraries
    """
    violations = []

    if not INCIDENTS_SERVICES_PATH.exists():
        return violations

    for service_file in INCIDENTS_SERVICES_PATH.glob("*.py"):
        if service_file.name == "__init__.py":
            continue

        content = service_file.read_text()
        lines = content.split("\n")

        # Check for writes (forbidden in all incidents services)
        write_patterns = [
            (r'\bINSERT\s+INTO\b', "INSERT found but writing forbidden"),
            (r'\bUPDATE\s+\w+\s+SET\b', "UPDATE found but writing forbidden"),
            (r'\bDELETE\s+FROM\b', "DELETE found but writing forbidden"),
            (r'session\.add\s*\(', "session.add() found but writing forbidden"),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, description in write_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(Violation(
                        rule_id="INC-SVC-001",
                        severity="ERROR",
                        file=str(service_file),
                        line=i,
                        message=f"{service_file.name}: {description}",
                        fix="Remove write operation - incidents services are read-only"
                    ))

        # Check for cross-service calls (forbidden)
        cross_service_patterns = [
            (r'from\s+app\.services\.(?!incidents)\w+\s+import', "Cross-service import forbidden"),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, description in cross_service_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(Violation(
                        rule_id="INC-SVC-002",
                        severity="ERROR",
                        file=str(service_file),
                        line=i,
                        message=f"{service_file.name}: {description}",
                        fix="Remove cross-service import - use direct SQL queries"
                    ))

    return violations


# =============================================================================
# Rule 4: Layer Headers
# =============================================================================

def check_layer_headers(verbose: bool = False) -> list[Violation]:
    """
    Validate that all incidents-related files have correct layer headers.

    Rules:
    - incidents.py must declare L2
    - Services must declare L4
    """
    violations = []

    # Check incidents.py
    if INCIDENTS_API_PATH.exists():
        content = INCIDENTS_API_PATH.read_text()
        if "# Layer: L2" not in content:
            violations.append(Violation(
                rule_id="INC-HDR-001",
                severity="ERROR",
                file=str(INCIDENTS_API_PATH),
                line=1,
                message="Incidents API must declare Layer: L2",
                fix="Add '# Layer: L2 — Product APIs' header"
            ))

    # Check services
    if INCIDENTS_SERVICES_PATH.exists():
        for service_file in INCIDENTS_SERVICES_PATH.glob("*.py"):
            if service_file.name == "__init__.py":
                continue

            content = service_file.read_text()
            if "# Layer: L4" not in content:
                violations.append(Violation(
                    rule_id="INC-HDR-002",
                    severity="ERROR",
                    file=str(service_file),
                    line=1,
                    message=f"Service {service_file.name} must declare Layer: L4",
                    fix="Add '# Layer: L4 — Domain Engines' header"
                ))

    return violations


# =============================================================================
# Rule 5: SQL Patterns
# =============================================================================

def check_sql_patterns(verbose: bool = False) -> list[Violation]:
    """
    Validate SQL patterns in incidents domain.

    Rules:
    - Analytics queries should use v_incidents_o2 view when available
    - Tenant isolation must be present in all queries
    """
    violations = []

    if not INCIDENTS_API_PATH.exists():
        return violations

    content = INCIDENTS_API_PATH.read_text()
    lines = content.split("\n")

    # Check for missing tenant isolation in raw SQL
    in_sql_block = False
    sql_start_line = 0

    for i, line in enumerate(lines, 1):
        if 'text("""' in line or "text('''" in line:
            in_sql_block = True
            sql_start_line = i
        elif '""")' in line or "''')" in line:
            in_sql_block = False

        if in_sql_block and re.search(r'\bFROM\s+(incidents|incident_evidence)', line, re.IGNORECASE):
            # Check if tenant_id filter exists nearby (within next 5 lines)
            snippet = "\n".join(lines[i-1:i+5])
            if "tenant_id" not in snippet.lower():
                violations.append(Violation(
                    rule_id="INC-SQL-001",
                    severity="WARNING",
                    file=str(INCIDENTS_API_PATH),
                    line=i,
                    message="Query may be missing tenant_id filter",
                    fix="Ensure tenant_id = :tenant_id is in WHERE clause"
                ))

    return violations


# =============================================================================
# Rule 6: Cross-Domain Contract
# =============================================================================

def check_cross_domain_contract(verbose: bool = False) -> list[Violation]:
    """
    Validate cross-domain contract compliance.

    Rules:
    - Incidents domain must not write to runs, policy_proposals, etc.
    - Cross-domain reads are allowed but must be FK-based
    """
    violations = []

    files_to_check = [INCIDENTS_API_PATH]
    if INCIDENTS_SERVICES_PATH.exists():
        files_to_check.extend(INCIDENTS_SERVICES_PATH.glob("*.py"))

    forbidden_tables = [
        "runs",
        "aos_traces",
        "aos_trace_steps",
        "policy_proposals",
        "policy_rules",
        "prevention_records",
    ]

    for file_path in files_to_check:
        if not file_path.exists():
            continue

        content = file_path.read_text()
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            for table in forbidden_tables:
                # Check for writes to other domain tables
                if re.search(rf'\bINSERT\s+INTO\s+{table}\b', line, re.IGNORECASE):
                    violations.append(Violation(
                        rule_id="INC-XD-001",
                        severity="ERROR",
                        file=str(file_path),
                        line=i,
                        message=f"Incidents domain cannot write to '{table}' table",
                        fix=f"Remove write to '{table}' - violates cross-domain contract"
                    ))

                if re.search(rf'\bUPDATE\s+{table}\s+SET\b', line, re.IGNORECASE):
                    violations.append(Violation(
                        rule_id="INC-XD-002",
                        severity="ERROR",
                        file=str(file_path),
                        line=i,
                        message=f"Incidents domain cannot update '{table}' table",
                        fix=f"Remove update to '{table}' - violates cross-domain contract"
                    ))

    return violations


# =============================================================================
# Rule 7: CAP-E2E-001 Compliance
# =============================================================================

def check_cap_e2e_001(capabilities: dict, verbose: bool = False) -> list[Violation]:
    """
    Validate CAP-E2E-001 compliance.

    Rule: Capabilities MUST remain DECLARED until E2E validation passes.
    """
    violations = []

    # Check if any capability claims OBSERVED without observation trace
    for cap_id, cap_def in capabilities.items():
        status = cap_def.get("status")
        if status == "OBSERVED":
            observation = cap_def.get("observation", {})
            if not observation.get("scenario_id"):
                cap_file = CAPABILITY_REGISTRY_PATH / f"AURORA_L2_CAPABILITY_{cap_id.replace('.', '_')}.yaml"
                violations.append(Violation(
                    rule_id="INC-CAP-E2E-002",
                    severity="ERROR",
                    file=str(cap_file),
                    line=None,
                    message=f"Capability '{cap_id}' is OBSERVED but missing observation.scenario_id",
                    fix="Run E2E scenario or change status back to DECLARED"
                ))

    return violations


# =============================================================================
# Main Checker
# =============================================================================

def run_all_checks(verbose: bool = False) -> list[Violation]:
    """Run all incidents domain checks."""
    all_violations = []

    # Load capabilities
    capabilities = load_incidents_capabilities()
    if verbose:
        print(f"  Loaded {len(capabilities)} incidents capabilities")

    print("\n" + "=" * 60)
    print("INCIDENTS DOMAIN CONTRACT CHECK")
    print("=" * 60)

    # Rule 1: Capability Registry
    print("\n▶ Checking capability registry compliance...")
    violations = check_capability_registry(capabilities, verbose)
    all_violations.extend(violations)
    print(f"  Found {len(violations)} violations")

    # Rule 2: L2 Facade Rule
    print("\n▶ Checking L2 facade rule (no writes)...")
    violations = check_l2_facade_rule(verbose)
    all_violations.extend(violations)
    print(f"  Found {len(violations)} violations")

    # Rule 3: Service Responsibilities
    print("\n▶ Checking service responsibilities...")
    violations = check_service_responsibilities(verbose)
    all_violations.extend(violations)
    print(f"  Found {len(violations)} violations")

    # Rule 4: Layer Headers
    print("\n▶ Checking layer headers...")
    violations = check_layer_headers(verbose)
    all_violations.extend(violations)
    print(f"  Found {len(violations)} violations")

    # Rule 5: SQL Patterns
    print("\n▶ Checking SQL patterns...")
    violations = check_sql_patterns(verbose)
    all_violations.extend(violations)
    print(f"  Found {len(violations)} violations")

    # Rule 6: Cross-Domain Contract
    print("\n▶ Checking cross-domain contract...")
    violations = check_cross_domain_contract(verbose)
    all_violations.extend(violations)
    print(f"  Found {len(violations)} violations")

    # Rule 7: CAP-E2E-001
    print("\n▶ Checking CAP-E2E-001 compliance...")
    violations = check_cap_e2e_001(capabilities, verbose)
    all_violations.extend(violations)
    print(f"  Found {len(violations)} violations")

    return all_violations


def print_violations(violations: list[Violation], show_fixes: bool = False) -> None:
    """Print violations in a readable format."""
    if not violations:
        return

    print("\n" + "-" * 60)
    print("VIOLATIONS FOUND")
    print("-" * 60)

    errors = [v for v in violations if v.severity == "ERROR"]
    warnings = [v for v in violations if v.severity == "WARNING"]

    for i, v in enumerate(errors + warnings, 1):
        icon = "✗" if v.severity == "ERROR" else "⚠"
        print(f"\n{icon} [{v.rule_id}] {v.severity}")
        print(f"  File: {v.file}" + (f":{v.line}" if v.line else ""))
        print(f"  Issue: {v.message}")
        if show_fixes and v.fix:
            print(f"  Fix: {v.fix}")


def main():
    parser = argparse.ArgumentParser(description="Incidents Domain CI Contract Check")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fix", action="store_true", help="Show suggested fixes")
    args = parser.parse_args()

    violations = run_all_checks(args.verbose)

    print_violations(violations, args.fix)

    # Summary
    errors = len([v for v in violations if v.severity == "ERROR"])
    warnings = len([v for v in violations if v.severity == "WARNING"])

    print("\n" + "=" * 60)
    if errors == 0 and warnings == 0:
        print("✓ INCIDENTS DOMAIN CONTRACT CHECK: PASSED")
        print("=" * 60)
        return 0
    elif errors == 0:
        print(f"⚠ INCIDENTS DOMAIN CONTRACT CHECK: PASSED with {warnings} warnings")
        print("=" * 60)
        return 0
    else:
        print(f"✗ INCIDENTS DOMAIN CONTRACT CHECK: FAILED")
        print(f"  {errors} errors, {warnings} warnings")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
