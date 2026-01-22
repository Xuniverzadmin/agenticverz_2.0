# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: IAM integration for identity and access management
# Callers: Auth middleware, API routes
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: GAP-173 (IAM Integration)

"""
IAM Integration (GAP-173)

Provides integration with external identity providers:
- Clerk (primary)
- Auth0 (planned)
- Custom OIDC providers

Features:
- Identity resolution
- Role mapping
- Permission checking
- Audit logging
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .iam_service import IAMService
    from .identity_resolver import IdentityResolver

__all__ = [
    "IAMService",
    "IdentityResolver",
    "get_iam_service",
    "configure_iam_service",
    "reset_iam_service",
]

# Lazy import cache
_iam_service = None


def get_iam_service():
    """Get the singleton IAM service."""
    global _iam_service
    if _iam_service is None:
        from .iam_service import IAMService
        _iam_service = IAMService()
    return _iam_service


def configure_iam_service(service=None):
    """Configure the IAM service (for testing)."""
    global _iam_service
    if service is not None:
        _iam_service = service


def reset_iam_service():
    """Reset the IAM service (for testing)."""
    global _iam_service
    _iam_service = None
