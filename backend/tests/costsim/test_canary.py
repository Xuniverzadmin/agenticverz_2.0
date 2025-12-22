# Tests for Canary Runner
"""
Test suite for the daily canary runner.

Tests leader election integration and circuit breaker reporting.
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


class TestCanaryRunnerConfig:
    """Tests for CanaryRunConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        from app.costsim.canary import CanaryRunConfig

        config = CanaryRunConfig()

        assert config.sample_count == 100
        assert config.max_runtime_seconds == 300
        assert config.parallel_workers == 4
        assert config.drift_threshold == 0.2
        assert config.require_leader_lock is True
        assert config.use_async_circuit_breaker is True

    def test_custom_config(self):
        """Test custom configuration values."""
        from app.costsim.canary import CanaryRunConfig

        config = CanaryRunConfig(
            sample_count=50,
            drift_threshold=0.15,
            require_leader_lock=False,
        )

        assert config.sample_count == 50
        assert config.drift_threshold == 0.15
        assert config.require_leader_lock is False


class TestCanarySample:
    """Tests for CanarySample."""

    def test_canary_sample_creation(self):
        """Test creating a canary sample."""
        from app.costsim.canary import CanarySample

        sample = CanarySample(
            id="sample_1",
            plan=[{"skill": "http_call", "params": {"url": "https://api.example.com"}}],
            budget_cents=100,
        )

        assert sample.id == "sample_1"
        assert len(sample.plan) == 1
        assert sample.budget_cents == 100
        assert sample.expected_cost_cents is None


class TestCanaryRunnerWithMock:
    """Tests using mocked dependencies."""

    @pytest.mark.asyncio
    async def test_run_skips_when_not_leader(self):
        """Test that canary run skips when we're not the leader."""
        with patch("app.costsim.canary.leader_election") as mock_election:
            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = False  # Not the leader
            mock_cm.__aexit__.return_value = None
            mock_election.return_value = mock_cm

            from app.costsim.canary import CanaryRunConfig, CanaryRunner

            config = CanaryRunConfig(require_leader_lock=True)
            runner = CanaryRunner(config)

            report = await runner.run()

            assert report.status == "skipped"
            assert report.passed is True  # Skipped is not a failure
            assert "another instance is the leader" in report.failure_reasons[0]

    @pytest.mark.asyncio
    async def test_run_executes_when_leader(self):
        """Test that canary run executes when we're the leader."""
        from app.costsim.canary import CanaryReport, CanaryRunConfig, CanaryRunner

        with patch("app.costsim.canary.leader_election") as mock_election:
            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = True  # We are the leader
            mock_cm.__aexit__.return_value = None
            mock_election.return_value = mock_cm

            mock_report = CanaryReport(
                run_id="test_run",
                timestamp=datetime.now(timezone.utc),
                status="pass",
                total_samples=10,
                matching_samples=10,
                minor_drift_samples=0,
                major_drift_samples=0,
                median_cost_diff=0.0,
                p90_cost_diff=0.0,
                kl_divergence=0.0,
                outlier_count=0,
                passed=True,
                failure_reasons=[],
            )

            with patch.object(CanaryRunner, "_run_internal", new_callable=AsyncMock) as mock_internal:
                mock_internal.return_value = mock_report

                config = CanaryRunConfig(require_leader_lock=True)
                runner = CanaryRunner(config)

                report = await runner.run()

                mock_internal.assert_called_once()
                assert report.status == "pass"

    @pytest.mark.asyncio
    async def test_run_without_leader_election(self):
        """Test canary run without leader election requirement."""
        from app.costsim.canary import CanaryReport, CanaryRunConfig, CanaryRunner

        mock_report = CanaryReport(
            run_id="test_run",
            timestamp=datetime.now(timezone.utc),
            status="pass",
            total_samples=10,
            matching_samples=10,
            minor_drift_samples=0,
            major_drift_samples=0,
            median_cost_diff=0.0,
            p90_cost_diff=0.0,
            kl_divergence=0.0,
            outlier_count=0,
            passed=True,
            failure_reasons=[],
        )

        with patch.object(CanaryRunner, "_run_internal", new_callable=AsyncMock) as mock_internal:
            mock_internal.return_value = mock_report

            config = CanaryRunConfig(require_leader_lock=False)
            runner = CanaryRunner(config)

            report = await runner.run()

            mock_internal.assert_called_once()
            assert report.status == "pass"


