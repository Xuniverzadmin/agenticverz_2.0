"""
Drift Detector Tests - M7 Implementation

Tests for drift detection between baseline and memory-enabled traces.

Run with:
    pytest tests/memory/test_drift_detector.py -v
"""


import pytest

# Import drift detector components
from app.memory.drift_detector import (
    DriftDetector,
    DriftPoint,
    DriftResult,
    ExecutionTrace,
    TraceStep,
    get_drift_detector,
    init_drift_detector,
)


class TestTraceStep:
    """Tests for TraceStep dataclass."""

    def test_create_trace_step(self):
        """Test creating a TraceStep."""
        step = TraceStep(
            index=0,
            skill="http_call",
            params={"url": "https://api.example.com"},
            result={"status": 200},
            status="completed",
            duration_ms=150.5,
        )
        assert step.index == 0
        assert step.skill == "http_call"
        assert step.params["url"] == "https://api.example.com"
        assert step.result["status"] == 200
        assert step.status == "completed"
        assert step.duration_ms == 150.5

    def test_trace_step_defaults(self):
        """Test TraceStep default values."""
        step = TraceStep(
            index=0,
            skill="test_skill",
            params={},
        )
        assert step.result is None
        assert step.status == "completed"
        assert step.duration_ms == 0.0
        assert step.timestamp is None


class TestExecutionTrace:
    """Tests for ExecutionTrace dataclass."""

    def test_create_execution_trace(self):
        """Test creating an ExecutionTrace."""
        steps = [
            TraceStep(index=0, skill="skill1", params={}),
            TraceStep(index=1, skill="skill2", params={}),
        ]
        trace = ExecutionTrace(
            workflow_id="wf-123",
            agent_id="agent-1",
            steps=steps,
            final_state={"completed": True},
            memory_enabled=True,
            memory_context={"key": "value"},
        )
        assert trace.workflow_id == "wf-123"
        assert trace.agent_id == "agent-1"
        assert len(trace.steps) == 2
        assert trace.final_state["completed"] is True
        assert trace.memory_enabled is True

    def test_execution_trace_defaults(self):
        """Test ExecutionTrace default values."""
        trace = ExecutionTrace(
            workflow_id="wf-test",
            agent_id=None,
            steps=[],
            final_state={},
        )
        assert trace.memory_enabled is False
        assert trace.memory_context is None
        assert trace.metadata == {}


class TestDriftPoint:
    """Tests for DriftPoint dataclass."""

    def test_create_drift_point(self):
        """Test creating a DriftPoint."""
        point = DriftPoint(
            step_index=2,
            field_path="steps[2].result.data",
            baseline_value="original",
            memory_value="modified",
            severity="high",
            category="output",
        )
        assert point.step_index == 2
        assert point.field_path == "steps[2].result.data"
        assert point.baseline_value == "original"
        assert point.memory_value == "modified"
        assert point.severity == "high"
        assert point.category == "output"


class TestDriftResult:
    """Tests for DriftResult dataclass."""

    def test_no_drift_result(self):
        """Test DriftResult with no drift."""
        result = DriftResult(
            has_drift=False,
            drift_score=0.0,
            drift_points=[],
            summary="No drift detected",
            baseline_hash="abc123",
            memory_hash="abc123",
            comparison_time_ms=5.0,
        )
        assert result.has_drift is False
        assert result.drift_score == 0.0
        assert result.severity == "none"

    def test_drift_result_severity(self):
        """Test DriftResult severity property."""
        points = [
            DriftPoint(0, "a", 1, 2, "low", "output"),
            DriftPoint(1, "b", 1, 2, "medium", "output"),
            DriftPoint(2, "c", 1, 2, "high", "output"),
        ]
        result = DriftResult(
            has_drift=True,
            drift_score=25.0,
            drift_points=points,
            summary="Test",
            baseline_hash="abc",
            memory_hash="xyz",
            comparison_time_ms=10.0,
        )
        # Should return highest severity
        assert result.severity == "high"

    def test_drift_result_critical_severity(self):
        """Test DriftResult with critical severity."""
        points = [
            DriftPoint(0, "a", 1, 2, "critical", "behavior"),
        ]
        result = DriftResult(
            has_drift=True,
            drift_score=50.0,
            drift_points=points,
            summary="Test",
            baseline_hash="abc",
            memory_hash="xyz",
            comparison_time_ms=10.0,
        )
        assert result.severity == "critical"


