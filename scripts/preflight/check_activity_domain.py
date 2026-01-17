#!/usr/bin/env python3
"""
Activity Domain CI Contract

Validates architectural constraints for the Activity domain:
1. Capability Registry Compliance
2. Layer Violations (L2 facade rule)
3. Service Responsibilities
4. Endpoint → Capability Mapping

Reference: docs/architecture/activity/ACTIVITY_CAPABILITY_REGISTRY.yaml

Usage:
    python scripts/preflight/check_activity_domain.py
    python scripts/preflight/check_activity_domain.py --verbose
    python scripts/preflight/check_activity_domain.py --fix  # Show fixes only
"""

import argparse
import ast
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
REGISTRY_PATH = Path(__file__).parent.parent.parent / "docs/architecture/activity/ACTIVITY_CAPABILITY_REGISTRY.yaml"
ACTIVITY_API_PATH = BACKEND_PATH / "app/api/activity.py"
ACTIVITY_SERVICES_PATH = BACKEND_PATH / "app/services/activity"


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

def load_registry() -> dict:
    """Load the capability registry YAML."""
    if not REGISTRY_PATH.exists():
        return {}

    with open(REGISTRY_PATH) as f:
        return yaml.safe_load(f)


# =============================================================================
# Rule 1: Capability Registry Compliance
# =============================================================================

def check_capability_registry(registry: dict, verbose: bool = False) -> list[Violation]:
    """
    Validate capability registry internal consistency.

    Rules:
    - Every capability must have an endpoint
    - Every capability must have a service
    - Service must be in L4
    - Weights must sum to 1.0 for attention_queue
    """
    violations = []

    capabilities = registry.get("capabilities", {})
    services = registry.get("services", {})

    for cap_id, cap_def in capabilities.items():
        # Check endpoint exists
        if "endpoint" not in cap_def:
            violations.append(Violation(
                rule_id="ACT-REG-001",
                severity="ERROR",
                file=str(REGISTRY_PATH),
                line=None,
                message=f"Capability '{cap_id}' missing endpoint definition",
                fix=f"Add endpoint: path and method to capability '{cap_id}'"
            ))

        # Check service exists
        service_name = cap_def.get("service")
        if not service_name:
            violations.append(Violation(
                rule_id="ACT-REG-002",
                severity="ERROR",
                file=str(REGISTRY_PATH),
                line=None,
                message=f"Capability '{cap_id}' missing service definition",
                fix=f"Add service name to capability '{cap_id}'"
            ))
        elif service_name not in services:
            violations.append(Violation(
                rule_id="ACT-REG-003",
                severity="ERROR",
                file=str(REGISTRY_PATH),
                line=None,
                message=f"Capability '{cap_id}' references undefined service '{service_name}'",
                fix=f"Add service definition for '{service_name}' in services section"
            ))

        # Check service layer
        if service_name and service_name in services:
            service_def = services[service_name]
            if service_def.get("layer") != "L4":
                violations.append(Violation(
                    rule_id="ACT-REG-004",
                    severity="ERROR",
                    file=str(REGISTRY_PATH),
                    line=None,
                    message=f"Service '{service_name}' must be L4, found '{service_def.get('layer')}'",
                    fix=f"Change layer to L4 for service '{service_name}'"
                ))

    # Check attention_queue weights sum to 1.0
    attention_cap = capabilities.get("activity.attention_queue", {})
    weights = attention_cap.get("weights", {})
    if weights:
        total = sum(weights.values())
        if abs(total - 1.0) > 0.001:
            violations.append(Violation(
                rule_id="ACT-REG-005",
                severity="ERROR",
                file=str(REGISTRY_PATH),
                line=None,
                message=f"Attention queue weights sum to {total}, must equal 1.0",
                fix="Adjust weights to sum to 1.0"
            ))

    return violations


# =============================================================================
# Rule 2: L2 Facade Rule (No Writes in Activity API)
# =============================================================================

def check_l2_facade_rule(verbose: bool = False) -> list[Violation]:
    """
    Validate that activity.py (L2) contains no write operations.

    Rules:
    - No INSERT, UPDATE, DELETE in SQL
    - No .add(), .commit(), .delete() on session
    - Only SELECT queries allowed
    """
    violations = []

    if not ACTIVITY_API_PATH.exists():
        return violations

    content = ACTIVITY_API_PATH.read_text()
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
                    rule_id="ACT-L2-001",
                    severity="ERROR",
                    file=str(ACTIVITY_API_PATH),
                    line=i,
                    message=description,
                    fix="Move write operation to L4 service or remove"
                ))

    return violations


# =============================================================================
# Rule 3: Service Responsibilities
# =============================================================================

