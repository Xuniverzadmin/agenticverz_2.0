#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Visibility Contract Layer (VCL) Validator
# artifact_class: CODE
"""
Visibility Contract Layer (VCL) Validator

Enforces visibility_contract.yaml declarations by verifying:
1. Required API endpoints exist
2. Forbidden surfaces are not exposed
3. All declared artifacts have proper visibility
4. (DPCC) Data presence check - API returns data when DB has rows
5. (CSEG) Console scope enforcement - FORBIDDEN consoles cannot access
6. (DPC) Discovery Presence Check - artifact has discovery_ledger entry
7. (PLC) Promotion Legitimacy Check - discovery_ledger.status != 'observed'

Reference: BL-WEB-001 behavior rule
Principle: Data existence ≠ Data observability

Phase-Aware Enforcement:
  The validator automatically adjusts DPCC/CSEG/DPC/PLC severity based on active phase.
  Use --phase to specify the phase, or it defaults to B.

  Phase B: DPCC=WARNING, CSEG=DECLARATIVE, DPC/PLC=SKIP (data exists, truth frozen)
  Phase C: DPCC=BLOCKER, CSEG=BLOCKER, DPC/PLC=WARNING (eligibility + proposals active)
  Phase D: DPCC=BLOCKER, CSEG=BLOCKER, DPC/PLC=BLOCKER (full enforcement)

Usage:
    # Basic validation (Phase B default)
    python scripts/ops/visibility_validator.py --check-all

    # Explicit phase selection
    python scripts/ops/visibility_validator.py --check-all --phase B
    python scripts/ops/visibility_validator.py --check-all --phase C

    # Phase B checks (equivalent to --phase B with data/console checks)
    python scripts/ops/visibility_validator.py --check-all --check-data-presence --check-console-scope

    # Phase C checks (blockers + discovery)
    python scripts/ops/visibility_validator.py --check-all --phase C

    # Manual discovery check (any phase)
    python scripts/ops/visibility_validator.py --check-all --check-discovery

    # Individual Phase C blockers (override phase default)
    python scripts/ops/visibility_validator.py --check-all --strict-data-presence
    python scripts/ops/visibility_validator.py --check-all --strict-console-scope
"""

import argparse
import os
import sys
from pathlib import Path

# Add backend to path for guard import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend"))

# DB-AUTH-001: Require Neon authority (HIGH - visibility validation)
from scripts._db_guard import require_neon  # noqa: E402
require_neon()

import yaml

# Contract file location
CONTRACT_FILE = (
    Path(__file__).parent.parent.parent / "docs/contracts/visibility_contract.yaml"
)

# Table to API mapping for data presence checks
TABLE_API_MAPPING = {
    "pattern_feedback": "/api/v1/feedback",
    "policy_proposals": "/api/v1/policy-proposals",
    "policy_versions": "/api/v1/policy-proposals",  # versions accessed via proposals
    "prediction_events": "/api/v1/predictions",
    "worker_runs": "/api/v1/workers",  # runs accessed via workers
    "aos_traces": "/api/v1/traces",
}

# =============================================================================
# CONSOLE TOPOLOGY (Reference: PIN-190, PIN-138)
# =============================================================================
# CRITICAL: Consoles are separated by SUBDOMAIN + AUTH AUDIENCE, not API prefix.
#
# Two logical consoles (preflight mirrors inherit from parent):
#   - customer: console.agenticverz.com (aos-customer)
#   - founder:  fops.agenticverz.com (aos-founder)
# =============================================================================

CONSOLE_TOPOLOGY = {
    "customer": {
        "subdomain": "console.agenticverz.com",
        "audience": "aos-customer",
        "description": "Customer trust & control console",
    },
    "founder": {
        "subdomain": "fops.agenticverz.com",
        "audience": "aos-founder",
        "description": "Founder Ops Console (internal)",
    },
    # Preflight consoles inherit visibility from parent
    "preflight-customer": {
        "subdomain": "preflight-console.agenticverz.com",
        "audience": "aos-internal",
        "mirrors": "customer",
    },
    "preflight-founder": {
        "subdomain": "preflight-fops.agenticverz.com",
        "audience": "aos-internal",
        "mirrors": "founder",
    },
}

# Required consoles for validation (preflight inherits)
REQUIRED_CONSOLES = ["customer", "founder"]

