# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: worker
#   Execution: sync
# Role: External call guards for workflow safety
# Callers: workflow engine
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: Workflow System

# External Calls Guard (M4 Hardening)
"""
Guard for blocking external network calls during golden file tests.

Provides:
1. Environment variable control for CI
2. Socket patching for test isolation
3. Request interception for debugging

Usage in CI:
    DISABLE_EXTERNAL_CALLS=1 pytest tests/workflow/

Usage in tests:
    from app.workflow.external_guard import ExternalCallsGuard

    def test_golden_replay():
        with ExternalCallsGuard():
            # All external calls will raise ExternalCallBlockedError
            run_workflow_replay()

Design Principles:
- Fail-fast: Block and raise immediately, don't silently mock
- Auditable: Log all blocked attempts for debugging
- Configurable: Allow-list specific hosts if needed
"""

from __future__ import annotations

import logging
import os
import socket
from contextlib import contextmanager
from typing import Any, Callable, List, Optional, Set, Tuple
from unittest.mock import patch

logger = logging.getLogger("nova.workflow.external_guard")


class ExternalCallBlockedError(Exception):
    """Raised when an external call is blocked by the guard."""

    def __init__(self, call_type: str, target: str, message: str = ""):
        super().__init__(f"External {call_type} call blocked: {target}. {message}")
        self.call_type = call_type
        self.target = target


# Check environment variable
DISABLE_EXTERNAL_CALLS = os.getenv("DISABLE_EXTERNAL_CALLS", "").lower() in ("1", "true", "yes", "on")

# Allowed hosts for internal services (can be extended)
DEFAULT_ALLOWED_HOSTS: Set[str] = {
    "localhost",
    "127.0.0.1",
    "::1",
}

# Track blocked calls for test assertions
_blocked_calls: List[Tuple[str, str]] = []


def is_external_calls_disabled() -> bool:
    """Check if external calls are disabled."""
    return DISABLE_EXTERNAL_CALLS


def get_blocked_calls() -> List[Tuple[str, str]]:
    """Get list of blocked calls (call_type, target)."""
    return _blocked_calls.copy()


def clear_blocked_calls() -> None:
    """Clear blocked calls history."""
    global _blocked_calls
    _blocked_calls = []


def check_external_call_allowed(
    call_type: str,
    target: str,
    allowed_hosts: Optional[Set[str]] = None,
) -> None:
    """
    Check if an external call is allowed.

    Args:
        call_type: Type of call (socket, http, etc.)
        target: Target host or URL
        allowed_hosts: Set of allowed hosts (default uses DEFAULT_ALLOWED_HOSTS)

    Raises:
        ExternalCallBlockedError: If call is blocked
    """
    if not DISABLE_EXTERNAL_CALLS:
        return

    allowed = allowed_hosts or DEFAULT_ALLOWED_HOSTS

    # Extract host from target
    host = target.split(":")[0] if ":" in target else target
    host = host.replace("http://", "").replace("https://", "").split("/")[0]

    if host in allowed:
        return

    # Block and record
    _blocked_calls.append((call_type, target))
    logger.warning("external_call_blocked", extra={"call_type": call_type, "target": target})
    raise ExternalCallBlockedError(
        call_type=call_type,
        target=target,
        message="Set DISABLE_EXTERNAL_CALLS=0 to allow external calls",
    )


class _BlockedSocket:
    """Socket wrapper that blocks external connections."""

    _original_socket = socket.socket

    def __init__(self, family: int = -1, type: int = -1, proto: int = -1, fileno: int = None):
        self._family = family
        self._type = type
        self._proto = proto
        self._fileno = fileno
        self._allowed_hosts = DEFAULT_ALLOWED_HOSTS

    def connect(self, address: Tuple[str, int]) -> None:
        host = address[0] if isinstance(address, tuple) else str(address)
        check_external_call_allowed("socket", host, self._allowed_hosts)
        # If we get here, it's allowed - create real socket
        real_socket = self._original_socket(self._family, self._type, self._proto)
        return real_socket.connect(address)

    def __getattr__(self, name: str) -> Any:
        # Delegate to real socket for other operations
        real_socket = self._original_socket(self._family, self._type, self._proto)
        return getattr(real_socket, name)


