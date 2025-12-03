# Failure Catalog (M4.5)
"""
Offline failure catalog for structured error handling and recovery.

Provides:
1. Load and validate failure catalog from JSON
2. Match error codes/messages to catalog entries
3. Get recovery strategies and suggestions
4. Support for exact, prefix, and regex matching

Design Principles:
- Offline-first: No runtime dependencies, works standalone
- Deterministic: Same input produces same match result
- Extensible: Easy to add new error codes and recovery modes
"""

from __future__ import annotations
import json
import logging
import os
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger("nova.runtime.failure_catalog")

# Default catalog path relative to this file
DEFAULT_CATALOG_PATH = Path(__file__).parent.parent / "data" / "failure_catalog.json"


class MatchType(str, Enum):
    """Types of matching for error lookup."""
    EXACT = "exact"
    PREFIX = "prefix"
    REGEX = "regex"
    CODE = "code"  # Direct code lookup


class RecoveryStrategy(str, Enum):
    """Recovery strategies from the catalog."""
    RETRY_IMMEDIATE = "RETRY_IMMEDIATE"
    RETRY_EXPONENTIAL = "RETRY_EXPONENTIAL"
    RETRY_WITH_JITTER = "RETRY_WITH_JITTER"
    FALLBACK = "FALLBACK"
    CIRCUIT_BREAKER = "CIRCUIT_BREAKER"
    SKIP = "SKIP"
    ABORT = "ABORT"
    ESCALATE = "ESCALATE"
    CHECKPOINT_RESTORE = "CHECKPOINT_RESTORE"
    MANUAL_INTERVENTION = "MANUAL_INTERVENTION"


@dataclass
class CatalogEntry:
    """A single entry from the failure catalog."""
    code: str
    category: str
    message: str
    severity: str
    is_retryable: bool
    recovery_mode: str
    recovery_suggestions: List[str]
    http_status: int
    metrics_labels: Dict[str, str]

    # Computed fields
    max_retries: int = 0
    base_delay_ms: int = 0
    max_delay_ms: int = 0
    jitter_factor: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "code": self.code,
            "category": self.category,
            "message": self.message,
            "severity": self.severity,
            "is_retryable": self.is_retryable,
            "recovery_mode": self.recovery_mode,
            "recovery_suggestions": self.recovery_suggestions,
            "http_status": self.http_status,
            "metrics_labels": self.metrics_labels,
            "max_retries": self.max_retries,
            "base_delay_ms": self.base_delay_ms,
            "max_delay_ms": self.max_delay_ms,
            "jitter_factor": self.jitter_factor,
        }


@dataclass
class MatchResult:
    """Result of a catalog match operation."""
    matched: bool
    entry: Optional[CatalogEntry]
    match_type: MatchType
    confidence: float  # 1.0 for exact/code, 0.8 for prefix, 0.6 for regex

    @property
    def recovery_mode(self) -> Optional[str]:
        return self.entry.recovery_mode if self.entry else None

    @property
    def is_retryable(self) -> bool:
        return self.entry.is_retryable if self.entry else False

    @property
    def suggestions(self) -> List[str]:
        return self.entry.recovery_suggestions if self.entry else []


