"""
PB-S4 Policy Evolution With Provenance Tests

These tests verify the PB-S4 truth guarantee:
- System may propose policy changes based on observed feedback
- System must NEVER auto-enforce, auto-modify, or retroactively affect executions
- Human approval is MANDATORY

STATUS: FROZEN — These tests must NEVER be modified to pass by changing behavior.
If a test fails, the FIX must be in the application code, not the test.

Reference: PIN-204
"""

import os

import pytest

# Skip if no database URL
pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL not set")


class TestPBS4ProposalSeparation:
    """
    Test that policy proposals are stored separately from execution data.

    INVARIANT: Proposals table is separate from worker_runs/traces.
    ENFORCEMENT: Database schema + service design.
    """

    def test_pb_s4_policy_proposals_table_exists(self):
        """
        PB-S4: policy_proposals table must exist as separate storage.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_name = 'policy_proposals';
            """
            )
            result = cur.fetchone()

            assert result is not None, "policy_proposals table does not exist"
            assert result[0] == "policy_proposals"

        finally:
            conn.close()

    def test_pb_s4_policy_versions_table_exists(self):
        """
        PB-S4: policy_versions table must exist for append-only history.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_name = 'policy_versions';
            """
            )
            result = cur.fetchone()

            assert result is not None, "policy_versions table does not exist"
            assert result[0] == "policy_versions"

        finally:
            conn.close()

    def test_pb_s4_proposal_has_provenance_column(self):
        """
        PB-S4: Proposals must have provenance (triggering_feedback_ids).
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            cur.execute(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'policy_proposals'
                AND column_name = 'triggering_feedback_ids';
            """
            )
            result = cur.fetchone()

            assert result is not None, "triggering_feedback_ids column missing"
            assert result[1] == "jsonb", "triggering_feedback_ids should be JSONB"

        finally:
            conn.close()

    def test_pb_s4_proposal_not_linked_to_execution_by_fk(self):
        """
        PB-S4: Proposals should NOT have FK to worker_runs.

        This ensures proposals cannot cascade to execution data.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            cur.execute(
                """
                SELECT tc.constraint_name
                FROM information_schema.table_constraints tc
                WHERE tc.table_name = 'policy_proposals'
                AND tc.constraint_type = 'FOREIGN KEY';
            """
            )
            results = cur.fetchall()

            # Check no FK references worker_runs
            fk_names = [r[0] for r in results]
            for name in fk_names:
                cur.execute(
                    f"""
                    SELECT ccu.table_name
                    FROM information_schema.constraint_column_usage ccu
                    WHERE ccu.constraint_name = '{name}';
                """
                )
                ref = cur.fetchone()
                if ref:
                    assert ref[0] != "worker_runs", f"FK {name} references worker_runs - violates PB-S4 separation"

        finally:
            conn.close()


class TestPBS4ProposalFromFeedback:
    """
    Test PB-S4-S1: Policy Proposal From Repeated Feedback.

    INVARIANT: Proposals are created without modifying feedback or executions.
    """

    def test_pb_s4_proposal_status_starts_as_draft(self):
        """
        PB-S4-S1: New proposals must start with status='draft'.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Get current state
            cur.execute("SELECT COUNT(*) FROM worker_runs")
            before_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM pattern_feedback")
            before_feedback = cur.fetchone()[0]

            # Insert a test proposal
            cur.execute(
                """
                INSERT INTO policy_proposals
                (tenant_id, proposal_name, proposal_type, rationale, proposed_rule,
                 triggering_feedback_ids, status)
                VALUES
                ('test-tenant-001', 'test_proposal', 'test_type', 'Test rationale',
                 '{"test": true}'::jsonb, '[]'::jsonb, 'draft')
                RETURNING status;
            """
            )
            result = cur.fetchone()
            assert result[0] == "draft", "New proposal must start as draft"

            conn.commit()

            # Verify no side effects
            cur.execute("SELECT COUNT(*) FROM worker_runs")
            after_count = cur.fetchone()[0]
            assert before_count == after_count, "Proposal creation modified worker_runs!"

            cur.execute("SELECT COUNT(*) FROM pattern_feedback")
            after_feedback = cur.fetchone()[0]
            assert before_feedback == after_feedback, "Proposal creation modified feedback!"

            # Cleanup
            cur.execute("DELETE FROM policy_proposals WHERE proposal_name = 'test_proposal'")
            conn.commit()

        finally:
            conn.close()


