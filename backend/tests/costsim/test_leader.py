# Tests for Leader Election
"""
Test suite for PostgreSQL advisory lock-based leader election.

Requires PostgreSQL with advisory lock support.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock


# Skip if dependencies not available
pytest.importorskip("asyncpg")


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


class TestLeaderElectionWithMock:
    """Tests using mocked database."""

    @pytest.mark.asyncio
    async def test_try_acquire_leader_lock_success(self):
        """Test successful lock acquisition."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (True,)
        mock_session.execute.return_value = mock_result

        from app.costsim.leader import try_acquire_leader_lock, LOCK_CANARY_RUNNER

        result = await try_acquire_leader_lock(mock_session, LOCK_CANARY_RUNNER)

        assert result is True
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_try_acquire_leader_lock_failure(self):
        """Test failed lock acquisition (another instance holds it)."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (False,)
        mock_session.execute.return_value = mock_result

        from app.costsim.leader import try_acquire_leader_lock, LOCK_CANARY_RUNNER

        result = await try_acquire_leader_lock(mock_session, LOCK_CANARY_RUNNER)

        assert result is False

    @pytest.mark.asyncio
    async def test_release_leader_lock_success(self):
        """Test successful lock release."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (True,)
        mock_session.execute.return_value = mock_result

        from app.costsim.leader import release_leader_lock, LOCK_CANARY_RUNNER

        result = await release_leader_lock(mock_session, LOCK_CANARY_RUNNER)

        assert result is True

    @pytest.mark.asyncio
    async def test_release_leader_lock_not_held(self):
        """Test release when we don't hold the lock."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (False,)
        mock_session.execute.return_value = mock_result

        from app.costsim.leader import release_leader_lock, LOCK_ALERT_WORKER

        result = await release_leader_lock(mock_session, LOCK_ALERT_WORKER)

        assert result is False


class TestLeaderContext:
    """Tests for LeaderContext context manager."""

    @pytest.mark.asyncio
    async def test_leader_context_acquires_lock(self):
        """Test that LeaderContext acquires lock on entry."""
        with patch("app.costsim.leader.AsyncSessionLocal") as mock_session_local:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.fetchone.return_value = (True,)
            mock_session.execute.return_value = mock_result
            mock_session.close = AsyncMock()
            mock_session_local.return_value = mock_session

            from app.costsim.leader import LeaderContext, LOCK_CANARY_RUNNER

            ctx = LeaderContext(LOCK_CANARY_RUNNER)

            async with ctx as is_leader:
                assert is_leader is True
                assert ctx.is_leader is True

            # Session should be closed on exit
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_leader_context_not_leader(self):
        """Test LeaderContext when we don't acquire the lock."""
        with patch("app.costsim.leader.AsyncSessionLocal") as mock_session_local:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.fetchone.return_value = (False,)
            mock_session.execute.return_value = mock_result
            mock_session.close = AsyncMock()
            mock_session_local.return_value = mock_session

            from app.costsim.leader import LeaderContext, LOCK_CANARY_RUNNER

            async with LeaderContext(LOCK_CANARY_RUNNER) as is_leader:
                assert is_leader is False

    @pytest.mark.asyncio
    async def test_leader_context_timeout(self):
        """Test LeaderContext handles timeout."""
        with patch("app.costsim.leader.AsyncSessionLocal") as mock_session_local:
            mock_session = AsyncMock()
            # Make execute hang longer than timeout
            async def slow_execute(*args, **kwargs):
                await asyncio.sleep(10)
                return MagicMock()

            mock_session.execute = slow_execute
            mock_session.close = AsyncMock()
            mock_session_local.return_value = mock_session

            from app.costsim.leader import LeaderContext, LOCK_CANARY_RUNNER

            # Short timeout
            ctx = LeaderContext(LOCK_CANARY_RUNNER, timeout_seconds=0.1)

            async with ctx as is_leader:
                # Should timeout and return False
                assert is_leader is False


