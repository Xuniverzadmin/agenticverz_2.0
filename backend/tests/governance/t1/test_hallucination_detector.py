# Layer: L8 — Tests
# Product: system-wide
# Reference: GAP-023, INV-002 (HALLU-INV-001)
"""
Unit tests for GAP-023: Hallucination Detection Service.

Tests the non-blocking hallucination detection service that respects
INV-002 (HALLU-INV-001) invariant.

CRITICAL TEST COVERAGE:
- INV-002: Detection is non-blocking by default
- Blocking only when customer explicitly opts in
- Confidence-based detection
- Multiple indicator types
"""

import pytest
from datetime import datetime


class TestHallucinationDetectorImport:
    """Test module imports."""

    def test_detector_import(self):
        """HallucinationDetector should be importable."""
        from app.services.hallucination import HallucinationDetector

        assert HallucinationDetector is not None

    def test_result_import(self):
        """HallucinationResult should be importable."""
        from app.services.hallucination import HallucinationResult

        assert HallucinationResult is not None

    def test_config_import(self):
        """HallucinationConfig should be importable."""
        from app.services.hallucination import HallucinationConfig

        assert HallucinationConfig is not None

    def test_types_import(self):
        """HallucinationType and HallucinationSeverity should be importable."""
        from app.services.hallucination import (
            HallucinationType,
            HallucinationSeverity,
        )

        assert HallucinationType.FABRICATED_CITATION is not None
        assert HallucinationSeverity.HIGH is not None


class TestINV002Compliance:
    """Test INV-002 (HALLU-INV-001) compliance - Non-blocking by default."""

    def test_default_config_non_blocking(self):
        """Default config MUST have blocking disabled (INV-002)."""
        from app.services.hallucination import HallucinationConfig

        config = HallucinationConfig()

        # INV-002: blocking_enabled MUST be False by default
        assert config.blocking_enabled is False

    def test_detection_non_blocking_by_default(self):
        """Detection result MUST be non-blocking by default (INV-002)."""
        from app.services.hallucination import HallucinationDetector

        detector = HallucinationDetector()

        # Content with potential hallucination (future citation)
        content = "According to Smith (2030), the study found..."

        result = detector.detect(content)

        # INV-002: blocking_recommended MUST be False without opt-in
        assert result.blocking_recommended is False
        assert result.blocking_customer_opted_in is False

    def test_high_confidence_still_non_blocking(self):
        """Even high confidence detection MUST be non-blocking without opt-in."""
        from app.services.hallucination import HallucinationDetector

        detector = HallucinationDetector()

        # Content with clear fabrication (future citation)
        current_year = datetime.now().year
        content = f"According to Smith ({current_year + 5}), the experiment proved..."

        result = detector.detect(content)

        # INV-002: Even high confidence MUST NOT block without opt-in
        assert result.blocking_recommended is False

    def test_blocking_requires_explicit_opt_in(self):
        """Blocking MUST require explicit customer opt-in (INV-002)."""
        from app.services.hallucination import (
            HallucinationDetector,
            HallucinationConfig,
        )

        # Config with blocking enabled
        config = HallucinationConfig(
            blocking_enabled=True,
            blocking_threshold=0.8,
        )
        detector = HallucinationDetector(config)

        # Content with clear hallucination
        current_year = datetime.now().year
        content = f"According to Smith ({current_year + 10}), the results show..."

        # Without opt-in flag, still non-blocking
        result_no_opt_in = detector.detect(content, customer_blocking_opted_in=False)
        assert result_no_opt_in.blocking_recommended is False

        # With opt-in flag AND config enabled, can block
        result_with_opt_in = detector.detect(content, customer_blocking_opted_in=True)
        # May or may not recommend blocking based on confidence, but opt-in is registered
        assert result_with_opt_in.blocking_customer_opted_in is True


class TestHallucinationDetection:
    """Test hallucination detection functionality."""

    def test_detect_future_citation(self):
        """Detector should flag future year citations."""
        from app.services.hallucination import (
            HallucinationDetector,
            HallucinationType,
        )

        detector = HallucinationDetector()
        current_year = datetime.now().year
        content = f"According to Johnson ({current_year + 1}), the study revealed..."

        result = detector.detect(content)

        assert result.detected is True
        assert any(
            i.indicator_type == HallucinationType.FABRICATED_CITATION
            for i in result.indicators
        )

    def test_detect_ancient_citation(self):
        """Detector should flag suspiciously old citations."""
        from app.services.hallucination import (
            HallucinationDetector,
            HallucinationType,
        )

        detector = HallucinationDetector()
        content = "According to Aristotle (150), the theory states..."

        result = detector.detect(content)

        assert any(
            i.indicator_type == HallucinationType.FABRICATED_CITATION
            for i in result.indicators
        )

    def test_clean_content_no_detection(self):
        """Clean content should not trigger detection."""
        from app.services.hallucination import HallucinationDetector

        detector = HallucinationDetector()
        content = "The quick brown fox jumps over the lazy dog."

        result = detector.detect(content)

        assert result.detected is False
        assert result.overall_confidence == 0.0

    def test_content_hash_generated(self):
        """Detection result should include content hash."""
        from app.services.hallucination import HallucinationDetector

        detector = HallucinationDetector()
        content = "Some test content."

        result = detector.detect(content)

        assert result.content_hash is not None
        assert len(result.content_hash) == 64  # SHA256 hex

    def test_checked_at_timestamp(self):
        """Detection result should include timestamp."""
        from app.services.hallucination import HallucinationDetector
        from datetime import timezone

        before = datetime.now(timezone.utc)
        detector = HallucinationDetector()
        result = detector.detect("Test content")
        after = datetime.now(timezone.utc)

        assert result.checked_at is not None
        assert before <= result.checked_at <= after


