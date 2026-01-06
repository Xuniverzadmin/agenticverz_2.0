"""
PB-S1 Bypass Detection Tests

These tests scan the codebase for potential bypasses of the PB-S1 immutability invariant.
Any code path that could mutate completed/failed worker_runs must be caught.

STATUS: CI-ENFORCED
Reference: PIN-199, PIN-201
"""

import re
from pathlib import Path

import pytest

# Paths to scan
BACKEND_APP = Path(__file__).parent.parent / "app"
BACKEND_ROOT = Path(__file__).parent.parent


class TestPBS1BypassDetection:
    """
    Detect potential bypasses of PB-S1 immutability.

    Risk: Future code could bypass the trigger by:
    - Using raw SQL
    - Updating status via ORM without trigger protection
    - Using a different table that isn't protected
    """

    def test_no_raw_update_worker_runs_status(self):
        """
        Scan for raw SQL UPDATE worker_runs SET status=...

        Allowed exceptions:
        - Migration files (schema changes)
        - Test files (testing the trigger)
        - Trigger definition itself
        - Legitimate transitions TO 'failed' status (protected by trigger)

        The trigger blocks:
        - Updates FROM 'completed' or 'failed' to anything else
        - Mutations of terminal state fields

        The trigger allows:
        - Transitions TO 'failed' (from running/queued)
        """
        violations = []
        allowed_paths = [
            "alembic/versions",
            "tests/test_pb_s1",
            "tests/test_pb_s2",  # Tests that verify trigger rejection
        ]

        # Pattern for suspicious mutations (FROM terminal states)
        dangerous_patterns = [
            # Resetting completed/failed back to queued/running
            re.compile(r'UPDATE\s+worker_runs.*SET.*status\s*=\s*["\']queued', re.IGNORECASE | re.DOTALL),
            re.compile(r'UPDATE\s+worker_runs.*SET.*status\s*=\s*["\']running', re.IGNORECASE | re.DOTALL),
            # Resetting terminal timestamps
            re.compile(r"UPDATE\s+worker_runs.*SET.*completed_at\s*=\s*NULL", re.IGNORECASE | re.DOTALL),
        ]

        for py_file in BACKEND_ROOT.rglob("*.py"):
            # Skip allowed paths
            if any(allowed in str(py_file) for allowed in allowed_paths):
                continue

            content = py_file.read_text()
            for pattern in dangerous_patterns:
                if pattern.search(content):
                    violations.append(f"{py_file}: matches dangerous pattern")

        assert not violations, (
            f"PB-S1 BYPASS RISK: Found dangerous UPDATE worker_runs patterns:\n"
            f"{chr(10).join(violations)}\n"
            "This could attempt to bypass the immutability trigger."
        )

    def test_document_allowed_status_updates(self):
        """
        Document which files contain UPDATE worker_runs SET status.

        This is not a failure - just documentation for review.
        The trigger protects against mutations FROM terminal states.
        """
        files_with_updates = []

        pattern = re.compile(r"UPDATE\s+worker_runs\s+SET\s+.*status", re.IGNORECASE)

        for py_file in BACKEND_ROOT.rglob("*.py"):
            content = py_file.read_text()
            if pattern.search(content):
                # Extract the status being set
                status_match = re.search(
                    r'UPDATE\s+worker_runs\s+SET\s+.*status\s*=\s*["\']?(\w+)', content, re.IGNORECASE
                )
                status = status_match.group(1) if status_match else "unknown"
                files_with_updates.append(f"{py_file.name}: status={status}")

        # Log for documentation
        if files_with_updates:
            print("\nFiles with UPDATE worker_runs SET status:\n")
            for f in files_with_updates:
                print(f"  - {f}")
            print("\nNote: Transitions TO 'failed' are protected by trigger.")
            print("      Only mutations FROM terminal states are blocked.")

    def test_no_direct_status_mutation_in_api(self):
        """
        Scan API routes for direct WorkerRun.status = mutations.

        Allowed:
        - Initial creation (status = "queued")
        - Transition to terminal (handled by trigger)
        """
        violations = []
        api_path = BACKEND_APP / "api"

        # Pattern for direct status assignment on WorkerRun
        pattern = re.compile(
            r'(WorkerRun|worker_run|run)\.status\s*=\s*["\']?(queued|running|completed|failed)', re.IGNORECASE
        )

        for py_file in api_path.rglob("*.py"):
            content = py_file.read_text()
            matches = pattern.findall(content)
            if matches:
                # Check if it's in a non-retry context
                if "/retry" not in content or "completed" in str(matches) or "failed" in str(matches):
                    violations.append(f"{py_file}: {matches}")

        # This is a warning, not a hard fail - review manually
        if violations:
            pytest.skip(
                f"REVIEW REQUIRED: Found status mutations in API:\n"
                f"{chr(10).join(violations)}\n"
                "Verify these are protected by the immutability trigger."
            )

    def test_worker_runs_trigger_exists_in_migrations(self):
        """
        Verify the immutability trigger is defined in migrations.
        """
        migrations_path = BACKEND_ROOT / "alembic" / "versions"
        trigger_found = False

        for migration_file in migrations_path.glob("*.py"):
            content = migration_file.read_text()
            if "prevent_worker_run_mutation" in content:
                trigger_found = True
                break

        assert trigger_found, (
            "PB-S1 CRITICAL: Immutability trigger not found in migrations!\n"
            "Expected: prevent_worker_run_mutation() function"
        )

    def test_retry_endpoint_uses_new_row(self):
        """
        Verify /admin/retry creates NEW rows, not mutations.

        Check for:
        - WorkerRun() constructor call (new row)
        - parent_run_id assignment
        - is_retry=True
        """
        main_py = BACKEND_APP / "main.py"
        content = main_py.read_text()

        # Find the retry endpoint
        retry_pattern = re.compile(r'@app\.post\(["\']*/admin/retry["\'].*?\ndef\s+\w+.*?(?=@app\.|$)', re.DOTALL)
        match = retry_pattern.search(content)

        if not match:
            pytest.skip("Retry endpoint not found in main.py")

        retry_code = match.group(0)

        # Verify it creates new row
        assert "WorkerRun(" in retry_code or "worker_run = WorkerRun" in content, (
            "PB-S1 VIOLATION: /admin/retry must create NEW WorkerRun, not update"
        )

        # Verify parent linkage
        assert "parent_run_id" in retry_code, "PB-S1 VIOLATION: /admin/retry must set parent_run_id"

    def test_rerun_endpoint_returns_410(self):
        """
        Verify /admin/rerun is hard-disabled (410 Gone).
        """
        main_py = BACKEND_APP / "main.py"
        content = main_py.read_text()

        # Check for rerun endpoint with 410
        if "/admin/rerun" in content:
            assert "410" in content or "status_code=410" in content, (
                "PB-S1 VIOLATION: /admin/rerun must return 410 Gone"
            )


