# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Connection pool management for database and external services
# Callers: ConnectorRegistry, Services, API routes
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: GAP-172 (Connection Pool Management)

"""
Connection Pool Management (GAP-172)

Provides unified connection pool management for:
- Database connections (PostgreSQL via asyncpg)
- Redis connections
- HTTP client pools
- External service connections

Features:
- Health checking
- Connection limits per tenant
- Graceful shutdown
- Metrics collection
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pool_manager import ConnectionPoolManager

__all__ = [
    "ConnectionPoolManager",
    "get_pool_manager",
    "configure_pool_manager",
    "reset_pool_manager",
]

# Lazy import cache
_pool_manager = None


def get_pool_manager():
    """Get the singleton pool manager."""
    global _pool_manager
    if _pool_manager is None:
        from .pool_manager import ConnectionPoolManager
        _pool_manager = ConnectionPoolManager()
    return _pool_manager


def configure_pool_manager(manager=None):
    """Configure the pool manager (for testing)."""
    global _pool_manager
    if manager is not None:
        _pool_manager = manager


def reset_pool_manager():
    """Reset the pool manager (for testing)."""
    global _pool_manager
    _pool_manager = None