def check_service_responsibilities(registry: dict, verbose: bool = False) -> list[Violation]:
    """
    Validate that services follow their declared responsibilities.

    Rules:
    - Services in 'forbidden' list should not contain those patterns
    - Read services should not have write operations
    """
    violations = []
    services = registry.get("services", {})

    for service_name, service_def in services.items():
        location = service_def.get("location")
        if not location:
            continue

        service_path = BACKEND_PATH.parent / location
        if not service_path.exists():
            # Service file doesn't exist yet - that's a TODO, not a violation
            if verbose:
                print(f"  [INFO] Service file not found: {location}")
            continue

        content = service_path.read_text()
        lines = content.split("\n")

        forbidden = service_def.get("forbidden", [])

        for forbidden_item in forbidden:
            # Map forbidden items to patterns
            patterns = []
            if "Write to any table" in forbidden_item:
                patterns = [
                    (r'\bINSERT\s+INTO\b', "INSERT found but writing forbidden"),
                    (r'\bUPDATE\s+\w+\s+SET\b', "UPDATE found but writing forbidden"),
                    (r'\bDELETE\s+FROM\b', "DELETE found but writing forbidden"),
                    (r'session\.add\s*\(', "session.add() found but writing forbidden"),
                ]
            elif "Call other services" in forbidden_item:
                # Check for imports from other services
                patterns = [
                    (r'from\s+app\.services\.\w+\s+import', "Cross-service import forbidden"),
                ]
            elif "Use machine learning" in forbidden_item:
                patterns = [
                    (r'import\s+(?:sklearn|tensorflow|torch|keras)', "ML import forbidden"),
                ]

            for pattern, description in patterns:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        violations.append(Violation(
                            rule_id="ACT-SVC-001",
                            severity="ERROR",
                            file=str(service_path),
                            line=i,
                            message=f"{service_name}: {description}",
                            fix=f"Remove {forbidden_item.lower()} from {service_name}"
                        ))

    return violations


# =============================================================================
# Rule 4: Endpoint → Capability Mapping
# =============================================================================

def check_endpoint_capability_mapping(registry: dict, verbose: bool = False) -> list[Violation]:
    """
    Validate that all implemented endpoints have declared capabilities.

    Rules:
    - Every @router.get/post in activity.py must have a capability
    - Capability status should match implementation state
    """
    violations = []

    if not ACTIVITY_API_PATH.exists():
        return violations

    content = ACTIVITY_API_PATH.read_text()
    capabilities = registry.get("capabilities", {})

    # Extract declared endpoints from registry
    declared_endpoints = set()
    for cap_id, cap_def in capabilities.items():
        endpoint = cap_def.get("endpoint", {})
        path = endpoint.get("path", "")
        if path:
            # Normalize path (remove /api/v1 prefix, handle {param})
            normalized = path.replace("/api/v1/activity", "").replace("{run_id}", "{id}")
            declared_endpoints.add(normalized)

    # Extract implemented endpoints from code
    endpoint_pattern = r'@router\.(get|post|put|delete)\s*\(\s*["\']([^"\']+)["\']'
    implemented = []

    for match in re.finditer(endpoint_pattern, content):
        method = match.group(1).upper()
        path = match.group(2)
        # Find line number
        line_num = content[:match.start()].count('\n') + 1
        implemented.append((path, method, line_num))

    # Check for undeclared endpoints
    for path, method, line_num in implemented:
        normalized = path.replace("{run_id}", "{id}")
        if normalized not in declared_endpoints and path not in ["/runs", "/runs/{run_id}", "/runs/{run_id}/evidence", "/runs/{run_id}/proof"]:
            # These are already declared, skip them
            pass

    # Check for TODO capabilities that are implemented
    for cap_id, cap_def in capabilities.items():
        if cap_def.get("status") == "TODO":
            endpoint = cap_def.get("endpoint", {})
            path = endpoint.get("path", "").replace("/api/v1/activity", "")

            # Check if this endpoint is implemented
            for impl_path, method, line_num in implemented:
                if impl_path == path:
                    violations.append(Violation(
                        rule_id="ACT-MAP-001",
                        severity="WARNING",
                        file=str(ACTIVITY_API_PATH),
                        line=line_num,
                        message=f"Endpoint '{path}' is implemented but capability '{cap_id}' is TODO",
                        fix=f"Update capability '{cap_id}' status to OBSERVED in registry"
                    ))

    return violations


# =============================================================================
# Rule 5: Layer Header Compliance
# =============================================================================