class TestDriftDetectorBasics:
    """Tests for DriftDetector basic functionality."""

    @pytest.fixture
    def detector(self):
        """Create DriftDetector instance."""
        return DriftDetector()

    def test_detector_default_ignored_fields(self, detector):
        """Test detector has default ignored fields."""
        assert "timestamp" in detector._ignored
        assert "duration_ms" in detector._ignored
        assert "request_id" in detector._ignored

    def test_detector_custom_ignored_fields(self):
        """Test detector with custom ignored fields."""
        detector = DriftDetector(ignored_fields={"custom_field"})
        assert "custom_field" in detector._ignored
        assert "timestamp" in detector._ignored  # Still has defaults

    def test_detector_threshold(self):
        """Test detector threshold configuration."""
        detector = DriftDetector(drift_threshold=10.0)
        assert detector._threshold == 10.0


class TestDriftDetectorCompare:
    """Tests for DriftDetector compare functionality."""

    @pytest.fixture
    def detector(self):
        """Create DriftDetector instance."""
        return DriftDetector(drift_threshold=5.0)

    @pytest.fixture
    def baseline_trace(self):
        """Create baseline trace."""
        return ExecutionTrace(
            workflow_id="wf-test",
            agent_id="agent-1",
            steps=[
                TraceStep(
                    index=0,
                    skill="http_call",
                    params={"url": "https://api.example.com"},
                    result={"status": 200, "data": "hello"},
                    status="completed",
                ),
                TraceStep(
                    index=1,
                    skill="transform",
                    params={"type": "json"},
                    result={"output": {"processed": True}},
                    status="completed",
                ),
            ],
            final_state={"success": True, "items": 2},
            memory_enabled=False,
        )

    @pytest.fixture
    def identical_trace(self, baseline_trace):
        """Create trace identical to baseline."""
        return ExecutionTrace(
            workflow_id="wf-test",
            agent_id="agent-1",
            steps=[
                TraceStep(
                    index=0,
                    skill="http_call",
                    params={"url": "https://api.example.com"},
                    result={"status": 200, "data": "hello"},
                    status="completed",
                ),
                TraceStep(
                    index=1,
                    skill="transform",
                    params={"type": "json"},
                    result={"output": {"processed": True}},
                    status="completed",
                ),
            ],
            final_state={"success": True, "items": 2},
            memory_enabled=True,
        )

    def test_compare_identical_traces(self, detector, baseline_trace, identical_trace):
        """Test comparing identical traces shows no drift."""
        result = detector.compare(baseline_trace, identical_trace)

        assert result.has_drift is False
        assert result.drift_score == 0.0
        assert len(result.drift_points) == 0
        assert result.baseline_hash == result.memory_hash

    def test_compare_different_step_count(self, detector, baseline_trace):
        """Test comparing traces with different step counts."""
        memory_trace = ExecutionTrace(
            workflow_id="wf-test",
            agent_id="agent-1",
            steps=[
                TraceStep(index=0, skill="http_call", params={}, status="completed"),
            ],  # Only 1 step instead of 2
            final_state={},
            memory_enabled=True,
        )

        result = detector.compare(baseline_trace, memory_trace)

        assert result.has_drift is True
        # Should have a drift point for step count difference
        step_count_drift = [p for p in result.drift_points if "steps.length" in p.field_path]
        assert len(step_count_drift) == 1
        assert step_count_drift[0].severity == "high"

    def test_compare_different_skill(self, detector, baseline_trace):
        """Test comparing traces with different skills."""
        memory_trace = ExecutionTrace(
            workflow_id="wf-test",
            agent_id="agent-1",
            steps=[
                TraceStep(
                    index=0,
                    skill="different_skill",  # Different skill
                    params={"url": "https://api.example.com"},
                    result={"status": 200, "data": "hello"},
                    status="completed",
                ),
                TraceStep(
                    index=1,
                    skill="transform",
                    params={"type": "json"},
                    result={"output": {"processed": True}},
                    status="completed",
                ),
            ],
            final_state={"success": True, "items": 2},
            memory_enabled=True,
        )

        result = detector.compare(baseline_trace, memory_trace)

        assert result.has_drift is True
        skill_drift = [p for p in result.drift_points if ".skill" in p.field_path]
        assert len(skill_drift) == 1
        assert skill_drift[0].severity == "critical"

    def test_compare_different_result(self, detector, baseline_trace):
        """Test comparing traces with different results."""
        memory_trace = ExecutionTrace(
            workflow_id="wf-test",
            agent_id="agent-1",
            steps=[
                TraceStep(
                    index=0,
                    skill="http_call",
                    params={"url": "https://api.example.com"},
                    result={"status": 200, "data": "different"},  # Different data
                    status="completed",
                ),
                TraceStep(
                    index=1,
                    skill="transform",
                    params={"type": "json"},
                    result={"output": {"processed": True}},
                    status="completed",
                ),
            ],
            final_state={"success": True, "items": 2},
            memory_enabled=True,
        )

        result = detector.compare(baseline_trace, memory_trace)

        assert result.has_drift is True
        data_drift = [p for p in result.drift_points if "data" in p.field_path]
        assert len(data_drift) >= 1

    def test_compare_different_final_state(self, detector, baseline_trace):
        """Test comparing traces with different final state."""
        memory_trace = ExecutionTrace(
            workflow_id="wf-test",
            agent_id="agent-1",
            steps=[
                TraceStep(
                    index=0,
                    skill="http_call",
                    params={"url": "https://api.example.com"},
                    result={"status": 200, "data": "hello"},
                    status="completed",
                ),
                TraceStep(
                    index=1,
                    skill="transform",
                    params={"type": "json"},
                    result={"output": {"processed": True}},
                    status="completed",
                ),
            ],
            final_state={"success": False, "items": 5},  # Different final state
            memory_enabled=True,
        )

        result = detector.compare(baseline_trace, memory_trace)

        assert result.has_drift is True