class TestLeaderElectionFunction:
    """Tests for leader_election context manager function."""

    @pytest.mark.asyncio
    async def test_leader_election_success(self):
        """Test leader_election function with successful acquisition."""
        with patch("app.costsim.leader.AsyncSessionLocal") as mock_session_local:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.fetchone.return_value = (True,)
            mock_session.execute.return_value = mock_result
            mock_session.close = AsyncMock()
            mock_session_local.return_value = mock_session

            from app.costsim.leader import leader_election, LOCK_CANARY_RUNNER

            async with leader_election(LOCK_CANARY_RUNNER) as is_leader:
                assert is_leader is True

    @pytest.mark.asyncio
    async def test_leader_election_exception_handling(self):
        """Test that leader_election handles exceptions gracefully."""
        with patch("app.costsim.leader.AsyncSessionLocal") as mock_session_local:
            mock_session = AsyncMock()
            mock_session.execute.side_effect = Exception("DB error")
            mock_session.close = AsyncMock()
            mock_session_local.return_value = mock_session

            from app.costsim.leader import leader_election, LOCK_CANARY_RUNNER

            async with leader_election(LOCK_CANARY_RUNNER) as is_leader:
                # Should return False on exception
                assert is_leader is False


class TestWithLeaderLock:
    """Tests for with_leader_lock helper."""

    @pytest.mark.asyncio
    async def test_with_leader_lock_executes_callback(self):
        """Test that callback executes when we're the leader."""
        callback = AsyncMock(return_value="success")

        with patch("app.costsim.leader.leader_election") as mock_election:
            # Mock leader_election to be an async context manager that yields True
            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = True
            mock_cm.__aexit__.return_value = None
            mock_election.return_value = mock_cm

            from app.costsim.leader import with_leader_lock, LOCK_CANARY_RUNNER

            result = await with_leader_lock(LOCK_CANARY_RUNNER, callback, "arg1", key="val")

            assert result == "success"
            callback.assert_called_once_with("arg1", key="val")

    @pytest.mark.asyncio
    async def test_with_leader_lock_skips_callback(self):
        """Test that callback is skipped when we're not the leader."""
        callback = AsyncMock(return_value="success")

        with patch("app.costsim.leader.leader_election") as mock_election:
            # Mock leader_election to yield False
            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = False
            mock_cm.__aexit__.return_value = None
            mock_election.return_value = mock_cm

            from app.costsim.leader import with_leader_lock, LOCK_CANARY_RUNNER

            result = await with_leader_lock(LOCK_CANARY_RUNNER, callback)

            assert result is None
            callback.assert_not_called()


class TestLockConstants:
    """Tests for lock ID constants."""

    def test_lock_ids_are_unique(self):
        """Test that all lock IDs are unique."""
        from app.costsim.leader import (
            LOCK_CANARY_RUNNER,
            LOCK_ALERT_WORKER,
            LOCK_PROVENANCE_ARCHIVER,
            LOCK_BASELINE_BACKFILL,
        )

        lock_ids = [
            LOCK_CANARY_RUNNER,
            LOCK_ALERT_WORKER,
            LOCK_PROVENANCE_ARCHIVER,
            LOCK_BASELINE_BACKFILL,
        ]

        assert len(lock_ids) == len(set(lock_ids)), "Lock IDs must be unique"

    def test_lock_ids_in_expected_range(self):
        """Test that lock IDs are in the 7xxx range."""
        from app.costsim.leader import (
            LOCK_CANARY_RUNNER,
            LOCK_ALERT_WORKER,
            LOCK_PROVENANCE_ARCHIVER,
            LOCK_BASELINE_BACKFILL,
        )

        for lock_id in [LOCK_CANARY_RUNNER, LOCK_ALERT_WORKER,
                        LOCK_PROVENANCE_ARCHIVER, LOCK_BASELINE_BACKFILL]:
            assert 7000 <= lock_id < 8000, f"Lock ID {lock_id} not in 7xxx range"