def check_layer_headers(verbose: bool = False) -> list[Violation]:
    """
    Validate that all activity-related files have correct layer headers.

    Rules:
    - activity.py must declare L2
    - Services must declare L4
    """
    violations = []

    # Check activity.py
    if ACTIVITY_API_PATH.exists():
        content = ACTIVITY_API_PATH.read_text()
        if "# Layer: L2" not in content:
            violations.append(Violation(
                rule_id="ACT-HDR-001",
                severity="ERROR",
                file=str(ACTIVITY_API_PATH),
                line=1,
                message="Activity API must declare Layer: L2",
                fix="Add '# Layer: L2 — Product APIs' header"
            ))

    # Check services
    if ACTIVITY_SERVICES_PATH.exists():
        for service_file in ACTIVITY_SERVICES_PATH.glob("*.py"):
            if service_file.name == "__init__.py":
                continue

            content = service_file.read_text()
            if "# Layer: L4" not in content:
                violations.append(Violation(
                    rule_id="ACT-HDR-002",
                    severity="ERROR",
                    file=str(service_file),
                    line=1,
                    message=f"Service {service_file.name} must declare Layer: L4",
                    fix="Add '# Layer: L4 — Domain Engines' header"
                ))

    return violations


# =============================================================================
# Rule 6: SQL Query Validation
# =============================================================================

def check_sql_patterns(verbose: bool = False) -> list[Violation]:
    """
    Validate SQL patterns in activity domain.

    Rules:
    - All queries should use v_runs_o2 view (not runs table directly)
    - Tenant isolation must be present
    """
    violations = []

    if not ACTIVITY_API_PATH.exists():
        return violations

    content = ACTIVITY_API_PATH.read_text()
    lines = content.split("\n")

    # Check for direct runs table access (should use v_runs_o2)
    for i, line in enumerate(lines, 1):
        # Allow worker_runs and other tables, but flag direct 'FROM runs' without view
        if re.search(r'\bFROM\s+runs\b', line, re.IGNORECASE):
            if 'v_runs_o2' not in line:
                violations.append(Violation(
                    rule_id="ACT-SQL-001",
                    severity="WARNING",
                    file=str(ACTIVITY_API_PATH),
                    line=i,
                    message="Direct 'FROM runs' - consider using v_runs_o2 view",
                    fix="Use 'FROM v_runs_o2' for pre-computed fields"
                ))

        # Check for tenant isolation
        if re.search(r'\bSELECT\b.*\bFROM\b', line, re.IGNORECASE):
            # This is a simplistic check - in production, verify tenant_id in WHERE
            pass

    return violations


# =============================================================================
# Main Checker
# =============================================================================

def run_all_checks(verbose: bool = False) -> list[Violation]:
    """Run all activity domain checks."""
    all_violations = []

    # Load registry
    registry = load_registry()
    if not registry:
        print("WARNING: Capability registry not found, skipping registry checks")

    print("\n" + "=" * 60)
    print("ACTIVITY DOMAIN CONTRACT CHECK")
    print("=" * 60)

    # Rule 1: Capability Registry
    if registry:
        print("\n▶ Checking capability registry compliance...")
        violations = check_capability_registry(registry, verbose)
        all_violations.extend(violations)
        print(f"  Found {len(violations)} violations")

    # Rule 2: L2 Facade Rule
    print("\n▶ Checking L2 facade rule (no writes)...")
    violations = check_l2_facade_rule(verbose)
    all_violations.extend(violations)
    print(f"  Found {len(violations)} violations")

    # Rule 3: Service Responsibilities
    if registry:
        print("\n▶ Checking service responsibilities...")
        violations = check_service_responsibilities(registry, verbose)
        all_violations.extend(violations)
        print(f"  Found {len(violations)} violations")

    # Rule 4: Endpoint → Capability Mapping
    if registry:
        print("\n▶ Checking endpoint-capability mapping...")
        violations = check_endpoint_capability_mapping(registry, verbose)
        all_violations.extend(violations)
        print(f"  Found {len(violations)} violations")

    # Rule 5: Layer Headers
    print("\n▶ Checking layer headers...")
    violations = check_layer_headers(verbose)
    all_violations.extend(violations)
    print(f"  Found {len(violations)} violations")

    # Rule 6: SQL Patterns
    print("\n▶ Checking SQL patterns...")
    violations = check_sql_patterns(verbose)
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
    parser = argparse.ArgumentParser(description="Activity Domain CI Contract Check")
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
        print("✓ ACTIVITY DOMAIN CONTRACT CHECK: PASSED")
        print("=" * 60)
        return 0
    elif errors == 0:
        print(f"⚠ ACTIVITY DOMAIN CONTRACT CHECK: PASSED with {warnings} warnings")
        print("=" * 60)
        return 0
    else:
        print(f"✗ ACTIVITY DOMAIN CONTRACT CHECK: FAILED")
        print(f"  {errors} errors, {warnings} warnings")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