class TestHallucinationResult:
    """Test HallucinationResult dataclass."""

    def test_to_incident_data(self):
        """to_incident_data should return correct structure."""
        from app.services.hallucination import (
            HallucinationResult,
            HallucinationIndicator,
            HallucinationType,
            HallucinationSeverity,
        )

        result = HallucinationResult(
            detected=True,
            overall_confidence=0.75,
            indicators=[
                HallucinationIndicator(
                    indicator_type=HallucinationType.FABRICATED_CITATION,
                    description="Test",
                    confidence=0.8,
                    evidence="evidence text",
                    severity=HallucinationSeverity.MEDIUM,
                )
            ],
            blocking_recommended=False,
            blocking_customer_opted_in=False,
            content_hash="abc123",
        )

        incident_data = result.to_incident_data()

        assert incident_data["category"] == "HALLUCINATION"
        assert incident_data["blocking"] is False  # INV-002
        assert incident_data["confidence"] == 0.75
        assert len(incident_data["indicators"]) == 1

    def test_incident_data_blocking_follows_opt_in(self):
        """to_incident_data blocking MUST follow opt-in status (INV-002)."""
        from app.services.hallucination import HallucinationResult

        # Not opted in
        result_no_opt_in = HallucinationResult(
            detected=True,
            overall_confidence=0.95,  # High confidence
            blocking_recommended=True,  # Even if recommended
            blocking_customer_opted_in=False,  # Not opted in
            content_hash="abc",
        )
        assert result_no_opt_in.to_incident_data()["blocking"] is False

        # Opted in
        result_opted_in = HallucinationResult(
            detected=True,
            overall_confidence=0.95,
            blocking_recommended=True,
            blocking_customer_opted_in=True,  # Opted in
            content_hash="abc",
        )
        assert result_opted_in.to_incident_data()["blocking"] is True


class TestHallucinationIndicator:
    """Test HallucinationIndicator dataclass."""

    def test_indicator_to_dict(self):
        """Indicator to_dict should return correct structure."""
        from app.services.hallucination import (
            HallucinationIndicator,
            HallucinationType,
            HallucinationSeverity,
        )

        indicator = HallucinationIndicator(
            indicator_type=HallucinationType.INVALID_URL,
            description="Suspicious URL detected",
            confidence=0.7,
            evidence="https://fake.example/test",
            severity=HallucinationSeverity.MEDIUM,
        )

        data = indicator.to_dict()

        assert data["indicator_type"] == "invalid_url"
        assert data["confidence"] == 0.7
        assert data["severity"] == "medium"

    def test_evidence_truncated(self):
        """Long evidence should be truncated in to_dict."""
        from app.services.hallucination import (
            HallucinationIndicator,
            HallucinationType,
            HallucinationSeverity,
        )

        long_evidence = "x" * 1000

        indicator = HallucinationIndicator(
            indicator_type=HallucinationType.UNKNOWN,
            description="Test",
            confidence=0.5,
            evidence=long_evidence,
            severity=HallucinationSeverity.LOW,
        )

        data = indicator.to_dict()

        assert len(data["evidence"]) == 500  # Truncated


class TestHallucinationConfig:
    """Test HallucinationConfig dataclass."""

    def test_default_values(self):
        """Default config should have expected values."""
        from app.services.hallucination import HallucinationConfig

        config = HallucinationConfig()

        assert config.minimum_confidence == 0.6
        assert config.blocking_enabled is False  # INV-002
        assert config.blocking_threshold == 0.9
        assert config.max_content_length == 50000

    def test_custom_values(self):
        """Config should accept custom values."""
        from app.services.hallucination import HallucinationConfig

        config = HallucinationConfig(
            minimum_confidence=0.7,
            blocking_enabled=True,  # Customer opt-in
            blocking_threshold=0.95,
        )

        assert config.minimum_confidence == 0.7
        assert config.blocking_enabled is True
        assert config.blocking_threshold == 0.95


class TestCreateDetectorForTenant:
    """Test tenant-specific detector creation."""

    def test_create_default_detector(self):
        """create_detector_for_tenant with no config should be non-blocking."""
        from app.services.hallucination import create_detector_for_tenant

        detector = create_detector_for_tenant()

        # INV-002: Default must be non-blocking
        assert detector.config.blocking_enabled is False

    def test_create_with_tenant_config(self):
        """create_detector_for_tenant should apply tenant config."""
        from app.services.hallucination import create_detector_for_tenant

        tenant_config = {
            "hallucination_blocking_enabled": True,  # Tenant opted in
            "hallucination_blocking_threshold": 0.85,
            "hallucination_min_confidence": 0.7,
        }

        detector = create_detector_for_tenant(tenant_config)

        assert detector.config.blocking_enabled is True
        assert detector.config.blocking_threshold == 0.85
        assert detector.config.minimum_confidence == 0.7

    def test_create_without_blocking_opt_in(self):
        """Tenant without explicit opt-in should not have blocking."""
        from app.services.hallucination import create_detector_for_tenant

        # Tenant config without blocking opt-in
        tenant_config = {
            "hallucination_min_confidence": 0.5,
            # Note: hallucination_blocking_enabled not set
        }

        detector = create_detector_for_tenant(tenant_config)

        # INV-002: No explicit opt-in means blocking disabled
        assert detector.config.blocking_enabled is False