class TestIgnoredFields:
    """Tests for field ignoring during comparison."""

    @pytest.fixture
    def detector(self):
        """Create DriftDetector instance."""
        return DriftDetector()

    def test_timestamp_ignored(self, detector):
        """Test that timestamp fields are ignored."""
        baseline = ExecutionTrace(
            workflow_id="wf-test",
            agent_id=None,
            steps=[
                TraceStep(
                    index=0,
                    skill="test",
                    params={},
                    result={"value": 1, "timestamp": "2024-01-01"},
                    status="completed",
                ),
            ],
            final_state={"timestamp": "2024-01-01"},
            memory_enabled=False,
        )

        memory = ExecutionTrace(
            workflow_id="wf-test",
            agent_id=None,
            steps=[
                TraceStep(
                    index=0,
                    skill="test",
                    params={},
                    result={"value": 1, "timestamp": "2024-01-02"},  # Different timestamp
                    status="completed",
                ),
            ],
            final_state={"timestamp": "2024-01-02"},  # Different timestamp
            memory_enabled=True,
        )

        result = detector.compare(baseline, memory)

        # Should have no drift since only timestamps differ
        assert result.has_drift is False

    def test_custom_ignored_field(self):
        """Test that custom ignored fields are ignored."""
        detector = DriftDetector(ignored_fields={"custom_id"})

        baseline = ExecutionTrace(
            workflow_id="wf-test",
            agent_id=None,
            steps=[
                TraceStep(
                    index=0,
                    skill="test",
                    params={},
                    result={"value": 1, "custom_id": "abc"},
                    status="completed",
                ),
            ],
            final_state={},
            memory_enabled=False,
        )

        memory = ExecutionTrace(
            workflow_id="wf-test",
            agent_id=None,
            steps=[
                TraceStep(
                    index=0,
                    skill="test",
                    params={},
                    result={"value": 1, "custom_id": "xyz"},  # Different custom_id
                    status="completed",
                ),
            ],
            final_state={},
            memory_enabled=True,
        )

        result = detector.compare(baseline, memory)

        assert result.has_drift is False


