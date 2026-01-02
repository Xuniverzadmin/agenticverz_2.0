# M12 Multi-Agent System Unit Tests
# Tests for job service, worker service, blackboard, and registry
#
# NOTE: These tests require the 'agents' schema to be present in the database.
# The schema is defined in PIN-062 and includes: agents.jobs, agents.job_items,
# agents.instances, agents.messages. Tests are skipped if schema is missing.

import os
import time
from decimal import Decimal
from uuid import uuid4

import pytest

# Set test environment
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_cVfk6XMYdt4G@ep-long-surf-a1n0hv91-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")


def _agents_schema_exists() -> bool:
    """Check if the 'agents' schema exists in the database."""
    try:
        import psycopg2

        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            return False
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'agents'")
        result = cur.fetchone()
        conn.close()
        return result is not None
    except Exception:
        return False


# Skip all tests requiring agents schema if it doesn't exist
AGENTS_SCHEMA_EXISTS = _agents_schema_exists()
requires_agents_schema = pytest.mark.skipif(
    not AGENTS_SCHEMA_EXISTS,
    reason="agents schema not present in database (see PIN-062 for schema definition)",
)

from app.agents.services.blackboard_service import get_blackboard_service
from app.agents.services.credit_service import CREDIT_COSTS, get_credit_service
from app.agents.services.job_service import JobConfig, get_job_service
from app.agents.services.message_service import get_message_service
from app.agents.services.registry_service import get_registry_service
from app.agents.services.worker_service import get_worker_service
from app.agents.skills.agent_spawn import AgentSpawnInput, AgentSpawnSkill
from app.agents.skills.blackboard_ops import (
    BlackboardLockInput,
    BlackboardLockSkill,
    BlackboardReadInput,
    BlackboardReadSkill,
    BlackboardWriteInput,
    BlackboardWriteSkill,
)

# =====================
# Test Fixtures
# =====================


@pytest.fixture
def job_service():
    """Get job service instance."""
    return get_job_service()


@pytest.fixture
def worker_service():
    """Get worker service instance."""
    return get_worker_service()


@pytest.fixture
def blackboard_service():
    """Get blackboard service instance."""
    try:
        return get_blackboard_service()
    except Exception:
        pytest.skip("Redis not available")


@pytest.fixture
def message_service():
    """Get message service instance."""
    return get_message_service()


@pytest.fixture
def registry_service():
    """Get registry service instance."""
    return get_registry_service()


@pytest.fixture
def credit_service():
    """Get credit service instance."""
    return get_credit_service()


# =====================
# Credit Service Tests
# =====================


class TestCreditService:
    """Tests for credit service."""

    def test_get_skill_cost(self, credit_service):
        """Test skill cost lookup."""
        assert credit_service.get_skill_cost("agent_spawn") == Decimal("5")
        assert credit_service.get_skill_cost("agent_invoke") == Decimal("10")
        assert credit_service.get_skill_cost("blackboard_read") == Decimal("1")
        assert credit_service.get_skill_cost("unknown_skill") == Decimal("1")

    def test_credit_costs_defined(self):
        """Test all credit costs are defined."""
        assert "agent_spawn" in CREDIT_COSTS
        assert "agent_invoke" in CREDIT_COSTS
        assert "blackboard_read" in CREDIT_COSTS
        assert "blackboard_write" in CREDIT_COSTS
        assert "blackboard_lock" in CREDIT_COSTS
        assert "job_item" in CREDIT_COSTS


# =====================
# Job Service Tests
# =====================


