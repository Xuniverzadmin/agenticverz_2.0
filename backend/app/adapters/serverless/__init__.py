# Layer: L3 — Boundary Adapters
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Serverless function adapters
# Callers: SkillExecutor, WorkflowEngine
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2
# Reference: GAP-149, GAP-150 (Serverless Adapters)

"""
Serverless Adapters (GAP-149, GAP-150)

Provides adapters for serverless function execution:
- AWS Lambda (GAP-149)
- Google Cloud Functions (GAP-150)

Features:
- Unified interface for function invocation
- Async and sync invocation modes
- Response parsing
- Error handling
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import ServerlessAdapter
    from .lambda_adapter import LambdaAdapter
    from .cloud_functions_adapter import CloudFunctionsAdapter

__all__ = [
    "ServerlessAdapter",
    "LambdaAdapter",
    "CloudFunctionsAdapter",
    "get_serverless_adapter",
    "ServerlessType",
]


from enum import Enum


class ServerlessType(str, Enum):
    """Supported serverless types."""
    LAMBDA = "lambda"
    CLOUD_FUNCTIONS = "cloud_functions"


def get_serverless_adapter(
    serverless_type: ServerlessType,
    **config,
):
    """
    Factory function to get a serverless adapter.

    Args:
        serverless_type: Type of serverless platform
        **config: Platform-specific configuration

    Returns:
        ServerlessAdapter instance
    """
    if serverless_type == ServerlessType.LAMBDA:
        from .lambda_adapter import LambdaAdapter
        return LambdaAdapter(**config)
    elif serverless_type == ServerlessType.CLOUD_FUNCTIONS:
        from .cloud_functions_adapter import CloudFunctionsAdapter
        return CloudFunctionsAdapter(**config)
    else:
        raise ValueError(f"Unsupported serverless type: {serverless_type}")
