#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Infra Obligation Promotion Checker
# artifact_class: CODE
"""
Infra Obligation Promotion Checker

Checks the status of all infrastructure obligations and determines
which are PROMOTED (tests must pass) vs UNFULFILLED (tests may skip).

Usage:
    python scripts/ops/check_infra_obligations.py [--ci] [--verbose]

Output:
    - List of all obligations with status
    - Promotion eligibility for each
    - CI exit code: 0 if all promoted obligations pass, 1 otherwise

Reference: docs/infra/INFRA_OBLIGATION_SCHEMA.md
"""

import sys
import yaml
import argparse
from pathlib import Path
from typing import Any

# Add backend to path for imports
BACKEND_DIR = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))


def load_obligations(registry_path: Path) -> list[dict[str, Any]]:
    """Load obligations from registry YAML."""
    with open(registry_path) as f:
        data = yaml.safe_load(f)
    return data.get("obligations", [])


def check_table_exists(table_name: str, schema: str = "public") -> bool:
    """Check if a table exists in the database."""
    try:
        from sqlalchemy import text
        from app.db import get_engine

        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = :schema
                    AND table_name = :table
                )
            """
                ),
                {"schema": schema, "table": table_name},
            )
            return result.scalar()
    except Exception:
        return False


def check_column_exists(
    table_name: str, column_name: str, schema: str = "public"
) -> bool:
    """Check if a column exists in a table."""
    try:
        from sqlalchemy import text
        from app.db import get_engine

        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_schema = :schema
                    AND table_name = :table
                    AND column_name = :column
                )
            """
                ),
                {"schema": schema, "table": table_name, "column": column_name},
            )
            return result.scalar()
    except Exception:
        return False


def check_trigger_exists(trigger_name: str, schema: str = "public") -> bool:
    """Check if a trigger exists."""
    try:
        from sqlalchemy import text
        from app.db import get_engine

        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT FROM information_schema.triggers
                    WHERE trigger_schema = :schema
                    AND trigger_name = :trigger
                )
            """
                ),
                {"schema": schema, "trigger": trigger_name},
            )
            return result.scalar()
    except Exception:
        return False


def check_function_exists(func_name: str, schema: str = "public") -> bool:
    """Check if a function exists."""
    try:
        from sqlalchemy import text
        from app.db import get_engine

        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT FROM information_schema.routines
                    WHERE routine_schema = :schema
                    AND routine_name = :func
                )
            """
                ),
                {"schema": schema, "func": func_name},
            )
            return result.scalar()
    except Exception:
        return False


def check_view_exists(view_name: str, schema: str = "public") -> bool:
    """Check if a view exists."""
    try:
        from sqlalchemy import text
        from app.db import get_engine

        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT FROM information_schema.views
                    WHERE table_schema = :schema
                    AND table_name = :view
                )
            """
                ),
                {"schema": schema, "view": view_name},
            )
            return result.scalar()
    except Exception:
        return False


def check_constraint_exists(constraint_name: str, schema: str = "public") -> bool:
    """Check if a constraint exists."""
    try:
        from sqlalchemy import text
        from app.db import get_engine

        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT FROM information_schema.table_constraints
                    WHERE constraint_schema = :schema
                    AND constraint_name = :constraint
                )
            """
                ),
                {"schema": schema, "constraint": constraint_name},
            )
            return result.scalar()
    except Exception:
        return False


def check_requirement(req: dict[str, Any]) -> tuple[bool, str]:
    """Check if a single requirement is satisfied."""
    req_type = req.get("type", "")
    name = req.get("name", "")
    schema = req.get("schema", "public")

    # Parse compound names (e.g., "runs.retry_of_run_id")
    if "." in name and req_type == "column":
        parts = name.split(".")
        table_name = parts[0]
        column_name = parts[1].split(" ")[0]  # Handle "(includes 'crashed')" syntax
        exists = check_column_exists(table_name, column_name, schema)
        return exists, f"column {table_name}.{column_name}"

    if req_type == "table":
        exists = check_table_exists(name, schema)
        return exists, f"table {name}"
    elif req_type == "trigger":
        exists = check_trigger_exists(name, schema)
        return exists, f"trigger {name}"
    elif req_type == "function":
        exists = check_function_exists(name, schema)
        return exists, f"function {name}"
    elif req_type == "view":
        exists = check_view_exists(name, schema)
        return exists, f"view {name}"
    elif req_type == "constraint":
        exists = check_constraint_exists(name, schema)
        return exists, f"constraint {name}"
    elif req_type == "column":
        # Already handled above for compound names
        return False, f"column {name} (parse error)"
    else:
        return False, f"unknown type {req_type}"