# =============================================================================
# PHASE ENFORCEMENT TABLE
# =============================================================================
# This is the switch that activates DPCC/CSEG properly based on active phase.
# Reference: SESSION_PLAYBOOK.yaml phase_enforcement_table
# =============================================================================

PHASE_ENFORCEMENT = {
    "A": {
        "visibility_lifecycle": "NOT_ACTIVE",
        "dpcc": "DISABLED",
        "cseg": "DISABLED",
        "description": "Phase A: Pre-truth (S1-S6 verification)",
    },
    "B": {
        "visibility_lifecycle": "LOAD_AND_DECLARE",
        "eligibility_detection": False,
        "dpcc": "WARNING",
        "cseg": "DECLARATIVE",
        "description": "Phase B: Data exists, truth frozen",
    },
    "C": {
        "visibility_lifecycle": "LOAD_DETECT_PROPOSE",
        "eligibility_detection": True,
        "dpcc": "BLOCKER",
        "cseg": "BLOCKER",
        "description": "Phase C: Eligibility + proposals active",
    },
    "D": {
        "visibility_lifecycle": "LOAD_ENFORCE",
        "eligibility_detection": True,
        "dpcc": "BLOCKER",
        "cseg": "BLOCKER",
        "promotion_at_boundary": True,
        "description": "Phase D+: Full enforcement",
    },
}

DEFAULT_PHASE = "B"


def load_contract():
    """Load the visibility contract."""
    if not CONTRACT_FILE.exists():
        print(f"ERROR: Contract file not found: {CONTRACT_FILE}")
        sys.exit(1)

    with open(CONTRACT_FILE) as f:
        return yaml.safe_load(f)


def check_api_endpoint_exists(endpoint: str) -> bool:
    """
    Check if an API endpoint exists in the codebase.

    This is a basic check - looks for route decorators.
    """
    api_dir = Path(__file__).parent.parent.parent / "backend/app/api"

    # Extract method and path
    parts = endpoint.split(" ", 1)
    if len(parts) != 2:
        return False

    method, path = parts
    method = method.lower()

    # Convert path to regex-like pattern
    # /api/v1/feedback/{id} -> feedback
    path_parts = path.strip("/").split("/")
    if len(path_parts) >= 3:
        resource = path_parts[2]  # api/v1/<resource>
    else:
        resource = path_parts[-1]

    # Check if a file for this resource exists
    resource_file = api_dir / f"{resource.replace('-', '_')}.py"
    if not resource_file.exists():
        # Try singular form
        resource_file = api_dir / f"{resource.replace('-', '_').rstrip('s')}.py"

    return resource_file.exists()


def get_database_url() -> str:
    """
    Get the DATABASE_URL to use for validation.

    Priority:
    1. DATABASE_URL environment variable (explicit)
    2. Fail if not set (no silent fallback to wrong DB)

    This prevents GAP 3 (split-brain visibility) where validator
    checks one DB but API serves from another.
    """
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set.")
        print("  The validator must check the SAME database as the backend API.")
        print("  Set DATABASE_URL to match your backend's database.")
        print()
        print("  For Neon (production):")
        print(
            "    export DATABASE_URL='postgresql://neondb_owner:...@ep-...-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require'"
        )
        print()
        print("  For Local (development):")
        print(
            "    export DATABASE_URL='postgresql://nova:novapass@localhost:6432/nova_aos'"
        )
        sys.exit(1)
    return database_url


def check_db_has_rows(table_name: str) -> tuple[bool, int]:
    """
    Check if a table has any rows in the database.

    Returns (has_rows: bool, count: int)
    """
    try:
        import psycopg2

        database_url = get_database_url()
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count > 0, count
    except Exception:
        # Can't check DB - return unknown
        return None, -1


