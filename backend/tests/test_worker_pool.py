# Tests for Worker Pool and Runner
# Run with: pytest backend/tests/test_worker_pool.py -v

import pytest


class TestRunRunner:
    """Tests for RunRunner."""

    def test_runner_constructs_without_crashing(self):
        """RunRunner can be constructed with a run_id."""
        # Import here to avoid DB initialization at module load
        import os

        # Set DATABASE_URL for import (won't actually connect in this test)
        os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")

        from app.hoc.int.worker.runner import RunRunner

        # Create runner with test run_id
        runner = RunRunner(run_id="run-test-1")
        assert runner.run_id == "run-test-1"
        assert runner.publisher is not None


class TestWorkerPool:
    """Tests for WorkerPool."""

    def test_pool_constructs_with_default_concurrency(self):
        """WorkerPool constructs with default concurrency."""
        import os

        os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")

        from app.hoc.int.worker.pool import WorkerPool

        pool = WorkerPool()
        assert pool.concurrency == 4  # Default from WORKER_CONCURRENCY
        assert pool._stop.is_set() is False

    def test_pool_constructs_with_custom_concurrency(self):
        """WorkerPool accepts custom concurrency."""
        import os

        os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")

        from app.hoc.int.worker.pool import WorkerPool

        pool = WorkerPool(concurrency=8)
        assert pool.concurrency == 8


class TestEventsPublisher:
    """Tests for events publisher."""

    def test_logging_publisher_works(self):
        """LoggingPublisher can publish events."""
        from app.events.publisher import LoggingPublisher

        publisher = LoggingPublisher()
        # Should not raise
        publisher.publish("test.event", {"key": "value"})

    def test_get_publisher_returns_logging_by_default(self):
        """get_publisher returns LoggingPublisher by default."""
        import os

        # Ensure NATS is not configured
        os.environ.pop("EVENT_PUBLISHER", None)
        os.environ.pop("NATS_URL", None)

        from app.events.publisher import LoggingPublisher, get_publisher

        publisher = get_publisher()
        assert isinstance(publisher, LoggingPublisher)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