def check_obligation(
    obligation: dict[str, Any], verbose: bool = False
) -> dict[str, Any]:
    """Check the status of an obligation."""
    obl_id = obligation.get("id", "UNKNOWN")
    title = obligation.get("title", "")
    status = obligation.get("status", "UNFULFILLED")
    requires = obligation.get("requires", [])
    test_files = obligation.get("test_files", [])

    # Check all requirements
    missing = []
    found = []

    for req in requires:
        exists, desc = check_requirement(req)
        if exists:
            found.append(desc)
        else:
            missing.append(desc)

    # Determine computed status
    if len(missing) == 0 and len(found) > 0:
        computed_status = "PROMOTED"
    elif len(found) > 0:
        computed_status = "PARTIAL"
    else:
        computed_status = "UNFULFILLED"

    # Calculate test count
    test_count = sum(tf.get("count", 0) for tf in test_files)

    return {
        "id": obl_id,
        "title": title,
        "declared_status": status,
        "computed_status": computed_status,
        "found": found,
        "missing": missing,
        "test_count": test_count,
        "promotion_ready": len(missing) == 0 and len(found) > 0,
    }


def print_obligation_status(result: dict[str, Any], verbose: bool = False) -> None:
    """Print the status of an obligation."""
    obl_id = result["id"]
    computed = result["computed_status"]
    declared = result["declared_status"]
    test_count = result["test_count"]

    # Status emoji
    if computed == "PROMOTED":
        emoji = "✅"
    elif computed == "PARTIAL":
        emoji = "⚠️"
    else:
        emoji = "❌"

    # Status mismatch warning
    mismatch = ""
    if declared == "PROMOTED" and computed != "PROMOTED":
        mismatch = " [REGRESSION - declared PROMOTED but missing infra!]"
    elif computed == "PROMOTED" and declared != "PROMOTED":
        mismatch = " [READY FOR PROMOTION]"

    print(f"{emoji} {obl_id}: {computed} ({test_count} tests){mismatch}")

    if verbose:
        if result["missing"]:
            print("   Missing:")
            for m in result["missing"]:
                print(f"     - {m}")
        if result["found"]:
            print("   Found:")
            for f in result["found"]:
                print(f"     + {f}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Check infra obligation promotion status"
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode: exit 1 if promoted obligations have missing infra",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed requirement status"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    # Find registry
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent
    registry_path = repo_root / "docs" / "infra" / "INFRA_OBLIGATION_REGISTRY.yaml"

    if not registry_path.exists():
        print(f"ERROR: Registry not found at {registry_path}")
        sys.exit(1)

    # Load and check obligations
    obligations = load_obligations(registry_path)
    results = []

    print("=" * 70)
    print("INFRA OBLIGATION STATUS CHECK")
    print("=" * 70)
    print()

    # Check each obligation
    for obl in obligations:
        result = check_obligation(obl, args.verbose)
        results.append(result)
        print_obligation_status(result, args.verbose)

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    # Summary stats
    promoted = sum(1 for r in results if r["computed_status"] == "PROMOTED")
    partial = sum(1 for r in results if r["computed_status"] == "PARTIAL")
    unfulfilled = sum(1 for r in results if r["computed_status"] == "UNFULFILLED")
    ready_for_promotion = sum(
        1
        for r in results
        if r["promotion_ready"] and r["declared_status"] != "PROMOTED"
    )
    regressions = sum(
        1
        for r in results
        if r["declared_status"] == "PROMOTED" and r["computed_status"] != "PROMOTED"
    )
    total_tests = sum(r["test_count"] for r in results)

    print(f"Total Obligations: {len(results)}")
    print(f"  PROMOTED:    {promoted}")
    print(f"  PARTIAL:     {partial}")
    print(f"  UNFULFILLED: {unfulfilled}")
    print()
    print(f"Total Bucket B Tests: {total_tests}")
    print()

    if ready_for_promotion > 0:
        print(f"🎯 Ready for Promotion: {ready_for_promotion}")
        for r in results:
            if r["promotion_ready"] and r["declared_status"] != "PROMOTED":
                print(f"   - {r['id']}")
        print()

    if regressions > 0:
        print(f"🚨 REGRESSIONS DETECTED: {regressions}")
        for r in results:
            if (
                r["declared_status"] == "PROMOTED"
                and r["computed_status"] != "PROMOTED"
            ):
                print(f"   - {r['id']}: declared PROMOTED but infra missing!")
        print()

    # CI exit code
    if args.ci:
        if regressions > 0:
            print("CI: FAIL (promoted obligations have missing infrastructure)")
            sys.exit(1)
        else:
            print("CI: PASS (no regressions in promoted obligations)")
            sys.exit(0)


if __name__ == "__main__":
    main()
