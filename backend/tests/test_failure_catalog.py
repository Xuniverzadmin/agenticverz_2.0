# Tests for Failure Catalog (M4.5)
"""
Unit tests for failure catalog loading, matching, and recovery suggestions.
"""

# Add backend to path for imports
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.runtime.failure_catalog import (
    FailureCatalog,
    MatchType,
    get_catalog,
    match_failure,
)


class TestFailureCatalogLoading:
    """Tests for catalog loading."""

    def test_load_default_catalog(self):
        """Test loading default catalog."""
        catalog = FailureCatalog()
        assert catalog.version == "1.0.0"
        assert catalog.error_count >= 50  # M4.5 requires 50+ codes

    def test_catalog_has_all_categories(self):
        """Test catalog has all expected categories."""
        catalog = FailureCatalog()
        expected_categories = [
            "TRANSIENT",
            "PERMANENT",
            "RESOURCE",
            "PERMISSION",
            "VALIDATION",
            "INFRASTRUCTURE",
            "PLANNER",
            "SKILL",
            "DATA",
            "SECURITY",
            "CHECKPOINT",
        ]
        for category in expected_categories:
            assert catalog.get_category(category) is not None, f"Missing category: {category}"

    def test_catalog_has_recovery_modes(self):
        """Test catalog has all recovery modes."""
        catalog = FailureCatalog()
        expected_modes = [
            "RETRY_IMMEDIATE",
            "RETRY_EXPONENTIAL",
            "RETRY_WITH_JITTER",
            "ABORT",
            "ESCALATE",
            "CHECKPOINT_RESTORE",
        ]
        for mode in expected_modes:
            config = catalog.get_recovery_config(mode)
            assert config is not None or mode in ["ABORT", "ESCALATE"], f"Missing recovery mode: {mode}"


class TestCodeMatching:
    """Tests for exact code matching."""

    def test_match_timeout_code(self):
        """Test matching TIMEOUT code."""
        catalog = FailureCatalog()
        result = catalog.match_code("TIMEOUT")

        assert result.matched is True
        assert result.entry is not None
        assert result.entry.code == "TIMEOUT"
        assert result.entry.category == "TRANSIENT"
        assert result.entry.is_retryable is True
        assert result.confidence == 1.0
        assert result.match_type == MatchType.CODE

    def test_match_budget_exceeded_code(self):
        """Test matching BUDGET_EXCEEDED code."""
        catalog = FailureCatalog()
        result = catalog.match_code("BUDGET_EXCEEDED")

        assert result.matched is True
        assert result.entry.code == "BUDGET_EXCEEDED"
        assert result.entry.category == "RESOURCE"
        assert result.entry.is_retryable is False
        assert result.entry.http_status == 402

    def test_match_permission_denied_code(self):
        """Test matching PERMISSION_DENIED code."""
        catalog = FailureCatalog()
        result = catalog.match_code("PERMISSION_DENIED")

        assert result.matched is True
        assert result.entry.code == "PERMISSION_DENIED"
        assert result.entry.category == "PERMISSION"
        assert result.entry.http_status == 403

    def test_match_unknown_code(self):
        """Test matching unknown code returns no match."""
        catalog = FailureCatalog()
        result = catalog.match_code("TOTALLY_FAKE_ERROR_CODE")

        assert result.matched is False
        assert result.entry is None
        assert result.confidence == 0.0

    def test_case_insensitive_code_match(self):
        """Test code matching is case insensitive."""
        catalog = FailureCatalog()

        result_upper = catalog.match_code("TIMEOUT")
        result_lower = catalog.match_code("timeout")
        result_mixed = catalog.match_code("TimeOut")

        assert result_upper.matched is True
        assert result_lower.matched is True
        assert result_mixed.matched is True


class TestMessageMatching:
    """Tests for message-based matching."""

    def test_match_timeout_message(self):
        """Test matching timeout in message."""
        catalog = FailureCatalog()
        result = catalog.match_message("Connection timed out after 30 seconds")

        assert result.matched is True
        assert result.entry.code == "TIMEOUT"

    def test_match_dns_message(self):
        """Test matching DNS failure in message."""
        catalog = FailureCatalog()
        result = catalog.match_message("Failed to resolve hostname api.example.com")

        assert result.matched is True
        assert result.entry.code == "DNS_FAILURE"

    def test_match_rate_limit_message(self):
        """Test matching rate limit in message."""
        catalog = FailureCatalog()
        result = catalog.match_message("Rate limit exceeded, please retry after 30 seconds")

        assert result.matched is True
        assert result.entry.code == "RATE_LIMITED"

    def test_match_http_status_code(self):
        """Test matching HTTP status codes in message."""
        catalog = FailureCatalog()

        result_429 = catalog.match_message("HTTP 429: Too Many Requests")
        assert result_429.matched is True
        assert result_429.entry.code == "RATE_LIMITED"

        result_403 = catalog.match_message("HTTP 403 Forbidden")
        assert result_403.matched is True
        assert result_403.entry.code == "PERMISSION_DENIED"

    def test_match_llm_error_message(self):
        """Test matching LLM errors in message."""
        catalog = FailureCatalog()
        result = catalog.match_message("Anthropic Claude API returned error")

        assert result.matched is True
        assert result.entry.code == "LLM_ERROR"

    def test_no_match_gibberish(self):
        """Test no match for irrelevant message."""
        catalog = FailureCatalog()
        result = catalog.match_message("The quick brown fox jumps over the lazy dog")

        assert result.matched is False