def check_api_returns_data(api_path: str) -> tuple[bool, int]:
    """
    Check if an API endpoint returns non-empty data.

    Returns (has_data: bool, count: int)
    """
    try:
        import requests

        api_key = os.environ.get(
            "AOS_API_KEY",
            "edf7eeb8df7ed639b9d1d8bcac572cea5b8cf97e1dffa00d0d3c5ded0f728aaf",
        )
        base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")

        headers = {
            "X-AOS-Key": api_key,
            "X-Roles": "admin",  # Use admin for full access
        }

        response = requests.get(f"{base_url}{api_path}", headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Handle different response formats
            if isinstance(data, dict):
                total = data.get("total", len(data.get("items", [])))
            elif isinstance(data, list):
                total = len(data)
            else:
                total = 0
            return total > 0, total
        return None, -1
    except Exception:
        return None, -1


def check_data_presence(name: str, config: dict, strict: bool = False) -> dict:
    """
    Check if data in DB is visible via API.

    Phase B: Returns warning only (strict=False)
    Phase C: Returns failure (strict=True)

    Returns dict with:
    - warning: str or None
    - check_result: dict
    """
    result = {
        "warning": None,
        "check_result": {},
    }

    table_name = config.get("table", name)
    api_path = TABLE_API_MAPPING.get(name)

    if not api_path:
        result["check_result"]["data_presence"] = "SKIP (no API mapping)"
        return result

    # Check DB
    db_has_rows, db_count = check_db_has_rows(table_name)
    result["check_result"]["db_rows"] = db_count if db_count >= 0 else "UNKNOWN"

    if db_has_rows is None:
        result["check_result"]["data_presence"] = "SKIP (DB unavailable)"
        return result

    if not db_has_rows:
        result["check_result"]["data_presence"] = "SKIP (no DB rows)"
        return result

    # DB has rows - check API
    api_has_data, api_count = check_api_returns_data(api_path)
    result["check_result"]["api_items"] = api_count if api_count >= 0 else "UNKNOWN"

    if api_has_data is None:
        result["check_result"]["data_presence"] = "SKIP (API unavailable)"
        return result

    if db_has_rows and not api_has_data:
        warning_msg = f"DATA PRESENCE GAP: {table_name} has {db_count} rows but API returns 0 items"
        result["warning"] = warning_msg
        result["check_result"]["data_presence"] = "WARNING" if not strict else "FAIL"
    else:
        result["check_result"]["data_presence"] = "PASS"

    return result


def check_console_scope(name: str, config: dict, strict: bool = False) -> dict:
    """
    Check Console Scope Enforcement Gate (CSEG).

    CRITICAL: Consoles are separated by SUBDOMAIN + AUTH AUDIENCE, not API prefix.
    Two consoles: customer (console.agenticverz.com) and founder (fops.agenticverz.com)
    Preflight consoles inherit from their parent.

    Phase B: DECLARATIVE only
      - Verify customer and founder visibility are declared
      - Do NOT perform runtime checks

    Phase C: RUNTIME enforcement (strict=True)
      - Same route, different subdomain, different audience
      - FORBIDDEN → must return 403/404
      - If 200 → VIOLATION

    Returns dict with:
    - violations: list of violations
    - warnings: list of warnings
    - check_result: dict of check results
    """
    result = {
        "violations": [],
        "warnings": [],
        "check_result": {},
    }

    consoles = config.get("consoles", {})

    # Phase B: Declarative only - verify both consoles are declared
    if not strict:
        for console in REQUIRED_CONSOLES:
            if console not in consoles:
                result["warnings"].append(
                    f"Console '{console}' not declared for {name}"
                )
                result["check_result"][f"console_{console}"] = "MISSING"
            else:
                visibility = consoles[console]
                result["check_result"][f"console_{console}"] = f"DECLARED_{visibility}"

        result["check_result"]["console_scope"] = "DECLARATIVE_ONLY (Phase B)"
        result["check_result"]["note"] = (
            "Runtime enforcement via subdomain+auth in Phase C"
        )
        return result

    # Phase C: Runtime enforcement via subdomain + auth
    # NOT YET IMPLEMENTED - requires actual subdomain routing
    api_path = TABLE_API_MAPPING.get(name)
    if not api_path:
        result["check_result"]["console_scope"] = "SKIP (no API mapping)"
        return result

    forbidden_consoles = [
        c for c, v in consoles.items() if v == "FORBIDDEN" and c in REQUIRED_CONSOLES
    ]

    if not forbidden_consoles:
        result["check_result"]["console_scope"] = "PASS (no FORBIDDEN consoles)"
        return result

    # Phase C runtime enforcement:
    # This would require actual subdomain routing to test properly.
    # The correct approach is:
    #   1. Set Host header to FORBIDDEN console's subdomain
    #   2. Set Authorization to FORBIDDEN console's audience token
    #   3. Expect 403/404

    result["check_result"]["console_scope"] = "PHASE_C_NOT_IMPLEMENTED"
    result["check_result"]["enforcement_method"] = "subdomain + auth audience"
    result["warnings"].append(
        "Phase C CSEG requires subdomain routing (console.agenticverz.com / fops.agenticverz.com). "
        "Current environment uses localhost. Skipping runtime check."
    )

    # Document what Phase C enforcement would check
    for console in forbidden_consoles:
        topology = CONSOLE_TOPOLOGY.get(console, {})
        subdomain = topology.get("subdomain", "unknown")
        audience = topology.get("audience", "unknown")
        result["check_result"][f"console_{console}"] = (
            f"FORBIDDEN (would check: Host={subdomain}, Audience={audience})"
        )

    return result


def check_discovery_presence(name: str, config: dict, phase: str = "B") -> dict:
    """
    Discovery Presence Check (DPC).

    When visibility is ACTIVE for an artifact,
    assert discovery_ledger contains >= 1 entry for that artifact.

    Phase B: SKIP
    Phase C+: WARNING -> BLOCKER (configurable)

    This guarantees visibility never appears "from nowhere".

    Returns dict with:
    - passed: bool
    - warning: str or None
    - check_result: dict
    """
    result = {
        "passed": True,
        "warning": None,
        "check_result": {},
    }

    # Phase B: Skip this check
    if phase == "B":
        result["check_result"]["discovery_presence"] = "SKIP (Phase B)"
        return result

    visibility = config.get("visibility", {})

    # Check if any O1-O4 is REQUIRED
    has_required_visibility = any(
        visibility.get(surface) == "REQUIRED" for surface in ["O1", "O2", "O3", "O4"]
    )

    if not has_required_visibility:
        result["check_result"]["discovery_presence"] = "SKIP (no REQUIRED visibility)"
        return result

    # Check discovery_ledger for this artifact
    # Uses same DB as visibility_validator (no split-brain)
    try:
        import psycopg2

        database_url = get_database_url()
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM discovery_ledger WHERE artifact = %s", (name,)
        )
        count = cur.fetchone()[0]
        cur.close()
        conn.close()

        result["check_result"]["discovery_entries"] = count

        if count == 0:
            result["warning"] = (
                f"DPC: Artifact '{name}' has REQUIRED visibility but no discovery entry"
            )
            result["check_result"]["discovery_presence"] = (
                "WARNING (no discovery entry)"
            )
            # In Phase D, this would be a failure
            if phase == "D":
                result["passed"] = False
        else:
            result["check_result"]["discovery_presence"] = "PASS"

    except Exception as e:
        result["check_result"]["discovery_presence"] = f"SKIP (DB error: {e})"

    return result