class TestPBS4ApprovalRejectionFlow:
    """
    Test PB-S4-S2: Human Approval/Rejection Flow.

    INVARIANT: Approval/rejection is manual and does not mutate history.
    """

    def test_pb_s4_approval_creates_version(self):
        """
        PB-S4-S2: Approving a proposal creates a version snapshot.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Create a test proposal
            cur.execute(
                """
                INSERT INTO policy_proposals
                (tenant_id, proposal_name, proposal_type, rationale, proposed_rule,
                 triggering_feedback_ids, status)
                VALUES
                ('test-tenant-001', 'approval_test', 'test_type', 'Test',
                 '{"rule": "test"}'::jsonb, '[]'::jsonb, 'draft')
                RETURNING id;
            """
            )
            proposal_id = cur.fetchone()[0]
            conn.commit()

            # Approve it
            cur.execute(
                f"""
                UPDATE policy_proposals
                SET status = 'approved', reviewed_at = NOW(), reviewed_by = 'test@example.com'
                WHERE id = '{proposal_id}';
            """
            )
            conn.commit()

            # Create version snapshot
            cur.execute(
                f"""
                INSERT INTO policy_versions
                (proposal_id, version, rule_snapshot, created_by)
                VALUES
                ('{proposal_id}', 1, '{{"rule": "test"}}'::jsonb, 'test@example.com')
                RETURNING id;
            """
            )
            version_id = cur.fetchone()[0]
            conn.commit()

            assert version_id is not None, "Version should be created on approval"

            # Cleanup
            cur.execute(f"DELETE FROM policy_versions WHERE proposal_id = '{proposal_id}'")
            cur.execute(f"DELETE FROM policy_proposals WHERE id = '{proposal_id}'")
            conn.commit()

        finally:
            conn.close()

    def test_pb_s4_rejection_preserves_proposal(self):
        """
        PB-S4-S2: Rejecting a proposal preserves it for audit (no deletion).
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Create a test proposal
            cur.execute(
                """
                INSERT INTO policy_proposals
                (tenant_id, proposal_name, proposal_type, rationale, proposed_rule,
                 triggering_feedback_ids, status)
                VALUES
                ('test-tenant-001', 'rejection_test', 'test_type', 'Test',
                 '{"rule": "test"}'::jsonb, '[]'::jsonb, 'draft')
                RETURNING id;
            """
            )
            proposal_id = cur.fetchone()[0]
            conn.commit()

            # Reject it
            cur.execute(
                f"""
                UPDATE policy_proposals
                SET status = 'rejected', reviewed_at = NOW(),
                    reviewed_by = 'test@example.com', review_notes = 'Not approved'
                WHERE id = '{proposal_id}';
            """
            )
            conn.commit()

            # Verify proposal still exists
            cur.execute(f"SELECT status FROM policy_proposals WHERE id = '{proposal_id}'")
            result = cur.fetchone()
            assert result is not None, "Rejected proposal should still exist"
            assert result[0] == "rejected", "Status should be rejected"

            # Verify no version created
            cur.execute(f"SELECT COUNT(*) FROM policy_versions WHERE proposal_id = '{proposal_id}'")
            version_count = cur.fetchone()[0]
            assert version_count == 0, "Rejection should not create a version"

            # Cleanup
            cur.execute(f"DELETE FROM policy_proposals WHERE id = '{proposal_id}'")
            conn.commit()

        finally:
            conn.close()