@requires_agents_schema
class TestJobService:
    """Tests for job service (requires agents.jobs table)."""

    def test_create_job_success(self, job_service):
        """Test successful job creation."""
        config = JobConfig(
            orchestrator_agent="test_orchestrator",
            worker_agent="test_worker",
            task="test_task",
            items=["item1", "item2", "item3"],
            parallelism=2,
        )

        job = job_service.create_job(
            config=config,
            orchestrator_instance_id="test_orch_123",
            tenant_id="test_tenant",
        )

        assert job.id is not None
        assert job.status == "running"
        assert job.progress.total == 3
        assert job.progress.completed == 0
        assert job.progress.pending == 3
        assert float(job.credits.reserved) > 0

    def test_create_job_empty_items_fails(self, job_service):
        """Test that empty items list fails."""
        config = JobConfig(
            orchestrator_agent="test_orchestrator",
            worker_agent="test_worker",
            task="test_task",
            items=[],
        )

        with pytest.raises(ValueError, match="at least one item"):
            job_service.create_job(
                config=config,
                orchestrator_instance_id="test_orch_123",
            )

    def test_get_job(self, job_service):
        """Test job retrieval."""
        # Create job first
        config = JobConfig(
            orchestrator_agent="test_orch",
            worker_agent="test_worker",
            task="get_test",
            items=["a", "b"],
        )
        created = job_service.create_job(
            config=config,
            orchestrator_instance_id="test_orch_456",
        )

        # Retrieve it
        job = job_service.get_job(created.id)

        assert job is not None
        assert job.id == created.id
        assert job.task == "get_test"

    def test_list_jobs(self, job_service):
        """Test job listing."""
        jobs = job_service.list_jobs(tenant_id="default", limit=10)
        assert isinstance(jobs, list)

    def test_cancel_job(self, job_service):
        """Test job cancellation."""
        config = JobConfig(
            orchestrator_agent="test_orch",
            worker_agent="test_worker",
            task="cancel_test",
            items=["x"],
        )
        job = job_service.create_job(
            config=config,
            orchestrator_instance_id="test_orch_789",
        )

        cancelled = job_service.cancel_job(job.id)
        assert cancelled is not None  # Returns cancellation details dict, not bool

        # Verify status
        updated = job_service.get_job(job.id)
        assert updated.status == "cancelled"


# =====================
# Worker Service Tests
# =====================


@requires_agents_schema
class TestWorkerService:
    """Tests for worker service (SKIP LOCKED pattern, requires agents.job_items table)."""

    def test_claim_item_success(self, job_service, worker_service):
        """Test successful item claim."""
        # Create job
        config = JobConfig(
            orchestrator_agent="claim_orch",
            worker_agent="claim_worker",
            task="claim_test",
            items=["url1", "url2", "url3"],
        )
        job = job_service.create_job(
            config=config,
            orchestrator_instance_id="claim_orch_1",
        )

        # Claim item
        claimed = worker_service.claim_item(job.id, "worker_instance_1")

        assert claimed is not None
        assert claimed.job_id == job.id
        assert claimed.item_index == 0
        assert claimed.input is not None

    def test_claim_items_no_duplicates(self, job_service, worker_service):
        """Test that multiple workers don't claim same item."""
        config = JobConfig(
            orchestrator_agent="dup_orch",
            worker_agent="dup_worker",
            task="dup_test",
            items=["a", "b", "c"],
        )
        job = job_service.create_job(
            config=config,
            orchestrator_instance_id="dup_orch_1",
        )

        # Two workers claim
        claim1 = worker_service.claim_item(job.id, "worker_1")
        claim2 = worker_service.claim_item(job.id, "worker_2")

        assert claim1 is not None
        assert claim2 is not None
        assert claim1.id != claim2.id  # Different items

    def test_complete_item(self, job_service, worker_service):
        """Test item completion."""
        config = JobConfig(
            orchestrator_agent="complete_orch",
            worker_agent="complete_worker",
            task="complete_test",
            items=["item"],
        )
        job = job_service.create_job(
            config=config,
            orchestrator_instance_id="complete_orch_1",
        )

        # Claim and complete
        claimed = worker_service.claim_item(job.id, "worker_complete")
        assert claimed is not None

        result = worker_service.complete_item(claimed.id, {"result": "success"})
        assert result is True

        # Check job progress
        updated = job_service.get_job(job.id)
        assert updated.progress.completed >= 1

    def test_fail_item_with_retry(self, job_service, worker_service):
        """Test item failure with retry."""
        config = JobConfig(
            orchestrator_agent="fail_orch",
            worker_agent="fail_worker",
            task="fail_test",
            items=["item"],
            max_retries=3,
        )
        job = job_service.create_job(
            config=config,
            orchestrator_instance_id="fail_orch_1",
        )

        # Claim and fail
        claimed = worker_service.claim_item(job.id, "worker_fail")
        assert claimed is not None

        result = worker_service.fail_item(claimed.id, "Test error", retry=True)
        assert result is True

        # Item should be available for retry
        reclaimed = worker_service.claim_item(job.id, "worker_fail_2")
        assert reclaimed is not None
        assert reclaimed.retry_count > 0


# =====================
# Blackboard Service Tests
# =====================


