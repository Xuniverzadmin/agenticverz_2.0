# Checkpoint Store Tests (M4)
"""
Tests for checkpoint store functionality.

Tests:
1. Save and load checkpoints
2. Upsert behavior
3. List running workflows
4. Delete checkpoints
"""

import pytest
import asyncio
from datetime import datetime

from app.workflow.checkpoint import (
    InMemoryCheckpointStore,
    CheckpointData,
)


@pytest.fixture
def store():
    """Create in-memory checkpoint store."""
    return InMemoryCheckpointStore()


class TestInMemoryCheckpointStore:
    """Tests for InMemoryCheckpointStore."""

    @pytest.mark.asyncio
    async def test_save_and_load(self, store):
        """Save checkpoint and load it back."""
        run_id = "test-run-1"

        await store.save(
            run_id=run_id,
            next_step_index=2,
            last_result_hash="abc123",
            step_outputs={"step1": {"value": 1}},
            status="running",
            workflow_id="test-workflow",
        )

        ck = await store.load(run_id)

        assert ck is not None
        assert ck.run_id == run_id
        assert ck.next_step_index == 2
        assert ck.last_result_hash == "abc123"
        assert ck.step_outputs == {"step1": {"value": 1}}
        assert ck.status == "running"
        assert ck.workflow_id == "test-workflow"

    @pytest.mark.asyncio
    async def test_load_nonexistent(self, store):
        """Load returns None for nonexistent run."""
        ck = await store.load("nonexistent-run")
        assert ck is None

    @pytest.mark.asyncio
    async def test_upsert_updates_existing(self, store):
        """Save updates existing checkpoint."""
        run_id = "upsert-run"

        # Initial save
        await store.save(
            run_id=run_id,
            next_step_index=1,
            last_result_hash="hash1",
            status="running",
        )

        # Update
        await store.save(
            run_id=run_id,
            next_step_index=3,
            last_result_hash="hash3",
            status="completed",
        )

        ck = await store.load(run_id)
        assert ck.next_step_index == 3
        assert ck.last_result_hash == "hash3"
        assert ck.status == "completed"

    @pytest.mark.asyncio
    async def test_delete(self, store):
        """Delete removes checkpoint."""
        run_id = "delete-run"

        await store.save(run_id=run_id, next_step_index=1, status="running")
        assert await store.load(run_id) is not None

        result = await store.delete(run_id)
        assert result is True
        assert await store.load(run_id) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, store):
        """Delete returns False for nonexistent run."""
        result = await store.delete("nonexistent-run")
        assert result is False

    @pytest.mark.asyncio
    async def test_list_running(self, store):
        """List returns only running workflows."""
        # Create mixed statuses
        await store.save(run_id="run-1", next_step_index=1, status="running")
        await store.save(run_id="run-2", next_step_index=2, status="completed")
        await store.save(run_id="run-3", next_step_index=3, status="running")
        await store.save(run_id="run-4", next_step_index=4, status="failed")

        running = await store.list_running()

        assert len(running) == 2
        run_ids = {r.run_id for r in running}
        assert "run-1" in run_ids
        assert "run-3" in run_ids
        assert "run-2" not in run_ids

    @pytest.mark.asyncio
    async def test_list_running_limit(self, store):
        """List respects limit parameter."""
        for i in range(10):
            await store.save(run_id=f"run-{i}", next_step_index=i, status="running")

        running = await store.list_running(limit=5)
        assert len(running) == 5

    @pytest.mark.asyncio
    async def test_step_outputs_serialization(self, store):
        """Step outputs survive save/load cycle."""
        run_id = "outputs-run"
        outputs = {
            "step1": {"result": "value", "nested": {"a": 1}},
            "step2": [1, 2, 3],
        }

        await store.save(
            run_id=run_id,
            next_step_index=3,
            step_outputs=outputs,
            status="running",
        )

        ck = await store.load(run_id)
        assert ck.step_outputs == outputs

    @pytest.mark.asyncio
    async def test_content_hash_returned(self, store):
        """Save returns content hash."""
        hash1 = await store.save(
            run_id="hash-run",
            next_step_index=1,
            step_outputs={"a": 1},
            status="running",
        )

        assert hash1 is not None
        assert len(hash1) == 16  # SHA256 truncated to 16 chars

    @pytest.mark.asyncio
    async def test_content_hash_deterministic(self, store):
        """Same inputs produce same content hash."""
        inputs = {
            "run_id": "hash-test",
            "next_step_index": 5,
            "step_outputs": {"x": 1},
            "status": "running",
        }

        store2 = InMemoryCheckpointStore()

        hash1 = await store.save(**inputs)
        hash2 = await store2.save(**inputs)

        assert hash1 == hash2

    @pytest.mark.asyncio
    async def test_timestamps_set(self, store):
        """Timestamps are set on save."""
        await store.save(run_id="ts-run", next_step_index=1, status="running")

        ck = await store.load("ts-run")
        assert ck.created_at is not None
        assert ck.updated_at is not None
        assert isinstance(ck.created_at, datetime)

    @pytest.mark.asyncio
    async def test_update_preserves_created_at(self, store):
        """Update preserves original created_at."""
        await store.save(run_id="preserve-run", next_step_index=1, status="running")
        ck1 = await store.load("preserve-run")
        created1 = ck1.created_at

        # Small delay and update
        await asyncio.sleep(0.01)
        await store.save(run_id="preserve-run", next_step_index=2, status="running")
        ck2 = await store.load("preserve-run")

        assert ck2.created_at == created1
        assert ck2.updated_at > ck2.created_at


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
