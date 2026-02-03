# Layer: L2 — Adapter
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Base class for serverless adapters
# Callers: Serverless adapter implementations
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2
# Reference: GAP-149, GAP-150

"""
Serverless Base Adapter

Provides abstract interface for serverless function operations.
All serverless adapters must implement this interface.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class InvocationType(str, Enum):
    """Type of function invocation."""
    SYNC = "sync"  # Wait for response
    ASYNC = "async"  # Fire and forget
    DRY_RUN = "dry_run"  # Validate only


@dataclass
class InvocationRequest:
    """Request to invoke a serverless function."""

    function_name: str
    payload: Dict[str, Any]
    invocation_type: InvocationType = InvocationType.SYNC
    timeout_seconds: int = 30
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "function_name": self.function_name,
            "payload": self.payload,
            "invocation_type": self.invocation_type.value,
            "timeout_seconds": self.timeout_seconds,
            "metadata": self.metadata,
        }


@dataclass
class InvocationResult:
    """Result of a serverless function invocation."""

    request_id: str
    status_code: int
    payload: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    logs: Optional[str] = None
    duration_ms: Optional[int] = None
    billed_duration_ms: Optional[int] = None
    memory_used_mb: Optional[int] = None
    invoked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def success(self) -> bool:
        return 200 <= self.status_code < 300 and self.error is None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request_id": self.request_id,
            "status_code": self.status_code,
            "payload": self.payload,
            "error": self.error,
            "logs": self.logs,
            "duration_ms": self.duration_ms,
            "billed_duration_ms": self.billed_duration_ms,
            "memory_used_mb": self.memory_used_mb,
            "invoked_at": self.invoked_at.isoformat(),
            "success": self.success,
        }


@dataclass
class FunctionInfo:
    """Information about a serverless function."""

    name: str
    arn_or_uri: str
    runtime: Optional[str] = None
    memory_mb: Optional[int] = None
    timeout_seconds: Optional[int] = None
    last_modified: Optional[datetime] = None
    description: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "arn_or_uri": self.arn_or_uri,
            "runtime": self.runtime,
            "memory_mb": self.memory_mb,
            "timeout_seconds": self.timeout_seconds,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "description": self.description,
            "tags": self.tags,
        }


class ServerlessAdapter(ABC):
    """
    Abstract base class for serverless adapters.

    All serverless implementations must implement these methods.
    """

    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to the serverless platform.

        Returns:
            True if connected successfully
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the serverless platform."""
        pass

    @abstractmethod
    async def invoke(
        self,
        request: InvocationRequest,
    ) -> InvocationResult:
        """
        Invoke a serverless function.

        Args:
            request: Invocation request

        Returns:
            InvocationResult
        """
        pass

    @abstractmethod
    async def invoke_batch(
        self,
        requests: List[InvocationRequest],
        max_concurrent: int = 10,
    ) -> List[InvocationResult]:
        """
        Invoke multiple functions concurrently.

        Args:
            requests: List of invocation requests
            max_concurrent: Maximum concurrent invocations

        Returns:
            List of InvocationResult
        """
        pass

    @abstractmethod
    async def get_function_info(
        self,
        function_name: str,
    ) -> Optional[FunctionInfo]:
        """
        Get information about a function.

        Args:
            function_name: Name of the function

        Returns:
            FunctionInfo or None if not found
        """
        pass

    @abstractmethod
    async def list_functions(
        self,
        prefix: Optional[str] = None,
        max_results: int = 100,
    ) -> List[FunctionInfo]:
        """
        List available functions.

        Args:
            prefix: Optional name prefix filter
            max_results: Maximum results

        Returns:
            List of FunctionInfo
        """
        pass

    @abstractmethod
    async def function_exists(
        self,
        function_name: str,
    ) -> bool:
        """
        Check if a function exists.

        Args:
            function_name: Name of the function

        Returns:
            True if exists
        """
        pass

    async def health_check(self) -> bool:
        """
        Check if the serverless platform is healthy.

        Returns:
            True if healthy
        """
        try:
            await self.list_functions(max_results=1)
            return True
        except Exception as e:
            logger.warning(f"Serverless health check failed: {e}")
            return False