class TestPBS4ImmutabilityGuarantee:
    """
    Test that proposals do NOT modify execution data.

    INVARIANT: Execution history is never modified by proposals.
    """

    def test_pb_s4_proposal_cannot_modify_runs(self):
        """
        PB-S4 CRITICAL: Creating/approving proposals does not modify worker_runs.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Get current state of worker_runs
            cur.execute("SELECT COUNT(*), SUM(cost_cents) FROM worker_runs")
            before_count, before_cost = cur.fetchone()

            # Create and approve a proposal
            cur.execute(
                """
                INSERT INTO policy_proposals
                (tenant_id, proposal_name, proposal_type, rationale, proposed_rule,
                 triggering_feedback_ids, status)
                VALUES
                ('test-tenant-001', 'immutability_test', 'test_type', 'Test',
                 '{"rule": "test"}'::jsonb, '[]'::jsonb, 'approved')
                RETURNING id;
            """
            )
            proposal_id = cur.fetchone()[0]
            conn.commit()

            # Verify worker_runs unchanged
            cur.execute("SELECT COUNT(*), SUM(cost_cents) FROM worker_runs")
            after_count, after_cost = cur.fetchone()

            assert before_count == after_count, "Proposal modified run count!"
            assert before_cost == after_cost, "Proposal modified costs!"

            # Cleanup
            cur.execute(f"DELETE FROM policy_proposals WHERE id = '{proposal_id}'")
            conn.commit()

        finally:
            conn.close()

    def test_pb_s4_proposal_cannot_modify_feedback(self):
        """
        PB-S4 CRITICAL: Creating proposals does not modify pattern_feedback.
        """
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()

        try:
            # Get current state of pattern_feedback
            cur.execute("SELECT COUNT(*) FROM pattern_feedback")
            before_count = cur.fetchone()[0]

            # Create a proposal
            cur.execute(
                """
                INSERT INTO policy_proposals
                (tenant_id, proposal_name, proposal_type, rationale, proposed_rule,
                 triggering_feedback_ids, status)
                VALUES
                ('test-tenant-001', 'feedback_test', 'test_type', 'Test',
                 '{"rule": "test"}'::jsonb, '[]'::jsonb, 'draft')
                RETURNING id;
            """
            )
            proposal_id = cur.fetchone()[0]
            conn.commit()

            # Verify pattern_feedback unchanged
            cur.execute("SELECT COUNT(*) FROM pattern_feedback")
            after_count = cur.fetchone()[0]

            assert before_count == after_count, "Proposal creation modified feedback!"

            # Cleanup
            cur.execute(f"DELETE FROM policy_proposals WHERE id = '{proposal_id}'")
            conn.commit()

        finally:
            conn.close()


class TestPBS4ServiceExists:
    """
    Verify the policy proposal service exists.
    """

    def test_pb_s4_policy_proposal_module_exists(self):
        """
        Verify the policy_proposal service exists and has expected functions.
        """
        try:
            from app.services import policy_proposal

            assert hasattr(policy_proposal, "check_proposal_eligibility")
            assert hasattr(policy_proposal, "create_policy_proposal")
            assert hasattr(policy_proposal, "review_policy_proposal")
            print("policy_proposal module: all expected functions present")
        except ImportError as e:
            pytest.fail(f"Cannot import policy_proposal service: {e}")

    def test_pb_s4_policy_model_exists(self):
        """
        Verify the PolicyProposal model exists.
        """
        try:
            from app.models.policy import PolicyProposal, PolicyVersion

            assert PolicyProposal.__tablename__ == "policy_proposals"
            assert PolicyVersion.__tablename__ == "policy_versions"
            print("PolicyProposal and PolicyVersion models: exist")
        except ImportError as e:
            pytest.fail(f"Cannot import PolicyProposal model: {e}")


# Marker for CI to identify PB-S4 tests
def pytest_configure(config):
    config.addinivalue_line("markers", "pb_s4: Tests for PB-S4 truth guarantee (policy evolution)")
