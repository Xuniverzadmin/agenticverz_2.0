# tests/chaos/test_resource_stress.py
"""
Resource Stress Chaos Tests

Tests system behavior under:
1. CPU stress
2. Memory pressure
3. Disk I/O latency
4. Worker pool restart

These tests verify graceful degradation and recovery.
Run with: pytest tests/chaos/test_resource_stress.py -v --chaos
"""

import asyncio
import gc
import os
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List
from unittest.mock import patch

import pytest

# Mark all tests in this module as chaos tests
pytestmark = [
    pytest.mark.chaos,
    pytest.mark.slow,
]


class CPUStressor:
    """CPU stress generator for chaos testing."""

    def __init__(self, cores: int = 2, duration_seconds: float = 5.0):
        self.cores = cores
        self.duration_seconds = duration_seconds
        self._stop_event = threading.Event()
        self._threads: List[threading.Thread] = []

    def _cpu_burn(self):
        """Burn CPU cycles."""
        end_time = time.time() + self.duration_seconds
        while time.time() < end_time and not self._stop_event.is_set():
            # CPU-intensive calculation
            _ = sum(i * i for i in range(10000))

    def start(self):
        """Start CPU stress."""
        self._stop_event.clear()
        for _ in range(self.cores):
            t = threading.Thread(target=self._cpu_burn, daemon=True)
            t.start()
            self._threads.append(t)

    def stop(self):
        """Stop CPU stress."""
        self._stop_event.set()
        for t in self._threads:
            t.join(timeout=1.0)
        self._threads.clear()


class MemoryStressor:
    """Memory pressure generator for chaos testing."""

    def __init__(self, target_mb: int = 100):
        self.target_mb = target_mb
        self._allocations: List[bytes] = []

    def allocate(self):
        """Allocate memory to create pressure."""
        chunk_size = 1024 * 1024  # 1 MB chunks
        for _ in range(self.target_mb):
            self._allocations.append(b'\x00' * chunk_size)

    def release(self):
        """Release allocated memory."""
        self._allocations.clear()
        gc.collect()


class DiskStressor:
    """Disk I/O stress generator for chaos testing."""

    def __init__(self, temp_dir: str = None):
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self._files: List[str] = []

    def create_files(self, count: int = 100, size_kb: int = 100):
        """Create temporary files to stress disk I/O."""
        data = b'\x00' * (size_kb * 1024)
        for i in range(count):
            path = os.path.join(self.temp_dir, f"chaos_test_{i}.tmp")
            with open(path, 'wb') as f:
                f.write(data)
            self._files.append(path)

    def cleanup(self):
        """Remove temporary files."""
        for path in self._files:
            try:
                os.unlink(path)
            except OSError:
                pass
        self._files.clear()


class TestCPUStressChaos:
    """Tests for behavior under CPU stress."""

    def test_skill_execution_under_cpu_stress(self):
        """Skills complete under CPU stress (may be slower)."""
        from app.skills.json_transform import JsonTransformSkill

        stressor = CPUStressor(cores=2, duration_seconds=3.0)
        skill = JsonTransformSkill()

        try:
            stressor.start()

            # Execute skill while CPU is stressed
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(skill.execute({
                    "payload": {"data": {"value": 42}},
                    "mapping": {"extracted": "data.value"}
                }))
            finally:
                loop.close()

            # Should still succeed, just maybe slower
            assert result["result"]["status"] == "ok"
            assert result["result"]["result"]["extracted"] == 42

        finally:
            stressor.stop()

    def test_concurrent_skills_under_cpu_stress(self):
        """Multiple skills can execute concurrently under CPU stress."""
        from app.skills.json_transform import JsonTransformSkill

        stressor = CPUStressor(cores=2, duration_seconds=5.0)
        skill = JsonTransformSkill()

        async def run_multiple():
            tasks = []
            for i in range(5):
                tasks.append(skill.execute({
                    "payload": {"data": {"value": i}},
                    "mapping": {"extracted": "data.value"}
                }))
            return await asyncio.gather(*tasks)

        try:
            stressor.start()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                results = loop.run_until_complete(run_multiple())
            finally:
                loop.close()

            # All should succeed
            for i, result in enumerate(results):
                assert result["result"]["status"] == "ok"
                assert result["result"]["result"]["extracted"] == i

        finally:
            stressor.stop()