class TestRecoverySuggestions:
    """Tests for recovery suggestions."""

    def test_timeout_has_retry_suggestions(self):
        """Test TIMEOUT has retry suggestions."""
        catalog = FailureCatalog()
        entry = catalog.get_entry("TIMEOUT")

        assert entry is not None
        assert len(entry.recovery_suggestions) > 0
        assert entry.recovery_mode == "RETRY_EXPONENTIAL"
        assert entry.max_retries >= 1

    def test_budget_exceeded_has_escalate(self):
        """Test BUDGET_EXCEEDED suggests escalation."""
        catalog = FailureCatalog()
        entry = catalog.get_entry("BUDGET_EXCEEDED")

        assert entry is not None
        assert entry.is_retryable is False
        assert "budget" in " ".join(entry.recovery_suggestions).lower()

    def test_security_errors_not_retryable(self):
        """Test security errors are not retryable."""
        catalog = FailureCatalog()

        security_codes = ["INJECTION_DETECTED", "TAMPER_DETECTED", "SIGNATURE_INVALID"]
        for code in security_codes:
            entry = catalog.get_entry(code)
            assert entry is not None, f"Missing security code: {code}"
            assert entry.is_retryable is False, f"{code} should not be retryable"
            assert entry.category == "SECURITY", f"{code} should be SECURITY category"


class TestCatalogListing:
    """Tests for listing catalog entries."""

    def test_list_all_codes(self):
        """Test listing all error codes."""
        catalog = FailureCatalog()
        codes = catalog.list_codes()

        assert len(codes) >= 50
        assert "TIMEOUT" in codes
        assert "BUDGET_EXCEEDED" in codes
        assert "PERMISSION_DENIED" in codes

    def test_list_by_category(self):
        """Test listing entries by category."""
        catalog = FailureCatalog()

        transient = catalog.list_by_category("TRANSIENT")
        assert len(transient) >= 4  # TIMEOUT, DNS_FAILURE, CONNECTION_RESET, etc.

        resource = catalog.list_by_category("RESOURCE")
        assert len(resource) >= 5  # Budget and rate limit errors

    def test_list_retryable(self):
        """Test listing retryable errors."""
        catalog = FailureCatalog()
        retryable = catalog.list_retryable()

        assert len(retryable) >= 10  # Many transient errors are retryable
        for entry in retryable:
            assert entry.is_retryable is True


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_get_catalog_singleton(self):
        """Test get_catalog returns singleton."""
        cat1 = get_catalog()
        cat2 = get_catalog()
        assert cat1 is cat2

    def test_match_failure_function(self):
        """Test match_failure convenience function."""
        result = match_failure("TIMEOUT")
        assert result.matched is True
        assert result.entry.code == "TIMEOUT"

        result = match_failure("Connection timed out")
        assert result.matched is True


class TestMetricsLabels:
    """Tests for metrics label normalization."""

    def test_metrics_labels_normalized(self):
        """Test all metrics labels are lowercase with underscores."""
        catalog = FailureCatalog()

        import re

        label_pattern = re.compile(r"^[a-z][a-z0-9_]*$")

        for code in catalog.list_codes():
            entry = catalog.get_entry(code)
            for label_key in entry.metrics_labels.keys():
                assert label_pattern.match(label_key), f"Label key '{label_key}' in {code} is not normalized"

    def test_all_entries_have_metrics_labels(self):
        """Test all entries have metrics_labels."""
        catalog = FailureCatalog()

        for code in catalog.list_codes():
            entry = catalog.get_entry(code)
            assert entry.metrics_labels is not None
            assert "error_type" in entry.metrics_labels
            assert "category" in entry.metrics_labels


class TestCatalogExport:
    """Tests for catalog export."""

    def test_export_to_dict(self):
        """Test exporting catalog to dict."""
        catalog = FailureCatalog()
        data = catalog.to_dict()

        assert "version" in data
        assert "categories" in data
        assert "recovery_modes" in data
        assert "errors" in data
        assert len(data["errors"]) >= 50

    def test_entry_to_dict(self):
        """Test entry serialization."""
        catalog = FailureCatalog()
        entry = catalog.get_entry("TIMEOUT")
        entry_dict = entry.to_dict()

        assert entry_dict["code"] == "TIMEOUT"
        assert entry_dict["category"] == "TRANSIENT"
        assert entry_dict["is_retryable"] is True
        assert "recovery_suggestions" in entry_dict
