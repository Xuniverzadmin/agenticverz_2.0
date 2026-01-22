# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Execution sandboxing for safe code execution
# Callers: Runtime, Skill executors
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: GAP-174 (Execution Sandboxing)

"""
Execution Sandboxing (GAP-174)

Provides isolated execution environments for:
- Code execution with resource limits
- Network isolation
- File system sandboxing
- Process isolation

Features:
- Container-based isolation (Docker/Podman)
- Process-based isolation (subprocess with limits)
- Resource limits (CPU, memory, time)
- Network policies
- File system restrictions
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .sandbox_service import SandboxService
    from .sandbox_executor import SandboxExecutor

__all__ = [
    "SandboxService",
    "SandboxExecutor",
    "get_sandbox_service",
    "configure_sandbox_service",
    "reset_sandbox_service",
]

# Lazy import cache
_sandbox_service = None


def get_sandbox_service():
    """Get the singleton sandbox service."""
    global _sandbox_service
    if _sandbox_service is None:
        from .sandbox_service import SandboxService
        _sandbox_service = SandboxService()
    return _sandbox_service


def configure_sandbox_service(service=None):
    """Configure the sandbox service (for testing)."""
    global _sandbox_service
    if service is not None:
        _sandbox_service = service


def reset_sandbox_service():
    """Reset the sandbox service (for testing)."""
    global _sandbox_service
    _sandbox_service = None