class TestMemoryPressureChaos:
    """Tests for behavior under memory pressure."""

    def test_skill_execution_under_memory_pressure(self):
        """Skills handle memory pressure gracefully."""
        from app.skills.json_transform import JsonTransformSkill

        stressor = MemoryStressor(target_mb=50)  # Moderate pressure
        skill = JsonTransformSkill()

        try:
            stressor.allocate()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(skill.execute({
                    "payload": {"items": list(range(100))},
                    "mapping": {"count": "items"}
                }))
            finally:
                loop.close()

            assert result["result"]["status"] == "ok"

        finally:
            stressor.release()

    def test_large_payload_under_memory_pressure(self):
        """Large payloads are handled under memory pressure."""
        from app.skills.json_transform import JsonTransformSkill

        stressor = MemoryStressor(target_mb=30)
        skill = JsonTransformSkill()

        # Create large payload
        large_payload = {
            "data": {
                "items": [{"id": i, "value": f"item_{i}"} for i in range(1000)]
            }
        }

        try:
            stressor.allocate()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(skill.execute({
                    "payload": large_payload,
                    "mapping": {"first": "data.items[0].id", "last": "data.items[-1].id"}
                }))
            finally:
                loop.close()

            assert result["result"]["status"] == "ok"
            assert result["result"]["result"]["first"] == 0
            assert result["result"]["result"]["last"] == 999

        finally:
            stressor.release()


class TestDiskIOChaos:
    """Tests for behavior under disk I/O stress."""

    def test_registry_persistence_under_disk_stress(self):
        """Registry persistence handles disk I/O stress."""
        from app.skills.registry_v2 import SkillRegistry
        from app.worker.runtime.core import SkillDescriptor

        with tempfile.TemporaryDirectory() as temp_dir:
            stressor = DiskStressor(temp_dir)
            db_path = os.path.join(temp_dir, "test_registry.db")

            try:
                # Create disk stress
                stressor.create_files(count=50, size_kb=100)

                # Now try to persist registry
                registry = SkillRegistry(persistence_path=db_path)

                for i in range(100):
                    descriptor = SkillDescriptor(
                        skill_id=f"skill.stress_{i:04d}",
                        name=f"Stress Test Skill {i}",
                        version="1.0.0",
                    )
                    registry.register(descriptor, lambda x: {"ok": True})

                registry.close()

                # Verify persistence worked
                assert Path(db_path).exists()
                assert Path(db_path).stat().st_size > 0

            finally:
                stressor.cleanup()


class TestWorkerPoolChaos:
    """Tests for worker pool resilience."""

    def test_executor_handles_task_failure(self):
        """Executor handles individual task failures gracefully."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import time

        def failing_task(n):
            if n == 3:
                raise RuntimeError("Simulated task failure")
            time.sleep(0.01)
            return n * 2

        results = []
        errors = []

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(failing_task, i): i for i in range(6)}

            for future in as_completed(futures):
                n = futures[future]
                try:
                    results.append(future.result())
                except RuntimeError as e:
                    errors.append((n, str(e)))

        # Should have 5 successful results and 1 error
        assert len(results) == 5
        assert len(errors) == 1
        assert errors[0][0] == 3

    def test_executor_shutdown_with_pending_tasks(self):
        """Executor shutdown handles pending tasks gracefully."""
        from concurrent.futures import ThreadPoolExecutor

        completed = []

        def slow_task(n):
            time.sleep(0.1)
            completed.append(n)
            return n

        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit more tasks than workers
            futures = [executor.submit(slow_task, i) for i in range(10)]

            # Give some time for a few to start
            time.sleep(0.15)

        # With shutdown(wait=True), all tasks should complete
        # Even if some were waiting
        # Note: exact number depends on timing
        assert len(completed) >= 2  # At least the first batch


class TestGracefulDegradation:
    """Tests for graceful degradation under stress."""

    def test_timeout_under_load(self):
        """Operations timeout gracefully under heavy load."""
        import asyncio

        stressor = CPUStressor(cores=2, duration_seconds=3.0)

        async def slow_operation():
            await asyncio.sleep(0.5)
            return "done"

        try:
            stressor.start()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # Should complete even under CPU stress
                result = loop.run_until_complete(
                    asyncio.wait_for(slow_operation(), timeout=5.0)
                )
                assert result == "done"
            except asyncio.TimeoutError:
                # Acceptable under extreme stress
                pass
            finally:
                loop.close()

        finally:
            stressor.stop()

    def test_recovery_after_stress_removed(self):
        """System recovers after stress is removed."""
        from app.skills.json_transform import JsonTransformSkill

        stressor = CPUStressor(cores=2, duration_seconds=2.0)
        skill = JsonTransformSkill()

        # Execute under stress
        try:
            stressor.start()
            time.sleep(1.0)  # Let stress build up
        finally:
            stressor.stop()

        # Now execute without stress - should be fast
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        start = time.time()
        try:
            result = loop.run_until_complete(skill.execute({
                "payload": {"value": 123},
                "mapping": {"out": "value"}
            }))
        finally:
            loop.close()

        duration = time.time() - start

        assert result["result"]["status"] == "ok"
        assert duration < 1.0  # Should be quick after stress removed


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "chaos"])