class TestBlackboardService:
    """Tests for Redis blackboard."""

    def test_set_get(self, blackboard_service):
        """Test basic set and get."""
        key = f"test_key_{uuid4().hex[:8]}"
        value = {"foo": "bar", "count": 42}

        blackboard_service.set(key, value)
        result = blackboard_service.get(key)

        assert result == value

        # Cleanup
        blackboard_service.delete(key)

    def test_set_with_ttl(self, blackboard_service):
        """Test set with TTL."""
        key = f"ttl_key_{uuid4().hex[:8]}"

        blackboard_service.set(key, "temporary", ttl=1)

        # Should exist
        assert blackboard_service.get(key) == "temporary"

        # Wait for expiry
        time.sleep(1.5)
        assert blackboard_service.get(key) is None

    def test_increment(self, blackboard_service):
        """Test atomic increment."""
        key = f"counter_{uuid4().hex[:8]}"

        # Initialize
        blackboard_service.set(key, 0)

        # Increment
        new_val = blackboard_service.increment(key, 5)
        assert new_val == 5

        new_val = blackboard_service.increment(key, 3)
        assert new_val == 8

        # Cleanup
        blackboard_service.delete(key)

    def test_lock_acquire_release(self, blackboard_service):
        """Test distributed lock."""
        lock_key = f"lock_{uuid4().hex[:8]}"
        holder = "test_holder"

        # Acquire
        result = blackboard_service.acquire_lock(lock_key, holder, ttl=30)
        assert result.acquired is True

        # Try to acquire again (should fail)
        result2 = blackboard_service.acquire_lock(lock_key, "other_holder", ttl=30)
        assert result2.acquired is False
        assert result2.holder == holder

        # Release
        released = blackboard_service.release_lock(lock_key, holder)
        assert released is True

        # Now another can acquire
        result3 = blackboard_service.acquire_lock(lock_key, "other_holder", ttl=30)
        assert result3.acquired is True

        # Cleanup
        blackboard_service.release_lock(lock_key, "other_holder")

    def test_scan_pattern(self, blackboard_service):
        """Test pattern scan."""
        prefix = f"scan_test_{uuid4().hex[:8]}"

        # Set multiple keys
        for i in range(5):
            blackboard_service.set(f"{prefix}:item:{i}", {"index": i})

        # Scan
        entries = blackboard_service.scan_pattern(f"{prefix}:item:*")
        assert len(entries) == 5

        # Cleanup
        for i in range(5):
            blackboard_service.delete(f"{prefix}:item:{i}")


# =====================
# Registry Service Tests
# =====================


@requires_agents_schema
class TestRegistryService:
    """Tests for agent registry."""

    def test_register_agent(self, registry_service):
        """Test agent registration."""
        agent_id = f"test_agent_{uuid4().hex[:8]}"

        result = registry_service.register(
            agent_id=agent_id,
            capabilities={"skills": ["scrape", "transform"]},
        )

        assert result.success is True
        assert result.instance_id is not None

        # Verify
        agent = registry_service.get_instance(result.instance_id)
        assert agent is not None
        assert agent.status == "running"

    def test_heartbeat(self, registry_service):
        """Test agent heartbeat."""
        result = registry_service.register(agent_id="heartbeat_test")
        assert result.success

        # Send heartbeat
        success = registry_service.heartbeat(result.instance_id)
        assert success is True

        # Check heartbeat was updated
        agent = registry_service.get_instance(result.instance_id)
        assert agent.heartbeat_at is not None

    def test_deregister(self, registry_service):
        """Test agent deregistration."""
        result = registry_service.register(agent_id="deregister_test")
        assert result.success

        # Deregister
        success = registry_service.deregister(result.instance_id)
        assert success is True

        # Check status
        agent = registry_service.get_instance(result.instance_id)
        assert agent.status == "stopped"

    def test_list_instances(self, registry_service):
        """Test listing agent instances."""
        agents = registry_service.list_instances()
        assert isinstance(agents, list)


# =====================
# Message Service Tests
# =====================