class FailureCatalog:
    """
    Failure catalog for structured error handling.

    Usage:
        catalog = FailureCatalog()

        # Match by error code
        result = catalog.match_code("TIMEOUT")

        # Match by error message
        result = catalog.match_message("Connection timed out after 30s")

        # Get recovery info
        if result.matched:
            print(f"Recovery: {result.entry.recovery_mode}")
            print(f"Retryable: {result.is_retryable}")
    """

    def __init__(self, path: Optional[Union[str, Path]] = None):
        """
        Initialize failure catalog.

        Args:
            path: Path to failure_catalog.json. Uses default if not provided.
        """
        self._path = Path(path) if path else DEFAULT_CATALOG_PATH
        self._catalog: Dict[str, Dict[str, Any]] = {}
        self._categories: Dict[str, Dict[str, Any]] = {}
        self._recovery_modes: Dict[str, Dict[str, Any]] = {}
        self._version: str = "0.0.0"
        self._entries: Dict[str, CatalogEntry] = {}

        self._load()

    def _load(self) -> None:
        """Load catalog from JSON file."""
        if not self._path.exists():
            logger.warning(f"Failure catalog not found at {self._path}, using empty catalog")
            return

        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._version = data.get("version", "0.0.0")
            self._categories = data.get("categories", {})
            self._recovery_modes = data.get("recovery_modes", {})
            self._catalog = data.get("errors", {})

            # Pre-process entries
            for code, error_data in self._catalog.items():
                entry = self._parse_entry(code, error_data)
                self._entries[code] = entry

            logger.info(f"Loaded failure catalog v{self._version} with {len(self._entries)} errors")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse failure catalog: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load failure catalog: {e}")
            raise

    def _parse_entry(self, code: str, data: Dict[str, Any]) -> CatalogEntry:
        """Parse a catalog entry from JSON data."""
        # Get category defaults
        category_name = data.get("category", "PERMANENT")
        category = self._categories.get(category_name, {})

        # Get recovery mode config
        recovery_mode = data.get("recovery_mode", category.get("default_recovery", "ABORT"))
        recovery_config = self._recovery_modes.get(recovery_mode, {}).get("config", {})

        # Merge with category defaults
        is_retryable = data.get("is_retryable", category.get("is_retryable", False))
        max_retries = recovery_config.get("max_retries", category.get("max_retries", 0))
        base_delay_ms = recovery_config.get("base_delay_ms", category.get("base_delay_ms", 0))
        max_delay_ms = recovery_config.get("max_delay_ms", 30000)
        jitter_factor = recovery_config.get("jitter_factor", 0.0)

        return CatalogEntry(
            code=code,
            category=category_name,
            message=data.get("message", ""),
            severity=data.get("severity", "MEDIUM"),
            is_retryable=is_retryable,
            recovery_mode=recovery_mode,
            recovery_suggestions=data.get("recovery_suggestions", []),
            http_status=data.get("http_status", 500),
            metrics_labels=data.get("metrics_labels", {}),
            max_retries=max_retries,
            base_delay_ms=base_delay_ms,
            max_delay_ms=max_delay_ms,
            jitter_factor=jitter_factor,
        )

    @property
    def version(self) -> str:
        """Get catalog version."""
        return self._version

    @property
    def error_count(self) -> int:
        """Get number of error codes in catalog."""
        return len(self._entries)

    def match_code(self, code: str) -> MatchResult:
        """
        Match by exact error code.

        Args:
            code: Error code to look up (e.g., "TIMEOUT", "BUDGET_EXCEEDED")

        Returns:
            MatchResult with entry if found
        """
        code_upper = code.upper()

        if code_upper in self._entries:
            return MatchResult(
                matched=True,
                entry=self._entries[code_upper],
                match_type=MatchType.CODE,
                confidence=1.0,
            )

        return MatchResult(
            matched=False,
            entry=None,
            match_type=MatchType.CODE,
            confidence=0.0,
        )

    def match_message(self, message: str) -> MatchResult:
        """
        Match by error message content.

        Matching priority:
        1. Exact match on error code in message
        2. Prefix match on message patterns
        3. Keyword-based matching

        Args:
            message: Error message to match

        Returns:
            MatchResult with best match
        """
        message_lower = message.lower()

        # Try to extract error code from message
        for code in self._entries.keys():
            if code.lower() in message_lower or code.replace("_", " ").lower() in message_lower:
                return MatchResult(
                    matched=True,
                    entry=self._entries[code],
                    match_type=MatchType.EXACT,
                    confidence=0.95,
                )

        # Keyword-based matching
        keyword_matches = {
            "timeout": "TIMEOUT",
            "timed out": "TIMEOUT",
            "dns": "DNS_FAILURE",
            "resolve": "DNS_FAILURE",
            "connection reset": "CONNECTION_RESET",
            "connection refused": "DB_CONNECTION_FAILED",
            "service unavailable": "SERVICE_UNAVAILABLE",
            "503": "SERVICE_UNAVAILABLE",
            "gateway timeout": "GATEWAY_TIMEOUT",
            "504": "GATEWAY_TIMEOUT",
            "rate limit": "RATE_LIMITED",
            "429": "RATE_LIMITED",
            "budget": "BUDGET_EXCEEDED",
            "quota": "QUOTA_EXHAUSTED",
            "permission denied": "PERMISSION_DENIED",
            "forbidden": "PERMISSION_DENIED",
            "403": "PERMISSION_DENIED",
            "unauthorized": "UNAUTHORIZED",
            "401": "UNAUTHORIZED",
            "invalid input": "INVALID_INPUT",
            "validation": "SCHEMA_VALIDATION_FAILED",
            "schema": "SCHEMA_VALIDATION_FAILED",
            "missing required": "MISSING_REQUIRED_FIELD",
            "not found": "DATA_NOT_FOUND",
            "404": "DATA_NOT_FOUND",
            "llm": "LLM_ERROR",
            "claude": "LLM_ERROR",
            "anthropic": "LLM_ERROR",
            "context exceeded": "LLM_CONTEXT_EXCEEDED",
            "token limit": "LLM_CONTEXT_EXCEEDED",
            "injection": "INJECTION_DETECTED",
            "tamper": "TAMPER_DETECTED",
            "checkpoint": "CHECKPOINT_SAVE_FAILED",
            "planner": "PLANNER_ERROR",
        }

        for keyword, code in keyword_matches.items():
            if keyword in message_lower and code in self._entries:
                return MatchResult(
                    matched=True,
                    entry=self._entries[code],
                    match_type=MatchType.PREFIX,
                    confidence=0.7,
                )

        # No match found
        return MatchResult(
            matched=False,
            entry=None,
            match_type=MatchType.PREFIX,
            confidence=0.0,
        )

    def match(self, code_or_message: str) -> MatchResult:
        """
        Match by either error code or message.

        Tries code match first, then message match.

        Args:
            code_or_message: Error code or message

        Returns:
            MatchResult with best match
        """
        # Try code match first
        result = self.match_code(code_or_message)
        if result.matched:
            return result

        # Fall back to message match
        return self.match_message(code_or_message)

    def get_entry(self, code: str) -> Optional[CatalogEntry]:
        """
        Get catalog entry by code.

        Args:
            code: Error code

        Returns:
            CatalogEntry or None
        """
        return self._entries.get(code.upper())

    def get_recovery_config(self, recovery_mode: str) -> Dict[str, Any]:
        """
        Get recovery mode configuration.

        Args:
            recovery_mode: Recovery mode name

        Returns:
            Recovery configuration dict
        """
        return self._recovery_modes.get(recovery_mode, {}).get("config", {})

    def get_category(self, category_name: str) -> Dict[str, Any]:
        """
        Get category configuration.

        Args:
            category_name: Category name

        Returns:
            Category configuration dict
        """
        return self._categories.get(category_name, {})

    def list_codes(self) -> List[str]:
        """List all error codes in catalog."""
        return list(self._entries.keys())

    def list_by_category(self, category: str) -> List[CatalogEntry]:
        """
        List all entries in a category.

        Args:
            category: Category name

        Returns:
            List of CatalogEntry in category
        """
        return [e for e in self._entries.values() if e.category == category]

    def list_retryable(self) -> List[CatalogEntry]:
        """List all retryable error entries."""
        return [e for e in self._entries.values() if e.is_retryable]

    def to_dict(self) -> Dict[str, Any]:
        """Export catalog as dictionary."""
        return {
            "version": self._version,
            "categories": self._categories,
            "recovery_modes": self._recovery_modes,
            "errors": {code: entry.to_dict() for code, entry in self._entries.items()},
        }


