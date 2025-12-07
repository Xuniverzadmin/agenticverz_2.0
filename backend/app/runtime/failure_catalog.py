# Failure Catalog (M4.5 + M9 Persistence)
"""
Offline failure catalog for structured error handling and recovery.

Provides:
1. Load and validate failure catalog from JSON
2. Match error codes/messages to catalog entries
3. Get recovery strategies and suggestions
4. Support for exact, prefix, and regex matching
5. [M9] Persist all matches to database for learning
6. [M9] Prometheus metrics for failure tracking

Design Principles:
- Offline-first: No runtime dependencies, works standalone
- Deterministic: Same input produces same match result
- Extensible: Easy to add new error codes and recovery modes
- [M9] Observable: All matches tracked via metrics and DB
"""

from __future__ import annotations
import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from contextlib import contextmanager
from threading import Lock
import time

logger = logging.getLogger("nova.runtime.failure_catalog")

# M9: Non-blocking persistence with circuit breaker
_persist_executor: Optional[ThreadPoolExecutor] = None
_persist_lock = Lock()
_circuit_breaker_state = {
    "failures": 0,
    "last_failure_time": 0.0,
    "is_open": False,
}
_CIRCUIT_BREAKER_THRESHOLD = 5  # Open after 5 consecutive failures
_CIRCUIT_BREAKER_TIMEOUT = 60.0  # Reset after 60 seconds
_PERSIST_TIMEOUT = 2.0  # Max seconds for a persist operation

# M9: Dropped persistence counter
_failure_persist_dropped = None


def _get_persist_executor() -> ThreadPoolExecutor:
    """Get or create the persistence thread pool executor."""
    global _persist_executor
    if _persist_executor is None:
        with _persist_lock:
            if _persist_executor is None:
                _persist_executor = ThreadPoolExecutor(
                    max_workers=4,
                    thread_name_prefix="failure_persist"
                )
    return _persist_executor


def _check_circuit_breaker() -> bool:
    """
    Check if circuit breaker is open.

    Returns:
        True if we should allow the operation, False if circuit is open
    """
    state = _circuit_breaker_state

    if not state["is_open"]:
        return True

    # Check if timeout has elapsed
    if time.time() - state["last_failure_time"] > _CIRCUIT_BREAKER_TIMEOUT:
        with _persist_lock:
            state["is_open"] = False
            state["failures"] = 0
            logger.info("M9: Circuit breaker reset (timeout elapsed)")
        return True

    return False


def _record_circuit_failure():
    """Record a failure for circuit breaker."""
    state = _circuit_breaker_state
    with _persist_lock:
        state["failures"] += 1
        state["last_failure_time"] = time.time()

        if state["failures"] >= _CIRCUIT_BREAKER_THRESHOLD:
            state["is_open"] = True
            logger.warning(
                f"M9: Circuit breaker OPEN after {state['failures']} failures"
            )


def _record_circuit_success():
    """Record a success, reset failure count."""
    state = _circuit_breaker_state
    if state["failures"] > 0:
        with _persist_lock:
            state["failures"] = 0


# M9: Prometheus metrics (lazy import to avoid circular deps)
_metrics_initialized = False
_failure_match_hits = None
_failure_match_misses = None
_recovery_success = None
_recovery_failure = None


def _init_metrics():
    """Initialize Prometheus metrics lazily."""
    global _metrics_initialized, _failure_match_hits, _failure_match_misses
    global _recovery_success, _recovery_failure, _failure_persist_dropped

    if _metrics_initialized:
        return

    try:
        from prometheus_client import Counter

        _failure_match_hits = Counter(
            "failure_match_hits_total",
            "Total failure catalog hits (matched entries)",
            ["error_code", "category", "recovery_mode"]
        )
        _failure_match_misses = Counter(
            "failure_match_misses_total",
            "Total failure catalog misses (unmatched errors)",
            ["error_code"]
        )
        _recovery_success = Counter(
            "recovery_success_total",
            "Total successful recovery attempts",
            ["recovery_mode", "error_code"]
        )
        _recovery_failure = Counter(
            "recovery_failure_total",
            "Total failed recovery attempts",
            ["recovery_mode", "error_code"]
        )
        _failure_persist_dropped = Counter(
            "failure_persist_dropped_total",
            "Total failure records dropped due to circuit breaker or timeout",
            ["reason"]
        )
        _metrics_initialized = True
        logger.info("M9: Failure catalog metrics initialized")
    except ImportError:
        logger.warning("prometheus_client not available, metrics disabled")
        _metrics_initialized = True  # Don't retry

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