@requires_agents_schema
class TestMessageService:
    """Tests for P2P messaging."""

    def test_send_message(self, message_service):
        """Test sending a message."""
        result = message_service.send(
            from_instance_id="sender_1",
            to_instance_id="receiver_1",
            message_type="test",
            payload={"content": "Hello"},
        )

        assert result.success is True
        assert result.message_id is not None

    def test_get_inbox(self, message_service):
        """Test getting inbox messages."""
        # Send a message
        message_service.send(
            from_instance_id="sender_inbox",
            to_instance_id="receiver_inbox",
            message_type="test",
            payload={"test": True},
        )

        # Get inbox
        messages = message_service.get_inbox("receiver_inbox")
        assert isinstance(messages, list)

    def test_mark_read(self, message_service):
        """Test marking message as read."""
        # Send
        result = message_service.send(
            from_instance_id="sender_read",
            to_instance_id="receiver_read",
            message_type="test",
            payload={"test": True},
        )

        # Mark read
        success = message_service.mark_read(result.message_id)
        assert success is True


# =====================
# Skill Tests
# =====================


@requires_agents_schema
class TestAgentSpawnSkill:
    """Tests for agent_spawn skill."""

    def test_spawn_success(self):
        """Test successful agent spawn."""
        skill = AgentSpawnSkill()

        input_data = AgentSpawnInput(
            orchestrator_agent="spawn_test_orch",
            worker_agent="spawn_test_worker",
            task="spawn_test_task",
            items=["a", "b", "c"],
            parallelism=2,
        )

        output = skill.execute(input_data, tenant_id="test_tenant")

        assert output.success is True
        assert output.job_id is not None
        assert output.total_items == 3
        assert output.credits_reserved > 0

    def test_spawn_empty_items_fails(self):
        """Test spawn with empty items fails."""
        skill = AgentSpawnSkill()

        input_data = AgentSpawnInput(
            orchestrator_agent="spawn_fail_orch",
            worker_agent="spawn_fail_worker",
            task="spawn_fail_task",
            items=[],
        )

        output = skill.execute(input_data)

        assert output.success is False
        assert "at least one item" in output.error.lower()


class TestBlackboardSkills:
    """Tests for blackboard skills."""

    def test_read_skill(self, blackboard_service):
        """Test blackboard read skill."""
        # Setup
        key = f"read_skill_test_{uuid4().hex[:8]}"
        blackboard_service.set(key, {"value": 123})

        # Execute skill
        skill = BlackboardReadSkill()
        output = skill.execute(BlackboardReadInput(key=key))

        assert output.success is True
        assert output.found is True
        assert output.value == {"value": 123}

        # Cleanup
        blackboard_service.delete(key)

    def test_write_skill(self, blackboard_service):
        """Test blackboard write skill."""
        key = f"write_skill_test_{uuid4().hex[:8]}"

        skill = BlackboardWriteSkill()
        output = skill.execute(BlackboardWriteInput(key=key, value={"test": True}))

        assert output.success is True

        # Verify
        value = blackboard_service.get(key)
        assert value == {"test": True}

        # Cleanup
        blackboard_service.delete(key)

    def test_lock_skill(self, blackboard_service):
        """Test blackboard lock skill."""
        lock_key = f"lock_skill_test_{uuid4().hex[:8]}"

        skill = BlackboardLockSkill()

        # Acquire
        output = skill.execute(
            BlackboardLockInput(
                key=lock_key,
                holder="test_holder",
                action="acquire",
            )
        )

        assert output.success is True
        assert output.acquired is True

        # Release
        output2 = skill.execute(
            BlackboardLockInput(
                key=lock_key,
                holder="test_holder",
                action="release",
            )
        )

        assert output2.success is True
        assert output2.released is True


# =====================
# Integration Tests
# =====================


@requires_agents_schema
class TestJobWorkflow:
    """Integration tests for complete job workflow."""

    def test_complete_job_workflow(self, job_service, worker_service, blackboard_service):
        """Test complete job workflow: create -> claim -> complete -> check."""
        # Create job
        config = JobConfig(
            orchestrator_agent="workflow_orch",
            worker_agent="workflow_worker",
            task="workflow_test",
            items=["item1", "item2"],
            parallelism=2,
        )
        job = job_service.create_job(
            config=config,
            orchestrator_instance_id="workflow_orch_1",
        )

        # Process all items
        for i in range(2):
            claimed = worker_service.claim_item(job.id, f"worker_{i}")
            assert claimed is not None

            # Store result in blackboard
            blackboard_service.store_result(job.id, claimed.item_index, {"processed": True})

            # Complete
            worker_service.complete_item(claimed.id, {"success": True})

        # Check job completion
        job_service.check_job_completion(job.id)
        final = job_service.get_job(job.id)

        assert final.status == "completed"
        assert final.progress.completed == 2
        assert final.progress.failed == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