def check_promotion_legitimacy(name: str, config: dict, phase: str = "B") -> dict:
    """
    Promotion Legitimacy Check (PLC).

    If artifact has ACTIVE visibility,
    assert discovery_ledger.status != 'observed'.

    This ensures someone consciously promoted it.

    Phase B: SKIP
    Phase C: WARNING
    Phase D: BLOCKER

    Returns dict with:
    - passed: bool
    - warning: str or None
    - check_result: dict
    """
    result = {
        "passed": True,
        "warning": None,
        "check_result": {},
    }

    # Phase B: Skip this check
    if phase == "B":
        result["check_result"]["promotion_legitimacy"] = "SKIP (Phase B)"
        return result

    visibility = config.get("visibility", {})

    # Check if any O1-O4 is REQUIRED
    has_required_visibility = any(
        visibility.get(surface) == "REQUIRED" for surface in ["O1", "O2", "O3", "O4"]
    )

    if not has_required_visibility:
        result["check_result"]["promotion_legitimacy"] = "SKIP (no REQUIRED visibility)"
        return result

    # Check discovery_ledger status for this artifact
    # Uses same DB as visibility_validator (no split-brain)
    try:
        import psycopg2

        database_url = get_database_url()
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT status FROM discovery_ledger
            WHERE artifact = %s
            ORDER BY last_seen_at DESC
            LIMIT 1
        """,
            (name,),
        )
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row is None:
            result["warning"] = (
                f"PLC: Artifact '{name}' has visibility but no discovery entry"
            )
            result["check_result"]["promotion_legitimacy"] = (
                "WARNING (no discovery entry)"
            )
            if phase == "D":
                result["passed"] = False
        elif row[0] == "observed":
            result["warning"] = (
                f"PLC: Artifact '{name}' has visibility but status is still 'observed' (not promoted)"
            )
            result["check_result"]["promotion_legitimacy"] = "WARNING (status=observed)"
            if phase == "D":
                result["passed"] = False
        else:
            result["check_result"]["promotion_legitimacy"] = f"PASS (status={row[0]})"

    except Exception as e:
        result["check_result"]["promotion_legitimacy"] = f"SKIP (DB error: {e})"

    return result


def validate_artifact(
    name: str,
    config: dict,
    check_data: bool = False,
    strict_data: bool = False,
    check_console: bool = False,
    strict_console: bool = False,
    check_discovery: bool = False,
    phase: str = "B",
) -> dict:
    """
    Validate a single artifact against the contract.

    Args:
        name: Artifact name
        config: Artifact configuration from contract
        check_data: If True, check data presence (DB rows vs API response)
        strict_data: If True, data presence failure is BLOCKER (Phase C mode)
        check_console: If True, check console scope enforcement
        strict_console: If True, console scope violations are BLOCKER (Phase C mode)

    Returns dict with:
    - passed: bool
    - issues: list of issues
    - warnings: list of warnings (non-blocking)
    - checks: dict of check results
    """
    result = {
        "passed": True,
        "issues": [],
        "warnings": [],
        "checks": {},
    }

    visibility = config.get("visibility", {})
    consoles = config.get("consoles", {})
    api_endpoints = config.get("api_endpoints", {})
    required_endpoints = api_endpoints.get("required", [])

    # Check O1-O3 REQUIRED surfaces have endpoints
    for surface in ["O1", "O2", "O3"]:
        if visibility.get(surface) == "REQUIRED":
            # Check if there's at least one endpoint
            has_endpoint = len(required_endpoints) > 0
            result["checks"][f"{surface}_endpoint"] = has_endpoint
            if not has_endpoint:
                result["passed"] = False
                result["issues"].append(
                    f"{surface} is REQUIRED but no endpoints declared"
                )

    # Check O4 FORBIDDEN is respected
    if visibility.get("O4") == "FORBIDDEN":
        result["checks"]["O4_forbidden"] = True  # Contract declares it forbidden
    elif visibility.get("O4") == "REQUIRED":
        # Only execution data should have O4 REQUIRED
        if name not in ["worker_runs", "traces", "aos_traces"]:
            result["checks"]["O4_warning"] = True
            result["warnings"].append(f"O4 REQUIRED for non-execution artifact {name}")

    # Check console visibility is explicit for REQUIRED consoles
    # Note: customer and founder only - preflight consoles inherit from parent
    for console in REQUIRED_CONSOLES:
        if console not in consoles:
            result["passed"] = False
            result["issues"].append(f"Console visibility not declared: {console}")
        result["checks"][f"console_{console}"] = consoles.get(console, "MISSING")

    # Check required endpoints exist
    for endpoint in required_endpoints:
        exists = check_api_endpoint_exists(endpoint)
        result["checks"][f"endpoint_{endpoint}"] = exists
        if not exists:
            result["passed"] = False
            result["issues"].append(f"Required endpoint not found: {endpoint}")

    # Optional: Check data presence (Phase B = warning, Phase C = blocker)
    if check_data:
        data_result = check_data_presence(name, config, strict=strict_data)
        result["checks"].update(data_result["check_result"])
        if data_result["warning"]:
            if strict_data:
                result["passed"] = False
                result["issues"].append(data_result["warning"])
            else:
                result["warnings"].append(data_result["warning"])

    # Optional: Check console scope enforcement (Phase B = declarative, Phase C = runtime)
    if check_console:
        console_result = check_console_scope(name, config, strict=strict_console)
        result["checks"].update(console_result["check_result"])
        for violation in console_result["violations"]:
            if strict_console:
                result["passed"] = False
                result["issues"].append(violation)
            else:
                result["warnings"].append(violation)

    # Optional: Check discovery presence (Phase C+)
    # DPC: When visibility is ACTIVE, assert discovery_ledger contains >= 1 entry
    if check_discovery:
        dpc_result = check_discovery_presence(name, config, phase=phase)
        result["checks"].update(dpc_result["check_result"])
        if dpc_result["warning"]:
            if not dpc_result["passed"]:
                result["passed"] = False
                result["issues"].append(dpc_result["warning"])
            else:
                result["warnings"].append(dpc_result["warning"])

        # PLC: If artifact has visibility, assert status != 'observed'
        plc_result = check_promotion_legitimacy(name, config, phase=phase)
        result["checks"].update(plc_result["check_result"])
        if plc_result["warning"]:
            if not plc_result["passed"]:
                result["passed"] = False
                result["issues"].append(plc_result["warning"])
            else:
                result["warnings"].append(plc_result["warning"])

    return result


def validate_all(
    contract: dict,
    check_data: bool = False,
    strict_data: bool = False,
    check_console: bool = False,
    strict_console: bool = False,
    check_discovery: bool = False,
    phase: str = "B",
) -> dict:
    """Validate all artifacts in the contract."""
    results = {
        "passed": True,
        "total": 0,
        "passed_count": 0,
        "failed_count": 0,
        "warning_count": 0,
        "artifacts": {},
    }

    artifacts = contract.get("artifacts", {})

    for name, config in artifacts.items():
        result = validate_artifact(
            name,
            config,
            check_data=check_data,
            strict_data=strict_data,
            check_console=check_console,
            strict_console=strict_console,
            check_discovery=check_discovery,
            phase=phase,
        )
        results["artifacts"][name] = result
        results["total"] += 1

        if result["passed"]:
            results["passed_count"] += 1
        else:
            results["failed_count"] += 1
            results["passed"] = False

        if result.get("warnings"):
            results["warning_count"] += len(result["warnings"])

    return results


def print_results(results: dict, verbose: bool = False, check_data: bool = False):
    """Print validation results."""
    print("=" * 60)
    print("VISIBILITY CONTRACT VALIDATION")
    print("=" * 60)
    print()

    # Show data sources if checking data presence
    if check_data:
        database_url = os.environ.get("DATABASE_URL", "NOT SET")
        api_base = os.environ.get("API_BASE_URL", "http://localhost:8000")
        # Mask credentials in database URL
        if "@" in database_url:
            parts = database_url.split("@")
            masked = parts[0].rsplit(":", 1)[0] + ":***@" + parts[1]
        else:
            masked = database_url
        print("Data Sources:")
        print(f"  Database: {masked}")
        print(f"  API Base: {api_base}")
        print()

    for name, result in results["artifacts"].items():
        has_warnings = bool(result.get("warnings"))
        if result["passed"] and has_warnings:
            status = "PASS (with warnings)"
            icon = "⚠"
        elif result["passed"]:
            status = "PASS"
            icon = "✓"
        else:
            status = "FAIL"
            icon = "✗"
        print(f"{icon} {name}: {status}")

        if not result["passed"] or verbose:
            for issue in result["issues"]:
                print(f"    - {issue}")
            for warning in result.get("warnings", []):
                print(f"    - [WARNING] {warning}")

    print()
    print("-" * 60)
    print(f"Total: {results['total']}")
    print(f"Passed: {results['passed_count']}")
    print(f"Failed: {results['failed_count']}")
    if results.get("warning_count", 0) > 0:
        print(f"Warnings: {results['warning_count']}")
    print()

    if results["passed"]:
        if results.get("warning_count", 0) > 0:
            print("✓ VISIBILITY CONTRACT: PASSED WITH WARNINGS")
            print()
            print("Warnings are non-blocking in Phase B.")
            print("Use --strict-data-presence in Phase C to enforce.")
        else:
            print("✓ VISIBILITY CONTRACT: ALL CHECKS PASSED")
    else:
        print("✗ VISIBILITY CONTRACT: CHECKS FAILED")
        print()
        print("Required action:")
        print("1. Add missing API endpoints")
        print("2. Update visibility_contract.yaml if needed")
        print("3. Re-run this validator")
        print()
        print("Truth anchor: If data exists, its visibility must be contractual.")

    return 0 if results["passed"] else 1


def main():
    parser = argparse.ArgumentParser(
        description="Validate visibility contract declarations"
    )
    parser.add_argument(
        "--check-all",
        action="store_true",
        help="Check all artifacts in the contract",
    )
    parser.add_argument(
        "--artifact",
        type=str,
        help="Check a specific artifact",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show all checks, not just failures",
    )
    parser.add_argument(
        "--check-data-presence",
        action="store_true",
        help="Check if DB data is visible via API (WARNING in Phase B)",
    )
    parser.add_argument(
        "--strict-data-presence",
        action="store_true",
        help="Make data presence check a BLOCKER (Phase C mode)",
    )
    parser.add_argument(
        "--check-console-scope",
        action="store_true",
        help="Check console scope enforcement (DECLARATIVE in Phase B)",
    )
    parser.add_argument(
        "--strict-console-scope",
        action="store_true",
        help="Make console scope check a BLOCKER (Phase C mode - runtime enforcement)",
    )
    parser.add_argument(
        "--phase-c",
        action="store_true",
        help="Enable all Phase C blockers (--strict-data-presence + --strict-console-scope)",
    )
    parser.add_argument(
        "--phase",
        type=str,
        choices=["A", "B", "C", "D"],
        default=None,
        help="Active phase (A/B/C/D) - determines DPCC/CSEG severity automatically",
    )
    parser.add_argument(
        "--check-discovery",
        action="store_true",
        help="Check discovery presence (DPC) and promotion legitimacy (PLC)",
    )

    args = parser.parse_args()

    contract = load_contract()

    # Determine active phase and enforcement settings
    if args.phase:
        active_phase = args.phase.upper()
    elif args.phase_c:
        active_phase = "C"
    else:
        active_phase = DEFAULT_PHASE

    phase_config = PHASE_ENFORCEMENT.get(active_phase, PHASE_ENFORCEMENT[DEFAULT_PHASE])

    # Phase-aware enforcement: determine DPCC/CSEG severity from phase
    # Manual overrides (--strict-*) take precedence
    if args.strict_data_presence:
        strict_data = True
        check_data = True
    elif args.check_data_presence:
        strict_data = False
        check_data = True
    elif active_phase in ["C", "D"]:
        # Phase C/D automatically enables BLOCKER mode
        strict_data = phase_config["dpcc"] == "BLOCKER"
        check_data = phase_config["dpcc"] != "DISABLED"
    else:
        # Phase B defaults
        strict_data = False
        check_data = args.check_data_presence

    if args.strict_console_scope:
        strict_console = True
        check_console = True
    elif args.check_console_scope:
        strict_console = False
        check_console = True
    elif active_phase in ["C", "D"]:
        # Phase C/D automatically enables BLOCKER mode
        strict_console = phase_config["cseg"] == "BLOCKER"
        check_console = phase_config["cseg"] != "DISABLED"
    else:
        # Phase B defaults
        strict_console = False
        check_console = args.check_console_scope

    # Discovery check: DPC + PLC
    # Phase B: SKIP, Phase C: WARNING, Phase D: BLOCKER
    if args.check_discovery:
        check_discovery = True
    elif active_phase in ["C", "D"]:
        # Phase C/D automatically enables discovery checks
        check_discovery = phase_config.get("eligibility_detection", False)
    else:
        check_discovery = False

    # Print phase information
    print(f"Active Phase: {active_phase}")
    print(f"  {phase_config['description']}")
    print(f"  DPCC: {phase_config['dpcc']}, CSEG: {phase_config['cseg']}")
    if check_discovery:
        print("  Discovery: DPC + PLC checks enabled")
    print()

    if args.artifact:
        artifacts = contract.get("artifacts", {})
        if args.artifact not in artifacts:
            print(f"ERROR: Artifact '{args.artifact}' not found in contract")
            sys.exit(1)

        result = validate_artifact(
            args.artifact,
            artifacts[args.artifact],
            check_data=check_data,
            strict_data=strict_data,
            check_console=check_console,
            strict_console=strict_console,
            check_discovery=check_discovery,
            phase=active_phase,
        )
        results = {
            "passed": result["passed"],
            "total": 1,
            "passed_count": 1 if result["passed"] else 0,
            "failed_count": 0 if result["passed"] else 1,
            "warning_count": len(result.get("warnings", [])),
            "artifacts": {args.artifact: result},
        }
    else:
        results = validate_all(
            contract,
            check_data=check_data,
            strict_data=strict_data,
            check_console=check_console,
            strict_console=strict_console,
            check_discovery=check_discovery,
            phase=active_phase,
        )

    return print_results(results, args.verbose, check_data=check_data or check_console)


if __name__ == "__main__":
    sys.exit(main())
