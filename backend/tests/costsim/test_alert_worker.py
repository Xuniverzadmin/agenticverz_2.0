# Tests for Alert Worker
"""
Test suite for the reliable alert delivery worker.

Requires PostgreSQL with the costsim_alert_queue table.
"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch, MagicMock

import pytest_asyncio


# Skip if dependencies not available
pytest.importorskip("asyncpg")
pytest.importorskip("httpx")


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


class TestAlertWorkerWithMock:
    """Tests using mocked database and HTTP client."""

    @pytest.mark.asyncio
    async def test_process_batch_no_pending_alerts(self):
        """Test process_batch returns 0 when no pending alerts."""
        with patch("app.costsim.alert_worker.async_session_context") as mock_ctx:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value = []
            mock_session.execute.return_value = mock_result
            mock_session.commit = AsyncMock()

            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.return_value.__aexit__ = AsyncMock()

            from app.costsim.alert_worker import AlertWorker

            worker = AlertWorker(alertmanager_url="http://localhost:9093")
            processed = await worker.process_batch()

            assert processed == 0

    @pytest.mark.asyncio
    async def test_process_batch_sends_alert_successfully(self):
        """Test successful alert delivery."""
        with patch("app.costsim.alert_worker.async_session_context") as mock_ctx:
            # Create mock alert
            mock_alert = MagicMock()
            mock_alert.id = 1
            mock_alert.alert_type = "disable"
            mock_alert.payload = [{"alertname": "test"}]
            mock_alert.incident_id = None
            mock_alert.status = "pending"
            mock_alert.attempts = 0
            mock_alert.max_attempts = 10

            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value = [mock_alert]
            mock_session.execute.return_value = mock_result
            mock_session.commit = AsyncMock()

            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.return_value.__aexit__ = AsyncMock()

            # Mock HTTP client
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_client.post.return_value = mock_response
                mock_client.is_closed = False
                mock_client_cls.return_value = mock_client

                from app.costsim.alert_worker import AlertWorker

                worker = AlertWorker(alertmanager_url="http://localhost:9093")
                worker._client = mock_client
                processed = await worker.process_batch()

                assert processed == 1
                assert mock_alert.status == "sent"
                mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_batch_retries_on_failure(self):
        """Test alert retry on HTTP failure."""
        import httpx

        with patch("app.costsim.alert_worker.async_session_context") as mock_ctx:
            # Create mock alert
            mock_alert = MagicMock()
            mock_alert.id = 1
            mock_alert.alert_type = "disable"
            mock_alert.payload = [{"alertname": "test"}]
            mock_alert.incident_id = None
            mock_alert.status = "pending"
            mock_alert.attempts = 0
            mock_alert.max_attempts = 10
            mock_alert.last_error = None

            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value = [mock_alert]
            mock_session.execute.return_value = mock_result
            mock_session.commit = AsyncMock()

            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.return_value.__aexit__ = AsyncMock()

            # Mock HTTP client to fail
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.post.side_effect = httpx.TimeoutException("timeout")
                mock_client.is_closed = False
                mock_client_cls.return_value = mock_client

                from app.costsim.alert_worker import AlertWorker

                worker = AlertWorker(alertmanager_url="http://localhost:9093")
                worker._client = mock_client
                processed = await worker.process_batch()

                assert processed == 1
                assert mock_alert.attempts == 1
                assert mock_alert.status == "pending"  # Still pending for retry
                assert mock_alert.last_error is not None
                assert "Timeout" in mock_alert.last_error

    @pytest.mark.asyncio
    async def test_process_batch_marks_failed_after_max_attempts(self):
        """Test alert marked as failed after max attempts."""
        import httpx

        with patch("app.costsim.alert_worker.async_session_context") as mock_ctx:
            # Create mock alert near max attempts
            mock_alert = MagicMock()
            mock_alert.id = 1
            mock_alert.alert_type = "disable"
            mock_alert.payload = [{"alertname": "test"}]
            mock_alert.incident_id = None
            mock_alert.status = "pending"
            mock_alert.attempts = 9  # One more attempt allowed
            mock_alert.max_attempts = 10
            mock_alert.last_error = None

            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value = [mock_alert]
            mock_session.execute.return_value = mock_result
            mock_session.commit = AsyncMock()

            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.return_value.__aexit__ = AsyncMock()

            # Mock HTTP client to fail
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.post.side_effect = httpx.TimeoutException("timeout")
                mock_client.is_closed = False
                mock_client_cls.return_value = mock_client

                from app.costsim.alert_worker import AlertWorker

                worker = AlertWorker(alertmanager_url="http://localhost:9093")
                worker._client = mock_client
                processed = await worker.process_batch()

                assert processed == 1
                assert mock_alert.attempts == 10
                assert mock_alert.status == "failed"


class TestEnqueueAlert:
    """Tests for enqueue_alert function."""

    @pytest.mark.asyncio
    async def test_enqueue_alert_creates_record(self):
        """Test that enqueue_alert creates a queue record."""
        with patch("app.costsim.alert_worker.AsyncSessionLocal") as mock_session_local:
            mock_session = AsyncMock()
            mock_session.add = MagicMock()
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()
            mock_session.close = AsyncMock()
            mock_session_local.return_value = mock_session

            from app.costsim.alert_worker import enqueue_alert

            payload = [{"alertname": "TestAlert"}]

            alert_id = await enqueue_alert(
                payload=payload,
                alert_type="disable",
                circuit_breaker_name="costsim_v2",
                incident_id="inc_123",
            )

            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()


class TestRetryFailedAlerts:
    """Tests for retry_failed_alerts function."""

    @pytest.mark.asyncio
    async def test_retry_failed_alerts(self):
        """Test that retry_failed_alerts resets failed alerts."""
        with patch("app.costsim.alert_worker.async_session_context") as mock_ctx:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.rowcount = 3
            mock_session.execute.return_value = mock_result
            mock_session.commit = AsyncMock()

            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.return_value.__aexit__ = AsyncMock()

            from app.costsim.alert_worker import retry_failed_alerts

            count = await retry_failed_alerts(max_retries=3)

            assert count == 3


class TestPurgeOldAlerts:
    """Tests for purge_old_alerts function."""

    @pytest.mark.asyncio
    async def test_purge_old_alerts(self):
        """Test that purge_old_alerts deletes old records."""
        with patch("app.costsim.alert_worker.async_session_context") as mock_ctx:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.rowcount = 100
            mock_session.execute.return_value = mock_result
            mock_session.commit = AsyncMock()

            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_ctx.return_value.__aexit__ = AsyncMock()

            from app.costsim.alert_worker import purge_old_alerts

            count = await purge_old_alerts(days=30)

            assert count == 100


class TestAlertWorkerQueueStats:
    """Tests for queue statistics."""

    @pytest.mark.asyncio
    async def test_get_queue_stats(self):
        """Test that get_queue_stats returns correct counts."""
        with patch("app.costsim.alert_worker.async_session_context") as mock_ctx:
            mock_session = AsyncMock()

            # Mock count queries - called once for each status + once for oldest_pending
            count_calls = [10, 100, 5, None]  # pending, sent, failed, oldest_pending
            call_idx = [0]

            def mock_scalar():
                result = count_calls[call_idx[0]]
                call_idx[0] = min(call_idx[0] + 1, len(count_calls) - 1)
                return result

            mock_result = MagicMock()
            mock_result.scalar = mock_scalar
            mock_session.execute = AsyncMock(return_value=mock_result)

            # Create proper async context manager
            mock_cm = AsyncMock()
            mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
            mock_cm.__aexit__ = AsyncMock(return_value=None)
            mock_ctx.return_value = mock_cm

            from app.costsim.alert_worker import AlertWorker

            worker = AlertWorker()
            stats = await worker.get_queue_stats()

            assert "pending" in stats
            assert "sent" in stats
            assert "failed" in stats
            assert stats["pending"] == 10
            assert stats["sent"] == 100
            assert stats["failed"] == 5


class TestAlertWorkerContinuousMode:
    """Tests for continuous worker mode."""

    @pytest.mark.asyncio
    async def test_run_continuous_with_leader_election(self):
        """Test that run_continuous uses leader election."""
        with patch("app.costsim.alert_worker.leader_election") as mock_election:
            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = True
            mock_cm.__aexit__.return_value = None
            mock_election.return_value = mock_cm

            with patch("app.costsim.alert_worker.AlertWorker.process_batch", new_callable=AsyncMock) as mock_batch:
                mock_batch.return_value = 0

                from app.costsim.alert_worker import AlertWorker

                worker = AlertWorker(process_interval_seconds=0.01)

                # Run for a short time
                async def run_briefly():
                    task = asyncio.create_task(worker.run_continuous())
                    await asyncio.sleep(0.05)
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

                await run_briefly()

                # Should have processed at least one batch
                assert mock_batch.call_count >= 1