# Singleton instance for convenience
_catalog_instance: Optional[FailureCatalog] = None


def get_catalog(path: Optional[str] = None) -> FailureCatalog:
    """
    Get or create singleton catalog instance.

    Args:
        path: Optional path override

    Returns:
        FailureCatalog instance
    """
    global _catalog_instance
    if _catalog_instance is None or path is not None:
        _catalog_instance = FailureCatalog(path)
    return _catalog_instance


def match_failure(code_or_message: str) -> MatchResult:
    """
    Convenience function to match failure.

    Args:
        code_or_message: Error code or message

    Returns:
        MatchResult
    """
    return get_catalog().match(code_or_message)


if __name__ == "__main__":
    # Quick smoke test
    catalog = FailureCatalog()
    print(f"Loaded catalog v{catalog.version} with {catalog.error_count} errors")

    # Test code match
    result = catalog.match_code("TIMEOUT")
    print(f"\nMatch 'TIMEOUT': {result.matched}")
    if result.entry:
        print(f"  Recovery: {result.entry.recovery_mode}")
        print(f"  Retryable: {result.entry.is_retryable}")
        print(f"  Suggestions: {result.entry.recovery_suggestions}")

    # Test message match
    result = catalog.match_message("Connection timed out after 30 seconds")
    print(f"\nMatch 'Connection timed out...': {result.matched}")
    if result.entry:
        print(f"  Code: {result.entry.code}")
        print(f"  Confidence: {result.confidence}")