class TestCanaryMetricsCalculation:
    """Tests for metrics calculation."""

    def test_calculate_metrics_empty_comparisons(self):
        """Test metrics calculation with no comparisons."""
        from app.costsim.canary import CanaryRunConfig, CanaryRunner

        config = CanaryRunConfig()
        runner = CanaryRunner(config)

        metrics = runner._calculate_metrics([])

        assert metrics["matching_count"] == 0
        assert metrics["kl_divergence"] == 0.0
        assert metrics["outlier_count"] == 0

    def test_calculate_metrics_with_comparisons(self):
        """Test metrics calculation with comparisons."""
        from app.costsim.canary import CanaryRunConfig, CanaryRunner
        from app.costsim.models import ComparisonResult, ComparisonVerdict

        config = CanaryRunConfig()
        runner = CanaryRunner(config)

        # Create mock comparisons
        comparisons = [
            ComparisonResult(
                verdict=ComparisonVerdict.MATCH,
                v1_cost_cents=100,
                v2_cost_cents=100,
                cost_delta_cents=0,
                cost_delta_pct=0.0,
                v1_duration_ms=100,
                v2_duration_ms=100,
                duration_delta_ms=0,
                v1_feasible=True,
                v2_feasible=True,
                feasibility_match=True,
                drift_score=0.0,
            ),
            ComparisonResult(
                verdict=ComparisonVerdict.MINOR_DRIFT,
                v1_cost_cents=100,
                v2_cost_cents=105,
                cost_delta_cents=5,
                cost_delta_pct=0.05,
                v1_duration_ms=100,
                v2_duration_ms=110,
                duration_delta_ms=10,
                v1_feasible=True,
                v2_feasible=True,
                feasibility_match=True,
                drift_score=0.05,
            ),
            ComparisonResult(
                verdict=ComparisonVerdict.MAJOR_DRIFT,
                v1_cost_cents=100,
                v2_cost_cents=150,
                cost_delta_cents=50,
                cost_delta_pct=0.50,
                v1_duration_ms=100,
                v2_duration_ms=200,
                duration_delta_ms=100,
                v1_feasible=True,
                v2_feasible=True,
                feasibility_match=True,
                drift_score=0.55,
            ),
        ]

        metrics = runner._calculate_metrics(comparisons)

        assert metrics["matching_count"] == 1
        assert metrics["minor_drift_count"] == 1
        assert metrics["major_drift_count"] == 1
        assert metrics["outlier_count"] == 1  # drift > 0.5


class TestCanaryEvaluation:
    """Tests for pass/fail evaluation."""

    def test_evaluate_results_pass(self):
        """Test evaluation that passes."""
        from app.costsim.canary import CanaryRunConfig, CanaryRunner

        config = CanaryRunConfig(drift_threshold=0.2, outlier_max_pct=0.05)
        runner = CanaryRunner(config)

        metrics = {
            "matching_count": 90,
            "minor_drift_count": 8,
            "major_drift_count": 2,
            "kl_divergence": 0.1,
            "outlier_count": 2,
        }

        passed, reasons = runner._evaluate_results(metrics, None)

        assert passed is True
        assert len(reasons) == 0

    def test_evaluate_results_fail_kl_divergence(self):
        """Test evaluation fails on high KL divergence."""
        from app.costsim.canary import CanaryRunConfig, CanaryRunner

        config = CanaryRunConfig(drift_threshold=0.2)
        runner = CanaryRunner(config)

        metrics = {
            "matching_count": 90,
            "minor_drift_count": 8,
            "major_drift_count": 2,
            "kl_divergence": 0.5,  # Above threshold
            "outlier_count": 2,
        }

        passed, reasons = runner._evaluate_results(metrics, None)

        assert passed is False
        assert "KL divergence" in reasons[0]

    def test_evaluate_results_fail_outlier_percentage(self):
        """Test evaluation fails on high outlier percentage."""
        from app.costsim.canary import CanaryRunConfig, CanaryRunner

        config = CanaryRunConfig(outlier_max_pct=0.05)
        runner = CanaryRunner(config)

        metrics = {
            "matching_count": 80,
            "minor_drift_count": 10,
            "major_drift_count": 10,
            "kl_divergence": 0.1,
            "outlier_count": 10,  # 10% outliers
        }

        passed, reasons = runner._evaluate_results(metrics, None)

        assert passed is False
        assert "Outlier percentage" in reasons[0]


class TestKLDivergence:
    """Tests for KL divergence calculation."""

    def test_approximate_kl_divergence_identical(self):
        """Test KL divergence is 0 for identical distributions."""
        from app.costsim.canary import CanaryRunConfig, CanaryRunner

        config = CanaryRunConfig()
        runner = CanaryRunner(config)

        p = [100, 100, 100, 100, 100]
        q = [100, 100, 100, 100, 100]

        kl = runner._approximate_kl_divergence(p, q)

        assert kl == 0.0

    def test_approximate_kl_divergence_different(self):
        """Test KL divergence is positive for different distributions."""
        from app.costsim.canary import CanaryRunConfig, CanaryRunner

        config = CanaryRunConfig()
        runner = CanaryRunner(config)

        p = [100, 100, 100, 100, 100]
        q = [50, 150, 75, 125, 100]

        kl = runner._approximate_kl_divergence(p, q)

        assert kl > 0.0

    def test_approximate_kl_divergence_empty(self):
        """Test KL divergence handles empty lists."""
        from app.costsim.canary import CanaryRunConfig, CanaryRunner

        config = CanaryRunConfig()
        runner = CanaryRunner(config)

        kl = runner._approximate_kl_divergence([], [])

        assert kl == 0.0


class TestSyntheticSamples:
    """Tests for synthetic sample generation."""

    def test_generate_synthetic_samples(self):
        """Test synthetic sample generation."""
        from app.costsim.canary import CanaryRunConfig, CanaryRunner

        config = CanaryRunConfig()
        runner = CanaryRunner(config)

        samples = runner._generate_synthetic_samples()

        assert len(samples) >= 4
        for sample in samples:
            assert sample.id is not None
            assert sample.plan is not None
            assert sample.budget_cents > 0