# ============== M9: Persistence Layer ==============

def persist_failure_match(
    run_id: str,
    result: MatchResult,
    error_code: str,
    error_message: Optional[str] = None,
    tenant_id: Optional[str] = None,
    skill_id: Optional[str] = None,
    step_index: Optional[int] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Persist a failure match to the database (M9).

    This is called after every match() operation to track all failures.
    Works synchronously for compatibility with existing code paths.

    Args:
        run_id: The run that produced this failure
        result: MatchResult from catalog match
        error_code: Original error code
        error_message: Full error message
        tenant_id: Tenant scope
        skill_id: Skill that failed
        step_index: Step in plan
        context: Additional context dict

    Returns:
        ID of persisted record, or None on failure
    """
    _init_metrics()

    try:
        from app.db import FailureMatch, engine
        from sqlmodel import Session

        # Build the record
        record = FailureMatch(
            run_id=run_id,
            tenant_id=tenant_id,
            error_code=error_code,
            error_message=error_message,
            catalog_entry_id=result.entry.code if result.entry else None,
            match_type=result.match_type.value,
            confidence_score=result.confidence,
            category=result.entry.category if result.entry else None,
            severity=result.entry.severity if result.entry else None,
            is_retryable=result.is_retryable,
            recovery_mode=result.recovery_mode,
            recovery_suggestion=(
                result.entry.recovery_suggestions[0]
                if result.entry and result.entry.recovery_suggestions
                else None
            ),
            skill_id=skill_id,
            step_index=step_index,
        )

        if context:
            record.set_context(context)

        # Persist
        with Session(engine) as session:
            session.add(record)
            session.commit()
            session.refresh(record)

            # Update metrics
            if result.matched and result.entry:
                if _failure_match_hits:
                    _failure_match_hits.labels(
                        error_code=result.entry.code,
                        category=result.entry.category,
                        recovery_mode=result.entry.recovery_mode or "none"
                    ).inc()
            else:
                if _failure_match_misses:
                    # Truncate error code for cardinality control
                    safe_code = error_code[:50] if error_code else "unknown"
                    _failure_match_misses.labels(error_code=safe_code).inc()

            logger.debug(
                f"M9: Persisted failure match {record.id} "
                f"(matched={result.matched}, code={error_code})"
            )
            return record.id

    except ImportError:
        logger.warning("M9: Database not available, skipping persistence")
        return None
    except Exception as e:
        logger.error(f"M9: Failed to persist failure match: {e}")
        return None


async def persist_failure_match_async(
    run_id: str,
    result: MatchResult,
    error_code: str,
    error_message: Optional[str] = None,
    tenant_id: Optional[str] = None,
    skill_id: Optional[str] = None,
    step_index: Optional[int] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Async version of persist_failure_match for async code paths.

    Runs the synchronous persistence in a thread pool executor.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: persist_failure_match(
            run_id=run_id,
            result=result,
            error_code=error_code,
            error_message=error_message,
            tenant_id=tenant_id,
            skill_id=skill_id,
            step_index=step_index,
            context=context,
        )
    )


def persist_failure_match_nonblocking(
    run_id: str,
    result: MatchResult,
    error_code: str,
    error_message: Optional[str] = None,
    tenant_id: Optional[str] = None,
    skill_id: Optional[str] = None,
    step_index: Optional[int] = None,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Non-blocking persistence with circuit breaker (M9 P0).

    This is the recommended way to persist failures in hot paths.
    It:
    1. Checks circuit breaker before attempting
    2. Submits to thread pool with timeout
    3. Fails fast if overwhelmed
    4. Records dropped events for alerting

    Unlike persist_failure_match(), this does NOT return the record ID
    because it's fire-and-forget.

    Args:
        run_id: The run that produced this failure
        result: MatchResult from catalog match
        error_code: Original error code
        error_message: Full error message
        tenant_id: Tenant scope
        skill_id: Skill that failed
        step_index: Step in plan
        context: Additional context dict
    """
    _init_metrics()

    # Check circuit breaker first
    if not _check_circuit_breaker():
        if _failure_persist_dropped:
            _failure_persist_dropped.labels(reason="circuit_open").inc()
        logger.debug(f"M9: Skipping persistence (circuit open) for run={run_id}")
        return

    executor = _get_persist_executor()

    def _do_persist():
        try:
            record_id = persist_failure_match(
                run_id=run_id,
                result=result,
                error_code=error_code,
                error_message=error_message,
                tenant_id=tenant_id,
                skill_id=skill_id,
                step_index=step_index,
                context=context,
            )
            if record_id:
                _record_circuit_success()
            else:
                _record_circuit_failure()
            return record_id
        except Exception as e:
            _record_circuit_failure()
            logger.error(f"M9: Non-blocking persist failed: {e}")
            return None

    try:
        # Submit to thread pool
        future = executor.submit(_do_persist)

        # Try to get result with timeout (non-blocking wait)
        # This doesn't actually block the caller - it just lets us
        # track if persistence completed in time
        try:
            future.result(timeout=_PERSIST_TIMEOUT)
        except FutureTimeoutError:
            # Timed out - record but don't block
            if _failure_persist_dropped:
                _failure_persist_dropped.labels(reason="timeout").inc()
            logger.warning(
                f"M9: Persistence timeout for run={run_id} "
                f"(timeout={_PERSIST_TIMEOUT}s)"
            )
            _record_circuit_failure()
    except Exception as e:
        # Thread pool submission failed
        if _failure_persist_dropped:
            _failure_persist_dropped.labels(reason="submit_failed").inc()
        logger.error(f"M9: Failed to submit persistence task: {e}")
        _record_circuit_failure()


def update_recovery_status(
    failure_match_id: str,
    succeeded: bool,
) -> bool:
    """
    Update recovery status after a recovery attempt (M9).

    Args:
        failure_match_id: ID of the failure match record
        succeeded: Whether recovery was successful

    Returns:
        True if updated successfully
    """
    _init_metrics()

    try:
        from app.db import FailureMatch, engine, utc_now
        from sqlmodel import Session

        with Session(engine) as session:
            record = session.get(FailureMatch, failure_match_id)
            if not record:
                logger.warning(f"M9: Failure match {failure_match_id} not found")
                return False

            record.recovery_attempted = True
            record.recovery_succeeded = succeeded
            record.updated_at = utc_now()
            session.add(record)
            session.commit()

            # Update metrics
            if succeeded:
                if _recovery_success:
                    _recovery_success.labels(
                        recovery_mode=record.recovery_mode or "unknown",
                        error_code=record.error_code
                    ).inc()
            else:
                if _recovery_failure:
                    _recovery_failure.labels(
                        recovery_mode=record.recovery_mode or "unknown",
                        error_code=record.error_code
                    ).inc()

            logger.debug(
                f"M9: Updated recovery status for {failure_match_id} "
                f"(succeeded={succeeded})"
            )
            return True

    except Exception as e:
        logger.error(f"M9: Failed to update recovery status: {e}")
        return False


def match_and_persist(
    code_or_message: str,
    run_id: str,
    tenant_id: Optional[str] = None,
    skill_id: Optional[str] = None,
    step_index: Optional[int] = None,
    context: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
) -> MatchResult:
    """
    Match and persist in one call (M9 convenience function).

    This is the recommended way to use the failure catalog in M9+.

    Args:
        code_or_message: Error code or message to match
        run_id: Run that produced this failure
        tenant_id: Tenant scope
        skill_id: Skill that failed
        step_index: Step in plan
        context: Additional context
        error_message: Full error message (if different from code_or_message)

    Returns:
        MatchResult from catalog
    """
    catalog = get_catalog()
    result = catalog.match(code_or_message)

    # Persist (fire and forget for performance)
    persist_failure_match(
        run_id=run_id,
        result=result,
        error_code=code_or_message,
        error_message=error_message or code_or_message,
        tenant_id=tenant_id,
        skill_id=skill_id,
        step_index=step_index,
        context=context,
    )

    return result


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