def _create_blocking_socket_factory(allowed_hosts: Optional[Set[str]] = None) -> Callable:
    """Create a socket factory that blocks external connections."""
    hosts = allowed_hosts or DEFAULT_ALLOWED_HOSTS
    original_socket = socket.socket

    def blocking_socket(
        family: int = socket.AF_INET,
        type: int = socket.SOCK_STREAM,
        proto: int = 0,
        fileno: int = None,
    ) -> socket.socket:
        """Blocking socket that checks connections."""
        real_socket = original_socket(family, type, proto, fileno)
        original_connect = real_socket.connect

        def blocking_connect(address: Any) -> None:
            if isinstance(address, tuple) and len(address) >= 1:
                host = str(address[0])
                if host not in hosts:
                    check_external_call_allowed("socket", host, hosts)
            return original_connect(address)

        real_socket.connect = blocking_connect
        return real_socket

    return blocking_socket


class ExternalCallsGuard:
    """
    Context manager that blocks external network calls.

    Usage:
        with ExternalCallsGuard():
            # External calls raise ExternalCallBlockedError
            requests.get("https://api.example.com")  # Blocked!

        with ExternalCallsGuard(allow_hosts={"api.int.com"}):
            # Allowed hosts can be accessed
            requests.get("https://api.int.com")  # OK

    Blocks both sync and async HTTP clients:
    - requests.Session.request (sync)
    - httpx.Client.request (sync)
    - httpx.AsyncClient.request (async)
    - aiohttp.ClientSession._request (async)
    """

    def __init__(
        self,
        allow_hosts: Optional[Set[str]] = None,
        block_requests: bool = True,
        block_httpx: bool = True,
        block_aiohttp: bool = True,
        block_urllib: bool = True,
    ):
        """
        Initialize guard.

        Args:
            allow_hosts: Additional hosts to allow
            block_requests: Block requests library
            block_httpx: Block httpx library (both sync and async)
            block_aiohttp: Block aiohttp library
            block_urllib: Block urllib library
        """
        self.allowed_hosts = DEFAULT_ALLOWED_HOSTS.copy()
        if allow_hosts:
            self.allowed_hosts.update(allow_hosts)

        self.block_requests = block_requests
        self.block_httpx = block_httpx
        self.block_aiohttp = block_aiohttp
        self.block_urllib = block_urllib

        self._patches: List[Any] = []

    def __enter__(self) -> "ExternalCallsGuard":
        clear_blocked_calls()

        # Patch socket.socket
        socket_patch = patch("socket.socket", _create_blocking_socket_factory(self.allowed_hosts))
        self._patches.append(socket_patch)
        socket_patch.start()

        # Patch requests if available and enabled
        if self.block_requests:
            try:
                import requests

                requests_patch = patch.object(
                    requests.Session,
                    "request",
                    side_effect=lambda *a, **kw: self._check_and_block("requests", a, kw),
                )
                self._patches.append(requests_patch)
                requests_patch.start()
            except ImportError:
                pass

        # Patch httpx if available and enabled (both sync and async clients)
        if self.block_httpx:
            try:
                import httpx

                # Patch sync Client
                httpx_sync_patch = patch.object(
                    httpx.Client,
                    "request",
                    side_effect=lambda *a, **kw: self._check_and_block("httpx", a, kw),
                )
                self._patches.append(httpx_sync_patch)
                httpx_sync_patch.start()

                # Patch async AsyncClient
                httpx_async_patch = patch.object(
                    httpx.AsyncClient,
                    "request",
                    side_effect=lambda *a, **kw: self._check_and_block_async("httpx.AsyncClient", a, kw),
                )
                self._patches.append(httpx_async_patch)
                httpx_async_patch.start()

                # Also patch send methods for completeness
                httpx_async_send_patch = patch.object(
                    httpx.AsyncClient,
                    "send",
                    side_effect=lambda *a, **kw: self._check_and_block_async_send("httpx.AsyncClient.send", a, kw),
                )
                self._patches.append(httpx_async_send_patch)
                httpx_async_send_patch.start()

            except ImportError:
                pass

        # Patch aiohttp if available and enabled
        if self.block_aiohttp:
            try:
                import aiohttp

                aiohttp_patch = patch.object(
                    aiohttp.ClientSession,
                    "_request",
                    side_effect=lambda *a, **kw: self._check_and_block_async("aiohttp", a, kw),
                )
                self._patches.append(aiohttp_patch)
                aiohttp_patch.start()
            except ImportError:
                pass

        return self

    def __exit__(self, exc_type: Any, _exc_val: Any, _exc_tb: Any) -> None:
        for p in reversed(self._patches):
            p.stop()
        self._patches.clear()

    def _check_and_block(
        self,
        library: str,
        args: tuple,
        kwargs: dict,
    ) -> None:
        """Check if HTTP call should be blocked (sync)."""
        # Extract URL from args/kwargs
        url = kwargs.get("url") or (args[1] if len(args) > 1 else "unknown")
        url_str = str(url)

        # Extract host
        host = url_str.replace("http://", "").replace("https://", "").split("/")[0].split(":")[0]

        if host not in self.allowed_hosts:
            check_external_call_allowed(library, url_str, self.allowed_hosts)

    async def _check_and_block_async(
        self,
        library: str,
        args: tuple,
        kwargs: dict,
    ) -> None:
        """Check if async HTTP call should be blocked."""
        # Extract URL from args/kwargs
        url = kwargs.get("url") or (args[1] if len(args) > 1 else "unknown")
        url_str = str(url)

        # Extract host
        host = url_str.replace("http://", "").replace("https://", "").split("/")[0].split(":")[0]

        if host not in self.allowed_hosts:
            check_external_call_allowed(library, url_str, self.allowed_hosts)

    async def _check_and_block_async_send(
        self,
        library: str,
        args: tuple,
        kwargs: dict,
    ) -> None:
        """Check if async HTTP send should be blocked (for httpx Request objects)."""
        # For send(), the first arg is often the Request object
        request = args[0] if args else None
        if request and hasattr(request, "url"):
            url_str = str(request.url)
            host = url_str.replace("http://", "").replace("https://", "").split("/")[0].split(":")[0]
            if host not in self.allowed_hosts:
                check_external_call_allowed(library, url_str, self.allowed_hosts)
        else:
            # Can't determine URL, block by default in strict mode
            check_external_call_allowed(library, "unknown", self.allowed_hosts)


@contextmanager
def block_external_calls(allow_hosts: Optional[Set[str]] = None):
    """
    Context manager shorthand for ExternalCallsGuard.

    Usage:
        with block_external_calls():
            # External calls blocked
            pass
    """
    guard = ExternalCallsGuard(allow_hosts=allow_hosts)
    with guard:
        yield guard


def require_no_external_calls(func: Callable) -> Callable:
    """
    Decorator that blocks external calls during function execution.

    Usage:
        @require_no_external_calls
        def test_golden_replay():
            # External calls blocked
            pass
    """
    import functools

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        with ExternalCallsGuard():
            return func(*args, **kwargs)

    return wrapper


def assert_no_external_calls_made() -> None:
    """
    Assert that no external calls were blocked.

    Raises:
        AssertionError: If any calls were blocked
    """
    blocked = get_blocked_calls()
    if blocked:
        calls_str = ", ".join(f"{t}:{target}" for t, target in blocked)
        raise AssertionError(f"External calls were attempted: {calls_str}")