class TestSeverityClassification:
    """Tests for drift severity classification."""

    @pytest.fixture
    def detector(self):
        """Create DriftDetector instance."""
        return DriftDetector()

    def test_status_field_critical(self, detector):
        """Test status field changes are critical."""
        severity = detector._classify_severity("status", "success", "failed")
        assert severity == "critical"

    def test_error_field_critical(self, detector):
        """Test error field changes are critical."""
        severity = detector._classify_severity("error", None, "Connection failed")
        assert severity == "critical"

    def test_data_field_high(self, detector):
        """Test data field changes are high severity."""
        severity = detector._classify_severity("data", {"a": 1}, {"a": 2})
        assert severity == "high"

    def test_type_change_high(self, detector):
        """Test type changes are high severity."""
        severity = detector._classify_severity("field", "string", 123)
        assert severity == "high"

    def test_large_numeric_drift_high(self, detector):
        """Test large numeric drift is high severity."""
        severity = detector._classify_severity("count", 100, 10)  # 90% change
        assert severity == "high"

    def test_small_numeric_drift_low(self, detector):
        """Test small numeric drift is low severity."""
        severity = detector._classify_severity("count", 100, 95)  # 5% change
        assert severity == "low"


class TestDriftScoring:
    """Tests for drift score calculation."""

    @pytest.fixture
    def detector(self):
        """Create DriftDetector instance."""
        return DriftDetector()

    def test_no_drift_score_zero(self, detector):
        """Test zero score with no drift points."""
        score = detector._calculate_score([])
        assert score == 0.0

    def test_critical_drift_high_score(self, detector):
        """Test critical drift points add 25 to score."""
        points = [
            DriftPoint(0, "path", 1, 2, "critical", "behavior"),
        ]
        score = detector._calculate_score(points)
        assert score == 25.0

    def test_high_drift_score(self, detector):
        """Test high drift points add 10 to score."""
        points = [
            DriftPoint(0, "path", 1, 2, "high", "output"),
        ]
        score = detector._calculate_score(points)
        assert score == 10.0

    def test_medium_drift_score(self, detector):
        """Test medium drift points add 5 to score."""
        points = [
            DriftPoint(0, "path", 1, 2, "medium", "output"),
        ]
        score = detector._calculate_score(points)
        assert score == 5.0

    def test_low_drift_score(self, detector):
        """Test low drift points add 2 to score."""
        points = [
            DriftPoint(0, "path", 1, 2, "low", "output"),
        ]
        score = detector._calculate_score(points)
        assert score == 2.0

    def test_score_capped_at_100(self, detector):
        """Test score is capped at 100."""
        points = [
            DriftPoint(i, f"path{i}", 1, 2, "critical", "behavior")
            for i in range(10)  # 10 * 25 = 250
        ]
        score = detector._calculate_score(points)
        assert score == 100.0