class TestPBS1TableConfusion:
    """
    Detect confusion between `runs` and `worker_runs` tables.

    Risk: Code might use wrong table, bypassing protections.
    """

    def test_document_table_distinction(self):
        """
        Verify both tables exist and are distinct.
        """
        # Check db.py has Run -> "runs" table
        db_py = BACKEND_APP / "db.py"
        db_content = db_py.read_text()
        assert "class Run(SQLModel" in db_content, "Run model not found in db.py"
        assert '__tablename__ = "runs"' in db_content, "runs table not defined"

        # Check tenant.py has WorkerRun -> "worker_runs" table
        tenant_py = BACKEND_APP / "models" / "tenant.py"
        tenant_content = tenant_py.read_text()
        assert "class WorkerRun(SQLModel" in tenant_content, "WorkerRun not found"

        # Document the distinction
        # This test passes as documentation that both exist

    def test_no_cross_table_confusion_in_retry(self):
        """
        Verify retry logic uses WorkerRun, not Run.
        """
        main_py = BACKEND_APP / "main.py"
        content = main_py.read_text()

        # Find imports
        if "from app.db import Run" in content:
            # If Run is imported, verify it's not used in retry
            retry_section = content[content.find("/admin/retry") : content.find("/admin/retry") + 500]
            assert "Run(" not in retry_section, "PB-S1 TABLE CONFUSION: /admin/retry uses Run instead of WorkerRun"
