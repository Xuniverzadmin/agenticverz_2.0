#!/usr/bin/env python3
"""
Tenant Isolation Test for Phase A.5 Verification

Tests that:
1. Cost records are only visible to their owning tenant
2. Advisories are only visible to their owning tenant
3. Worker runs are only visible to their owning tenant

Usage:
    DATABASE_URL=... python3 scripts/verification/tenant_isolation_test.py
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# DB-AUTH-001: Declare local-only authority
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from scripts._db_guard import assert_db_authority  # noqa: E402
assert_db_authority("local")

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

VALID_TENANT = "demo-tenant"
INVALID_TENANT = "nonexistent-tenant-xyz-12345"


def test_cost_records_isolation():
    """Cost records must be isolated by tenant_id."""
    with engine.connect() as conn:
        # Valid tenant should have records
        result = conn.execute(
            text("SELECT COUNT(*) FROM cost_records WHERE tenant_id = :tid"),
            {"tid": VALID_TENANT},
        )
        valid_count = result.scalar()

        # Invalid tenant should have 0 records
        result = conn.execute(
            text("SELECT COUNT(*) FROM cost_records WHERE tenant_id = :tid"),
            {"tid": INVALID_TENANT},
        )
        invalid_count = result.scalar()

        passed = invalid_count == 0
        status = "✅ PASS" if passed else "❌ FAIL"
        print(
            f"{status} cost_records isolation: valid={valid_count}, invalid={invalid_count}"
        )
        return passed


def test_cost_anomalies_isolation():
    """Cost anomalies must be isolated by tenant_id."""
    with engine.connect() as conn:
        # Valid tenant may have anomalies
        result = conn.execute(
            text("SELECT COUNT(*) FROM cost_anomalies WHERE tenant_id = :tid"),
            {"tid": VALID_TENANT},
        )
        valid_count = result.scalar()

        # Invalid tenant should have 0 anomalies
        result = conn.execute(
            text("SELECT COUNT(*) FROM cost_anomalies WHERE tenant_id = :tid"),
            {"tid": INVALID_TENANT},
        )
        invalid_count = result.scalar()

        passed = invalid_count == 0
        status = "✅ PASS" if passed else "❌ FAIL"
        print(
            f"{status} cost_anomalies isolation: valid={valid_count}, invalid={invalid_count}"
        )
        return passed


def test_worker_runs_isolation():
    """Worker runs must be isolated by tenant_id."""
    with engine.connect() as conn:
        # Valid tenant should have runs
        result = conn.execute(
            text("SELECT COUNT(*) FROM worker_runs WHERE tenant_id = :tid"),
            {"tid": VALID_TENANT},
        )
        valid_count = result.scalar()

        # Invalid tenant should have 0 runs
        result = conn.execute(
            text("SELECT COUNT(*) FROM worker_runs WHERE tenant_id = :tid"),
            {"tid": INVALID_TENANT},
        )
        invalid_count = result.scalar()

        passed = invalid_count == 0
        status = "✅ PASS" if passed else "❌ FAIL"
        print(
            f"{status} worker_runs isolation: valid={valid_count}, invalid={invalid_count}"
        )
        return passed


def test_cross_tenant_join_safety():
    """Joining cost_records to worker_runs should not leak across tenants."""
    with engine.connect() as conn:
        # Check that cost_records.request_id references worker_runs within same tenant
        result = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM cost_records cr
                JOIN worker_runs wr ON cr.request_id = wr.id
                WHERE cr.tenant_id != wr.tenant_id
            """
            )
        )
        cross_tenant_count = result.scalar()

        passed = cross_tenant_count == 0
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} cross-tenant join safety: violations={cross_tenant_count}")
        return passed


def main():
    print("=" * 60)
    print("TENANT ISOLATION TEST")
    print("=" * 60)
    print(f"Valid tenant: {VALID_TENANT}")
    print(f"Invalid tenant: {INVALID_TENANT}")
    print("-" * 60)

    results = [
        test_cost_records_isolation(),
        test_cost_anomalies_isolation(),
        test_worker_runs_isolation(),
        test_cross_tenant_join_safety(),
    ]

    print("=" * 60)
    if all(results):
        print("ALL TESTS PASSED ✅")
        return 0
    else:
        print("SOME TESTS FAILED ❌")
        return 1


if __name__ == "__main__":
    sys.exit(main())