class TestTraceHashing:
    """Tests for trace hash computation."""

    @pytest.fixture
    def detector(self):
        """Create DriftDetector instance."""
        return DriftDetector()

    def test_hash_deterministic(self, detector):
        """Test hash is deterministic for same trace."""
        trace = ExecutionTrace(
            workflow_id="wf-test",
            agent_id=None,
            steps=[
                TraceStep(index=0, skill="test", params={"a": 1}, status="completed"),
            ],
            final_state={"done": True},
            memory_enabled=False,
        )

        hash1 = detector._compute_trace_hash(trace)
        hash2 = detector._compute_trace_hash(trace)

        assert hash1 == hash2

    def test_hash_ignores_timestamp(self, detector):
        """Test hash ignores timestamp fields."""
        trace1 = ExecutionTrace(
            workflow_id="wf-test",
            agent_id=None,
            steps=[
                TraceStep(
                    index=0,
                    skill="test",
                    params={},
                    result={"timestamp": "2024-01-01"},
                    status="completed",
                ),
            ],
            final_state={},
            memory_enabled=False,
        )

        trace2 = ExecutionTrace(
            workflow_id="wf-test",
            agent_id=None,
            steps=[
                TraceStep(
                    index=0,
                    skill="test",
                    params={},
                    result={"timestamp": "2024-12-31"},  # Different timestamp
                    status="completed",
                ),
            ],
            final_state={},
            memory_enabled=False,
        )

        assert detector._compute_trace_hash(trace1) == detector._compute_trace_hash(trace2)

    def test_hash_differs_for_different_content(self, detector):
        """Test hash differs for different trace content."""
        trace1 = ExecutionTrace(
            workflow_id="wf-test",
            agent_id=None,
            steps=[
                TraceStep(index=0, skill="skill_a", params={}, status="completed"),
            ],
            final_state={},
            memory_enabled=False,
        )

        trace2 = ExecutionTrace(
            workflow_id="wf-test",
            agent_id=None,
            steps=[
                TraceStep(index=0, skill="skill_b", params={}, status="completed"),
            ],
            final_state={},
            memory_enabled=False,
        )

        assert detector._compute_trace_hash(trace1) != detector._compute_trace_hash(trace2)


class TestGlobalInstance:
    """Tests for global instance management."""

    def test_get_drift_detector(self):
        """Test get_drift_detector returns instance."""
        import app.memory.drift_detector as drift_mod

        drift_mod._detector = None

        detector = get_drift_detector()
        assert detector is not None
        assert isinstance(detector, DriftDetector)

        # Cleanup
        drift_mod._detector = None

    def test_init_drift_detector(self):
        """Test init_drift_detector with custom config."""
        import app.memory.drift_detector as drift_mod

        drift_mod._detector = None

        detector = init_drift_detector(ignored_fields={"my_field"}, drift_threshold=10.0)

        assert detector is not None
        assert "my_field" in detector._ignored
        assert detector._threshold == 10.0

        # Cleanup
        drift_mod._detector = None


class TestSummaryGeneration:
    """Tests for summary generation."""

    @pytest.fixture
    def detector(self):
        """Create DriftDetector instance."""
        return DriftDetector()

    def test_no_drift_summary(self, detector):
        """Test summary for no drift."""
        summary = detector._generate_summary([], 0.0)
        assert summary == "No drift detected"

    def test_drift_summary_includes_score(self, detector):
        """Test summary includes drift score."""
        points = [
            DriftPoint(0, "path", 1, 2, "high", "output"),
        ]
        summary = detector._generate_summary(points, 10.0)
        assert "10.0/100" in summary
        assert "1 high" in summary

    def test_drift_summary_multiple_severities(self, detector):
        """Test summary with multiple severity levels."""
        points = [
            DriftPoint(0, "a", 1, 2, "critical", "behavior"),
            DriftPoint(1, "b", 1, 2, "high", "output"),
            DriftPoint(2, "c", 1, 2, "high", "output"),
            DriftPoint(3, "d", 1, 2, "low", "timing"),
        ]
        summary = detector._generate_summary(points, 50.0)

        assert "1 critical" in summary
        assert "2 high" in summary
        assert "1 low" in summary
